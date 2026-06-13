#!/usr/bin/env python3
"""Sourcing massif + rendu fidèle + tagging → collections.

Pour chaque requête curée (agents/tagging_data.json), recherche au Met, filtre
domaine public + résolution, génère la galerie « fidélité d'abord », analyse la
palette, tague (sujet + mouvement + palette) et alimente
web/public/renders/collection.json.

  python scripts/build_collections.py [n_par_requete=2] [cap_global=40]

Reprend où il en est (saute les œuvres déjà rendues). 100 % gratuit (API Met +
Wikidata + moteur local). Aucune clé. Aucune invention : tout vient des musées.
"""

import json
import os
import re
import shutil
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PIL import Image  # noqa: E402

from agents import tagging  # noqa: E402
from agents.render import InfosProvenance, charger, generer_carte, generer_galerie  # noqa: E402
from agents.render.palette import analyser_palette  # noqa: E402
from agents.sources import met, wikidata_dp  # noqa: E402
from agents.sources.base import finalize_record  # noqa: E402

OUT = os.path.join(ROOT, "web", "public", "renders")
MIN_RES = 3000
N_PAR_REQUETE = int(sys.argv[1]) if len(sys.argv) > 1 else 3
TARGET = int(sys.argv[2]) if len(sys.argv) > 2 else 60  # taille TOTALE visée pour la collection
IDX = os.path.join(OUT, "collection.json")

# Curation automatique : on ne garde que des œuvres MURALES 2D (pas d'objets 3D).
_CLASSIF_2D = ("painting", "print", "drawing", "watercolor", "pastel", "miniature",
               "woodblock", "etching", "engraving", "lithograph")


def _est_2d(rec):
    """Vrai si l'œuvre est une pièce murale plate (peinture/estampe/dessin), pas
    un objet 3D (épée, céramique, globe-horloge…) qui ferait un mauvais wall art."""
    classif = (rec.get("classification") or "").lower()
    objn = (rec.get("object_name") or "").lower()
    return (any(k in classif for k in _CLASSIF_2D)
            or any(k in objn for k in ("print", "drawing", "watercolor", "painting")))


def _norm_titre(titre):
    """Titre normalisé pour le dédoublonnage (retire séries, parenthèses, casse)."""
    t = (titre or "").lower()
    t = re.split(r"\(|,|;| from the series| from the | also known as", t)[0]
    return re.sub(r"[^a-z0-9 ]", "", t).strip()


# Sujets dévotionnels religieux : hors-thème pour une marque de déco murale.
_HORS_THEME = re.compile(
    r"\b(madonna|virgin|crucifix|christ|saint|holy family|our lady|annunciation"
    r"|nativity|baptism|apostle|gospel|jesus|piet[àa]|martyr|adoration of the|lamentation)\b",
    re.I,
)


def _hors_theme(rec):
    """Vrai si l'œuvre est un sujet dévotionnel religieux (écarté de la curation déco)."""
    hay = (rec.get("title") or "") + " " + " ".join(rec.get("tags") or [])
    return bool(_HORS_THEME.search(hay))


def _charger_index():
    if os.path.exists(IDX):
        try:
            return {c["id"]: c for c in json.load(open(IDX, encoding="utf-8"))}
        except Exception:
            return {}
    return {}


def _sauver_index(by_id):
    os.makedirs(OUT, exist_ok=True)
    json.dump(list(by_id.values()), open(IDX, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _infos(rec):
    return InfosProvenance(
        titre=rec.get("title") or "Sans titre",
        artiste=rec.get("artist") or "Anonyme",
        dates_artiste=f"{rec.get('artist_birth') or '?'}–{rec.get('artist_death') or '?'}",
        date_oeuvre=rec.get("object_date") or "",
        medium=(rec.get("medium") or "").split(",")[0].capitalize(),
        institution=rec.get("source") or "",
        numero_accession=rec.get("accession_number") or "",
        url_musee=rec.get("object_url") or "",
    )


def _layout_leger(manifeste):
    """Résumé du plan de mise en page pour l'index collection (cockpit/listing) :
    taille recommandée + orientation + liste des variantes Gelato avec leur bordure."""
    lay = manifeste.get("layout") or {}
    g = lay.get("gelato") or {}
    if not g:
        return None
    return {
        "taille": g.get("taille"),
        "orientation": g.get("orientation"),
        "ratioOeuvre": g.get("ratio_oeuvre"),
        "bordurePct": g.get("bordure_pct"),
        "variants": [{"taille": p.get("taille"), "bordurePct": p.get("bordure_pct")}
                     for p in lay.get("variants_gelato") or []],
    }


def _entree_collection(oid, rec, manifeste, tags, pal):
    dossier = os.path.join(OUT, str(oid))
    fid = manifeste.get("fidelite") or {}
    co = manifeste.get("couleur") or {}
    gam = manifeste.get("gamut") or {}
    return {
        "id": oid,
        "title": rec.get("title"),
        "artist": rec.get("artist"),
        "source": rec.get("source"),
        "dpEvidence": rec.get("dp_evidence"),
        "wikidataUrl": rec.get("wikidata_url"),
        "dir": f"/renders/{oid}",
        "encadre": os.path.relpath(manifeste["fichiers"]["encadre"], dossier),
        "tags": tags,
        "palette": {"tags": pal["tags"], "swatches": pal["swatches"],
                    "famille": pal["famille_dominante"], "chaleur": pal["chaleur"]},
        "fidelite": {"verdict": fid.get("verdict"), "deltaE": fid.get("delta_e_moyen"),
                     "chroma": fid.get("chroma_ratio"), "dominante": fid.get("dominante_ratio")},
        "couleur": {"espaceSource": co.get("espace_source"), "convertiSrgb": co.get("converti_srgb")},
        "gamut": {"methode": gam.get("methode"), "teinteARisque": gam.get("teinte_a_risque"),
                  "chromaMax": gam.get("chroma_max"), "pctChromaElevee": gam.get("pct_chroma_elevee"),
                  "horsGamutPct": gam.get("hors_gamut_pct"), "profilPapier": gam.get("profil_papier")},
        "layout": _layout_leger(manifeste),
    }


def _backfill_layout(by_id):
    """Calcule le plan de mise en page des œuvres déjà rendues qui n'en ont pas
    (le ratio du master web = celui du print → géométrie invariante d'échelle)."""
    from agents.render import layout as _layout

    for oid, entry in list(by_id.items()):
        if entry.get("layout"):
            continue
        master_p = os.path.join(OUT, str(oid), "master_restaure.jpg")
        if not os.path.exists(master_p):
            continue
        try:
            with Image.open(master_p) as im:
                aw, ah = im.size
        except Exception as e:  # master tronqué / 0 octet : on saute, sans tuer le run
            print(f"  ⚠ layout #{oid} ignoré : master illisible ({e})")
            continue
        lay = {
            "gelato": _layout.planifier(aw, ah, "gelato").to_dict(),
            "prodigi": _layout.planifier(aw, ah, "prodigi").to_dict(),
            "variants_gelato": [p.to_dict() for p in _layout.plans_variants(aw, ah, "gelato")],
            "variants_prodigi": [p.to_dict() for p in _layout.plans_variants(aw, ah, "prodigi")],
        }
        entry["layout"] = _layout_leger({"layout": lay})
        mp = os.path.join(OUT, str(oid), "manifest.json")
        if os.path.exists(mp):
            try:
                with open(mp, encoding="utf-8") as f:
                    man = json.load(f)
                man["layout"] = lay
                # Écriture atomique : temp + os.replace. Sans ça, une coupure en
                # cours de dump laisserait un manifest.json tronqué (et le bloc
                # except silencieux d'avant masquait la panne).
                tmp = mp + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(man, f, ensure_ascii=False, indent=2)
                os.replace(tmp, mp)
            except Exception as e:  # index déjà à jour ; on signale, on ne masque pas
                print(f"  ⚠ layout #{oid} : manifest non réécrit ({e})")
        g = lay["gelato"]
        print(f"  ↻ layout #{oid} → {g['taille']} ({g['orientation']}, bordure {g['bordure_pct']}%)")


def _enrichir_existants(by_id):
    """Tague les œuvres déjà rendues qui n'ont pas encore de tags (les 4 pionnières)."""
    for oid, entry in list(by_id.items()):
        if entry.get("tags"):
            continue
        master_p = os.path.join(OUT, str(oid), "master_restaure.jpg")
        if not os.path.exists(master_p):
            continue
        obj = met._fetch_object(oid)
        if not obj:
            continue
        rec = met._normalize(obj)
        pal = analyser_palette(Image.open(master_p).convert("RGB"))
        tags = tagging.tag_oeuvre(rec, pal["tags"])
        entry["tags"] = tags
        entry["palette"] = {"tags": pal["tags"], "swatches": pal["swatches"],
                            "famille": pal["famille_dominante"], "chaleur": pal["chaleur"]}
        if "encadre" not in entry:
            entry["encadre"] = "catalogue/02_encadre_chene.jpg"
        # injecte aussi les tags dans le manifest existant
        mp = os.path.join(OUT, str(oid), "manifest.json")
        if os.path.exists(mp):
            try:
                man = json.load(open(mp, encoding="utf-8"))
                man["tags"] = tags
                man["palette"] = pal
                json.dump(man, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass
        print(f"  ↻ tagué l'existant #{oid} {rec.get('artist')} → {tags['collections']}")


def main():
    by_id = _charger_index()
    print(f"Collection actuelle : {len(by_id)} œuvres · cible TOTALE {TARGET} (≤{N_PAR_REQUETE}/requête)\n")
    _enrichir_existants(by_id)
    _backfill_layout(by_id)
    _sauver_index(by_id)

    seen_titres = {_norm_titre(c.get("title")) for c in by_id.values()}
    debut = len(by_id)
    for req in tagging.REQUETES:
        if len(by_id) >= TARGET:
            break
        q = f"{req['artiste']} {req['query']}" if req.get("artiste") else req["query"]
        print(f"\n🔎 « {q} »  → attendu {req['collection_attendue']}")
        pris = 0
        for rec in met.iter_candidates(q, max_scan=60):
            if pris >= N_PAR_REQUETE or len(by_id) >= TARGET:
                break
            if rec.get("decision") != "CANDIDAT" or not rec.get("image_url"):
                continue
            oid = rec["objectID"]
            if oid in by_id:
                continue  # déjà rendu : ne compte PAS dans le quota NEW (on creuse plus loin)
            # ── curation automatique (attention extrême) ──
            if not _est_2d(rec):
                continue  # objet 3D → mauvais wall art
            if _hors_theme(rec):
                continue  # sujet dévotionnel religieux → hors-thème déco
            meta = tagging.tag_oeuvre(rec)  # sujet + mouvement (sans palette)
            if not meta["sujet"] and not meta["mouvement"]:
                continue  # incatégorisable / hors-thème
            nt = _norm_titre(rec.get("title"))
            if nt and nt in seen_titres:
                continue  # doublon de la même œuvre
            try:
                img = charger(rec["image_url"])
            except Exception as e:
                print(f"  ⤫ {oid} image inaccessible ({e})")
                continue
            if max(img.size) < MIN_RES:
                continue
            try:
                wikidata_dp.enrich(rec, source="met")
            except Exception:
                pass
            finalize_record(rec)
            dossier = os.path.join(OUT, str(oid))
            try:
                manifeste = generer_galerie(img, dossier, long_edge_print=MIN_RES)
            except Exception as e:
                print(f"  ⤫ {oid} rendu KO ({e})")
                continue
            verdict = (manifeste.get("fidelite") or {}).get("verdict")
            if verdict == "INFIDÈLE":  # garde-fou : jamais d'œuvre infidèle au catalogue
                shutil.rmtree(dossier, ignore_errors=True)
                print(f"  ⤫ {oid} écarté : audit INFIDÈLE")
                continue
            pal = analyser_palette(Image.open(os.path.join(dossier, "master_restaure.jpg")).convert("RGB"))
            tags = tagging.tag_oeuvre(rec, pal["tags"])
            manifeste["tags"] = tags
            manifeste["palette"] = pal
            json.dump(manifeste, open(os.path.join(dossier, "manifest.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)
            try:
                generer_carte(_infos(rec), dossier, vignette=img)
            except Exception:
                pass
            by_id[oid] = _entree_collection(oid, rec, manifeste, tags, pal)
            seen_titres.add(nt)
            _sauver_index(by_id)  # incrémental : robuste à l'interruption
            print(f"  ✓ {oid} {rec.get('artist')} — {(rec.get('title') or '')[:36]} · "
                  f"{tags['collections']} · {verdict}")
            pris += 1

    _sauver_index(by_id)
    print(f"\n✓ {len(by_id) - debut} œuvres ajoutées · {len(by_id)} au total dans la collection")
    cnt = Counter()
    for c in by_id.values():
        for t in (c.get("tags") or {}).get("collections", []):
            cnt[t] += 1
    print("\nCollections :")
    for t, n in cnt.most_common():
        print(f"   {n:3d}  {t}")


if __name__ == "__main__":
    main()
