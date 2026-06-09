# Décision — encadrement & tailles pour œuvres de ratio « musée »

*Comment imprimer/encadrer FIDÈLEMENT des reproductions de ratio arbitraire sur des
catalogues POD à tailles fixes. Issu de la recherche Gelato/Prodigi (oct. 2026).
Implémenté dans `agents/render/layout.py` + `frames.encadrer(ratio_cible=…)`.*

---

## 1. Le problème

Nos 60 œuvres ont des **ratios arbitraires** (un tableau 1,26:1, un portrait 0,78:1,
une estampe 0,68:1). Or **ni Gelato ni Prodigi ne fabriquent de cadre au ratio exact
de l'œuvre** — les deux travaillent sur un **catalogue de tailles fixes**. Face à un
fichier au mauvais ratio, le POD a trois comportements :

| Comportement | Effet | Verdict |
|---|---|---|
| `fill` / crop (souvent le défaut) | **coupe** l'œuvre | ✗ inacceptable (patrimoine) |
| `stretch` | **déforme** | ✗ amateur |
| `fit` / contain | contient l'œuvre, **bordure** sur le reste | ✓ **seule voie fidèle** |

> Règle dure : **jamais de crop ni de stretch** sur une œuvre. La marge est fournie
> par une **bordure (faux passe-partout) intégrée au fichier** ou par un **passe-partout
> physique**.

## 2. Deux modèles selon le fournisseur

- **Gelato — pas de passe-partout.** Le poster est glissé tel quel derrière un plexi,
  monté par le client. → On **intègre la bordure blanche dans le fichier**, au ratio
  exact d'une taille catalogue. Le fichier matche le produit → aucun crop fournisseur.
- **Prodigi — vrai passe-partout (mat) configurable** (snow white / black / hayseed,
  conservation, sans acide), verre/anti-reflet. → On commande au **ratio natif** en
  **`sizing=fitPrintArea`** + **mount activé** : le mat physique absorbe la marge,
  l'œuvre n'est jamais touchée. C'est le rendu galerie, idéal pour la ligne signature.

## 3. Grille de tailles retenue

(`agents/render/layout.CATALOGUE` — convergence Gelato/Prodigi, ratio = grand/petit)

| Taille (cm) | ≈ pouces | Ratio | Gelato | Prodigi |
|---|---|---|---|---|
| 20×25 | 8×10 | 1,25 | | ✓ |
| 28×36 | 11×14 | 1,27 | | ✓ |
| 30×40 | 12×16 | 1,33 | ✓ | ✓ |
| A3 30×42 | | 1,41 | ✓ | |
| 40×50 | 16×20 | 1,25 | ✓ | ✓ |
| 50×70 | ~20×28 | 1,40 | ✓ | ✓ |
| A2 42×59 | | 1,41 | ✓ | |
| 61×91 | 24×36 | 1,50 | ✓ | ✓ |
| 30×30 / 50×50 | carré | 1,00 | ✓ | ✓ |

Ratios disponibles : **1,0 · 1,25 · 1,27 · 1,33 · 1,40 · 1,41 · 1,50** (+ portrait inverses).

## 4. Logique par œuvre (implémentée)

`layout.planifier(largeur, hauteur, fournisseur)` :
1. **Choisit la taille** dont le ratio est le plus proche de l'œuvre (`meilleure_taille`)
   → bordure minimale et équilibrée. (Le carré est écarté sauf œuvre ~carrée.)
2. **Calcule l'ouverture** au ratio cible contenant l'œuvre + ≥ 8 % de mat par bord
   (`ouverture`) → marges asymétriques exactes, **jamais de crop** (testé).
3. **Recommande le `sizing`** : Prodigi `fitPrintArea`+mount ; Gelato bordure intégrée
   (le fichier au ratio exact → `fillPrintArea` sans risque).
4. `plans_variants` donne un plan par taille offerte (= variantes du listing).

Le mockup encadré (`frames.encadrer(ratio_cible=…)`, via `encadre_sur_mur`) rend ce
**vrai passe-partout** → le visuel Etsy correspond au produit livré (plus de cadre
sur mesure imaginaire).

## 5. Décisions

1. **Ligne standard → Gelato, bordure intégrée au fichier** à la taille catalogue
   choisie (mat ~8-12 %, blanc cassé). Tailles offertes : 30×40, A3, 50×70, A2, 61×91.
2. **Ligne signature → Prodigi, passe-partout physique** + `fitPrintArea`, verre (ou
   anti-reflet), insert provenance. Tailles : 30×40, 40×50, 50×70, 61×91.
3. **Jamais** `fill`-crop ni `stretch` sur une œuvre. Le fichier Gelato porte déjà la
   bordure → `fill` y est inoffensif (ratio identique).
4. **Mat couleur** : blanc cassé (snow white) par défaut, cohérent avec la marque papier.

## 6. À confirmer par mail (cf. [todo-lancement.md](todo-lancement.md) §3.2/§3.3)

- **Gelato** : libellé exact du fallback fit/fill via API ; bornes/pas exacts des posters
  custom ; existe-t-il une option passe-partout ; gabarits safe-area/bleed par produit.
- **Prodigi** : activation du mount + couleur via API ; liste complète des tailles +
  image visible après mat ; profils ICC papier (Photo Rag / German Etching) pour le
  soft-proof.

Tant que ces réponses ne sont pas obtenues, on s'appuie sur la **bordure intégrée au
fichier** (maîtrisée, fournisseur-agnostique) plutôt que sur un comportement fit/fill
POD non confirmé.
