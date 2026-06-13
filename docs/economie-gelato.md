# Économie Gelato — modèle recalibré (remplace les hypothèses Printful)

*Recalibrage du modèle économique de Provenance après la décision fournisseur **Gelato par défaut + Prodigi premium** (cf. [`benchmark-pod-fournisseurs.md`](benchmark-pod-fournisseurs.md)). L'ancien `business-plan.md` est calé sur **Printful** (marge ~8 $/vente, seuil hit-rate ~3,5-4 %). Ce document fixe un modèle propre Gelato et liste les chiffres à corriger.*

> **Règle de fiabilité.** Aucun prix Gelato ci-dessous n'est un tarif officiel à la décimale. Ce sont les **fourchettes documentées** dans `benchmark-pod-fournisseurs.md` et `process-vente-production.md`, ramenées à un point médian de travail. Chaque coût base/port porte la mention **`[à confirmer via Gelato API]`**. À recalibrer dès qu'on a un compte Gelato + le catalogue `productUid` réel.
>
> **Sources prix confirmées (mai 2026)** : Gelato+ = **23,99 $/mo (mensuel)** ou **19,99 $/mo en annuel** (239,88 $/an), remise **jusqu'à −25 %** sur produits (−35 % promo jusqu'au 31/12) — [Gelato Help Center, subscription cost](https://support.gelato.com/en/articles/8996313) et [product discounts](https://support.gelato.com/en/articles/8996297). Fourchettes catalogue poster/encadré issues de `benchmark-pod-fournisseurs.md` §1 (recherche octobre 2026, ~50 sources).
>
> ⚠️ **Source de vérité = le code, pas ce doc.** `web/lib/pricing.ts` est ce qui
> s'exécute en prod (`/api/etsy/publish`). Il diverge **volontairement** (sens plus
> prudent) des marges tabulées ci-dessous : il ajoute un **frais réglementaire Etsy
> ~0,47 %** (à confirmer sur la grille FR/UE 2026) et assoit la **provision SAV 5 %
> sur prix+port** (et non sur le prix seul). Écart par produit : −0,26 € (A4) à
> −0,85 € (A2 encadré). De plus, les **« margePct » des tableaux §1/§4 sont la marge
> € rapportée au PRIX, pas au brut** : la vraie marge nette/brut des encadrés est
> **≈ 36-37 %**, pas 43 %. En cas de doute, recalculer avec `calculerMarge()`.
> Tailles musée décidées (30×40, 50×70, 61×91) : voir `pricing.ts` (ce doc ne les
> chiffre pas encore — coûts `aConfirmer`). Plan : [audit-rentabilite.md](audit-rentabilite.md).

---

## 0. Hypothèses transverses

| Paramètre | Valeur retenue | Source / note |
|---|---|---|
| Devise de travail | EUR | Boutique Etsy FR/UE |
| Frais Etsy — transaction | **6,5 %** sur (prix + port) | CLAUDE.md §Économie |
| Frais Etsy — traitement paiement | **~4 % + 0,30 €** (zone UE) | `process-vente-production.md` §8 |
| Frais Etsy — listing | **0,20 €** par variant, renouvelé / 4 mois | amorti ≈ 0,05 €/vente |
| Provision SAV | **5 %** du prix de vente (réclamations/casse) | `process-vente-production.md` §6 (3-5 %, on prend le haut) |
| Insert provenance physique | **0,50 €** / colis (optionnel P1+) | non inclus dans la marge de base ci-dessous ; voir §1.7 |
| TVA | hors périmètre (micro-entreprise, franchise en base) | à valider fiscaliste |

> **Note frais Etsy.** L'ancien `business-plan.md` chiffrait le paiement à « 3 % + 0,25 $ ». Le réel UE 2026 est **~4 % + 0,30 €**. On retient le réel UE. Le « 0,25 $ » Printful-era est obsolète (voir §6).

---

## 1. Économie unitaire Gelato par produit

Méthode pour chaque ligne :
`Encaissement brut = prix + port` → `− Etsy transaction (6,5 % du brut)` → `− Etsy paiement (4 % du brut + 0,30 €)` → `− listing amorti (0,05 €)` → `− base Gelato` → `− port Gelato` → `− provision SAV (5 % du prix)` = **Marge nette**.

Tous les `base Gelato` et `port Gelato` sont **`[à confirmer via Gelato API]`** (médian des fourchettes documentées).

### 1.1 Poster A4 nu — prix 16,90 €

| Poste | Montant |
|---|---|
| Prix de vente | 16,90 € |
| + Port encaissé | +3,50 € |
| **= Encaissement brut** | **20,40 €** |
| − Etsy transaction 6,5 % | −1,33 € |
| − Etsy paiement 4 % + 0,30 € | −1,12 € |
| − Listing amorti | −0,05 € |
| − Base Gelato A4 `[à confirmer]` | −4,50 € |
| − Port Gelato UE `[à confirmer]` | −3,00 € |
| − Provision SAV 5 % | −0,85 € |
| **= Marge nette** | **≈ 9,55 €** (**47 %**) |

### 1.2 Poster A3 nu — prix 24,90 €

| Poste | Montant |
|---|---|
| Prix de vente | 24,90 € |
| + Port encaissé | +3,90 € |
| **= Encaissement brut** | **28,80 €** |
| − Etsy transaction 6,5 % | −1,87 € |
| − Etsy paiement 4 % + 0,30 € | −1,45 € |
| − Listing amorti | −0,05 € |
| − Base Gelato A3 200gsm `[à confirmer]` | −7,50 € |
| − Port Gelato UE `[à confirmer]` | −3,50 € |
| − Provision SAV 5 % | −1,25 € |
| **= Marge nette** | **≈ 13,18 €** (**45 %**) |

> Cohérent avec `process-vente-production.md` §8 (14,13 € à 3 % de SAV ; ici 5 % de SAV = un peu plus prudent).

### 1.3 Poster A2 nu — prix 32,90 €

| Poste | Montant |
|---|---|
| Prix de vente | 32,90 € |
| + Port encaissé | +4,50 € |
| **= Encaissement brut** | **37,40 €** |
| − Etsy transaction 6,5 % | −2,43 € |
| − Etsy paiement 4 % + 0,30 € | −1,80 € |
| − Listing amorti | −0,05 € |
| − Base Gelato A2 (fourchette 8-11 €, médian) `[à confirmer]` | −10,00 € |
| − Port Gelato UE `[à confirmer]` | −4,00 € |
| − Provision SAV 5 % | −1,65 € |
| **= Marge nette** | **≈ 17,47 €** (**53 %**) |

### 1.4 Poster A3 encadré chêne — prix 44,90 €

| Poste | Montant |
|---|---|
| Prix de vente | 44,90 € |
| + Port encaissé | +6,90 € |
| **= Encaissement brut** | **51,80 €** |
| − Etsy transaction 6,5 % | −3,37 € |
| − Etsy paiement 4 % + 0,30 € | −2,37 € |
| − Listing amorti | −0,05 € |
| − Base Gelato A3 encadré chêne `[à confirmer]` | −18,00 € |
| − Port Gelato encadré `[à confirmer]` | −6,50 € |
| − Provision SAV 5 % | −2,25 € |
| **= Marge nette** | **≈ 19,26 €** (**43 %**) |

### 1.5 Poster A2 encadré chêne — prix 67,90 €

| Poste | Montant |
|---|---|
| Prix de vente | 67,90 € |
| + Port encaissé | +9,90 € |
| **= Encaissement brut** | **77,80 €** |
| − Etsy transaction 6,5 % | −5,06 € |
| − Etsy paiement 4 % + 0,30 € | −3,41 € |
| − Listing amorti | −0,05 € |
| − Base Gelato A2 encadré chêne (fourchette 32-40 €, médian) `[à confirmer]` | −28,00 € |
| − Port Gelato encadré (volume) `[à confirmer]` | −8,50 € |
| − Provision SAV 5 % | −3,40 € |
| **= Marge nette** | **≈ 29,38 €** (**43 %**) |

> Cohérent avec `process-vente-production.md` §8 (31,38 € à SAV légèrement plus basse). C'est la **pièce qui porte la rentabilité** : ~2,2× la marge absolue d'un A2 nu, ~1,5× celle d'un A3 encadré.

### 1.6 Toile (canvas standard ~40×50 cm) — prix 54,90 €

| Poste | Montant |
|---|---|
| Prix de vente | 54,90 € |
| + Port encaissé | +7,90 € |
| **= Encaissement brut** | **62,80 €** |
| − Etsy transaction 6,5 % | −4,08 € |
| − Etsy paiement 4 % + 0,30 € | −2,81 € |
| − Listing amorti | −0,05 € |
| − Base Gelato canvas `[à confirmer]` | −22,00 € |
| − Port Gelato canvas (volume) `[à confirmer]` | −7,50 € |
| − Provision SAV 5 % | −2,75 € |
| **= Marge nette** | **≈ 23,61 €** (**43 %**) |

### 1.7 Giftable — mug 11 oz (ou torchon) — prix 18,90 €

| Poste | Montant |
|---|---|
| Prix de vente | 18,90 € |
| + Port encaissé | +4,50 € |
| **= Encaissement brut** | **23,40 €** |
| − Etsy transaction 6,5 % | −1,52 € |
| − Etsy paiement 4 % + 0,30 € | −1,24 € |
| − Listing amorti | −0,05 € |
| − Base Gelato mug `[à confirmer]` | −7,50 € |
| − Port Gelato mug `[à confirmer]` | −4,50 € |
| − Provision SAV 5 % | −0,95 € |
| **= Marge nette** | **≈ 7,64 €** (**40 %**) |

> Le giftable a la **marge absolue la plus faible** et le port le plus pénalisant relativement au prix. À traiter comme produit d'appel / panier secondaire, jamais comme moteur de marge. La casse mug en transit peut dépasser 5 % → surveiller.

### Synthèse marges unitaires

| Produit | Prix | Marge nette € | Marge % | Rôle |
|---|---|---|---|---|
| Poster A4 nu | 16,90 € | ~9,55 € | 47 % | entrée de gamme |
| Poster A3 nu | 24,90 € | ~13,18 € | 45 % | volume |
| Poster A2 nu | 32,90 € | ~17,47 € | 53 % | volume premium |
| A3 encadré chêne | 44,90 € | ~19,26 € | 43 % | **marge** |
| A2 encadré chêne | 67,90 € | ~29,38 € | 43 % | **marge** |
| Toile 40×50 | 54,90 € | ~23,61 € | 43 % | premium |
| Mug / torchon | 18,90 € | ~7,64 € | 40 % | appel |

**Insert provenance** (−0,50 €/colis) : si systématisé en P1+, retrancher 0,50 € de chaque ligne (≈ −2 à −5 points de marge selon le prix). Recommandé sur encadrés/toiles (positionnement), optionnel sur giftables.

---

## 2. Effet Gelato+ (abonnement, −25 % production)

Gelato+ donne **jusqu'à −25 %** sur le coût base produit (la remise ne s'applique **pas** au port ni aux frais Etsy). Tarif confirmé : **19,99 $/mo en annuel** (≈ **18,50 €/mo** au change ~0,92), soit ~**222 €/an**. On raisonne en annuel (le mensuel 23,99 $ est moins pertinent une fois la boutique active).

### Impact sur l'encadré A2 (la pièce-cible)

| Poste | Sans Gelato+ | Avec Gelato+ (−25 % base) |
|---|---|---|
| Base Gelato A2 encadré chêne | −28,00 € | −21,00 € |
| (reste du compte identique) | … | … |
| **Marge nette** | **≈ 29,38 €** | **≈ 36,38 €** |

Gain **+7,00 €/vente** sur l'A2 encadré (+24 % de marge). Sur l'A3 encadré : base 18 € → 13,50 €, gain **+4,50 €/vente**. Sur l'A3 nu : base 7,50 € → 5,625 €, gain **+1,88 €/vente**.

### Seuil de rentabilité de l'abonnement

Coût mensuel amorti ≈ **18,50 €/mo**. Le nombre de ventes/mois pour rentabiliser dépend du mix :

| Si le mois est surtout… | Gain moyen / vente | Ventes/mois pour amortir 18,50 € |
|---|---|---|
| Encadrés A2 | +7,00 € | **~3 ventes** |
| Encadrés A3 | +4,50 € | **~4 ventes** |
| Posters A3 nus | +1,88 € | **~10 ventes** |
| Mix réaliste 60 % encadré / 40 % nu | ≈ +4,40 € | **~5 ventes** |

**Règle opérationnelle :** activer Gelato+ **dès ~4-5 ventes/mois** (cohérent avec « amorti à 3 ventes » de `process-vente-production.md` pour un mois orienté encadrés). En dessous, rester sur le tarif gratuit. La promo −35 % (jusqu'au 31/12) abaisse encore le seuil à ~3 ventes mix.

> Hypothèse change EUR/USD ~0,92 `[à confirmer]`. Le « jusqu'à −25 % » n'est pas uniforme sur tout le catalogue — vérifier produit par produit via l'API une fois le compte ouvert.

---

## 3. Modèle hit-rate recalibré (Gelato)

On reprend la structure des 3 scénarios de `business-plan.md` §4, mais avec :
- **marge Gelato** sur un **mix réaliste 60 % encadré / 40 % nu**,
- coût production des SKU listés inchangé (c'est de la plomberie amont : Claude scoring + restauration + mockup + listing fee).

### Marge moyenne pondérée par vente (mix 60/40)

- 60 % encadré : moyenne (A3 19,26 € + A2 29,38 €)/2 = **24,32 €**
- 40 % nu : moyenne (A4 9,55 € + A3 13,18 € + A2 17,47 €)/3 = **13,40 €**
- **Marge moyenne pondérée = 0,6 × 24,32 + 0,4 × 13,40 ≈ 19,95 €/vente**, arrondi **≈ 20 €/vente** (sans Gelato+).
- Avec Gelato+ : ≈ **24 €/vente** (gain mix ~+4,40 €).

> À comparer aux **8 $ (~7,4 €)** de l'hypothèse Printful du `business-plan.md`. La marge unitaire est **~2,7× plus élevée**.

### Coûts (inchangés, structure amont)

- Coût chargé / design listé : **0,50 €** (scoring Claude + génération/restauration + listing fee amorti) — `business-plan.md` §3.
- Volume de référence : **1 000 designs listés / mois** (hypothèse haute, scale ; en P0-P1 réel c'est 15-50).
- Gagnant = design qui vend, ≈ **3 ventes/mois**.
- Frais fixes mensuels : **~150 €** (outils, hébergement) + **Gelato+ ~18,50 €** dès qu'actif.

### Les 3 scénarios (volume 1 000 designs/mois, marge 20 €/vente sans Gelato+)

| | Pessimiste | Réaliste | Optimiste |
|---|---|---|---|
| Hit-rate | 2 % | 5 % | 8 % |
| Designs gagnants / mois | 20 | 50 | 80 |
| Ventes / mois (×3) | 60 | 150 | 240 |
| Revenu net ventes (×20 €) | 1 200 € | 3 000 € | 4 800 € |
| Coût production (1 000 × 0,50 €) | −500 € | −500 € | −500 € |
| Frais fixes (+ Gelato+) | −168 € | −168 € | −168 € |
| **Résultat mensuel** | **≈ +532 €** | **≈ +2 332 €** | **≈ +4 132 €** |

> À comparer au tableau Printful (`business-plan.md` §4) : pessimiste **−170 $**, réaliste **+550 $**, optimiste **+1 270 $**. Même à 2 % de hit-rate, le modèle Gelato est **positif** là où Printful perdait de l'argent.

### Seuil de viabilité (hit-rate minimal)

Point mort : `revenu = coûts`.
`HR × 1000 × 3 × marge = (1000 × 0,50) + frais_fixes`

**Sans Gelato+** (marge 20 €, fixes 150 €) :
`HR × 3000 × 20 = 500 + 150 = 650` → `HR = 650 / 60 000` = **≈ 1,08 %**.

**Avec Gelato+** (marge 24 €, fixes 168,50 €) :
`HR × 3000 × 24 = 500 + 168,50 = 668,50` → `HR = 668,50 / 72 000` = **≈ 0,93 %**.

| Modèle | Marge/vente | **Seuil hit-rate** |
|---|---|---|
| **Ancien Printful** (`business-plan.md`) | ~8 $ (~7,4 €) | **~3,5-4 %** |
| **Nouveau Gelato — mix 60/40, sans Gelato+** | ~20 € | **~1,1 %** |
| **Nouveau Gelato — mix 60/40, avec Gelato+** | ~24 € | **~0,9-1 %** |

**Baisse du seuil : de ~3,5-4 % à ~1 %, soit une division par ~3 à ~4.** La marge de manœuvre du modèle s'élargit massivement : un scoring médiocre reste viable, et le levier devient le **mix produit** (pousser l'encadré) plutôt que la course au hit-rate.

> Note de prudence : ce seuil ~1 % suppose que le coût « 0,50 €/design » reste vrai à 1 000 designs/mois. En P0-P1 (15-50 listings), les frais fixes dominent et le seuil effectif en % est mécaniquement plus haut — mais sur des volumes où on compte en valeur absolue (couvrir ~170-220 €/mois de fixes), pas en %. Le seuil ~1 % est pertinent **à l'échelle**, pas à l'amorçage.

---

## 4. Paramètres en JSON (réutilisable cockpit / calculateur)

```json
{
  "version": "gelato-2026-05",
  "devise": "EUR",
  "avertissement": "Coûts base et port Gelato = medians de fourchettes documentees, a confirmer via Gelato API.",
  "fraisEtsy": {
    "transactionPct": 0.065,
    "paiementPct": 0.04,
    "paiementFixe": 0.30,
    "listingFee": 0.20,
    "listingAmortiParVente": 0.05,
    "baseCalculFrais": "prix_plus_port",
    "offsiteAds": {
      "seuilDeclencheur": 10000,
      "fenetreMois": 12,
      "tauxSousSeuil": 0.15,
      "tauxAuDessusSeuil": 0.12,
      "capParCommande": 100,
      "desactivable": false
    }
  },
  "hypotheses": {
    "provisionSavPct": 0.05,
    "insertProvenanceParColis": 0.50,
    "insertInclusDansMargeBase": false,
    "changeEurUsd": 0.92,
    "coutChargeParDesignListe": 0.50,
    "ventesParGagnantParMois": 3,
    "fraisFixesMensuels": 150,
    "mixRealiste": { "encadrePct": 0.60, "nuPct": 0.40 },
    "margeMoyennePonderee": 19.95,
    "margeMoyennePondereeGelatoPlus": 24.35
  },
  "gelatoPlus": {
    "coutMensuelAnnuelUsd": 19.99,
    "coutMensuelMensuelUsd": 23.99,
    "coutAnnuelUsd": 239.88,
    "coutMensuelEurApprox": 18.50,
    "remiseBasePct": 0.25,
    "remisePromoPct": 0.35,
    "remiseSurPort": false,
    "seuilRentabiliteVentesMois": 5,
    "source": "https://support.gelato.com/en/articles/8996313"
  },
  "produits": [
    { "id": "poster-a4-nu",        "type": "poster",  "prix": 16.90, "port": 3.50, "coutBase": 4.50,  "portGelato": 3.00, "margeNette": 9.55,  "margePct": 0.47, "aConfirmer": ["coutBase","portGelato"] },
    { "id": "poster-a3-nu",        "type": "poster",  "prix": 24.90, "port": 3.90, "coutBase": 7.50,  "portGelato": 3.50, "margeNette": 13.18, "margePct": 0.45, "aConfirmer": ["coutBase","portGelato"] },
    { "id": "poster-a2-nu",        "type": "poster",  "prix": 32.90, "port": 4.50, "coutBase": 10.00, "portGelato": 4.00, "margeNette": 17.47, "margePct": 0.53, "aConfirmer": ["coutBase","portGelato"] },
    { "id": "encadre-a3-chene",    "type": "framed",  "prix": 44.90, "port": 6.90, "coutBase": 18.00, "portGelato": 6.50, "margeNette": 19.26, "margePct": 0.43, "aConfirmer": ["coutBase","portGelato"] },
    { "id": "encadre-a2-chene",    "type": "framed",  "prix": 67.90, "port": 9.90, "coutBase": 28.00, "portGelato": 8.50, "margeNette": 29.38, "margePct": 0.43, "aConfirmer": ["coutBase","portGelato"] },
    { "id": "toile-40x50",         "type": "canvas",  "prix": 54.90, "port": 7.90, "coutBase": 22.00, "portGelato": 7.50, "margeNette": 23.61, "margePct": 0.43, "aConfirmer": ["coutBase","portGelato"] },
    { "id": "mug-11oz",            "type": "giftable","prix": 18.90, "port": 4.50, "coutBase": 7.50,  "portGelato": 4.50, "margeNette": 7.64,  "margePct": 0.40, "aConfirmer": ["coutBase","portGelato"] }
  ],
  "seuilHitRate": {
    "ancienPrintful": 0.0375,
    "gelatoSansPlus": 0.011,
    "gelatoAvecPlus": 0.0093,
    "formule": "HR = (designs * coutDesign + fraisFixes) / (designs * ventesParGagnant * margeMoyenne)",
    "noteEchelle": "Valide a ~1000 designs/mois. En P0-P1 (15-50 listings) raisonner en valeur absolue, pas en %."
  }
}
```

---

## 5. Seuil Offsite Ads Etsy (10 000 € / 12 mois → 15 % imposé)

**Règle Etsy (inchangée par le choix fournisseur).** Au-delà de **10 000 € de ventes sur 12 mois glissants**, Etsy inscrit la boutique **d'office** aux Offsite Ads, non désactivable : **15 %** de commission sur les ventes attribuées à une pub Etsy (12 % au-dessus du seuil de CA), **capé à 100 $/commande**. Sous le seuil, l'inscription est optionnelle (15 %, désactivable).

### Impact sur la marge effective

L'Offsite Ads ne s'applique **qu'aux ventes attribuées** à une pub (typiquement **10-30 %** des ventes selon catégorie/visibilité), pas à tout le CA. Calcul de l'impact moyen :

`perte_moyenne_par_vente = part_ventes_attribuees × 15 % × (prix + port)`

| Part de ventes attribuées | A2 encadré (77,80 € brut) | A3 nu (28,80 € brut) | Impact marge moyenne (20 €) |
|---|---|---|---|
| 10 % | −1,17 € | −0,43 € | ≈ −0,9 €/vente → **~−4,5 pts** |
| 20 % | −2,33 € | −0,86 € | ≈ −1,8 €/vente → **~−9 pts** |
| 30 % | −3,50 € | −1,30 € | ≈ −2,7 €/vente → **~−13 pts** |

Soit, en ligne avec l'ancienne estimation, **−3 à −9 points de marge effective** à l'échelle (cas central ~10-20 % d'attribution). Sur une marge à 43-53 %, ça reste confortable.

### Recommandation

1. **Sous 10 000 €/an : ne PAS activer les Offsite Ads** (rester sur le tarif désactivable). En P0-P2 on est très en dessous du seuil.
2. **À l'approche du seuil**, modéliser un scénario « post-Offsite Ads » dans le calculateur avec **−1,8 €/vente** (hypothèse 20 % attribution) comme provision prudente.
3. **Le seuil hit-rate post-Offsite reste bas** : marge mix 20 € − 1,8 € = 18,2 € → seuil ≈ 1,2 %. L'Offsite Ads ne change pas la viabilité structurelle.
4. Le cap à 100 $/commande protège les paniers chers (encadrés multiples) — non bloquant à nos prix.

> `[à confirmer]` : la part exacte de ventes attribuées Offsite Ads dépend de la boutique ; à mesurer dans les analytics Etsy une fois du volume réel observé (boucle P4).

---

## 6. Note de réconciliation — chiffres à corriger dans `business-plan.md`

L'actuel `business-plan.md` est **entièrement calé Printful + ancienne thèse « tendances + IA »**. Corrections à appliquer :

| # | Emplacement | Ancien (Printful / obsolète) | Nouveau (Gelato) |
|---|---|---|---|
| 1 | En-tête §pipeline | « Claude → nanobanana → **Printful** → Amazon/Etsy » | « curation DP → restauration → **Gelato (défaut) / Prodigi (premium)** → Etsy » |
| 2 | §3 marge unitaire | exemple **t-shirt** 30 $, base Printful **−18,50 $**, marge **≈ 8,20 $** | exemples **poster/encadré** EUR ; marge moyenne mix **≈ 20 € (≈24 € Gelato+)** |
| 3 | §3 frais Etsy | « 6,5 % + **3 % + 0,25 $** + 0,20 $ » | « 6,5 % + **~4 % + 0,30 €** + 0,20 € » (réel UE 2026) |
| 4 | §3 coût design | nanobanana 0,10-0,25 $ | restauration/upscale + mockup (Dynamic Mockups + Flux Pro Kontext) — total chargé ~0,50 € maintenu |
| 5 | §4 hypothèse marge | **8 $/vente** | **20 €/vente** (mix 60/40), 24 € avec Gelato+ |
| 6 | §4 tableau scénarios | pess. −170 $ / réal. +550 $ / opt. +1 270 $ | pess. **+532 €** / réal. **+2 332 €** / opt. **+4 132 €** |
| 7 | §4 « point de bascule » | « **3,5-4 %** de hit-rate » | « **~1 %** » (sans Gelato+), ~0,9 % avec |
| 8 | §2 axes scoring | « Risque PI », « **Saturation** », « Momentum/Traduisibilité » génériques | aligner sur CLAUDE.md : gates **G1 DP US+UE / G2 marque / G3 source / G4 résolution** + 4 axes pondérés (momentum 0,30 / attribution 0,20 / traduisibilité 0,25 / **concurrence** 0,25) |
| 9 | §1 thèse | « tendances + IA », hit-rate cible 6-10 % | **domaine public curé** ; le levier devient le **mix produit (encadré)**, pas la course au hit-rate |
| 10 | §5-6 phasage/risques | mentions Printful/Amazon, « contenu IA » | Gelato+Prodigi, Etsy seul P0-P1, eBay P2, **écarter Amazon** (cf. `process-vente-production.md` §7) |

**Décision suggérée :** soit réécrire `business-plan.md` en s'appuyant sur ce document comme source de vérité économique, soit y ajouter un bandeau en tête : *« §3-4 obsolètes (Printful) — voir `docs/economie-gelato.md` »*. Le calculateur `finance/calculateur-viabilite.xlsx` (calé sur 8 $/vente) doit être recalibré sur **20 €/vente** et le seuil hit-rate **~1 %** (cf. bloc JSON §4).

---

*Document de travail — chiffres à recalibrer dès l'ouverture du compte Gelato (catalogue `productUid` + tarifs réels + grille port par zone). Ni conseil juridique ni financier ; faire valider DP, marque et fiscalité par des pros avant le scale.*
