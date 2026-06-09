"""Tagging des œuvres pour les collections Vellum & Cie.

Trois axes (cf. agents/tagging_data.json) :
  • SUJET — déduit par mots-clés des métadonnées musée (titre, objectName,
    classification, medium, department, tags curés du Met).
  • MOUVEMENT — déduit de l'artiste via une table vérifiée domaine public ;
    repli sur la culture (estampes japonaises → Ukiyo-e).
  • PALETTE — injecté depuis l'analyse couleur (agents/render/palette.py).

Déterministe, gratuit, sans LLM. Aucune invention : tout vient des métadonnées.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Dict, List, Optional

_PATH = os.path.join(os.path.dirname(__file__), "tagging_data.json")
with open(_PATH, encoding="utf-8") as _f:
    DATA = json.load(_f)

AXES: Dict[str, List[str]] = DATA["axes"]
SUJET_MOTS: Dict[str, List[str]] = DATA["sujet_mots_cles"]
ARTISTE_MVT: Dict[str, str] = DATA["artiste_vers_mouvement"]
REQUETES = DATA["requetes_sourcing"]


def _norm_artiste(s: Optional[str]) -> str:
    s = re.sub(r"\(.*?\)", "", s or "")  # retire les parenthèses « (Rembrandt van Rijn) »
    # insensible aux accents : le Met écrit « Edouard Manet », la table « Édouard Manet »
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


_MVT_NORM = {_norm_artiste(k): v for k, v in ARTISTE_MVT.items()}


def tag_mouvement(rec: Dict) -> Optional[str]:
    """Mouvement de l'œuvre via l'artiste (table DP), repli sur la culture."""
    na = _norm_artiste(rec.get("artist"))
    if na:
        if na in _MVT_NORM:
            return _MVT_NORM[na]
        # correspondance partielle (nom de famille présent des deux côtés)
        for cle, mvt in _MVT_NORM.items():
            if cle and (cle in na or na in cle):
                return mvt
    if "japan" in (rec.get("culture") or "").lower():
        return "Ukiyo-e"
    return None


def tags_sujet(rec: Dict) -> List[str]:
    """Sujets de l'œuvre par mots-clés (titre + objectName + classification +
    medium + department + tags curés). Une œuvre peut cumuler plusieurs sujets."""
    parts = [
        rec.get("title"), rec.get("object_name"), rec.get("classification"),
        rec.get("medium"), rec.get("department"), " ".join(rec.get("tags") or []),
    ]
    hay = " ".join(p for p in parts if p).lower()
    out: List[str] = []
    for sujet, mots in SUJET_MOTS.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", hay) for kw in mots):
            out.append(sujet)
    return out


def tag_oeuvre(rec: Dict, palette_tags: Optional[List[str]] = None) -> Dict:
    """Assemble les 3 axes → {sujet, mouvement, palette, collections}."""
    sujets = tags_sujet(rec)
    mvt = tag_mouvement(rec)
    palette = list(palette_tags or [])
    collections: List[str] = []
    for t in [*sujets, *( [mvt] if mvt else [] ), *palette]:
        if t and t not in collections:
            collections.append(t)
    return {"sujet": sujets, "mouvement": mvt, "palette": palette, "collections": collections}
