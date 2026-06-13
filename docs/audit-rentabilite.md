# Audit rentabilité — synthèse vérifiée (juin 2026)

> **Origine.** Recherche marché + audit catalogue lancés le 12/06 (workflow
> `art-rentabilite-audit`). Les phases *vérification adversariale* et *synthèse*
> sont mortes sur la limite de session ; elles ont été **reprises et terminées**
> le 13/06 (workflow `art-rentabilite-synthese`, 4 vérificateurs + synthèse).
> Ce document est le livrable manquant : conclusions vérifiées + plan priorisé.
>
> **Règle d'honnêteté tenue :** rien d'inventé. Les coûts Gelato/Prodigi des
> tailles musée ne sont pas publiés → marqués `aConfirmer`, jamais présentés
> comme validés. Les dates DP sont vérifiées (Wikipedia/Wikidata).

## Le constat en une phrase
La rentabilité dépend du **hit-rate de curation**, pas du volume — or le catalogue
est **mono-source Met (60/60)** et **sur-doré (63 %)**, ce qui plafonne l'accroche
déco. Le vrai levier de revenu est la **diversification** (sources + palette +
formats), pas une remise de prix.

---

## 1. Verdicts domaine public / marque par niche (hard rule)

La recherche marché proposait des niches porteuses ; la **vérification a resserré
le gate DP/marque** — c'est elle qui protège la règle dure. Aucune œuvre ne part
en production sans **validation humaine** du gate, même « GO » ci-dessous.

| Niche / artiste | † | Verdict | Raison vérifiée |
|---|---|---|---|
| **Ernst Haeckel** — *Kunstformen der Natur* | 1919 | **GO** | DP US+UE, aucune marque. Cible BHL n°1 (planches naturalistes vives). |
| **John James Audubon** — *Birds of America* | 1851 | **GO** | DP US+UE, aucune marque. Sourcer via BHL/AIC/Cleveland (le Met n'a pas les planches HD). |
| **Hiroshige** — *53 stations du Tōkaidō* | 1858 | **GO** | DP US+UE. Casse le mur doré (bleus/indigos). Exclure kakemono ultra-allongés (ratio). |
| **Kuniyoshi** — ukiyo-e (guerriers/chats) | 1861 | **GO** | DP US+UE, palette vive. |
| **Hokusai** — *36 vues du Fuji* | 1849 | **GO** | DP US+UE, bleus de Prusse. Met + AIC. |
| **Redouté** — *Les Roses* | 1840 | **GO** | DP US+UE. Botanique colorée, antidote au sépia. BHL/Smithsonian/Rijks. |
| **Adolphe Millot** — planches Larousse | 1921 | **CONDITIONNEL** | DP OK, mais **marque éditeur Larousse** à lever (validation humaine) avant prod. |
| **William Morris** — *Strawberry Thief* | 1896 | **≈ NO-GO** | DP OK mais **marque active** (Morris & Co. / Sanderson Design Group). Probablement à écarter. |
| **Roger Broders** — affiches voyage Art déco | 1953 | **CONDITIONNEL** | DP UE depuis 2024, mais **DP US affiche par affiche** (carrière 1922-1932). |
| **Mucha** — Art nouveau | 1939 | **NO-GO** | Mucha Trust fait respecter la PI/marque. |
| **Hilma af Klint** — abstraction | 1944 | **NO-GO** | DP US incertain (œuvres dévoilées post-1980) + Fondation contrôle les droits. |
| **Kawase Hasui** — shin-hanga | 1957 | **NO-GO** | DP UE seulement au 01/01/2028. À revoir alors. |

**Action curation prioritaire :** brancher Hiroshige/Kuniyoshi/Hokusai/Haeckel/
Audubon/Redouté. Ils apportent les bleus/verts/indigos absents (palette actuelle :
38 doré, **4 bleus seulement**, 2 turquoise).

---

## 2. Plan priorisé (impact × effort)

### T1 — Code sûr, réversible, sans décision business *(fait dans ce lot, sauf mention)*

| Action | Statut vérif | Fix |
|---|---|---|
| La grille décidée §5.1 (30×40, A3, 50×70, A2, 61×91) est **invendable** : `pricing.ts:52-58` ne price que A4/A3/A2/toile-40×50 | CONFIRMÉ | `PRODUITS` réécrit sur les 5 tailles (poster + encadré). **Prix = extension prudente de l'échelle actuelle (proposition, arbitrage T3) ; coûts `aConfirmer`** (extrapolés, non publiés par Gelato). |
| **A4 fantôme** : `poster-a4-nu` vendu mais absent de `layout.CATALOGUE` → `planifier()` ne peut pas produire son fichier bordure-intégrée | CONFIRMÉ | Retiré de `PRODUITS`. Conséquence : le prix d'appel « à partir de » remonte (A4 était l'entrée). |
| `plans_variants('gelato')` rend **8** variantes (ajoute 40×50, 30×30, 50×50) là où §5.1 en retient **5** | CONFIRMÉ | Ajout de `variants_offre()` + `GELATO_STANDARD` **sans muter** `plans_variants` (mockup/backfill/tests consomment les 8). Carrés/40×50 restent dispo hors offre Etsy. |
| `calculerMarge()` **diverge** d'economie-gelato.md (reglementaire 0,47 % + SAV sur prix+port) → marges code ≠ doc ; commentaire « aligné sur §4 » faux | CONFIRMÉ | **`pricing.ts` = source de vérité** (c'est lui qui s'exécute en prod via `/api/etsy/publish`). Doc annoté, bloc JSON §4 corrigé. |
| Le doc affiche **« 43 % »** de marge (€ sur le brut mais % sur le prix) — vraies marges encadré ≈ **36-37 %** | CONFIRMÉ | Corrigé dans le doc (bug de communication, pas de calcul). |
| CLAUDE.md cite des frais Etsy **Printful-era** « 3 % + 0,25 $ » | CONFIRMÉ | Remplacé par le réel UE 2026 (6,5 % + ~4 % + 0,30 € + 0,20 €). |
| Ligne `signature` déclarée, **aucun produit** signature | CONFIRMÉ | Laissé en l'état (réintroduction = T3, exige des coûts Prodigi inexistants → ne pas inventer). |

### T2 — Curation / sourcing *(validation humaine du gate DP obligatoire)* — **IMPLÉMENTÉ**

**Fait (code) :**

- **`build_collections.py` multi-source** : dispatch Met/AIC/Cleveland/Smithsonian par
  requête (champ `source`), au lieu de Met seul. Mode ciblé `diversify` (CLI :
  `python scripts/build_collections.py 3 73 diversify`).
- **Garde-fou marque (hard rule, par construction)** : Morris (marque active),
  Mucha, af Klint, Hasui, Broders ne peuvent **jamais** entrer, même si une requête
  les vise.
- **Garde-fou artiste** (sans accents) : la recherche plein-texte large (AIC/Smithsonian
  remonte une céramique sur « Audubon ») est filtrée — seul le bon artiste passe.
- **Déprioriser les 14 œuvres faibles** : flag `curation.deprioritized` (persistant,
  pas suppression) appliqué au catalogue + **cockpit** (carte estompée, badge, tri en fin).
- **Cockpit** : œuvres fraîchement sourcées badgées « ⚠ À VALIDER DP » + **barre
  d'équilibre de palette** (le mur doré devient visible comme signal de curation).
- ⚠️ Tout sourcing produit un **candidat « à valider DP »** ; aucune validation/
  publication automatique — le gate reste **humain**.

**Diversification réelle (11 candidats ajoutés, à valider) + leçons empiriques :**

- **2 Redouté botanique** (vert/olive) = la **seule diversification de palette qui
  marche** avec les connecteurs sans clé. ✅
- **9 ukiyo-e** (Hiroshige/Hokusai/Kuniyoshi) : GO, fidèles, mais le **papier vieilli
  les fait lire « doré »** → ils diversifient le **sujet**, pas la palette (le mur doré
  passe à 66 %). Les bleus attendus (type Grande Vague) sont l'exception, déjà au catalogue.
- **BHL câblé** (clé posée) : **8 planches Haeckel** *Kunstformen der Natur* sourcées
  en HD (3900 px), vérifiées **à l'œil** (Tafel 1 Phaeodaria, 2 Globigerina, 3 Ciliata,
  4 Diatomea… — vraies planches, pas du texte). Olive 4 → 8. Connecteur durci :
  filtre planche **strict** (PageType Illustration/Plate explicite, plus de repli OCR
  qui ramenait les couvertures) + garde-fou **page de garde** (table des matières
  « Inhalts » écartée) + normalisation **« Nom, Prénom » → « Prénom Nom »** (le tagging
  reconnaît enfin les auteurs BHL).
- **Audubon** : le Met l'a mais **< 3000 px** ; BHL n'a **pas** la planche-folio couleur
  tagguée Illustration (que du texte « synopsis ») → Audubon reste à trouver (autre
  source HD). **Haeckel = le vrai gain naturaliste** (très forte demande Etsy).
- Le doré reste à 65 % (métrique « famille » grossière : le papier vieilli compte doré).
  La vraie diversité — sujet (ukiyo-e, Haeckel) + olive/vert (botanique, diatomées) — a
  progressé ; la **barre de palette** du cockpit + le flag « à valider » pilotent la curation humaine.

### T3 — Niveaux de prix & lignes *(décision founder — chiffrée, non publiée)*

Coûts base/port Gelato des tailles musée **non confirmés** (economie-gelato.md ne les
chiffre nulle part). Donc : grille présentée en **sensibilité**, jamais figée tant que
l'API Gelato n'a pas répondu.

- **Grille S/M/L** (convention code, coûts extrapolés = NC) — l'audit place le marché
  premium curé bien au-dessus de nos prix (Dybdahl : 30×40 nu **35 €**, encadré chêne
  30×40 **70 €**, 50×70 encadré **120 €** ; nos encadrés sont 35-45 % sous le marché).
  **Décision founder** : rester en entrée de gamme (traction P0 sans avis clients) vs
  monter (+30-45 % supportés par le marché). Le code livré garde des prix **prudents**.
- **Ligne signature Prodigi** : à lancer après 1-2 ventes standard validées ;
  exige un devis API Prodigi (coûts à obtenir, pas à inventer).

---

## 3. Sources (vérifiées)
Marché : accio.com (top art prints Etsy), eRank trends 2026, marchés Etsy dédiés
(audubon/japanese_woodblock/william_morris/celestial). Prix : thedybdahl.com,
pstrstudio.com, rijksmuseumshop.nl, desenio.fr (relevés live). DP : Wikipedia/Wikidata
par artiste (dates de décès). Repo : `pricing.ts`, `layout.py`, `collection.json`,
`build_collections.py`, `decision-encadrement-tailles.md §5`, `economie-gelato.md`.

*Ni conseil juridique ni fiscal — faire valider DP, marque et prix par des pros avant le scale.*
