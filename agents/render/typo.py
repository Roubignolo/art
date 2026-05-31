"""Chargement des polices pour le rendu — sérif éditorial premium.

Cherche les polices système macOS de qualité (Didot, Baskerville, Cochin,
Hoefler, Georgia) et retombe proprement sur la police PIL par défaut si rien
n'est trouvé (CI / Linux). La marque Vellum & Cie utilise un sérif à contraste
pour le titrage et un sérif lisible pour le texte.
"""

from __future__ import annotations

import os
from typing import List, Optional

from PIL import ImageFont

# Ordres de préférence (chemins macOS + noms génériques résolus par fontconfig)
_TITRAGE: List[str] = [
    "/System/Library/Fonts/Supplemental/Didot.ttc",
    "/System/Library/Fonts/Supplemental/Baskerville.ttc",
    "/System/Library/Fonts/Supplemental/Hoefler Text.ttc",
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
]
_TEXTE: List[str] = [
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/System/Library/Fonts/Supplemental/Baskerville.ttc",
    "/System/Library/Fonts/Supplemental/Cochin.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
]
_TITRAGE_GRAS: List[str] = [
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/System/Library/Fonts/Supplemental/Baskerville.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
]


def _premier_existant(chemins: List[str]) -> Optional[str]:
    for c in chemins:
        if os.path.exists(c):
            return c
    return None


def _charger(chemins: List[str], taille: int) -> ImageFont.FreeTypeFont:
    chemin = _premier_existant(chemins)
    if chemin:
        try:
            return ImageFont.truetype(chemin, taille)
        except Exception:
            pass
    try:
        return ImageFont.truetype("DejaVuSerif.ttf", taille)
    except Exception:
        return ImageFont.load_default()


def charger_police(taille: int, role: str = "texte") -> ImageFont.FreeTypeFont:
    if role == "titrage":
        return _charger(_TITRAGE, taille)
    if role == "gras":
        return _charger(_TITRAGE_GRAS, taille)
    return _charger(_TEXTE, taille)
