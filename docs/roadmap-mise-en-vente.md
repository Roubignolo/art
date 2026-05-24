# Roadmap mise en vente — todo opérationnelle détaillée

*Plan d'action concret pour aller du cockpit actuel (déployé sur Vercel, sourcing/scoring/marketing en place) à la **première vente Etsy** puis à un fonctionnement quasi-automatisé. Estimations en jours-personne pour un founder solo qui sait coder. Légende : 👤 humain obligatoire · ⚙️ automatisable · 🔴 chemin critique · 🔒 bloque d'autres étapes.*

---

## Vue d'ensemble — 5 phases

| Phase | Objectif                                                | Durée    | Sortie attendue                            |
|-------|---------------------------------------------------------|----------|--------------------------------------------|
| **P0** | Pré-requis non techniques (compte Etsy, statut, marque) | 1-2 sem. | Boutique Etsy ouverte, "Provenance" branded |
| **P1** | Premier listing manuel bout-en-bout                     | 1 sem.   | 1 produit en ligne, échantillon validé      |
| **P2** | 3 produits × 5 œuvres (collection d'amorçage)            | 1 sem.   | 15 listings, premières ventes              |
| **P3** | Automation du tunnel (publication + fulfillment)        | 2-3 sem. | Cockpit pousse vers Etsy/Gelato            |
| **P4** | Analytics + boucle feedback                             | 1 sem.   | Repondération du scoring sur ventes réelles |

**Durée totale : 6-8 semaines** pour un founder solo qui travaille ~20h/semaine sur le projet.

---

## PHASE P0 — Pré-requis non techniques (1-2 semaines)

*Tu fais tout ça depuis ton navigateur, pas de code. Ne pas sauter ces étapes : Etsy suspend des comptes pour des fautes administratives évitables.*

### P0.1 — Marque & nom (3-4 j)

- [ ] 👤 Choisir le nom définitif de la boutique (concept "Provenance" du brief-marque §4 recommandé)
- [ ] 👤 Vérifier la **disponibilité de la marque** : INPI (https://www.inpi.fr) pour la France, EUIPO pour l'UE. Recherche d'antériorité minimum.
- [ ] 👤 Réserver le nom de domaine (.com + .fr) — même si pas de site propre tout de suite, ne pas laisser un squatteur prendre
- [ ] 👤 Réserver les handles réseaux : Instagram + Pinterest minimum (cohérents avec le nom)
- [ ] 👤 (optionnel mais recommandé) Déposer la marque à l'INPI (~250 €, 3 mois) — ça protège ton nom de boutique

### P0.2 — Structure & fiscalité (1-2 j)

- [ ] 👤 Vérifier que le statut micro-entreprise actuel couvre la nouvelle activité (commerce de biens, code APE 4791B vente à distance, ou similaire)
- [ ] 👤 Plafond TVA micro à 36 800 € pour les services / 91 900 € pour la vente de biens en 2026 — vérifier où tu es positionné
- [ ] 👤 Vérifier l'obligation **OSS (One-Stop Shop)** pour les ventes intra-UE > 10 000 € — inscription via impots.gouv.fr si applicable
- [ ] 👤 Aux US : Etsy applique le marketplace facilitator → pas de sales tax à gérer côté toi pour les ventes US (mais vérifier 2026)

### P0.3 — Compte Etsy + branding boutique (2-3 j)

- [ ] 🔴👤 Créer le compte vendeur Etsy (https://www.etsy.com/sell)
- [ ] 👤 Renseigner l'adresse fiscale, le compte de paiement (Etsy Payments en EUR)
- [ ] 👤 Configurer la boutique :
  - [ ] Nom de boutique (= ta marque)
  - [ ] Bannière 1200×300 (peut être fait avec une scène neutre + logo)
  - [ ] Logo boutique
  - [ ] Page "À propos" : 3 paragraphes (pourquoi, comment, qui) — cf. `process-vente-production.md` §2
  - [ ] Annonce de boutique (1 phrase mise en avant)
- [ ] 🔴👤 Configurer les **politiques de boutique** :
  - [ ] Politique de retour (cf. `process-vente-production.md` §6 — pas de retour "j'ai changé d'avis", retours acceptés sur défaut/perte)
  - [ ] Politique d'expédition (UE 3-6j, US 5-10j via Gelato)
  - [ ] Conditions générales : mention "sourced by" obligatoire dans chaque fiche
  - [ ] Politique de confidentialité (RGPD)
- [ ] 👤 Configurer le **profil de livraison** par défaut (un profile par zone : UE, UK, US, monde) — coûts à pré-calculer avec [Gelato shipping calculator](https://www.gelato.com/shipping)

### P0.4 — Déclaration du production partner Gelato (1 j) 🔴🔒

- [ ] 🔴👤 Créer un compte Gelato (https://www.gelato.com) — gratuit, gratuit jusqu'à 10 produits avec mockups
- [ ] 🔴👤 Dans Etsy : **Shop Manager → Settings → Production Partners → Add → Gelato**
   - Renseigner : nom du partenaire, lieu de production, lien vers leur site
   - *Sans cette déclaration, ton shop risque la suspension pour POD non déclaré*
- [ ] 👤 Lier Gelato ↔ Etsy via le dashboard Gelato (intégration native)

### P0.5 — Politique d'attribution domaine public (1 j)

- [ ] 👤 Rédiger ton **template de mention provenance** standardisé à mettre sur chaque fiche :
  ```
  Cette pièce n'est pas une œuvre créée par moi.
  Elle est sourcée d'une collection muséale en domaine public,
  restaurée et réimprimée avec soin.
  Source : [nom institution] · Œuvre originale : [titre] par [artiste] ([dates])
  ```
- [ ] 👤 Préparer les **réponses aux questions clients récurrentes** :
  - "Est-ce une vraie œuvre ?" → "Reproduction haute fidélité d'un master numérique CC0..."
  - "Pourquoi l'avez-vous le droit de vendre ça ?" → "L'œuvre est dans le domaine public, mon travail est..."
  - "C'est imprimé chez vous ?" → "Imprimé à la demande par notre partenaire Gelato, en Europe"

**Livrable P0** : boutique Etsy publiée (mais vide), partenaire production déclaré, branding cohérent avec le concept "Provenance".

---

## PHASE P1 — Premier listing manuel bout-en-bout (1 semaine)

*L'objectif est de valider la chaîne en POSANT 1 produit à la main et en commandant un échantillon. Pas de code automation ici — on apprend la mécanique.*

### P1.1 — Choisir et préparer la 1re œuvre (1 j)

- [ ] 🔴👤 Sélectionner **1 œuvre du registre actuel** déjà importée dans le cockpit (les 4 vraies œuvres Met du fixture sont parfaites pour démarrer)
  - Recommandé : **Van Gogh — Irises (#436528)** (titre officiel Wikidata FR "Les Iris", très haute notoriété, vraie image HD)
- [ ] 👤 Dans le cockpit, valider les gates (passer la fougère/Van Gogh en `gate_g1_ue=true` si pas déjà fait) → statut `score`
- [ ] 👤 Cliquer **"Scoring Claude"** pour avoir les scores momentum/concurrence renseignés
- [ ] 👤 Cliquer **"Générer marketing FR/EN/DE/IT/ES"** pour avoir les 5 fiches multilingues prêtes

### P1.2 — Restaurer le master (1 j)

- [ ] 👤 Télécharger le master HD depuis l'URL Met (DP346474.jpg pour Irises)
- [ ] 👤 Restauration manuelle (cf. `brief-marque.md` §3) :
  - Upscale si nécessaire (Topaz Gigapixel, Real-ESRGAN ou nanobanana)
  - Correction colorimétrique (Lightroom / Affinity Photo)
  - Débruitage léger
  - Nettoyage (tampons, défauts scan)
  - Sortie : **fichier print en sRGB, 300 DPI à la taille A2 (au moins 5000×7000 px)**
- [ ] 👤 **Sauvegarder l'avant/après** — ces images servent au storytelling Pinterest/Instagram et à la défense juridique de la "valeur artistique ajoutée"

### P1.3 — Créer le produit sur Gelato (0,5 j)

- [ ] 👤 Dans le dashboard Gelato → **Add Product → Wall Art → Framed Poster**
  - Format A2 (42 × 59,4 cm)
  - Papier 200 gsm semi-mat
  - Cadre chêne par défaut (option naturel + noir + blanc en variants)
- [ ] 👤 Upload du fichier print restauré
- [ ] 👤 Vérifier le **mockup auto-généré par Gelato** (la zone d'impression et le rendu)
- [ ] 👤 Configurer les **variants** : A3 / A2 / 50×70, et 3 cadres (chêne, noir, naturel) → max 12 SKUs
- [ ] 👤 Définir les prix de vente (cf. tableau `process-vente-production.md` §3)

### P1.4 — Générer les mockups premium (0,5 j)

*En Phase 1, garder simple : utiliser les mockups Gelato par défaut (3 fournis) + 2-3 templates Dynamic Mockups à la main si abonnement actif. Le workflow IA hybride viendra en Phase 3.*

- [ ] 👤 (Optionnel Phase 1) Souscrire **Dynamic Mockups Pro** ($15/mo) si on veut des templates wall art moins génériques que ceux de Gelato
- [ ] 👤 Générer 3-5 mockups en plus des 3 fournis par Gelato

### P1.5 — Publier sur Etsy (manuel) (0,5 j)

- [ ] 🔴👤 Dans Gelato → **Publish to Etsy** (intégration native)
- [ ] 👤 Vérifier le listing créé sur Etsy :
  - [ ] Titre repris du `listingTitle` FR du marketing — copier depuis le cockpit
  - [ ] Description : copier la description FR du marketing + ajouter le bloc provenance + spécifications
  - [ ] 13 tags depuis le marketing FR (tags SEO générés)
  - [ ] 10 images : ordonner avec le poster nu en image 1 (vignette résultat de recherche)
  - [ ] Prix et variants Etsy alignés sur la grille Gelato
  - [ ] Catégorie Etsy : **Home & Living → Home Décor → Wall Décor → Wall Hangings → Posters & Prints**
  - [ ] Attribute "Who made it" : **Someone else** (Etsy le sait pour POD)
  - [ ] Attribute "What is it" : **A finished product**
  - [ ] Attribute "When was it made" : **2026** (la date d'impression, pas l'œuvre originale)
  - [ ] Renew automatically ON

### P1.6 — Commander un échantillon physique (3-5 j de délai)

- [ ] 🔴👤 Acheter ton propre produit (test A2 encadré chêne, ~67 €) — depuis ton propre Etsy ou directement Gelato Sample Order
- [ ] 👤 Vérifier à la réception :
  - [ ] Fidélité colorimétrique vs ce que tu avais visualisé
  - [ ] Qualité du papier / cadre (équerres, vitrage, fixation)
  - [ ] Emballage (carton tube ou colis plat, anti-pli)
  - [ ] Délai effectif vs annoncé
- [ ] 👤 **Décision go/no-go** sur l'étape suivante. Si défaut, retravailler le master ou changer de spec produit.

**Livrable P1** : 1 listing live sur Etsy, 1 échantillon physique validé, processus manuel maîtrisé.

---

## PHASE P2 — Collection d'amorçage : 3 produits × 5 œuvres (1 semaine)

*15 listings d'un coup pour avoir une vitrine cohérente. Toujours manuel, mais répété — c'est ce qui va te dire si l'effort/listing est tenable et révéler les points à automatiser en priorité en P3.*

### P2.1 — Choisir la 1re collection thématique (0,5 j)

Recommandation : **Herbiers** ou **Maîtres hollandais** (les deux ont du sourcing déjà fait dans le cockpit ; herbiers via BHL si la clé API est en place, hollandais via Rijksmuseum si la clé est en place).

- [ ] 👤 Lancer un sourcing live pour 15-20 œuvres dans le thème choisi
- [ ] 👤 Valider les gates dans le cockpit (REVIEW → décision humaine)
- [ ] 👤 Score les 15 retenues → garder les **5 meilleures** (filtre cockpit "score ≥ 6.5")
- [ ] 👤 Générer le marketing 5 langues pour chacune

### P2.2 — Produire les 5 œuvres × 3 produits (3-4 j)

Pour chaque œuvre (× 5) :

- [ ] 👤 Restauration master (procédure P1.2) — ~30 min par œuvre une fois le workflow rodé
- [ ] 👤 Créer 3 produits Gelato : poster nu A2, poster encadré chêne A2, **et un giftable** (mug ou torchon selon l'œuvre)
- [ ] 👤 Publier vers Etsy via intégration Gelato
- [ ] 👤 Vérifier chaque listing (titre, tags, prix, description, images)

**Total : 5 œuvres × 3 produits = 15 listings**

### P2.3 — Setup canaux marketing minimal (1 j)

- [ ] 👤 Créer le compte **Pinterest Business** (canal n°1 pour wall art déco)
- [ ] 👤 Créer 1 tableau par collection thématique
- [ ] 👤 Préparer 3-5 **pins** par œuvre (utiliser les hero shots IA si déjà générés, sinon les mockups Gelato)
- [ ] 👤 Créer un compte **Instagram** (optionnel P2, mais reservation du handle)
- [ ] 👤 Publier 3-4 pins le 1er jour, puis 1-2/jour pendant 1 semaine

### P2.4 — Mesure & ajustement (en continu sur P2)

- [ ] 👤 Suivre quotidiennement : impressions Etsy, clics, ventes
- [ ] 👤 Logger dans un Sheet (en attendant l'analytics du cockpit) : pour chaque listing, impressions/jour
- [ ] 👤 Au bout d'une semaine : **revue de hit-rate** (combien des 15 listings ont eu ≥ 1 vente ?)

**Livrable P2** : 15 listings en ligne, premiers pins Pinterest, premiers visiteurs réels, point de mesure du hit-rate.

---

## PHASE P3 — Automation du tunnel (2-3 semaines)

*C'est ici qu'on remet du code. Pas avant — le manuel de P0-P2 a révélé les vrais frottements à automatiser en priorité.*

### P3.1 — Restauration des masters via worker IA (2-3 j) ⚙️

- [ ] ⚙️ Ajouter un script `agents/restoration_agent.py` qui :
  - Lit les œuvres dont `status='score'` et `decision='produire'`
  - Télécharge le master HD depuis `imageUrl`
  - Lance un upscale (Real-ESRGAN local OU API Replicate)
  - Sauve dans `web/public/masters/{workId}.jpg` (ou R2/S3 plus tard)
  - PATCH la work avec `localFile` rempli
- [ ] ⚙️ Endpoint `/api/restoration/start { id }` dans Next.js qui kickoff la restauration

### P3.2 — Génération mockups via Dynamic Mockups + Flux Pro (3-4 j) ⚙️

- [ ] ⚙️ Ajouter route `/api/mockup { id, scene }` qui :
  - Génère les 3 mockups de base via [Dynamic Mockups API](https://dynamicmockups.com/integrations/etsy/)
  - Génère les 3 hero shots IA via [fal.ai Flux Pro Kontext](https://fal.ai/models/fal-ai/flux-pro/kontext) + compositing PIL
  - Stocke les 6 URLs dans `Work.mockups` (nouveau champ Json à ajouter au schéma Prisma)
- [ ] ⚙️ Bouton "Générer les 6 mockups" dans la fiche œuvre du cockpit
- [ ] ⚙️ Optionnel : pré-générer pour les œuvres `decision='produire'` en background

### P3.3 — Push automatique vers Etsy via API (3-5 j) 🔴⚙️

- [ ] ⚙️ Setup [Etsy Developer App](https://www.etsy.com/developers) + OAuth2 PKCE flow dans Next.js
- [ ] ⚙️ Route `/api/etsy/publish { id }` qui :
  1. Construit le listing à partir des données cockpit (marketing FR + mockups + variants Gelato)
  2. POST `createDraftListing` (titre, desc, prix, taxonomy, shipping profile, return policy)
  3. POST `uploadListingImage` × 10 (les mockups)
  4. POST `updateListingInventory` (variants taille + cadre)
  5. PATCH la work avec `etsyListingId`
- [ ] ⚙️ Stocker `ETSY_API_KEY` + tokens OAuth en env vars Vercel (chiffrés)
- [ ] ⚙️ Bouton "Publier sur Etsy" dans le cockpit

### P3.4 — Webhook Etsy `order.paid` → Gelato create order (3-4 j) 🔴⚙️

- [ ] ⚙️ Configurer le webhook Etsy (Etsy v3 webhooks GA depuis 2025)
- [ ] ⚙️ Route `/api/etsy/webhook` qui valide le HMAC-SHA256 et :
  1. Récupère le receipt complet (GET `resource_url`)
  2. Pour chaque line item, mappe `SKU → workId → productUid Gelato`
  3. POST `https://order.gelatoapis.com/v4/orders` (création commande)
  4. Stocke la commande dans une nouvelle table `Order` (à ajouter à Prisma)
- [ ] ⚙️ Stocker `GELATO_API_KEY` en env var Vercel

### P3.5 — Webhook Gelato `shipped` → tracking Etsy (1-2 j) ⚙️

- [ ] ⚙️ Route `/api/gelato/webhook` qui :
  1. Sur `order_item_tracking_code_updated`, récupère le tracking
  2. POST sur Etsy `/v3/.../receipts/{receipt_id}/tracking` pour informer le client
  3. Update la table `Order` avec le statut

### P3.6 — Production partner declaration check (0,5 j)

- [ ] ⚙️ Ajouter une checklist visible dans le cockpit ("Production partner Gelato déclaré sur Etsy ? OUI/NON")
- [ ] ⚙️ Audit log de toutes les fiches publiées (qui, quand, vers quel listing Etsy)

**Livrable P3** : un clic dans le cockpit déclenche restauration → mockups → publication Etsy. Une vente Etsy déclenche automatiquement la fab Gelato → expédition → tracking au client.

---

## PHASE P4 — Analytics + boucle feedback (1 semaine)

*Mettre en place ce qui fait du système un actif, pas juste un outil.*

### P4.1 — Capture des ventes dans la DB (1 j) ⚙️

- [ ] ⚙️ Webhook Etsy `order.paid` + `order.shipped` + `order.delivered` → INSERT dans `Sale` (table déjà au schéma)
- [ ] ⚙️ Stocker prix, montant, dates, workId, product (variant size + frame)
- [ ] ⚙️ Backfill : appel Etsy API pour récupérer les ventes historiques (P1 + P2)

### P4.2 — Dashboard analytics dans le cockpit (1-2 j) ⚙️

- [ ] ⚙️ Nouvel onglet "Analytics" :
  - Hit-rate global (œuvres vendues / œuvres listées sur 30 jours)
  - Marge nette moyenne par produit
  - Top 5 œuvres / collections par revenu
  - Approche du seuil Offsite Ads (10 000 € sur 365j glissants)
- [ ] ⚙️ Routes `/api/analytics/*` pour les calculs

### P4.3 — Repondération du scoring sur les ventes (2-3 j) ⚙️

- [ ] ⚙️ Script mensuel (cron Vercel ou manuel) qui :
  - Pour chaque œuvre vendue ≥ 3× : marque "gagnant"
  - Pour chaque œuvre listée ≥ 60j sans vente : marque "perdant"
  - Régression linéaire des 4 axes (momentum / attribution / translatab / competition) contre la cible "gagnant ?"
  - Propose de nouveaux poids → bouton humain "Appliquer"
- [ ] ⚙️ Sauvegarder l'historique des poids dans une table `ScoringWeights`

### P4.4 — Alertes opérationnelles (0,5 j) ⚙️

- [ ] ⚙️ Email/Slack quand :
  - 1re vente
  - Marge mensuelle < seuil de rentabilité
  - Approche du seuil Offsite Ads (≥ 80 % du 10 k€)
  - Listings sans vente depuis 90 j (à dépublier ou changer)

**Livrable P4** : le système s'améliore en lisant ses propres ventes.

---

## Garde-fous à ne JAMAIS retirer (de `CLAUDE.md` règles dures)

1. 🔴 **Validation humaine des gates DP/marque** — une erreur = suspension de compte Etsy. Jamais d'automation full sur G1/G2.
2. 🔴 **Échantillon physique** avant le lancement d'un nouveau produit (canvas, mug, torchon, etc.)
3. 🔴 **Veille politique Etsy/Amazon** — les règles évoluent. Re-checker tous les 6 mois.
4. 🔴 **Attribution "sourced by"** sur chaque fiche, jamais "made by".
5. 🔴 **Ne jamais commit de secrets** (clés API Etsy / Gelato / Anthropic / Neon).

---

## Estimations financières & temporelles

### Coût total mise en place (one-shot)

| Poste                                   | Coût            |
|-----------------------------------------|-----------------|
| Dépôt marque INPI (FR)                  | 250 € (optionnel) |
| Nom de domaine .com + .fr               | 30 €/an         |
| Échantillon physique 1er produit        | ~70 €           |
| Gelato compte                           | gratuit (Plus à $20/mo dès 15 ventes/mois) |
| Dynamic Mockups Pro                     | $15/mo          |
| fal.ai (Flux Pro Kontext)               | ~$10-20/mo en P3 |
| Anthropic API (déjà en place)           | $5-20/mo selon usage |
| Vercel + Neon (déjà en place)           | gratuit Phase 0 |
| **TOTAL démarrage**                     | **~400 €**      |
| **TOTAL mensuel récurrent dès P3**      | **~$50-80**     |

### Temps total pour un founder solo (~20h/sem)

| Phase | Travail concentré | Travail dispersé / attente | Total semaines |
|-------|-------------------|----------------------------|----------------|
| P0    | 1 sem.            | 0-1 sem. (validation INPI) | 1-2            |
| P1    | 0,5 sem.          | 0,5 sem. (délai échantillon) | 1            |
| P2    | 1 sem.            | mesure en continu          | 1              |
| P3    | 2 sem.            | 1 sem. (tests, OAuth)      | 2-3            |
| P4    | 0,5 sem.          | mesure en continu          | 1              |
| **TOTAL** |                |                             | **6-8 semaines** |

---

## Décisions à prendre en cours de route

1. **Après P1 (1re vente échantillon)** : la qualité Gelato te satisfait-elle ? Ou faut-il passer à Prodigi pour le premium ?
2. **Après P2 (15 listings, 2-3 semaines)** : hit-rate ≥ 2 % ? Si oui → P3. Si non → revoir le sourcing/scoring, pas le code.
3. **Après P3 (automation)** : ajouter eBay maintenant (cf. recommandation `process-vente-production.md` §7) ?
4. **Après P4 (analytics)** : repondérer le scoring 1× par mois ? Trimestriel ?

---

*Ce document est vivant. À chaque vente significative, revenir le mettre à jour avec ce qui s'est passé en réalité vs ce qui était prévu — c'est la même boucle de feedback que le scoring.*
