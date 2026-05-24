"""
Connecteur Sourcing — Rijksmuseum (Amsterdam, CC0 par défaut).

Clé API GRATUITE requise. Inscription :
  https://www.rijksmuseum.nl/en/research/conduct-research/data/api
La clé arrive par email après création d'un compte Rijksstudio (instantané).
À mettre dans la variable d'environnement RIJKSMUSEUM_API_KEY.

Doc API : https://data.rijksmuseum.nl/object-metadata/api/

Particularités vs Met :
  - Le Rijksmuseum publie webImage.width / webImage.height → on évite un
    téléchargement complet pour mesurer la résolution (gate G4 fait sans IO).
  - Les objectNumber sont des strings ("SK-C-5"). On utilise le `priref` (int)
    auquel on AJOUTE 10_000_000 pour garantir l'unicité côté DB face aux
    objectIDs Met (qui restent dans la plage [0, ~10_000_000]).
  - permitDownload=False → on rejette (rare mais existe pour œuvres récentes).
"""

from __future__ import annotations

import os
import time
from typing import Any, Iterator
from urllib.parse import quote

from .base import (
    DEFAULT_MIN_LONG_EDGE,
    EU_DEATH_CUTOFF,
    extract_year,
    http_get_json,
    trademark_hit,
)

SOURCE_NAME = "rijksmuseum"
BASE = "https://www.rijksmuseum.nl/api/en"
SOURCE_LABEL = "Rijksmuseum, Amsterdam (Rijksstudio, CC0)"

# Décale les IDs Rijks pour éviter toute collision avec ceux du Met.
ID_OFFSET = 10_000_000


def _require_key() -> str:
    key = os.environ.get("RIJKSMUSEUM_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "RIJKSMUSEUM_API_KEY non défini. Inscris-toi sur "
            "https://www.rijksmuseum.nl/en/research/conduct-research/data/api "
            "(gratuit, instantané), puis exporte la clé."
        )
    return key


def _search(query: str, page_size: int) -> list[dict[str, Any]]:
    """Renvoie une page de résultats Rijksstudio (objets avec image)."""
    data = http_get_json(f"{BASE}/collection", {
        "key": _require_key(),
        "q": query,
        "imgonly": "True",
        "format": "json",
        "ps": str(min(page_size, 100)),
    })
    return (data or {}).get("artObjects") or []


def _fetch_detail(object_number: str) -> dict[str, Any] | None:
    data = http_get_json(f"{BASE}/collection/{quote(object_number, safe='')}", {
        "key": _require_key(),
        "format": "json",
    })
    return ((data or {}).get("artObject")) or None


def _normalize(obj: dict[str, Any], min_long_edge: int) -> dict[str, Any]:
    web_image = obj.get("webImage") or {}
    width  = int(web_image.get("width")  or 0)
    height = int(web_image.get("height") or 0)
    long_edge = max(width, height)

    # principalMakers[0] est plus fiable que `principalOrFirstMaker` pour les dates.
    makers = obj.get("principalMakers") or []
    maker  = makers[0] if makers else {}
    death  = extract_year(maker.get("dateOfDeath"))

    dating = obj.get("dating") or {}
    year_late = dating.get("yearLate")

    # G1(UE) : auteur mort ≥70 ans. Fallback : œuvre datant d'avant 1900.
    if death is not None:
        g1_ue = death <= EU_DEATH_CUTOFF
    elif isinstance(year_late, int) and year_late > 0:
        g1_ue = year_late <= 1900
    else:
        g1_ue = None

    # G1(US) + G3 source : Rijks Rijksstudio est CC0 par défaut, et
    # `permitDownload` confirme l'autorisation de téléchargement.
    permit = obj.get("permitDownload", True)
    g1_us_g3 = bool(permit)

    # G2 marque résiduelle
    title = obj.get("title") or ""
    artist = (maker.get("name") or obj.get("principalOrFirstMaker") or "") if maker else (obj.get("principalOrFirstMaker") or "")
    g2_ok = not trademark_hit(f"{title} {artist}")

    # G4 résolution : ici on l'a déjà via webImage → décision finale immédiate
    res_ok = long_edge >= min_long_edge if long_edge else None

    has_image = bool(web_image.get("url"))

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

    priref = obj.get("priref") or 0
    object_number = obj.get("objectNumber") or ""

    return {
        "objectID":         (int(priref) + ID_OFFSET) if priref else None,
        "decision":         decision,
        "title":            obj.get("title"),
        "artist":           artist or None,
        "artist_bio":       _maker_bio(maker),
        "artist_death":     maker.get("dateOfDeath"),
        "object_date":      (obj.get("label") or {}).get("date") or dating.get("presentingDate"),
        "object_end_year":  year_late,
        "department":       _join(obj.get("classification", {}).get("iconClassDescription") or []),
        "classification":   _join((obj.get("objectTypes") or []) or (obj.get("techniques") or [])),
        "medium":           obj.get("physicalMedium") or _join(obj.get("materials") or []),
        "dimensions":       obj.get("subTitle"),
        "credit_line":      _join(obj.get("acquisition", {}).get("creditLine", []) if isinstance(obj.get("acquisition"), dict) else []),
        "is_public_domain": True,
        "source":           SOURCE_LABEL,
        "object_url":       (obj.get("links") or {}).get("web") or f"https://www.rijksmuseum.nl/en/collection/{object_number}",
        "image_url":        web_image.get("url"),
        "gate_g1_us_g3":    g1_us_g3,
        "gate_g1_ue":       g1_ue,
        "gate_g2_marque":   g2_ok,
        "resolution_px":    long_edge,
        "width":            width or None,
        "height":           height or None,
        "resolution_ok":    res_ok,
        "local_file":       "",
    }


def _join(parts: list[Any]) -> str | None:
    items = [str(p).strip() for p in parts if str(p).strip()]
    return ", ".join(items) if items else None


def _maker_bio(maker: dict[str, Any]) -> str | None:
    if not maker:
        return None
    nat = maker.get("nationality")
    birth = extract_year(maker.get("dateOfBirth"))
    death = extract_year(maker.get("dateOfDeath"))
    pieces: list[str] = []
    if nat:
        pieces.append(nat)
    if birth or death:
        pieces.append(f"{birth or '?'}–{death or '?'}")
    return ", ".join(pieces) if pieces else None


def iter_candidates(
    query: str,
    max_scan: int = 100,
    pause: float = 0.15,
    min_long_edge: int = DEFAULT_MIN_LONG_EDGE,
) -> Iterator[dict[str, Any]]:
    """Itère les œuvres Rijks correspondant à `query`, normalisées.

    On enchaîne search-listing → /collection/{objectNumber} pour chaque hit,
    parce que la search ne renvoie qu'un résumé (pas les principalMakers
    complets ni les dates fiables).
    """
    listing = _search(query, page_size=min(max_scan, 100))
    for short in listing[:max_scan]:
        on = short.get("objectNumber")
        if not on:
            continue
        detail = _fetch_detail(on)
        time.sleep(pause)
        if not detail:
            continue
        yield _normalize(detail, min_long_edge=min_long_edge)
