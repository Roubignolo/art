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
from agents.sources import artic, bhl, cleveland, met, smithsonian, wikidata_dp  # noqa: E402
from agents.sources.base import finalize_record  # noqa: E402

OUT = os.path.join(ROOT, "web", "public", "renders")
MIN_RES = 3000
N_PAR_REQUETE = int(sys.argv[1]) if len(sys.argv) > 1 else 3
TARGET = int(sys.argv[2]) if len(sys.argv) > 2 else 60  # taille TOTALE visée pour la collection
# Filtre source optionnel : ne traiter que les requêtes d'un musée donné — utile
# pour diversifier en ciblé (ex. « artic » pour les niches naturalistes).
SOURCE_FILTER = sys.argv[3] if len(sys.argv) > 3 else None
IDX = os.path.join(OUT, "collection.json")

# Connecteurs CC0 disponibles sans clé (Met/AIC/Cleveland) + Smithsonian (clé .env).
# Une requête peut viser un autre musée que le Met via son champ "source" — décisif
# pour les niches que le Met n'a pas en haute-déf (planches Audubon/Haeckel/Redouté
# → AIC). Voir docs/audit-rentabilite.md §T2. wikidata_dp enrichit la preuve DP.
SOURCES = {"met": met, "artic": artic, "cleveland": cleveland,
           "smithsonian": smithsonian, "bhl": bhl}


def _candidats(mod, src, q):
    """Itérateur de candidats, en gérant la signature propre de BHL (planches
    d'ouvrages : max_titles/pages_per_title au lieu de max_scan)."""
    if src == "bhl":
        return mod.iter_candidates(q, max_titles=4, pages_per_title=12)
    return mod.iter_candidates(q, max_scan=60)

# Curation automatique : on ne garde que des œuvres MURALES 2D (pas d'objets 3D).
# Inclut les techniques de gravure/planche naturaliste (AIC) en plus de l'estampe.
_CLASSIF_2D = ("painting", "print", "drawing", "watercolor", "pastel", "miniature",
               "woodblock", "woodcut", "etching", "engraving", "lithograph",
               "chromolithograph", "illustration", "aquatint")

# ── GARDE-FOU MARQUE (hard rule) : domaine public ≠ libre de marque. ──
# Refus PAR CONSTRUCTION des artistes/marques dont la vérification DP a conclu
# NO-GO/CONDITIONNEL (cf. docs/audit-rentabilite.md §1) : même si une requête les
# vise un jour, aucune œuvre ne passe. La validation HUMAINE du gate reste requise
# avant toute production — ce filtre ne fait que bloquer en amont, jamais valider.
_MARQUE_RISQUE = re.compile(
    r"\b(william\s+morris|morris\s*&\s*co|alphonse\s+mucha|\bmucha\b"
    r"|hilma\s+af\s+klint|kawase\s+hasui|roger\s+broders)\b",
    re.I,
)


def _marque_risque(rec):
    """Vrai si l'œuvre porte un risque marque vérifié (NO-GO/CONDITIONNEL)."""
    hay = f"{rec.get('artist') or ''} {rec.get('title') or ''}"
    return bool(_MARQUE_RISQUE.search(hay))


def _sans_accents(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s or "")
                   if unicodedata.category(c) != "Mn").lower()


def _artiste_concorde(req_artiste, rec_artist):
    """Vrai si l'œuvre est bien du bon artiste (nom de famille présent).

    Garde-fou multi-source : la recherche plein-texte AIC/Smithsonian classe large
    (un « Audubon » peut remonter une céramique). Sans artiste imposé → toujours vrai.
    """
    if not req_artiste:
        return True
    cle = _sans_accents(req_artiste).split()[-1]  # nom de famille
    return cle in _sans_accents(rec_artist)


# ── Œuvres commercialement faibles (audit rentabilité §T2) : on les DÉPRIORISE
# (flag, pas suppression) — vanités macabres, scènes brunes, portraits d'inconnus,
# ratios incadrables. id → raison courte. Surfacé dans le cockpit.
DEPRIORISEES = {
    "435904": "Vanité à crâne — memento mori macabre, faible appétence déco",
    "436485": "Vanité explicite (crâne) — iconographie morbide, mauvais wall art",
    "436952": "Sujet funèbre, palette terne — anti-déco",
    "436162": "Scène brune intérieure, sitter renfrogné — faible traduisibilité",
    "436122": "Scène de genre brun-sombre d'un personnage obscur — peu décoratif",
    "438011": "Portrait d'un sitter inconnu — faible reconnaissance",
    "437432": "Portrait de sitter obscur — niche, faible appétence murale",
    "438815": "Portrait de notable inconnu — appétence murale faible",
    "436529": "Portrait nominatif peu connu — sujet à faible hit-rate",
    "839041": "Étude inachevée, brune, artiste obscur — pas une pièce vendable",
    "39569": "Ratio extrême 2,08 (panoramique) + artiste non identifié — incadrable",
    "815478": "Ratio extrême 3,34 (ultra-allongé) — incadrable sur formats POD",
    "815476": "Ratio extrême 1,98 + sujet macabre — format et thème faibles",
    "358367": "Gravure austère brune sur fond doré — peu lisible en vignette",
}


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


# Pages de garde d'ouvrage (BHL tague parfois une table des matières « Illustration »).
# Préfixes (pas de \b final : « Inhalts », « contents » avec suffixes allemands).
_FRONT_MATTER = re.compile(
    r"\b(inhalt|verzeichnis|index|title\s*page|titelblatt|frontispiece|colophon|vorwort"
    r"|table\s+of\s+contents|contents|errata|preface|sommaire)", re.I)


def _front_matter(rec):
    """Vrai si la page est une page de garde/texte (table des matières, titre…)."""
    return bool(_FRONT_MATTER.search(rec.get("title") or ""))


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


def _appliquer_curation(by_id):
    """Marque les œuvres faibles comme dépriorisées (flag persistant, pas suppression).

    Idempotent : on garde l'œuvre au catalogue, le cockpit la met juste en retrait.
    """
    by_str = {str(k): v for k, v in by_id.items()}
    n = 0
    for oid, raison in DEPRIORISEES.items():
        entry = by_str.get(str(oid))
        if not entry:
            continue
        cur = entry.get("curation") or {}
        if cur.get("deprioritized") and cur.get("raison") == raison:
            continue
        cur.update({"deprioritized": True, "raison": raison})
        entry["curation"] = cur
        n += 1
    if n:
        print(f"  ⬇ {n} œuvre(s) dépriorisée(s) (audit rentabilité §T2)")


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
    _appliquer_curation(by_id)
    _sauver_index(by_id)

    seen_titres = {_norm_titre(c.get("title")) for c in by_id.values()}
    debut = len(by_id)
    for req in tagging.REQUETES:
        if len(by_id) >= TARGET:
            break
        src = req.get("source", "met")
        if SOURCE_FILTER == "diversify":
            if not req.get("diversify"):
                continue  # mode diversification : seules les niches GO marquées
        elif SOURCE_FILTER and src != SOURCE_FILTER:
            continue  # filtre par musée
        mod = SOURCES.get(src, met)
        q = f"{req['artiste']} {req['query']}" if req.get("artiste") else req["query"]
        print(f"\n🔎 [{src}] « {q} »  → attendu {req['collection_attendue']}")
        pris = 0
        for rec in _candidats(mod, src, q):
            if pris >= N_PAR_REQUETE or len(by_id) >= TARGET:
                break
            if rec.get("decision") != "CANDIDAT" or not rec.get("image_url"):
                continue
            oid = rec["objectID"]
            if oid in by_id:
                continue  # déjà rendu : ne compte PAS dans le quota NEW (on creuse plus loin)
            # ── curation automatique (attention extrême) ──
            if _marque_risque(rec):
                continue  # garde-fou marque (NO-GO/CONDITIONNEL vérifié) → jamais
            if not _artiste_concorde(req.get("artiste"), rec.get("artist")):
                continue  # recherche plein-texte large → on exige le bon artiste
            if _front_matter(rec):
                continue  # page de garde BHL (table des matières, titre) → pas une planche
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
                wikidata_dp.enrich(rec, source=src)
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
            entry = _entree_collection(oid, rec, manifeste, tags, pal)
            # Œuvre fraîchement sourcée : marquée « à valider » — le gate DP/marque
            # reste une décision HUMAINE avant toute publication (règle dure). Le
            # cockpit la signale ; rien n'est publié automatiquement.
            entry["curation"] = {"nouveau": True, "dpAValider": True, "source": src}
            by_id[oid] = entry
            seen_titres.add(nt)
            _sauver_index(by_id)  # incrémental : robuste à l'interruption
            print(f"  ✓ [{src}] {oid} {rec.get('artist')} — {(rec.get('title') or '')[:36]} · "
                  f"{tags['collections']} · {verdict} · À VALIDER DP")
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
