"""
Connecteur Sourcing — Art Institute of Chicago (Open Access, CC0).

API publique sans clé : https://api.artic.edu/docs/

Stratégie :
  1. /artworks/search?q=QUERY&fields=... → liste paginée d'œuvres (champs plats)
  2. Filtre is_public_domain + image_id présent
  3. Gates DP/marque/source (G1, G2, G3) ici → CANDIDAT / REVIEW / REJET
  4. G4 résolution : mesurée par l'orchestrateur après téléchargement (IIIF)

Images via IIIF 2.0 : {iiif_url}/{image_id}/full/full/0/default.jpg

Aucune invention : id, titre, dates, image viennent de l'API. Schéma vérifié
en direct le 2026-05-31. La règle [[feedback-no-fabrication]] s'applique.
"""

from __future__ import annotations

import re
import time
from typing import Any, Iterator

from .base import (
    EU_DEATH_CUTOFF,
    extract_year,
    http_get_json,
    trademark_hit,
)

SOURCE_NAME = "artic"
BASE = "https://api.artic.edu/api/v1"
IIIF = "https://www.artic.edu/iiif/2"
SOURCE_LABEL = "Art Institute of Chicago (Open Access, CC0)"

# Bande d'ID réservée (évite les collisions Met/Rijks/BHL). ids AIC < 1M.
ID_OFFSET = 300_000_000

_FIELDS = ",".join([
    "id", "title", "artist_display", "artist_title", "date_display",
    "date_start", "date_end", "medium_display", "dimensions", "credit_line",
    "is_public_domain", "classification_title", "department_title",
    "image_id", "api_link",
])


def _search(query: str, page: int, limit: int = 100) -> dict[str, Any] | None:
    return http_get_json(
        f"{BASE}/artworks/search",
        {"q": query, "fields": _FIELDS, "limit": limit, "page": page},
    )


def _death_year_depuis_display(artist_display: str) -> int | None:
    """Extrait l'année de décès de artist_display (« … 1853–1890 »).

    On prend la 2e année à 4 chiffres (naissance–décès). Une seule année →
    indéterminé (artiste peut-être vivant) → None.
    """
    annees = re.findall(r"\d{4}", artist_display or "")
    if len(annees) >= 2:
        return int(annees[1])
    return None


def _normalize(obj: dict[str, Any]) -> dict[str, Any]:
    g1_us_g3 = bool(obj.get("is_public_domain"))

    # G1(UE) : décès auteur depuis 70+ ans, sinon repli sur l'année de fin d'œuvre.
    death = _death_year_depuis_display(obj.get("artist_display") or "")
    end = obj.get("date_end") if isinstance(obj.get("date_end"), int) else extract_year(obj.get("date_end"))
    if death is not None:
        g1_ue = death <= EU_DEATH_CUTOFF
    elif end is not None:
        g1_ue = end <= 1900
    else:
        g1_ue = None  # → REVIEW

    artist = obj.get("artist_title") or ""
    g2_ok = not trademark_hit(f"{obj.get('title','')} {artist}")

    image_id = obj.get("image_id")
    has_image = bool(image_id)
    image_url = f"{IIIF}/{image_id}/full/full/0/default.jpg" if image_id else None

    if not has_image or not g1_us_g3 or not g2_ok:
        decision = "REJET"
    elif g1_ue is False:
        decision = "REJET"
    elif g1_ue is None:
        decision = "REVIEW"
    else:
        decision = "CANDIDAT"

    aid = obj.get("id")
    return {
        "objectID":         (int(aid) + ID_OFFSET) if aid is not None else None,
        "decision":         decision,
        "title":            obj.get("title"),
        "artist":           artist or None,
        "artist_bio":       obj.get("artist_display"),
        "artist_death":     death,
        "object_date":      obj.get("date_display"),
        "object_end_year":  end,
        "department":       obj.get("department_title"),
        "classification":   obj.get("classification_title"),
        "medium":           obj.get("medium_display"),
        "dimensions":       obj.get("dimensions"),
        "credit_line":      obj.get("credit_line"),
        "is_public_domain": g1_us_g3,
        "source":           SOURCE_LABEL,
        "object_url":       f"https://www.artic.edu/artworks/{aid}" if aid is not None else None,
        "image_url":        image_url,
        "gate_g1_us_g3":    g1_us_g3,
        "gate_g1_ue":       g1_ue,
        "gate_g2_marque":   g2_ok,
        "resolution_px":    0,      # mesurée par l'orchestrateur (IIIF, dims non exposées)
        "width":            None,
        "height":           None,
        "resolution_ok":    None,
        "local_file":       "",
    }


def iter_candidates(query: str, max_scan: int = 300, pause: float = 0.15) -> Iterator[dict[str, Any]]:
    """Itère les œuvres AIC correspondant à la query, normalisées."""
    vus = 0
    page = 1
    while vus < max_scan:
        data = _search(query, page=page)
        rows = (data or {}).get("data") or []
        if not rows:
            break
        for obj in rows:
            if vus >= max_scan:
                break
            vus += 1
            yield _normalize(obj)
        # pagination
        pagination = (data or {}).get("pagination") or {}
        if page >= (pagination.get("total_pages") or page):
            break
        page += 1
        time.sleep(pause)
