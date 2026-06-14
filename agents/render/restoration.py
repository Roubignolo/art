"""Restauration des masters — pipeline local (Pillow) + bascule Replicate.

POLITIQUE « FIDÉLITÉ D'ABORD » (cf. docs/restauration-politique.md)
------------------------------------------------------------------
Un master open-access de musée (Met, AIC, Cleveland, Rijks…) est DÉJÀ une
reproduction colorimétriquement fidèle : il a été numérisé sous mire + profil
ICC, selon les référentiels FADGI / Metamorfoze. Le « corriger » en couleur le
DÉGRADE. Notre analyse a montré qu'un gray-world global effaçait ~75 % du
parti-pris chromatique des peintres (la nappe bleue de Cézanne virait au blanc).

→ Profil « fidele » (DÉFAUT) = préparation print qui NE DÉPLACE PAS LA TEINTE :
    1. rognage des bords de scan (liseré uni)         [neutre en couleur]
    2. débruitage léger préservant les bords           [neutre en couleur]
    3. accentuation (unsharp mask)                     [neutre en couleur]
    4. upscale Lanczos / Real-ESRGAN vers la cible print

→ Profil « archive » (OPT-IN, scans NON calibrés / abîmés seulement) = ajoute
  une balance des blancs + un autocontraste BORNÉS. À n'activer que sur décision
  humaine (jamais sur un fichier musée), et toujours contrôlé a posteriori par
  agents.render.fidelity.auditer_fidelite (verdict FIDÈLE / À REVOIR / INFIDÈLE).

La règle dure : on ne neutralise JAMAIS une dominante sur la moyenne de l'image
(gray-world), ni un blanc PEINT (drapé, nappe = contenu, pas une mire).

Bascule optionnelle : si REPLICATE_API_TOKEN est présent, l'upscale Lanczos
est remplacé par un vrai super-résolution Real-ESRGAN (×2/×4).
"""

from __future__ import annotations

import io
import os
import time
from dataclasses import dataclass
from math import sqrt
from typing import Optional, Tuple

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

from .couleur import assurer_srgb

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
    profil: str                   # "fidele" (défaut) | "archive"
    equilibrage_blancs: bool      # gray-world — False en mode fidèle
    contraste: bool               # autocontraste — False en mode fidèle
    debruitage: bool
    accentuation: bool
    box_rognage: Optional[Tuple[int, int, int, int]] = None  # recadrage appliqué (pour l'audit)
    espace_source: str = "sRGB présumé (sans profil ICC)"    # profil ICC d'entrée détecté
    converti_srgb: bool = False                              # une conversion ICC→sRGB a eu lieu

    @property
    def long_edge_apres(self) -> int:
        return max(self.largeur_apres, self.hauteur_apres)

    @property
    def deplace_teinte(self) -> bool:
        """Vrai si une étape a pu modifier la couleur (→ audit de fidélité requis)."""
        return self.equilibrage_blancs or self.contraste


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

def _plus_grand_bloc(densite: list, seuil: float, gap_frac: float) -> Tuple[int, int]:
    """Plus grand segment contigu où ``densite > seuil`` (petits trous tolérés).

    Sépare l'œuvre d'une barre de calibration / d'un montage isolés par une bande
    de fond (densité ~0). Retourne (debut, fin) inclusifs.
    """
    on = [d > seuil for d in densite]
    n = len(on)
    gap = max(1, int(n * gap_frac))
    best = (0, 0, n - 1)
    i = 0
    while i < n:
        if not on[i]:
            i += 1
            continue
        j, trou = i, 0
        while j < n and (on[j] or trou < gap):
            trou = 0 if on[j] else trou + 1
            j += 1
        k = j - 1
        while k > i and not on[k]:
            k -= 1
        if k - i + 1 > best[0]:
            best = (k - i + 1, i, k)
        i = j
    return best[1], best[2]


def _bande_calibration(rgb: Image.Image, marge: float = 0.22, sat_max: int = 28,
                       std_min: float = 42.0) -> Tuple[float, float]:
    """Détecte une MIRE de calibration (réglette grise à patchs noir→blanc) sur le
    bord gauche/droit — typique des scans Met d'œuvres-sur-papier. Retourne les
    fractions à retirer (gauche, droite).

    Une colonne « mire » est GRISE (chroma faible) ET à FORTE variance de luminance
    (patchs contrastés). Garde-fous : seulement bords verticaux (la mire Met est
    verticale) ; si la bande court jusqu'à la limite ``marge``, c'est de l'œuvre grise
    continue (gravure N&B), pas une mire séparée → rejet (0).
    """
    w, h = rgb.size
    lum = rgb.convert("L")
    r, g, b = rgb.split()
    mx = ImageChops.lighter(ImageChops.lighter(r, g), b)
    mn = ImageChops.darker(ImageChops.darker(r, g), b)
    chroma = ImageChops.difference(mx, mn)  # max-min par pixel ≈ saturation
    e_l = list(lum.resize((w, 1), Image.BOX).getdata())
    e_l2 = [v * 256 for v in lum.point(lambda v: (v * v) // 256).resize((w, 1), Image.BOX).getdata()]
    std = [sqrt(max(0.0, e_l2[x] - e_l[x] ** 2)) for x in range(w)]
    sat = list(chroma.resize((w, 1), Image.BOX).getdata())
    barlike = [sat[x] < sat_max and std[x] > std_min for x in range(w)]

    def cote(gauche: bool) -> float:
        end, lim = 0, int(w * marge)
        for c in range(lim):
            x = c if gauche else w - 1 - c
            if barlike[x]:
                end = c + 1
            elif c - end > int(w * 0.03):  # fin de la mire (transition vers l'œuvre)
                break
        f = end / w
        return 0.0 if f >= marge * 0.88 else f  # bande jusqu'à la limite = œuvre grise

    return cote(True), cote(False)


def _box_fond(rgb: Image.Image, tol: int = 24, max_frac: float = 0.42,
              dens_frac: float = 0.03, gap_frac: float = 0.02
              ) -> Optional[Tuple[int, int, int, int]]:
    """Boîte de rognage du FOND uniforme d'un scan, ou None (œuvre plein cadre).

    Détecte un fond uni (4 coins concordants) et isole le plus grand bloc de contenu
    contigu. Garde-fous : plein cadre (coins discordants OU contenu > 92 %) → None ;
    anti-sur-rognage (retirer > 50 % de l'aire = composition étalée) → None.
    """
    w, h = rgb.size
    p = max(4, min(w, h) // 50)
    coins = [rgb.crop((0, 0, p, p)), rgb.crop((w - p, 0, w, p)),
             rgb.crop((0, h - p, p, h)), rgb.crop((w - p, h - p, w, h))]
    med = [ImageStat.Stat(c).median for c in coins]
    bg = tuple(sorted(m[i] for m in med)[1] for i in range(3))
    if max(abs(m[i] - bg[i]) for m in med for i in range(3)) > 26:
        return None  # coins discordants → peinture plein cadre
    masque = ImageChops.difference(rgb, Image.new("RGB", rgb.size, bg)).convert("L").point(
        lambda v: 255 if v > tol else 0)
    if ImageStat.Stat(masque).mean[0] / 255.0 > 0.92:
        return None  # pas de marge de fond → plein cadre
    seuil = dens_frac * 255
    x0, x1 = _plus_grand_bloc(list(masque.resize((w, 1), Image.BOX).getdata()), seuil, gap_frac)
    y0, y1 = _plus_grand_bloc(list(masque.resize((1, h), Image.BOX).getdata()), seuil, gap_frac)
    x0 = min(x0, int(w * max_frac)); y0 = min(y0, int(h * max_frac))
    x1 = max(x1, w - 1 - int(w * max_frac)); y1 = max(y1, h - 1 - int(h * max_frac))
    box = (x0, y0, x1 + 1, y1 + 1)
    if box == (0, 0, w, h):
        return None
    if (x1 + 1 - x0) * (y1 + 1 - y0) < 0.50 * w * h:
        return None  # > 50 % retiré = composition étalée → on laisse (gate humain)
    return box


def box_bords(img: Image.Image, tol: int = 24, max_frac: float = 0.42
              ) -> Optional[Tuple[int, int, int, int]]:
    """Boîte de rognage de l'APPARATUS de scan musée, ou None si rien à rogner.

    Beaucoup de scans d'œuvres-sur-papier (estampes japonaises notamment) incluent
    une **mire de calibration colorimétrique**, un fond de prise de vue et des coins
    de montage — qui, non retirés, rendent l'œuvre **inutilisable encadrée**. On
    retire d'abord la mire (bande grise contrastée sur un bord), puis le fond uniforme.
    Ce n'est PAS un crop de l'ŒUVRE : on enlève l'appareillage de photo. Recadrage
    réutilisé tel quel par l'audit de fidélité (même cadrage sur l'original).
    """
    rgb = img.convert("RGB")
    w, h = rgb.size
    if w < 8 or h < 8:
        return None
    fg, fd = _bande_calibration(rgb)
    bx0, bx1 = int(w * fg), w - int(w * fd)
    sub = rgb.crop((bx0, 0, bx1, h)) if (bx0 > 0 or bx1 < w) else rgb
    fond = _box_fond(sub, tol, max_frac)
    if fond:
        box = (bx0 + fond[0], fond[1], bx0 + fond[2], fond[3])
    elif bx0 > 0 or bx1 < w:
        box = (bx0, 0, bx1, h)  # mire retirée, pas de fond à rogner
    else:
        return None
    return None if box == (0, 0, w, h) else box


def rogner_bords(img: Image.Image, tol: int = 24, max_frac: float = 0.42) -> Image.Image:
    """Supprime l'apparatus de scan musée (mire de calibration + fond + montage)."""
    rgb = img.convert("RGB")
    box = box_bords(rgb, tol, max_frac)
    return rgb.crop(box) if box else rgb


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
    profil: str = "fidele",
    rogner: bool = True,
    debruitage: bool = True,
    accentuation: bool = True,
    upscale: bool = True,
    equilibrage: Optional[bool] = None,
    contraste: Optional[bool] = None,
    infos_couleur: Optional[dict] = None,
) -> Tuple[Image.Image, RapportRestauration]:
    """Applique le pipeline et retourne (image_restaurée, rapport).

    ``profil`` :
      • "fidele" (défaut) — aucune étape ne déplace la teinte (cf. docstring module).
      • "archive" — ajoute balance des blancs + autocontraste bornés (scans abîmés
        NON calibrés, sur décision humaine ; à valider via fidelity.auditer_fidelite).

    ``equilibrage`` / ``contraste`` forcent explicitement ces étapes couleur ; si
    None (défaut), elles découlent du profil (off en "fidele", on en "archive").
    """
    if equilibrage is None:
        equilibrage = (profil == "archive")
    if contraste is None:
        contraste = (profil == "archive")

    largeur_avant, hauteur_avant = img.size
    # Étape 0 — gestion couleur : garantir le sRGB de livraison (gestion ICC).
    # N'est PAS une correction esthétique : transporte fidèlement l'apparence
    # dans l'espace attendu par les RIP Gelato/Prodigi. Si l'appelant a déjà géré
    # la couleur (generer_galerie passe infos_couleur + une image déjà sRGB), on
    # réutilise son résultat pour éviter une seconde conversion pleine résolution.
    if infos_couleur is not None:
        out, infos_icc = img.convert("RGB"), infos_couleur
    else:
        out, infos_icc = assurer_srgb(img)

    box = box_bords(out) if rogner else None
    if box:
        out = out.crop(box)
    if equilibrage:
        out = equilibrer_blancs(out)
    if contraste:
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
        profil=profil,
        equilibrage_blancs=equilibrage,
        contraste=contraste,
        debruitage=debruitage,
        accentuation=accentuation,
        box_rognage=box,
        espace_source=infos_icc["espace_source"],
        converti_srgb=infos_icc["converti"],
    )
    return out, rapport


def composer_avant_apres(avant: Image.Image, apres: Image.Image, hauteur: int = 900) -> Image.Image:
    """Split avant/après — émis UNIQUEMENT en profil « archive », quand une vraie
    correction couleur d'un défaut a eu lieu (scan non calibré/jauni).

    En profil « fidèle » il n'y a rien à « restaurer » → ce visuel n'est pas produit
    (cf. docs/restauration-politique.md §2/§6). Ce n'est PAS un argument marketing
    systématique de « restauration couleur ».
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
