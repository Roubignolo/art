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

## Pipeline de restauration
1. **rognage** des bords (supprime le fond uni des scans de musée)
2. **équilibrage des blancs** (gray-world)
3. **autocontraste** doux (préserve hautes/basses lumières)
4. **débruitage** préservant les bords
5. **accentuation** (unsharp mask)
6. **upscale** → Real-ESRGAN (Replicate si `REPLICATE_API_TOKEN`) sinon Lanczos

## Bascule cloud (optionnelle)
- `REPLICATE_API_TOKEN` → super-résolution Real-ESRGAN.
- `DYNAMIC_MOCKUPS_API_KEY` + `FAL_KEY` → l'API `/api/mockup` du cockpit prend le relais
  (templates + hero shots Flux Pro Kontext). Sans clés, ce moteur local fait tout.

## Architecture (modules)
`perspective.py` (solveur 8×8 sans numpy) · `restoration.py` · `frames.py`
(moulures à coupe d'onglet) · `scenes.py` (intérieurs procéduraux) · `mockup.py`
(orchestrateur) · `provenance_card.py` (sceau + carte A6) · `typo.py` ·
`brand_assets.py` · `cli.py`.

Tests : `python -m unittest discover -s tests`.
