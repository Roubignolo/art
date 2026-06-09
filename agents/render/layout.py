"""Mise en page produit — adapte une œuvre de ratio « musée » aux tailles POD.

Problème : Gelato/Prodigi ne fabriquent pas de cadre au ratio exact de l'œuvre —
ils travaillent sur un CATALOGUE de tailles fixes. Une reproduction patrimoniale
ne doit JAMAIS être rognée (crop) ni déformée (stretch). La seule voie fidèle :
contenir l'œuvre à son ratio natif et combler le reste par une BORDURE / un
PASSE-PARTOUT — soit intégré au fichier (Gelato), soit physique (mat Prodigi).

Ce module choisit la taille catalogue dont le ratio est le plus proche (bordure
minimale, équilibrée) et calcule les marges exactes. Voir docs/decision-encadrement-tailles.md.

Sources POD : cf. docs/benchmark-pod-fournisseurs.md §6 + todo §3.2/3.3 (à confirmer
par mail pour Gelato : libellé fit/fill, bornes custom).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class TailleCatalogue:
    label: str
    court_cm: float        # petit côté
    long_cm: float         # grand côté
    fournisseurs: Tuple[str, ...]   # ("gelato", "prodigi")

    @property
    def ratio(self) -> float:       # toujours ≥ 1 (grand/petit)
        return self.long_cm / self.court_cm


# Tailles murales réelles, convergentes Gelato/Prodigi (cm). Ratio = grand/petit.
CATALOGUE: List[TailleCatalogue] = [
    TailleCatalogue("20×25", 20, 25, ("prodigi",)),               # 8×10"  · 1.25
    TailleCatalogue("28×36", 28, 35.6, ("prodigi",)),             # 11×14" · 1.27
    TailleCatalogue("30×40", 30, 40, ("gelato", "prodigi")),      # 12×16" · 1.33
    TailleCatalogue("A3 30×42", 29.7, 42, ("gelato",)),           # 1.414
    TailleCatalogue("40×50", 40, 50, ("gelato", "prodigi")),      # 16×20" · 1.25
    TailleCatalogue("50×70", 50, 70, ("gelato", "prodigi")),      # ~20×28" · 1.40
    TailleCatalogue("A2 42×59", 42, 59.4, ("gelato",)),           # 1.414
    TailleCatalogue("61×91", 61, 91.4, ("gelato", "prodigi")),    # 24×36" · 1.50
    TailleCatalogue("30×30", 30, 30, ("gelato", "prodigi")),      # carré 1.0
    TailleCatalogue("50×50", 50, 50, ("gelato", "prodigi")),      # carré 1.0
]


@dataclass
class PlanMiseEnPage:
    taille: str            # libellé catalogue
    fournisseur: str       # "gelato" | "prodigi"
    orientation: str       # "paysage" | "portrait" | "carré"
    ratio_oeuvre: float    # grand/petit de l'œuvre
    ratio_taille: float    # grand/petit de la taille catalogue
    marge_h_frac: float    # bordure gauche+droite, en fraction de la largeur d'œuvre
    marge_v_frac: float    # bordure haut+bas, en fraction de la hauteur d'œuvre
    bordure_pct: float     # part de la surface finale occupée par la bordure (0-100)
    sizing_prodigi: str    # comportement API recommandé
    strategie: str         # "bordure-fichier" (Gelato) | "passe-partout" (Prodigi)
    note: str

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)


def _orientation(ratio_brut: float) -> str:
    if ratio_brut > 1.05:
        return "paysage"
    if ratio_brut < 0.95:
        return "portrait"
    return "carré"


def ouverture(aw: int, ah: int, ratio_cible: float, mat_min_frac: float = 0.08
              ) -> Tuple[int, int, int, int]:
    """Géométrie de l'ouverture (œuvre + passe-partout) au ``ratio_cible`` exact,
    contenant l'œuvre + au moins ``mat_min_frac`` du petit côté en marge par bord.

    ``ratio_cible`` est exprimé dans l'ORIENTATION de l'œuvre (largeur/hauteur).
    Retourne (ouverture_w, ouverture_h, marge_x_px, marge_y_px). Jamais de crop.
    """
    m = int(min(aw, ah) * mat_min_frac)
    # ouverture_w / ouverture_h = ratio_cible, avec marge ≥ m sur chaque axe.
    oh = max(ah + 2 * m, math.ceil((aw + 2 * m) / ratio_cible))
    ow = max(aw + 2 * m, round(ratio_cible * oh))
    oh = max(oh, round(ow / ratio_cible))  # cohérence après arrondis
    mwx = (ow - aw) // 2
    mwy = (oh - ah) // 2
    return ow, oh, mwx, mwy


def meilleure_taille(ratio_oeuvre: float, fournisseur: Optional[str] = None
                     ) -> TailleCatalogue:
    """Taille catalogue dont le ratio est le plus proche de l'œuvre (bordure minimale).

    ``ratio_oeuvre`` ≥ 1 (grand/petit). Filtre par fournisseur si fourni.
    """
    cands = [t for t in CATALOGUE if (fournisseur is None or fournisseur in t.fournisseurs)]
    # exclure le carré sauf si l'œuvre est ~carrée (sinon bordure énorme)
    if ratio_oeuvre > 1.12:
        cands = [t for t in cands if t.ratio > 1.05] or cands
    return min(cands, key=lambda t: abs(t.ratio - ratio_oeuvre))


def planifier(aw: int, ah: int, fournisseur: str = "gelato",
              taille: Optional[TailleCatalogue] = None,
              mat_min_frac: float = 0.08) -> PlanMiseEnPage:
    """Plan de mise en page d'une œuvre ``aw×ah`` pour un fournisseur.

    Choisit la taille (la plus proche si non imposée), calcule les marges au ratio
    cible et recommande le comportement de mise à l'échelle. Aucune perte d'image.
    """
    ratio_brut = aw / ah
    orient = _orientation(ratio_brut)
    ratio_oeuvre = max(aw, ah) / min(aw, ah)
    if taille is None:
        taille = meilleure_taille(ratio_oeuvre, fournisseur)

    # ratio cible dans l'orientation de l'œuvre
    ratio_cible = taille.ratio if orient != "portrait" else 1.0 / taille.ratio
    if orient == "carré":
        ratio_cible = 1.0
    ow, oh, mwx, mwy = ouverture(aw, ah, ratio_cible, mat_min_frac)
    marge_h_frac = round(2 * mwx / aw, 3)
    marge_v_frac = round(2 * mwy / ah, 3)
    bordure_pct = round(100 * (1 - (aw * ah) / (ow * oh)), 1)

    if fournisseur == "prodigi":
        strategie = "passe-partout"
        sizing = "fitPrintArea (jamais de crop) + mount activé"
        note = ("Prodigi : commander en fitPrintArea avec passe-partout (mat) — l'œuvre "
                "garde son ratio, le mat physique fournit la marge. Choisir la couleur "
                "de mat (snow white).")
    else:
        strategie = "bordure-fichier"
        sizing = "fillPrintArea (le fichier est déjà au ratio exact → aucun crop)"
        note = ("Gelato : composer le fichier print à la taille catalogue avec la bordure "
                "blanche intégrée (faux passe-partout). Le ratio du fichier = celui du "
                "produit → pas de crop fournisseur.")

    return PlanMiseEnPage(
        taille=taille.label, fournisseur=fournisseur, orientation=orient,
        ratio_oeuvre=round(ratio_oeuvre, 3), ratio_taille=round(taille.ratio, 3),
        marge_h_frac=marge_h_frac, marge_v_frac=marge_v_frac, bordure_pct=bordure_pct,
        sizing_prodigi=sizing, strategie=strategie, note=note,
    )


def plans_variants(aw: int, ah: int, fournisseur: str = "gelato") -> List[PlanMiseEnPage]:
    """Un plan par taille catalogue offerte par le fournisseur (variantes du listing)."""
    return [planifier(aw, ah, fournisseur, t)
            for t in CATALOGUE if fournisseur in t.fournisseurs]
