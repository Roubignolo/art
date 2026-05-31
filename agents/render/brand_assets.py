"""Assets de marque Vellum & Cie — bannière Etsy, icône boutique, logotype.

Génère de vrais PNG prêts à uploader sur Etsy, avec la typographie premium
système (Didot/Baskerville) et la palette de marque. Réutilise le sceau
monogramme de la carte de provenance pour la cohérence.

    python -m agents.render.brand_assets --out web/public/brand
"""

from __future__ import annotations

import argparse
import os
from typing import Tuple

from PIL import Image, ImageDraw, ImageFilter

from .provenance_card import sceau
from .typo import charger_police

RGB = Tuple[int, int, int]
PAPIER: RGB = (244, 239, 230)
PAPIER2: RGB = (250, 248, 243)
ENCRE: RGB = (42, 38, 34)
ENCRE2: RGB = (107, 100, 91)
LAITON: RGB = (169, 128, 63)


def _fond_papier(taille: Tuple[int, int], couleur: RGB = PAPIER) -> Image.Image:
    """Fond papier avec vignette douce + léger grain."""
    w, h = taille
    img = Image.new("RGB", taille, couleur)
    # vignette
    masque = Image.new("L", taille, 0)
    d = ImageDraw.Draw(masque)
    d.ellipse([-w * 0.2, -h * 0.4, w * 1.2, h * 1.4], fill=255)
    masque = masque.filter(ImageFilter.GaussianBlur(min(w, h) // 5))
    sombre = Image.new("RGB", taille, tuple(int(c * 0.93) for c in couleur))  # type: ignore
    return Image.composite(img, sombre, masque)


def _texte_espace(d: ImageDraw.ImageDraw, xy: Tuple[int, int], texte: str, font,
                  fill: RGB, tracking: int) -> int:
    """Dessine du texte avec espacement (letter-spacing) manuel. Retourne la largeur."""
    x, y = xy
    for ch in texte:
        d.text((x, y), ch, font=font, fill=fill)
        bb = d.textbbox((0, 0), ch, font=font)
        x += (bb[2] - bb[0]) + tracking
    return x - xy[0] - tracking


def _largeur_espace(d: ImageDraw.ImageDraw, texte: str, font, tracking: int) -> int:
    w = 0
    for ch in texte:
        bb = d.textbbox((0, 0), ch, font=font)
        w += (bb[2] - bb[0]) + tracking
    return w - tracking


def banniere(taille: Tuple[int, int] = (1200, 300)) -> Image.Image:
    """Bannière de boutique Etsy (format recommandé 1200×300)."""
    W, H = taille
    img = _fond_papier(taille)
    d = ImageDraw.Draw(img)

    # sceau à gauche
    s = int(H * 0.62)
    img.paste(sceau(s), (int(W * 0.06), (H - s) // 2), sceau(s))

    # wordmark
    f_nom = charger_police(int(H * 0.30), role="titrage")
    tracking = int(H * 0.03)
    nom = "VELLUM"
    cie_font = charger_police(int(H * 0.16), role="titrage")
    lw = _largeur_espace(d, nom, f_nom, tracking)
    cie = "& Cie"
    lcie = d.textbbox((0, 0), cie, font=cie_font)
    bloc_w = lw + int(W * 0.02) + (lcie[2] - lcie[0])
    x0 = int(W * 0.30)
    y0 = int(H * 0.26)
    x_after = x0 + _texte_espace(d, (x0, y0), nom, f_nom, ENCRE, tracking)
    d.text((x_after + int(W * 0.015), y0 + int(H * 0.10)), cie, font=cie_font, fill=LAITON)

    # filet + baseline
    fy = int(H * 0.66)
    d.line([(x0, fy), (x0 + bloc_w, fy)], fill=LAITON, width=2)
    f_bl = charger_police(int(H * 0.085), role="texte")
    d.text((x0, fy + int(H * 0.04)), "Éditions d'art d'après les archives du domaine public",
           font=f_bl, fill=ENCRE2)
    return img


def icone(taille: int = 500) -> Image.Image:
    """Icône/logo de boutique (carré). Sceau + nom compact."""
    img = _fond_papier((taille, taille), PAPIER2)
    d = ImageDraw.Draw(img)
    s = int(taille * 0.54)
    img.paste(sceau(s), ((taille - s) // 2, int(taille * 0.09)), sceau(s))
    # taille de police ajustée pour tenir dans 84 % de la largeur, avec marge
    nom = "VELLUM & CIE"
    largeur_dispo = int(taille * 0.84)
    tps = int(taille * 0.085)
    while tps > 8:
        f = charger_police(tps, role="titrage")
        tracking = max(1, int(tps * 0.16))
        lw = _largeur_espace(d, nom, f, tracking)
        if lw <= largeur_dispo:
            break
        tps -= 2
    _texte_espace(d, ((taille - lw) // 2, int(taille * 0.76)), nom, f, ENCRE, tracking)
    return img


def logo(taille: Tuple[int, int] = (1600, 520), fond: str = "transparent") -> Image.Image:
    """Logotype horizontal (sceau + wordmark). Fond transparent ou papier."""
    W, H = taille
    if fond == "papier":
        img = _fond_papier(taille).convert("RGBA")
    else:
        img = Image.new("RGBA", taille, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = int(H * 0.82)
    img.alpha_composite(sceau(s), (int(W * 0.02), (H - s) // 2))

    f_nom = charger_police(int(H * 0.40), role="titrage")
    cie_font = charger_police(int(H * 0.22), role="titrage")
    tracking = int(H * 0.035)
    x0 = int(W * 0.30)
    y0 = int(H * 0.18)
    x_after = x0 + _texte_espace(d, (x0, y0), "VELLUM", f_nom, ENCRE, tracking)
    d.text((x_after + int(W * 0.012), y0 + int(H * 0.14)), "& Cie", font=cie_font, fill=LAITON)
    fy = int(H * 0.70)
    f_bl = charger_police(int(H * 0.10), role="texte")
    d.line([(x0, fy), (int(W * 0.95), fy)], fill=LAITON, width=2)
    d.text((x0, fy + int(H * 0.05)), "ÉDITIONS D'ART · DOMAINE PUBLIC", font=f_bl, fill=ENCRE2)
    return img


def generer_tout(dossier: str) -> dict:
    os.makedirs(dossier, exist_ok=True)
    chemins = {}
    banniere().save(os.path.join(dossier, "banniere-etsy-1200x300.png"))
    chemins["banniere"] = os.path.join(dossier, "banniere-etsy-1200x300.png")
    icone().save(os.path.join(dossier, "icone-boutique-500.png"))
    chemins["icone"] = os.path.join(dossier, "icone-boutique-500.png")
    logo().save(os.path.join(dossier, "logo.png"))
    chemins["logo"] = os.path.join(dossier, "logo.png")
    logo(fond="papier").save(os.path.join(dossier, "logo-papier.png"))
    chemins["logo_papier"] = os.path.join(dossier, "logo-papier.png")
    sceau(600).save(os.path.join(dossier, "sceau.png"))
    chemins["sceau"] = os.path.join(dossier, "sceau.png")
    return chemins


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Génère les assets de marque Vellum & Cie")
    ap.add_argument("--out", default="web/public/brand", help="dossier de sortie")
    args = ap.parse_args()
    res = generer_tout(args.out)
    for k, v in res.items():
        print(f"  ✓ {k}: {v}")
