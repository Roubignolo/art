"""
Connecteur Sourcing — Smithsonian Open Access (CC0).

API : https://api.si.edu/openaccess/api/v1.0/  (clé api.data.gov).
Clé via SMITHSONIAN_API_KEY ; repli automatique sur DEMO_KEY (rate-limité)
pour fonctionner sans inscription — passe une vraie clé pour le volume.

Schéma VÉRIFIÉ en live le 2026-05-31 (DEMO_KEY) :
  response.rows[].content.descriptiveNonRepeating.online_media.media[]
    → { type:"Images", usage:{access:"CC0"}, content:<url>, thumbnail }
  response.rows[].content.freetext.{name[],date[]}  (paires {label,content})

Le Smithsonian ne fournit l'image QUE pour les objets CC0/domaine public →
la présence d'un media CC0 vaut confirmation G1(US)+G3. La date de décès de
l'auteur est rarement structurée → souvent REVIEW (validation humaine), ce qui
est conforme à la philosophie des gates. Aucune invention ([[feedback-no-fabrication]]).
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
import time
from typing import Any, Iterator

from .base import EU_DEATH_CUTOFF, extract_year, trademark_hit, http_get_json

SOURCE_NAME = "smithsonian"
BASE = "https://api.si.edu/openaccess/api/v1.0"
SOURCE_LABEL = "Smithsonian Open Access (CC0)"

# Bande d'ID réservée. ids Smithsonian = chaînes → hash stable dans [500M, 590M).
ID_OFFSET = 500_000_000
_ID_SPAN = 90_000_000

# Labels freetext qui désignent l'auteur d'une œuvre.
_LABELS_AUTEUR = ("maker", "artist", "author", "creator", "painter",
                  "designer", "manufacturer", "attributed to", "engraver", "printmaker")


def _api_key() -> str:
    key = os.environ.get("SMITHSONIAN_API_KEY", "").strip()
    if not key:
        print("  ⚠ SMITHSONIAN_API_KEY absente → repli DEMO_KEY (rate-limité). "
              "Inscris-toi sur https://api.data.gov/signup/ pour le volume.", file=sys.stderr)
        return "DEMO_KEY"
    return key


def _hash_id(sid: str) -> int:
    h = int(hashlib.md5(sid.encode("utf-8")).hexdigest()[:12], 16)
    return ID_OFFSET + (h % _ID_SPAN)


def _search(query: str, start: int, rows: int, key: str) -> dict[str, Any] | None:
    return http_get_json(
        f"{BASE}/search",
        {"q": query, "start": start, "rows": rows, "api_key": key},
    )


def _freetext_list(freetext: dict[str, Any], champ: str) -> list[dict[str, Any]]:
    val = freetext.get(champ)
    return val if isinstance(val, list) else []


def _auteur(freetext: dict[str, Any]) -> str | None:
    for item in _freetext_list(freetext, "name"):
        label = (item.get("label") or "").lower()
        if any(k in label for k in _LABELS_AUTEUR):
            return (item.get("content") or "").strip() or None
    return None


def _media_cc0(dnr: dict[str, Any]) -> str | None:
    """URL image d'un média CC0. Utilise l'endpoint IIIF (full/full = résolution
    native, ~3000px+) plutôt que deliveryService (plafonné à 2000px)."""
    om = dnr.get("online_media")
    media = om.get("media") if isinstance(om, dict) else None
    if not isinstance(media, list):
        return None
    for m in media:
        if (m.get("type") == "Images") and ((m.get("usage") or {}).get("access") == "CC0"):
            ids_id = m.get("idsId")
            if ids_id:
                return f"https://ids.si.edu/ids/iiif/{ids_id}/full/full/0/default.jpg"
            if m.get("content"):
                return m.get("content")
    return None


def _annee_deces(auteur: str | None, freetext: dict[str, Any]) -> int | None:
    """Tente d'extraire une année de décès depuis le nom (« … 1853-1890 ») ou
    une date freetext explicitement labellisée décès."""
    if auteur:
        annees = re.findall(r"\d{4}", auteur)
        if len(annees) >= 2:
            return int(annees[1])
    for item in _freetext_list(freetext, "date"):
        if "death" in (item.get("label") or "").lower():
            y = extract_year(item.get("content"))
            if y:
                return y
    return None


def _date_oeuvre(freetext: dict[str, Any]) -> str | None:
    dates = _freetext_list(freetext, "date")
    for item in dates:
        if (item.get("label") or "").lower() in ("date", "manufacture date", "creation date"):
            return item.get("content")
    return dates[0].get("content") if dates else None


def _normalize(row: dict[str, Any]) -> dict[str, Any]:
    content = row.get("content") or {}
    dnr = content.get("descriptiveNonRepeating") or {}
    freetext = content.get("freetext") or {}

    image_url = _media_cc0(dnr)
    g1_us_g3 = bool(image_url)  # media CC0 fourni = domaine public confirmé par l'institution

    title = row.get("title") or (dnr.get("title") or {}).get("content")
    artist = _auteur(freetext)

    death = _annee_deces(artist, freetext)
    date_str = _date_oeuvre(freetext)
    end = extract_year(date_str)
    if death is not None:
        g1_ue = death <= EU_DEATH_CUTOFF
    elif end is not None:
        g1_ue = end <= 1900
    else:
        g1_ue = None  # → REVIEW

    g2_ok = not trademark_hit(f"{title or ''} {artist or ''}")

    if not g1_us_g3 or not g2_ok:
        decision = "REJET"
    elif g1_ue is False:
        decision = "REJET"
    elif g1_ue is None:
        decision = "REVIEW"
    else:
        decision = "CANDIDAT"

    sid = row.get("id") or ""
    unit = row.get("unitCode") or dnr.get("unit_code")
    return {
        "objectID":         _hash_id(sid) if sid else None,
        "decision":         decision,
        "title":            title,
        "artist":           artist,
        "artist_bio":       artist,
        "artist_death":     death,
        "object_date":      date_str,
        "object_end_year":  end,
        "department":       unit,
        "classification":   row.get("type"),
        "medium":           None,
        "dimensions":       None,
        "credit_line":      (freetext.get("dataSource") or [{}])[0].get("content") if isinstance(freetext.get("dataSource"), list) else None,
        "is_public_domain": g1_us_g3,
        "source":           f"{SOURCE_LABEL} — {unit}" if unit else SOURCE_LABEL,
        "object_url":       dnr.get("record_link") or row.get("url"),
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
        "artist_birth":      (lambda yy: int(yy[0]) if len(yy) >= 2 else None)(re.findall(r"\d{4}", artist or "")),
        "object_begin_year": end,
        "accession_number":  dnr.get("record_ID"),
        "rights_statement":  "CC0 (Smithsonian Open Access · usage.access=CC0)" if g1_us_g3 else None,
        "wikidata_url":      None,
    }


def iter_candidates(query: str, max_scan: int = 200, pause: float = 0.2) -> Iterator[dict[str, Any]]:
    """Itère les objets Smithsonian correspondant à la query, normalisés."""
    key = _api_key()
    # Restreint aux objets disposant d'une image (écarte les notices de
    # bibliothèque sans média) — ceux-ci sont quasi systématiquement CC0.
    q = f'{query} AND online_media_type:"Images"'
    vus = 0
    start = 0
    rows = 100
    while vus < max_scan:
        data = _search(q, start=start, rows=rows, key=key)
        batch = ((data or {}).get("response") or {}).get("rows") or []
        if not batch:
            break
        for row in batch:
            if vus >= max_scan:
                break
            vus += 1
            yield _normalize(row)
        if len(batch) < rows:
            break
        start += rows
        time.sleep(pause)
