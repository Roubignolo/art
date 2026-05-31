"""
Connecteur Sourcing — Europeana (agrégateur européen, domaine public / CC0).

API : https://api.europeana.eu/record/v2/search.json  (clé wskey).
Clé via EUROPEANA_API_KEY ; repli sur la clé de démo « api2demo » (rate-limité)
pour fonctionner sans inscription.

Europeana agrège des centaines d'institutions — dont **Paris Musées et les
musées français**, le Rijksmuseum, etc. On filtre strictement sur les droits
domaine public / CC0 (G3) : seuls « publicdomain » (mark/zero) et « NoC »
(No Copyright) sont retenus ; CC-BY et plus restrictifs → REJET.

Schéma VÉRIFIÉ en live le 2026-05-31 (api2demo) :
  items[].{ id, title[], dataProvider[], rights[], edmIsShownBy[]<url image>,
            edmPreview[], year[], dcCreator[], guid }

Aucune invention ([[feedback-no-fabrication]]).
"""

from __future__ import annotations

import hashlib
import os
import sys
import time
from typing import Any, Iterator

from .base import EU_DEATH_CUTOFF, extract_year, trademark_hit, http_get_json

SOURCE_NAME = "europeana"
BASE = "https://api.europeana.eu/record/v2/search.json"
SOURCE_LABEL = "Europeana"

# Bande d'ID réservée. ids Europeana = chaînes (« /90402/SK_A_3262 ») → hash.
ID_OFFSET = 600_000_000
_ID_SPAN = 90_000_000

# Mentions de droits acceptées comme domaine public / CC0 (G3).
_DROITS_LIBRES = ("publicdomain", "rightsstatements.org/vocab/noc")


def _api_key() -> str:
    key = os.environ.get("EUROPEANA_API_KEY", "").strip()
    if not key:
        print("  ⚠ EUROPEANA_API_KEY absente → repli api2demo (rate-limité). "
              "Clé personnelle gratuite (instantanée) : https://pro.europeana.eu/page/get-api", file=sys.stderr)
        return "api2demo"
    return key


def _hash_id(sid: str) -> int:
    h = int(hashlib.md5(sid.encode("utf-8")).hexdigest()[:12], 16)
    return ID_OFFSET + (h % _ID_SPAN)


def _first(val: Any) -> Any:
    if isinstance(val, list):
        return val[0] if val else None
    return val


def _search(query: str, start: int, rows: int, key: str) -> dict[str, Any] | None:
    return http_get_json(BASE, {
        "wskey": key,
        "query": query,
        "qf": "TYPE:IMAGE",
        "reusability": "open",   # CC0/PD/CC-BY… puis on filtre les droits en interne
        "media": "true",         # garantit un edmIsShownBy exploitable
        "start": start,
        "rows": rows,
    })


def _normalize(item: dict[str, Any]) -> dict[str, Any]:
    rights_url = _first(item.get("rights"))
    rights = (rights_url or "").lower()
    g1_us_g3 = any(tok in rights for tok in _DROITS_LIBRES)

    title = _first(item.get("title"))
    artist = _first(item.get("dcCreator"))
    provider = _first(item.get("dataProvider")) or _first(item.get("provider"))

    year = extract_year(_first(item.get("year")))
    # Europeana expose rarement la date de décès → on s'appuie sur l'année d'œuvre.
    if year is not None:
        g1_ue = year <= 1900
    else:
        g1_ue = None  # → REVIEW

    g2_ok = not trademark_hit(f"{title or ''} {artist or ''}")

    image_url = _first(item.get("edmIsShownBy")) or _first(item.get("edmPreview"))
    has_image = bool(image_url)

    if not has_image or not g1_us_g3 or not g2_ok:
        decision = "REJET"
    elif g1_ue is False:
        decision = "REJET"
    elif g1_ue is None:
        decision = "REVIEW"
    else:
        decision = "CANDIDAT"

    sid = item.get("id") or ""
    return {
        "objectID":         _hash_id(sid) if sid else None,
        "decision":         decision,
        "title":            title,
        "artist":           artist,
        "artist_bio":       None,
        "artist_death":     None,
        "object_date":      _first(item.get("year")),
        "object_end_year":  year,
        "department":       _first(item.get("country")),
        "classification":   None,
        "medium":           None,
        "dimensions":       None,
        "credit_line":      provider,
        "is_public_domain": g1_us_g3,
        "source":           f"{provider} via {SOURCE_LABEL} ({rights or 'droits ?'})" if provider else SOURCE_LABEL,
        "object_url":       item.get("guid") or _first(item.get("edmIsShownAt")),
        "image_url":        image_url,
        "gate_g1_us_g3":    g1_us_g3,
        "gate_g1_ue":       g1_ue,
        "gate_g2_marque":   g2_ok,
        "resolution_px":    0,      # mesurée par l'orchestrateur après téléchargement
        "width":            None,
        "height":           None,
        "resolution_ok":    None,
        "local_file":       "",
        # ── Preuve domaine public ──
        "artist_birth":      None,
        "object_begin_year": year,
        "accession_number":  None,
        "rights_statement":  rights_url,   # URL de licence Europeana (PD Mark / CC0 / NoC)
        "wikidata_url":      None,
    }


def iter_candidates(query: str, max_scan: int = 200, pause: float = 0.2) -> Iterator[dict[str, Any]]:
    """Itère les objets Europeana (domaine public/CC0) correspondant à la query."""
    key = _api_key()
    vus = 0
    start = 1   # Europeana : start est 1-based
    rows = 100
    while vus < max_scan:
        data = _search(query, start=start, rows=rows, key=key)
        items = (data or {}).get("items") or []
        if not items:
            break
        for item in items:
            if vus >= max_scan:
                break
            vus += 1
            yield _normalize(item)
        if len(items) < rows:
            break
        start += rows
        time.sleep(pause)
