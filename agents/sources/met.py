"""
Connecteur Sourcing — Metropolitan Museum of Art (Open Access, CC0).

API publique sans clé : https://metmuseum.github.io/

Stratégie :
  1. /search?q=QUERY&hasImages=true → liste d'objectIDs
  2. /objects/{id} → métadonnées détaillées
  3. Application des gates DP/marque/source (G1, G2, G3) ici
     → décision = CANDIDAT / REVIEW / REJET
  4. G4 résolution : vérifiée par l'orchestrateur après téléchargement image

Aucune invention : objectID, titre, image_url, dates viennent tous
directement de l'API. La règle [[feedback-no-fabrication]] s'applique.
"""

from __future__ import annotations

import time
from typing import Any, Iterator

from .base import (
    EU_DEATH_CUTOFF,
    extract_year,
    http_get_json,
    trademark_hit,
)

SOURCE_NAME = "met"
BASE = "https://collectionapi.metmuseum.org/public/collection/v1"
SOURCE_LABEL = "The Metropolitan Museum of Art (Open Access, CC0)"


def _search_object_ids(query: str) -> list[int]:
    """Renvoie les objectIDs candidats (filtrés sur hasImages côté API)."""
    data = http_get_json(f"{BASE}/search", {"q": query, "hasImages": "true"})
    return (data or {}).get("objectIDs") or []


def _fetch_object(object_id: int) -> dict[str, Any] | None:
    return http_get_json(f"{BASE}/objects/{object_id}")


def _normalize(obj: dict[str, Any]) -> dict[str, Any]:
    """Applique les gates G1/G2/G3 (G4 résolution = orchestrateur) et produit
    un SourcingRecord prêt à être complété par width/height/local_file."""
    # G3 + G1(US) : le Met confirme le domaine public (CC0) via isPublicDomain
    g1_us_g3 = bool(obj.get("isPublicDomain"))

    # G1(UE) : auteur mort depuis 70+ ans. Si la date est inconnue mais que
    # l'œuvre date d'avant 1900, on assume aussi DP (marge de sécurité).
    death = extract_year(obj.get("artistEndDate"))
    end   = extract_year(obj.get("objectEndDate"))
    if death is not None:
        g1_ue = death <= EU_DEATH_CUTOFF
    elif end is not None:
        g1_ue = end <= 1900
    else:
        g1_ue = None  # → REVIEW (validation humaine)

    # G2 : marque résiduelle
    hay = f"{obj.get('title','')} {obj.get('artistDisplayName','')}"
    g2_ok = not trademark_hit(hay)

    has_image = bool(obj.get("primaryImage"))

    if not has_image or not g1_us_g3 or not g2_ok:
        decision = "REJET"
    elif g1_ue is False:
        decision = "REJET"
    elif g1_ue is None:
        decision = "REVIEW"
    else:
        decision = "CANDIDAT"

    return {
        "objectID":         obj.get("objectID"),
        "decision":         decision,
        "title":            obj.get("title"),
        "artist":           obj.get("artistDisplayName"),
        "artist_bio":       obj.get("artistDisplayBio"),
        "artist_death":     obj.get("artistEndDate"),
        "object_date":      obj.get("objectDate"),
        "object_end_year":  obj.get("objectEndDate"),
        "department":       obj.get("department"),
        "classification":   obj.get("classification"),
        "medium":           obj.get("medium"),
        "dimensions":       obj.get("dimensions"),
        "credit_line":      obj.get("creditLine"),
        "is_public_domain": obj.get("isPublicDomain"),
        "source":           SOURCE_LABEL,
        "object_url":       obj.get("objectURL"),
        "image_url":        obj.get("primaryImage"),
        "gate_g1_us_g3":    g1_us_g3,
        "gate_g1_ue":       g1_ue,
        "gate_g2_marque":   g2_ok,
        "resolution_px":    0,
        "width":            None,
        "height":           None,
        "resolution_ok":    None,  # rempli par l'orchestrateur après check résolution
        "local_file":       "",
    }


def iter_candidates(query: str, max_scan: int = 300, pause: float = 0.15) -> Iterator[dict[str, Any]]:
    """Itère les objets Met correspondant à la query, normalisés.

    L'appelant doit gérer le téléchargement image + gate G4 (résolution)
    et l'arrêt à `target` candidats retenus.
    """
    ids = _search_object_ids(query)
    for oid in ids[:max_scan]:
        obj = _fetch_object(oid)
        time.sleep(pause)
        if not obj:
            continue
        yield _normalize(obj)
