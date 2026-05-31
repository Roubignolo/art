"""
Format normalisé + utilitaires communs aux connecteurs de sourcing.

Tous les connecteurs (Met, Rijksmuseum, BHL) produisent des dicts au même
format `SourcingRecord` — c'est ce que consomment :
  - agents/scoring_agent.py
  - web/lib/works.ts → /api/works POST
"""

from __future__ import annotations

import csv
import datetime
import io
import json
import os
import time
from typing import Any

import requests  # robust SSL handling via certifi (urllib galère sur certains Mac corporate)

try:
    from PIL import Image  # type: ignore
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ─────────────────────────── chargement .env ───────────────────────────

def _charger_dotenv() -> None:
    """Charge un fichier .env local (agents/.env ou racine du repo) dans
    os.environ, SANS écraser une variable déjà définie. Zéro dépendance.

    Permet de poser les clés de sourcing (SMITHSONIAN_API_KEY, EUROPEANA_API_KEY,
    RIJKSMUSEUM_API_KEY, BHL_API_KEY) dans un .env gitignoré plutôt que de les
    exporter à chaque session. Les variables d'env explicites restent prioritaires.
    """
    import pathlib

    ici = pathlib.Path(__file__).resolve()
    for chemin in (ici.parents[1] / ".env", ici.parents[2] / ".env"):
        try:
            if not chemin.is_file():
                continue
            for ligne in chemin.read_text(encoding="utf-8").splitlines():
                ligne = ligne.strip()
                if not ligne or ligne.startswith("#") or "=" not in ligne:
                    continue
                cle, _, val = ligne.partition("=")
                cle = cle.strip()
                val = val.strip().strip('"').strip("'")
                if cle and cle not in os.environ:
                    os.environ[cle] = val
        except OSError:
            continue


_charger_dotenv()


# ─────────────────────────── HTTP partagé ───────────────────────────

UA = "art-cockpit/0.1 (sourcing) +https://art-cockpit.vercel.app"
_session: requests.Session | None = None


def session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": UA})
    return _session


def http_get_json(url: str, params: dict[str, Any] | None = None, tries: int = 4, timeout: int = 30) -> dict[str, Any] | None:
    """GET avec retry expo sur 429/5xx. Renvoie le JSON ou None en cas d'échec."""
    s = session()
    for i in range(tries):
        try:
            r = s.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503):
                time.sleep(1.5 * (i + 1)); continue
            return None
        except requests.RequestException:
            time.sleep(1.5 * (i + 1))
    return None


_IMG_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def http_get_bytes(url: str, timeout: int = 60) -> bytes | None:
    """Télécharge un binaire (image). Renvoie None si réseau/HTTP error.

    Pose un Referer égal à l'origine de l'image + un UA navigateur : certains
    serveurs (ex. IIIF de l'Art Institute of Chicago) renvoient 403 sans cela
    (protection hotlink). Inoffensif pour les autres hôtes.
    """
    from urllib.parse import urlsplit

    parts = urlsplit(url)
    headers = {
        "Referer": f"{parts.scheme}://{parts.netloc}/",
        "User-Agent": _IMG_UA,
        "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
    }
    try:
        r = session().get(url, timeout=timeout, headers=headers)
        if r.status_code == 200:
            return r.content
        return None
    except requests.RequestException:
        return None


# ─────────────────────────── CONSTANTES PARTAGÉES ───────────────────────────

# Cutoffs DP recalculés à chaque exécution pour suivre la roulante annuelle.
TODAY = datetime.date.today()
EU_DEATH_CUTOFF = TODAY.year - 71   # UE : auteur mort depuis 70 ans révolus
US_PUB_CUTOFF   = TODAY.year - 95   # US : publié il y a 95 ans (≤1930 en 2026)

# Garde-fou marque résiduelle (G2). Liste minimale — la validation humaine
# reste obligatoire au démarrage (cf. CLAUDE.md règles dures).
TRADEMARK_FLAGS = [
    "disney", "mickey", "betty boop", "marvel", "pixar", "nintendo",
    "coca", "warner", "pokemon", "star wars", "barbie", "lego",
]

DEFAULT_MIN_LONG_EDGE = 3000  # px sur le grand côté (poster A3 ≈ 150 DPI)


# ─────────────────────────── UTILITAIRES ───────────────────────────

def extract_year(s: Any) -> int | None:
    """Extrait une année à 4 chiffres d'une chaîne (`"1880-01-01"` → 1880)."""
    if not s:
        return None
    digits = "".join(c for c in str(s)[:4] if c.isdigit())
    return int(digits) if len(digits) == 4 else None


def trademark_hit(haystack: str) -> bool:
    """True si au moins une marque sensible (G2) est détectée."""
    h = haystack.lower()
    return any(flag in h for flag in TRADEMARK_FLAGS)


def verify_resolution(image_bytes: bytes) -> tuple[int, int, int]:
    """Retourne (long_edge, width, height) ou (0, 0, 0) si illisible.

    Dépend de Pillow. Si Pillow n'est pas installé, on tombe sur la
    valeur conservatrice (0,0,0) et le caller décidera (rejet G4).
    """
    if not HAS_PIL:
        return 0, 0, 0
    try:
        im = Image.open(io.BytesIO(image_bytes))
        w, h = im.size
        return max(w, h), w, h
    except Exception:
        return 0, 0, 0


def empty_record(object_id: Any, decision: str, reason: str = "") -> dict[str, Any]:
    """Squelette de record pour les rejets précoces (avant gates complets)."""
    return {
        "objectID":        object_id,
        "decision":        decision,
        "reason":          reason,
        "title":           None,
        "artist":          None,
        "image_url":       None,
        "resolution_px":   0,
        "gate_g1_us_g3":   None,
        "gate_g1_ue":      None,
        "gate_g2_marque":  None,
        "resolution_ok":   None,
        "local_file":      "",
    }


# ─────────────────────────── REGISTRE (sortie) ───────────────────────────

def write_registry(records: list[dict[str, Any]], out_dir: str, name: str = "registre_provenance") -> tuple[str, str]:
    """Écrit le registre en JSON + CSV. Retourne (json_path, csv_path).

    Les deux fichiers sont écrasés s'ils existent — pour produire des
    registres incrémentaux, écrire dans un dossier dédié par run.
    """
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, f"{name}.json")
    csv_path  = os.path.join(out_dir, f"{name}.csv")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    if records:
        # Tous les records doivent avoir les mêmes clés pour le CSV. On prend
        # l'union pour ne perdre aucune colonne entre les rejets et les retenus.
        all_keys: list[str] = []
        seen: set[str] = set()
        for r in records:
            for k in r.keys():
                if k not in seen:
                    seen.add(k)
                    all_keys.append(k)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=all_keys)
            w.writeheader()
            w.writerows([{k: r.get(k, "") for k in all_keys} for r in records])
    return json_path, csv_path


def summarize(records: list[dict[str, Any]]) -> dict[str, int]:
    """Compteurs par décision pour le bilan terminal."""
    out = {"CANDIDAT": 0, "REVIEW": 0, "REJET": 0}
    for r in records:
        d = (r.get("decision") or "").upper()
        if d in out:
            out[d] += 1
    return out
