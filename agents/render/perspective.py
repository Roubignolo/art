"""Transformations perspective en Pillow pur — sans numpy.

Pillow sait appliquer une transformation perspective (``Image.PERSPECTIVE``)
à partir de 8 coefficients, mais ne sait pas les calculer. On résout donc
le système linéaire 8x8 nous-mêmes (élimination de Gauss) pour rester sur
zéro dépendance ajoutée (cf. conventions CLAUDE.md « peu de dépendances »).

Usage type — coller une œuvre rectangulaire dans un quadrilatère d'une scène :

    coeffs = coeffs_vers_quad(scene_quad, (w, h))
    deforme = art.transform(scene.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    scene.paste(deforme, (0, 0), deforme)
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

Point = Tuple[float, float]


def _resoudre(matrice: List[List[float]], second_membre: List[float]) -> List[float]:
    """Résout A·x = b par élimination de Gauss avec pivot partiel."""
    n = len(second_membre)
    # Matrice augmentée [A | b]
    aug = [list(matrice[i]) + [second_membre[i]] for i in range(n)]

    for col in range(n):
        # Pivot partiel : plus grande valeur absolue sur la colonne courante
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise ValueError("Système perspective dégénéré (points colinéaires ?)")
        aug[col], aug[pivot] = aug[pivot], aug[col]

        # Normalise la ligne pivot
        diviseur = aug[col][col]
        aug[col] = [v / diviseur for v in aug[col]]

        # Élimine la colonne sur les autres lignes
        for r in range(n):
            if r == col:
                continue
            facteur = aug[r][col]
            if facteur:
                aug[r] = [a - facteur * b for a, b in zip(aug[r], aug[col])]

    return [aug[i][n] for i in range(n)]


def coeffs_perspective(cibles: Sequence[Point], sources: Sequence[Point]) -> List[float]:
    """Calcule les 8 coefficients mappant ``cibles`` (sortie) → ``sources`` (entrée).

    Pillow applique : pour chaque pixel de sortie (x, y), il échantillonne
    l'entrée en ((a·x+b·y+c)/(g·x+h·y+1), (d·x+e·y+f)/(g·x+h·y+1)).
    On fournit donc les 4 coins de SORTIE (la scène) et les 4 coins
    correspondants d'ENTRÉE (l'œuvre source).
    """
    if len(cibles) != 4 or len(sources) != 4:
        raise ValueError("Il faut exactement 4 points cibles et 4 points sources")

    matrice: List[List[float]] = []
    second_membre: List[float] = []
    for (xc, yc), (xs, ys) in zip(cibles, sources):
        matrice.append([xc, yc, 1, 0, 0, 0, -xs * xc, -xs * yc])
        matrice.append([0, 0, 0, xc, yc, 1, -ys * xc, -ys * yc])
        second_membre.extend([xs, ys])

    return _resoudre(matrice, second_membre)


def coeffs_vers_quad(quad_cible: Sequence[Point], taille_source: Tuple[int, int]) -> List[float]:
    """Coefficients pour déformer une image source (rectangle plein) vers un quad.

    ``quad_cible`` : 4 points (haut-gauche, haut-droit, bas-droit, bas-gauche)
    exprimés dans le repère de la scène de sortie.
    ``taille_source`` : (largeur, hauteur) de l'image source.
    """
    w, h = taille_source
    coins_source: List[Point] = [(0, 0), (w, 0), (w, h), (0, h)]
    return coeffs_perspective(quad_cible, coins_source)
