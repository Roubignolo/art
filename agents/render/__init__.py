"""Moteur de rendu Vellum & Cie — restauration + mockups + carte de provenance.

100 % local (Pillow), zéro clé requise. Bascule sur Replicate (upscale réel)
si REPLICATE_API_TOKEN est posé. Conçu pour alimenter les fiches Etsy
(10 visuels = 10 slots) et l'insert provenance physique.

API publique :
    from agents.render import restaurer, generer_galerie, generer_carte, InfosProvenance
"""

from __future__ import annotations

from .mockup import (
    comparatif_tailles,
    composer_fichier_print,
    detail_texture,
    encadre_sur_mur,
    generer_galerie,
    lifestyle,
    options_cadres,
    poster_nu,
)
from .couleur import assurer_srgb, rapport_gamut, srgb_icc_bytes, taguer_srgb
from .fidelity import RapportFidelite, auditer_fidelite, formater_rapport
from .layout import PlanMiseEnPage, meilleure_taille, planifier, plans_variants
from .provenance_card import InfosProvenance, generer_carte, recto, verso, sceau
from .restoration import RapportRestauration, charger, composer_avant_apres, restaurer

__all__ = [
    "restaurer",
    "RapportRestauration",
    "auditer_fidelite",
    "RapportFidelite",
    "formater_rapport",
    "assurer_srgb",
    "rapport_gamut",
    "srgb_icc_bytes",
    "taguer_srgb",
    "planifier",
    "plans_variants",
    "meilleure_taille",
    "PlanMiseEnPage",
    "charger",
    "composer_avant_apres",
    "generer_galerie",
    "composer_fichier_print",
    "poster_nu",
    "encadre_sur_mur",
    "detail_texture",
    "options_cadres",
    "comparatif_tailles",
    "lifestyle",
    "InfosProvenance",
    "generer_carte",
    "recto",
    "verso",
    "sceau",
]
