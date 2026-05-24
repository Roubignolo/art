# Benchmark POD — Printful vs Gelato vs Prodigi

*Analyse comparative chiffrée des trois fournisseurs print-on-demand candidats pour Provenance : sur les axes intégration marketplaces, catalogue art mural, qualité mockups, white-label/branding, automation/webhooks, et logistique France. Décision finale et architecture hybride.*

> Mis à jour après recherche sur ~50 sources web (octobre 2026). 3 sub-agents parallèles ont contribué (benchmark fonctionnel, white-label, automation technique).

---

## TL;DR — Décision

**Architecture hybride** :
- **Gelato par défaut** pour les produits standard (poster, encadré standard, mug, torchon, tote). Production locale FR = expérience client la plus crédible.
- **Prodigi pour la ligne "signature premium"** : fine art Hahnemühle + encadrés vrai bois (Fine Art Trade Guild). White-label le plus propre + insert provenance pas cher.
- **Printful écarté** : trop d'instabilité en 2026 (bugs sync Etsy rapportés + arrêt warehousing EU/UK/Canada au 1er mars 2026), et white-label moins complet.

**Cette décision confirme le choix initial de `CLAUDE.md`** ("Gelato par défaut, Prodigi pour les pièces premium ; pas Printful"). La recherche apporte la justification chiffrée + la stratégie d'usage différenciée.

---

## 1. Tableau comparatif synthétique

| Critère                                       | Printful                              | **Gelato**                              | **Prodigi**                             |
|-----------------------------------------------|---------------------------------------|-----------------------------------------|-----------------------------------------|
| **Intégration Etsy native**                    | Oui, mature                          | **Oui, sync 1-5 min, la plus stable**  | Oui, mais création listing manuelle    |
| **Intégration eBay native**                    | **Oui** (le seul)                    | Non (via Shopify-bridge)               | Non (CSV ou Shopify)                   |
| **Intégration Amazon Seller / Handmade**       | Oui (Seller Central US/EU)           | Non natif                              | Non natif                              |
| **Intégration Shopify / WooCommerce**          | Oui                                  | Oui                                    | Oui                                    |
| **Catalogue poster**                           | Standard (Enhanced Matte, Premium Luster) | Premium 200gsm, Museum 250gsm, Classic | Budget, Premium, **Fine Art Hahnemühle** |
| **Catalogue encadré**                          | Alder + plexi                        | Chêne/noir/blanc/**noyer**/bois clair  | **Vrai bois (FATG approved)**          |
| **Catalogue canvas**                           | Standard + cadre bois                | Standard                               | **4 substrats** dont Hahnemühle Monet  |
| **Fine art (papiers d'archive)**               | Giclée standard                      | Hahnemühle Giclée 260gsm               | **Hahnemühle Photo Rag + German Etching** (ref marché) |
| **Production France**                          | Non (Barcelone ES, Riga LV)          | **Oui (production locale FR + 32 pays)** | Non (UK + Pays-Bas)                    |
| **Routing géo client Paris**                   | Barcelone fixe                       | **Velocity Switch (multi-hub auto)**   | Venlo (NL) ou UK, splittable           |
| **Délai livraison FR**                         | ~5-7 j (depuis ES)                   | **3-5 j (depuis FR/ES)**                | 4-7 j (depuis NL/UK)                   |
| **Pricing poster A2 mat**                      | ~12-14 €                              | **~8-11 €**                             | ~10-13 €                                |
| **Pricing poster A2 encadré chêne**            | ~38-45 €                              | **~32-40 €**                            | ~35-50 €                                |
| **API version 2026**                           | v2 (beta) + v1                       | v4 (Order/eCommerce)                   | v4 (CloudEvents)                       |
| **Webhooks signés HMAC**                       | **Oui (excellent)**                  | Non (point faible — URL signée à faire) | URL signée                              |
| **Mockup Generator API**                       | Oui (async + webhook)                | Oui (template + AI Magic Mockups)      | **Non (bloquant pour zéro-touch)**     |
| **Sender d'expédition modifiable**             | Partiel (pas DHL/UPS/FedEx)          | Oui (la plupart transporteurs)         | **Intégral 100 %**                     |
| **Carton extérieur neutre**                    | Oui                                  | Oui                                    | Oui                                    |
| **Sticker branding extérieur**                 | Custom mailers (25 $/mo storage min) | 0,49 $ (Gelato+ requis 19,99 $/mo)     | 1 £ (0,25 £ avec Prodigi Pro)          |
| **Insert provenance B&W**                      | 0,50 $ + 25 $/mo storage             | 0,49 $ (Gelato+ requis)                | **Packing slip gratuit ; insert 2£ (0,50£ Pro), sans minimum** |
| **Stabilité 2026 (Etsy)**                      | **⚠ Bugs token + shake-up warehousing EU mars 2026** | La plus propre                        | Lente mais stable                       |
| **API refund/claim auto**                      | Non                                  | Non                                    | Non                                    |

---

## 2. Pourquoi Gelato gagne sur "France" et "stabilité Etsy"

**Production locale FR**, c'est unique au marché. Concrètement, pour un client à Paris :
- **Gelato** imprime probablement à Barcelone, Pays-Bas ou directement en FR → expédié La Poste → **3-5 j** livraison.
- **Prodigi** imprime à Venlo (NL) ou UK → expédié DHL/UPS → **4-7 j**.
- **Printful** imprime à Barcelone (fixe) → expédié UPS → **5-7 j**.

L'écart n'est pas énorme en jours, **mais le tracking carrier est en français pour Gelato** vs souvent en anglais (UPS NL/UK). Pour un acheteur Etsy haut de gamme français, c'est un signal de crédibilité supplémentaire.

**Velocity Switch** (algorithme Gelato de routing multi-hub) → pas de choix manuel à faire, c'est optimisé automatiquement à la commande selon proximité + capacité + délai.

**Sur l'Etsy sync** : les threads communautaires 2026 rapportent fréquemment chez Printful des bugs de token (déconnexions, produits supprimés du compte Printful). Gelato est jugé "le plus propre" par les revues techniques 2026. C'est un risque de fond évité.

---

## 3. Pourquoi Prodigi gagne sur "premium" et "white-label"

**Catalogue fine art** : Prodigi propose les **vrais papiers Hahnemühle** (Photo Rag 308gsm, German Etching 310gsm) qui sont la référence du marché du fine art. Gelato propose un "Hahnemühle Giclée" 260gsm mais c'est moins haut de gamme. Printful n'a pas de partenariat Hahnemühle officiel.

**Encadrés "Fine Art Trade Guild approved"** : Prodigi est labellisé par la fédération britannique du commerce de fine art. C'est un argument à mettre dans la description Etsy pour la ligne signature.

**White-label intégral** :
- Le **sender d'expédition est 100 % modifiable** chez Prodigi (vs partiel chez Printful — pas DHL/UPS/FedEx).
- Le **packing slip est gratuit** sur fine art prints, framed et canvas (vs Gelato+ requis chez Gelato à 19,99 $/mo, ou 25 $/mo storage chez Printful).
- L'**insert provenance imprimable à la demande** est à 2£ (0,50£ avec Prodigi Pro à 40£/mois) **sans minimum d'engagement**. C'est l'option idéale pour glisser une **carte de provenance avec QR code** vers la fiche musée, dans chaque colis fine art.

→ Pour la ligne "signature premium" qui justifie un prix +30-50% (canvas Hahnemühle, encadré vrai bois), Prodigi est mieux outillé que Gelato.

---

## 4. Pourquoi Printful sort de l'équation

3 raisons cumulatives, dont 2 sont des risques 2026 réels :

1. **Bugs de sync Etsy rapportés en 2026** (threads forum Etsy : déconnexions de token, produits qui disparaissent du compte Printful). Risque de fond pour une opération critique.
2. **⚠ Arrêt du warehousing EU/UK/Canada au 1er mars 2026** ([source officielle Printful](https://help.printful.com/hc/en-us/articles/21048694941340)). Impact réel sur la résilience du fulfillment.
3. **White-label moins propre** : le sender d'expédition n'est **pas modifiable pour DHL/UPS/FedEx** (et les transporteurs internationaux sont précisément ceux-là). Notre marque ne contrôle pas l'expéditeur visible côté tracking.

**Seul argument restant en faveur de Printful** : c'est le seul à avoir une intégration eBay native. Mais pour ça, on préférera ajouter un connecteur tiers (Commercium pour Gelato→eBay) plutôt que d'ajouter un 3ᵉ fournisseur dans l'architecture.

---

## 5. Architecture hybride recommandée

```
                      ┌──────────────────────────────────┐
                      │   Cockpit Next.js (déjà déployé)  │
                      │   - decision par produit / œuvre  │
                      │   - routing selon ligne produit   │
                      └──────────────┬───────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                  │
                    ▼                                  ▼
   ┌─────────────────────────────┐    ┌─────────────────────────────┐
   │   GELATO (par défaut)       │    │   PRODIGI (signature)        │
   │                              │    │                              │
   │ Produits :                   │    │ Produits :                   │
   │  - poster A4/A3/A2/A1 mat    │    │  - fine art Hahnemühle      │
   │  - encadré standard          │    │    Photo Rag, German Etching │
   │  - mug, coussin, torchon     │    │  - encadrés vrai bois (FATG) │
   │  - canvas standard           │    │  - canvas Hahnemühle Monet  │
   │                              │    │                              │
   │ Avantages :                  │    │ Avantages :                  │
   │  - Production locale FR      │    │  - White-label intégral      │
   │  - Velocity Switch           │    │  - Insert provenance pas cher│
   │  - Etsy sync la + stable    │    │  - Catalogue fine art top    │
   │  - Mockup API native         │    │  - "FATG approved" arg vente│
   │                              │    │                              │
   │ Tarif : gratuit base,        │    │ Tarif : gratuit base,        │
   │   activer Gelato+ ($240/an)  │    │   Prodigi Pro (£480/an) si  │
   │   dès 15-20 ventes/mois      │    │   on veut sticker à 0,25£    │
   └─────────────────────────────┘    └─────────────────────────────┘
                    │                                  │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                      ┌──────────────────────────────────┐
                      │       ETSY (vitrine unique)       │
                      │   Variants standards + signature  │
                      │   séparés par "Section" Etsy      │
                      └──────────────────────────────────┘
```

**Règle de routing dans le cockpit** :
- Tout produit standard → Gelato
- Tout produit avec tag `signature` ou `fine-art` → Prodigi
- Œuvre signalée "premium" dans le cockpit (axe attribution ≥ 9) → automatiquement candidat pour ligne signature Prodigi

---

## 6. Réponses aux questions opérationnelles

### Vendre des impressions encadrées : oui chez les deux

| Type | Gelato | Prodigi |
|------|--------|---------|
| Cadre standard (oak laminé) | ✓ chêne, noir, blanc, noyer, bois clair | ✓ oak laminé |
| Cadre premium (vrai bois) | option **noyer** | ✓ vrai bois **FATG approved** |
| Vitrage | Plexi standard | Plexi standard (vrai verre optionnel selon zone) |
| Tailles | A4 → A1 | A4 → A1 + custom |
| Emballage | Coins + I-beams + double cannelure | Coins + carton + bulle pour grands |

### Ce que reçoit l'acheteur Etsy

**Le colis** :
- Carton extérieur **neutre, sans logo POD** (chez les deux)
- Étiquette d'expédition au nom du marchand (intégral chez Prodigi, modifiable chez Gelato)
- Posters dans tube renforcé triangulaire ; encadrés à plat avec coins protecteurs
- Pas de fuite "Printful/Gelato/Prodigi" sur le carton

**Dans le colis** :
- **Packing slip white-label** au nom du marchand — pas de logo POD
- **Optionnel : insert provenance** (carte avec œuvre + artiste + dates + source institution + QR code vers la fiche musée + mot de remerciement). Coût marginal 0,49-0,50 € par colis. **Recommandé fortement** pour le positionnement Provenance.

**Côté Etsy** :
- Email de confirmation au nom de la marchand
- Email de tracking au nom de la marchand
- Facture commerciale Etsy au nom de la marchand
- Le tracking carrier (La Poste, UPS) montre la ville d'origine de l'usine mais c'est invisible/peu lu dans la majorité des cas.

**Seule fuite résiduelle inévitable** : pour les commandes hors-UE (FR→US/UK), la **déclaration douanière CN23** porte l'adresse de l'usine d'origine comme expéditeur physique. Le destinataire peut le voir sur le tracking. C'est technique, partagé par les 3 POD, pas de contournement.

### Ré-expédition par nous : non

**Aucun des 3 POD ne propose le mode "envoi au marchand pour réexpédition"**. C'est par design — le modèle POD c'est usine → client. Le seul cas où on reçoit chez nous : commandes d'échantillons (sample orders) pour QC manuel ou prises de vue Instagram.

---

## 7. Optimisations à apporter au process actuel

D'après le croisement des 3 findings :

### À ajouter immédiatement (P1-P2)

- [ ] **Insert provenance physique** dans chaque colis :
  - Format : carte 105 × 148 mm (A6) recto-verso
  - Recto : œuvre + artiste + dates + collection source + QR code vers fiche musée
  - Verso : mot de remerciement + signature marque + URL boutique
  - Coût : 0,50 € par colis (Prodigi free packing slip + insert 2£ ou 0,50£ Pro)
  - **À budgéter dans le pricing dès la phase 1**
- [ ] **Sticker logo extérieur** : pas en Phase 0-1 (cher à activer chez Gelato/Prodigi), à reconsidérer en Phase 2 quand le volume justifie Gelato+ ou Prodigi Pro
- [ ] **Sample orders systématiques pour chaque nouveau produit** : commander 1 exemplaire à notre adresse, vérifier qualité physique, photos pour Instagram avant publication large

### À automatiser en P3 (cockpit)

- [ ] **Routing automatique Gelato/Prodigi dans le cockpit** selon tag du produit :
  ```typescript
  const provider = work.classification === 'signature' || product.line === 'fine-art'
    ? 'prodigi'
    : 'gelato';
  ```
- [ ] **Module insert provenance auto-généré** : pour chaque commande, générer le PDF A6 avec les données de l'œuvre + QR code, envoyé en pièce jointe via Gelato/Prodigi API
- [ ] **Sécuriser les webhooks Gelato (pas de HMAC natif)** via URL signée custom (secret en query string, vérifié côté `/api/gelato/webhook`)
- [ ] **UI de claim/refund manuel** dans le cockpit (aucun POD n'a d'endpoint API auto) : bouton "Ouvrir un litige Gelato/Prodigi" avec champs prédéfinis + photos du défaut, sortie email/dashboard

### À considérer en P3-P4

- [ ] **Activer Gelato+** dès 15-20 ventes/mois standard (amortissement à 3 ventes : -25 % production sur ces 3, hop ROI)
- [ ] **Activer Prodigi Pro** uniquement quand la ligne signature représente ≥ 5 ventes/mois (£480/an = ~£40/mois)
- [ ] **Si on active eBay en Phase 2** : connecteur tiers (Commercium ou équivalent) Gelato→eBay, plutôt qu'ajouter Printful comme 3e fournisseur

---

## 8. Sources

Recherche menée via 3 sub-agents parallèles. ~50 sources web croisées :

### Printful
- [API v2 docs](https://developers.printful.com/docs/v2-beta/)
- [Help — Connect Etsy](https://help.printful.com/hc/en-us/articles/360014008560)
- [Framed Posters](https://www.printful.com/custom/wall-art/framed-posters)
- [Branded packaging inserts](https://www.printful.com/branded-packaging-inserts)
- [EU warehousing changes mars 2026](https://help.printful.com/hc/en-us/articles/21048694941340)
- [Sender address modifiable (DHL/UPS exception)](https://help.printful.com/hc/en-us/articles/360014065699)
- [Etsy sync bugs thread 2026](https://community.etsy.com/t5/Technical-Issues/Printful-is-still-not-synching/td-p/139399350)

### Gelato
- [API v4 Create Order](https://dashboard.gelato.com/docs/orders/v4/create/)
- [Webhooks](https://dashboard.gelato.com/docs/webhooks/)
- [Create Product (from template) API](https://dashboard.gelato.com/docs/ecommerce/products/create-from-template/)
- [Velocity Switch](https://www.gelato.com/velocity-switch)
- [Available integrations](https://support.gelato.com/en/articles/8996020-gelato-s-available-integrations)
- [Print on Demand in France](https://www.gelato.com/print-on-demand/france)
- [Gelato+ subscription cost](https://support.gelato.com/en/articles/8996313)
- [Branded packaging page](https://www.gelato.com/branded-packaging)
- [How framed posters packed](https://support.gelato.com/en/articles/8996173)
- [Etsy integration limits](https://support.gelato.com/en/articles/8996461)
- [Sender name on shipping label](https://support.gelato.com/en/articles/8996185)

### Prodigi
- [Print API reference](https://www.prodigi.com/print-api/docs/reference/)
- [E-commerce integrations](https://www.prodigi.com/ecommerce-integrations/)
- [Etsy integration FAQ](https://www.prodigi.com/faq/etsy/)
- [Hahnemühle German Etching](https://www.prodigi.com/products/prints-and-posters/art-prints/hahnemuhle-german-etching/)
- [Hahnemühle Photo Rag](https://www.prodigi.com/products/prints-and-posters/photo-prints/hahnemuhle-photo-rag/)
- [Best custom canvas wall art](https://www.prodigi.com/blog/best-custom-canvas-wall-art-to-sell-in-your-store/)
- [AI Mockup Generator](https://www.prodigi.com/blog/ai-mockup-generator/)
- [White-label confirmation](https://support.prodigi.com/hc/en-us/articles/13159029986332)
- [Packaging FAQ](https://www.prodigi.com/faq/packaging/)
- [Custom packaging inserts (prix)](https://www.prodigi.com/branded-packaging-inserts/)
- [Free packing slips](https://support.prodigi.com/hc/en-us/articles/19862285488668)
- [Prodigi Pro cost](https://support.prodigi.com/hc/en-us/articles/19847945394460)
- [France POD](https://www.prodigi.com/start/france-print-on-demand/)
- [Brexit-proof supply chain](https://www.prodigi.com/blog/building-a-brexit-proof-supply-chain-for-your-dropshipping-business/)
- [Wingly Prodigi TypeScript wrapper (community)](https://github.com/Wingly-Company/prodigi)

### Comparatifs croisés
- [Gelato vs Printful vs Printify EU 2026 — marketing4ecommerce](https://marketing4ecommerce.net/en/gelato-printful-printify-comparative/)
- [Gelato vs Printful shipping speed 2026](https://www.gelato.com/blog/gelato-vs-printful-vs-printify)
- [Top art POD services 2026 — MerchOne](https://merchone.com/blog/top-art-print-on-demand-services/)
- [Etsy POD integration deep dive 2026](https://www.printondemandbusiness.com/blog/etsy-pod-integration/)
- [POD API integration guide 2026 — Merch Titans](https://merchtitans.com/blog/print-on-demand-api-integration-guide)
- [Etsy international shipments / customs](https://help.etsy.com/hc/en-us/articles/360001987487)

---

*Ce document est issu d'une recherche croisée d'octobre 2026. Les tarifs et capacités évoluent — recheck tous les 6 mois (notamment l'impact réel du shake-up warehousing Printful mars 2026 et les éventuelles nouvelles intégrations eBay chez Gelato/Prodigi).*
