#!/usr/bin/env python3
"""
Sous-agent SCORING — Phase 0
Consomme le registre de provenance produit par sourcing_agent.py, score chaque
couple (œuvre × produit) selon le moteur défini dans docs/moteur-scoring.md, et
écrit un registre scoré (JSON + CSV) + un bilan terminal.

Deux modes :
  • heuristique (défaut, offline, gratuit) : déterministe pour attribution &
    traduisibilité ; momentum et espace concurrentiel à 5/10 (neutre).
  • llm (--llm) : appelle l'API Claude pour estimer momentum, espace, angle
    recommandé et accroche de provenance. Requiert ANTHROPIC_API_KEY.

Dépendances : requests (déjà installé pour le sourcing).
              anthropic (uniquement si --llm) → pip install anthropic
Lancement   : python scoring_agent.py --input collection_botanique/registre_provenance.json
                                      --product poster
                                      [--llm] [--include-review]

Conformité  : ne produit AUCUNE décision finale automatique sans gates verts.
              La validation humaine reste obligatoire sur les œuvres REVIEW.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Any

# ─────────────────────────── PRODUITS CIBLES ───────────────────────────
# Spécification simplifiée des produits POD visés. ratio = largeur / hauteur idéal
# du visuel d'impression. min_long_edge = pixels minimum pour atteindre ~300 DPI
# sur la dimension d'impression dominante.
PRODUCTS: dict[str, dict[str, Any]] = {
    "poster":  {"ratio": 0.71, "min_long_edge": 3500, "label": "Poster A2 portrait"},
    "framed":  {"ratio": 0.71, "min_long_edge": 3500, "label": "Poster encadré"},
    "canvas":  {"ratio": 1.00, "min_long_edge": 4000, "label": "Toile carrée 60×60"},
    "torchon": {"ratio": 0.66, "min_long_edge": 3000, "label": "Torchon 50×70"},
    "coussin": {"ratio": 1.00, "min_long_edge": 3000, "label": "Coussin 45×45"},
    "mug":     {"ratio": 2.60, "min_long_edge": 2700, "label": "Mug wrap 11oz"},
}

# Classifications/médiums Met qui rendent particulièrement bien sur les supports plats.
FLAT_PRINT_CLASSES = {"prints", "drawings", "books", "watercolors", "photographs"}
PAINTING_CLASSES   = {"paintings"}

# Seuils de décision (cf. moteur-scoring §3)
THRESH_PRODUIRE   = 6.5
THRESH_FILE_ATTENTE = 5.0

# Pondérations (cf. moteur-scoring §2)
WEIGHTS = {
    "momentum":       0.30,
    "attribution":    0.20,
    "traduisibilite": 0.25,
    "espace":         0.25,
}


# ─────────────────────────── STRUCTURE DE SORTIE ───────────────────────────
@dataclass
class Score:
    object_id: int | str | None
    title: str
    artist: str
    product: str
    # gates rappelés depuis le registre de provenance (audit)
    gate_g1_us_g3: Any
    gate_g1_ue:    Any
    gate_g2:       Any
    resolution_ok: Any
    # 4 axes notés /10
    momentum: float
    attribution: float
    traduisibilite: float
    espace: float
    # synthèse
    score_final: float
    decision: str            # produire | file_attente | rejet
    angle_recommande: str    # suggestion si saturé
    accroche_provenance: str # 1 phrase storytelling
    mode: str                # heuristic | llm


# ─────────────────────────── HEURISTIQUES ───────────────────────────
def score_attribution(rec: dict[str, Any]) -> float:
    """Densité de provenance : plus on a de champs propres, plus l'œuvre 'se raconte'."""
    pts = 0
    artist = (rec.get("artist") or "").strip()
    if artist and artist.lower() not in {"unknown", "anonymous", "anonyme"}:
        pts += 2
    if (rec.get("artist_bio") or "").strip():
        pts += 2
    if (rec.get("object_date") or "").strip():
        pts += 1
    if (rec.get("medium") or "").strip():
        pts += 1
    if (rec.get("dimensions") or "").strip():
        pts += 1
    if (rec.get("credit_line") or "").strip():
        pts += 1
    if (rec.get("classification") or "").strip():
        pts += 1
    if (rec.get("department") or "").strip():
        pts += 1
    return float(min(pts, 10))


def score_traduisibilite(rec: dict[str, Any], product: str) -> float:
    """Adéquation visuelle/technique œuvre × produit."""
    pspec = PRODUCTS[product]
    w, h = rec.get("width") or 0, rec.get("height") or 0
    long_edge = rec.get("resolution_px") or 0

    # 1) Compatibilité de ratio (max 4 pts)
    ratio_pts = 0.0
    if w and h:
        src_ratio = w / h
        # On compare le ratio source au ratio cible, en autorisant la rotation.
        target = pspec["ratio"]
        diff = min(abs(src_ratio - target), abs((1 / src_ratio) - target))
        # 0 d'écart → 4 pts ; 0.5 d'écart → 0 pt
        ratio_pts = max(0.0, 4.0 - diff * 8.0)

    # 2) Résolution suffisante pour le produit cible (max 3 pts)
    needed = pspec["min_long_edge"]
    if long_edge >= needed * 1.3:
        res_pts = 3.0
    elif long_edge >= needed:
        res_pts = 2.0
    elif long_edge >= needed * 0.75:
        res_pts = 1.0
    else:
        res_pts = 0.0

    # 3) Type d'œuvre vs support (max 3 pts)
    cls = (rec.get("classification") or "").lower()
    fit_pts = 1.5  # défaut neutre
    if product in {"torchon", "poster", "framed"}:
        if any(k in cls for k in FLAT_PRINT_CLASSES):
            fit_pts = 3.0
        elif any(k in cls for k in PAINTING_CLASSES):
            fit_pts = 2.0
    elif product == "canvas":
        if any(k in cls for k in PAINTING_CLASSES):
            fit_pts = 3.0
        elif any(k in cls for k in FLAT_PRINT_CLASSES):
            fit_pts = 2.0
    elif product == "mug":
        # Wrap mug : motifs répétables / planches détaillées passent, peinture sombre mal.
        if any(k in cls for k in FLAT_PRINT_CLASSES):
            fit_pts = 2.5
        elif any(k in cls for k in PAINTING_CLASSES):
            fit_pts = 1.0
    elif product == "coussin":
        if any(k in cls for k in FLAT_PRINT_CLASSES):
            fit_pts = 2.5
        elif any(k in cls for k in PAINTING_CLASSES):
            fit_pts = 2.0

    return float(min(round(ratio_pts + res_pts + fit_pts, 1), 10))


def build_accroche_heuristic(rec: dict[str, Any]) -> str:
    """Template de storytelling à partir des métadonnées Met."""
    artist = (rec.get("artist") or "").strip() or "Auteur anonyme"
    bio    = (rec.get("artist_bio") or "").strip()
    date   = (rec.get("object_date") or "").strip()
    medium = (rec.get("medium") or "").strip()
    src    = rec.get("source") or "The Metropolitan Museum of Art (Open Access, CC0)"

    bits = [artist]
    if bio:
        bits[-1] += f" ({bio})"
    if medium:
        bits.append(medium.lower())
    if date:
        bits.append(f"vers {date}")
    head = ", ".join(bits)
    return f"{head}. Source : {src}."


# ─────────────────────────── MODE LLM (Claude API) ───────────────────────────
LLM_SYSTEM = (
    "Tu es un expert en domaine public (US 95 ans / UE vie+70), en tendances déco "
    "(Pinterest/Instagram/Etsy) et en marché POD. On te fournit une œuvre déjà "
    "validée sur les gates DP/marque/source/résolution et un produit cible. "
    "Tu dois UNIQUEMENT estimer deux axes : "
    "(a) momentum esthétique (l'esthétique/thème monte-t-il dans la déco mainstream ?), "
    "(b) espace concurrentiel (cette œuvre est-elle saturée sur Etsy/Amazon ?). "
    "Puis proposer un angle différenciant si saturé et une accroche de provenance "
    "(1 phrase, ton premium et factuel). Réponds en JSON strict, sans Markdown."
)

LLM_SCHEMA_HINT = (
    '{"momentum": 0-10, "espace": 0-10, '
    '"angle_recommande": "...", "accroche_provenance": "..."}'
)


def llm_estimate(rec: dict[str, Any], product: str, client) -> dict[str, Any]:
    """Appelle Claude pour les axes que l'heuristique ne peut pas estimer."""
    user_msg = (
        f"Œuvre :\n"
        f"  - titre : {rec.get('title')}\n"
        f"  - artiste : {rec.get('artist')} {rec.get('artist_bio') or ''}\n"
        f"  - date : {rec.get('object_date')}\n"
        f"  - classification : {rec.get('classification')}\n"
        f"  - médium : {rec.get('medium')}\n"
        f"  - département : {rec.get('department')}\n"
        f"  - source : {rec.get('source')}\n"
        f"  - URL œuvre : {rec.get('object_url')}\n\n"
        f"Produit cible : {PRODUCTS[product]['label']} ({product})\n\n"
        f"Renvoie uniquement : {LLM_SCHEMA_HINT}"
    )

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=LLM_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    # Tolère un éventuel fence ```json ... ```
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"momentum": 5.0, "espace": 5.0, "angle_recommande": "",
                "accroche_provenance": "", "_llm_parse_error": raw[:200]}


# ─────────────────────────── ORCHESTRATION ───────────────────────────
def decide(score_final: float) -> str:
    if score_final >= THRESH_PRODUIRE:
        return "produire"
    if score_final >= THRESH_FILE_ATTENTE:
        return "file_attente"
    return "rejet"


def keep_record(rec: dict[str, Any], include_review: bool) -> bool:
    """On ne score que les œuvres qui ont passé les gates du sourcing."""
    dec = (rec.get("decision") or "").upper()
    if dec == "REJET":
        return False
    if dec == "REVIEW" and not include_review:
        return False
    # Filet de sécurité : si le sourcing a marqué resolution_ok=False explicitement, skip.
    if rec.get("resolution_ok") is False:
        return False
    return True


def score_one(rec: dict[str, Any], product: str, mode: str, client=None) -> Score:
    attribution    = score_attribution(rec)
    traduisibilite = score_traduisibilite(rec, product)

    if mode == "llm" and client is not None:
        est = llm_estimate(rec, product, client)
        momentum = float(est.get("momentum", 5.0) or 5.0)
        espace   = float(est.get("espace", 5.0) or 5.0)
        angle    = str(est.get("angle_recommande") or "")
        accroche = str(est.get("accroche_provenance") or "") or build_accroche_heuristic(rec)
    else:
        momentum = 5.0
        espace   = 5.0
        angle    = ""
        accroche = build_accroche_heuristic(rec)

    score_final = round(
        WEIGHTS["momentum"]       * momentum
      + WEIGHTS["attribution"]    * attribution
      + WEIGHTS["traduisibilite"] * traduisibilite
      + WEIGHTS["espace"]         * espace,
        2,
    )

    return Score(
        object_id=rec.get("objectID"),
        title=rec.get("title") or "",
        artist=rec.get("artist") or "",
        product=product,
        gate_g1_us_g3=rec.get("gate_g1_us_g3"),
        gate_g1_ue=rec.get("gate_g1_ue"),
        gate_g2=rec.get("gate_g2_marque"),
        resolution_ok=rec.get("resolution_ok"),
        momentum=momentum,
        attribution=attribution,
        traduisibilite=traduisibilite,
        espace=espace,
        score_final=score_final,
        decision=decide(score_final),
        angle_recommande=angle,
        accroche_provenance=accroche,
        mode=mode,
    )


def make_llm_client():
    """Init paresseuse de l'API Claude. Échec explicite si la dépendance manque."""
    try:
        import anthropic  # type: ignore
    except ImportError:
        print("⚠️  Mode --llm : installe d'abord  pip install anthropic", file=sys.stderr)
        sys.exit(2)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  Mode --llm : exporte ANTHROPIC_API_KEY=…", file=sys.stderr)
        sys.exit(2)
    return anthropic.Anthropic()


def write_outputs(scores: list[Score], out_dir: str, product: str) -> tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, f"registre_scoring_{product}.json")
    csv_path  = os.path.join(out_dir, f"registre_scoring_{product}.csv")
    payload = [asdict(s) for s in scores]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    if payload:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(payload[0].keys()))
            w.writeheader(); w.writerows(payload)
    return json_path, csv_path


def print_bilan(scores: list[Score], product: str) -> None:
    by = {"produire": 0, "file_attente": 0, "rejet": 0}
    for s in scores:
        by[s.decision] += 1
    print("\n── Bilan scoring ──")
    print(f"   Produit cible    : {PRODUCTS[product]['label']}")
    print(f"   Œuvres scorées   : {len(scores)}")
    print(f"   ✅ Produire       : {by['produire']}  (score ≥ {THRESH_PRODUIRE})")
    print(f"   ⏸  File d'attente : {by['file_attente']}  ({THRESH_FILE_ATTENTE}–{THRESH_PRODUIRE - 0.1})")
    print(f"   ❌ Rejet          : {by['rejet']}")

    top = sorted(scores, key=lambda s: s.score_final, reverse=True)[:5]
    if top:
        print("\n   Top 5 :")
        for s in top:
            tag = {"produire": "✅", "file_attente": "⏸ ", "rejet": "❌"}[s.decision]
            short_title = (s.title or "")[:48]
            print(f"   {tag} {s.score_final:>4.2f}  {short_title:<48}  {s.artist[:30]}")
    print()


# ─────────────────────────── CLI ───────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sous-agent SCORING — registre noté à partir du sourcing.")
    p.add_argument("--input", "-i", required=True,
                   help="Chemin vers registre_provenance.json (sortie du sourcing_agent).")
    p.add_argument("--product", "-p", default="poster", choices=sorted(PRODUCTS.keys()),
                   help=f"Produit cible (défaut: poster). Choix : {', '.join(sorted(PRODUCTS.keys()))}.")
    p.add_argument("--mode", "-m", default="heuristic", choices=["heuristic", "llm"],
                   help="heuristic (offline, défaut) ou llm (Claude API, requiert ANTHROPIC_API_KEY).")
    p.add_argument("--llm", action="store_true",
                   help="Raccourci équivalent à --mode llm.")
    p.add_argument("--include-review", action="store_true",
                   help="Scorer aussi les œuvres marquées REVIEW (à valider humainement).")
    p.add_argument("--output-dir", "-o", default=None,
                   help="Dossier de sortie (défaut : même dossier que --input).")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    mode = "llm" if args.llm else args.mode

    if not os.path.isfile(args.input):
        print(f"❌ Fichier introuvable : {args.input}", file=sys.stderr)
        return 1

    with open(args.input, encoding="utf-8") as f:
        registry = json.load(f)

    eligible = [r for r in registry if keep_record(r, args.include_review)]
    print(f"🔢 {len(eligible)} œuvres éligibles (sur {len(registry)} dans le registre).")
    if not eligible:
        print("   Rien à scorer. Vérifie ton registre de provenance.")
        return 0

    client = make_llm_client() if mode == "llm" else None

    scores: list[Score] = []
    for i, rec in enumerate(eligible, 1):
        s = score_one(rec, args.product, mode, client)
        scores.append(s)
        tag = {"produire": "✅", "file_attente": "⏸ ", "rejet": "❌"}[s.decision]
        print(f"[{i:>3}] {tag} {s.score_final:>4.2f}  {(s.title or '')[:48]:<48}")

    out_dir = args.output_dir or os.path.dirname(os.path.abspath(args.input)) or "."
    json_path, csv_path = write_outputs(scores, out_dir, args.product)
    print_bilan(scores, args.product)
    print(f"   Registre JSON    : {json_path}")
    print(f"   Registre CSV     : {csv_path}")
    if mode == "heuristic":
        print("\n💡 En mode heuristique, momentum & espace = 5/10 (neutres).")
        print("   Relance avec --llm pour les estimer via Claude.")
    print("\n👤 Étape suivante : valide les lignes 'produire' avant restauration & POD.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
