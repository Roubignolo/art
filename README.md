# Art — Marque POD « domaine public curé »

Projet d'édition d'art à la demande : curation d'œuvres du **domaine public**, restauration, mise en récit (provenance), production via POD (Gelato / Prodigi) et distribution Etsy / Amazon — le tout piloté par un système semi-automatisé.

> **Thèse** : on ne vend pas l'art (il est libre), on vend la **curation, la restauration et la confiance**. La rentabilité dépend du *hit-rate* de sélection, pas du volume.

**Cockpit en production** : <https://art-cockpit.vercel.app> (HTTP Basic Auth, user `art`). Auto-déployé à chaque push sur `main` depuis `web/`. Voir [`web/README.md`](web/README.md) pour la stack et la procédure complète.

## Structure du repo

```
Art/
├─ docs/
│  ├─ business-plan.md         Viabilité, économie unitaire, scénarios
│  ├─ brief-marque.md          Produits, sourcing, qualité, marque, positionnement
│  ├─ moteur-scoring.md        Gates DP + scoring 4 axes (spec implémentable)
│  ├─ plan-projet.md           WBS : 9 chantiers, chemin critique, phasage
│  ├─ architecture-agents.md   Chef de projet + sous-agents + mapping Vercel
│  └─ backend-vercel.md        Scaffold Next.js + Postgres + worker
├─ finance/
│  └─ calculateur-viabilite.xlsx   Modèle + comparateur de fournisseurs
├─ agents/
│  ├─ sourcing_agent.py        Orchestrateur Sourcing (CLI multi-sources)
│  ├─ sources/                 Connecteurs : met.py, rijksmuseum.py, bhl.py
│  └─ scoring_agent.py         Sous-agent Scoring (4 axes pondérés, mode heuristic|llm)
├─ web/                        Cockpit Next.js 15 + Prisma + Postgres (Neon)
│  ├─ app/                     UI + routes API (works, scoring)
│  ├─ prisma/schema.prisma     Modèle Work + Sale
│  └─ README.md                Détail stack + déploiement Vercel pas-à-pas
└─ cockpit/
   └─ provenance-cockpit.jsx   Prototype React initial (gardé pour référence)
```

## Démarrage rapide

```bash
# 1. Sourcer une première collection (gates DP/marque/résolution appliqués)
pip install requests pillow
python agents/sourcing_agent.py --source met --query botanical --target 20
#   → collection_met_botanical/registre_provenance.json

# Variantes (clé API gratuite à exporter d'abord) :
export RIJKSMUSEUM_API_KEY=…                  # https://www.rijksmuseum.nl/en/research/conduct-research/data/api
python agents/sourcing_agent.py --source rijks --query landscape --target 15
export BHL_API_KEY=…                          # https://www.biodiversitylibrary.org/getapikey.aspx
python agents/sourcing_agent.py --source bhl --query fern --titles 3 --pages 20

# 2. Scorer les œuvres pour un produit cible (mode heuristique, offline)
python agents/scoring_agent.py -i collection_botanique/registre_provenance.json -p poster
#   → collection_botanique/registre_scoring_poster.json

# 2bis. Variante avec estimation momentum/concurrence par Claude
pip install anthropic
export ANTHROPIC_API_KEY=…
python agents/scoring_agent.py -i collection_botanique/registre_provenance.json -p poster --llm

# 3. Lancer le cockpit (Next.js + Postgres)
cd web
npm install
cp .env.example .env.local            # DATABASE_URL Neon + COCKPIT_PASSWORD
npx prisma db push                    # crée les tables
npm run dev                            # → http://localhost:3000

# 4. Déployer sur Vercel (voir web/README.md pour le pas-à-pas Neon + Vercel)
```

## Conformité (à ne jamais retirer)

- Domaine public vérifié **US (publié ≤ 1930)** ET **UE (auteur † depuis 70 ans)**.
- Validation **humaine** des gates DP/marque avant toute production.
- Attribution Etsy : **« sourced by »**, jamais « made by ». Provenance documentée par œuvre.

## Phasage

- **Phase 0** : micro-entreprise, sourcing manuel, cockpit en local, mesure du hit-rate.
- **Phase 1+** : backend Vercel + Postgres, automatisation, scale — *seulement* une fois le hit-rate prouvé au-dessus du seuil de rentabilité.

---

*Avertissement : ni conseil juridique ni financier. Statut domaine public, marque et fiscalité à faire valider par des professionnels avant passage à l'échelle.*
