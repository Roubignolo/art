# Art — Marque POD « domaine public curé »

Projet d'édition d'art à la demande : curation d'œuvres du **domaine public**, restauration, mise en récit (provenance), production via POD (Gelato / Prodigi) et distribution Etsy / Amazon — le tout piloté par un système semi-automatisé.

> **Thèse** : on ne vend pas l'art (il est libre), on vend la **curation, la restauration et la confiance**. La rentabilité dépend du *hit-rate* de sélection, pas du volume.

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
│  └─ sourcing_agent.py        Sous-agent Sourcing (API du Met) + registre provenance
└─ cockpit/
   └─ provenance-cockpit.jsx   Webapp de pilotage (front-end React)
```

## Démarrage rapide

```bash
# 1. Sourcer une première collection
pip install requests pillow
python agents/sourcing_agent.py        # → collection_botanique/registre_provenance.json

# 2. Piloter
# Ouvrir cockpit/provenance-cockpit.jsx, onglet Import, coller le registre.
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
