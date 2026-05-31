"""
Connecteur Sourcing — Cleveland Museum of Art (Open Access, CC0).

API publique sans clé : https://openaccess-api.clevelandart.org/

Stratégie :
  1. /api/artworks/?q=QUERY&cc0=1&has_image=1 → œuvres CC0 avec image (champs complets)
  2. Gates DP/marque/source (G1, G2, G3) ici → CANDIDAT / REVIEW / REJET
  3. G4 résolution : DÉJÀ connue via images.{full|print}.{width,height} → décision
     finale immédiate, sans téléchargement (comme Rijksmuseum).

Atouts qualité : creators[].death_year structuré (gate UE fiable) + dimensions
image exposées. Master = images.full (TIFF) si dispo, sinon print/web.

Schéma vérifié en direct le 2026-05-31. Aucune invention ([[feedback-no-fabrication]]).
"""

from __future__ import annotations

import time
from typing import Any, Iterator

from .base import (
    DEFAULT_MIN_LONG_EDGE,
    EU_DEATH_CUTOFF,
    extract_year,
    trademark_hit,
)
from .base import http_get_json

SOURCE_NAME = "cleveland"
BASE = "https://openaccess-api.clevelandart.org/api"
SOURCE_LABEL = "Cleveland Museum of Art (Open Access, CC0)"

# Bande d'ID réservée (évite les collisions Met/Rijks/BHL/AIC). ids CMA < 1M.
ID_OFFSET = 400_000_000


def _search(query: str, skip: int, limit: int = 100) -> dict[str, Any] | None:
    return http_get_json(
        f"{BASE}/artworks/",
        {"q": query, "cc0": 1, "has_image": 1, "limit": limit, "skip": skip},
    )


def _createur_principal(creators: list[dict[str, Any]]) -> dict[str, Any]:
    if not creators:
        return {}
    for c in creators:
        if "artist" in (c.get("role") or "").lower():
            return c
    return creators[0]


def _image_master(images: dict[str, Any]) -> tuple[str | None, int, int]:
    """Renvoie (url, width, height) du meilleur tier dispo (full > print > web)."""
    for tier in ("full", "print", "web"):
        img = images.get(tier) if isinstance(images, dict) else None
        if isinstance(img, dict) and img.get("url"):
            w = int(img.get("width") or 0)
            h = int(img.get("height") or 0)
            return img["url"], w, h
    return None, 0, 0


def _normalize(obj: dict[str, Any], min_long_edge: int) -> dict[str, Any]:
    g1_us_g3 = (obj.get("share_license_status") or "").upper() == "CC0"

    createur = _createur_principal(obj.get("creators") or [])
    description = createur.get("description") or ""
    artist = description.split(" (")[0].strip() or None
    death = createur.get("death_year") if isinstance(createur.get("death_year"), int) else extract_year(createur.get("death_year"))
    end = obj.get("creation_date_latest") if isinstance(obj.get("creation_date_latest"), int) else extract_year(obj.get("creation_date_latest"))

    if death is not None and death > 0:
        g1_ue = death <= EU_DEATH_CUTOFF
    elif end is not None:
        g1_ue = end <= 1900
    else:
        g1_ue = None  # → REVIEW

    g2_ok = not trademark_hit(f"{obj.get('title','')} {artist or ''}")

    url, width, height = _image_master(obj.get("images") or {})
    long_edge = max(width, height)
    res_ok = (long_edge >= min_long_edge) if long_edge else None
    has_image = bool(url)

    if not has_image or not g1_us_g3 or not g2_ok:
        decision = "REJET"
    elif res_ok is False:
        decision = "REJET"
    elif g1_ue is False:
        decision = "REJET"
    elif g1_ue is None:
        decision = "REVIEW"
    else:
        decision = "CANDIDAT"

    cid = obj.get("id")
    bio = description or None

    return {
        "objectID":         (int(cid) + ID_OFFSET) if cid is not None else None,
        "decision":         decision,
        "title":            obj.get("title"),
        "artist":           artist,
        "artist_bio":       bio,
        "artist_death":     death,
        "object_date":      obj.get("creation_date"),
        "object_end_year":  end,
        "department":       obj.get("department"),
        "classification":   obj.get("type"),
        "medium":           obj.get("technique"),
        "dimensions":       obj.get("measurements"),
        "credit_line":      obj.get("creditline") or obj.get("tombstone"),
        "is_public_domain": g1_us_g3,
        "source":           SOURCE_LABEL,
        "object_url":       obj.get("url") or (f"https://www.clevelandart.org/art/{obj.get('accession_number')}" if obj.get("accession_number") else None),
        "image_url":        url,
        "gate_g1_us_g3":    g1_us_g3,
        "gate_g1_ue":       g1_ue,
        "gate_g2_marque":   g2_ok,
        "resolution_px":    long_edge,
        "width":            width or None,
        "height":           height or None,
        "resolution_ok":    res_ok,
        "local_file":       "",
        # ── Preuve domaine public ──
        "artist_birth":      createur.get("birth_year"),
        "object_begin_year": obj.get("creation_date_earliest"),
        "accession_number":  obj.get("accession_number"),
        "rights_statement":  obj.get("share_license_status"),
        "wikidata_url":      None,
    }


def iter_candidates(query: str, max_scan: int = 200, pause: float = 0.15,
                    min_long_edge: int = DEFAULT_MIN_LONG_EDGE) -> Iterator[dict[str, Any]]:
    """Itère les œuvres CC0 de Cleveland correspondant à la query."""
    vus = 0
    skip = 0
    limit = 100
    while vus < max_scan:
        data = _search(query, skip=skip, limit=limit)
        rows = (data or {}).get("data") or []
        if not rows:
            break
        for obj in rows:
            if vus >= max_scan:
                break
            vus += 1
            yield _normalize(obj, min_long_edge)
        if len(rows) < limit:
            break
        skip += limit
        time.sleep(pause)
