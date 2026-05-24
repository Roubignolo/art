#!/usr/bin/env python3
"""
Sous-agent SOURCING — orchestrateur multi-sources.

Dispatche la query vers le connecteur choisi (Met / Rijksmuseum / BHL),
applique le gate G4 résolution sur l'image, télécharge optionnellement les
masters et écrit le registre de provenance (JSON + CSV) au format consommé
par scoring_agent.py et /api/works POST du cockpit.

Dépendances :  pip install pillow         (requests N'est PAS utilisé — urllib stdlib)

Exemples :
  python agents/sourcing_agent.py --source met --query botanical --target 20
  python agents/sourcing_agent.py --source rijks --query landscape --target 15
  python agents/sourcing_agent.py --source bhl --query fern --titles 3 --pages 20

Variables d'environnement requises par source :
  - met         : aucune
  - rijksmuseum : RIJKSMUSEUM_API_KEY (https://www.rijksmuseum.nl/en/research/conduct-research/data/api)
  - bhl         : BHL_API_KEY         (https://www.biodiversitylibrary.org/getapikey.aspx)

Push direct vers le cockpit après sourcing (optionnel) :
  --push-to-cockpit URL --cockpit-user USER --cockpit-password PASS
Ex : --push-to-cockpit https://art-cockpit.vercel.app --cockpit-user art \
                      --cockpit-password "$COCKPIT_PASSWORD"

Conformité : ce script PRODUIT des décisions provisoires sur les gates.
La validation humaine reste obligatoire sur les lignes REVIEW et avant
toute production POD (cf. CLAUDE.md règles dures).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from typing import Iterator, Any

# Permet d'importer le package `sources` que l'on soit lancé depuis la racine
# du repo ou depuis n'importe quel cwd.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from sources.base import (  # noqa: E402
    DEFAULT_MIN_LONG_EDGE,
    http_get_bytes,
    summarize,
    verify_resolution,
    write_registry,
)


# ─────────────────────────── DISPATCH ───────────────────────────

def get_iterator(args: argparse.Namespace) -> Iterator[dict[str, Any]]:
    if args.source == "met":
        from sources.met import iter_candidates
        return iter_candidates(args.query, max_scan=args.max_scan, pause=args.pause)
    if args.source == "rijks" or args.source == "rijksmuseum":
        from sources.rijksmuseum import iter_candidates
        return iter_candidates(
            args.query, max_scan=args.max_scan, pause=args.pause,
            min_long_edge=args.min_resolution,
        )
    if args.source == "bhl":
        from sources.bhl import iter_candidates
        return iter_candidates(
            args.query, max_titles=args.titles, pages_per_title=args.pages,
            pause=args.pause,
        )
    raise ValueError(f"source inconnue : {args.source}")


# ─────────────────────────── PIPELINE COMMUN ───────────────────────────

def _process_resolution(rec: dict[str, Any], img_bytes: bytes, min_long_edge: int) -> dict[str, Any]:
    """Met à jour width/height/resolution_px/resolution_ok et ajuste la décision
    si la résolution force un REJET. N'écrase pas un REVIEW gate UE existant."""
    long_edge, w, h = verify_resolution(img_bytes)
    rec["resolution_px"] = long_edge
    rec["width"] = w or None
    rec["height"] = h or None
    rec["resolution_ok"] = (long_edge >= min_long_edge) if long_edge else False
    if rec["resolution_ok"] is False and rec["decision"] != "REJET":
        rec["decision"] = "REJET"
        rec["reason"] = f"résolution {long_edge}px < {min_long_edge}px"
    return rec


def main() -> int:
    args = _parse_args()

    out_dir = args.output_dir or f"collection_{args.source}_{args.query.replace(' ', '_')}"
    masters_dir = os.path.join(out_dir, "masters")
    if args.download:
        os.makedirs(masters_dir, exist_ok=True)

    print(f"🔎 Source: {args.source}   query: « {args.query} »   cible: {args.target} candidats")
    print(f"   Sortie : {out_dir}/registre_provenance.{{json,csv}}\n")

    try:
        iterator = get_iterator(args)
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2

    records: list[dict[str, Any]] = []
    kept = 0
    i = 0

    try:
        items = iter(iterator)
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2

    while True:
        try:
            rec = next(items)
        except StopIteration:
            break
        except RuntimeError as e:
            # Clé API manquante levée lazy au 1er appel HTTP du connecteur.
            print(f"❌ {e}", file=sys.stderr)
            return 2
        i += 1
        if kept >= args.target:
            break

        # Rejets précoces (gates DP/marque/source) : on archive et on continue.
        if rec["decision"] == "REJET":
            records.append(rec)
            print(f"[{i:>3}] ⤫ REJET  {(rec.get('title') or '')[:55]}")
            continue

        img_url = rec.get("image_url")
        if not img_url:
            rec["decision"] = "REJET"
            rec["reason"] = "image_url manquante"
            records.append(rec)
            print(f"[{i:>3}] ⤫ pas d'image")
            continue

        # Pour les sources qui n'ont PAS déjà rempli resolution_px (Met, BHL),
        # on télécharge pour mesurer. Rijks renseigne déjà → on saute le téléchargement.
        if rec.get("resolution_px"):
            res_known = True
        else:
            res_known = False
            img_bytes = http_get_bytes(img_url)
            time.sleep(args.pause)
            if img_bytes is None:
                rec["decision"] = "REJET"
                rec["reason"] = "image inaccessible"
                records.append(rec)
                print(f"[{i:>3}] ⤫ image inaccessible")
                continue
            rec = _process_resolution(rec, img_bytes, args.min_resolution)

        # Téléchargement du master (si demandé ET candidat retenu)
        if args.download and rec["decision"] in ("CANDIDAT", "REVIEW"):
            if not res_known:
                ext = os.path.splitext(img_url)[1].split("?")[0][:5] or ".jpg"
            else:
                # Rijks : on n'a pas img_bytes encore, fetch maintenant
                img_bytes = http_get_bytes(img_url)
                time.sleep(args.pause)
                ext = ".jpg"
                if img_bytes is None:
                    rec["decision"] = "REJET"
                    rec["reason"] = "image inaccessible au DL"
                    records.append(rec)
                    print(f"[{i:>3}] ⤫ image inaccessible au DL")
                    continue
            local_path = os.path.join(masters_dir, f"{rec['objectID']}{ext}")
            try:
                with open(local_path, "wb") as f:
                    f.write(img_bytes)
                rec["local_file"] = local_path
            except OSError as e:
                rec["reason"] = f"erreur écriture master: {e}"

        if rec["decision"] in ("CANDIDAT", "REVIEW"):
            kept += 1
            tag = "✅ RETENU" if rec["decision"] == "CANDIDAT" else "🟠 RETENU (à valider)"
            print(f"[{i:>3}] {tag}  {(rec.get('title') or '')[:55]}  ({rec['resolution_px']}px)")
        else:
            print(f"[{i:>3}] ⤫ REJET  {(rec.get('title') or '')[:55]}")

        records.append(rec)

    json_path, csv_path = write_registry(records, out_dir)
    bilan = summarize(records)

    print("\n── Bilan ──")
    print(f"   Inspectés      : {len(records)}")
    print(f"   ✅ CANDIDAT   : {bilan['CANDIDAT']}")
    print(f"   🟠 REVIEW     : {bilan['REVIEW']}  ← validation humaine requise")
    print(f"   ❌ REJET      : {bilan['REJET']}")
    print(f"   Registre JSON  : {json_path}")
    print(f"   Registre CSV   : {csv_path}")
    if args.download:
        print(f"   Masters HD     : {masters_dir}/")

    # Push direct vers le cockpit si demandé
    if args.push_to_cockpit:
        push_ok = push_registry_to_cockpit(records, args.push_to_cockpit, args.cockpit_user, args.cockpit_password)
        if not push_ok:
            return 3
    else:
        print("\n👤 Étape suivante : importer le registre dans le cockpit")
        print(f"   curl -u art:$COCKPIT_PASSWORD -X POST https://art-cockpit.vercel.app/api/works \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -d @{json_path}")
    return 0


def push_registry_to_cockpit(
    records: list[dict[str, Any]],
    base_url: str,
    user: str,
    password: str,
) -> bool:
    """POST le registre vers /api/works du cockpit. Auth HTTP Basic.

    On utilise urllib stdlib pour éviter une dépendance optionnelle.
    """
    from urllib import request, error
    url = base_url.rstrip("/") + "/api/works"
    payload = json.dumps(records).encode("utf-8")
    creds = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {creds}",
        "User-Agent": "art-cockpit/0.1 (sourcing-push)",
    }
    print(f"\n📤 Push vers {url} ({len(records)} records)…")
    try:
        req = request.Request(url, data=payload, headers=headers, method="POST")
        with request.urlopen(req, timeout=60) as r:
            body = r.read().decode("utf-8", errors="replace")
            if r.status >= 200 and r.status < 300:
                print(f"   ✅ HTTP {r.status} — {body[:200]}")
                return True
            print(f"   ⚠ HTTP {r.status} — {body[:200]}", file=sys.stderr)
            return False
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print(f"   ❌ HTTP {e.code} — {body[:300]}", file=sys.stderr)
        return False
    except error.URLError as e:
        print(f"   ❌ Erreur réseau : {e}", file=sys.stderr)
        return False


# ─────────────────────────── CLI ───────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sous-agent SOURCING multi-sources.")
    p.add_argument("--source", "-s", required=True,
                   choices=["met", "rijks", "rijksmuseum", "bhl"],
                   help="Connecteur à utiliser.")
    p.add_argument("--query", "-q", required=True,
                   help="Mot-clé de recherche (ex: botanical, fern, landscape).")
    p.add_argument("--target", "-t", type=int, default=20,
                   help="Nombre d'œuvres retenues visé (défaut: 20).")
    p.add_argument("--max-scan", type=int, default=200,
                   help="Plafond d'objets à inspecter (Met/Rijks). Défaut: 200.")
    p.add_argument("--titles", type=int, default=5,
                   help="(BHL) nombre d'ouvrages à scanner. Défaut: 5.")
    p.add_argument("--pages", type=int, default=30,
                   help="(BHL) pages d'illustration max par ouvrage. Défaut: 30.")
    p.add_argument("--min-resolution", type=int, default=DEFAULT_MIN_LONG_EDGE,
                   help=f"Seuil gate G4 en pixels (défaut: {DEFAULT_MIN_LONG_EDGE}).")
    p.add_argument("--pause", type=float, default=0.15,
                   help="Pause entre appels API (politesse). Défaut: 0.15s.")
    p.add_argument("--no-download", dest="download", action="store_false",
                   help="N'écrit pas les masters sur disque (métadonnées + gates seulement).")
    p.add_argument("--output-dir", "-o", default=None,
                   help="Dossier de sortie (défaut: collection_<source>_<query>).")
    p.add_argument("--push-to-cockpit", default=None,
                   help="URL base du cockpit (ex: https://art-cockpit.vercel.app). Si défini, "
                        "POST le registre vers /api/works après écriture des fichiers.")
    p.add_argument("--cockpit-user", default=os.environ.get("COCKPIT_USER", "art"),
                   help="Utilisateur HTTP Basic Auth du cockpit (défaut: 'art' ou COCKPIT_USER).")
    p.add_argument("--cockpit-password", default=os.environ.get("COCKPIT_PASSWORD", ""),
                   help="Mot de passe HTTP Basic Auth du cockpit (défaut: COCKPIT_PASSWORD env).")
    p.set_defaults(download=True)
    args = p.parse_args()
    if args.push_to_cockpit and not args.cockpit_password:
        p.error("--push-to-cockpit requiert --cockpit-password ou la variable d'env COCKPIT_PASSWORD")
    return args


if __name__ == "__main__":
    sys.exit(main())
