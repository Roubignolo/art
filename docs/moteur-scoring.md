# Moteur de scoring — version « domaine public curé »

*Spec implémentable. Claude score des œuvres/thèmes candidats ; seuls ceux qui passent les filtres ET dépassent le seuil partent en restauration → Printful → Etsy.*

---

## Architecture en deux temps

1. **Les GATES (filtres éliminatoires)** — si un seul échoue, score = 0, rejet immédiat. Ils protègent tes comptes vendeurs. C'est non négociable.
2. **Les AXES NOTÉS** — sur les œuvres qui passent les gates, un score pondéré sur 10 décide quoi produire.

---

## 1. Les 4 GATES (réussite obligatoire)

### G1 — Statut domaine public (double règle, on prend la plus stricte)
Pour vendre dans le monde entier sans risque, l'œuvre doit être DP **à la fois** :
- **US** : publiée en **1930 ou avant** (règle des 95 ans, mise à jour chaque 1ᵉʳ janvier — en 2027 ce sera 1931, etc.).
- **UE / France** : auteur **mort depuis 70 ans ou plus** (en 2026 → décès en 1955 ou avant).

⚠️ Le piège : une œuvre publiée en 1928 mais dont l'auteur est mort en 1965 est DP aux US mais **encore protégée en UE** jusqu'en 2036. → rejet pour la vente mondiale. En cas de date d'auteur inconnue/incertaine → **rejet par défaut**.

### G2 — Absence de marque résiduelle
Une œuvre peut être DP *et* rester couverte par une marque déposée vivante (personnages, logos : Betty Boop, Mickey, mascottes, blasons de marques). Claude vérifie : est-ce un personnage/symbole encore exploité commercialement comme marque ? Si oui → **rejet**, même si l'œuvre est techniquement DP.

### G3 — Source propre
- Accepté : scan d'institution en **CC0 / DP confirmé** (Met, Rijksmuseum, Smithsonian, BHL, etc.).
- Rejeté : version retravaillée propriétaire utilisée telle quelle (ex. rendition « enhanced/remixed » rawpixel comme élément principal) — sauf transformation lourde de ta part.

### G4 — Résolution suffisante pour le produit cible
La résolution du master doit permettre **≥ 150 DPI à la taille finale du produit visé** (idéal 300). Sinon : soit on rétrograde vers un produit plus petit, soit **rejet** si même le plus petit produit viable n'est pas atteignable. (Renvoie à la spec qualité du brief.)

---

## 2. Les 4 AXES NOTÉS (sur 10, pondérés)

| Axe | Poids | Question centrale |
|-----|-------|-------------------|
| Momentum esthétique | **30 %** | L'esthétique/le thème est-il en train de monter ? |
| Conformité & richesse d'attribution | **20 %** | La provenance est-elle propre ET racontable (atout marketing) ? |
| Traduisibilité produit | **25 %** | L'œuvre rend-elle bien sur le produit Printful visé ? |
| Espace concurrentiel (anti-saturation) | **25 %** | Reste-t-il de la place, ou est-ce ultra-vendu ? |

### Axe 1 — Momentum esthétique (30 %)
On ne score pas un meme, mais une **esthétique de déco/lifestyle**. Où est-elle sur la courbe d'adoption ?

- **Sources** : Pinterest Trends (le signal n°1 pour la déco murale), Google Trends, tendances de recherche Etsy, hashtags esthétiques Instagram/TikTok, magazines déco.
- **Rubrique** : 9-10 = montée nette, pas encore au pic (ex. une niche esthétique émergente) · 5-6 = établie/stable · 1-3 = en déclin ou au pic dépassé (tu arriverais trop tard vu le délai Printful).
- *Exemples de territoires* : cottagecore/botanique, dark academia, celestial/astronomie, japandi & ukiyo-e, anatomie vintage, cartographie ancienne, Art nouveau.

### Axe 2 — Conformité & richesse d'attribution (20 %)
Au-delà du gate G1-G3 : à quel point la provenance est-elle **documentée et narrable** ? C'est un axe marketing déguisé.
- 9-10 = artiste, date, institution, anecdote disponibles → fiche produit riche, storytelling premium possible.
- 4-6 = DP confirmé mais provenance pauvre (anonyme, peu d'histoire).
- *Pourquoi ça compte* : ta différenciation = la transparence. Une œuvre qui « se raconte » justifie le prix premium.

### Axe 3 — Traduisibilité produit (25 %)
L'œuvre rend-elle bien sur **le produit visé précisément** ? Une planche botanique fine = parfaite sur torchon/poster ; une peinture sombre = canvas, pas mug.
- Critères : format/ratio compatible avec le produit, impact visuel à la taille d'impression, lisibilité de la composition, colorimétrie adaptée au support.
- 9-10 = évident et fort sur le produit · 4-6 = passable, demande recadrage · 1-3 = inadapté.
- *Note* : le même visuel peut scorer 9 sur poster et 3 sur mug → scorer **par couple œuvre × produit**.

### Axe 4 — Espace concurrentiel / anti-saturation (25 %)
Combien de vendeurs sont déjà sur cette œuvre/ce thème ?
- **Sources** : nombre de listings Etsy/Amazon sur le mot-clé, nombre d'avis (proxy de volume), âge des boutiques dominantes.
- **Rubrique** : 9-10 = belle œuvre peu exploitée · 5-6 = thème porteur mais concurrencé · 1-3 = ultra-saturé (La Nuit étoilée, La Grande Vague de Hokusai, Le Baiser de Klimt — superbes mais invendables sans angle unique).

---

## 3. Décision

```
score_final = 0.30*momentum + 0.20*attribution + 0.25*traduisibilité + 0.25*espace_concurrentiel   (sur 10)

SI un gate échoue        → REJET (0)
SINON SI score_final ≥ 6.5 → PRODUIRE
SINON SI 5.0–6.4         → FILE D'ATTENTE (revoir avec un angle/produit différent)
SINON                    → REJET
```

Plafonner à N œuvres produites/semaine pour ne pas noyer le catalogue de SKU faibles (cf. logique du calculateur : c'est le hit-rate qui paie, pas le volume).

---

## 4. Trois exemples (dont un contre-intuitif)

| Œuvre | G1 | G2 | G3 | G4 | Mom. | Attr. | Trad. | Espace | Score | Décision |
|-------|----|----|----|----|------|-------|-------|--------|-------|----------|
| Planche de fougère, BHL, ~1880, 6000 px → **torchon** | ✓ | ✓ | ✓ | ✓ | 8 | 9 | 9 | 6 | **7,7** | ✅ Produire |
| Van Gogh, *Nuit étoilée* → **poster** | ✓ | ✓ | ✓ | ✓ | 6 | 9 | 9 | 1 | **5,6** | ⏸ File d'attente (saturé : besoin d'un angle) |
| Betty Boop 1930 → **mug** | ✓ | ✗ | — | — | — | — | — | — | **0** | ❌ Rejet (marque vivante) |

Le cas Betty Boop est pédagogique : « entrée dans le DP en 2026 » fait le buzz, donc momentum élevé et tentation forte… mais le gate marque la tue. C'est exactement le type d'erreur que le moteur doit empêcher automatiquement.

---

## 5. Prompt de scoring (à brancher sur l'API)

Puisque tu automatises avec Claude, voici un gabarit qui renvoie du JSON exploitable directement :

```
SYSTÈME : Tu es un expert en domaine public, en droit d'auteur (US 95 ans / UE vie+70)
et en marché de la déco POD. Tu évalues une œuvre candidate pour un produit donné.
Réponds UNIQUEMENT en JSON, sans préambule ni balises Markdown.

UTILISATEUR :
Œuvre : {titre, artiste, année_publication, année_décès_auteur, institution, licence, résolution_px}
Produit cible : {type Printful, taille}
Données concurrence : {nb_listings_etsy, nb_avis_moyens}
Signal tendance : {pinterest/google trends fournis}

Renvoie :
{
  "gates": {
    "dp_us": true/false, "dp_ue": true/false,
    "marque_residuelle": true/false,
    "source_propre": true/false,
    "resolution_ok": true/false,
    "rejet": true/false, "raison_rejet": "..."
  },
  "scores": { "momentum": 0-10, "attribution": 0-10,
              "traduisibilite": 0-10, "espace": 0-10 },
  "score_final": 0-10,
  "decision": "produire | file_attente | rejet",
  "angle_recommande": "si saturé, suggestion de traitement différenciant",
  "accroche_provenance": "1 phrase de storytelling pour la fiche produit"
}
```

Garder une **validation humaine sur les gates** au démarrage (surtout G1/G2), avant de faire confiance à l'automatisation complète.

---

## 6. Boucle de feedback (ce qui transforme le moteur en actif)

Réinjecter les ventes réelles : pour chaque œuvre produite, log du score prédit vs ventes obtenues. Tous les mois :
- Quel axe prédit le mieux les gagnants ? Réajuster les poids.
- Quels territoires esthétiques sur-performent ? Réorienter le sourcing.
- Affiner le seuil (6,5) selon le hit-rate observé dans le calculateur.

C'est cette boucle qui fait que ton système s'améliore au lieu de stagner — et c'est elle qui justifie l'investissement dans l'automation plutôt que la curation 100 % manuelle.

---

*Je ne suis ni avocat ni conseiller financier. Les règles de domaine public varient selon les pays et les cas (œuvres anonymes, posthumes, photographies) ont des durées spécifiques ; faire valider le gate G1/G2 par un spécialiste avant de passer à l'échelle.*
