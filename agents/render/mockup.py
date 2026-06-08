"""Orchestrateur de mockups — assemble restauration + cadres + scènes.

Produit la galerie complète d'une fiche Etsy (≈ 10 visuels, exactement le
nombre de slots Etsy) à partir d'une seule image source :

  1. master restauré (web)              5. comparatif de tailles
  2. avant / après restauration          6. trois options de cadre
  3. poster nu sur mur neutre            7-9. trois scènes lifestyle
  4. détail texture (crop)               10. carte de provenance (recto)

100 % local (Pillow). Aucune clé requise.
"""

from __future__ import annotations

import io
import json
import os
from dataclasses import asdict
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import frames, scenes
from .couleur import assurer_srgb, rapport_gamut, taguer_srgb
from .fidelity import auditer_fidelite
from .perspective import coeffs_vers_quad
from .restoration import composer_avant_apres, restaurer
from .typo import charger_police

RGB = Tuple[int, int, int]
PAPIER: RGB = (244, 239, 230)
ENCRE: RGB = (42, 38, 34)
LAITON: RGB = (169, 128, 63)


def _fond_studio(taille: Tuple[int, int], couleur: RGB = (236, 232, 224)) -> Image.Image:
    w, h = taille
    base = Image.new("RGB", (1, h))
    px = base.load()
    for y in range(h):
        t = y / max(1, h - 1)
        # mur légèrement plus clair au centre, vignette douce en bas
        k = 1.0 - 0.06 * abs(t - 0.42)
        px[0, y] = tuple(min(255, int(c * k)) for c in couleur)  # type: ignore
    return base.resize((w, h))


def _poser_dans_scene(scene: Image.Image, quad: scenes.Quad, piece: Image.Image) -> Image.Image:
    """Déforme ``piece`` (RGBA) dans le quad de la scène, avec ombre de contact."""
    scene = scene.convert("RGBA")
    coeffs = coeffs_vers_quad(quad, piece.size)
    deforme = piece.convert("RGBA").transform(scene.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)

    alpha = deforme.split()[-1]
    ombre = Image.new("RGBA", scene.size, (0, 0, 0, 0))
    noir = Image.new("RGBA", scene.size, (14, 11, 8, 130))
    forme = Image.composite(noir, ombre, alpha)
    # décale l'ombre vers le bas et floute
    decalee = Image.new("RGBA", scene.size, (0, 0, 0, 0))
    decalee.paste(forme, (max(2, scene.size[0] // 220), max(6, scene.size[1] // 90)))
    decalee = decalee.filter(ImageFilter.GaussianBlur(scene.size[0] // 130))

    scene.alpha_composite(decalee)
    scene.alpha_composite(deforme)
    return scene.convert("RGB")


def _redim_long_edge(img: Image.Image, long_edge: int) -> Image.Image:
    if max(img.size) <= long_edge:
        return img
    f = long_edge / max(img.size)
    return img.resize((round(img.width * f), round(img.height * f)), Image.LANCZOS)


# ──────────────────────────── visuels catalogue ────────────────────────────

def poster_nu(art: Image.Image, sortie: Tuple[int, int] = (1600, 1600)) -> Image.Image:
    """Tirage nu posé sur mur neutre, avec liseré papier et ombre portée."""
    scene = _fond_studio(sortie)
    art_red = _redim_long_edge(art.convert("RGB"), int(min(sortie) * 0.66))
    # fin liseré pour figurer le bord du papier
    bord = 0
    piece = Image.new("RGBA", (art_red.width + 2 * bord, art_red.height + 2 * bord), (255, 255, 255, 255))
    piece.paste(art_red, (bord, bord))
    avec_ombre = frames.ombre_portee(piece, decalage=(0, 14), flou=20, opacite=90, marge=70)
    x = (sortie[0] - avec_ombre.width) // 2
    y = (sortie[1] - avec_ombre.height) // 2
    scene = scene.convert("RGBA")
    scene.alpha_composite(avec_ombre, (x, y))
    return scene.convert("RGB")


def encadre_sur_mur(art: Image.Image, profil: str = "chene",
                    sortie: Tuple[int, int] = (1600, 1600)) -> Image.Image:
    scene = _fond_studio(sortie)
    piece = frames.encadrer(_redim_long_edge(art, 1400), profil)
    piece = _redim_long_edge(piece, int(min(sortie) * 0.72))
    avec_ombre = frames.ombre_portee(piece, decalage=(0, 16), flou=24, opacite=120, marge=80)
    x = (sortie[0] - avec_ombre.width) // 2
    y = (sortie[1] - avec_ombre.height) // 2
    scene = scene.convert("RGBA")
    scene.alpha_composite(avec_ombre, (x, y))
    return scene.convert("RGB")


def detail_texture(art: Image.Image, sortie: Tuple[int, int] = (1600, 1600),
                   zoom: float = 2.6) -> Image.Image:
    """Crop serré (centre) pour montrer la finesse de restauration."""
    w, h = art.size
    cw, ch = int(w / zoom), int(h / zoom)
    cx, cy = w // 2, int(h * 0.42)
    crop = art.crop((max(0, cx - cw // 2), max(0, cy - ch // 2),
                     min(w, cx + cw // 2), min(h, cy + ch // 2)))
    crop = crop.resize(sortie, Image.LANCZOS)
    # léger renforcement micro-contraste pour « voir le grain »
    return crop.filter(ImageFilter.UnsharpMask(radius=1.4, percent=70, threshold=2))


def options_cadres(art: Image.Image, profils: List[str],
                   sortie: Tuple[int, int] = (1600, 1100)) -> Image.Image:
    """Présente la même œuvre dans plusieurs cadres côte à côte (variantes)."""
    scene = _fond_studio(sortie).convert("RGBA")
    n = len(profils)
    art_petit = _redim_long_edge(art, 700)
    largeur_case = sortie[0] // n
    police = charger_police(int(sortie[1] * 0.045))
    d = ImageDraw.Draw(scene)
    for i, prof in enumerate(profils):
        piece = frames.encadrer(art_petit, prof, mat_frac=0.07)
        piece = _redim_long_edge(piece, int(largeur_case * 0.78))
        piece = frames.ombre_portee(piece, decalage=(0, 10), flou=16, opacite=100, marge=40)
        x = i * largeur_case + (largeur_case - piece.width) // 2
        y = int(sortie[1] * 0.40) - piece.height // 2
        scene.alpha_composite(piece, (x, max(10, y)))
        nom = frames.PROFILS.get(prof, frames.PROFILS["chene"]).nom
        bbox = d.textbbox((0, 0), nom, font=police)
        tw = bbox[2] - bbox[0]
        d.text((i * largeur_case + (largeur_case - tw) // 2, int(sortie[1] * 0.86)),
               nom, font=police, fill=ENCRE)
    return scene.convert("RGB")


def comparatif_tailles(art: Image.Image, formats: List[Tuple[str, float, float]],
                       sortie: Tuple[int, int] = (1600, 1200)) -> Image.Image:
    """Cadres à l'échelle relative (cm) pour visualiser les tailles.

    ``formats`` : liste de (libellé, largeur_cm, hauteur_cm). Les formats sont
    orientés selon l'œuvre (paysage/portrait) et l'œuvre est CONTENUE (jamais
    recadrée) dans chaque cadre, avec une fine marge papier.
    """
    scene = _fond_studio(sortie).convert("RGBA")
    d = ImageDraw.Draw(scene)
    sol_y = int(sortie[1] * 0.82)
    d.rectangle([0, sol_y, sortie[0], sortie[1]], fill=(214, 203, 186))
    d.line([(0, sol_y), (sortie[0], sol_y)], fill=(190, 178, 160), width=2)

    paysage = art.width >= art.height
    art_ratio = art.width / art.height
    # oriente chaque format dans le sens de l'œuvre
    orientes = []
    for libelle, a, b in formats:
        long_cm, court_cm = max(a, b), min(a, b)
        fw, fh = (long_cm, court_cm) if paysage else (court_cm, long_cm)
        orientes.append((libelle, fw, fh))

    cm_max = max(max(fw, fh) for _, fw, fh in orientes)
    px_par_cm = (sortie[0] * 0.74) / sum(fw for _, fw, _ in orientes)  # tient en largeur
    px_par_cm = min(px_par_cm, (sortie[1] * 0.56) / cm_max)            # et en hauteur

    largeur_totale = sum(int(fw * px_par_cm) for _, fw, _ in orientes) + int(sortie[0] * 0.05) * (len(orientes) - 1)
    x = (sortie[0] - largeur_totale) // 2
    police = charger_police(int(sortie[1] * 0.040), role="titrage")
    petite = charger_police(int(sortie[1] * 0.030))

    for libelle, fw_cm, fh_cm in orientes:
        pw, ph = int(fw_cm * px_par_cm), int(fh_cm * px_par_cm)
        y = sol_y - ph - int(sortie[1] * 0.02)
        # cadre fin + passe-partout blanc
        d.rectangle([x, y, x + pw, y + ph], fill=(250, 248, 243), outline=(120, 100, 70), width=4)
        # œuvre contenue (contain) centrée dans l'intérieur
        inter_w, inter_h = pw - 16, ph - 16
        if inter_w / inter_h > art_ratio:
            vh = inter_h
            vw = int(vh * art_ratio)
        else:
            vw = inter_w
            vh = int(vw / art_ratio)
        vign = art.resize((max(1, vw), max(1, vh)), Image.LANCZOS)
        scene.paste(vign, (x + (pw - vw) // 2, y + (ph - vh) // 2))
        bb = d.textbbox((0, 0), libelle, font=police)
        d.text((x + (pw - (bb[2] - bb[0])) // 2, sol_y + int(sortie[1] * 0.025)), libelle,
               font=police, fill=ENCRE)
        dim = f"{int(round(fw_cm))}×{int(round(fh_cm))} cm"
        bb2 = d.textbbox((0, 0), dim, font=petite)
        d.text((x + (pw - (bb2[2] - bb2[0])) // 2, sol_y + int(sortie[1] * 0.075)), dim,
               font=petite, fill=(107, 100, 91))
        x += pw + int(sortie[0] * 0.05)
    return scene.convert("RGB")


def lifestyle(art: Image.Image, scene_nom: str, profil: Optional[str] = None,
              sortie: Tuple[int, int] = (1600, 1200)) -> Image.Image:
    sc = scenes.SCENES.get(scene_nom, scenes.SCENES["galerie"])
    profil = profil or sc.cadre_suggere
    scene_img, _ = sc.builder(sortie)
    piece = frames.encadrer(_redim_long_edge(art, 1200), profil)
    ratio = piece.width / piece.height
    quad = scenes.quad_pour_scene(scene_nom, sortie, ratio)
    return _poser_dans_scene(scene_img, quad, piece)


# ──────────────────────────── orchestration ────────────────────────────

def _sauver(img: Image.Image, chemin: str, qualite: int = 90) -> str:
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    # Tague sRGB sur les fichiers livrés (consigne Gelato ; neutre pour Prodigi).
    if chemin.lower().endswith((".jpg", ".jpeg")):
        img.convert("RGB").save(chemin, "JPEG", quality=qualite, optimize=True, icc_profile=taguer_srgb())
    else:
        img.save(chemin)
    return chemin


def generer_galerie(
    source: Image.Image,
    dossier: str,
    *,
    profils: Optional[List[str]] = None,
    scenes_choisies: Optional[List[str]] = None,
    long_edge_print: int = 4000,
    restauration: bool = True,
    profil: str = "fidele",
    profil_papier: Optional[str] = None,
) -> Dict:
    """Génère la galerie complète et retourne un manifeste (chemins + métadonnées).

    Chaîne couleur : la source est ramenée en **sRGB** (gestion ICC) avant toute
    chose, puis :
      • audit de fidélité — master vs source recalée, en sRGB → verdict honnête ;
      • soft-proof gamut — quelles couleurs profondes risquent l'écrêtage print.
    L'avant/après n'est émis QUE si une vraie restauration couleur a eu lieu
    (profil "archive") — en mode fidèle, il n'y a rien à « restaurer » à montrer.
    """
    profils = profils or ["chene", "noir", "blanc"]
    scenes_choisies = scenes_choisies or ["galerie", "scandinave", "atelier"]

    # Gestion couleur UNE seule fois : sRGB de livraison + provenance de l'espace
    # source. Réutilisée pour la restauration ET la référence d'audit (pas de 2e
    # conversion pleine résolution sur les sources à profil non-sRGB).
    source_srgb, infos_icc = assurer_srgb(source)
    couleur = {"espace_source": infos_icc["espace_source"], "converti_srgb": infos_icc["converti"]}

    if restauration:
        master, rapport = restaurer(source_srgb, long_edge_cible=long_edge_print,
                                    profil=profil, infos_couleur=infos_icc)
    else:
        master, rapport = source_srgb.convert("RGB"), None

    manifeste: Dict = {
        "dossier": dossier, "fichiers": {},
        "restauration": asdict(rapport) if rapport else None,
        "couleur": couleur,
    }

    # Audit de fidélité colorimétrique (garde-fou anti-délavage) — toujours, même
    # en préparation print : si une étape « neutre » dérive, c'est un bug à voir.
    # La référence est la source DÉJÀ color-managée en sRGB (mesure la VÉRITÉ, pas
    # une co-mésinterprétation), recalée sur le recadrage du master.
    ref = source_srgb
    if rapport is not None and rapport.box_rognage:
        ref = ref.crop(rapport.box_rognage)
    fid = auditer_fidelite(ref, master)
    manifeste["fidelite"] = fid.to_dict()

    # Soft-proof gamut (informatif, jamais une correction).
    manifeste["gamut"] = rapport_gamut(master, profil_papier=profil_papier)

    # master web (pour la galerie ; le print HD reste en mémoire/local séparé)
    web = _redim_long_edge(master, 2000)
    manifeste["fichiers"]["master"] = _sauver(web, f"{dossier}/master_restaure.jpg")

    # Avant/après : honnête seulement quand on a réellement modifié la couleur.
    if restauration and rapport is not None and rapport.deplace_teinte:
        manifeste["fichiers"]["avant_apres"] = _sauver(
            composer_avant_apres(source, master), f"{dossier}/avant_apres.jpg")

    manifeste["fichiers"]["poster_nu"] = _sauver(poster_nu(master), f"{dossier}/catalogue/01_poster_nu.jpg")
    manifeste["fichiers"]["encadre"] = _sauver(
        encadre_sur_mur(master, profils[0]), f"{dossier}/catalogue/02_encadre_{profils[0]}.jpg")
    manifeste["fichiers"]["detail"] = _sauver(detail_texture(master), f"{dossier}/catalogue/03_detail.jpg")
    manifeste["fichiers"]["options_cadres"] = _sauver(
        options_cadres(master, profils), f"{dossier}/catalogue/04_cadres.jpg")
    manifeste["fichiers"]["comparatif"] = _sauver(
        comparatif_tailles(master, [("A4", 21, 29.7), ("A3", 29.7, 42), ("A2", 42, 59.4)]),
        f"{dossier}/catalogue/05_tailles.jpg")

    manifeste["fichiers"]["lifestyle"] = []
    for nom in scenes_choisies:
        chemin = _sauver(lifestyle(master, nom), f"{dossier}/lifestyle/{nom}.jpg")
        manifeste["fichiers"]["lifestyle"].append(chemin)

    with open(f"{dossier}/manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifeste, f, ensure_ascii=False, indent=2)
    return manifeste
