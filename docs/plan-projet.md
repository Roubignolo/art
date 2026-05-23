# Plan de projet — Marque POD « domaine public curé » quasi-automatisée

*Todo maître par chantiers et sous-chantiers. Cases à cocher prêtes à coller dans Notion/Linear/Trello. Les marqueurs : 🔴 chemin critique · 🔒 bloquant pour d'autres tâches · ⚙️ automatisable à terme · 👤 garder un humain dans la boucle.*

---

## Vue d'ensemble — 9 chantiers

| # | Chantier | Rôle | Dépend de |
|---|----------|------|-----------|
| A | Légal & conformité | Fondations (protège les comptes) | — |
| B | Sourcing & contenu | Matière première | A |
| C | Moteur de scoring / IA | Le cerveau décisionnel | B |
| D | Webapp de pilotage | Le poste de commande | B, C, E |
| E | Printful & marketplaces | La chaîne de production | A |
| F | Site & vitrine de marque | Les canaux de vente | A, E |
| G | Marketing & acquisition | La demande | F |
| H | Données & analytics | La boucle de feedback | D |
| I | Opérations & pilotage | La cadence | tous |

**Chemin critique 🔴 :** A (légal) → E (Printful/Etsy) → B (sourcing) → C (scoring) → première collection en ligne → mesure du hit-rate → décision d'automatiser (D).

---

## CHANTIER A — Légal & conformité 🔒

### A1. Structure & cadre
- [ ] 🔴 Vérifier que la structure juridique actuelle (activité POD existante) couvre la nouvelle marque, ou créer/adapter
- [ ] Définir la marque commerciale et le nom de boutique
- [ ] 🔴🔒 Déposer la marque (INPI pour la France, EUIPO pour l'UE) — vérifier l'antériorité avant
- [ ] Réserver le nom de domaine + handles réseaux sociaux cohérents

### A2. Conformité domaine public (le cœur du risque)
- [ ] 🔴🔒 Rédiger la **procédure de vérification DP** (double règle US ≤1930 / UE décès +70 ans)
- [ ] 🔒 Créer le **registre de provenance** : pour chaque œuvre, archiver preuve de statut DP (artiste, dates, institution, lien source, capture licence) — c'est ta défense en cas de litige
- [ ] Définir la règle anti-marque résiduelle (personnages/logos exclus même si DP)
- [ ] Lister les sources autorisées (institutions CC0) et interdites (versions « enhanced » propriétaires)

### A3. Conformité plateformes
- [ ] 🔴 Cartographier les Creative Standards d'Etsy et fixer la règle **attribution « sourced by », jamais « made by »**
- [ ] Vérifier les politiques Amazon (contenu, marque, IA)
- [ ] Définir la mention provenance type sur chaque fiche produit

### A4. Conformité commerciale & RGPD
- [ ] Rédiger CGV, mentions légales, politique de retour
- [ ] 👤 Politique de confidentialité **RGPD** (cookies, données clients, newsletter) — domaine que tu maîtrises déjà
- [ ] Cadre fiscal : TVA, **OSS** pour les ventes intra-UE, seuils, déclarations
- [ ] Vérifier obligations sur les ventes US (sales tax via marketplace facilitator)

---

## CHANTIER B — Sourcing & production de contenu

### B1. Cartographie & accès aux sources
- [ ] 🔒 Recenser les sources et leurs **API/accès** : Met (Open Access API), Rijksmuseum (Rijksdata API), Smithsonian Open Access API, Art Institute of Chicago API, Cleveland Museum API, Biodiversity Heritage Library, NYPL, Library of Congress
- [ ] Documenter pour chaque source : licence, résolution dispo, format (TIFF/JPG), limites d'API, métadonnées exposées
- [ ] Définir les territoires esthétiques de départ (botanique, ornithologie, celestial, cartes, ukiyo-e, anatomie…)

### B2. Pipeline d'ingestion ⚙️
- [ ] Script de téléchargement des **masters haute résolution** + métadonnées
- [ ] Stockage organisé (œuvre, source, licence, résolution, statut DP)
- [ ] Dédoublonnage et nommage normalisé

### B3. Pipeline de restauration (nanobanana + retouche) ⚙️👤
- [ ] Définir les étapes : upscale, débruitage, correction colorimétrique, nettoyage des défauts, recomposition éventuelle
- [ ] 🔒 Cette étape = la « valeur artistique ajoutée » qui sécurise juridiquement → la documenter
- [ ] Contrôle qualité automatisé : vérif **≥150 DPI (idéal 300)** à la taille produit visée
- [ ] 👤 Validation visuelle humaine avant publication (au moins en phase 1)

### B4. Génération des visuels produit
- [ ] Création des mockups Printful par produit
- [ ] Recadrage automatique selon le ratio de chaque produit

---

## CHANTIER C — Moteur de scoring / IA (le cerveau)

### C1. Connecteurs de données ⚙️
- [ ] Brancher signaux tendances : Pinterest Trends, Google Trends, tendances de recherche Etsy
- [ ] Récupérer données concurrence : nb de listings + nb d'avis par mot-clé/thème

### C2. Implémentation des gates 🔴🔒
- [ ] Gate G1 (DP US + UE) · G2 (marque résiduelle) · G3 (source propre) · G4 (résolution)
- [ ] 👤 Validation humaine des gates G1/G2 au démarrage avant automatisation complète

### C3. Implémentation du scoring ⚙️
- [ ] Prompt Claude → sortie **JSON** (gates, 4 scores, décision, angle, accroche provenance)
- [ ] Calcul du score pondéré + application du seuil (≥6,5 produire / 5–6,4 file d'attente / sinon rejet)
- [ ] Plafond de N œuvres produites/semaine (anti-saturation du catalogue)

### C4. Boucle de feedback ⚙️
- [ ] Logger score prédit vs ventes réelles par œuvre
- [ ] Routine mensuelle de réajustement des poids des axes et du seuil

---

## CHANTIER D — Webapp de pilotage (poste de commande) 🔴

### D1. Spécifications fonctionnelles
- [ ] Dashboard : hit-rate, marge, ventes, file de production, alertes
- [ ] Module **file d'attente d'œuvres scorées** avec validation/rejet humain en 1 clic
- [ ] Module **registre de provenance** (consultable, exportable — preuve de conformité)
- [ ] Module **suivi production** (statut : sourcé → restauré → mocké → publié)
- [ ] Module **analytics ventes** branché sur le calculateur de viabilité
- [ ] Gestion des collections/territoires esthétiques

### D2. Architecture & stack
- [ ] Choisir la stack (ex. front React, back Node/Python, base Postgres, auth, hébergement)
- [ ] Schéma de base de données (œuvres, scores, produits, ventes, provenance)
- [ ] Gestion sécurisée des clés API (Printful, Etsy, Amazon, Claude, sources DP)

### D3. Intégrations
- [ ] 🔒 API Claude (scoring) · API Printful (création produit/commande) · API Etsy · API Amazon · sources DP · pipeline restauration
- [ ] Webhooks (commandes Printful, ventes marketplaces)

### D4. Build itératif
- [ ] **MVP** : ingestion + scoring + validation humaine + publication manuelle assistée
- [ ] **V1** : publication semi-auto + analytics + registre provenance
- [ ] **V2** : automation de bout en bout avec garde-fous humains sur les gates

---

## CHANTIER E — Printful & marketplaces 🔴

- [ ] 🔴 Configurer le compte Printful et sélectionner le catalogue produits prioritaires (poster, encadré, 1 giftable)
- [ ] 🔒 Maîtriser les **gabarits print** par produit (zones d'impression, DPI, bleed)
- [ ] Connexion Printful → Etsy · Printful → Amazon
- [ ] Stratégie de **pricing automatique** (base Printful + marge cible, cf. calculateur)
- [ ] Gestion des variantes (tailles, cadres, couleurs)
- [ ] ⚙️ Webhooks de commande → fulfillment automatique
- [ ] 👤 Commander des **échantillons physiques** pour valider la qualité d'impression avant de scaler

---

## CHANTIER F — Site & vitrine de marque

### F1. Canal d'amorçage (rapide)
- [ ] 🔴 Ouvrir la boutique **Etsy** (attribution « sourced by », fiches provenance complètes)
- [ ] Charte visuelle de la boutique (bannière, logo, à-propos avec le récit de marque)

### F2. Site propre (phase 2)
- [ ] Boutique Shopify (ou custom) pour capter la marge et sortir de la dépendance plateforme
- [ ] Template de **fiche produit avec provenance auto-générée** (le storytelling = ta différenciation)
- [ ] SEO technique + pages collections thématiques

---

## CHANTIER G — Marketing & acquisition

### G1. Identité de marque
- [ ] Finaliser nom (après vérif marque), logo, charte, **ton de voix** (curateur érudit et chaleureux)
- [ ] Récit de marque (concept « Provenance » : transparence radicale sur l'origine)

### G2. Canaux (par priorité)
- [ ] 🔴 **Pinterest** (moteur n°1 déco) : tableaux par collection, ⚙️ automation des pins
- [ ] Instagram : contenu **avant/après restauration** (fort taux d'engagement)
- [ ] Etsy SEO : recherche de mots-clés thématiques précis par collection
- [ ] Email/CRM : capture + séquences (nouveautés par collection)

### G3. Calendrier éditorial
- [ ] Planning par collection + saisonnalité (cadeaux, fêtes)
- [ ] ⚙️ Génération assistée des descriptions/visuels sociaux

---

## CHANTIER H — Données & analytics

- [ ] Définir les **KPIs** : hit-rate, marge nette/vente, panier moyen, CAC, taux d'avis, seuil Offsite Ads Etsy (10 000 $/an)
- [ ] Tableau de bord branché sur le calculateur de viabilité (chiffres réels)
- [ ] ⚙️ Reporting automatique hebdo/mensuel
- [ ] Alerte sur dérive de marge ou approche du seuil Offsite Ads

---

## CHANTIER I — Opérations & pilotage

- [ ] Cadence de revue (hebdo : production/file ; mensuel : réinjection feedback + repondération)
- [ ] ⚙️👤 SAV automatisé au maximum, escalade humaine sur litiges
- [ ] Process retours / réclamations / avis négatifs
- [ ] Veille conformité (changements de politique Etsy/Amazon, nouveautés DP au 1ᵉʳ janvier)

---

## Phasage recommandé

**Phase 0 — Fondations & validation (semaines 1-4)**
Chantier A (légal/conformité) + E (Printful/Etsy de base) + B1 (sourcing manuel d'une collection) + scoring **manuel** avec Claude. Objectif : 5 œuvres restaurées, 3 produits en ligne, premières ventes. *Aucune ligne de webapp ici.*

**Phase 1 — MVP semi-automatisé (semaines 5-12)**
Si le hit-rate de la Phase 0 dépasse le seuil du calculateur (~2,6 %) : construire le MVP de la webapp (C + D1/D2), automatiser le scoring et l'ingestion, garder la validation humaine. Élargir à 2-3 collections.

**Phase 2 — Automation & scale (mois 4-9)**
Webapp V1/V2, publication semi-auto puis auto avec garde-fous, site propre (F2), montée en puissance marketing (G), boucle de feedback active (H). Scaler le volume **seulement** une fois le hit-rate stabilisé.

**Phase 3 — Optimisation continue**
Repondération du moteur, nouvelles collections pilotées par la donnée, diversification produits/canaux.

---

## Garde-fous à ne jamais retirer 👤

- Validation humaine des gates DP/marque (G1/G2) — une erreur = suspension de compte.
- Échantillons physiques avant tout scale d'un nouveau produit.
- Veille sur les politiques plateformes et le seuil Offsite Ads.
- Ne pas automatiser la publication avant d'avoir prouvé le hit-rate manuellement.

---

*Je ne suis ni avocat ni conseiller financier ; le chantier A (notamment statut DP, marque et fiscalité OSS) mérite une validation par des spécialistes avant le passage à l'échelle.*
