---
title: "Dossier P0 — Création de la micro-entreprise et lancement de la boutique Etsy"
subtitle: "Projet *Art* — Édition d'art à la demande sur domaine public curé"
author: "Jérôme Firon"
date: "24 mai 2026"
lang: fr-FR
documentclass: article
geometry:
  - margin=2.2cm
fontsize: 11pt
colorlinks: true
linkcolor: NavyBlue
urlcolor: NavyBlue
toc: true
toc-depth: 2
numbersections: true
header-includes:
  - \usepackage{microtype}
  - \usepackage[svgnames]{xcolor}
  - \usepackage{fancyhdr}
  - \pagestyle{fancy}
  - \fancyhead[L]{\small Dossier P0 — Création micro-entreprise}
  - \fancyhead[R]{\small Projet \emph{Art}}
  - \fancyfoot[C]{\thepage}
  - \renewcommand{\headrulewidth}{0.2pt}
---

\newpage

# Résumé exécutif

Ce dossier consolide en un seul document l'ensemble des démarches administratives, juridiques et opérationnelles nécessaires à l'ouverture de la boutique Etsy du projet *Art* — édition d'art à la demande basée sur du **domaine public curé**, produit via partenaires POD européens (Gelato par défaut, Prodigi pour la signature premium).

Il couvre la **phase P0** au sens de la roadmap interne : pré-requis non techniques avant la mise en vente. À l'issue de P0, le porteur disposera d'un statut juridique opérationnel, d'un compte vendeur Etsy configuré et conforme, et d'une chaîne de production POD déclarée.

**Trois chiffres à retenir :**

- **0 €** : coût d'immatriculation de la micro-entreprise au guichet unique INPI.
- **~110 €** : coût total P0 hors dépôt INPI de marque (~360 € si dépôt).
- **10 à 13 jours calendaires** : délai prévisionnel entre la saisie INPI et l'ouverture effective de la boutique Etsy.

**Trois décisions structurantes à prendre :**

1. **Versement libératoire de l'impôt sur le revenu** — oui si revenu fiscal de référence 2024 au plus 29 315 € par part[^1].
2. **ACRE** — éligibilité conditionnelle (voir §4.4) ; à demander dans les 60 jours suivant l'immatriculation[^2].
3. **Dépôt de marque INPI** — recommandé mais optionnel (250 €) ; peut être fait après l'immatriculation pour cession directe à l'entreprise.

[^1]: Revenu fiscal de référence sur avis d'imposition 2025 portant sur les revenus 2024. Seuil par part fiscale ; majoration 50 % par demi-part additionnelle. Source : [Urssaf — Modalités d'adhésion au versement libératoire 2026](https://www.autoentrepreneur.urssaf.fr/portail/accueil/sinformer-sur-le-statut/toutes-les-actualites/modalites-dadhesion-au-verseme-2.html).
[^2]: Article L. 131-6-4 du Code de la Sécurité sociale. Délai de 60 jours à compter de la date de début d'activité déclarée. Source : [Service-Public — Aide à la création ou reprise d'une entreprise (Acre)](https://entreprendre.service-public.gouv.fr/vosdroits/F11677).

\newpage

# Phase et contexte projet

## Position dans la roadmap

Le projet *Art* est organisé en cinq phases consécutives, de l'ouverture du compte Etsy à l'automatisation complète du tunnel sourcing → mise en vente :

| Phase | Objet                                            | Durée founder solo | Statut          |
|-------|--------------------------------------------------|---------------------|-----------------|
| **P0** | Pré-requis non techniques (objet du présent dossier) | 1-2 semaines       | À démarrer      |
| P1    | Premier listing échantillon                       | 1 semaine           | À venir         |
| P2    | Collection d'amorçage (15 listings)               | 1 semaine           | À venir         |
| P3    | Automatisation mockups + push Etsy + webhook Gelato | 2-3 semaines       | Stubs prêts     |
| P4    | Analytics + repondération scoring                 | 1 semaine           | À venir         |

Source détaillée des phases : [`docs/roadmap-mise-en-vente.md`](roadmap-mise-en-vente.md).

## Thèse commerciale rappelée

La rentabilité du projet repose sur la **curation, la restauration et la confiance** plutôt que sur le volume. Trois conséquences directes pour P0 :

1. La conformité administrative (SIRET déclaré, statut clair) est un **signal de marque** et non une formalité — la promesse « provenance documentée » s'étend à la transparence sur le vendeur.
2. La déclaration des production partners (Gelato + Prodigi) auprès d'Etsy est **non négociable** : son omission est cause de suspension du shop[^3].
3. La marque (nom + dépôt) protège un actif au cœur du modèle (la curation porte le nom de la boutique) — recommandée dès P0.

[^3]: Politique Etsy sur les vendeurs POD : tout produit fabriqué par un tiers doit faire l'objet d'une déclaration explicite de production partner. Source : [Gelato Help Center — Do I have to list Gelato as a production partner on Etsy?](https://support.gelato.com/en/articles/8996467-do-i-have-to-list-gelato-as-a-production-partner-on-etsy).

\newpage

# Bilan financier P0

## Coûts one-shot

| Poste                                          | Coût       | Optionnel | Justification                          |
|------------------------------------------------|------------|-----------|----------------------------------------|
| Immatriculation micro-entreprise INPI          | **0 €**    | Non       | Gratuit pour activité commerciale[^4]  |
| Ouverture compte bancaire pro (offre starter)  | **0 €**    | Oui*      | Obligation seulement au-delà de 10 k€ CA pendant 2 ans consécutifs |
| Nom de domaine .com + .fr (1 an)               | ~30 €      | Non       | Protection du nom de marque            |
| Dépôt de marque INPI (1 classe)                | 250 €      | Oui       | Recommandé pour pérenniser la boutique |
| Échantillon physique Gelato (test qualité P1)  | ~70 €      | Non       | Validation produit avant 1er listing public |
| Listing fees Etsy initiaux (15 × 0,20 $)       | ~3 $       | Non       | Frais de référencement amortis sur 4 mois |
| **Total minimal (sans dépôt marque)**          | **~110 €** |           |                                        |
| **Total avec dépôt marque**                    | **~360 €** |           |                                        |

\* Vivement recommandé en pratique pour la séparation des flux comptables, gratuit chez Shine (offre Start).

[^4]: Source : [INPI — Créer en tant que micro-entrepreneur](https://www.inpi.fr/realiser-demarches/formalites-dentreprises/creer-en-tant-que-micro-entrepreneur). La création est gratuite que l'activité soit commerciale, libérale ou artisanale.

## Coûts récurrents post-P0 (pour mémoire)

Détaillés au §coûts du dossier financier annexe. Ordre de grandeur :

- **P0 → P2** (manuel) : ~10 $/mois (essentiellement Anthropic API pour scoring/marketing).
- **P3** (automatisation mockups) : ~50 $/mois (Dynamic Mockups Pro + fal.ai + Anthropic).
- **Phase scale** : ~100-135 $/mois (ajout Gelato+ à 15 ventes/mois).

\newpage

# Création de la micro-entreprise

## Pourquoi ce statut

Le statut de **micro-entreprise** (anciennement auto-entrepreneur) est retenu pour la phase de démarrage du projet, pour quatre raisons :

1. **Création gratuite et immédiate** au guichet unique INPI ([procedures.inpi.fr](https://procedures.inpi.fr))[^4].
2. **Plafonds de chiffre d'affaires élevés** : 203 100 € en vente de biens pour la période 2026-2028[^5], largement au-dessus de la cible commerciale des deux premières années.
3. **Comptabilité ultra-simplifiée** : tenue d'un livre de recettes uniquement, pas de bilan ni de TVA à gérer tant que le seuil de franchise n'est pas atteint.
4. **Réversibilité** : bascule vers EURL ou SASU sans rupture d'activité quand le scaling le justifie (décision documentée dans `CLAUDE.md` : *bascule société seulement au scale*).

[^5]: Plafond fixé pour la période triennale 2026-2028, en hausse de 14 400 € par rapport au plafond précédent (188 700 €). Source : [Urssaf — 2026 : modification des seuils de chiffre d'affaires](https://www.autoentrepreneur.urssaf.fr/portail/accueil/sinformer-sur-le-statut/toutes-les-actualites/2026--modification-des-seuils-de.html).

## Documents à préparer

Avant d'entamer la saisie sur [procedures.inpi.fr](https://procedures.inpi.fr), réunir les pièces suivantes au format numérique (PDF ou JPG/PNG en couleur, recto-verso, < 7 Mo)[^6] :

| Pièce                                          | Détail                                       |
|------------------------------------------------|----------------------------------------------|
| Pièce d'identité valide                         | CNI ou passeport, recto + verso, en couleur  |
| Justificatif de domicile                       | Facture électricité, gaz, internet ou avis d'imposition de moins de 3 mois |
| Déclaration sur l'honneur de non-condamnation  | Document rédigé par le porteur, attestant de l'absence de condamnation interdisant l'exercice d'une activité commerciale |
| Attestation de filiation                       | Extrait d'acte de naissance simple ou copie du livret de famille (parfois demandé) |
| RIB                                            | Pour le prélèvement des cotisations URSSAF   |

[^6]: Sources techniques : [INPI — Formalités de création](https://www.inpi.fr/realiser-demarches/formalites-dentreprises/formalites-de-creation) et [Service-Public — Guichet des formalités](https://entreprendre.service-public.gouv.fr/vosdroits/R61572). Le portail accepte les formats PDF, JPG et PNG ; chaque pièce ne doit pas excéder 7 Mo.

## Saisie sur le guichet unique INPI

Le parcours en ligne se déroule en cinq étapes principales[^7] :

1. **Création d'un compte** sur [procedures.inpi.fr](https://procedures.inpi.fr).
2. **Choix de l'activité** : sélectionner *« Entreprise individuelle »* puis cocher *« Option pour le régime micro »*.
3. **Saisie des informations personnelles** (état civil, adresse, situation familiale).
4. **Dépôt des pièces justificatives** (cf. liste ci-dessus).
5. **Validation et signature électronique** du dossier.

[^7]: Source : [Service-Public — Guichet des formalités des entreprises](https://entreprendre.service-public.gouv.fr/vosdroits/R61572). Depuis le 1er janvier 2023, le guichet unique de l'INPI est l'unique point d'entrée légal pour toute formalité de création d'entreprise en France.

### Choix structurants à effectuer pendant la saisie

| Question du formulaire        | Choix retenu                                         |
|-------------------------------|------------------------------------------------------|
| Forme juridique                | Entreprise individuelle                              |
| Régime fiscal                  | Micro-entreprise (case dédiée)                       |
| Activité principale            | « Commerce de détail par correspondance ou Internet — édition et vente de reproductions d'art en domaine public » |
| Code APE / NAF                 | **4791B** — *Vente à distance sur catalogue spécialisé*[^8] |
| Date de début d'activité       | Date du jour ou jusqu'à 30 jours dans le futur       |
| Lieu d'exercice                | À domicile (option par défaut)                       |
| Adresse de l'entreprise        | Adresse personnelle du porteur                       |
| Régime social                  | Micro-social simplifié (lié automatiquement à l'option micro) |
| Régime de TVA                  | Franchise en base de TVA (option par défaut)         |
| Versement libératoire IR       | À décider selon revenu fiscal de référence (cf. §4.3) |

[^8]: Code APE applicable à l'ensemble des activités de vente à distance par Internet, y compris les boutiques Etsy, eBay et Amazon. Source : [Pôle Auto-Entrepreneur — Code APE 4791B](https://pole-autoentrepreneur.com/liste-code-ape/code-4791b/) et [Pappers — Code APE 4791B](https://www.pappers.fr/code-naf-ape/4791b-vente-a-distance-sur-catalogue-specialise). L'activité n'est pas réglementée : aucune qualification professionnelle préalable n'est requise.

## Décision n°1 — Versement libératoire de l'impôt sur le revenu

Le versement libératoire permet de payer l'IR au fil de l'eau, directement à l'URSSAF, sous forme d'un pourcentage fixe appliqué au chiffre d'affaires encaissé. Pour la vente de biens, le taux est de **1 %** du CA[^9].

### Conditions d'éligibilité 2026

- Revenu fiscal de référence 2024 (sur avis d'imposition 2025) au plus **29 315 €** par part de quotient familial.
- Majoration de 50 % par demi-part additionnelle (ex. : couple sans enfant = 2 parts → seuil 58 630 €).
- Adhésion à demander à l'URSSAF **avant le 30 septembre N-1** pour application au 1er janvier N (donc avant le 30 septembre 2026 pour bénéficier dès 2027).

À noter : pour une création en cours d'année, l'option peut être exercée jusqu'à la fin du 3e mois suivant la création de l'activité[^9].

[^9]: Sources : [impots.gouv.fr — Le versement libératoire](https://www.impots.gouv.fr/professionnel/le-versement-liberatoire) et [Urssaf — Modalités d'adhésion au versement libératoire 2026](https://www.autoentrepreneur.urssaf.fr/portail/accueil/sinformer-sur-le-statut/toutes-les-actualites/modalites-dadhesion-au-verseme-2.html). Taux : 1 % vente de marchandises, 1,7 % prestations BIC, 2,2 % BNC.

### Avantage / inconvénient

- **Avantage** : pas d'effet de seuil sur l'IR (le revenu de la micro n'est pas réintégré dans la tranche marginale d'imposition). Idéal pour un porteur déjà imposable par ailleurs.
- **Inconvénient** : on paye 1 % du CA même si l'année est déficitaire. Pour la 1re année, où le CA est typiquement faible, l'option peut être moins favorable que l'IR classique avec abattement micro de 71 %.

**Recommandation pour ton cas** : à arbitrer en fonction de ton avis d'impôt 2025. Si tu es déjà au-dessus de la tranche à 11 % (revenu imposable > 11 497 € / part en 2024), l'option est nettement favorable dès que ton CA dépasse ~5 000 € / an. Sinon, l'IR classique avec abattement 71 % est probablement préférable la 1re année.

## Décision n°2 — ACRE (exonération partielle de cotisations sociales)

L'ACRE (Aide à la création ou reprise d'une entreprise) permet une exonération partielle des cotisations sociales personnelles pendant les 12 premiers mois d'activité.

### Réforme 2026 : taux d'exonération en baisse

**Calendrier critique[^10] :**

- Immatriculation **avant le 30 juin 2026** : exonération de **50 %** des cotisations sociales pendant 12 mois.
- Immatriculation **à partir du 1er juillet 2026** : exonération réduite à **25 %**.

[^10]: Source : [Service-Public — Aide à la création ou à la reprise d'une entreprise (Acre)](https://entreprendre.service-public.gouv.fr/vosdroits/F11677) et confirmé par les communications URSSAF de mars 2026 sur la réforme.

**Conséquence opérationnelle directe : déposer le dossier de création AVANT le 30 juin 2026** est financièrement supérieur, à condition d'être éligible.

### Conditions d'éligibilité ACRE (restrictives)

L'ACRE n'est **pas automatique** pour tout créateur. Pour en bénéficier, il faut entrer dans **au moins une** des catégories suivantes[^11] :

- Demandeur d'emploi indemnisé ou non (inscrit depuis 6 mois minimum sur les 18 derniers mois).
- Bénéficiaire du RSA, de l'ASS ou de l'ATA.
- Personne âgée de 18 à 25 ans inclus.
- Personne âgée de moins de 30 ans en situation de handicap.
- Création d'une activité dans un Quartier Prioritaire de la Politique de la Ville (QPV) ou une Zone France Ruralités Revitalisation (ZFRR).
- Salarié ou ancien salarié d'une entreprise en sauvegarde, redressement ou liquidation, qui reprend tout ou partie de l'entreprise.
- Bénéficiaire de la PreParE (prestation partagée d'éducation de l'enfant).

[^11]: Liste exhaustive des bénéficiaires : [Service-Public — Acre](https://entreprendre.service-public.gouv.fr/vosdroits/F11677). Condition supplémentaire transversale : n'avoir pas bénéficié de l'ACRE au cours des 3 années précédentes.

Si aucune de ces situations ne s'applique, **l'ACRE n'est pas accessible** — c'est un point important à clarifier avant d'estimer le coût net de la 1re année.

### Démarche

Si éligible :

1. Compléter le formulaire de demande d'ACRE (Cerfa n° 13584*02).
2. Envoyer à l'URSSAF compétente (au plus tard **60 jours après la déclaration de début d'activité**).
3. Joindre : justificatif de la situation (attestation France Travail, notification RSA, etc.) + extrait Kbis ou avis de situation INSEE + RIB.

L'absence de réponse de l'URSSAF dans un délai d'un mois vaut acceptation[^11].

## Décision n°3 — Régime de TVA

Par défaut, la micro-entreprise relève de la **franchise en base de TVA**[^12], avec deux conséquences :

- Pas de TVA facturée aux clients, pas de TVA collectée à reverser à l'État.
- Pas de TVA déductible sur les achats (notamment les commandes Gelato).
- Mention obligatoire sur toute facture : **« TVA non applicable, article 293 B du CGI »**.

[^12]: Sources : [impots.gouv.fr — Pour rester micro-entrepreneur](https://www.impots.gouv.fr/professionnel/questions/pour-rester-micro-entrepreneur-quel-montant-de-chiffre-daffaires-ou-de) et [Service-Public — Franchise en base de TVA](https://entreprendre.service-public.gouv.fr/vosdroits/F21746). Au 1er janvier 2026, les seuils restent inchangés par rapport à 2024 après plusieurs reports parlementaires.

### Seuils de franchise 2026

| Activité                              | Seuil de base | Seuil majoré |
|---------------------------------------|---------------|--------------|
| Vente de biens (cas du projet)        | **85 000 €**  | **93 500 €** |
| Prestations de services               | 37 500 €      | 41 250 €     |

Tant que le CA reste en dessous du seuil de base sur deux années civiles consécutives, le régime de franchise se reconduit automatiquement.

### Option pour la TVA — utile ou non ?

Possibilité d'opter volontairement pour le régime réel de TVA dès la création. **Non recommandé en P0** :

- La franchise est un avantage net : simplicité, prix d'affichage Etsy stable, marges nettes plus élevées sur le périmètre B2C.
- L'option ne devient intéressante que si les achats HT (Gelato facturé HT en intra-UE) deviennent significatifs face au CA — ce qui n'est pas le cas avant ~30 ventes/mois.

À réévaluer en P3-P4 si le volume grimpe rapidement.

## Numéros attribués après immatriculation

Une fois le dossier validé par l'INPI et transmis à l'INSEE[^13] :

| Numéro                              | Format                  | Usage                              |
|-------------------------------------|-------------------------|------------------------------------|
| **SIREN**                           | 9 chiffres              | Identifie l'entreprise              |
| **SIRET**                           | 14 chiffres (SIREN + NIC) | Identifie l'établissement principal |
| **N° TVA intracommunautaire**       | FR + clé + SIREN        | Achats B2B intra-UE (Gelato HT)    |
| **Code APE** (confirmé par INSEE)   | 4 chiffres + 1 lettre   | 4791B attendu                       |

[^13]: Délai de traitement : 1 à 4 semaines après validation du dossier complet, en pratique 7-15 jours pour un dossier sans irrégularité. Source : [INPI — Créer en tant que micro-entrepreneur](https://www.inpi.fr/realiser-demarches/formalites-dentreprises/creer-en-tant-que-micro-entrepreneur).

Vérification publique en ligne dès réception : [annuaire-entreprises.data.gouv.fr](https://annuaire-entreprises.data.gouv.fr).

## Suite immédiate : URSSAF & déclarations

Après réception du SIRET :

1. **Création de l'espace personnel URSSAF** sur [autoentrepreneur.urssaf.fr](https://www.autoentrepreneur.urssaf.fr).
2. **Choix de la fréquence de déclaration de CA** : mensuelle ou trimestrielle (recommandation : **trimestrielle** au démarrage — souplesse, moins de paperasse). Le choix est irréversible pour 12 mois.
3. **Première déclaration** : au prochain trimestre civil suivant la création, même si CA = 0 (déclaration nulle obligatoire, pénalité de 50 € par déclaration omise[^14]).
4. **Cotisations sociales** : prélèvement automatique sur le compte fourni, taux de **12,3 %** du CA encaissé pour la vente de biens (6,4 % la 1re année si ACRE 50 % obtenu).
5. **Demande d'ACRE** dans les 60 jours si éligible.

[^14]: Source : [Urssaf — Déclarer et payer mes cotisations](https://www.autoentrepreneur.urssaf.fr/portail/accueil/payer-mes-cotisations.html). Sanction prévue à l'article L. 133-6-7-2 du Code de la Sécurité sociale.

\newpage

# Marque et identité

## Vérification d'antériorité

Avant tout dépôt ou ouverture de compte Etsy, vérifier la disponibilité du nom de marque retenu :

- **Base INPI Marques** : [data.inpi.fr](https://data.inpi.fr) — recherche par dénomination, par classe Nice, par titulaire.
- **EUIPO TMview** : [tmdn.org/tmview](https://www.tmdn.org/tmview/) — recherche élargie à l'ensemble des registres européens et internationaux.

Classes Nice probablement pertinentes pour le projet :

| Classe | Objet                                                           |
|--------|------------------------------------------------------------------|
| 16     | Produits de l'imprimerie ; affiches ; reproductions graphiques  |
| 35     | Services de vente au détail en ligne                            |
| 41     | Services d'édition (mention « sourced by ») — facultatif        |

## Dépôt INPI (optionnel mais recommandé)

- **Tarif** : 190 € pour 1 classe en dépôt électronique + 40 € par classe supplémentaire (tarifs 2026 INPI[^15]).
- **Durée** : protection pour 10 ans, renouvelable.
- **Délai d'enregistrement** : 4 à 6 mois (publication au BOPI, période d'opposition, enregistrement définitif).
- **Recommandation** : déposer au nom de l'entreprise individuelle une fois le SIRET reçu, pour éviter une cession ultérieure du patrimoine personnel vers la micro.

[^15]: Source : [INPI — Coûts officiels du dépôt de marque](https://www.inpi.fr/proteger-vos-creations/proteger-votre-marque/les-cles-pour-bien-deposer-votre-marque).

## Réservation des actifs numériques

À effectuer **immédiatement** dès le nom validé, indépendamment de l'immatriculation :

- Nom de domaine **.com** et **.fr** (~15-20 €/an chacun chez OVH, Gandi ou Cloudflare Registrar).
- Compte **Instagram** + compte **Pinterest** avec le handle exact (gratuit, mais l'antériorité du compte compte dans les conflits ultérieurs de marque).

\newpage

# Configuration du compte Etsy

## Préalable : informations légales requises

Etsy exige depuis 2023 que tout vendeur français professionnel renseigne ses **identifiants fiscaux complets**[^16], faute de quoi le compte est suspendu après plusieurs rappels :

- **SIRET** complet (14 chiffres) dans le champ *Additional Taxpayer Identification*.
- **N° de TVA intracommunautaire** dans le champ principal, même en régime de franchise (le champ accepte un n° de TVA non assujetti).
- **Nom légal** = nom du porteur (en EI, il n'y a pas de personnalité morale séparée).
- **Adresse fiscale** = adresse déclarée à l'INPI.

[^16]: Source : [Etsy Help — What Are Sales Reporting Requirements for French Sellers?](https://help.etsy.com/hc/en-us/articles/360048262494-What-Are-Sales-Reporting-Requirements-for-French-Sellers) et [Etsy Help — Am I Required To Add a VAT ID to my Account?](https://help.etsy.com/hc/en-us/articles/360058652054-Am-I-Required-To-Add-a-VAT-ID-to-my-Account).

## DAC7 — Transmission automatique aux impôts

Conformément à la directive européenne DAC7 (transposée en droit français aux articles 1649 ter A à 1649 ter E du Code général des impôts), Etsy transmet annuellement à l'administration fiscale française les données de vente dès que le seuil suivant est atteint :

- **30 transactions ou plus** dans l'année civile, **OU**
- **2 000 € ou plus** de chiffre d'affaires brut sur Etsy[^17].

[^17]: Sources : [Etsy Help — What Information Does Etsy Report for EU Sellers?](https://help.etsy.com/hc/en-us/articles/17795509361431-What-Information-Does-Etsy-Report-for-EU-Sellers) et [impots.gouv.fr — Transfert d'informations DPI-DAC7](https://www.impots.gouv.fr/transfert-dinformations-en-application-des-dispositifs-dpi-dac7-plateformes-deconomie-collaborative).

Etsy fournit à chaque vendeur un récapitulatif PDF des données transmises, disponible avant le 31 janvier de chaque année. Avec une micro-entreprise déclarée, ce dispositif est neutre : il sert au contrôle, pas à imposer une obligation supplémentaire.

## Configuration de la boutique

Une fois le compte vendeur ouvert sur [etsy.com/sell](https://www.etsy.com/sell), procéder dans l'ordre :

1. **Renseignement des informations fiscales** (Shop Manager → Finances → Legal and tax information) : SIRET, n° TVA, nom légal, adresse.
2. **Configuration des paiements** : Etsy Payments en EUR, RIB IBAN FR (cf. recommandation §coût bancaire).
3. **Branding** :
   - Nom de boutique = marque retenue.
   - Bannière 1200 × 300 px.
   - Logo (carré, fond neutre).
   - Page « À propos » (3 paragraphes : pourquoi, comment, qui).
   - Annonce de boutique (1 phrase mise en avant).
4. **Politiques de boutique** (obligatoires pour pouvoir publier) :
   - Politique de retour (cf. [`process-vente-production.md`](process-vente-production.md) §6).
   - Politique d'expédition (UE 3-6 j, US 5-10 j via Gelato).
   - Conditions générales mentionnant la formule **« sourced by »** (provenance documentée, jamais « made by »).
   - Politique de confidentialité (RGPD).
5. **Profil de livraison** : un profil par zone (UE, UK, US, monde), coûts pré-calculés via le [Gelato shipping calculator](https://www.gelato.com/shipping).

\newpage

# Déclaration des production partners

Etsy impose la déclaration explicite de tout tiers fabriquant pour le compte du vendeur. Sans cette déclaration, le shop encourt une **suspension immédiate**[^18].

[^18]: Source : [Gelato Help Center — Do I have to list Gelato as a production partner on Etsy?](https://support.gelato.com/en/articles/8996467-do-i-have-to-list-gelato-as-a-production-partner-on-etsy). Politique applicable à tout vendeur POD.

## Comptes à créer

| Service                | URL                        | Coût           | Usage projet                          |
|------------------------|----------------------------|----------------|----------------------------------------|
| **Gelato**             | [gelato.com](https://www.gelato.com) | Gratuit (free tier) | Fournisseur POD par défaut             |
| **Prodigi**            | [prodigi.com](https://www.prodigi.com) | Gratuit       | Signature premium fine art             |

## Renseignements à fournir à Gelato et Prodigi (espace pro)

- Country : France
- Business name : nom commercial
- SIRET (14 chiffres)
- VAT number (FR + 11 chiffres) — déclencheur du régime B2B intra-UE
- Adresse de facturation

L'activation du flag *« VAT-registered business »* permet à Gelato de facturer **HT en intra-UE** (mécanisme d'auto-liquidation), simplifiant la comptabilité de la micro en franchise.

## Déclaration côté Etsy

Dans Shop Manager → Settings → Production Partners :

1. **Add a new production partner** → renseigner :
   - Production partner name : *Gelato*
   - About this partnership : 1-2 lignes (ex. *« Gelato produces print-on-demand wall art for our shop in their European network »*).
   - Where they work : *Oslo, Norway* (siège mondial Gelato — pratique recommandée par Gelato pour Etsy[^18]).
2. **Répéter** pour Prodigi : production partner name *Prodigi*, localisation *Leavesden, United Kingdom*.

## Liaison technique Gelato <-> Etsy

- Dans le dashboard Gelato : *Stores → Connect → Etsy*.
- Autoriser OAuth (Etsy redirige sur Gelato avec un token de scope produit/listing).
- Sync produits : 1-5 minutes après la première création de produit côté Gelato.

Prodigi ne dispose pas, à date, d'un connecteur Etsy natif équivalent : la création de listing se fait manuellement sur Etsy puis l'import est déclenché côté Prodigi (limite connue de l'intégration, documentée dans [`benchmark-pod-fournisseurs.md`](benchmark-pod-fournisseurs.md)).

\newpage

# Obligations fiscales post-création à connaître

## OSS — One-Stop Shop (TVA intra-UE)

Au-delà de **10 000 €** de ventes B2C cumulées vers d'autres pays de l'Union européenne (hors France) dans une même année civile, l'inscription au **guichet unique OSS** devient obligatoire[^19].

[^19]: Sources : [Commission européenne — One Stop Shop](https://vat-one-stop-shop.ec.europa.eu/) et [impots.gouv.fr — Guichet unique TVA](https://www.impots.gouv.fr/portail/professionnel/le-guichet-unique-de-tva-oss).

Sous ce seuil : la TVA française s'applique (en franchise pour la micro = pas de TVA à facturer).

Au-dessus du seuil :

- La TVA du pays de l'acheteur s'applique (taux variable : 17 % Luxembourg → 27 % Hongrie).
- Inscription sur [impots.gouv.fr → Espace Professionnel → OSS](https://www.impots.gouv.fr/portail/professionnel).
- Déclaration trimestrielle + paiement unique en France → redistribution automatique vers les autres États membres.
- À noter : **l'OSS s'applique même en franchise de TVA française** dès le franchissement du seuil intra-UE.

**Conséquence opérationnelle** : surveiller le CA UE hors France dès P2-P3, car le franchissement peut intervenir rapidement avec une boutique Etsy fonctionnelle. Probable inscription préventive en P3.

## Plafonds à surveiller

Une vigilance régulière (semestrielle minimum) est requise sur quatre seuils :

| Seuil                                 | Montant 2026     | Conséquence du dépassement                |
|---------------------------------------|------------------|-------------------------------------------|
| Régime micro — vente de biens         | 203 100 €        | Bascule de plein droit au régime réel BIC |
| Franchise TVA — seuil de base         | 85 000 €         | Assujettissement TVA l'année suivante     |
| Franchise TVA — seuil majoré          | 93 500 €         | Assujettissement TVA immédiat (mois suivant) |
| Seuil OSS intra-UE                    | 10 000 €         | Inscription OSS obligatoire               |
| Compte bancaire dédié obligatoire     | 10 000 € pendant 2 ans | Obligation d'un compte séparé        |
| Déclaration DAC7 par Etsy             | 2 000 € ou 30 transactions | Transmission auto aux impôts (neutre) |

## Cotisations sociales et déclaration de CA

- **Fréquence** : trimestrielle (recommandée) ou mensuelle, choix annuel.
- **Taux** : 12,3 % du CA encaissé en vente de biens (6,4 % la 1re année avec ACRE 50 %).
- **CFP** (Contribution à la Formation Professionnelle) : 0,1 % ajouté pour les commerçants.
- **Versement libératoire IR** (si option exercée) : +1 % du CA.
- **Déclaration nulle obligatoire** même si CA = 0 sur la période (sanction 50 €/déclaration manquante).

## Mentions légales obligatoires sur les fiches Etsy et factures

- En franchise de TVA : *« TVA non applicable, article 293 B du CGI »*.
- Mention du SIRET sur toute facture commerciale.
- Adresse complète du vendeur (= adresse INPI déclarée).
- Mention provenance projet *Art* : *« Reproduction issue d'une œuvre du domaine public — sourced by [nom de la boutique] »* (cf. policy interne dans [`process-vente-production.md`](process-vente-production.md) §6).

\newpage

# Calendrier opérationnel détaillé

Hypothèse : démarrage le **lundi J0** ; founder solo à 20 h/semaine.

| Jour      | Action                                                                   | Acteur     | Durée |
|-----------|--------------------------------------------------------------------------|------------|-------|
| **J0**    | Vérification d'antériorité marque INPI + EUIPO                            | Toi         | 2 h   |
| **J0**    | Réservation domaines .com + .fr                                          | Toi         | 30 min|
| **J0**    | Réservation handles Instagram + Pinterest                                | Toi         | 30 min|
| **J1**    | Préparation pièces justificatives (CNI, justif domicile, déclaration honneur) | Toi    | 1 h   |
| **J1**    | Saisie complète du dossier sur procedures.inpi.fr                        | Toi         | 1 h   |
| **J2-3**  | Ouverture compte bancaire pro en ligne (Shine recommandé)                | Toi         | 30 min + validation 1-2 j |
| **J3-J10**| *Attente de l'INSEE pour attribution SIREN/SIRET*                        | INSEE      | 7-15 j calendaires |
| **J3-J9** | (En parallèle) préparation visuelle boutique : logo, bannière, page À propos | Toi      | 3-5 h |
| **J3-J9** | (En parallèle) rédaction politiques boutique (retours, expédition, RGPD) | Toi         | 2 h   |
| **J10**   | Réception SIREN + SIRET par mail INPI/INSEE                              | -          | -     |
| **J10**   | Création espace personnel URSSAF + choix fréquence de déclaration         | Toi         | 30 min|
| **J10**   | Demande d'ACRE si éligible (envoi formulaire URSSAF)                     | Toi         | 30 min|
| **J11**   | Ouverture compte vendeur Etsy + saisie informations légales              | Toi         | 1 h   |
| **J11**   | Configuration boutique (branding, politiques, profils livraison)         | Toi         | 2 h   |
| **J12**   | Création comptes Gelato + Prodigi + saisie informations B2B               | Toi         | 30 min|
| **J12**   | Liaison Gelato <-> Etsy via dashboard Gelato                                | Toi         | 15 min|
| **J12**   | Déclaration production partners Gelato + Prodigi dans Etsy               | Toi         | 30 min|
| **J13**   | **Fin P0 — passage à P1** (échantillon physique + premier listing)        | Toi         | -     |

**Temps de travail effectif** : ~12-15 heures réparties sur 10-13 jours calendaires, soit ~2 semaines pour un founder à 20 h/semaine.

\newpage

# Points d'attention juridiques

## Cumul micro-entreprise et autres statuts

Si le porteur est par ailleurs **salarié**, **fonctionnaire** ou **bénéficiaire d'aides** (chômage, RSA, AAH), des règles spécifiques s'appliquent :

- **Salarié du privé** : possible sans formalité, sauf clause de non-concurrence ou d'exclusivité dans le contrat de travail. Vérifier ces clauses **avant** la déclaration.
- **Fonctionnaire** : autorisation de l'employeur public requise, sauf si l'activité accessoire entre dans la liste autorisée par l'article L. 123-7 du Code général de la fonction publique.
- **Demandeur d'emploi indemnisé** : maintien partiel de l'ARE possible (cumul partiel) ou capitalisation (ARCE = 60 % des droits versés en deux fois). Choix structurant à arbitrer avec France Travail.

## Responsabilité civile professionnelle

Activité non réglementée → assurance RC pro **non obligatoire** pour le code 4791B. Recommandée néanmoins dès que le CA dépasse 10 k€/an (coût ~120-200 €/an pour une micro vente de biens).

## RGPD

Etsy gère la collecte et le traitement des données clients sur sa plateforme. **Aucun fichier client n'est constitué côté vendeur** tant que la communication se fait via la messagerie Etsy. Si le projet déploie ultérieurement une newsletter ou un site propre, une politique RGPD étendue + registre des traitements devra être mis en place.

## Comptabilité minimale à tenir

Sous régime micro :

- **Livre des recettes** : daté, montant, mode de paiement, identité du client (ou « ventes au comptoir » pour les ventes B2C), référence facture.
- **Registre des achats** : uniquement pour activité de vente de biens, obligatoire (article L. 123-28 du Code de commerce).
- **Conservation 10 ans** des justificatifs (factures Gelato, frais Etsy, etc.).

Aucun bilan, aucun compte de résultat, pas de TVA à déclarer en franchise.

\newpage

# Récapitulatif décisionnel

| Question                              | Décision recommandée                            | Conditionnée à |
|---------------------------------------|-------------------------------------------------|----------------|
| Statut juridique                       | Micro-entreprise                                | Décidée        |
| Code APE                               | 4791B                                           | Décidée        |
| Régime fiscal                          | Micro-BIC                                       | Décidée        |
| Régime TVA                             | Franchise en base                               | Décidée        |
| Versement libératoire IR               | OUI si RFR 2024 au plus 29 315 € / part               | À chiffrer     |
| ACRE                                   | OUI si éligibilité ; immatriculer avant 30/06/26 | À vérifier    |
| Dépôt INPI marque                      | Recommandé (190 € pour 1 classe)                | À décider      |
| Compte bancaire pro                    | Shine Start (gratuit)                           | Recommandé     |
| Fréquence déclaration URSSAF           | Trimestrielle                                   | Recommandée    |
| Production partners Etsy               | Gelato + Prodigi déclarés                       | Obligatoire    |
| OSS                                    | À surveiller, inscription en P3                 | Conditionnée   |

\newpage

# Sources et références

## Sources officielles consultées

### Création et statut micro-entreprise

- [INPI — Créer en tant que micro-entrepreneur](https://www.inpi.fr/realiser-demarches/formalites-dentreprises/creer-en-tant-que-micro-entrepreneur)
- [INPI — Guichet unique des formalités d'entreprises](https://www.inpi.fr/decouvrir-inpi/formalites-dentreprises/guichet-unique-formalites-dentreprises-et-registre-national-entreprises)
- [INPI — Portail e-procedures (saisie officielle)](https://procedures.inpi.fr)
- [Service-Public — Guichet des formalités des entreprises](https://entreprendre.service-public.gouv.fr/vosdroits/R61572)
- [Service-Public — Régime fiscal de la micro-entreprise](https://entreprendre.service-public.gouv.fr/vosdroits/F23267)
- [Urssaf Autoentrepreneur — Site officiel](https://www.autoentrepreneur.urssaf.fr)

### Plafonds et fiscalité 2026

- [Urssaf — 2026 : modification des seuils de chiffre d'affaires](https://www.autoentrepreneur.urssaf.fr/portail/accueil/sinformer-sur-le-statut/toutes-les-actualites/2026--modification-des-seuils-de.html)
- [Service-Public — Seuils de chiffre d'affaires de la micro-entreprise](https://entreprendre.service-public.gouv.fr/vosdroits/F32353)
- [impots.gouv.fr — Pour rester micro-entrepreneur](https://www.impots.gouv.fr/professionnel/questions/pour-rester-micro-entrepreneur-quel-montant-de-chiffre-daffaires-ou-de)
- [impots.gouv.fr — Le versement libératoire](https://www.impots.gouv.fr/professionnel/le-versement-liberatoire)
- [Urssaf — Modalités d'adhésion au versement libératoire 2026](https://www.autoentrepreneur.urssaf.fr/portail/accueil/sinformer-sur-le-statut/toutes-les-actualites/modalites-dadhesion-au-verseme-2.html)
- [Service-Public — Franchise en base de TVA](https://entreprendre.service-public.gouv.fr/vosdroits/F21746)
- [economie.gouv.fr — Montant des cotisations sociales micro-entreprise](https://www.economie.gouv.fr/entreprises/gerer-sa-micro-entreprise/micro-entreprises-quel-est-le-montant-de-vos-cotisations-sociales)

### ACRE

- [Service-Public — Aide à la création ou à la reprise d'une entreprise (Acre)](https://entreprendre.service-public.gouv.fr/vosdroits/F11677)

### TVA intra-UE / OSS

- [Commission européenne — VAT One Stop Shop](https://vat-one-stop-shop.ec.europa.eu/)
- [impots.gouv.fr — Guichet unique de TVA (OSS)](https://www.impots.gouv.fr/portail/professionnel/le-guichet-unique-de-tva-oss)

### DAC7

- [impots.gouv.fr — Transfert d'informations DPI-DAC7](https://www.impots.gouv.fr/transfert-dinformations-en-application-des-dispositifs-dpi-dac7-plateformes-deconomie-collaborative)

### Etsy et plateforme

- [Etsy Help — What Are Sales Reporting Requirements for French Sellers?](https://help.etsy.com/hc/en-us/articles/360048262494-What-Are-Sales-Reporting-Requirements-for-French-Sellers)
- [Etsy Help — Am I Required To Add a VAT ID to my Account?](https://help.etsy.com/hc/en-us/articles/360058652054-Am-I-Required-To-Add-a-VAT-ID-to-my-Account)
- [Etsy Help — What Information Does Etsy Report for EU Sellers?](https://help.etsy.com/hc/en-us/articles/17795509361431-What-Information-Does-Etsy-Report-for-EU-Sellers)
- [Etsy Help — How to Update Your Legal Name and Taxpayer Information](https://help.etsy.com/hc/en-us/articles/360000337047-How-to-Update-Your-Legal-Name-and-Taxpayer-Information)

### POD et production partners

- [Gelato Help Center — Do I have to list Gelato as a production partner on Etsy?](https://support.gelato.com/en/articles/8996467-do-i-have-to-list-gelato-as-a-production-partner-on-etsy)
- [Gelato Help Center — How to connect my Etsy store to Gelato?](https://support.gelato.com/en/articles/8996451-how-to-connect-my-etsy-store-to-gelato)
- [Prodigi — Site officiel](https://www.prodigi.com)

### Marque

- [INPI — Protéger votre marque](https://www.inpi.fr/proteger-vos-creations/proteger-votre-marque/les-cles-pour-bien-deposer-votre-marque)
- [data.inpi.fr — Recherche d'antériorité marques](https://data.inpi.fr)
- [EUIPO TMview](https://www.tmdn.org/tmview/)

### Documents internes du projet *Art*

- [`CLAUDE.md`](../CLAUDE.md) — contexte projet et décisions structurantes.
- [`docs/roadmap-mise-en-vente.md`](roadmap-mise-en-vente.md) — planification P0 à P4 détaillée.
- [`docs/process-vente-production.md`](process-vente-production.md) — flow Etsy/Gelato/mockups et coûts unitaires.
- [`docs/benchmark-pod-fournisseurs.md`](benchmark-pod-fournisseurs.md) — comparatif Printful/Gelato/Prodigi, décision hybride.
- [`docs/business-plan.md`](business-plan.md) — modèle économique et thèse commerciale.

## Avertissement

Ce dossier est une synthèse opérationnelle préparée à des fins de planification interne. Il **ne constitue pas un conseil juridique, fiscal ou comptable**. Avant tout dépôt INPI ou validation d'option fiscale structurante (versement libératoire, option TVA, choix d'ACRE), une consultation ponctuelle avec un expert-comptable ou un conseiller URSSAF (gratuit) est recommandée.

Tous les montants, taux et seuils cités sont ceux en vigueur à la date du présent document (24 mai 2026), vérifiés auprès des sources officielles citées. Les réformes fiscales annuelles (notamment la réduction du taux ACRE au 1er juillet 2026) sont susceptibles de modifier les conclusions au-delà de cette date.

---

\vspace{1em}

*Document généré dans le cadre du projet Art — Édition d'art à la demande sur domaine public curé. Version 1 du 24 mai 2026.*
