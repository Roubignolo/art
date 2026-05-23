# Architecture multi-agents — « Chef de projet » & ses sous-agents

*Le Chef de projet est l'orchestrateur : il séquence le travail, dépêche les sous-agents, fait respecter les dépendances et les points de validation humaine. Chaque sous-agent a une mission étroite, des entrées/sorties claires et ses propres outils.*

---

## Principe d'orchestration

```
                       ┌──────────────────────────┐
                       │   CHEF DE PROJET (orchestr.)│
                       │  - détient le plan & l'état │
                       │  - applique le chemin critique│
                       │  - déclenche les gates 👤    │
                       └──────────────┬─────────────┘
        ┌───────────┬──────────┬──────┴─────┬───────────┬────────────┐
        ▼           ▼          ▼            ▼           ▼            ▼
   1.Légal &   2.Sourcing  3.Gate DP   4.Restau-   5.Scoring/   6.Produit &
   Conformité            (conformité)  ration      Tendances    Printful
        │                    │            │            │            │
        └──────────► 7.Marketing & Contenu ◄──────────┘            ▼
                            │                            8.Analytics & Feedback
                            └────────────► (boucle) ──────────────┘
```

Le Chef de projet ne « fait » rien lui-même : il **décide quoi lancer, dans quel ordre, et quand stopper pour validation humaine.** Les sous-agents sont stateless et reçoivent un contexte précis à chaque appel.

---

## ORCHESTRATEUR — Chef de projet

**Mission** : transformer le plan de projet en exécution, en respectant le chemin critique (Légal → Printful → Sourcing → Scoring → mise en ligne → mesure) et en bloquant sur les gates humains.

**Responsabilités**
- Maintient l'état de chaque chantier (à faire / en cours / bloqué / fait).
- Refuse de lancer un sous-agent si ses dépendances ne sont pas satisfaites.
- Insère des **points d'arrêt humains** obligatoires (validation gates DP/marque, échantillons physiques, première publication).
- Agrège les sorties et décide de l'étape suivante.

**Scaffold de prompt système**
```
Tu es le Chef de projet d'une marque POD « domaine public curé ».
Tu disposes de sous-agents : Legal, Sourcing, GateDP, Restauration, Scoring,
Produit, Marketing, Analytics. Tu ne produis jamais le travail toi-même :
tu décides quel sous-agent appeler, avec quelles entrées, et tu fais
respecter les dépendances et les validations humaines.
Règles dures :
- Ne lance Sourcing/Scoring que si le chantier Légal a livré la procédure DP.
- Ne publie jamais sans (a) gate DP validé par un humain, (b) échantillon validé.
- Plafonne la production à N œuvres/semaine.
Sortie : un plan d'action JSON {prochaine_etape, sous_agent, entrées, gate_humain?}.
```

---

## SOUS-AGENT 1 — Légal & Conformité

- **Mission** : produire et maintenir le cadre qui protège les comptes.
- **Entrées** : marque envisagée, pays de vente, sources de contenu.
- **Sorties** : procédure de vérification DP (US ≤1930 / UE décès +70), schéma du **registre de provenance**, règles d'attribution Etsy (« sourced by »), check-list RGPD/CGV, drapeaux fiscaux (micro vs société, TVA/OSS).
- **Outils** : recherche web (politiques plateformes, droit), génération de documents.
- **Gate humain 👤** : validation par un juriste/comptable avant scale.

## SOUS-AGENT 2 — Sourcing

- **Mission** : récupérer les masters HD + métadonnées depuis les institutions CC0.
- **Entrées** : territoire esthétique ciblé (ex. botanique), seuils qualité.
- **Sorties** : œuvres téléchargées + fiche métadonnées (artiste, dates, institution, licence, résolution) → alimente le registre de provenance.
- **Outils** : APIs musées (Met, Rijksmuseum, Smithsonian, BHL…), stockage objet.

## SOUS-AGENT 3 — Gate DP (conformité) 🔒👤

- **Mission** : filtre éliminatoire AVANT toute production.
- **Entrées** : fiche œuvre.
- **Sorties** : verdict JSON {dp_us, dp_ue, marque_residuelle, source_propre, resolution_ok, rejet, raison}.
- **Particularité** : c'est le sous-agent le plus critique. **Validation humaine obligatoire** sur G1 (statut DP) et G2 (marque) au démarrage.

## SOUS-AGENT 4 — Restauration

- **Mission** : transformer le master en visuel prêt à imprimer + ajouter la « valeur artistique » qui sécurise juridiquement.
- **Entrées** : master HD, produit cible.
- **Sorties** : fichiers print conformes (≥150 DPI, idéal 300, ratio produit), mockups.
- **Outils** : nanobanana (upscale/restauration), QC automatisé.
- **Gate humain 👤** : validation visuelle avant publication (phase 1).

## SOUS-AGENT 5 — Scoring / Tendances

- **Mission** : décider quoi produire.
- **Entrées** : œuvre (post-gate), produit cible, signaux tendances, données concurrence.
- **Sorties** : JSON {4 scores, score_final, décision, angle, accroche_provenance}.
- **Outils** : Pinterest/Google Trends, recherche listings Etsy/Amazon, Claude (scoring).

## SOUS-AGENT 6 — Produit & Printful

- **Mission** : créer et publier les produits.
- **Entrées** : fichiers print validés, pricing cible, accroche provenance.
- **Sorties** : produits Printful créés, listings Etsy/Amazon publiés (attribution correcte).
- **Outils** : API Printful, API Etsy, API Amazon, webhooks commandes.

## SOUS-AGENT 7 — Marketing & Contenu

- **Mission** : générer la demande et le récit.
- **Entrées** : œuvre + provenance + collection.
- **Sorties** : fiches produit (storytelling provenance), pins Pinterest, posts avant/après, mots-clés SEO.
- **Outils** : Claude (rédaction), planificateur social.

## SOUS-AGENT 8 — Analytics & Feedback

- **Mission** : fermer la boucle.
- **Entrées** : ventes réelles, scores prédits.
- **Sorties** : KPIs (hit-rate, marge, panier moyen), alertes (seuil Offsite Ads, dérive marge), **repondération des axes du scoring**.
- **Outils** : données marketplaces, le calculateur de viabilité.

---

## Mapping technique (réponse Vercel)

| Composant | Où ça vit | Pourquoi |
|-----------|-----------|----------|
| App de pilotage + UI cockpit | **Vercel** (Next.js) | idéal pour l'app & l'auth |
| Orchestrateur + sous-agents légers (scoring, marketing) | **Vercel Functions / Cron** | tâches courtes, planifiables |
| Base de données (œuvres, scores, ventes, provenance) | **Postgres managé** (Neon / Supabase) | Vercel n'est pas une base |
| Masters HD + fichiers print | **Stockage objet** (Cloudflare R2 / S3) | trop lourd pour Vercel |
| Restauration d'images (nanobanana, upscale) | **Worker séparé** (file de jobs + service GPU/conteneur) | dépasse les limites de durée serverless |
| Webhooks Printful/Etsy | **Vercel API routes** | réception d'événements OK |

> Vercel = le cerveau + l'interface ; un worker externe + une base + un stockage objet font le gros œuvre. C'est une archi classique « serverless + worker » qui reste légère et peu coûteuse au démarrage.

---

## Séquence de démarrage que le Chef de projet exécute

1. **Légal** livre la procédure DP + le schéma du registre → 👤 validation.
2. **Produit & Printful** configure le compte + 1-2 produits → 👤 échantillon physique.
3. **Sourcing** récupère 15-20 œuvres d'une collection (ex. botanique).
4. **Gate DP** filtre → 👤 validation G1/G2.
5. **Scoring** classe les survivants → garde le top selon le seuil.
6. **Restauration** traite les retenues → 👤 validation visuelle.
7. **Produit** publie sur Etsy (attribution « sourced by »).
8. **Marketing** génère fiches + pins.
9. **Analytics** mesure le hit-rate → décision go/no-go pour automatiser (construire la webapp complète).

Tant que l'étape 9 ne confirme pas un hit-rate au-dessus du seuil, **on reste en orchestration manuelle assistée** — pas de développement lourd.

---

## Mode de réalisation avec Claude

Chaque sous-agent = un appel Claude avec son prompt système dédié + ses outils. Le Chef de projet = un appel Claude qui renvoie « prochaine étape » en JSON, que ton code exécute en appelant le bon sous-agent. Démarrer en **semi-manuel** (tu déclenches chaque étape depuis la webapp) avant d'enchaîner automatiquement.

---

*Je ne suis ni avocat ni comptable. Les choix micro-entreprise vs société, TVA/OSS et conformité DP doivent être validés par des professionnels avant le passage à l'échelle.*
