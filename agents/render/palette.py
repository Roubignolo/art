"""Analyse de palette — dérive les tags de TONALITÉ d'une œuvre depuis ses couleurs.

Alimente l'axe « palette » des collections (Tons orangés, Bleus profonds, Verts &
nature, Tons dorés, Sépia & neutres, Camaïeu pastel, Clair-obscur, Vif & saturé).
Réutilise la conversion CIELAB de fidelity.py (sRGB → Lab, D65). 100 % local.

Sortie : familles de teinte (histogramme pondéré par la chroma), chaleur, niveau de
saturation et de clarté, contraste, + une bande de couleurs dominantes (swatches)
pour l'affichage cockpit. Aucune invention : tout est mesuré sur les pixels.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from PIL import Image

from .fidelity import _dims_grille, _grille_lab

# Familles de teinte par secteur d'angle de teinte CIELAB (h_ab). ATTENTION : la
# roue Lab est « tournée » par rapport à la roue naïve — le bleu sRGB tombe vers
# ~300-306°, le rouge vers ~40°, le jaune vers ~100°. Bornes calées sur les
# angles Lab réels des primaires/secondaires (vérifié dans tests/test_palette).
_FAMILLES = [
    ("rose", 0, 20), ("rouge", 20, 45), ("orange", 45, 70), ("doré", 70, 105),
    ("olive", 105, 135), ("vert", 135, 175), ("turquoise", 175, 215),
    ("bleu", 215, 300), ("violet", 300, 330), ("rose", 330, 360),
]
_CHAUDES = {"rouge", "orange", "doré", "rose"}
_FROIDES = {"vert", "turquoise", "bleu", "violet"}
# « olive » (jaune-vert) est volontairement ni chaud ni froid : il ne vote pas
# pour la chaleur, qui reste un vrai marqueur rouge/orange/doré vs bleu/vert.

# Seuils (calibrés sur les 4 maîtres impressionnistes — voir tests/build_collections).
_C_NEUTRE = 8.0      # cellule sous ce C* = quasi-neutre (ignorée pour la teinte)
_C_FAIBLE = 13.0     # saturation moyenne en deçà = désaturé (sépia/neutres)
_C_VIF = 30.0        # au-delà = vif & saturé
_L_CLAIR = 68.0      # clarté moyenne au-delà = clair (pastel possible)
_L_SOMBRE = 46.0     # en deçà = sombre
_CONTRASTE = 26.0    # écart-type de L au-delà = contrasté


def _famille(h_deg: float) -> str:
    h = h_deg % 360
    for nom, lo, hi in _FAMILLES:
        if lo <= h < hi:
            return nom
    return "rouge"


def _swatches(img: Image.Image, n: int = 5) -> List[str]:
    """Couleurs dominantes (médiane-cut) en hex, par fréquence décroissante."""
    petit = img.convert("RGB")
    if max(petit.size) > 200:
        f = 200 / max(petit.size)
        petit = petit.resize((max(1, round(petit.width * f)), max(1, round(petit.height * f))))
    q = petit.quantize(colors=max(n, 6), method=Image.MEDIANCUT)
    pal = q.getpalette() or []
    couleurs = q.getcolors() or []
    out: List[str] = []
    for _count, idx in sorted(couleurs, key=lambda c: -c[0])[:n]:
        r, g, b = pal[idx * 3], pal[idx * 3 + 1], pal[idx * 3 + 2]
        out.append(f"#{r:02x}{g:02x}{b:02x}")
    return out


def analyser_palette(img: Image.Image, *, n_grille: int = 64) -> Dict:
    """Retourne la signature chromatique + les tags de palette de l'œuvre."""
    cols, rows = _dims_grille(img.size, n_grille)
    grille = _grille_lab(img, cols, rows)

    poids_famille: Dict[str, float] = {}
    poids_total = 0.0
    poids_chaud = 0.0
    somme_c = somme_l = 0.0
    ls: List[float] = []
    n = cols * rows

    for r in range(rows):
        for c in range(cols):
            l, a, b = grille[r][c]
            cstar = math.hypot(a, b)
            somme_c += cstar
            somme_l += l
            ls.append(l)
            if cstar < _C_NEUTRE:
                continue  # quasi-neutre : ne vote pas pour une teinte
            fam = _famille(math.degrees(math.atan2(b, a)))
            poids_famille[fam] = poids_famille.get(fam, 0.0) + cstar
            poids_total += cstar
            if fam in _CHAUDES:
                poids_chaud += cstar

    sat = somme_c / n
    clarte = somme_l / n
    moy_l = clarte
    contraste = math.sqrt(sum((x - moy_l) ** 2 for x in ls) / n)
    chaleur = (poids_chaud / poids_total) if poids_total > 0 else 0.5

    familles = sorted(poids_famille.items(), key=lambda kv: -kv[1])
    part = {k: v / poids_total for k, v in poids_famille.items()} if poids_total > 0 else {}
    dominante = familles[0][0] if familles else "neutre"

    tags = _tags_palette(dominante, part, chaleur, sat, clarte, contraste)

    return {
        "tags": tags,
        "famille_dominante": dominante,
        "familles": [(k, round(part[k], 3)) for k, _ in familles[:4]],
        "chaleur": round(chaleur, 3),
        "saturation": round(sat, 1),
        "clarte": round(clarte, 1),
        "contraste": round(contraste, 1),
        "swatches": _swatches(img),
    }


def _tags_palette(dominante: str, part: Dict[str, float], chaleur: float,
                  sat: float, clarte: float, contraste: float) -> List[str]:
    """Règles de nommage des collections de tonalité (1 à 3 tags).

    Le tag couleur principal exige une vraie DOMINANCE (part de chroma), pas juste
    « famille en tête » — sinon « Verts & nature » devient un fourre-tout. Les
    œuvres chaudes-mais-vertes (feuillage + sujet chaud) vont aux tons chauds.
    """
    tags: List[str] = []
    g = lambda k: part.get(k, 0.0)  # noqa: E731
    # olive (jaune-vert saturé) = feuillage → compté « nature ». turquoise = teal,
    # surtout bleu. (Les terres désaturées partent en « Sépia & neutres » plus bas.)
    vert = g("vert") + g("olive") + g("turquoise") * 0.5
    bleu = g("bleu") + g("violet") + g("turquoise") * 0.5

    if sat < _C_FAIBLE:
        # œuvre désaturée → neutre/sépia : pas de tag couleur vif, juste un lean.
        tags.append("Sépia & neutres")
        tags.append("Tons chauds" if chaleur >= 0.5 else "Tons froids")
    else:
        # œuvre colorée → un tag couleur principal par dominance nette.
        if g("orange") + g("rouge") >= 0.26:
            tags.append("Tons orangés")
        elif g("doré") >= 0.32 and chaleur >= 0.5 and vert < 0.40:
            tags.append("Tons dorés")
        elif bleu >= 0.30:
            tags.append("Bleus profonds")
        elif vert >= 0.42:
            tags.append("Verts & nature")
        elif chaleur >= 0.5:
            tags.append("Tons chauds")
        else:
            tags.append("Tons froids")
        if sat >= _C_VIF:
            tags.append("Vif & saturé")

    # Caractère tonal (cumulable).
    if clarte >= _L_CLAIR and sat < _C_VIF:
        tags.append("Camaïeu pastel")
    if contraste >= _CONTRASTE and clarte <= _L_SOMBRE:
        tags.append("Clair-obscur")

    # dédoublonne en conservant l'ordre
    vus: set = set()
    return [t for t in tags if not (t in vus or vus.add(t))]
