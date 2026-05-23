# `web/` — Cockpit Provenance (Next.js + Postgres)

Front-end de pilotage + API du projet **Art**. Porte le cockpit React livré (anciennement `cockpit/provenance-cockpit.jsx`) sur Next.js 15 + Prisma + Postgres, avec une protection HTTP Basic Auth pour le déploiement public.

## Stack

| Brique     | Choix                                              |
|-----------|----------------------------------------------------|
| Framework  | Next.js 15 (App Router, React 19, TypeScript)      |
| ORM        | Prisma 6                                           |
| Base       | PostgreSQL (Neon recommandé, free tier)            |
| LLM        | `@anthropic-ai/sdk` (scoring momentum/concurrence) |
| Auth       | HTTP Basic via `middleware.ts`                     |
| Hébergement| Vercel                                             |

## Démarrage local

```bash
# 1. Installer
cd web
npm install

# 2. Configurer la DB et le mot de passe
cp .env.example .env.local
# → ouvrir .env.local et remplir :
#   DATABASE_URL=postgresql://…    (créé sur https://neon.tech)
#   COCKPIT_PASSWORD=…             (mot de passe que tu veux taper dans le navigateur)
#   ANTHROPIC_API_KEY=…            (optionnel, sans clé le bouton "Scoring Claude" renvoie 503)

# 3. Créer les tables Postgres
npx prisma db push

# 4. Lancer
npm run dev
# → http://localhost:3000 (Basic Auth — user "art" / mot de passe configuré)
```

## Importer un registre depuis le sourcing Python

```bash
# Depuis la racine du repo
python agents/sourcing_agent.py
# Copie ensuite le contenu de collection_botanique/registre_provenance.json
# Dans le cockpit : onglet "Import" → coller → "Importer le JSON"
```

L'API filtre automatiquement les lignes `REJET` ; les `REVIEW` (date d'auteur inconnue) atterrissent dans le cockpit avec `gateUe = null` et un bouton "Valider DP" pour la décision humaine — conforme à la règle dure du projet (`CLAUDE.md`).

## Architecture

```
web/
├─ app/
│  ├─ page.tsx              ← cockpit (use client) — gates / scoring / viabilité
│  ├─ layout.tsx            ← layout racine
│  └─ api/
│     ├─ works/route.ts     ← CRUD œuvres (GET, POST import, PATCH update, DELETE)
│     └─ scoring/route.ts   ← scoring Claude (POST { id, product })
├─ lib/
│  ├─ db.ts                 ← client Prisma (singleton dev-safe)
│  └─ works.ts              ← adaptateur SourcingRecord → Prisma
├─ prisma/schema.prisma     ← Work + Sale
├─ middleware.ts            ← HTTP Basic Auth
├─ vercel.json              ← build avec prisma generate + db push
└─ .env.example             ← DATABASE_URL, COCKPIT_PASSWORD, ANTHROPIC_API_KEY
```

## Déploiement Vercel

### 1. Provisionner la base Neon (5 min, gratuit)

1. Aller sur <https://neon.tech>, créer un compte (GitHub OK).
2. Créer un projet (région : `eu-central-1` ou `eu-west-2` pour latence FR).
3. Copier la connection string "Pooled" (commence par `postgresql://…sslmode=require`).

### 2. Importer le repo sur Vercel

1. Aller sur <https://vercel.com/new>, importer `Roubignolo/art`.
2. **Root Directory** : `web` (important — le repo est un monorepo).
3. Framework Preset : `Next.js` (détecté).
4. Build & Output : laisser par défaut (le `vercel.json` du dossier prend le relais).

### 3. Variables d'environnement

Dans Settings → Environment Variables, ajouter :

| Nom                 | Valeur                                         | Environnement       |
|---------------------|------------------------------------------------|---------------------|
| `DATABASE_URL`      | Connection string Neon (Pooled)                | Production, Preview |
| `COCKPIT_PASSWORD`  | Un mot de passe long (`openssl rand -base64 24`)| Production, Preview |
| `ANTHROPIC_API_KEY` | Clé Anthropic — *optionnel*                    | Production          |

### 4. Déployer

Cliquer **Deploy**. Le build :
1. `prisma generate` (client TS)
2. `prisma db push` (crée les tables `Work` / `Sale` dans Neon)
3. `next build`

Premier accès → challenge HTTP Basic. Utilisateur : `art` (configurable via `COCKPIT_USER`), mot de passe : valeur de `COCKPIT_PASSWORD`.

## Endpoints API

| Méthode | Route               | Body / Query                         | Effet                                                  |
|---------|---------------------|--------------------------------------|--------------------------------------------------------|
| GET     | `/api/works`        | —                                    | Liste toutes les œuvres (triées par `updatedAt`)       |
| POST    | `/api/works`        | `SourcingRecord[]`                   | Upsert depuis le registre Python (filtre les REJET)    |
| PATCH   | `/api/works`        | `{ id, ...patch }`                   | Met à jour gates/scores/statut, recalcule `scoreFinal` |
| DELETE  | `/api/works?id=123` | —                                    | Supprime une œuvre + ses ventes                        |
| POST    | `/api/scoring`      | `{ id, product? }`                   | Scoring Claude (axes momentum/competition + hook/angle)|

## Sécurité

- Aucune valeur secrète n'est committée (`.env*` ignoré).
- Le middleware Basic Auth est actif **dès que `COCKPIT_PASSWORD` est défini**. Si tu veux un environnement de dev sans auth, ne définis simplement pas cette variable dans `.env.local`.
- L'API ne renvoie pas d'erreurs détaillées contenant des informations de schéma DB.

---

*Conforme aux règles dures de `CLAUDE.md` : pas de secrets en clair, validation humaine des gates DP/marque, attribution "sourced by" gérée côté affichage produit.*
