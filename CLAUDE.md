# CLAUDE.md — Contexte projet pour Claude Code

Ce fichier donne à Claude Code le contexte complet du projet **Art**. Lis-le en priorité.

## Le projet en une phrase
Marque d'édition d'art à la demande basée sur le **domaine public curé** : on sélectionne des œuvres libres de droits, on les restaure, on les met en récit (provenance), on produit via POD et on vend sur Etsy/Amazon — piloté par un système semi-automatisé.

## Thèse centrale
On ne vend pas l'art (il est libre) mais la **curation, la restauration et la confiance**. La rentabilité dépend du **hit-rate** de sélection, pas du volume de SKU.

## Décisions déjà prises (ne pas relitiger sans raison)
- **Modèle** : domaine public curé (et non « tendances + IA »), pour minimiser le risque marque.
- **Statut** : micro-entreprise (Phase 0-1), bascule société (EURL/SASU) seulement au scale.
- **Fournisseur POD** : Gelato (défaut, production UE) et Prodigi (pièces premium) ; pas Printful (plus cher), pas le moins cher absolu (qualité).
- **Produits** : art mural d'abord (poster, encadré, toile), puis giftables (mug, coussin, torchon).
- **Sources** : institutions CC0 (Met, Rijksmuseum, Smithsonian, Biodiversity Heritage Library). PAS les versions « enhanced » de rawpixel sur du merch.

## Conformité — RÈGLES DURES (ne jamais contourner)
- Domaine public vérifié **US (publié ≤ 1930)** ET **UE (auteur † depuis 70 ans)**. Au moindre doute → rejet.
- Une œuvre DP peut rester sous **marque** (ex. Betty Boop) → rejet.
- **Validation humaine obligatoire** des gates DP/marque avant production. Jamais automatisée.
- Attribution Etsy : **« sourced by »**, jamais « made by ». Provenance documentée par œuvre.
- Ne jamais committer de secrets (.env, tokens, clés API).

## Moteur de scoring (paramètres)
- Gates éliminatoires : G1 DP US+UE · G2 marque · G3 source propre · G4 résolution (≥150 DPI, idéal 300).
- 4 axes pondérés /10 : momentum **0.30** · attribution **0.20** · traduisibilité **0.25** · concurrence **0.25**.
- Seuil : ≥ 6.5 produire · 5–6.4 file d'attente · sinon rejet.

## Économie (pour référence)
Marge/vente = (prix + port) − frais Etsy (6,5 % + 3 % + 0,25 $ + 0,20 $) − base fournisseur.
Seuil hit-rate = (designs × coût/design + fixes) / (designs × ventes/gagnant × marge). Voir `finance/`.

## Structure du repo
- `docs/` — business plan, brief marque, moteur scoring, plan projet, architecture agents, backend Vercel.
- `finance/` — calculateur de viabilité (xlsx) + comparateur fournisseurs.
- `agents/sourcing_agent.py` — sous-agent Sourcing (API du Met) → registre de provenance.
- `agents/scoring_agent.py` — sous-agent Scoring (4 axes pondérés, modes `heuristic` & `llm`) → registre noté par produit.
- `web/` — cockpit Next.js 15 (App Router, TS) + Prisma + Postgres (Neon) + HTTP Basic Auth, prêt pour déploiement Vercel.
- `cockpit/provenance-cockpit.jsx` — prototype React initial conservé pour référence (remplacé par `web/`).

## État actuel & prochaines tâches
- ✅ Stratégie, finances, sous-agents Sourcing + Scoring, cockpit Next.js + backend Prisma/Postgres.
- ⏭️ Provisionner Neon + déployer sur Vercel (voir `web/README.md`).
- ⏭️ Ajouter d'autres sources (Rijksmuseum, BHL) au sourcing.
- ⏭️ Boucle de feedback Analytics : réinjecter ventes réelles via la table `Sale` pour repondérer les axes.
- ⏭️ Cron Vercel : sourcing quotidien + scoring auto des nouvelles œuvres (gates restent humains).

## Conventions
- Langue : français (docs, commentaires, UI).
- Phase 0 = local + manuel ; pas de backend/cron tant que le hit-rate n'est pas prouvé au-dessus du seuil.
- Style code : concis, peu de dépendances. Front sans librairie de stockage navigateur (pas de localStorage).

*Avertissement intégré : ni conseil juridique ni financier ; faire valider DP, marque et fiscalité par des pros avant le scale.*
