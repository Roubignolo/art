#!/usr/bin/env python3
"""
Sous-agent SOURCING — Phase 0
Interroge l'API publique du Metropolitan Museum (sans clé), filtre les œuvres
réellement en domaine public + haute résolution, applique les GATES du moteur
de scoring, produit le REGISTRE DE PROVENANCE (CSV + JSON) et télécharge les
masters des œuvres retenues.

Dépendances :  pip install requests pillow
Lancement   :  python sourcing_agent.py
Doc API Met :  https://metmuseum.github.io/

NB : ce script est conçu pour tourner sur TA machine (l'API n'est pas joignable
depuis l'environnement de chat). Aucune clé d'API n'est nécessaire.
"""

import os, csv, json, time, datetime, io
import requests
from PIL import Image

# ─────────────────────────── CONFIGURATION ───────────────────────────
THEME_QUERY     = "botanical"     # thème de la 1re collection (ex: "botanical", "ornithology", "celestial map")
TARGET_COUNT    = 20              # nombre d'œuvres retenues visé
MIN_LONG_EDGE   = 3000            # px sur le grand côté (≈ poster A3 @150 DPI). 5000+ pour grands formats.
MAX_TO_SCAN     = 300             # plafond d'objets inspectés (politesse + temps)
OUTPUT_DIR      = "collection_botanique"
DOWNLOAD_MASTERS= True            # télécharger les fichiers HD des œuvres retenues
REQUEST_PAUSE   = 0.15            # pause entre appels (politesse envers l'API)

BASE = "https://collectionapi.metmuseum.org/public/collection/v1"
EU_DEATH_CUTOFF = datetime.date.today().year - 71   # UE : auteur mort depuis 70 ans révolus
US_PUB_CUTOFF   = datetime.date.today().year - 95    # US : publié il y a 95 ans (≤1930 en 2026)

# Garde-fou marque résiduelle (G2) — liste minimale, la validation humaine reste requise
TRADEMARK_FLAGS = ["disney","mickey","betty boop","marvel","pixar","nintendo","coca",
                   "warner","pokemon","star wars","barbie","lego"]

session = requests.Session()
session.headers.update({"User-Agent": "Phase0-SourcingAgent/1.0 (curated public-domain POD)"})


# ─────────────────────────── APPELS API ───────────────────────────
def _get(url, params=None, tries=4):
    for i in range(tries):
        try:
            r = session.get(url, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503):
                time.sleep(1.5 * (i + 1)); continue
            return None
        except requests.RequestException:
            time.sleep(1.5 * (i + 1))
    return None

def search_objects(query):
    data = _get(f"{BASE}/search", {"q": query, "hasImages": "true"})
    return (data or {}).get("objectIDs") or []

def fetch_object(object_id):
    return _get(f"{BASE}/objects/{object_id}")


# ─────────────────────────── GATES (filtres éliminatoires) ───────────────────────────
def _year(s):
    """Extrait une année d'un champ Met (ex '1901-01-01' ou '1880')."""
    if not s: return None
    digits = "".join(c for c in str(s)[:4] if c.isdigit())
    return int(digits) if len(digits) == 4 else None

def check_gates(obj):
    """Retourne (decision, raisons, infos) sans encore vérifier la résolution (G4 à part)."""
    reasons = {}

    # G3 + G1(US) : le Met confirme le domaine public (CC0)
    reasons["g1_us_g3_source"] = bool(obj.get("isPublicDomain"))

    # G1(UE) conservateur : mort de l'auteur > 70 ans, sinon œuvre très ancienne
    death = _year(obj.get("artistEndDate"))
    end   = _year(obj.get("objectEndDate"))
    if death is not None:
        reasons["g1_ue"] = death <= EU_DEATH_CUTOFF
    elif end is not None:
        reasons["g1_ue"] = end <= 1900            # marge de sécurité si auteur inconnu
    else:
        reasons["g1_ue"] = None                    # indéterminé → REVIEW

    # G2 : marque résiduelle (garde-fou minimal)
    hay = f"{obj.get('title','')} {obj.get('artistDisplayName','')}".lower()
    reasons["g2_no_trademark"] = not any(t in hay for t in TRADEMARK_FLAGS)

    # image disponible ?
    reasons["has_image"] = bool(obj.get("primaryImage"))

    # décision provisoire (résolution vérifiée ensuite)
    if not reasons["has_image"] or not reasons["g1_us_g3_source"] or not reasons["g2_no_trademark"]:
        decision = "REJET"
    elif reasons["g1_ue"] is False:
        decision = "REJET"
    elif reasons["g1_ue"] is None:
        decision = "REVIEW"   # à valider par un humain (date d'auteur inconnue)
    else:
        decision = "CANDIDAT" # passe les gates, reste la résolution
    return decision, reasons

def verify_resolution(image_bytes):
    """Retourne (long_edge_px, width, height) ou (0,0,0) si illisible."""
    try:
        im = Image.open(io.BytesIO(image_bytes))
        w, h = im.size
        return max(w, h), w, h
    except Exception:
        return 0, 0, 0


# ─────────────────────────── REGISTRE DE PROVENANCE ───────────────────────────
def build_record(obj, decision, reasons, res=(None, None, None), local_file=""):
    long_edge, w, h = res
    return {
        "objectID":        obj.get("objectID"),
        "decision":        decision,
        "title":           obj.get("title"),
        "artist":          obj.get("artistDisplayName"),
        "artist_bio":      obj.get("artistDisplayBio"),
        "artist_death":    obj.get("artistEndDate"),
        "object_date":     obj.get("objectDate"),
        "object_end_year": obj.get("objectEndDate"),
        "department":      obj.get("department"),
        "classification":  obj.get("classification"),
        "medium":          obj.get("medium"),
        "dimensions":      obj.get("dimensions"),
        "credit_line":     obj.get("creditLine"),
        "is_public_domain":obj.get("isPublicDomain"),
        "source":          "The Metropolitan Museum of Art (Open Access, CC0)",
        "object_url":      obj.get("objectURL"),
        "image_url":       obj.get("primaryImage"),
        "resolution_px":   long_edge,
        "width":           w,
        "height":          h,
        "resolution_ok":   (long_edge or 0) >= MIN_LONG_EDGE if long_edge else None,
        "gate_g1_us_g3":   reasons.get("g1_us_g3_source"),
        "gate_g1_ue":      reasons.get("g1_ue"),
        "gate_g2_marque":  reasons.get("g2_no_trademark"),
        "local_file":      local_file,
    }


# ─────────────────────────── BOUCLE PRINCIPALE ───────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    masters_dir = os.path.join(OUTPUT_DIR, "masters")
    if DOWNLOAD_MASTERS:
        os.makedirs(masters_dir, exist_ok=True)

    print(f"🔎 Recherche « {THEME_QUERY} » sur l'API du Met…")
    ids = search_objects(THEME_QUERY)
    print(f"   {len(ids)} objets trouvés. Inspection (max {MAX_TO_SCAN})…\n")

    records, kept = [], 0
    for i, oid in enumerate(ids[:MAX_TO_SCAN]):
        if kept >= TARGET_COUNT:
            break
        obj = fetch_object(oid)
        time.sleep(REQUEST_PAUSE)
        if not obj:
            continue

        decision, reasons = check_gates(obj)
        if decision == "REJET":
            records.append(build_record(obj, decision, reasons))
            continue

        # vérification de résolution (G4) — on télécharge l'image pour mesurer
        res, local_file = (None, None, None), ""
        img_url = obj.get("primaryImage")
        if img_url:
            try:
                ir = session.get(img_url, timeout=60)
                if ir.status_code == 200:
                    res = verify_resolution(ir.content)
                    if (res[0] or 0) >= MIN_LONG_EDGE and decision in ("CANDIDAT", "REVIEW"):
                        if DOWNLOAD_MASTERS:
                            ext = os.path.splitext(img_url)[1].split("?")[0] or ".jpg"
                            local_file = os.path.join(masters_dir, f"{oid}{ext}")
                            with open(local_file, "wb") as f:
                                f.write(ir.content)
                        kept += 1
                        tag = "✅ RETENU" if decision == "CANDIDAT" else "🟠 RETENU (à valider)"
                    else:
                        decision = "REJET" if (res[0] or 0) < MIN_LONG_EDGE else decision
                        tag = f"⤫ résolution {res[0]}px < {MIN_LONG_EDGE}"
                else:
                    tag = "⤫ image inaccessible"
            except requests.RequestException:
                tag = "⤫ erreur image"
            time.sleep(REQUEST_PAUSE)
        else:
            tag = "⤫ pas d'image"

        records.append(build_record(obj, decision, reasons, res, local_file))
        print(f"[{i+1:>3}] {str(obj.get('title'))[:48]:48s} {tag}")

    # ── écriture du registre ──
    json_path = os.path.join(OUTPUT_DIR, "registre_provenance.json")
    csv_path  = os.path.join(OUTPUT_DIR, "registre_provenance.csv")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    if records:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            w.writeheader(); w.writerows(records)

    retenus = [r for r in records if r["local_file"]]
    print(f"\n── Bilan ──")
    print(f"   Objets inspectés : {len(records)}")
    print(f"   Œuvres RETENUES  : {len(retenus)}  (dossier : {masters_dir})")
    print(f"   Registre         : {csv_path}")
    print(f"\n👤 Étape suivante : valide manuellement les lignes 'REVIEW' (gate UE)")
    print(f"   avant de passer ces œuvres au sous-agent Scoring.")


if __name__ == "__main__":
    main()
