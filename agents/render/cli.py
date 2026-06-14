"""CLI du moteur de rendu.

Exemples :
    # à partir d'un objet Met (récupère les métadonnées + l'image automatiquement)
    python -m agents.render --met-id 436535 --out collection_demo/render_436535

    # à partir d'une image locale ou d'une URL
    python -m agents.render --image master.tif --out out/ --titre "..." --artiste "..."
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from .mockup import generer_galerie
from .provenance_card import InfosProvenance, generer_carte
from .restoration import charger

MET_API = "https://collectionapi.metmuseum.org/public/collection/v1/objects/{}"


def _infos_depuis_met(met_id: int) -> tuple[InfosProvenance, str]:
    """Récupère les VRAIES métadonnées Met (aucune invention)."""
    import requests

    rep = requests.get(MET_API.format(met_id), timeout=30,
                       headers={"User-Agent": "art-render/1.0"})
    rep.raise_for_status()
    o = rep.json()
    image = o.get("primaryImage") or o.get("primaryImageSmall")
    if not image:
        raise SystemExit(f"L'objet Met {met_id} n'expose pas d'image primaire.")
    if not o.get("isPublicDomain"):
        print(f"  ⚠ objet {met_id} non marqué isPublicDomain — vérification humaine requise.", file=sys.stderr)

    debut = str(o.get("artistBeginDate") or "").strip()
    fin = str(o.get("artistEndDate") or "").strip()
    dates = f"{debut}–{fin}" if debut and fin else (o.get("artistDisplayBio") or "")
    infos = InfosProvenance(
        titre=o.get("title") or "Sans titre",
        artiste=o.get("artistDisplayName") or "Anonyme",
        dates_artiste=dates,
        date_oeuvre=o.get("objectDate") or "",
        medium=(o.get("medium") or "").split(",")[0].capitalize(),
        institution=o.get("repository") or "The Metropolitan Museum of Art",
        numero_accession=o.get("accessionNumber") or "",
        url_musee=o.get("objectURL") or "",
    )
    return infos, image


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Moteur de rendu Vellum & Cie (local, Pillow)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--image", help="chemin local ou URL de l'image source")
    src.add_argument("--met-id", type=int, help="objectID Met (métadonnées + image auto)")
    ap.add_argument("--out", required=True, help="dossier de sortie")
    ap.add_argument("--profils", default="chene,noir,blanc", help="profils de cadre (csv)")
    ap.add_argument("--scenes", default="galerie,scandinave,atelier", help="scènes lifestyle (csv)")
    ap.add_argument("--no-restauration", action="store_true", help="désactive le pipeline de restauration")
    ap.add_argument("--profil", choices=["fidele", "archive"], default="fidele",
                    help="fidele (défaut, n'altère pas la teinte) | archive (corrige les scans abîmés NON calibrés)")
    ap.add_argument("--profil-papier", default=None,
                    help="chemin d'un profil ICC papier (Hahnemühle/Prodigi) pour un soft-proof gamut exact")
    ap.add_argument("--long-edge", type=int, default=4000, help="résolution print cible (grand côté)")
    # métadonnées manuelles (mode --image)
    ap.add_argument("--titre", default="")
    ap.add_argument("--artiste", default="")
    ap.add_argument("--institution", default="")
    ap.add_argument("--accession", default="")
    ap.add_argument("--url-musee", default="")
    ap.add_argument("--fichier-print", default="",
                    help="exporte le(s) fichier(s) print prêt(s) à uploader (csv : gelato,prodigi). "
                         "Gelato = bordure intégrée au ratio catalogue ; Prodigi = ratio natif (mat physique).")
    args = ap.parse_args(argv)

    infos: Optional[InfosProvenance] = None
    if args.met_id:
        print(f"→ Récupération des métadonnées Met {args.met_id}…")
        infos, image_url = _infos_depuis_met(args.met_id)
        print(f"  {infos.titre} — {infos.artiste} · {infos.institution}")
        source = charger(image_url)
    else:
        source = charger(args.image)
        if args.titre:
            infos = InfosProvenance(
                titre=args.titre, artiste=args.artiste or "Anonyme", dates_artiste="",
                date_oeuvre="", medium="", institution=args.institution or "",
                numero_accession=args.accession, url_musee=args.url_musee,
            )

    print(f"→ Image source : {source.size[0]}×{source.size[1]} px")
    print("→ Génération de la galerie (restauration + mockups)…")
    manifeste = generer_galerie(
        source, args.out,
        profils=[p.strip() for p in args.profils.split(",") if p.strip()],
        scenes_choisies=[s.strip() for s in args.scenes.split(",") if s.strip()],
        long_edge_print=args.long_edge,
        restauration=not args.no_restauration,
        profil=args.profil,
        profil_papier=args.profil_papier,
        exporter_print=[f.strip() for f in args.fichier_print.split(",") if f.strip()],
    )
    if manifeste.get("couleur"):
        c = manifeste["couleur"]
        flag = "→ converti en sRGB (ICC relatif+BPC)" if c["converti_srgb"] else "déjà sRGB, aucune conversion"
        print(f"  couleur : source {c['espace_source']} · {flag}")
    if manifeste.get("restauration"):
        r = manifeste["restauration"]
        print(f"  restauration : profil {r['profil']} · {r['largeur_avant']}×{r['hauteur_avant']} → "
              f"{r['largeur_apres']}×{r['hauteur_apres']} ({r['upscale_methode']})")
    if manifeste.get("fidelite"):
        from .fidelity import RapportFidelite, formater_rapport
        print(formater_rapport(RapportFidelite(**manifeste["fidelite"])))
    if manifeste.get("gamut"):
        g = manifeste["gamut"]
        if g["methode"] == "icc-softproof":
            print(f"  gamut ({g['profil_papier']}) : {g['hors_gamut_pct']}% hors-gamut · "
                  f"ΔE max {g['delta_e_max']} en {g['region_max']} ({g['teinte_a_risque']})")
        else:
            print(f"  gamut (heuristique) : chroma max {g['chroma_max']} · "
                  f"{g['pct_chroma_elevee']}% très saturé ({g['teinte_a_risque']}) — fournir --profil-papier pour un soft-proof exact")

    if infos is not None:
        print("→ Carte de provenance (recto/verso)…")
        cr, cv = generer_carte(infos, args.out, vignette=source)
        manifeste.setdefault("fichiers", {})["provenance"] = [cr, cv]

    n = sum(len(v) if isinstance(v, list) else 1 for v in manifeste["fichiers"].values())
    print(f"✓ {n} visuels générés dans {args.out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
