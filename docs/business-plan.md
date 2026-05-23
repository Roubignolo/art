# Projet POD automatisé — Business plan réaliste & moteur de scoring

*Pipeline : Claude (détection + scoring de tendances) → nanobanana (génération visuelle) → Printful → Amazon / Etsy*

---

## 1. La thèse en une phrase

Sur du print-on-demand basé sur l'actualité, **la rentabilité n'est pas pilotée par le volume de designs produits, mais par le taux de réussite (hit-rate) de la sélection des sujets.** L'automation a donc un seul vrai job : faire passer le hit-rate de ~2 % (production aveugle) à 6-10 % (production guidée par un scoring sérieux). Tout le reste — génération d'images, push Printful — est de la plomberie déjà résolue par les API.

---

## 2. Le moteur de scoring (le cœur du projet)

L'erreur classique est de coder un détecteur de « ce qui est viral ». Un bon sujet POD doit cocher **quatre critères simultanément**. Claude évalue chaque sujet candidat sur ces axes et ne déclenche la production que au-dessus d'un seuil.

### Les 4 axes

| Axe | Poids | Ce qu'on mesure | Sources de données |
|-----|-------|-----------------|--------------------|
| **Momentum** | 30 % | La tendance *monte-t-elle encore* ? Position sur la courbe (début vs pic). Une tendance au pic = trop tard vu le délai Printful. | Google Trends (requêtes en hausse), Reddit/X en montée, vélocité des recherches Etsy/Amazon |
| **Risque PI / juridique** | Gate + 25 % | Marque déposée ? Nom de personnalité ? Personnage protégé ? Paroles de chanson ? Meme sous copyright ? | Recherche USPTO / EUIPO, raisonnement de Claude sur ce qui est protégeable |
| **Traduisibilité visuelle** | 20 % | Le sujet devient-il un design texte/graphique propre et vendable sur tee/mug/poster ? | Évaluation par Claude du concept visuel |
| **Saturation** | 25 % | Combien de vendeurs sont déjà dessus ? Demande montante + offre faible = sweet spot. | Nombre de listings Etsy/Amazon sur le mot-clé, âge des listings, nombre d'avis |

### Règle de décision

1. **Le risque PI est un filtre éliminatoire (gate), pas juste un poids.** Si Claude détecte un risque élevé (marque, personnage, célébrité, paroles), le sujet est **rejeté à 0**, peu importe son momentum. C'est ce qui protège tes comptes vendeurs — le vrai tueur d'activité POD automatisée n'est pas la concurrence, c'est la suspension de compte Amazon/Etsy pour infraction.
2. Les sujets survivants reçoivent un **score pondéré sur 100**.
3. On ne produit qu'au-dessus d'un **seuil** (à calibrer, ex. ≥ 65/100), et on plafonne à N designs/jour pour ne pas noyer le catalogue de SKU faibles.

> C'est précisément la tâche où Claude apporte de la valeur que ne donnent ni un script de scraping ni nanobanana : le raisonnement sur le risque juridique et la qualité du concept. Le scraping te dit *ce qui bouge* ; le scoring décide *ce qui mérite 0,50 € de production*.

---

## 3. Économie unitaire (chiffres 2026, à ajuster avec tes vrais coûts)

### Marge sur UNE vente — exemple t-shirt

| Poste | Montant |
|-------|---------|
| Prix de vente + port encaissés | 30,00 $ |
| Frais Etsy (6,5 % transac + 3 % + 0,25 $ traitement + 0,20 $ listing) | −3,30 $ |
| Base Printful + expédition (blended) | −18,50 $ |
| **Marge nette / vente** | **≈ 8,20 $** |

⚠️ **Seuil Offsite Ads** : au-delà de 10 000 $ de ventes sur 12 mois glissants, Etsy inscrit d'office aux Offsite Ads (15 % sur ventes attribuées, non désactivable). Prévoir −3 à −5 points de marge effective à l'échelle.

### Coût d'un design produit (qu'il vende ou non)

| Poste | Estimation |
|-------|------------|
| Appels Claude (scoring d'un lot de sujets, amorti par design retenu) | ~0,05–0,15 $ |
| Génération nanobanana (avec quelques itérations) | ~0,10–0,25 $ |
| Frais de mise en ligne Etsy (0,20 $, renouvelé tous les 4 mois) | ~0,20 $ + renouvellements |
| **Coût chargé par design listé** | **≈ 0,40–0,60 $** |

C'est ce coût, multiplié par les designs **morts**, qui détermine la viabilité.

---

## 4. Business plan réaliste — 3 scénarios

Hypothèses communes : **1 000 designs produits/mois**, marge nette **8 $/vente**, coût chargé **0,50 $/design listé**, designs « gagnants » = ≥ 3 ventes/mois en moyenne.

| | Pessimiste | Réaliste | Optimiste |
|---|---|---|---|
| Hit-rate (designs qui vendent) | 2 % | 5 % | 8 % |
| Designs gagnants / mois | 20 | 50 | 80 |
| Ventes / mois (≈3 par gagnant) | 60 | 150 | 240 |
| Revenu net ventes (×8 $) | 480 $ | 1 200 $ | 1 920 $ |
| Coût production (1 000 × 0,50 $) | −500 $ | −500 $ | −500 $ |
| Frais fixes (abos, outils, hébergement) | −150 $ | −150 $ | −150 $ |
| **Résultat mensuel** | **≈ −170 $** | **≈ +550 $** | **≈ +1 270 $** |

### Lecture

- **À 2 % de hit-rate, l'automation perd de l'argent** : tu paies la production de 980 SKU morts. C'est exactement le piège de la production aveugle.
- **Le point de bascule se situe autour de 3,5–4 % de hit-rate.** En dessous, ne pas lancer. C'est l'objectif chiffrable du moteur de scoring.
- Le levier n'est pas « produire 5 000 designs » mais « monter le hit-rate ». Doubler le hit-rate vaut bien mieux que doubler le volume (qui double aussi les coûts morts).

---

## 5. Phasage recommandé (éviter de tout coder d'un coup)

**Phase 0 — Valider le scoring AVANT d'automatiser (2-3 semaines).**
Fais tourner le moteur de scoring « à la main » avec Claude sur 50-100 sujets, produis manuellement les 10-15 mieux notés, mesure leur hit-rate réel vs ta production habituelle. Si le scoring ne bat pas ton intuition actuelle, l'automation n'a aucun intérêt. *C'est l'étape la moins chère et la plus décisive.*

**Phase 1 — Automatiser la génération + le push.**
Une fois le scoring validé : Claude score → nanobanana génère → API Printful crée le produit → sync Etsy/Amazon. Garder une **validation humaine sur le gate juridique** au début.

**Phase 2 — Boucle de feedback.**
Réinjecter les ventes réelles dans le scoring : quels axes prédisaient le mieux les gagnants ? Réajuster les poids. C'est là que le système devient un vrai actif.

**Phase 3 — Scale prudent.**
Monter le volume seulement une fois le hit-rate stabilisé > 4 %, en surveillant le seuil Offsite Ads et la santé des comptes vendeurs.

---

## 6. Les 3 risques qui peuvent tout arrêter

1. **Suspension de compte (PI)** — le plus probable et le plus grave. Le gate juridique doit être strict et, au début, supervisé humainement. Deux ans de réputation vendeur ne se rachètent pas.
2. **Politiques contenu IA / volume** — Amazon et Etsy durcissent les règles sur les listings de masse et le contenu généré. Etsy valorise la dimension créateur/fait-main. Produire trop vite peut déclencher des flags qualité.
3. **Hit-rate sous le seuil** — si le scoring ne bat pas le hasard, le modèle est structurellement déficitaire. D'où la Phase 0.

---

## 7. Prochaines étapes concrètes

- [ ] Remplacer les hypothèses du §3-4 par tes vrais chiffres (prix de vente moyen, base Printful par type de produit, ton hit-rate actuel sur 2 ans).
- [ ] Définir le seuil de score et les poids des 4 axes.
- [ ] Lancer la Phase 0 (scoring manuel sur 50-100 sujets).
- [ ] Décider go/no-go automation sur la base du hit-rate observé.

*Document de travail — chiffres à calibrer. Je ne suis pas conseiller juridique ni financier ; le volet PI mérite l'avis d'un spécialiste marques avant de passer à l'échelle.*
