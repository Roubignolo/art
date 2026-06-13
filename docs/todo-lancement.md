# TODO de lancement — Vellum & Cie

*Checklist opérationnelle vivante. On coche au fur et à mesure. Légende : ✅ fait ·
⏳ en cours · ⬜ à faire · 👤 action humaine (hors code) · ⚙️ code.*

> Vue narrative par phases : [`roadmap-mise-en-vente.md`](roadmap-mise-en-vente.md).
> Ce fichier est la **liste d'actions concrètes** à tenir à jour.

---

## 0. Marque & légal 👤

- ⬜ Confirmer la **disponibilité du nom « Vellum & Cie »** : INPI (FR) + EUIPO (UE), recherche d'antériorité.
- ⬜ Réserver le **domaine** (.com + .fr) même sans site immédiat.
- ⬜ Réserver les **handles** Instagram + Pinterest.
- ⬜ (optionnel) Déposer la marque INPI (~250 €).
- ⬜ Rédiger le **template de mention provenance** (« sourced by », jamais « made by ») — cf. [process-vente-production.md](process-vente-production.md) §6.

## 1. Statut & fiscalité 👤

- ⬜ Vérifier que la **micro-entreprise** couvre la vente de biens (APE 4791B vente à distance).
- ⬜ Plafonds TVA 2026 (biens 91 900 € / services 36 800 €) — situer le positionnement.
- ⬜ **OSS** (One-Stop-Shop) pour ventes intra-UE > 10 000 € — inscription impots.gouv.fr si applicable.
- ⬜ US : marketplace facilitator Etsy → pas de sales tax à gérer côté nous (revérifier 2026).

## 2. Compte Etsy & boutique 👤 🔴

- ⬜ Créer le **compte vendeur** Etsy + Etsy Payments (EUR).
- ⬜ Boutique : nom = marque · bannière 1200×300 · logo · annonce · page « À propos » (3 §).
- ⬜ **Politiques** : retour (défaut/perte oui, « changé d'avis » non), expédition (UE 3-6j / US 5-10j), CGV (« sourced by »), confidentialité RGPD.
- ⬜ **Profils de livraison** par zone (UE / UK / US / monde) — coûts pré-calculés.
- 🔴 ⬜ **Déclarer les production partners** dans Shop Manager → Settings → Production Partners : **Gelato** ET **Prodigi** (sans ça → risque de suspension).

## 3. Lien avec les imprimeurs (Gelato + Prodigi)

### 3.1 Comptes & intégration 👤
- ⬜ Créer compte **Gelato** (gratuit) + lier à Etsy (intégration native, sync 1-5 min).
- ⬜ Créer compte **Prodigi** (gratuit). NB : création de listing Etsy **manuelle** côté Prodigi.
- ⬜ Définir le **routing** : standard → Gelato · signature premium → Prodigi (cf. [benchmark](benchmark-pod-fournisseurs.md) §5).

### 3.2 ✉️ ÉCRIRE UN MAIL — questions ouvertes à **Gelato** 👤 🔴
*(Réponses non vérifiables en doc publique — pages support en 403. À confirmer avant de figer le pipeline d'export. Cf. [decision-encadrement-tailles.md](decision-encadrement-tailles.md).)*
### 3.3 ✉️ ÉCRIRE UN MAIL — questions ouvertes à **Prodigi** 👤
*(La doc API Prodigi confirme déjà l'essentiel — à valider en conditions réelles.)*

- ⬜ **Confirmer le `sizing` API** : `fitPrintArea` préserve bien le ratio sans crop ni déformation, et `fillPrintArea` (défaut) **crope** — confirmer le comportement sur un vrai order test.
- ⬜ **Passe-partout via API** : peut-on **activer le mount** et choisir sa **couleur** (snow white / black / hayseed) par commande via l'API ? Les **paliers de mat** (1″ / 1,5″ / 2″) sont-ils figés par taille de cadre ou paramétrables ?
- ⬜ **Tailles** : confirmer le **catalogue fixe** (pas de custom au mm) et récupérer la **liste complète des tailles** Classic/Box + leurs **ratios** + la **taille d'image visible** après mat pour chacune.
- ⬜ **Upload PDF** : confirmer qu'un **PDF est imprimé à la taille reçue** sans redimensionnement (contrôle total du ratio par le fichier).
- ⬜ **Profils ICC papier** : où télécharger les **profils Prodigi** spécifiques pour Hahnemühle **Photo Rag** et **German Etching** (pour notre soft-proof — cf. [restauration-politique.md](restauration-politique.md) §5) ?
- ⬜ **Verre anti-reflet (moth-eye)** : disponible sur quelles zones d'expédition / tailles ?
- ⬜ **Insert provenance** : confirmer prix (2£ / 0,50£ Pro) + format A6 + dépôt du PDF par commande via API.

### 3.bis — Brouillons prêts à envoyer 📨

**Canaux :**
- **Prodigi** → email **`support@prodigi.com`** (technique/API) · `sales@prodigi.com` (commercial).
- **Gelato** → **pas d'email public** : formulaire <https://www.gelato.com/contact> ou **chat live 24/7** du dashboard (le plus fiable une fois le compte créé). Coller le texte ci-dessous.

*(Rédigés en anglais — langue du support des deux ; remplacer `[Nom / boutique]`.)*

---

**➤ GELATO** — *à coller dans le formulaire / chat. Objet : « Pre-onboarding — fine-art posters & framed prints, non-standard aspect ratios »*

> Hi Gelato team,
>
> We're launching a print-on-demand art shop (public-domain museum reproductions) on Etsy, with Gelato as our default producer. Before finalizing our file pipeline, could you confirm a few technical points?
>
> 1. **Aspect-ratio handling (fit vs fill):** if an uploaded image's aspect ratio doesn't exactly match the product/size ratio, what does Gelato do by default — center-crop to fill, stretch, add a white border (fit/contain), or reject/warn? Can we force a "fit/contain, no crop" behaviour, and if so via the API or the editor? What is the exact attribute/field name?
> 2. **Custom poster sizes:** what are the exact min and max width/height, and the step (1 cm? 1 mm?) for a custom-size poster? Is custom sizing available via the API (v4), or only via the editor?
> 3. **Framed prints:** are framed sizes limited to the standard catalogue, or can frames follow custom poster sizes? Could you send the full list of framed sizes with their aspect ratios? Is there any passe-partout / mat option (configurable width/colour), or is the poster mounted edge-to-edge by the customer?
> 4. **Templates / safe area:** do you provide per-product print templates with the exact safe area and bleed (poster, framed, canvas)?
> 5. **White-label:** can the shipping sender, outer carton, label and packing slip be fully white-labelled (no Gelato branding), and under what plan (is Gelato+ required)? Can we include an A6 provenance insert card in the parcel via the API, and at what cost?
>
> Thanks a lot — happy to share more about our use case.
> [Nom / boutique]

---

**➤ PRODIGI** — *email à `support@prodigi.com`. Objet : « Pre-onboarding API questions — framed fine-art prints (mounts, sizing, ICC profiles) »*

> Hi Prodigi team,
>
> We're launching a print-on-demand art shop (public-domain museum reproductions) and plan to use Prodigi for our premium "signature" line (Hahnemühle fine art + real-wood framing). A few technical confirmations before we build our pipeline:
>
> 1. **Sizing / no-crop:** can you confirm that ordering with `sizing=fitPrintArea` preserves the image aspect ratio with no crop and no distortion (white space added as needed), while `fillPrintArea` (default) center-crops? We must never crop the artwork.
> 2. **Mounts via API:** can we enable the mount (passe-partout) and choose its colour (snow white / black / hayseed) per order via the Print API? Are mat widths fixed per frame size (1"/1.5"/2"), or configurable?
> 3. **Sizes:** could you send the full list of Classic and Box frame sizes with (a) outer/glazing size, (b) aspect ratio, and (c) the visible image size after the mount, for each? And confirm there is no true mm-level custom size.
> 4. **PDF:** can you confirm a PDF upload is printed at the received size with no resizing (so we control the ratio entirely in the file)?
> 5. **ICC profiles:** where can we download your printer/paper ICC profiles for Hahnemühle **Photo Rag** and **German Etching**, for accurate soft-proofing on our side?
> 6. **Anti-reflective glazing (moth-eye):** which sizes / shipping regions support it?
> 7. **Provenance insert:** can we include an A6 insert card per order via the API, and what's the cost (standard vs Prodigi Pro)?
>
> Thanks very much.
> [Nom / boutique]

---

### 3.4 Échantillons & QC 👤 🔴
- ⬜ Commander un **sample order** par produit/ligne (Gelato encadré chêne + Prodigi fine art matté) à notre adresse.
- ⬜ Vérifier : fidélité couleur vs soft-proof · qualité cadre/verre/mat · emballage neutre · packing slip white-label · délai réel.
- ⬜ **Go/no-go** par produit avant publication large.

## 4. Préparation produit — fichiers, tailles, encadrement ⚙️

- ✅ **Catalogue source** : 60 œuvres curées, 100 % FIDÈLES, taguées (sujet/mouvement/palette) — [collection.json](../web/public/renders/collection.json).
- ✅ **Chaîne couleur** : sRGB de livraison (ICC), audit de fidélité ΔE2000, soft-proof gamut — cf. [restauration-politique.md](restauration-politique.md).
- ✅ **Mise en page produit (ratios non standard)** : module `agents/render/layout.py` (taille catalogue au ratio le plus proche + passe-partout/bordure asymétrique, jamais de crop) — cf. [decision-encadrement-tailles.md](decision-encadrement-tailles.md).
- ✅ **Mockups = produit livré** : `frames.encadrer(ratio_cible=…)` rend le vrai passe-partout (Prodigi) / bordure fichier (Gelato) ; 60 mockups encadrés régénérés.
- ⬜ Geler la **grille de tailles** définitive par ligne (après réponses mails §3.2/3.3).
- ⬜ Générer les **fichiers print** finaux (Gelato : bordure intégrée au bon ratio · Prodigi : ratio exact + `fitPrintArea` + mount).

## 5. Premier listing manuel 👤 🔴

- ⬜ Choisir la **1re œuvre** (ex. Van Gogh *Irises* #436528, forte notoriété).
- ⬜ Marketing 5 langues (cockpit) + aperçu listing.
- ⬜ Produit Gelato (poster encadré A2 chêne) → publier vers Etsy.
- ⬜ Vérifier titre/tags/description/10 images/prix/variants/attributs (who made it = someone else).
- ⬜ Commander l'échantillon, valider, **go/no-go**.

## 6. Collection d'amorçage (15 listings) 👤

- ⬜ Choisir une **collection thématique** (cockpit : filtre par tag — Floral / Impressionnisme / Estampes japonaises…).
- ⬜ 5 œuvres × 3 produits (poster nu, encadré, giftable).
- ⬜ Mesure hit-rate sur 2-3 semaines.

## 7. Marketing 👤

- ⬜ Pinterest Business (canal n°1 wall art) : 1 tableau par collection, 3-5 pins/œuvre.
- ⬜ Instagram (réservation handle + premiers posts avant/après-déco).

## 8. Automation du tunnel (cockpit P3) ⚙️

- ⬜ OAuth Etsy live (tokens) → `/api/etsy/publish` réel.
- ⬜ Webhook Etsy `order.paid` → routing Gelato/Prodigi → création commande.
- ⬜ Insert provenance auto (PDF A6 + QR) par commande.
- ⬜ Webhooks Gelato/Prodigi `shipped` → tracking Etsy.
- ⬜ Mockups cloud (Dynamic Mockups + fal.ai) — optionnel, le moteur local suffit.

## 9. Analytics & boucle feedback (P4) ⚙️

- ⬜ Capture ventes en DB (table `Sale`).
- ⬜ Dashboard hit-rate / marge / top collections.
- ⬜ Repondération du scoring sur ventes réelles.

## 10. Garde-fous permanents (ne jamais retirer) 🔴

- ✅ **Audit de fidélité** automatique (jamais d'œuvre INFIDÈLE au catalogue).
- ⬜ **Validation humaine** des gates DP/marque avant toute production.
- ⬜ **Échantillon physique** avant tout nouveau produit.
- ⬜ Attribution **« sourced by »** sur chaque fiche.
- ⬜ Jamais de secret committé (clés Etsy/Gelato/Prodigi/Anthropic).
- ⬜ Veille politique Etsy / POD tous les 6 mois.

---

*Mise à jour : à chaque action significative, cocher ici et noter le réel vs le prévu.*
