"""Restauration des masters — pipeline local (Pillow) + bascule Replicate.

Objectif marque : transformer un scan d'institution (parfois plat, jauni,
sous-contrasté) en un master print « valeur artistique considérable » qui
justifie le positionnement premium ET sécurise juridiquement l'usage
(cf. docs/brief-marque.md).

Pipeline local (zéro clé) :
  1. équilibrage des blancs (gray-world)
  2. autocontraste doux (préserve les hautes/basses lumières)
  3. débruitage léger préservant les bords
  4. accentuation (unsharp mask)
  5. upscale Lanczos vers la résolution print cible

Bascule optionnelle : si REPLICATE_API_TOKEN est présent, l'upscale Lanczos
est remplacé par un vrai super-résolution Real-ESRGAN (×2/×4). Sinon, on
reste 100 % local et fonctionnel.
"""

from __future__ import annotations

import io
import os
import time
from dataclasses import dataclass
from typing import Optional, Tuple

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

try:  # requests est déjà une dépendance des connecteurs sourcing
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore


@dataclass
class RapportRestauration:
    """Trace ce qui a été appliqué — utile pour l'audit et la fiche produit."""

    largeur_avant: int
    hauteur_avant: int
    largeur_apres: int
    hauteur_apres: int
    upscale_methode: str          # "aucun" | "lanczos" | "real-esrgan"
    equilibrage_blancs: bool
    debruitage: bool
    accentuation: bool

    @property
    def long_edge_apres(self) -> int:
        return max(self.largeur_apres, self.hauteur_apres)


# ───────────────────────────── chargement ─────────────────────────────

def charger(source: str) -> Image.Image:
    """Charge une image depuis un chemin local ou une URL http(s)."""
    if source.startswith("http://") or source.startswith("https://"):
        if requests is None:
            raise RuntimeError("requests indisponible pour télécharger l'image")
        rep = requests.get(source, timeout=60, headers={"User-Agent": "art-render/1.0"})
        rep.raise_for_status()
        img = Image.open(io.BytesIO(rep.content))
    else:
        img = Image.open(source)
    return img.convert("RGB")


# ───────────────────────── recadrage des bords ─────────────────────────

def rogner_bords(img: Image.Image, tol: int = 22, max_frac: float = 0.18) -> Image.Image:
    """Supprime un liseré uniforme (fond noir/blanc des scans de musée).

    Beaucoup d'institutions photographient l'œuvre sur un fond uni : le Met
    renvoie par ex. un fond noir pur ``(1,1,1)``. On détecte la couleur des
    coins, on isole le contenu (différence > ``tol``) et on rogne — sans jamais
    couper plus de ``max_frac`` par côté (garde-fou anti-rognage d'œuvre sombre).
    """
    rgb = img.convert("RGB")
    w, h = rgb.size
    coins = [rgb.getpixel((1, 1)), rgb.getpixel((w - 2, 1)),
             rgb.getpixel((1, h - 2)), rgb.getpixel((w - 2, h - 2))]
    # couleur de bord = médiane par canal des 4 coins
    bord = tuple(sorted(c[i] for c in coins)[1] for i in range(3))
    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, bord)).convert("L")
    masque = diff.point(lambda v: 255 if v > tol else 0)
    bbox = masque.getbbox()
    if not bbox:
        return rgb
    g, t, dr, b = bbox
    # garde-fous : ne jamais rogner plus de max_frac par côté
    g = min(g, int(w * max_frac))
    t = min(t, int(h * max_frac))
    dr = max(dr, w - int(w * max_frac))
    b = max(b, h - int(h * max_frac))
    if (g, t, dr, b) == (0, 0, w, h):
        return rgb
    return rgb.crop((g, t, dr, b))


# ───────────────────────── étapes colorimétriques ─────────────────────────

def equilibrer_blancs(img: Image.Image, force: float = 0.8) -> Image.Image:
    """Gray-world : ramène la moyenne de chaque canal vers la moyenne globale.

    ``force`` ∈ [0,1] dose l'effet (0.8 = correction franche mais non destructive).
    """
    stat = ImageStat.Stat(img)
    moyennes = stat.mean[:3]
    cible = sum(moyennes) / 3.0
    if cible <= 0:
        return img

    tables = []
    for moy in moyennes:
        if moy <= 0:
            gain = 1.0
        else:
            gain = 1.0 + force * ((cible / moy) - 1.0)
        tables.append([min(255, int(round(v * gain))) for v in range(256)])
    # point() attend une LUT concaténée R+G+B pour une image RGB
    return img.point(tables[0] + tables[1] + tables[2])


def autocontraste(img: Image.Image, cutoff: float = 0.4) -> Image.Image:
    """Autocontraste doux : ignore ``cutoff`` % aux extrêmes pour éviter le clipping."""
    return ImageOps.autocontrast(img, cutoff=cutoff, preserve_tone=True)


def debruiter_leger(img: Image.Image, force: float = 0.35) -> Image.Image:
    """Débruitage préservant les bords : mélange image originale / médiane 3x3."""
    median = img.filter(ImageFilter.MedianFilter(size=3))
    return Image.blend(img, median, alpha=max(0.0, min(1.0, force)))


def accentuer(img: Image.Image) -> Image.Image:
    """Unsharp mask calibré pour la reproduction d'œuvres (net sans halo)."""
    return img.filter(ImageFilter.UnsharpMask(radius=2.0, percent=115, threshold=3))


# ───────────────────────────── upscale ─────────────────────────────

def _upscale_lanczos(img: Image.Image, long_edge_cible: int) -> Image.Image:
    long_edge = max(img.size)
    if long_edge >= long_edge_cible:
        return img
    facteur = long_edge_cible / long_edge
    nouvelle_taille = (round(img.width * facteur), round(img.height * facteur))
    agrandi = img.resize(nouvelle_taille, Image.LANCZOS)
    # Un upscale interpolé adoucit : on ré-accentue légèrement.
    return agrandi.filter(ImageFilter.UnsharpMask(radius=1.6, percent=90, threshold=2))


def _upscale_replicate(img: Image.Image, facteur: int = 4) -> Optional[Image.Image]:
    """Super-résolution Real-ESRGAN via Replicate si REPLICATE_API_TOKEN présent.

    Retourne None si la clé manque ou en cas d'échec (le pipeline retombe alors
    sur l'upscale Lanczos). Implémenté mais dormant tant que la clé n'est pas posée.
    """
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token or requests is None:
        return None
    try:
        tampon = io.BytesIO()
        img.save(tampon, format="PNG")
        import base64

        data_uri = "data:image/png;base64," + base64.b64encode(tampon.getvalue()).decode()
        creation = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                # Real-ESRGAN (nightmareai) — version à figer en prod.
                "version": "f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa",
                "input": {"image": data_uri, "scale": facteur, "face_enhance": False},
            },
            timeout=30,
        )
        creation.raise_for_status()
        pred = creation.json()
        url_get = pred["urls"]["get"]
        for _ in range(60):  # poll jusqu'à ~2 min
            time.sleep(2)
            etat = requests.get(url_get, headers={"Authorization": f"Bearer {token}"}, timeout=30).json()
            if etat.get("status") == "succeeded":
                sortie = etat["output"]
                url_img = sortie[0] if isinstance(sortie, list) else sortie
                octets = requests.get(url_img, timeout=120).content
                return Image.open(io.BytesIO(octets)).convert("RGB")
            if etat.get("status") in {"failed", "canceled"}:
                return None
        return None
    except Exception:
        return None


# ───────────────────────────── pipeline ─────────────────────────────

def restaurer(
    img: Image.Image,
    *,
    long_edge_cible: int = 4000,
    rogner: bool = True,
    equilibrage: bool = True,
    debruitage: bool = True,
    accentuation: bool = True,
    upscale: bool = True,
) -> Tuple[Image.Image, RapportRestauration]:
    """Applique le pipeline complet et retourne (image_restaurée, rapport)."""
    largeur_avant, hauteur_avant = img.size
    out = img.convert("RGB")

    if rogner:
        out = rogner_bords(out)
    if equilibrage:
        out = equilibrer_blancs(out)
    out = autocontraste(out)
    if debruitage:
        out = debruiter_leger(out)
    if accentuation:
        out = accentuer(out)

    methode = "aucun"
    if upscale and max(out.size) < long_edge_cible:
        agrandi = _upscale_replicate(out)
        if agrandi is not None:
            # Real-ESRGAN peut dépasser la cible : on cadre si besoin.
            if max(agrandi.size) > long_edge_cible * 1.05:
                agrandi = _upscale_lanczos(agrandi, long_edge_cible) if max(agrandi.size) < long_edge_cible else agrandi
            out = agrandi
            methode = "real-esrgan"
        else:
            out = _upscale_lanczos(out, long_edge_cible)
            methode = "lanczos"

    largeur_apres, hauteur_apres = out.size
    rapport = RapportRestauration(
        largeur_avant=largeur_avant,
        hauteur_avant=hauteur_avant,
        largeur_apres=largeur_apres,
        hauteur_apres=hauteur_apres,
        upscale_methode=methode,
        equilibrage_blancs=equilibrage,
        debruitage=debruitage,
        accentuation=accentuation,
    )
    return out, rapport


def composer_avant_apres(avant: Image.Image, apres: Image.Image, hauteur: int = 900) -> Image.Image:
    """Visuel marketing « avant / après restauration » (split vertical net).

    Très performant sur Instagram/Pinterest (pilier différenciation restauration).
    """
    def _cadrer(im: Image.Image) -> Image.Image:
        im = im.convert("RGB")
        ratio = hauteur / im.height
        return im.resize((round(im.width * ratio), hauteur), Image.LANCZOS)

    a = _cadrer(avant)
    b = _cadrer(apres.resize(avant.size, Image.LANCZOS)) if apres.size != avant.size else _cadrer(apres)
    largeur = min(a.width, b.width)
    a = a.crop(((a.width - largeur) // 2, 0, (a.width - largeur) // 2 + largeur, hauteur))
    b = b.crop(((b.width - largeur) // 2, 0, (b.width - largeur) // 2 + largeur, hauteur))

    canevas = Image.new("RGB", (largeur, hauteur))
    moitie = largeur // 2
    canevas.paste(a.crop((0, 0, moitie, hauteur)), (0, 0))
    canevas.paste(b.crop((moitie, 0, largeur, hauteur)), (moitie, 0))
    # Ligne de séparation laiton
    from PIL import ImageDraw

    d = ImageDraw.Draw(canevas)
    d.line([(moitie, 0), (moitie, hauteur)], fill=(169, 128, 63), width=3)
    return canevas
