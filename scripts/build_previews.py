#!/usr/bin/env python3
"""
Driver bout-en-bout : récupère des œuvres au musée → restauration + mockups →
aperçus prêts pour la fiche Etsy + carte de provenance.

  python scripts/build_previews.py [source] [query] [n]
  ex : python scripts/build_previews.py met "Claude Monet" 4

100 % gratuit (API musées + Wikidata + moteur Pillow local). Aucun crédit Claude.
Sortie : web/public/renders/<objectID>/  + index web/public/renders/collection.json
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from agents.sources import artic, cleveland, met, smithsonian  # noqa: E402
from agents.sources import wikidata_dp  # noqa: E402
from agents.sources.base import finalize_record  # noqa: E402
from agents.render import InfosProvenance, charger, generer_carte, generer_galerie  # noqa: E402

SOURCES = {"met": met, "artic": artic, "cleveland": cleveland, "smithsonian": smithsonian}

source_name = sys.argv[1] if len(sys.argv) > 1 else "met"
query = sys.argv[2] if len(sys.argv) > 2 else "Claude Monet"
n = int(sys.argv[3]) if len(sys.argv) > 3 else 4

mod = SOURCES[source_name]
OUT = os.path.join(ROOT, "web", "public", "renders")
MIN_RES = 3000

print(f"🔎 {source_name} · « {query} » · cible {n} aperçus\n")

collection = []
count = 0
for rec in mod.iter_candidates(query, max_scan=80):
    if count >= n:
        break
    if rec.get("decision") != "CANDIDAT" or not rec.get("image_url"):
        continue

    # Preuve domaine public (recoupement Wikidata gratuit ; Met = par P3634)
    try:
        wikidata_dp.enrich(rec, source=source_name)
    except Exception:
        pass
    finalize_record(rec)

    oid = rec["objectID"]
    try:
        img = charger(rec["image_url"])
    except Exception as e:
        print(f"  ⤫ skip {oid}: image inaccessible ({e})")
        continue
    if max(img.size) < MIN_RES:
        print(f"  ⤫ skip {oid}: {max(img.size)}px < {MIN_RES} (résolution print insuffisante)")
        continue

    dossier = os.path.join(OUT, str(oid))
    print(f"→ {(rec.get('title') or '')[:55]}  ({max(img.size)}px)")
    manifeste = generer_galerie(img, dossier, long_edge_print=MIN_RES)
    fid = manifeste.get("fidelite") or {}
    couleur = manifeste.get("couleur") or {}
    gam = manifeste.get("gamut") or {}
    print(f"   fidélité : {fid.get('verdict')} (ΔE {fid.get('delta_e_moyen')}) · "
          f"couleur : {couleur.get('espace_source')} · gamut : {gam.get('methode')}")

    infos = InfosProvenance(
        titre=rec.get("title") or "Sans titre",
        artiste=rec.get("artist") or "Anonyme",
        dates_artiste=f"{rec.get('artist_birth') or '?'}–{rec.get('artist_death') or '?'}",
        date_oeuvre=rec.get("object_date") or "",
        medium=(rec.get("medium") or "").split(",")[0].capitalize(),
        institution=rec.get("source") or "",
        numero_accession=rec.get("accession_number") or "",
        url_musee=rec.get("object_url") or "",
    )
    generer_carte(infos, dossier, vignette=img)

    collection.append({
        "id": oid,
        "title": rec.get("title"),
        "artist": rec.get("artist"),
        "source": rec.get("source"),
        "dpEvidence": rec.get("dp_evidence"),
        "wikidataUrl": rec.get("wikidata_url"),
        "dir": f"/renders/{oid}",
        # chemin réel du mockup encadré (nom dépend du 1er profil) — le front ne le devine pas
        "encadre": os.path.relpath(manifeste["fichiers"]["encadre"], dossier),
        "fidelite": {
            "verdict": fid.get("verdict"),
            "deltaE": fid.get("delta_e_moyen"),
            "chroma": fid.get("chroma_ratio"),
            "dominante": fid.get("dominante_ratio"),
        } if fid else None,
        "couleur": {
            "espaceSource": couleur.get("espace_source"),
            "convertiSrgb": couleur.get("converti_srgb"),
        } if couleur else None,
        "gamut": {
            "methode": gam.get("methode"),
            "teinteARisque": gam.get("teinte_a_risque"),
            "chromaMax": gam.get("chroma_max"),
            "pctChromaElevee": gam.get("pct_chroma_elevee"),
            "horsGamutPct": gam.get("hors_gamut_pct"),
            "profilPapier": gam.get("profil_papier"),
        } if gam else None,
    })
    count += 1

# Index de collection (fusion avec l'existant par id)
os.makedirs(OUT, exist_ok=True)
idx_path = os.path.join(OUT, "collection.json")
existing = []
if os.path.exists(idx_path):
    try:
        existing = json.load(open(idx_path, encoding="utf-8"))
    except Exception:
        existing = []
by_id = {c["id"]: c for c in existing}
for c in collection:
    by_id[c["id"]] = c
json.dump(list(by_id.values()), open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print(f"\n✓ {count} aperçus générés dans web/public/renders/ — index: {idx_path}")
for c in collection:
    print(f"   #{c['id']} {c['title']}")
