# Audit — ratio des œuvres vs cadres Gelato / Prodigi / marché (juin 2026)

> **Question :** a-t-on réglé le problème du ratio hauteur×largeur de nos œuvres
> (ratios « musée » arbitraires) face aux tailles fixes des 2 imprimeurs et aux
> cadres standard du marché ?
>
> **Réponse : oui.** Le moteur ne rogne/déforme jamais (bordure/passe-partout),
> la pénalité de ratio est négligeable, et les 2 trous restants ont été corrigés :
> le 40×50 (4:5) est réintégré à l'offre Gelato, et le **fichier print** prêt à
> uploader est désormais généré. Sources : benchmark web Gelato + Prodigi + cadres
> marché (4 agents, juin 2026) + mesure sur les 79 manifestes réels.

## 1. Le moteur était déjà sain
- **Jamais de crop ni de stretch** (règle dure, testé) — `layout.planifier` choisit
  la taille catalogue la plus proche et comble par une bordure (Gelato, intégrée au
  fichier) ou un passe-partout physique (Prodigi, `fitPrintArea` + mount).
- **Pénalité de ratio négligeable** : sur les 79 œuvres, médiane **0,4 point** de
  bordure en plus vs un match parfait. Les ~25 % de bordure observés sont le
  **passe-partout 8 % volontaire** (fine marge propre), pas un échec de ratio.
- **Gelato ne crope pas par défaut** (laisse du blanc) → notre fichier au ratio exact
  est sûr quoi qu'il arrive.

## 2. Couverture par ratio (benchmark juin 2026)

| Ratio | Gelato | Prodigi | Cadres marché | Verdict |
|---|---|---|---|---|
| **4:5 (1,25)** | ✅ 40×50 poster + framed | ✅ 16×20″ | **Excellent** (IKEA Ribba/Knoppäng 40×50 ; 8×10/16×20″ US) — ratio dominant Etsy | **Était hors offre → corrigé** |
| **3:4 (1,33)** | ✅ 30×40 | ✅ 12×16″ | Excellent (30×40 = Ribba phare) | OK |
| **A/√2 (1,41)** | ✅ A3/A2 | ✅ A4-A2 Hahnemühle | Bon FR/UE, faible US | OK *(50×70 = 5:7=1,40, pas 1,41 — écart ~1 %, ne pas étiqueter « 1,41 »)* |
| **3:2 (1,50)** | ✅ 61×91 (=24×36″, 1,49) | ✅ 8×12/24×36″ | Bon en grand format | OK *(60×90 serait 1,50 pur ; non bloquant)* |
| **1:1 carré** | ✅ 30×30/50×50 | ✅ 12×12″ | OK | Réservé aux œuvres ~carrées (à raison) |

## 3. Ce qui a été corrigé
- **40×50 (4:5) réintégré à l'offre Gelato** (`layout.OFFRE['gelato']` + `pricing.ts`
  + decision §5.1). Mesure : ~22 œuvres de la bande 1,20-1,30 (et 27 sous 1,30)
  passaient en 30×40 (~28-33 % bordure) ; elles ont maintenant le 40×50 (~24-29 %,
  match strict). Bonus : 4:5 = ratio art-print le + vendu sur Etsy **et** ratio des
  vignettes de recherche → gain SEO/conversion. L'exclusion d'origine était un oubli
  (le §3 le donnait pourtant dispo Gelato+Prodigi).
- **Œuvres ~carrées (ratio < 1,12)** : `variants_offre` ajoute désormais les carrés
  pour elles (sinon forcées en 30×40 à ~40 % de bordure).
- **Fichier print prêt à uploader** : `composer_fichier_print(master, fournisseur)`
  (+ CLI `--fichier-print`) — Gelato = œuvre + bordure intégrée au ratio catalogue
  exact ; Prodigi = ratio natif (mat physique). On ne générait avant que des mockups.

## 4. À confirmer avant publication (humain, hors code)
- **🔴 Cadre chêne 40×50 en 4:5** : confirmer au Dashboard Gelato qu'il existe en
  *framed poster* 4:5 (distinct du *framed canvas* 40×50). Si non → garder 40×50 en
  poster non encadré seulement.
- **fitMethod / fillMethod Gelato** : valeurs d'énumération exactes (pages support en
  403). Reco opérationnelle déjà sûre : **livrer le fichier au ratio EXACT bord-à-bord**,
  ne pas dépendre du fitMethod.
- **Coûts Gelato 40×50** réels (base ≠ 30×40) → revérifier la marge vs seuil.

*Ni conseil juridique ni POD officiel — confirmer les tailles/cadres au compte fournisseur avant de figer.*
