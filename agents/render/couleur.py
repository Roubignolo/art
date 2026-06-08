"""Gestion colorimétrique (ICC) — séparée de l'audit de fidélité.

Deux responsabilités, toutes deux au service de « le tirage = l'original » :

1. `assurer_srgb` — garantit que le master livré est en **sRGB** (l'espace attendu
   par les RIP de Gelato/Prodigi). Si la source porte un profil ICC ≠ sRGB
   (Adobe RGB, ProPhoto…), conversion ICC-managée *qui préserve l'apparence*
   (rendu colorimétrique relatif + compensation de point noir). C'est l'INVERSE
   d'une correction esthétique : on ne change pas l'intention, on la transporte
   fidèlement dans l'espace de livraison. Sources : doc Gelato (« use sRGB images »,
   « tag with sRGB »), Prodigi (« work in RGB », ne pas embarquer leur profil),
   color.org (BPC). Cf. docs/restauration-politique.md.

2. `rapport_gamut` — **soft-proof informatif** : quelles couleurs profondes (les
   bleus de Cézanne !) risquent l'écrêtage à l'impression. Avec un profil papier
   (`--profil-papier`, Hahnemühle/Prodigi téléchargeables) → vrai soft-proof ICC
   (aller-retour sRGB→papier→sRGB, ΔE2000). Sans profil → pré-écran heuristique
   par chroma, explicitement marqué approximatif. JAMAIS une correction : on
   N'écrête PAS nous-mêmes (c'est le RIP du POD qui mappe vers le papier) — on
   informe l'humain pour le choix du papier (mat < gamut < baryté/toile).

100 % local, Pillow + lcms2 (déjà embarqué dans Pillow).
"""

from __future__ import annotations

import io
import math
import os
from typing import Dict, Optional, Tuple

from PIL import Image, ImageCms

from .fidelity import _dims_grille, _grille_lab, _recadrer_marge, delta_e_2000

# Profil sRGB de référence, construit une fois.
_SRGB = ImageCms.createProfile("sRGB")
_INTENT_REL = ImageCms.Intent.RELATIVE_COLORIMETRIC
_BPC = ImageCms.Flags.BLACKPOINTCOMPENSATION


def srgb_icc_bytes() -> bytes:
    """Octets du profil sRGB — pour taguer les fichiers livrés (consigne Gelato)."""
    return ImageCms.ImageCmsProfile(_SRGB).tobytes()


_ICC_SRGB = srgb_icc_bytes()


def _est_srgb(desc: str) -> bool:
    return "srgb" in desc.lower()


def assurer_srgb(img: Image.Image) -> Tuple[Image.Image, Dict]:
    """Garantit une image RGB en espace sRGB (gestion ICC).

    Retourne (image_rgb_srgb, infos) où infos = {espace_source, converti}.
      • aucun profil embarqué → supposé sRGB (convention web), pas de conversion.
      • profil sRGB → pas de conversion.
      • profil ≠ sRGB → conversion ICC relatif-colorimétrique + BPC (préserve
        l'apparence, n'écrête que le hors-gamut sRGB).
    """
    icc = img.info.get("icc_profile")
    if not icc:
        if img.mode in ("RGB", "L"):
            return img.convert("RGB"), {"espace_source": "sRGB présumé (sans profil ICC)", "converti": False}
        # Mode non-RGB sans profil (CMYK d'archive…) : le convert('RGB') de Pillow
        # n'est PAS color-managé (formule fixe, sans intent ni BPC). On l'étiquette
        # honnêtement plutôt que « sRGB présumé » (provenance couleur exacte).
        return img.convert("RGB"), {
            "espace_source": f"{img.mode} sans profil → conversion non gérée (naïve Pillow)",
            "converti": True,
        }
    try:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        desc = ImageCms.getProfileDescription(src).strip()
    except Exception:
        return img.convert("RGB"), {"espace_source": "profil ICC illisible (sRGB présumé)", "converti": False}
    if _est_srgb(desc) and img.mode == "RGB":
        return img.convert("RGB"), {"espace_source": desc, "converti": False}
    try:
        # Transformer depuis le mode NATIF (gère CMYK / niveaux de gris d'archive) ;
        # on ne « convert('RGB') » que les modes que lcms ne lit pas tels quels.
        base = img if img.mode in ("RGB", "CMYK", "L") else img.convert("RGB")
        out = ImageCms.profileToProfile(
            base, src, _SRGB,
            renderingIntent=_INTENT_REL, outputMode="RGB", flags=_BPC,
        )
        if out is not None:
            return out.convert("RGB"), {"espace_source": desc, "converti": True}
    except Exception as e:  # pragma: no cover - dépend du profil/mode
        return img.convert("RGB"), {"espace_source": f"{desc} (conversion échouée: {e})", "converti": False}
    return img.convert("RGB"), {"espace_source": desc, "converti": False}


def taguer_srgb() -> bytes:
    """Octets sRGB à passer à Image.save(icc_profile=...) pour les fichiers livrés."""
    return _ICC_SRGB


# ──────────────────────── soft-proof / gamut ────────────────────────

_FAMILLES = [
    (0, "rouge"), (30, "orange"), (60, "jaune"), (110, "vert"),
    (160, "cyan"), (200, "bleu-cyan"), (250, "bleu"), (290, "violet"),
    (330, "magenta"), (360, "rouge"),
]


def _famille_teinte(h_deg: float) -> str:
    h = h_deg % 360
    for borne, nom in _FAMILLES:
        if h <= borne:
            return nom
    return "rouge"


def _petit(img: Image.Image, long_edge: int = 800) -> Image.Image:
    if max(img.size) <= long_edge:
        return img.convert("RGB")
    f = long_edge / max(img.size)
    return img.convert("RGB").resize((round(img.width * f), round(img.height * f)), Image.LANCZOS)


def rapport_gamut(master_srgb: Image.Image, *, profil_papier: Optional[str] = None,
                  n_grille: int = 48, seuil_de: float = 2.0,
                  seuil_chroma: float = 55.0) -> Dict:
    """Soft-proof informatif (jamais une correction).

    Avec ``profil_papier`` (chemin .icc) : vrai soft-proof ICC — aller-retour
    sRGB→papier→sRGB (relatif + BPC) et ΔE2000 par patch ; les pixels qui bougent
    (> ``seuil_de``) sont hors-gamut papier. Sans profil : heuristique de chroma
    (C* élevée = à risque sur mat), explicitement approximative.
    """
    petit = _petit(master_srgb)
    cols, rows = _dims_grille(petit.size, n_grille)
    g_master = _grille_lab(petit, cols, rows)

    if profil_papier and os.path.exists(profil_papier):
        try:
            paper = ImageCms.getOpenProfile(profil_papier)
            desc = ImageCms.getProfileDescription(paper).strip()
            proofed = ImageCms.profileToProfile(petit, _SRGB, paper, renderingIntent=_INTENT_REL, outputMode="RGB", flags=_BPC)
            back = ImageCms.profileToProfile(proofed, paper, _SRGB, renderingIntent=_INTENT_REL, outputMode="RGB", flags=_BPC)
            g_proof = _grille_lab(back, cols, rows)
            oog = 0
            worst = (0.0, (0.0, 0.0), "—")
            for r in range(rows):
                for c in range(cols):
                    d = delta_e_2000(g_master[r][c], g_proof[r][c])
                    if d > seuil_de:
                        oog += 1
                    if d > worst[0]:
                        a, b = g_master[r][c][1], g_master[r][c][2]
                        worst = (d, ((c + 0.5) / cols, (r + 0.5) / rows),
                                 _famille_teinte(math.degrees(math.atan2(b, a))))
            n = cols * rows
            return {
                "methode": "icc-softproof",
                "profil_papier": desc,
                "hors_gamut_pct": round(100 * oog / n, 1),
                "delta_e_max": round(worst[0], 2),
                "region_max": (round(worst[1][0], 3), round(worst[1][1], 3)),
                "teinte_a_risque": worst[2],
                "note": "ΔE2000 sRGB↔papier (relatif+BPC). Le RIP du POD fait le mapping final ; aperçu seulement.",
            }
        except Exception as e:  # pragma: no cover - dépend du profil fourni
            note_icc = f"profil papier inexploitable ({e}) → repli heuristique"
    else:
        note_icc = None

    # Heuristique chroma (pas de profil papier) : repère les zones très saturées.
    chromas = []
    worst = (0.0, (0.0, 0.0), "—")
    for r in range(rows):
        for c in range(cols):
            _, a, b = g_master[r][c]
            cstar = math.hypot(a, b)
            chromas.append(cstar)
            if cstar > worst[0]:
                worst = (cstar, ((c + 0.5) / cols, (r + 0.5) / rows),
                         _famille_teinte(math.degrees(math.atan2(b, a))))
    chromas.sort()
    n = len(chromas)
    p99 = chromas[min(n - 1, int(0.99 * n))]
    pct = round(100 * sum(1 for x in chromas if x > seuil_chroma) / n, 1)
    note = "Approximatif (pas de profil papier). Fournir --profil-papier (Hahnemühle/Prodigi) pour un soft-proof ICC exact. Sur mat, les zones très saturées seront partiellement écrêtées par le RIP."
    if note_icc:
        note = note_icc + " · " + note
    return {
        "methode": "heuristique-chroma",
        "chroma_max": round(worst[0], 1),
        "chroma_p99": round(p99, 1),
        "pct_chroma_elevee": pct,
        "seuil_chroma": seuil_chroma,
        "region_max": (round(worst[1][0], 3), round(worst[1][1], 3)),
        "teinte_a_risque": worst[2],
        "avertissement": "proxy de SATURATION (C*), pas une mesure de gamut papier : "
                         "non comparable d'une œuvre à l'autre, et sous-détecte l'écrêtage "
                         "des bleus/cyans clairs. Fournir --profil-papier pour un vrai soft-proof.",
        "note": note,
    }
