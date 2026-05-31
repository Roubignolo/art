"""Carte de provenance A6 (recto/verso) — l'insert physique signature.

Glissée dans chaque colis (cf. docs/process-vente-production.md §6), elle porte
une valeur perçue énorme pour le positionnement premium : recto = l'œuvre + sa
fiche d'origine + QR vers le musée ; verso = sceau de marque + remerciement.

Rendu A6 à 300 DPI (1240×1748 px). QR réel si la lib ``qrcode`` est présente,
sinon un sceau monogramme élégant (jamais de faux QR non scannable).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple

from PIL import Image, ImageDraw

from .typo import charger_police

RGB = Tuple[int, int, int]
PAPIER: RGB = (244, 239, 230)
PAPIER2: RGB = (250, 248, 243)
ENCRE: RGB = (42, 38, 34)
ENCRE2: RGB = (107, 100, 91)
LAITON: RGB = (169, 128, 63)

A6_300 = (1240, 1748)


@dataclass
class InfosProvenance:
    titre: str
    artiste: str
    dates_artiste: str          # ex. "1853–1890"
    date_oeuvre: str            # ex. "1889"
    medium: str                 # ex. "Huile sur toile"
    institution: str            # ex. "The Metropolitan Museum of Art"
    numero_accession: str       # ex. "1993.132"
    url_musee: str              # cible du QR
    marque: str = "Vellum & Cie"
    baseline: str = "Éditions d'art d'après les archives du domaine public"
    url_boutique: str = "etsy.com/shop/VellumEtCie"


def _centrer(d: ImageDraw.ImageDraw, texte: str, font, y: int, largeur: int,
             fill: RGB = ENCRE, x0: int = 0) -> int:
    bb = d.textbbox((0, 0), texte, font=font)
    tw = bb[2] - bb[0]
    d.text((x0 + (largeur - tw) // 2, y), texte, font=font, fill=fill)
    return y + (bb[3] - bb[1])


def _filet(d: ImageDraw.ImageDraw, y: int, largeur: int, marge: int, couleur: RGB = LAITON,
           epaisseur: int = 2, orn: bool = True) -> None:
    d.line([(marge, y), (largeur - marge, y)], fill=couleur, width=epaisseur)
    if orn:
        cx = largeur // 2
        d.ellipse([cx - 5, y - 5, cx + 5, y + 5], fill=PAPIER, outline=couleur, width=2)
        d.ellipse([cx - 2, y - 2, cx + 2, y + 2], fill=couleur)


def _qr(data: str, taille: int) -> Optional[Image.Image]:
    """QR réel si la lib qrcode est installée, sinon None (→ sceau de repli)."""
    try:
        import qrcode  # type: ignore

        qr = qrcode.QRCode(border=2, box_size=10)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=(42, 38, 34), back_color=(250, 248, 243)).convert("RGB")
        return img.resize((taille, taille), Image.NEAREST)
    except Exception:
        return None


def sceau(taille: int, marque: str = "V&C") -> Image.Image:
    """Sceau monogramme dans un cartouche ovale (codes de l'ex-libris / tampon d'archive)."""
    img = Image.new("RGBA", (taille, taille), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = int(taille * 0.06)
    # double ovale
    d.ellipse([m, m, taille - m, taille - m], outline=LAITON, width=max(2, taille // 90))
    m2 = int(taille * 0.11)
    d.ellipse([m2, m2, taille - m2, taille - m2], outline=LAITON, width=max(1, taille // 160))
    # monogramme
    police = charger_police(int(taille * 0.34), role="titrage")
    bb = d.textbbox((0, 0), marque, font=police)
    d.text(((taille - (bb[2] - bb[0])) // 2, (taille - (bb[3] - bb[1])) // 2 - bb[1]),
           marque, font=police, fill=ENCRE)
    # petits losanges latéraux (dessinés — pas de glyphe ✦ qui rend en tofu)
    r = max(2, int(taille * 0.022))
    cy = taille // 2
    for signe in (1, -1):
        cx = taille // 2 + int(taille * 0.31 * signe)
        d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=LAITON)
    return img


def recto(infos: InfosProvenance, vignette: Optional[Image.Image] = None,
          taille: Tuple[int, int] = A6_300) -> Image.Image:
    W, H = taille
    carte = Image.new("RGB", taille, PAPIER)
    d = ImageDraw.Draw(carte)
    marge = int(W * 0.085)

    # cadre fin
    d.rectangle([marge // 2, marge // 2, W - marge // 2, H - marge // 2], outline=LAITON, width=2)

    # eyebrow marque
    eb = charger_police(int(W * 0.035), role="titrage")
    y = int(H * 0.06)
    y = _centrer(d, infos.marque.upper(), eb, y, W, LAITON) + int(H * 0.012)
    _filet(d, y, W, marge)
    y += int(H * 0.03)

    # vignette de l'œuvre
    if vignette is not None:
        vmax = int(W * 0.62)
        v = vignette.convert("RGB")
        f = vmax / max(v.size)
        v = v.resize((round(v.width * f), round(v.height * f)), Image.LANCZOS)
        vx = (W - v.width) // 2
        d.rectangle([vx - 6, y - 6, vx + v.width + 6, y + v.height + 6], outline=(150, 130, 95), width=3)
        carte.paste(v, (vx, y))
        y += v.height + int(H * 0.035)

    # titre + artiste
    f_titre = charger_police(int(W * 0.062), role="titrage")
    y = _centrer(d, infos.titre, f_titre, y, W, ENCRE) + int(H * 0.018)
    f_art = charger_police(int(W * 0.040), role="texte")
    artiste = f"{infos.artiste} ({infos.dates_artiste})" if infos.dates_artiste else infos.artiste
    y = _centrer(d, artiste, f_art, y, W, ENCRE2) + int(H * 0.01)
    f_meta = charger_police(int(W * 0.034), role="texte")
    meta = " · ".join([p for p in (infos.medium, infos.date_oeuvre) if p])
    if meta:
        y = _centrer(d, meta, f_meta, y, W, ENCRE2) + int(H * 0.012)

    _filet(d, y + int(H * 0.005), W, marge, orn=False, epaisseur=1, couleur=(190, 178, 160))
    y += int(H * 0.028)

    # source institutionnelle
    src = charger_police(int(W * 0.032), role="texte")
    y = _centrer(d, infos.institution, src, y, W, ENCRE)
    if infos.numero_accession:
        y = _centrer(d, f"N° d'accession {infos.numero_accession}", f_meta, y + int(H * 0.004), W, ENCRE2)

    # QR (ou sceau) + légende
    bloc = int(W * 0.22)
    q = _qr(infos.url_musee, bloc)
    by = int(H * 0.80)
    if q is not None:
        carte.paste(q, ((W - bloc) // 2, by))
        _centrer(d, "Scannez pour la fiche du musée", f_meta, by + bloc + int(H * 0.006), W, ENCRE2)
    else:
        carte.paste(sceau(bloc), ((W - bloc) // 2, by), sceau(bloc))
        _centrer(d, "Domaine public · sourced & restauré", f_meta, by + bloc + int(H * 0.006), W, ENCRE2)

    return carte


def verso(infos: InfosProvenance, taille: Tuple[int, int] = A6_300) -> Image.Image:
    W, H = taille
    carte = Image.new("RGB", taille, PAPIER2)
    d = ImageDraw.Draw(carte)
    d.rectangle([int(W * 0.04), int(W * 0.04), W - int(W * 0.04), H - int(W * 0.04)],
                outline=LAITON, width=2)

    # sceau central
    s = int(W * 0.42)
    carte.paste(sceau(s), ((W - s) // 2, int(H * 0.16)), sceau(s))

    f_nom = charger_police(int(W * 0.075), role="titrage")
    y = int(H * 0.46)
    y = _centrer(d, infos.marque, f_nom, y, W, ENCRE) + int(H * 0.02)
    f_bl = charger_police(int(W * 0.034), role="texte")
    y = _centrer(d, infos.baseline, f_bl, y, W, ENCRE2) + int(H * 0.05)

    _filet(d, y, W, int(W * 0.15))
    y += int(H * 0.03)
    f_merci = charger_police(int(W * 0.040), role="texte")
    y = _centrer(d, "Merci de faire vivre ces œuvres.", f_merci, y, W, ENCRE) + int(H * 0.03)
    f_url = charger_police(int(W * 0.034), role="titrage")
    _centrer(d, infos.url_boutique, f_url, int(H * 0.88), W, LAITON)
    return carte


def generer_carte(infos: InfosProvenance, dossier: str,
                  vignette: Optional[Image.Image] = None) -> Tuple[str, str]:
    os.makedirs(dossier, exist_ok=True)
    cr = os.path.join(dossier, "provenance_recto.png")
    cv = os.path.join(dossier, "provenance_verso.png")
    recto(infos, vignette).save(cr)
    verso(infos).save(cv)
    return cr, cv
