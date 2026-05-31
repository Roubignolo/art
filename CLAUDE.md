# CLAUDE.md — Contexte projet pour Claude Code

Ce fichier donne à Claude Code le contexte complet du projet **Art**. Lis-le en priorité.

## Le projet en une phrase
Marque d'édition d'art à la demande basée sur le **domaine public curé** : on sélectionne des œuvres libres de droits, on les restaure, on les met en récit (provenance), on produit via POD et on vend sur Etsy/Amazon — piloté par un système semi-automatisé.

## Thèse centrale
On ne vend pas l'art (il est libre) mais la **curation, la restauration et la confiance**. La rentabilité dépend du **hit-rate** de sélection, pas du volume de SKU.

## Décisions déjà prises (ne pas relitiger sans raison)
- **Modèle** : domaine public curé (et non « tendances + IA »), pour minimiser le risque marque.
- **Statut** : micro-entreprise (Phase 0-1), bascule société (EURL/SASU) seulement au scale.
- **Fournisseur POD** : architecture hybride **Gelato (défaut)** + **Prodigi (signature premium)**. Décision confirmée et chiffrée dans [`docs/benchmark-pod-fournisseurs.md`](docs/benchmark-pod-fournisseurs.md) après recherche octobre 2026 (3 sub-agents, ~50 sources). Gelato = production locale FR (Velocity Switch, 3-5j FR/UE), intégration Etsy la plus stable, Mockup API native. Prodigi = white-label intégral (sender 100% modifiable, packing slip + insert gratuit), fine art Hahnemühle Photo Rag + German Etching, encadrés FATG approved. **Printful écarté** : bugs sync Etsy rapportés en 2026 + arrêt warehousing EU/UK/Canada au 1er mars 2026 + sender pas modifiable pour DHL/UPS/FedEx.
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
- `docs/` — business plan, brief marque, moteur scoring, plan projet, architecture agents, backend Vercel, **process-vente-production** (flow concret Etsy/Gelato/mockups), **roadmap-mise-en-vente** (todo op détaillée par phases), **benchmark-pod-fournisseurs** (comparatif Printful/Gelato/Prodigi + décision hybride + grille white-label).
- `finance/` — calculateur de viabilité (xlsx) + comparateur fournisseurs.
- `agents/sourcing_agent.py` — orchestrateur Sourcing multi-sources (CLI). Dispatche vers `agents/sources/{met,rijksmuseum,bhl}.py` selon `--source`. Format de sortie commun (snake_case) consommable par `/api/works` POST et `scoring_agent.py`.
- `agents/sources/` — **7 connecteurs CC0/domaine public** : **Met** (sans clé), **Rijksmuseum** (`RIJKSMUSEUM_API_KEY`), **BHL** (`BHL_API_KEY`), **Art Institute of Chicago** (sans clé, IIIF), **Cleveland** (sans clé, dimensions + décès auteur exposés), **Smithsonian** (`SMITHSONIAN_API_KEY`, repli `DEMO_KEY` ; image IIIF haute-déf), **Europeana** (`EUROPEANA_API_KEY`, repli `api2demo` ; agrège **Paris Musées + musées français/européens**, filtre droits PD/CC0 strict). Tous vérifiés en live. IDs préfixés par offset anti-collision (Met < 10M, Rijks 10M, BHL 20M, AIC 300M, Cleveland 400M, Smithsonian 500M, Europeana 600M ; ids string → hash md5 dans la bande pour SI/Europeana). Note : `http_get_bytes` pose un Referer = origine de l'image (anti-hotlink AIC/Smithsonian IDS).
- `agents/scoring_agent.py` — sous-agent Scoring (4 axes pondérés, modes `heuristic` & `llm`) → registre noté par produit.
- `agents/render/` — **moteur de rendu local (Pillow, zéro clé)** : restauration HD (rognage bords, colorimétrie, accentuation, upscale Lanczos/Replicate), mockups encadrés (moulures coupe d'onglet, marie-louise, verre, ombre), scènes lifestyle (perspective maison), comparatif tailles, **carte de provenance A6**, et `brand_assets.py` (bannière/icône/logo). CLI : `python -m agents.render --met-id <id> --out <dir>`. Bascule cloud (Dynamic Mockups + fal.ai) via `/api/mockup` quand les clés sont posées.
- `docs/brand/` — identité de marque **Vellum & Cie** (nom retenu vs « Provenance » jugé générique ; dispo domaine/INPI à confirmer), `logo.svg`. `docs/etsy-listing-system.md` (best practices Etsy 2026 + kit type) · `docs/economie-gelato.md` (économie unitaire Gelato + seuil hit-rate recalibré ~1,1 %).
- **Preuve de domaine public** : chaque œuvre sourcée porte un champ `dp_evidence` consolidé (règle UE décès +70 ans · règle US publié ≤ ~1930 · énoncé de droits institutionnel · recoupement Wikidata P570/P571/P6216) construit par `base.build_dp_evidence()`. Champs : `artist_birth`, `object_begin_year`, `accession_number`, `rights_statement`, `wikidata_url`, `dp_evidence`. Enrichissement Wikidata gratuit via `agents/sources/wikidata_dp.py` (flag `--enrich-dp` ; recoupe par ID Met P3634 + décès par nom d'auteur, s'abstient si ambigu). Surfacé dans le cockpit (bloc « Preuve domaine public » + colonnes Prisma).
- `tests/` — tests `unittest` (gates sourcing, scoring, moteur de rendu, **preuve DP**). `python -m unittest discover -s tests`.
- `web/` — cockpit Next.js 15 (App Router, TS) + Prisma + Postgres (Neon) + HTTP Basic Auth. Déployé en production sur Vercel : <https://art-cockpit.vercel.app> (user `art`).
- `cockpit/provenance-cockpit.jsx` — prototype React initial conservé pour référence (remplacé par `web/`).

## État actuel & prochaines tâches
- ✅ Stratégie, finances, sous-agents Sourcing (multi-sources Met/Rijks/BHL) + Scoring + Marketing multilingue (Wikidata), cockpit Next.js + backend Prisma/Postgres, déployé sur Vercel (Neon Postgres, root directory `web/`, branche prod `main`, auto-deploy à chaque push).
- ✅ Process vente & production documenté (`docs/process-vente-production.md`) : flow Etsy/Gelato, fiche type, mockups hybrides (Dynamic Mockups + Flux Pro Kontext), SAV (packaging neutre, white-label, dropshipping direct, facture Etsy au nom de la boutique, insert provenance physique recommandé), coûts réels par vente. Décision : Etsy seul en P0-P1, eBay en P2, écarter Amazon.
- ✅ Benchmark POD documenté (`docs/benchmark-pod-fournisseurs.md`) : Gelato par défaut + Prodigi pour signature premium + Printful écarté. Précise les réponses opérationnelles : oui pour les encadrés (oak/noyer Gelato, FATG vrai bois Prodigi), oui pour la facture au nom de la boutique (Etsy), oui pour le dropshipping direct (jamais de ré-expédition par nous), white-label intégral possible.
- ✅ Roadmap mise en vente détaillée par phases (`docs/roadmap-mise-en-vente.md`) — 5 phases P0→P4, 6-8 semaines pour un founder solo, ~400€ + ~$50/mo récurrent.
- ✅ **v2 (mai 2026)** : moteur de rendu local `agents/render/` (restauration + 10 visuels + carte provenance, validé sur Met 436535) · identité de marque **Vellum & Cie** (dossier + assets PNG/SVG) · système de listing Etsy + `lib/etsy-listing.ts` + `lib/pricing.ts` · routes `/api/etsy/publish` (preview/POST), `/api/etsy/oauth` (PKCE), `/api/restoration` (Replicate) + `/api/mockup` réel (fal.ai/Dynamic Mockups) · cockpit : aperçu listing + galerie rendus + marque · finance recalibrée Gelato · tests `unittest`. `next build` vert.
- ⏭️ **P0 (manuel, 1-2 sem.)** : ouvrir Etsy + déclarer Gelato comme production partner + **confirmer dispo nom Vellum & Cie (registrar + INPI/EUIPO)**.
- ⏭️ **P1-P2 (manuel, 2 sem.)** : 1er listing puis collection d'amorçage 15 listings.
- ⏭️ **P3 (reste à câbler)** : OAuth Etsy live (tokens) + webhook order.paid → création commande Gelato + insert provenance dynamique par commande.
- ⏭️ **P4 (code, 1 sem.)** : analytics + repondération scoring sur ventes réelles.

## Conventions
- Langue : français (docs, commentaires, UI).
- Phase 0 = local + manuel ; pas de backend/cron tant que le hit-rate n'est pas prouvé au-dessus du seuil.
- Style code : concis, peu de dépendances. Front sans librairie de stockage navigateur (pas de localStorage).

*Avertissement intégré : ni conseil juridique ni financier ; faire valider DP, marque et fiscalité par des pros avant le scale.*
