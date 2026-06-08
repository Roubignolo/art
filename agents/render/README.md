# Moteur de rendu — Vellum & Cie

Restauration + mockups + carte de provenance, **100 % local** (Pillow), **zéro clé requise**.
Bascule automatiquement sur des API cloud quand les clés sont posées.

## Pourquoi local d'abord
La qualité perçue d'une fiche Etsy se joue sur les visuels. Ce moteur produit
une galerie de **niveau galerie** sans aucun abonnement (Dynamic Mockups, fal.ai)
ni coût par image — exactement les 10 visuels qui remplissent les 10 slots Etsy.

## Usage

```bash
# Depuis un objet Met (métadonnées + image récupérées automatiquement)
python -m agents.render --met-id 436535 --out web/public/renders/436535

# Depuis une image locale / URL
python -m agents.render --image master.tif --out out/ \
  --titre "Wheat Field with Cypresses" --artiste "Vincent van Gogh"

# Assets de marque (bannière Etsy, icône, logo)
python -m agents.render.brand_assets --out web/public/brand
```

Options : `--profils chene,noir,blanc` · `--scenes galerie,scandinave,atelier`
· `--long-edge 4000` · `--no-restauration`.

## Ce qui est généré (12 fichiers)

| Fichier | Rôle |
|---|---|
| `master_restaure.jpg` | master restauré (web) |
| `avant_apres.jpg` | visuel « avant/après » (pilier marque) |
| `catalogue/01_poster_nu.jpg` | tirage nu sur mur neutre |
| `catalogue/02_encadre_*.jpg` | encadré (moulure + marie-louise + verre + ombre) |
| `catalogue/03_detail.jpg` | détail texture (finesse restauration) |
| `catalogue/04_cadres.jpg` | options de cadres côte à côte |
| `catalogue/05_tailles.jpg` | comparatif A4/A3/A2 à l'échelle |
| `lifestyle/{galerie,scandinave,atelier}.jpg` | scènes lifestyle (perspective + ombre) |
| `provenance_recto.png` / `provenance_verso.png` | carte A6 (insert physique) |
| `manifest.json` | inventaire + rapport de restauration |

## Pipeline de restauration — « fidélité d'abord »
Voir [`docs/restauration-politique.md`](../../docs/restauration-politique.md).
Un master de musée est **déjà** fidèle (mire + ICC) → on ne touche **pas** à la teinte.

**Profil `fidele` (défaut)** — n'altère pas la couleur :
1. **rognage** des bords (supprime le fond uni des scans de musée)
2. **débruitage** léger préservant les bords
3. **accentuation** (unsharp mask)
4. **upscale** → Real-ESRGAN (Replicate si `REPLICATE_API_TOKEN`) sinon Lanczos

**Profil `archive`** (opt-in, `--profil archive`) — scans NON calibrés / abîmés
seulement : ajoute balance des blancs + autocontraste **bornés**, sur décision
humaine. Jamais sur un fichier musée. `gray-world` global est proscrit.

## Audit de fidélité (garde-fou automatique)
Après chaque rendu, `fidelity.auditer_fidelite` compare le master à la source
(vérité terrain) en CIELAB / ΔE2000 et émet **FIDÈLE / À REVOIR / INFIDÈLE**
(inscrit au `manifest.json`, surfacé dans le cockpit). Détecte la dérive couleur,
la neutralisation d'une dominante voulue (signature gray-world) et le délavage.
Né de l'incident Cézanne : le gray-world délavait le bleu volontaire de la nappe.

## Gestion couleur (ICC) — `couleur.py`
La « correction » légitime, à l'inverse du gray-world : transporter fidèlement
l'apparence vers l'espace imprimeur.
- **`assurer_srgb`** : garantit le **sRGB** de livraison (Gelato/Prodigi). Si la source
  porte un profil ≠ sRGB (Adobe RGB…), conversion ICC relatif-colorimétrique + BPC.
  Fichiers livrés **tagués sRGB**. On ne pré-convertit PAS en CMYK : le RIP du POD mappe.
- **`rapport_gamut`** : soft-proof **informatif** (jamais une correction). Avec
  `--profil-papier <icc>` (Hahnemühle/Prodigi) → vrai soft-proof ICC (% hors-gamut) ;
  sinon → pré-écran chroma approximatif. Aide au choix du papier (mat < baryté/toile).

## Bascule cloud (optionnelle)
- `REPLICATE_API_TOKEN` → super-résolution Real-ESRGAN.
- `DYNAMIC_MOCKUPS_API_KEY` + `FAL_KEY` → l'API `/api/mockup` du cockpit prend le relais
  (templates + hero shots Flux Pro Kontext). Sans clés, ce moteur local fait tout.

## Architecture (modules)
`perspective.py` (solveur 8×8 sans numpy) · `restoration.py` · `couleur.py`
(gestion ICC + soft-proof) · `fidelity.py` (audit ΔE2000) · `frames.py`
(moulures à coupe d'onglet) · `scenes.py` (intérieurs procéduraux) · `mockup.py`
(orchestrateur) · `provenance_card.py` (sceau + carte A6) · `typo.py` ·
`brand_assets.py` · `cli.py`.

Tests : `python -m unittest discover -s tests`.
