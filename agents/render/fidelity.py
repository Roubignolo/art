"""Audit de fidélité colorimétrique — le garde-fou de la restauration.

Systématise l'analyse manuelle qui a révélé que notre gray-world délavait le
bleu volontaire de la nappe de Cézanne (cf. docs/restauration-politique.md).

Principe : un master de musée open-access est DÉJÀ une reproduction fidèle
(numérisé avec mire + profil ICC). Toute « restauration » qui déplace la teinte
DÉGRADE la fidélité au lieu de l'améliorer. Ce module compare l'original (vérité
terrain) à la version traitée et répond, chiffres à l'appui :
  • de combien la couleur a-t-elle dérivé ? (ΔE perceptuel, CIELAB)
  • a-t-on neutralisé une dominante chromatique VOULUE par l'artiste ?
    (chute de chroma C*, recentrage du nuage a*/b* vers le gris)
  • où la dérive est-elle maximale ? (localisation du pire patch)

100 % local, Pillow uniquement (aucune dépendance numpy). La conversion
sRGB→CIELAB et ΔE2000 suivent les formules canoniques (Lindbloom / Sharma) —
vérifiées par tests/test_fidelity.py contre des valeurs de référence publiées.

Robustesse au recadrage + redimensionnement : on ne compare pas pixel-à-pixel
mais une GRILLE de patchs (chaque image est réduite à n×m cellules, ce qui
moyenne les blocs et tolère un léger décalage de cadrage).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import List, Tuple

from PIL import Image

# ─────────────────────────── seuils de verdict ───────────────────────────
# Calés sur les budgets d'erreur des référentiels de numérisation patrimoniale,
# transposés à la DÉRIVE D'ÉDITION (master musée → notre sortie). Sources :
#   • FADGI 3e éd. (2023), ΔE2000 : 4★ moyen ~2-3 / max ~6 ; 3★ moyen <3 / p90 ~7.
#   • Metamorfoze 2.0 (2025), ΔE2000 : Full moyen ≤3-4 / max ≤7-10 ; Light ≤4-5.
#   • Neutralité (balance des blancs) Metamorfoze : ΔE(ab) ≤3 Full/Light, ≤5 Extra.
#   → Un édit qui dépasse la tolérance d'une chaîne de capture 3★/Full n'est plus
#     « fidèle ». Détail + URLs dans docs/restauration-politique.md.
# ΔE = CIEDE2000. Séparation empirique vérifiée : masters gray-world ΔE≈9-13 (REJET),
# masters fidélité-d'abord ΔE≈1-3 (FIDÈLE).
SEUIL_DELTA_E_MOYEN_OK = 3.0      # ≤ : fidèle (budget FADGI 4★ / Metamorfoze Full)
SEUIL_DELTA_E_MOYEN_REVOIR = 6.0  # ]OK, REVOIR] : revue humaine ; au-delà : infidèle
SEUIL_DELTA_E_P95 = 10.0          # queue de distribution (≈ max FADGI/Metamorfoze)
SEUIL_DELTA_E_MAX = 15.0          # un patch très au-dessus = dérive locale franche
# Neutralisation de dominante : C* global après / avant. < seuil = palette délavée.
SEUIL_CHROMA_RATIO_REVOIR = 0.93
SEUIL_CHROMA_RATIO_INFIDELE = 0.85
# Recentrage du nuage a*/b* global vers le gris = signature du gray-world
# (la « dominante » voulue par l'artiste est effacée).
SEUIL_DOMINANTE_RATIO_REVOIR = 0.88
SEUIL_DOMINANTE_RATIO_INFIDELE = 0.80
# Un patch « délavé » a perdu plus de ce % de sa chroma.
SEUIL_PERTE_CHROMA_PATCH = 0.25
# Le ratio de chroma seul est instable sur les œuvres peu colorées (gravure, sépia) :
# un infime écart absolu y produit un grand écart de ratio. On n'escalade sur la
# chroma que si la PERTE ABSOLUE moyenne de C* est significative — un vrai délavage
# perd 4-6 unités (Manet/Caillebotte), une gravure fidèle perd ~1. Robuste sans
# dépendre d'un seuil de chroma absolue ajusté sur une seule œuvre.
SEUIL_PERTE_CHROMA_ABS = 2.0
# Marge ignorée sur chaque bord avant comparaison (absorbe le bord de scan rogné).
MARGE_IGNOREE = 0.03

# Noms canoniques des métriques ΔE (CIE76 = ΔE*ab ; CIEDE2000 = ΔE00). « CIEDE76 »
# n'existe pas → mapping explicite plutôt qu'un préfixe mécanique.
_NOMS_METHODE = {"2000": "ciede2000", "76": "cie76"}


# ─────────────────────────── sRGB → CIELAB ───────────────────────────
# Constantes canoniques (Bruce Lindbloom, http://www.brucelindbloom.com).
# Matrice sRGB(D65) linéaire → XYZ ; blanc de référence D65.
_M = (
    (0.4124564, 0.3575761, 0.1804375),
    (0.2126729, 0.7151522, 0.0721750),
    (0.0193339, 0.1191920, 0.9503041),
)
_XN, _YN, _ZN = 0.95047, 1.00000, 1.08883  # D65, échelle Y=1
_EPS = 216.0 / 24389.0   # (6/29)^3
_KAP = 24389.0 / 27.0    # (29/3)^3

# LUT sRGB 8 bits → linéaire (256 entrées, calculée une fois).
_LIN = [
    (c / 12.92) if c <= 0.04045 else (((c + 0.055) / 1.055) ** 2.4)
    for c in (i / 255.0 for i in range(256))
]


def _f(t: float) -> float:
    return t ** (1.0 / 3.0) if t > _EPS else (_KAP * t + 16.0) / 116.0


def rgb_to_lab(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """sRGB 8 bits (0-255) → CIELAB (L*, a*, b*), blanc D65."""
    r, g, b = _LIN[rgb[0]], _LIN[rgb[1]], _LIN[rgb[2]]
    x = _M[0][0] * r + _M[0][1] * g + _M[0][2] * b
    y = _M[1][0] * r + _M[1][1] * g + _M[1][2] * b
    z = _M[2][0] * r + _M[2][1] * g + _M[2][2] * b
    fx, fy, fz = _f(x / _XN), _f(y / _YN), _f(z / _ZN)
    return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))


# ─────────────────────────── ΔE ───────────────────────────

def delta_e_76(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    """ΔE*ab (CIE76) — distance euclidienne en Lab."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def delta_e_2000(lab1: Tuple[float, float, float],
                 lab2: Tuple[float, float, float],
                 kl: float = 1.0, kc: float = 1.0, kh: float = 1.0) -> float:
    """ΔE00 (CIEDE2000). Implémentation de la formule de Sharma, Wu & Dalal (2005).

    Vérifiée contre les vecteurs de test publiés dans tests/test_fidelity.py.
    """
    l1, a1, b1 = lab1
    l2, a2, b2 = lab2
    c1 = math.hypot(a1, b1)
    c2 = math.hypot(a2, b2)
    c_bar = (c1 + c2) / 2.0
    g = 0.5 * (1 - math.sqrt(c_bar ** 7 / (c_bar ** 7 + 25.0 ** 7))) if c_bar > 0 else 0.0
    a1p, a2p = (1 + g) * a1, (1 + g) * a2
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)

    def _hp(ap: float, bp: float) -> float:
        if ap == 0 and bp == 0:
            return 0.0
        h = math.degrees(math.atan2(bp, ap))
        return h + 360.0 if h < 0 else h

    h1p, h2p = _hp(a1p, b1), _hp(a2p, b2)

    dlp = l2 - l1
    dcp = c2p - c1p
    if c1p * c2p == 0:
        dhp = 0.0
    else:
        dh = h2p - h1p
        if dh > 180:
            dh -= 360
        elif dh < -180:
            dh += 360
        dhp = dh
    dHp = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dhp) / 2.0)

    lp_bar = (l1 + l2) / 2.0
    cp_bar = (c1p + c2p) / 2.0
    if c1p * c2p == 0:
        hp_bar = h1p + h2p
    else:
        if abs(h1p - h2p) > 180:
            hp_bar = (h1p + h2p + 360) / 2.0 if (h1p + h2p) < 360 else (h1p + h2p - 360) / 2.0
        else:
            hp_bar = (h1p + h2p) / 2.0

    t = (1
         - 0.17 * math.cos(math.radians(hp_bar - 30))
         + 0.24 * math.cos(math.radians(2 * hp_bar))
         + 0.32 * math.cos(math.radians(3 * hp_bar + 6))
         - 0.20 * math.cos(math.radians(4 * hp_bar - 63)))
    d_theta = 30 * math.exp(-(((hp_bar - 275) / 25.0) ** 2))
    rc = 2 * math.sqrt(cp_bar ** 7 / (cp_bar ** 7 + 25.0 ** 7)) if cp_bar > 0 else 0.0
    sl = 1 + (0.015 * (lp_bar - 50) ** 2) / math.sqrt(20 + (lp_bar - 50) ** 2)
    sc = 1 + 0.045 * cp_bar
    sh = 1 + 0.015 * cp_bar * t
    rt = -math.sin(math.radians(2 * d_theta)) * rc

    return math.sqrt(
        (dlp / (kl * sl)) ** 2
        + (dcp / (kc * sc)) ** 2
        + (dHp / (kh * sh)) ** 2
        + rt * (dcp / (kc * sc)) * (dHp / (kh * sh))
    )


# ─────────────────────────── grille de patchs ───────────────────────────

def _dims_grille(taille: Tuple[int, int], n_long: int) -> Tuple[int, int]:
    """(cols, rows) pour une grille dont le côté long fait n_long cellules.

    ``n_long`` est borné à ≥ 2 (un 0/négatif accidentel dégrade au lieu de lever
    une erreur Pillow cryptique sur le resize)."""
    n_long = max(2, int(n_long))
    w, h = taille
    if w >= h:
        return n_long, max(1, round(n_long * h / w))
    return max(1, round(n_long * w / h)), n_long


def _recadrer_marge(img: Image.Image, marge: float) -> Image.Image:
    """Rogne ``marge`` (fraction) sur chaque bord — absorbe le bord de scan rogné
    côté master pour que les deux grilles s'alignent."""
    if marge <= 0:
        return img
    w, h = img.size
    dx, dy = int(w * marge), int(h * marge)
    return img.crop((dx, dy, w - dx, h - dy))


def _grille_lab(img: Image.Image, cols: int, rows: int) -> List[List[Tuple[float, float, float]]]:
    """Réduit l'image à la grille EXACTE cols×rows (BOX = vraie moyenne de bloc,
    robuste au resampling), convertie en Lab. La grille est imposée pour que les
    deux images comparées partagent la même structure même si leur cadrage diffère."""
    petite = img.convert("RGB").resize((cols, rows), Image.BOX)
    px = petite.load()
    return [[rgb_to_lab(px[c, r]) for c in range(cols)] for r in range(rows)]


# ─────────────────────────── rapport ───────────────────────────

@dataclass
class RapportFidelite:
    """Verdict chiffré de la dérive colorimétrique original → traité."""

    delta_e_moyen: float
    delta_e_p95: float
    delta_e_max: float
    region_max: Tuple[float, float]   # position normalisée (x, y) du pire patch
    chroma_ratio: float               # C* moyen traité / original (1.0 = conservé)
    dominante_ratio: float            # |a*,b*| global traité / original
    derive_teinte_deg: float          # |Δteinte| moyen pondéré par la chroma
    patchs_delaves: int               # nb de cellules ayant perdu > seuil de chroma
    n_patchs: int
    methode: str
    verdict: str                      # FIDÈLE | À REVOIR | INFIDÈLE
    raisons: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.verdict == "FIDÈLE"

    def to_dict(self) -> dict:
        return asdict(self)


def auditer_fidelite(original: Image.Image, traite: Image.Image, *,
                     n_grille: int = 48, methode: str = "2000") -> RapportFidelite:
    """Compare ``traite`` à ``original`` (vérité terrain) et rend un verdict.

    Indépendant du recadrage/redimensionnement : comparaison sur grille de patchs.
    """
    orig = _recadrer_marge(original, MARGE_IGNOREE)
    trai = _recadrer_marge(traite, MARGE_IGNOREE)
    cols, rows = _dims_grille(orig.size, n_grille)  # grille commune imposée
    g_or = _grille_lab(orig, cols, rows)
    g_tr = _grille_lab(trai, cols, rows)
    de = delta_e_2000 if methode == "2000" else delta_e_76

    deltas: List[float] = []
    sum_c_or = sum_c_tr = 0.0
    sum_a_or = sum_b_or = sum_a_tr = sum_b_tr = 0.0
    sum_hue = poids_hue = 0.0
    delaves = 0
    worst = (0.0, (0.0, 0.0))

    for r in range(rows):
        for c in range(cols):
            lo, ao, bo = g_or[r][c]
            lt, at, bt = g_tr[r][c]
            d = de((lo, ao, bo), (lt, at, bt))
            deltas.append(d)
            if d > worst[0]:
                worst = (d, ((c + 0.5) / cols, (r + 0.5) / rows))
            c_or, c_tr = math.hypot(ao, bo), math.hypot(at, bt)
            sum_c_or += c_or
            sum_c_tr += c_tr
            sum_a_or += ao; sum_b_or += bo
            sum_a_tr += at; sum_b_tr += bt
            if c_or > 1.0 and (c_or - c_tr) / c_or > SEUIL_PERTE_CHROMA_PATCH:
                delaves += 1
            # dérive de teinte pondérée par la chroma d'origine (ignore les gris)
            if c_or > 3.0 and c_tr > 0.0:
                ho = math.degrees(math.atan2(bo, ao))
                ht = math.degrees(math.atan2(bt, at))
                dh = abs((ht - ho + 180) % 360 - 180)
                sum_hue += dh * c_or
                poids_hue += c_or

    n = len(deltas)
    deltas.sort()
    moyen = sum(deltas) / n
    p95 = deltas[min(n - 1, int(0.95 * n))]
    chroma_ratio = (sum_c_tr / sum_c_or) if sum_c_or > 0 else 1.0
    dom_or = math.hypot(sum_a_or / n, sum_b_or / n)
    dom_tr = math.hypot(sum_a_tr / n, sum_b_tr / n)
    dominante_ratio = (dom_tr / dom_or) if dom_or > 0.5 else 1.0
    derive_teinte = (sum_hue / poids_hue) if poids_hue > 0 else 0.0
    # Perte absolue moyenne de chroma (garde-fou contre les faux positifs de ratio
    # sur les œuvres peu colorées).
    perte_chroma_abs = (sum_c_or - sum_c_tr) / n

    # ── verdict ──
    raisons: List[str] = []
    verdict = "FIDÈLE"

    def _aggraver(niveau: str) -> None:
        nonlocal verdict
        ordre = {"FIDÈLE": 0, "À REVOIR": 1, "INFIDÈLE": 2}
        if ordre[niveau] > ordre[verdict]:
            verdict = niveau

    if moyen > SEUIL_DELTA_E_MOYEN_REVOIR:
        _aggraver("INFIDÈLE"); raisons.append(f"ΔE moyen {moyen:.1f} > {SEUIL_DELTA_E_MOYEN_REVOIR} (dérive globale)")
    elif moyen > SEUIL_DELTA_E_MOYEN_OK:
        _aggraver("À REVOIR"); raisons.append(f"ΔE moyen {moyen:.1f} > {SEUIL_DELTA_E_MOYEN_OK}")
    if p95 > SEUIL_DELTA_E_P95:
        _aggraver("À REVOIR"); raisons.append(f"ΔE p95 {p95:.1f} > {SEUIL_DELTA_E_P95} (queue de dérive)")
    if worst[0] > SEUIL_DELTA_E_MAX:
        _aggraver("À REVOIR")
        raisons.append(f"patch à ΔE {worst[0]:.1f} en ({worst[1][0]:.2f},{worst[1][1]:.2f})")
    # Délavage de chroma : seulement si la perte ABSOLUE est significative (évite
    # les faux positifs sur gravures/sépia où le ratio bouge sans enjeu visible).
    if perte_chroma_abs >= SEUIL_PERTE_CHROMA_ABS:
        if chroma_ratio < SEUIL_CHROMA_RATIO_INFIDELE:
            _aggraver("INFIDÈLE"); raisons.append(f"chroma délavée à {chroma_ratio*100:.0f}% de l'original")
        elif chroma_ratio < SEUIL_CHROMA_RATIO_REVOIR:
            _aggraver("À REVOIR"); raisons.append(f"chroma réduite à {chroma_ratio*100:.0f}%")
    # Neutralisation d'une dominante (gray-world) : dom_or>0.5 garde déjà les neutres.
    if dominante_ratio < SEUIL_DOMINANTE_RATIO_INFIDELE:
        _aggraver("INFIDÈLE")
        raisons.append(f"dominante chromatique neutralisée ({dominante_ratio*100:.0f}% conservée — signature gray-world)")
    elif dominante_ratio < SEUIL_DOMINANTE_RATIO_REVOIR:
        _aggraver("À REVOIR")
        raisons.append(f"dominante chromatique atténuée ({dominante_ratio*100:.0f}% conservée)")
    if not raisons:
        raisons.append(f"ΔE moyen {moyen:.1f}, chroma {chroma_ratio*100:.0f}% — conforme")

    return RapportFidelite(
        delta_e_moyen=round(moyen, 2),
        delta_e_p95=round(p95, 2),
        delta_e_max=round(worst[0], 2),
        region_max=(round(worst[1][0], 3), round(worst[1][1], 3)),
        chroma_ratio=round(chroma_ratio, 3),
        dominante_ratio=round(dominante_ratio, 3),
        derive_teinte_deg=round(derive_teinte, 1),
        patchs_delaves=delaves,
        n_patchs=n,
        methode=_NOMS_METHODE.get(methode, methode),
        verdict=verdict,
        raisons=raisons,
    )


def formater_rapport(r: RapportFidelite) -> str:
    """Rendu lisible pour la CLI / les logs."""
    icone = {"FIDÈLE": "✓", "À REVOIR": "⚠", "INFIDÈLE": "✗"}[r.verdict]
    lignes = [
        f"  {icone} fidélité : {r.verdict}",
        f"    ΔE {r.methode} : moyen {r.delta_e_moyen} · p95 {r.delta_e_p95} · max {r.delta_e_max}",
        f"    chroma conservée {r.chroma_ratio*100:.0f}% · dominante {r.dominante_ratio*100:.0f}%"
        f" · dérive teinte {r.derive_teinte_deg}° · patchs délavés {r.patchs_delaves}/{r.n_patchs}",
    ]
    for raison in r.raisons:
        lignes.append(f"    – {raison}")
    return "\n".join(lignes)
