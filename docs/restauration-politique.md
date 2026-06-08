# Politique de restauration — « fidélité d'abord »

*Comment décider s'il faut « restaurer » une œuvre, et comment garantir qu'on ne
trahit jamais le peintre. Doctrine + garde-fou logiciel. Née de l'incident Cézanne
(juin 2026) : notre gray-world délavait le bleu volontaire de la nappe.*

---

## 1. Le principe

**Un master open-access de musée EST déjà une reproduction fidèle.** Il a été
numérisé sous mire colorimétrique + profil ICC, selon les référentiels FADGI /
Metamorfoze. Sa couleur n'est pas un défaut à corriger : c'est la vérité terrain.

> Notre valeur ajoutée n'est pas la « correction des couleurs » — c'est la
> **curation**, la **provenance**, et la **préparation print fidèle** (résolution,
> netteté pour le substrat, conversion sRGB). On vend la confiance, pas un filtre.

Corollaire : toute opération qui **déplace la teinte** (balance des blancs,
autocontraste, « réchauffement »…) est **suspecte par défaut** sur un fichier de
musée. Elle doit être (1) justifiée par un vrai défaut, (2) décidée par un humain,
(3) bornée et **mesurée**.

---

## 2. L'incident Cézanne (l'exemple travaillé)

*Still Life with Apples and a Pot of Primroses*, Paul Cézanne, ca. 1890
([Met 435882](https://www.metmuseum.org/art/collection/search/435882)). Cézanne
**modèle le blanc à la couleur froide** : ses « nappes blanches » sont peintes au
bleu cobalt, outremer et de Prusse — c'est sa signature, pas de la crasse
([Art Institute](https://www.artic.edu/articles/991/cezanne-s-still-lifes-under-the-microscope)).

Notre étape `equilibrer_blancs` (gray-world) supposait « la moyenne d'une image
est grise » et corrigeait l'écart. Sur une toile au parti-pris **froid** (moyenne
RGB `94,8 / 121,2 / 116,0` — rouge le plus bas), elle appliquait `R ×1,13` et
`B ×0,96` → réchauffement, neutralisation. Mesuré sur les 4 premiers masters :

| Œuvre | AVANT (gray-world) | APRÈS (fidèle) |
|---|---|---|
| Van Gogh — Wheat Field | ✗ INFIDÈLE · ΔE **9,6** · dominante **25 %** | ✓ FIDÈLE · ΔE 0,6 · dominante 98 % |
| Manet — Monet Family | ✗ INFIDÈLE · ΔE **13,0** · chroma 72 % · dominante 27 % | ✓ FIDÈLE · ΔE 0,4 · chroma 100 % · dominante 100 % |
| Cézanne — Still Life | ✗ INFIDÈLE · ΔE **8,3** · dominante 23 % | ✓ FIDÈLE · ΔE 0,4 · dominante 100 % |
| Caillebotte — Chrysanthemums | ✗ INFIDÈLE · ΔE **11,1** · chroma 62 % · dominante 28 % | ✓ FIDÈLE · ΔE 0,4 · dominante 100 % |

On effaçait **~75 % du parti-pris chromatique** des peintres. Le visuel « avant /
après » qu'on poussait comme preuve de savoir-faire montrait en réalité une
**dégradation** — incompatible avec une marque dont l'argument est l'honnêteté.

---

## 3. Décider s'il faut restaurer — l'arbre de décision

```
Le fichier vient-il d'une source colorimétriquement gérée
(Met, AIC, Cleveland, Rijks, Smithsonian, NGA… open-access) ?
│
├─ OUI (cas par défaut) ───────────────► PROFIL « FIDELE »
│   La couleur est la vérité terrain. AUCUNE correction de teinte.
│   Seules opérations autorisées (n'altèrent pas la teinte) :
│     • rognage du liseré de scan (fond uni)
│     • débruitage léger préservant les bords
│     • accentuation (unsharp mask)
│     • upscale (Lanczos / Real-ESRGAN)
│
└─ NON : scan d'archive NON calibré, jauni, abîmé ────► PROFIL « ARCHIVE » (opt-in)
    Décision HUMAINE documentée (quel défaut ?). Ajoute une balance des blancs +
    un autocontraste BORNÉS — puis l'audit vérifie qu'on n'a pas sur-corrigé.
```

### Comment reconnaître un VRAI défaut (vs un choix d'artiste)

On ne peut **jamais prouver** « vernis jauni » vs « palette voulue » au seul pixel
(il faudrait l'UV / une coupe stratigraphique, réservés au labo). D'où la règle
musée : **validation humaine**. Signaux indicatifs :

- **Référence neutre dans l'image** (mire, carte grise) : un patch gris doit donner
  `a*≈0, b*≈0`. Un écart y = dominante de chaîne (défaut). Les fichiers musée n'en
  ont en général pas dans le cadrage final → présomption « déjà géré ».
- **Uniformité spatiale** : un jaunissement de vernis est un **voile chaud
  uniforme** (jusque dans les hautes lumières) ; un parti-pris d'artiste est
  **structuré** (la froideur vit dans certaines zones, pas partout).
- **Signature du vernis** : défaut **chaud + assombrissant** (bleus → vert). Une
  froideur n'est jamais un vernis jauni.
- **Métadonnées** : profil ICC + provenance institutionnelle = déjà géré.

### Règles dures (ne jamais contourner)

1. **Jamais de gray-world / balance auto sur la moyenne globale d'une œuvre.**
2. **Ne jamais neutraliser un blanc PEINT** (drapé, nappe = contenu modelé à la
   couleur, pas une mire). Il n'a pas de « neutralité » de référence.
3. **Aucune correction couleur automatique** : le profil « archive » est opt-in
   humain, exactement comme les gates DP/marque.
4. **On ne re-corrige pas un fichier musée déjà géré** — baseline = préparation
   print, pas re-grading.

---

## 4. Le garde-fou logiciel — `agents/render/fidelity.py`

Systématise l'analyse manuelle du Cézanne. Après **chaque** rendu, compare le
master à la source (vérité terrain, recalée sur le même recadrage) et émet un
verdict inscrit au `manifest.json` et surfacé dans le cockpit.

### Métriques (en CIELAB, D65 ; ΔE = CIEDE2000)

- **ΔE moyen / p95 / max** sur une grille de patchs → dérive colorimétrique globale
  et locale (où ça dérive le plus).
- **chroma_ratio** = C\* moyen après / avant → détecte le **délavage** (washout).
- **dominante_ratio** = ‖(ā\*, b̄\*)‖ après / avant → détecte la **neutralisation
  d'une dominante voulue** (signature du gray-world : le nuage a\*/b\* se recentre
  vers le gris).
- **dérive de teinte** (° pondérés par la chroma), **patchs délavés** (compte).

Robustesse au recadrage/redimensionnement : comparaison sur **grille de patchs**
(downscale BOX → moyennes de blocs), original recalé sur la boîte de rognage du
master. Conversion sRGB→Lab et ΔE2000 = formules canoniques (Lindbloom / Sharma),
**vérifiées par `tests/test_fidelity.py`** contre les vecteurs de référence publiés.

### Seuils (ΔE2000), calés sur les budgets des standards de numérisation

| Verdict | Critère |
|---|---|
| **FIDÈLE** | ΔE moyen ≤ 3 · chroma ≥ 93 % · dominante ≥ 88 % |
| **À REVOIR** | ΔE moyen 3–6, ou p95 > 10, ou chroma 85–93 %, ou dominante 80–88 % |
| **INFIDÈLE** | ΔE moyen > 6, ou chroma < 85 %, ou dominante < 80 % |

Ancrage (transposé de la **tolérance de chaîne de capture** à la **dérive
d'édition** : un édit qui dépasse le budget d'une chaîne 3★/Full n'est plus fidèle) :

- **FADGI 3e éd. (2023)**, ΔE2000 : 4★ moyen ~2–3 / max ~6 ; 3★ moyen <3 / p90 ~7.
- **Metamorfoze 2.0 (2025)**, ΔE2000 : Full moyen ≤3–4 / max ≤7–10 ; neutralité
  (balance des blancs) ΔE(ab) ≤ 3.
- Repère perceptuel : ΔE ≈ 1 = seuil de discrimination ; < ~2,5 ≈ non perçu.

Empiriquement, la séparation est nette : masters gray-world **ΔE 8–13** (INFIDÈLE)
vs masters fidélité-d'abord **ΔE 0,4–0,6** (FIDÈLE).

> **Réserves d'honnêteté** (cf. recherche) : les valeurs exactes ISO 19264-1
> (A/B/C) sont sous paywall → non figées ici. Les lignes exactes FADGI 3★ /
> Metamorfoze 2.0 sont à confirmer sur les PDF primaires avant durcissement. Les
> seuils ci-dessus sont défendables, pas gravés.

---

## 5. Gestion couleur & préparation print (ICC) — la « correction » légitime

Il y a UNE correction couleur qui a bien lieu, et c'est l'**inverse** du gray-world :
elle ne change pas l'intention de l'artiste, elle la **transporte fidèlement** vers
l'espace attendu par l'imprimeur. Module `agents/render/couleur.py`.

- **Garantie sRGB (gestion ICC).** Les RIP de Gelato et Prodigi attendent du **sRGB**
  (Gelato : « use sRGB images », « tag with sRGB » ; Prodigi : « work in RGB », ne pas
  embarquer leur profil). `assurer_srgb` lit le profil ICC embarqué ; s'il est ≠ sRGB
  (Adobe RGB, ProPhoto, P3…), conversion **rendu colorimétrique relatif + compensation
  de point noir** (préserve les couleurs en gamut, n'écrête que le hors-gamut sRGB ;
  de toute façon les profils sRGB v2 n'ont qu'une table relative). Nos 4 Met sont déjà
  sRGB → aucune conversion ; mais AIC/Cleveland/Rijks/Europeana peuvent livrer autre
  chose. Sans cette étape, on mésinterpréterait silencieusement un fichier Adobe RGB
  (désaturation). Les fichiers livrés sont **tagués sRGB**.

- **On ne fait PAS le gamut mapping vers le papier.** C'est le **RIP du POD** qui mappe
  vers le profil papier (ne jamais pré-convertir en CMYK ni écrêter soi-même — ce serait
  une double correction). Notre livrable = **sRGB propre, 300 DPI, tagué**.

- **Soft-proof informatif (jamais une correction).** `rapport_gamut` répond à « quelles
  couleurs profondes risquent l'écrêtage print ? ». Avec un profil papier
  (`--profil-papier`, Hahnemühle/Prodigi téléchargeables) → vrai soft-proof ICC
  (aller-retour sRGB→papier→sRGB, ΔE2000, % hors-gamut). Sans profil → pré-écran par
  chroma, marqué approximatif. **Important** (recherche) : un papier **mat** a un gamut
  plus PETIT que le baryté/la toile → les bleus/verts très saturés y seront partiellement
  écrêtés **quel que soit le fichier**. Le levier est donc le **choix du papier**, pas un
  filtre sur l'image. L'aperçu sert à décider (mat vs giclé/baryté) — il ne modifie rien.
  *Best practice* : commander une **épreuve physique** avant de figer un produit (Prodigi
  le recommande explicitement ; le soft-proof écran reste indicatif).

> En résumé : la couleur n'est jamais « améliorée ». Elle est **gérée** (sRGB de
> livraison) pour que le tirage = l'original, et **profilée** (soft-proof) pour informer
> le choix du papier. C'est exactement « matcher les recommandations de l'imprimeur ».

## 6. Conséquence sur la marque (à arbitrer)

Le profil fidèle ne « restaure » plus la couleur → le récit ne peut plus être
« on restaure les couleurs ». Le positionnement honnête et défendable :

> **Curation + provenance documentée + préparation print de qualité galerie,
> fidèle à l'original du musée.** La fidélité *prouvée* (badge ΔE dans le cockpit)
> devient elle-même un argument de confiance.

Copy **reformulée** en conséquence (juin 2026) dans `web/lib/etsy-listing.ts` :
description « préparation print fidèle / gestion colorimétrique, couleurs de
l'artiste intactes » (au lieu de « fichier restauré »), attribution « sélectionnée
et préparée pour l'impression » (au lieu de « restaurée »), matériau « couleur
fidèle » (au lieu de « restauration HD »), galerie sans slot « avant/après ». Le
**brief marque** (`docs/brief-marque.md`) reste à harmoniser au même cadrage.

---

## Sources

- FADGI Technical Guidelines 3rd Ed. (2023) — <https://www.digitizationguidelines.gov/guidelines/FADGI%20Technical%20Guidelines%20for%20Digitizing%20Cultural%20Heritage%20Materials_3rd%20Edition_05092023.pdf>
- Metamorfoze Preservation Imaging Guidelines 2.0 (2025) — <https://www.metamorfoze.nl/sites/default/files/documents/Preservation%20Imaging%20Guidelines%20English%202.0,%20April%202025.pdf>
- DT Heritage — Overview FADGI & Metamorfoze (ΔE) — <https://heritage-digitaltransitions.com/digitization-program-planning/overview-of-fadgi-metamorfoze-guidelines/>
- npj Heritage Science — limites de précision couleur (FADGI strict = ΔE2000 2,0) — <https://www.nature.com/articles/s40494-021-00536-x>
- Sharma, Wu, Dalal (2005), CIEDE2000 (référence + données de test) — <https://www.ece.rochester.edu/~gsharma/ciede2000/>
- Bruce Lindbloom — sRGB↔XYZ↔Lab (constantes ε=216/24389, κ=24389/27) — <http://www.brucelindbloom.com/>
- CHSOS — Color Management for Paintings Documentation — <https://chsopensource.org/color-management-for-paintings-documentation/>
- Stanford psych221 — limites du gray-world — <https://acorn.stanford.edu/psych221/projects/2010/JasonSu/grayworld.html>
- Cézanne, palette (bleu dans les blancs) — <https://www.artic.edu/articles/991/cezanne-s-still-lifes-under-the-microscope>

*Avertissement : ni conseil de conservation professionnelle ni juridique. Faire
valider DP, marque et choix de conservation par des pros avant le scale.*
