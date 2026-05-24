# `tests/fixtures/` — Jeux de données pour tester le pipeline

## `registre_provenance_sample.json`

Mini-registre de 4 œuvres au format de sortie de `agents/sourcing_agent.py`, conçu pour exercer **les 3 cas de décision** du pipeline sans avoir à lancer un vrai sourcing.

| objectID | Cas couvert                                  | Comportement attendu                                                          |
|----------|----------------------------------------------|--------------------------------------------------------------------------------|
| 437853   | `CANDIDAT` gates verts (Van Gogh, peinture)  | Importée, prête à scorer, badge selon score                                   |
| 339001   | `CANDIDAT` gates verts (Redouté, gravure)    | Importée, prête à scorer, idéale poster/torchon                               |
| 110055   | `REVIEW` (auteur anonyme, date UE inconnue)  | Importée avec `gateUe = null` → badge `À VALIDER`, boutons Valider/Rejeter   |
| 999001   | `REJET` (marque résiduelle simulée)          | **Filtrée à l'import** par `/api/works` POST (ne sera pas en DB)              |

### Usage

**Via le cockpit** (UI) :

1. Aller sur <https://art-cockpit.vercel.app> (auth `art` / `COCKPIT_PASSWORD`)
2. Onglet **Import** → coller le contenu de ce fichier → bouton **Importer le JSON**
3. L'écran bascule sur l'onglet Œuvres avec 3 entrées (la 4e est rejetée silencieusement)

**Via curl** (API directe) :

```bash
curl -u "art:$COCKPIT_PASSWORD" -X POST https://art-cockpit.vercel.app/api/works \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/registre_provenance_sample.json
# → {"imported":3,"skipped":1,"received":4}
```

**Via le scoring agent Python** (chaîne complète offline) :

```bash
python agents/scoring_agent.py -i tests/fixtures/registre_provenance_sample.json -p poster
# → tests/fixtures/registre_scoring_poster.json
```

### Convention pour ajouter d'autres fixtures

- Garder un nom suffixé par la nature : `_sample.json` (jeu minimal), `_small.json` (~10 œuvres), `_real.json` (sortie d'un vrai sourcing).
- Ne **jamais** committer de masters d'images (toujours `local_file: ""` dans les fixtures versionnés).
- Aligner sur le contrat `SourcingRecord` défini dans `web/lib/works.ts` — c'est ce que `/api/works` POST attend.
