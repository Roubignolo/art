"""
Connecteur Sourcing — Biodiversity Heritage Library (BHL).

Clé API GRATUITE requise. Inscription :
  https://www.biodiversitylibrary.org/getapikey.aspx
La clé arrive instantanément. À mettre dans BHL_API_KEY.

Doc API v3 : https://about.biodiversitylibrary.org/api-documentation/

Particularité importante vs Met / Rijksmuseum :
  BHL est une fédération d'ouvrages scientifiques digitalisés (XVIIIe-XIXe
  surtout). L'unité d'« œuvre » la plus pertinente pour le POD est la PAGE
  d'illustration (planche botanique, planche zoologique). On utilise donc :

  1. PublicationSearch sur la query → liste de titres
  2. Pour chaque titre, GetTitleMetadata pour récupérer le 1er Item disponible
     et ses métadonnées (auteur, année)
  3. GetItemPages pour lister les pages, puis on filtre les pages dont
     le TypeOfText = "Illustration" (ou équivalent)
  4. Chaque page d'illustration retenue devient un SourcingRecord

Identifiants : on prefixe les PageIDs par ID_OFFSET = 20_000_000 pour éviter
toute collision avec Met (≤ ~10M) et Rijksmuseum (10M-20M).

Limites Phase 0 :
  - On ne consomme PAS la résolution depuis l'API (pas exposée), donc on
    laisse `resolution_px` à 0 et l'orchestrateur télécharge l'image pour
    vérifier le gate G4.
  - L'auteur d'une page est l'auteur de l'ouvrage (souvent = scientifique
    auteur du livre, pas l'illustrateur). À affiner manuellement avant Etsy.
"""

from __future__ import annotations

import os
import time
from typing import Any, Iterator

from .base import (
    EU_DEATH_CUTOFF,
    extract_year,
    http_get_json,
    trademark_hit,
)

SOURCE_NAME = "bhl"
BASE = "https://www.biodiversitylibrary.org/api3"
SOURCE_LABEL = "Biodiversity Heritage Library (Public Domain)"

# Décale les IDs BHL pour éviter collisions avec Met (< 10M) et Rijks (10M-20M).
ID_OFFSET = 20_000_000

# Volume de scan minimal — chaque titre génère N pages, donc on est vite à
# beaucoup de records. On limite agressivement par défaut.
DEFAULT_TITLES_TO_SCAN = 5
DEFAULT_PAGES_PER_TITLE = 30


def _require_key() -> str:
    key = os.environ.get("BHL_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "BHL_API_KEY non défini. Inscris-toi sur "
            "https://www.biodiversitylibrary.org/getapikey.aspx (gratuit), "
            "puis exporte la clé."
        )
    return key


def _call(op: str, **params: Any) -> dict[str, Any] | None:
    """GET sur l'endpoint api3 avec l'op donnée. Renvoie le bloc Result ou None."""
    return http_get_json(BASE, {"op": op, "apikey": _require_key(), "format": "json", **params})


def _publication_search(query: str) -> list[dict[str, Any]]:
    data = _call("PublicationSearch", searchterm=query, searchtype="C")
    return (data or {}).get("Result") or []


def _title_metadata(title_id: str) -> dict[str, Any] | None:
    data = _call("GetTitleMetadata", id=title_id, items="t")
    res = (data or {}).get("Result") or []
    return res[0] if res else None


def _item_pages(item_id: str) -> list[dict[str, Any]]:
    data = _call("GetItemMetadata", id=item_id, pages="t", ocr="f", parts="f")
    res = (data or {}).get("Result") or []
    if not res:
        return []
    return res[0].get("Pages") or []


def _author_summary(authors: list[dict[str, Any]]) -> tuple[str | None, str | None, int | None]:
    """Renvoie (display_name, bio_str, death_year) à partir d'Authors[]."""
    if not authors:
        return None, None, None
    a = authors[0]
    name = (a.get("Name") or a.get("FullName") or "").strip() or None
    dates = (a.get("Dates") or "").strip()
    # Dates BHL souvent au format "1758-1830" ou "1707-1778"
    death_year: int | None = None
    if "-" in dates:
        try:
            death_year = int(dates.split("-")[1][:4])
        except (ValueError, IndexError):
            death_year = None
    bio = dates if dates else None
    return name, bio, death_year


def _is_illustration_page(p: dict[str, Any]) -> bool:
    """Page de PLANCHE uniquement : PageType explicite Illustration/Plate/Foldout.

    On EXIGE le type explicite — le repli « OCR vide » d'avant ramenait les
    couvertures et pages blanches (un scan de couverture n'a pas d'OCR) → on
    sourçait des reliures, pas des planches. Voir docs/audit-rentabilite.md §T2.
    """
    for pt in (p.get("PageTypes") or []):
        name = (pt.get("PageTypeName") or "").lower()
        if "illustration" in name or "plate" in name or "foldout" in name:
            return True
    return False


def iter_candidates(
    query: str,
    max_titles: int = DEFAULT_TITLES_TO_SCAN,
    pages_per_title: int = DEFAULT_PAGES_PER_TITLE,
    pause: float = 0.2,
) -> Iterator[dict[str, Any]]:
    """Itère les pages d'illustration BHL pour la query.

    Stratégie : sur les `max_titles` premiers ouvrages trouvés, prend au plus
    `pages_per_title` pages identifiées comme illustrations.
    """
    titles = _publication_search(query)
    if not titles:
        return

    for pub in titles[:max_titles]:
        title_id = pub.get("TitleID")
        if not title_id:
            continue
        meta = _title_metadata(str(title_id))
        time.sleep(pause)
        if not meta:
            continue

        items = meta.get("Items") or []
        if not items:
            continue
        # Premier item disponible (souvent il y en a plusieurs volumes/éditions)
        item = items[0]
        item_id = item.get("ItemID")
        if not item_id:
            continue

        artist, bio, death = _author_summary(meta.get("Authors") or [])
        pub_year = extract_year(meta.get("PublicationDate"))
        book_title = (meta.get("FullTitle") or meta.get("ShortTitle") or "").strip()
        item_url = item.get("ItemUrl") or f"https://www.biodiversitylibrary.org/item/{item_id}"

        pages = _item_pages(str(item_id))
        time.sleep(pause)
        illus_pages = [p for p in pages if _is_illustration_page(p)][:pages_per_title]

        for p in illus_pages:
            page_id = p.get("PageID")
            if not page_id:
                continue

            # G1 US (publication ≤ 1930) — BHL agrège du contenu public domain US.
            g1_us_g3 = (pub_year is not None and pub_year <= 1930)

            # G1 UE (auteur † + 70). Si pas de date d'auteur, fallback sur pub
            # ≤ 1900 comme marge de sécurité.
            if death is not None:
                g1_ue = death <= EU_DEATH_CUTOFF
            elif pub_year is not None:
                g1_ue = pub_year <= 1900
            else:
                g1_ue = None

            # G2 marque
            g2_ok = not trademark_hit(f"{book_title} {artist or ''}")

            decision = "CANDIDAT"
            if not g1_us_g3 or not g2_ok:
                decision = "REJET"
            elif g1_ue is False:
                decision = "REJET"
            elif g1_ue is None:
                decision = "REVIEW"

            page_num = p.get("PageNumbers", [{}])[0].get("Number") if p.get("PageNumbers") else None
            short_title = (book_title[:80] + "…") if len(book_title) > 80 else book_title
            yield {
                "objectID":         int(page_id) + ID_OFFSET,
                "decision":         decision,
                "title":            f"{short_title} — page {page_num}" if page_num else short_title,
                "artist":           artist,
                "artist_bio":       bio,
                "artist_death":     str(death) if death else None,
                "object_date":      str(pub_year) if pub_year else (meta.get("PublicationDate") or None),
                "object_end_year":  pub_year,
                "department":       "Biodiversity / Natural History",
                "classification":   "Illustration",
                "medium":           None,  # BHL ne distingue pas systématiquement gravure/litho/aquarelle
                "dimensions":       None,
                "credit_line":      meta.get("ContributorName"),
                "is_public_domain": True,
                "source":           SOURCE_LABEL,
                "object_url":       f"https://www.biodiversitylibrary.org/page/{page_id}",
                "image_url":        f"https://www.biodiversitylibrary.org/pageimage/{page_id}",
                "gate_g1_us_g3":    g1_us_g3,
                "gate_g1_ue":       g1_ue,
                "gate_g2_marque":   g2_ok,
                "resolution_px":    0,        # à mesurer par l'orchestrateur
                "width":            None,
                "height":           None,
                "resolution_ok":    None,
                "local_file":       "",
                # ── Preuve domaine public ──
                "artist_birth":      extract_year(bio),
                "object_begin_year": pub_year,
                "accession_number":  None,
                "rights_statement":  "Public Domain (Biodiversity Heritage Library)",
                "wikidata_url":      None,
                "_book_url":        item_url,  # debug / traçabilité
            }
