"""
Enrichissement « preuve de domaine public » via Wikidata — gratuit (SPARQL).

Deux stratégies, par ordre de fiabilité :
  1. Par identifiant d'œuvre : Met (P3634) → l'item Wikidata de l'œuvre, d'où
     l'on lit le créateur, son décès (P570), l'inception (P571) et SURTOUT le
     statut de droit d'auteur (P6216, ex. « public domain ») — recoupement
     indépendant et autoritaire.
  2. Fallback universel : par NOM d'auteur → date de décès (P570). Marche pour
     toutes les sources. Si le nom est ambigu (plusieurs décès distincts), on
     n'affirme RIEN (pas d'invention).

Coût : nul (endpoint public). On n'enrichit que les œuvres qui en ont besoin
(décès manquant / gate UE indéterminé), pour rester poli avec le service.
"""

from __future__ import annotations

import time
from typing import Any

from .base import EU_DEATH_CUTOFF, extract_year, http_get_json

SPARQL = "https://query.wikidata.org/sparql"


def _query(q: str) -> list[dict[str, Any]] | None:
    data = http_get_json(SPARQL, {"query": q, "format": "json"})
    if not data:
        return None
    return data.get("results", {}).get("bindings", [])


def _val(b: dict[str, Any], k: str) -> str | None:
    return (b.get(k) or {}).get("value")


def _qid_to_url(entity_uri: str | None) -> str | None:
    if not entity_uri:
        return None
    qid = entity_uri.rsplit("/", 1)[-1]
    return f"https://www.wikidata.org/wiki/{qid}" if qid.startswith("Q") else None


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').strip()


def by_external_id(prop: str, value: str) -> dict[str, Any] | None:
    """Cherche l'œuvre par identifiant externe (ex. P3634 = Met objectID)."""
    q = f'''SELECT ?work ?creatorLabel ?death ?inception ?copyrightStatusLabel WHERE {{
  ?work wdt:{prop} "{_esc(str(value))}".
  OPTIONAL {{ ?work wdt:P170 ?creator. OPTIONAL {{ ?creator wdt:P570 ?death. }} }}
  OPTIONAL {{ ?work wdt:P571 ?inception. }}
  OPTIONAL {{ ?work wdt:P6216 ?copyrightStatus. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr". }}
}} LIMIT 1'''
    rows = _query(q)
    if not rows:
        return None
    r = rows[0]
    return {
        "wikidata_url": _qid_to_url(_val(r, "work")),
        "creator": _val(r, "creatorLabel"),
        "death_year": extract_year(_val(r, "death")),
        "inception_year": extract_year(_val(r, "inception")),
        "copyright_status": _val(r, "copyrightStatusLabel"),
    }


def death_year_by_name(name: str) -> int | None:
    """Décès (P570) d'un humain dont le libellé EN/FR correspond exactement.

    Retourne None si introuvable OU ambigu (plusieurs années de décès distinctes)
    — on préfère l'absence de preuve à une preuve inventée.
    """
    n = _esc(name)
    if not n or len(n) < 3:
        return None
    q = f'''SELECT DISTINCT ?death WHERE {{
  VALUES ?lbl {{ "{n}"@en "{n}"@fr }}
  ?person rdfs:label ?lbl ; wdt:P31 wd:Q5 ; wdt:P570 ?death .
}} LIMIT 10'''
    rows = _query(q)
    if not rows:
        return None
    annees = {extract_year(_val(r, "death")) for r in rows}
    annees.discard(None)
    return annees.pop() if len(annees) == 1 else None


# Propriété Wikidata d'identifiant d'œuvre par source (vérifiées).
_PROP_PAR_SOURCE = {
    "met": "P3634",   # The Met object ID
}


def _recompute_decision(rec: dict[str, Any]) -> None:
    """Recalcule la décision provisoire à partir des gates (mêmes règles que les
    connecteurs). La validation humaine reste obligatoire avant production."""
    if not rec.get("gate_g1_us_g3") or rec.get("gate_g2_marque") is False or not rec.get("image_url"):
        rec["decision"] = "REJET"
        return
    if rec.get("resolution_ok") is False:
        rec["decision"] = "REJET"
        return
    g = rec.get("gate_g1_ue")
    rec["decision"] = "REJET" if g is False else ("REVIEW" if g is None else "CANDIDAT")


def enrich(rec: dict[str, Any], source: str | None = None, pause: float = 0.2) -> dict[str, Any]:
    """Complète un record avec les preuves DP issues de Wikidata (best-effort)."""
    # 1. Recoupement par identifiant d'œuvre (Met pour l'instant)
    prop = _PROP_PAR_SOURCE.get((source or "").lower())
    if prop and rec.get("objectID") is not None:
        info = by_external_id(prop, rec["objectID"])
        time.sleep(pause)
        if info:
            if info.get("wikidata_url"):
                rec["wikidata_url"] = info["wikidata_url"]
            if info.get("copyright_status"):
                rec["wikidata_copyright_status"] = info["copyright_status"]
            if not extract_year(rec.get("artist_death")) and info.get("death_year"):
                rec["artist_death"] = info["death_year"]
            if not rec.get("object_begin_year") and info.get("inception_year"):
                rec["object_begin_year"] = info["inception_year"]

    # 2. Fallback universel : décès par nom d'auteur (si toujours manquant)
    if not extract_year(rec.get("artist_death")) and rec.get("artist"):
        dy = death_year_by_name(rec["artist"])
        time.sleep(pause)
        if dy:
            rec["artist_death"] = dy

    # 3. Affine le gate UE s'il était indéterminé, grâce aux nouvelles données
    death = extract_year(rec.get("artist_death"))
    if death is not None and rec.get("gate_g1_ue") is None:
        rec["gate_g1_ue"] = death <= EU_DEATH_CUTOFF
        _recompute_decision(rec)

    return rec
