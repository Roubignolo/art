"""Scènes lifestyle procédurales en Pillow pur.

Plutôt que de dessiner du mobilier (qui vire vite à l'amateur), on compose
des intérieurs ÉDITORIAUX et minimalistes : mur ton craie/lin, bain de lumière
latérale (fenêtre hors-champ), plinthe, sol en perspective douce, et au plus
un élément de premier plan FLOU (plante, lampe) pour la profondeur de champ.

Chaque preset renvoie (scène RGB, quad cible) où le quad indique où poser
l'œuvre encadrée. Pour les scènes de biais, le quad porte une légère
perspective ; le compositing (mockup.py) déforme l'œuvre en conséquence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Tuple

from PIL import Image, ImageDraw, ImageFilter

RGB = Tuple[int, int, int]
Point = Tuple[float, float]
Quad = List[Point]


def _degrade_vertical(taille: Tuple[int, int], haut: RGB, bas: RGB) -> Image.Image:
    w, h = taille
    base = Image.new("RGB", (1, h))
    px = base.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px[0, y] = tuple(int(haut[i] + (bas[i] - haut[i]) * t) for i in range(3))  # type: ignore
    return base.resize((w, h))


def _bain_lumiere(scene: Image.Image, centre: Point, rayon: float, intensite: float) -> None:
    """Ajoute un bain de lumière radial doux (fenêtre hors-champ)."""
    w, h = scene.size
    masque = Image.new("L", scene.size, 0)
    d = ImageDraw.Draw(masque)
    cx, cy = centre[0] * w, centre[1] * h
    r = rayon * max(w, h)
    # gradient radial approximé par cercles concentriques
    etapes = 40
    for i in range(etapes, 0, -1):
        rr = r * i / etapes
        val = int(255 * (1 - i / etapes) ** 1.6)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=val)
    masque = masque.filter(ImageFilter.GaussianBlur(r / 6))
    lumiere = Image.new("RGB", scene.size, (255, 250, 240))
    scene.paste(Image.composite(lumiere, scene, masque.point(lambda v: int(v * intensite))), (0, 0))


def _sol(scene: Image.Image, hauteur_frac: float, couleur_sol: RGB, couleur_plinthe: RGB) -> None:
    w, h = scene.size
    y_sol = int(h * (1 - hauteur_frac))
    d = ImageDraw.Draw(scene)
    # sol : léger dégradé (plus clair près du mur)
    sol = _degrade_vertical((w, h - y_sol), _eclaircir(couleur_sol, 0.10), couleur_sol)
    scene.paste(sol, (0, y_sol))
    # plinthe
    d.rectangle([0, y_sol - int(h * 0.018), w, y_sol], fill=couleur_plinthe)
    d.line([(0, y_sol), (w, y_sol)], fill=_assombrir(couleur_plinthe, 0.2), width=2)


def _eclaircir(c: RGB, k: float) -> RGB:
    return tuple(max(0, min(255, int(v + (255 - v) * k))) for v in c)  # type: ignore


def _assombrir(c: RGB, k: float) -> RGB:
    return tuple(max(0, min(255, int(v * (1 - k)))) for v in c)  # type: ignore


def _plante_floue(scene: Image.Image, cote: str = "droite") -> None:
    """Branche d'eucalyptus floue en premier plan — profondeur de champ éditoriale.

    Tiges fines et arquées + petites feuilles ovales, vert sauge désaturé, fort
    flou et opacité réduite : suggestif, jamais cartoon.
    """
    w, h = scene.size
    calque = Image.new("RGBA", scene.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(calque)
    signe = 1 if cote == "droite" else -1
    base_x = int(w * (0.965 if cote == "droite" else 0.035))
    base_y = h
    vert = (96, 112, 86)
    feuille = int(h * 0.028)
    for s, (haut_frac, courbe) in enumerate([(0.58, 0.10), (0.46, 0.16), (0.66, 0.06)]):
        haut = int(h * haut_frac)
        # tige arquée : points le long d'un arc, feuilles alternées
        prev = (base_x, base_y)
        for t in range(1, 13):
            f = t / 12
            x = base_x - signe * int(w * courbe * f) - signe * int(w * 0.01 * s)
            y = base_y - int(haut * f)
            d.line([prev, (x, y)], fill=vert + (200,), width=max(2, int(w * 0.004)))
            if t % 2 == 0:
                ddx = signe * feuille
                d.ellipse([x - feuille, y - feuille // 2, x + feuille, y + feuille // 2],
                          fill=vert + (175,))
                d.ellipse([x - ddx - feuille, y - feuille, x - ddx + feuille, y],
                          fill=_eclaircir(vert, 0.1) + (160,))
            prev = (x, y)
    calque = calque.filter(ImageFilter.GaussianBlur(int(w * 0.018)))
    # opacité globale réduite
    alpha = calque.split()[-1].point(lambda v: int(v * 0.72))
    calque.putalpha(alpha)
    scene.paste(calque, (0, 0), calque)


@dataclass
class Scene:
    nom: str
    builder: Callable[[Tuple[int, int]], Tuple[Image.Image, Quad]]
    cadre_suggere: str  # profil de cadre qui va le mieux avec la scène


def _quad_centre(taille: Tuple[int, int], ratio_oeuvre: float, hauteur_frac: float,
                 centre: Point, inclinaison: float = 0.0) -> Quad:
    """Construit un quad respectant le ratio de l'œuvre (pas de distorsion).

    ``inclinaison`` ∈ [0,1] rétrécit le côté droit pour une vue de 3/4.
    """
    w, h = taille
    hauteur = hauteur_frac * h
    largeur = hauteur * ratio_oeuvre
    cx, cy = centre[0] * w, centre[1] * h
    x0, x1 = cx - largeur / 2, cx + largeur / 2
    y0, y1 = cy - hauteur / 2, cy + hauteur / 2
    # perspective : on remonte/abaisse les coins droits
    dec = inclinaison * hauteur * 0.12
    return [(x0, y0), (x1, y0 + dec), (x1, y1 - dec), (x0, y1)]


# ──────────────────────────── presets ────────────────────────────

def _scene_galerie(taille: Tuple[int, int]) -> Tuple[Image.Image, Quad]:
    """Mur chaux clair, vue de face, lumière centrale douce. Éditorial, premium."""
    scene = _degrade_vertical(taille, (240, 236, 228), (231, 226, 216))
    _bain_lumiere(scene, (0.5, 0.42), 0.85, 0.5)
    _sol(scene, 0.16, (214, 203, 186), (222, 214, 199))
    quad = _quad_centre(taille, 0.0, 0, (0, 0))  # placeholder, recalculé avec ratio
    return scene, quad


def _scene_scandinave(taille: Tuple[int, int]) -> Tuple[Image.Image, Quad]:
    """Mur lin, sol chêne clair, plante floue à droite, légère vue de 3/4."""
    scene = _degrade_vertical(taille, (236, 231, 222), (226, 219, 207))
    _bain_lumiere(scene, (0.18, 0.3), 0.95, 0.55)
    _sol(scene, 0.22, (197, 168, 124), (228, 220, 205))
    _plante_floue(scene, "droite")
    quad = _quad_centre(taille, 0.0, 0, (0, 0))
    return scene, quad


def _scene_atelier(taille: Tuple[int, int]) -> Tuple[Image.Image, Quad]:
    """Mur argile/sauge chaud, lumière rasante latérale, ambiance cabinet."""
    scene = _degrade_vertical(taille, (216, 210, 196), (200, 196, 180))
    _bain_lumiere(scene, (0.78, 0.32), 0.8, 0.42)
    _sol(scene, 0.18, (150, 120, 92), (176, 158, 130))
    quad = _quad_centre(taille, 0.0, 0, (0, 0))
    return scene, quad


SCENES: dict[str, Scene] = {
    "galerie": Scene("galerie", _scene_galerie, "chene"),
    "scandinave": Scene("scandinave", _scene_scandinave, "chene"),
    "atelier": Scene("atelier", _scene_atelier, "noir"),
}


# paramètres de placement par scène (hauteur de l'œuvre, centre, inclinaison)
PLACEMENT = {
    "galerie": dict(hauteur_frac=0.52, centre=(0.5, 0.46), inclinaison=0.0),
    "scandinave": dict(hauteur_frac=0.46, centre=(0.56, 0.44), inclinaison=0.10),
    "atelier": dict(hauteur_frac=0.50, centre=(0.46, 0.45), inclinaison=0.06),
}


def quad_pour_scene(nom: str, taille: Tuple[int, int], ratio_oeuvre: float) -> Quad:
    p = PLACEMENT.get(nom, PLACEMENT["galerie"])
    return _quad_centre(taille, ratio_oeuvre, p["hauteur_frac"], p["centre"], p["inclinaison"])
