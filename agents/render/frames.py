"""Encadrement réaliste en Pillow pur.

Produit une pièce encadrée (cadre + marie-louise + œuvre + reflet de verre)
qui tient la comparaison « galerie ». Les moulures ont une coupe d'onglet
(corners à 45°), un biseau directionnel (lumière haut-gauche), un veinage
bois pour chêne/noyer, et une ombre portée pour le compositing en scène.

Profils alignés sur le catalogue Gelato/Prodigi (chêne, noir, blanc, noyer)
+ un profil « or » pour la ligne signature Prodigi.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Tuple

from PIL import Image, ImageDraw, ImageFilter

RGB = Tuple[int, int, int]


@dataclass
class ProfilCadre:
    nom: str
    base: RGB            # couleur principale de la moulure
    veinage: RGB | None  # couleur des veines bois (None = pas de veinage)
    largeur_frac: float  # largeur du cadre en fraction du petit côté de l'œuvre
    marie_louise: RGB    # couleur du passe-partout (mat)
    sheen: float         # brillance du biseau (0 mat → 1 brillant)


PROFILS: dict[str, ProfilCadre] = {
    "chene":  ProfilCadre("chêne",  (181, 146, 96),  (150, 116, 70),  0.060, (244, 240, 230), 0.45),
    "noyer":  ProfilCadre("noyer",  (78, 52, 33),    (54, 34, 20),    0.060, (244, 240, 230), 0.40),
    "noir":   ProfilCadre("noir",   (28, 26, 24),    None,            0.050, (244, 240, 230), 0.30),
    "blanc":  ProfilCadre("blanc",  (242, 240, 234), None,            0.050, (250, 248, 243), 0.25),
    "or":     ProfilCadre("or",     (176, 141, 74),  (150, 116, 60),  0.055, (247, 243, 233), 0.70),
}


def _eclaircir(c: RGB, k: float) -> RGB:
    return tuple(max(0, min(255, int(round(v + (255 - v) * k)))) for v in c)  # type: ignore


def _assombrir(c: RGB, k: float) -> RGB:
    return tuple(max(0, min(255, int(round(v * (1 - k))))) for v in c)  # type: ignore


def _dessiner_moulure(draw: ImageDraw.ImageDraw, boite: Tuple[int, int, int, int],
                      fw: int, profil: ProfilCadre) -> None:
    """Dessine la moulure entre le rectangle extérieur ``boite`` et l'ouverture intérieure.

    Anneaux concentriques (coins à 45° automatiques) + biseau directionnel via
    4 trapèzes d'accent (haut/gauche clairs, bas/droit sombres).
    """
    x0, y0, x1, y1 = boite

    # 1) Face de la moulure : anneaux concentriques avec une courbe de brillance douce
    for t in range(fw):
        p = t / max(1, fw - 1)            # 0 = bord extérieur, 1 = bord intérieur
        # léger creux au centre puis remontée (profil de moulure « scotia »)
        courbe = 1.0 - 0.5 * (1 - abs(2 * p - 1))
        k = (courbe - 0.5) * profil.sheen
        couleur = _eclaircir(profil.base, max(0, k)) if k >= 0 else _assombrir(profil.base, -k)
        draw.rectangle([x0 + t, y0 + t, x1 - t, y1 - t], outline=couleur, width=1)

    # 2) Biseau directionnel : accents clairs en haut/gauche, sombres en bas/droite
    haut = _eclaircir(profil.base, 0.22)
    gauche = _eclaircir(profil.base, 0.12)
    bas = _assombrir(profil.base, 0.28)
    droite = _assombrir(profil.base, 0.18)
    draw.line([(x0, y0), (x1, y0)], fill=haut, width=2)
    draw.line([(x0, y0), (x0, y1)], fill=gauche, width=2)
    draw.line([(x0, y1), (x1, y1)], fill=bas, width=2)
    draw.line([(x1, y0), (x1, y1)], fill=droite, width=2)
    # creux intérieur (la moulure « descend » vers la marie-louise)
    draw.rectangle([x0 + fw - 1, y0 + fw - 1, x1 - fw + 1, y1 - fw + 1],
                   outline=_assombrir(profil.base, 0.35), width=2)


def _veiner(img: Image.Image, boite: Tuple[int, int, int, int], fw: int, profil: ProfilCadre) -> None:
    """Ajoute un veinage bois subtil sur la zone moulure (déterministe par graine)."""
    if profil.veinage is None:
        return
    x0, y0, x1, y1 = boite
    rng = random.Random(hash(profil.nom) & 0xFFFF)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    n = int((x1 - x0) / 6)
    for _ in range(n):
        # veines horizontales sur moulures haut/bas, verticales sur gauche/droite
        if rng.random() < 0.5:
            yy = rng.randint(y0, y1)
            d.line([(x0, yy), (x1, yy)], fill=profil.veinage + (rng.randint(10, 34),), width=1)
        else:
            xx = rng.randint(x0, x1)
            d.line([(xx, y0), (xx, y1)], fill=profil.veinage + (rng.randint(10, 34),), width=1)
    img.alpha_composite(overlay)


def _reflet_verre(img: Image.Image, ouverture: Tuple[int, int, int, int]) -> None:
    """Ajoute un reflet de verre diagonal très léger sur l'ouverture (œuvre + mat)."""
    x0, y0, x1, y1 = ouverture
    w, h = x1 - x0, y1 - y0
    reflet = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(reflet)
    # bande diagonale claire
    d.polygon([(0, int(h * 0.10)), (int(w * 0.42), 0), (int(w * 0.62), 0), (0, int(h * 0.42))],
              fill=(255, 255, 255, 16))
    d.polygon([(int(w * 0.70), 0), (w, 0), (w, int(h * 0.22))], fill=(255, 255, 255, 9))
    reflet = reflet.filter(ImageFilter.GaussianBlur(2))
    img.alpha_composite(reflet, (x0, y0))


def encadrer(art: Image.Image, profil: str = "chene", *,
             marie_louise: bool = True, mat_frac: float = 0.10,
             verre: bool = True) -> Image.Image:
    """Encadre ``art`` et retourne une image RGBA opaque (la pièce encadrée).

    ``mat_frac`` : largeur du passe-partout en fraction du petit côté de l'œuvre.
    """
    if profil not in PROFILS:
        profil = "chene"
    p = PROFILS[profil]
    art = art.convert("RGB")
    aw, ah = art.size
    petit_cote = min(aw, ah)

    fw = max(14, int(petit_cote * p.largeur_frac))
    mw = max(0, int(petit_cote * mat_frac)) if marie_louise else 0

    W = aw + 2 * (fw + mw)
    H = ah + 2 * (fw + mw)
    piece = Image.new("RGBA", (W, H), p.base + (255,))
    draw = ImageDraw.Draw(piece)

    # Moulure
    _dessiner_moulure(draw, (0, 0, W - 1, H - 1), fw, p)
    _veiner(piece, (0, 0, W - 1, H - 1), fw, p)

    # Passe-partout (marie-louise) + biseau d'ouverture
    if mw > 0:
        draw.rectangle([fw, fw, W - fw - 1, H - fw - 1], fill=p.marie_louise)
        # ombre douce du cadre sur le mat
        draw.rectangle([fw, fw, W - fw - 1, fw + 2], fill=_assombrir(p.marie_louise, 0.08))
        draw.rectangle([fw, fw, fw + 2, H - fw - 1], fill=_assombrir(p.marie_louise, 0.06))

    # Ouverture où vit l'œuvre
    ox0, oy0 = fw + mw, fw + mw
    ox1, oy1 = ox0 + aw, oy0 + ah
    # liseré du biseau de coupe du mat
    if mw > 0:
        draw.rectangle([ox0 - 2, oy0 - 2, ox1 + 1, oy1 + 1], outline=_assombrir(p.marie_louise, 0.18), width=1)
        draw.rectangle([ox0 - 1, oy0 - 1, ox1, oy1], outline=_eclaircir(p.marie_louise, 0.5), width=1)

    piece.paste(art, (ox0, oy0))

    if verre:
        _reflet_verre(piece, (fw, fw, W - fw, H - fw))

    return piece


def ombre_portee(piece: Image.Image, decalage: Tuple[int, int] = (0, 18),
                 flou: int = 22, opacite: int = 120, marge: int = 60) -> Image.Image:
    """Retourne une image RGBA (sur marge transparente) : ombre portée + pièce.

    Utilisé pour poser l'œuvre encadrée sur un mur avec un détachement crédible.
    """
    w, h = piece.size
    toile = Image.new("RGBA", (w + 2 * marge, h + 2 * marge), (0, 0, 0, 0))

    masque = piece.split()[-1] if piece.mode == "RGBA" else Image.new("L", piece.size, 255)
    ombre = Image.new("RGBA", toile.size, (0, 0, 0, 0))
    bloc = Image.new("RGBA", piece.size, (15, 12, 9, opacite))
    ombre.paste(bloc, (marge + decalage[0], marge + decalage[1]), masque)
    ombre = ombre.filter(ImageFilter.GaussianBlur(flou))

    toile.alpha_composite(ombre)
    toile.alpha_composite(piece.convert("RGBA"), (marge, marge))
    return toile
