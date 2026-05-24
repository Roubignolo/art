# Process vente & production — de la curation au colis livré

*Document opérationnel : à quoi ressemble concrètement la boutique, comment une œuvre devient un produit en ligne, comment une vente Etsy déclenche la fabrication et l'expédition, et ce qu'on voit aux différentes étapes.*

> Audience : le founder solo qui a déjà la stratégie et l'outillage (cockpit + sourcing + scoring + marketing multilingue) et veut maintenant comprendre **le reste de la chaîne** avant de l'implémenter.

---

## Sommaire

1. [Vue d'ensemble — le flow en 1 schéma](#1-vue-densemble)
2. [À quoi ressemble la vitrine](#2-vitrine)
3. [À quoi ressemble une fiche produit](#3-fiche-produit)
4. [Les mockups de mise en situation](#4-mockups)
5. [Tunnel technique : vente → fabrication → expédition](#5-tunnel-technique)
6. [Service client & SAV](#6-sav)
7. [Multi-canal : Amazon Handmade et eBay](#7-multi-canal)
8. [Coûts réels par vente (et impact sur le hit-rate)](#8-couts)

---

<a name="1-vue-densemble"></a>
## 1. Vue d'ensemble — le flow en 1 schéma

```
   ┌────────────────────────────────────────────────────────────────────┐
   │                  PIPELINE EN AMONT (déjà fait, cockpit)             │
   ├────────────────────────────────────────────────────────────────────┤
   │ Sourcing  →  Gates DP/marque  →  Scoring 4 axes  →  Marketing 5 lg │
   │ (Met,       (validation         (heuristic ou      (Wikidata +      │
   │  Rijks,      humaine sur         Claude API,         Claude pour    │
   │  BHL)        REVIEW)             produit cible)      desc + tags)   │
   └─────────────────────────┬──────────────────────────────────────────┘
                             │  status: gate → score → restore → publish
                             ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │                   ÉTAPE 5 — PUBLICATION  (à construire)             │
   ├────────────────────────────────────────────────────────────────────┤
   │  Restauration HD (upscale)  →  Génération mockups  →  Push Etsy    │
   │   (nanobanana, Topaz,           (Gelato Studio +       (API listing  │
   │    Real-ESRGAN selon            mockups IA lifestyle    Etsy v3 +    │
   │    coût/qualité)                pour mise en scène)     variants)    │
   └─────────────────────────┬──────────────────────────────────────────┘
                             │  listing live sur Etsy
                             ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │            ÉTAPE 6 — VENTE & FULFILLMENT (90% géré par Gelato)      │
   ├────────────────────────────────────────────────────────────────────┤
   │  Client achète sur Etsy  →  Notif vente (Etsy → webhook ou poll)   │
   │           ↓                                                          │
   │  Cockpit (ou intégration Gelato↔Etsy) crée la commande Gelato      │
   │           ↓                                                          │
   │  Gelato imprime (UE pour clients UE, US pour clients US)           │
   │           ↓                                                          │
   │  Gelato expédie + envoie le tracking à Etsy (visible au client)    │
   │           ↓                                                          │
   │  Client reçoit son colis (3-7 jours UE, 5-10 jours US)             │
   └─────────────────────────┬──────────────────────────────────────────┘
                             │  ventes loggées dans la table Sale
                             ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │              ÉTAPE 7 — BOUCLE DE FEEDBACK (à construire)            │
   ├────────────────────────────────────────────────────────────────────┤
   │  Analytics ventes  →  réajustement des poids du scoring  →  redirection │
   │  sourcing vers les territoires esthétiques qui convertissent       │
   └────────────────────────────────────────────────────────────────────┘
```

Les étapes 1-4 (sourcing, gates, scoring, marketing multilingue) sont **déjà livrées** dans le cockpit (cf. CLAUDE.md). Le présent document décrit le reste : étapes 5 (publication), 6 (vente/fulfillment) et 7 (boucle de feedback).

---

<a name="2-vitrine"></a>
## 2. À quoi ressemble la vitrine Etsy (concept "Provenance")

Cohérent avec le concept de marque B retenu dans [`brief-marque.md`](brief-marque.md) — la **transparence radicale sur l'origine** est la signature.

### Header de la boutique

```
┌──────────────────────────────────────────────────────────────────────┐
│  [Bannière 1200×300 : photo discrète d'un atelier de restauration   │
│   ou détail haute résolution d'une planche botanique]                 │
│                                                                       │
│                              PROVENANCE                               │
│             Archives restaurées · Origine documentée                  │
│                                                                       │
│  ✦ Tirages d'art sourcés des grandes collections muséales (CC0)     │
│  ✦ Restauration manuelle · Fiche provenance pour chaque pièce        │
│  ✦ Imprimé à la demande dans l'UE · 100% domaine public              │
└──────────────────────────────────────────────────────────────────────┘
```

### Page "À propos" — clé du positionnement

3 paragraphes, ton érudit et chaleureux (cf. brief-marque §4) :
1. **Pourquoi** : pourquoi Provenance existe (l'art mural mérite mieux que des scans flous revendus anonymement)
2. **Comment** : la procédure (sourcing institutions CC0, restauration, documentation de l'origine)
3. **Qui** : présentation rapide du founder, photo

### Organisation par collections

Pas de catalogue fourre-tout. **3 à 5 collections thématiques** maximum :

- **Herbiers** — planches botaniques Met / BHL / Redouté
- **Cabinets de curiosités** — coquillages, papillons, anatomie vintage
- **Cartes anciennes** — atlas, cartes célestes
- **Estampes japonaises** — ukiyo-e Hokusai, Hiroshige (DP confirmé)
- **Maîtres hollandais** — Rijksmuseum (paysages, natures mortes)

Chaque collection a sa **page Etsy "Section"** avec sa propre description courte (3-4 lignes) qui pose le contexte historique.

---

<a name="3-fiche-produit"></a>
## 3. À quoi ressemble une fiche produit

Exemple complet avec **Van Gogh — Irises** (Met 436528, déjà importé dans le cockpit) :

### Titre Etsy (listingTitle, version FR)

```
Les Iris de Van Gogh — Affiche d'art encadrée, reproduction muséale
domaine public, déco salon florale Saint-Rémy 1890
```

130 caractères, contient le titre officiel (Wikidata), le type produit ("Affiche d'art encadrée"), l'esthétique ("florale"), le lieu/date pour le SEO long-tail ("Saint-Rémy 1890"). Généré par `/api/marketing` (cf. `web/app/api/marketing/route.ts`).

### Galerie d'images (10 max sur Etsy)

```
┌─────────────────────────────────────────────────────────────────┐
│  1. PRODUIT PUR sur fond neutre                                   │
│     → Mockup Gelato : poster encadré noir, vue de face, fond beige │
├─────────────────────────────────────────────────────────────────┤
│  2. LIFESTYLE 1 — au-dessus d'un canapé                          │
│     → Mockup IA : salon scandinave, lumière du jour, l'œuvre      │
│       encadrée centrée sur le mur                                  │
├─────────────────────────────────────────────────────────────────┤
│  3. LIFESTYLE 2 — dans une chambre                                │
│     → Mockup IA : chambre tons pastel, table de chevet visible    │
├─────────────────────────────────────────────────────────────────┤
│  4. LIFESTYLE 3 — bureau / espace créatif                        │
│     → Mockup IA : bureau, livres, plantes, l'œuvre en arrière-plan│
├─────────────────────────────────────────────────────────────────┤
│  5. DÉTAIL — gros plan sur la texture des fleurs (zoom 1:1)       │
│     → Crop direct du master HD restauré                            │
├─────────────────────────────────────────────────────────────────┤
│  6. PROVENANCE — la fiche musée                                   │
│     → Image composite : œuvre + texte                              │
│       "Vincent van Gogh, 1890 — Metropolitan Museum of Art"       │
├─────────────────────────────────────────────────────────────────┤
│  7. TAILLES — comparatif visuel sur mur                          │
│     → Schéma : A2, A3, 50×70 cm avec silhouette humaine            │
├─────────────────────────────────────────────────────────────────┤
│  8. ENCADRÉS — les 3 options de cadre (noir, naturel, blanc)      │
└─────────────────────────────────────────────────────────────────┘
```

### Description (ton premium, ~500 mots structurés)

```markdown
**Les Iris — Vincent van Gogh, Saint-Rémy-de-Provence, mai 1890**

Une des dernières œuvres peintes par Van Gogh à l'asile de Saint-Paul-de-Mausole,
quelques semaines avant sa mort. Le bleu profond, l'ocre, le vert presque acide
— le souffle d'un artiste qui voit le monde comme personne d'autre.

✦ Reproduction haute fidélité du master numérique en accès libre (CC0)
  du Metropolitan Museum of Art (New York).
✦ Restauration colorimétrique manuelle pour rendre justice aux nuances
  originales — densité maximale du noir, fidélité du bleu de Prusse.
✦ Imprimée à la demande en Europe sur papier d'art mat 200 g/m²,
  encres pigmentaires longue durée.

**Provenance**
Œuvre originale : huile sur toile, 73,7 × 92,1 cm
Conservée au Metropolitan Museum of Art, New York (don d'Adele R. Levy, 1958)
Numéro d'accession : 58.187 · Source : https://www.metmuseum.org/art/collection/search/436528

**Spécifications**
• Format au choix : A3 (29,7×42 cm) · A2 (42×59,4 cm) · 50×70 cm
• Encadrement optionnel : noir, bois naturel, blanc
• Papier d'art mat 200 g/m², encres pigmentaires longue durée
• Fabrication & expédition par Gelato (Europe → 3-5 jours · US → 7-10 jours)

**Expédition**
Imprimé dans le pays le plus proche du client (UE/UK/US/CA/AU).
Tracking systématique. Emballage tube renforcé pour les non-encadrés.

---

Cette pièce n'est pas une œuvre créée par moi.
Elle est *sourcée* d'une collection muséale en domaine public, restaurée et
réimprimée avec soin. Mon travail : trouver, restaurer, raconter.
```

⚠️ Note importante : le dernier paragraphe est la **mention "sourced by"** obligatoire selon les Creative Standards d'Etsy pour le print-on-demand (cf. brief-marque §3 et CLAUDE.md règles dures).

### Tags Etsy (13 max, optimisés SEO)

Générés automatiquement par `/api/marketing` dans chaque langue. Pour Van Gogh Irises en français :
```
van gogh, iris, affiche art, reproduction musee, domaine public,
poster floral, deco salon, encadre, peinture impressionniste,
saint remy, mai 1890, art mural, cadeau amateur art
```

### Prix et variants

```
Format         | Prix base Gelato | Marge | Prix Etsy
─────────────────────────────────────────────────────
A3 nu          |    7,50 €        | x3.3  |  24,90 €
A2 nu          |   11,00 €        | x3.0  |  32,90 €
50×70 nu       |   12,50 €        | x3.2  |  39,90 €
A3 encadré N   |   18,00 €        | x2.5  |  44,90 €
A2 encadré N   |   28,00 €        | x2.4  |  67,90 €
```

*(Prix indicatifs — à recalibrer avec les vraies grilles Gelato — cf. agent recherche)*

### Frais de port

- **UE** : port gratuit absorbé dans le prix (Gelato imprime localement → port court)
- **Hors UE** : port calculé selon zone par Etsy/Gelato

---

<a name="4-mockups"></a>
## 4. Les mockups de mise en situation

### Pourquoi c'est un sujet à part entière

Sur Etsy, **~80% des vendeurs POD utilisent les mêmes scènes Placeit/Gelato** (templates massivement utilisés). Pour un positionnement "curation premium domaine public", ça nuit directement à la différenciation : ton acheteur cible voit les mêmes mises en scène chez 20 boutiques. Le mockup n'est pas qu'un visuel, c'est **un signal de marque**.

### Workflow recommandé : hybride 2 étages, 6 mockups par œuvre

**Étage 1 — Base produit (3 templates) via [Dynamic Mockups Pro](https://dynamicmockups.com/pricing/) ($15/mo, API propre, intégration Etsy native)** :

- **Image 1** : poster nu isolé fond neutre — la vignette principale de la grille Etsy (la 1re image vue dans les résultats de recherche)
- **Image 2** : cadre en gros plan, détail texture — met en valeur la qualité de restauration
- **Image 3** : scène neutre d'intérieur (canapé beige, mur clair) — référence visuelle dimensionnelle

Coût : ~3 × $0,05 = **$0,15 par œuvre**, batchable en script via API.

**Étage 2 — Hero shots premium (3 mockups IA) via [Flux Pro Kontext sur fal.ai](https://fal.ai/models/fal-ai/flux-pro/kontext) ($0,05/image) + compositing Python** :

- **Image 4** : scène **contextuelle pertinente à l'œuvre** :
  - marine du Met → salon bord de mer
  - botanique BHL → véranda lumineuse, plantes vraies
  - estampe japonaise → intérieur wabi-sabi
- **Image 5** : scène "ambiance scandinave / japandi" — matche le persona Etsy haut de gamme déco
- **Image 6** : scène contextuelle alternative (ex. bureau créatif pour les cartes, chambre pastel pour les florales)

Coût : ~3 × $0,08 = **$0,24 par œuvre**.

**Total budget : ~$0,40 par œuvre × 50 œuvres = $20 one-shot + $15/mo Dynamic Mockups + $10-20/mo crédits fal.ai.**

### Technique : compositing pour préserver la fidélité de l'œuvre

La voie propre pour insérer une œuvre dans une scène IA **sans la dégrader** :

1. Génération de la scène vide avec un masque/cadre via Flux Pro Kontext + ControlNet (depth/canny)
2. Collage de l'œuvre HD dans le cadre via Python/PIL :
   - perspective warp pour matcher l'angle du cadre
   - ré-éclairage léger (multiply + grain) pour fondre dans la scène
   - sharpening pour préserver la texture restaurée

C'est exactement la technique de [Prodigi AI Mockups](https://www.prodigi.com/blog/ai-mockup-generator/) en interne : *"the real power is the work we do before using the AI model"* — pré-render produit + AI scène derrière.

### Outils écartés et pourquoi

- **Gelato+ Mockup Studio** ($19,99/mo) : scènes vues partout chez les vendeurs Gelato, anti-thèse du positionnement. À garder pour usage interne uniquement si on souscrit Gelato+ pour les remises produit.
- **Placeit** : ~799 templates wall art mais saturation Etsy massive
- **Smartmockups** : **API fermée depuis sept. 2024** après acquisition Canva → pas d'automatisation possible
- **Prodigi AI Mockups** : excellent mais lock-in fournisseur, contredit la décision Gelato par défaut
- **Midjourney** : pas d'API officielle propre pour contrôler l'image source

### À construire dans le cockpit

Une route `/api/mockup` qui prend `{ workId, scene: "scandinavian|maritime|botanical|...", product: "framed-a3|canvas-30x40|..." }` et :

1. Récupère l'œuvre HD depuis la DB
2. Appelle Dynamic Mockups (3 templates de base) OU Flux Pro Kontext + compositing Python (3 lifestyle)
3. Stocke les 6 URLs dans `Work.mockups` (nouveau champ Json)
4. Bouton "Générer les 6 mockups" dans la fiche œuvre du cockpit

Sources : [Dynamic Mockups](https://dynamicmockups.com/integrations/etsy/), [Flux Pro Kontext](https://fal.ai/models/fal-ai/flux-pro/kontext), [Prodigi AI Mockups](https://www.prodigi.com/blog/ai-mockup-generator/), [comparatif wall art mockups 2026 — Mockey](https://mockey.ai/blog/best-wall-art-mockup-generator/).

---

<a name="5-tunnel-technique"></a>
## 5. Tunnel technique : vente → fabrication → expédition

### Deux options réelles en 2026

**Option A — Connecteur natif Gelato↔Etsy (recommandé Phase 0-1, zéro code)**

Tu lies ton shop Etsy dans le dashboard Gelato. Ensuite :
1. Tu crées le produit côté Gelato (catalogue, prix, mockups) → Gelato pousse automatiquement le listing sur Etsy avec ses mockups
2. Client achète sur Etsy → notification interne Gelato (pas de webhook côté toi)
3. Gelato **route vers le print provider le plus proche du client** (technologie "Velocity Switch" — UE vers usine UE, US vers usine US)
4. Production 1-3 jours ouvrés
5. Expédition + tracking renvoyé automatiquement à Etsy → mail au client
6. Tu ne touches à rien.

Avec une option **"approval auto ou manuel" paramétrable** — pratique en Phase 0 pour faire du QC humain avant que l'usine n'imprime.

**Option B — API pure (Phase 2+ quand on veut du contrôle fin)**

Le flow technique précis :

```
┌──────────────────────────────────────────────────────────────────────┐
│ 1. Client achète sur Etsy                                             │
│    └─→ Etsy déclenche webhook `order.paid`                            │
│        - POST sur ton endpoint (signature HMAC-SHA256 à valider)      │
│        - Payload : { event_type, resource_url, shop_id }              │
├──────────────────────────────────────────────────────────────────────┤
│ 2. Cockpit reçoit le webhook (/api/etsy/webhook)                      │
│    └─→ GET resource_url (Etsy v3) pour récupérer la receipt complète  │
│        - line items : SKU, quantité, address, montant                  │
├──────────────────────────────────────────────────────────────────────┤
│ 3. Cockpit fait le mapping :                                          │
│    SKU Etsy `sku-met-436528-a2-oak`                                   │
│      → workId 436528 en DB → image_url master HD                     │
│      → productUid Gelato `framed_poster_pf_a2_pt_..._cl_4-0`          │
├──────────────────────────────────────────────────────────────────────┤
│ 4. POST https://order.gelatoapis.com/v4/orders                        │
│    Header X-API-KEY                                                    │
│    Body :                                                              │
│    {                                                                   │
│      "orderType": "order",                                             │
│      "orderReferenceId": "etsy-receipt-12345",                         │
│      "customerReferenceId": "etsy-buyer-678",                          │
│      "currency": "EUR",                                                │
│      "items": [{ productUid, files: [{url}], quantity }],             │
│      "shipmentMethodUid": "normal",                                    │
│      "shippingAddress": { ... }                                        │
│    }                                                                   │
├──────────────────────────────────────────────────────────────────────┤
│ 5. Gelato imprime (1-3 j ouvrés). Webhooks vers /api/gelato/webhook : │
│    - order_status_updated   created → in_production → shipped         │
│    - order_item_tracking_code_updated (tracking_code + url)           │
├──────────────────────────────────────────────────────────────────────┤
│ 6. À l'événement `shipped`, cockpit POST                              │
│    https://openapi.etsy.com/v3/application/shops/{shop_id}/receipts/  │
│      {receipt_id}/tracking                                             │
│    avec tracking_code + carrier → mail auto Etsy au client            │
├──────────────────────────────────────────────────────────────────────┤
│ 7. Client reçoit le colis (UE 3-6 j, FR 2-4 j depuis Espagne/Allemagne, │
│    US 4-8 j). Packaging neutre par défaut (option packing slip brandé)│
└──────────────────────────────────────────────────────────────────────┘
```

### Pour démarrer (1re vente) : Option A

Ça fait gagner des semaines de dev. Bascule vers Option B quand tu auras besoin de :
- Sélection master selon variant (différents crops pour A3 vs canvas square)
- Stratégie multi-fournisseur (Gelato pour standard, Prodigi pour premium)
- Batching de commandes
- Détection de fraude / vérification pré-print

### Détails techniques importants

**Etsy API v3 — quotas & auth**
- OAuth2 PKCE, scopes `listings_r/w/d`, `transactions_r`, `shops_r`
- 10 req/s, **10 000 req/jour** par clé app (augmentation sur demande à developer@etsy.com)
- 429 + header `retry-after` au dépassement

**Etsy Webhooks** (GA depuis 2025 — important, ça change le design)
- 4 événements : `order.paid`, `order.canceled`, `order.shipped`, `order.delivered`
- Signature HMAC-SHA256 avec clé `whsec_…` (base64-decodée)
- **Plus besoin de poller** — switch direct sur webhook

**Etsy listings — limites à connaître**
- 10 images max par listing, recommandé 2000 px côté court, ratio 4:5
- Titre 140 caractères max, 13 tags de 20 caractères max
- **70 combinaisons de variants max par produit** (largement suffisant : 4 tailles × 3 cadres = 12)
- **Listing fee `0,20 $` s'applique PAR variant** : 12 variants × 0,20 = 2,40 $ par œuvre, renouvelé tous les 4 mois si non vendu

**Gelato API**
- Base URL `https://order.gelatoapis.com/v4/orders`, header `X-API-KEY`
- Fichiers print : JPEG/PNG/SVG/PDF (PDF/X préféré), **sRGB**, 150 DPI minimum, 300 idéal
- Statuts order : `created` → `passed_to_print_provider` → `in_production` → `shipped` → `delivered`
- Mapping SKU → productUid via le catalogue (un uid par variation, format `poster_product_pf_a2_pt_170-gsm-coated-silk_cl_4-0`)

**Gelato+ subscription** ($19,99/mo annuel)
- Jusqu'à **-25 % sur les produits** (-35 % en promo jusqu'à fév. 2026)
- Mockups premium
- Discount shipping
- À activer dès qu'on dépasse ~15-20 ventes/mois

### Obligation Etsy à ne pas oublier

Le **production partner** (Gelato) doit être déclaré dans Etsy :
**Shop Manager → Settings → Production Partners → Add Gelato**. Sinon risque de suspension du shop. Cf. [Etsy Creativity Standards](https://www.etsy.com/legal/creativity/).

Sources : [Etsy API v3 Auth](https://developer.etsy.com/documentation/essentials/authentication/), [Etsy Rate Limits](https://developers.etsy.com/documentation/essentials/rate-limits/), [Etsy Webhooks GA](https://github.com/etsy/open-api/discussions/1509), [Gelato API v4 Create Order](https://dashboard.gelato.com/docs/orders/v4/create/), [Gelato Webhooks](https://dashboard.gelato.com/docs/webhooks/), [Gelato + Etsy fulfillment](https://www.gelato.com/blog/etsy-fulfillment).

---

<a name="6-sav"></a>
## 6. Service client & SAV

### Qui répond aux clients ? **Toi**.

Gelato fait du **B2B uniquement** — support marchand 24/7 mais **zéro contact avec le client final**. Tout litige passe par toi :

| Situation              | Qui agit                                                                |
|------------------------|-------------------------------------------------------------------------|
| Question avant achat   | Toi sur Etsy (messages Etsy)                                            |
| "Où est ma commande ?" | Toi → tu réponds avec le tracking déjà transmis par Gelato              |
| Colis perdu            | Toi → ouvre un ticket Gelato → ils réimpriment/refund → tu rembourses Etsy |
| Qualité défectueuse    | Toi → photo client → ticket Gelato → réimpression                       |
| Demande de retour      | Toi, selon ta `return_policy` Etsy (recommandé : retour sous 14j si défaut) |
| Avis 1 étoile          | Toi → réponse publique mesurée + offre privée                            |

### Politique de retour à mettre dans Etsy

Vue la nature POD : pas de retour pour "j'ai changé d'avis" (impossible de revendre une pièce imprimée). Acceptés :
- Défaut d'impression → réimpression gratuite (Gelato refait)
- Colis perdu / endommagé → renvoi
- Erreur de format/cadre (faute marchand) → réimpression
- Délais dépassés (15+ jours UE, 25+ jours US) → refund partiel

### Provisionner dans la marge

Compter **~3-5 % des commandes en réclamation** sur du poster encadré (le plus fragile à l'expédition). Sur une marge nette de 8-10 €/vente, c'est ~0,30 € de "casse" à intégrer dans le pricing.

### Templates de réponse à préparer

À écrire en FR + EN avant le 1er listing (sera utilisé fréquemment dès la 1re vente) :
- "Production en cours" (J+1 après achat)
- "Expédié, voici le tracking" (auto via webhook mais doublé d'un mot personnel)
- "Désolé pour le délai" (J+10 sans tracking)
- "Photo du défaut svp" (demande d'élément)
- "Réimpression en cours" (suite à défaut)
- Réponse publique à un avis 1-3 étoiles (calme, factuelle, offre de réimpression en privé)

Le ton doit matcher la marque "Provenance" : érudit, soigné, jamais en mode service client industriel.

---

<a name="7-multi-canal"></a>
## 7. Multi-canal : Amazon Handmade et eBay

### TL;DR — Etsy seul en Phase 0-1, eBay en Phase 2, oublier Amazon

| Critère                  | Etsy             | Amazon Handmade        | eBay              |
|--------------------------|------------------|------------------------|-------------------|
| Public                   | Déco/cadeau, curation premium | Généraliste, prix-sensible | Collection, chasse |
| Frais effectifs          | **~12-13 %**     | 15 %                   | 15 % + 0,30-0,40 $ |
| Conformité DP reproductions | OK avec attribution "sourced by" | **Zone grise** (refus fréquents) | **OK explicite** |
| Intégration Gelato       | Native           | Native (Amazon US seulement) | Native           |
| Effort d'onboarding      | Faible           | **Élevé** (candidature artisan, refus possible) | Faible      |
| Risque suspension        | Modéré           | **Élevé** (reclassement non-handmade) | Faible        |

### Amazon Handmade — zone grise défavorable

Amazon Handmade exige une candidature artisan validée et 5 catégories acceptées (`hand-altered`, `hand-designed`, `handcrafted`, `repurposed`, `upcycled`). Le **POD pur via Gelato/Printful** (impression automatisée) est généralement considéré comme *mass-produced* et donc non conforme. Des vendeurs POD passent toutefois la validation en *hand-altered* ou *hand-designed* sur poster/toile, mais les refus sont fréquents et arbitraires.

Pour une **reproduction stricte d'œuvre du Met**, le critère "original design" pose problème : pas un design original au sens d'Amazon. Une restauration substantielle documentée peut être défendable, mais sans garantie.

Frais : referral fee **15 %** (vs Etsy ~12-13 %), pas de listing fee, Pro 39,99 $/mois exonéré sur Handmade. Intégration Gelato **native sur Amazon US seulement**, pas EU.

→ **Ne pas perdre de temps là-dessus en Phase 0-1.** À reconsidérer uniquement si on développe une gamme à valeur artisanale documentable (impression giclée signée, encadrement maison).

### Amazon Merch on Demand — non pertinent

Catalogue limité à apparel + quelques accessoires (mugs, throw pillows, tote bags). **Pas de poster, pas de toile.** Modèle royalty (pas de marge libre), incompatible avec une politique de prix premium. **À écarter.**

### eBay — bon canal additionnel pour Phase 2

Policy art **autorise explicitement** les reproductions tant que l'œuvre originale n'est plus protégée. Mention "reproduction" obligatoire dans le titre et la description, attribution de l'artiste autorisée.

Frais : final value fee **15 %** sur Collectibles & Fine Art (14 % avec store) + 0,30-0,40 $ par commande. Plus cher qu'Etsy, comparable à Handmade.

**Intégration Gelato** : native, setup direct (cf. <https://www.gelato.com/integrations>).

**Public** : davantage orienté collection, vintage, chasseurs de prix. Moins aligné avec le buyer intent "déco curée" d'Etsy, mais utile pour écoulement de pièces premium encadrées et toiles à prix élevé.

### Recommandation phasée

- **Phase 0-1 (maintenant → preuve du hit-rate ≥ seuil)** : Etsy seul. Tout l'effort dans une boutique excellente, pas dilué sur 3 canaux.
- **Phase 2 (après ~3 mois Etsy validés)** : ajouter eBay. Effort marginal grâce à l'intégration Gelato native, audience complémentaire, +15 % de frais absorbés par un prix +20-25 % sur la cible eBay (acheteurs de pièces encadrées premium).
- **Écarter Amazon Handmade et Merch on Demand** sauf changement majeur de stratégie (ajout d'un atelier physique).

Sources : [Amazon Handmade policies](https://sellercentral.amazon.com/help/hub/reference/external/GNGMMFQ5FPLJFBJP), [eBay Selling art policy](https://www.ebay.com/help/policies/prohibited-restricted-items/selling-art-policy?id=4284), [Gelato integrations](https://www.gelato.com/integrations), [Etsy IP policy](https://www.etsy.com/legal/ip/).

---

<a name="8-couts"></a>
## 8. Coûts réels par vente (et impact sur le hit-rate)

### Exemple chiffré : poster A3 nu, prix de vente 24,90 €

| Poste                                       | Montant       | Note |
|---------------------------------------------|---------------|------|
| Prix de vente affiché (encaissé)            | **24,90 €**   | TTC |
| + Port encaissé du client                   |  +3,90 €      | TTC |
| **= Encaissement brut**                     |  28,80 €      | |
| − Frais Etsy transaction (6,5 %)            |  −1,87 €      | sur prix + port |
| − Frais Etsy paiement (~4 % + 0,30 € EU)    |  −1,45 €      | |
| − Listing fee amorti (0,20 € / 4 mois)      |  −0,05 €      | par variant |
| − Coût production Gelato (poster A3 200gsm) |  −7,50 €      | ordre de grandeur |
| − Port Gelato (UE zone proche)              |  −3,50 €      | |
| − Provision SAV (3-5 % réclamations)        |  −0,30 €      | |
| **= Marge nette avant taxes**               | **14,13 €**   | **49 % de marge** |

Plus généreux que les chiffres du `business-plan.md` (qui datait avec Printful) — Gelato production UE + port court compresse le coût total et la marge brute monte de ~28 % à ~49 % sur un poster A3 nu.

### Exemple chiffré : poster A2 encadré chêne, prix de vente 67,90 €

| Poste                                       | Montant       |
|---------------------------------------------|---------------|
| Encaissement brut (67,90 + 9,90 port)        | 77,80 €       |
| − Frais Etsy transaction (6,5 %)            |  −5,06 €      |
| − Frais Etsy paiement (~4 % + 0,30 €)        |  −3,41 €      |
| − Listing fee amorti                        |  −0,05 €      |
| − Coût production Gelato (A2 encadré chêne) | −28,00 €      |
| − Port Gelato encadré (volume)              |  −8,50 €      |
| − Provision SAV (5 % réclamations)          |  −1,40 €      |
| **= Marge nette**                           | **31,38 €**   |

40 % de marge, **3,5× plus de marge absolue** que sur le poster nu → confirme la stratégie brief-marque §2 : **les encadrés portent la rentabilité**.

### Avec Gelato+ ($19,99/mo, jusqu'à -25 % production)

Le coût production tombe de 28 € à ~21 €, la marge passe à ~38 € par vente d'encadré (+22 %). **Activer Gelato+ dès qu'on dépasse 15-20 ventes/mois** — l'abonnement est amorti à 3 ventes.

### Impact sur le seuil hit-rate

Le calculateur (`finance/calculateur-viabilite.xlsx`) est calibré sur 8 €/vente. **Recalibrer à 14 €/vente** (poster nu Gelato) divise le hit-rate seuil par ~1,7 :

- Ancien seuil de rentabilité estimé : ~3,5-4 % (Printful, 8 €/vente)
- Nouveau seuil estimé : **~2-2,5 %** (Gelato, 14 €/vente)
- Avec mix 60% encadrés / 40% nus : **~1,5-2 %**

Ça **élargit considérablement la marge de manœuvre** du modèle. À recalibrer formellement dans le calculateur xlsx avant de prendre des décisions de scale.

### Seuil Offsite Ads Etsy

Inchangé : au-delà de **10 000 € de ventes sur 12 mois glissants**, Etsy inscrit d'office aux Offsite Ads (15 % sur ventes attribuées, 12 % à partir du seuil, **non désactivable**, capé à 100 $/commande).

À l'échelle, prévoir −3 à −5 points de marge effective. Dans le calculateur, ajouter un scénario "post-Offsite Ads".

### Ce que ça change opérationnellement

1. **Le pricing peut être plus généreux** que les hypothèses originales → des prix à 24-30 € sur A3 nus restent rentables
2. **L'encadré est l'arme stratégique** — 3,5× la marge du nu, à pousser dans les images et le titre
3. **Le seuil hit-rate vrai est ~2 %** — plus accessible qu'estimé à l'origine
4. **Gelato+ devient mandatory** dès la 4e vente du mois

---

*Ce document est volontairement opérationnel et concret. Pour la stratégie de marque, voir [`brief-marque.md`](brief-marque.md). Pour les chiffres financiers, voir [`finance/calculateur-viabilite.xlsx`](../finance/calculateur-viabilite.xlsx). Pour la todo opérationnelle de mise en vente, voir [`roadmap-mise-en-vente.md`](roadmap-mise-en-vente.md).*
