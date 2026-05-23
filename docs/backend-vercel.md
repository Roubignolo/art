# Backend production — Next.js + Vercel + Postgres

Le cockpit React livré est le **front-end**. Voici comment le brancher sur un vrai backend déployable. L'archi suit ce qu'on a défini : Vercel porte l'app + l'API + le cron ; Postgres et le stockage objet vivent à côté ; un worker traite la restauration lourde.

## Arborescence

```
provenance/
├─ app/
│  ├─ page.tsx                 ← le cockpit (le .jsx livré, porté en page Next)
│  ├─ api/
│  │  ├─ works/route.ts        ← CRUD œuvres (GET liste, POST import, PATCH update)
│  │  ├─ sourcing/route.ts     ← déclenche le sous-agent Sourcing (Met API)
│  │  ├─ scoring/route.ts      ← appelle Claude → JSON des 4 axes
│  │  └─ cron/route.ts         ← tâche planifiée (Vercel Cron)
├─ lib/
│  ├─ db.ts                    ← client Prisma
│  ├─ met.ts                   ← logique de sourcing (port du script Python)
│  └─ claude.ts                ← appel API Anthropic (scoring)
├─ prisma/schema.prisma        ← modèle de données
├─ vercel.json                 ← config cron
└─ .env                        ← clés (jamais commit)
```

## 1. Modèle de données (`prisma/schema.prisma`)

```prisma
datasource db { provider = "postgresql"; url = env("DATABASE_URL") }
generator client { provider = "prisma-client-js" }

model Work {
  id            Int      @id            // objectID du musée
  title         String
  artist        String?
  artistDeath   Int?
  date          String?
  department    String?
  medium        String?
  source        String   @default("The Met — Open Access (CC0)")
  imageUrl      String?
  localFile     String?                 // chemin dans le stockage objet
  resolutionPx  Int      @default(0)
  // gates
  gateUsSource  Boolean  @default(false)
  gateUe        Boolean?                 // null = à valider par un humain
  gateNoTm      Boolean  @default(true)
  // scoring
  momentum      Int      @default(5)
  attribution   Int      @default(5)
  translatab    Int      @default(5)
  competition   Int      @default(5)
  hook          String?                  // accroche provenance
  status        String   @default("gate") // source|gate|score|restore|publish
  collection    String?
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt
}

model Sale {                              // pour la boucle de feedback / KPIs
  id        Int      @id @default(autoincrement())
  workId    Int
  product   String
  amount    Float
  soldAt    DateTime @default(now())
}
```

## 2. Client base (`lib/db.ts`)

```ts
import { PrismaClient } from "@prisma/client";
export const db = globalThis.prisma ?? new PrismaClient();
if (process.env.NODE_ENV !== "production") globalThis.prisma = db;
```

## 3. API œuvres (`app/api/works/route.ts`)

```ts
import { db } from "@/lib/db";
import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json(await db.work.findMany({ orderBy: { updatedAt: "desc" } }));
}

export async function POST(req: Request) {          // import du registre Sourcing
  const works = await req.json();
  const created = await db.$transaction(
    works.map((w: any) => db.work.upsert({
      where: { id: w.objectID },
      update: {},
      create: {
        id: w.objectID, title: w.title, artist: w.artist, artistDeath: w.artist_death,
        date: w.object_date, department: w.department, medium: w.medium,
        imageUrl: w.image_url, resolutionPx: w.resolution_px,
        gateUsSource: w.gate_g1_us_g3, gateUe: w.gate_g1_ue, gateNoTm: w.gate_g2_marque,
      },
    }))
  );
  return NextResponse.json({ count: created.length });
}

export async function PATCH(req: Request) {          // valider gate, scorer, changer statut
  const { id, ...patch } = await req.json();
  return NextResponse.json(await db.work.update({ where: { id }, data: patch }));
}
```

## 4. Déclenchement du sourcing (`app/api/sourcing/route.ts`)

```ts
import { searchAndFilter } from "@/lib/met";   // port TS du script Python livré
import { db } from "@/lib/db";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const { theme = "botanical", target = 20 } = await req.json();
  const works = await searchAndFilter(theme, target);   // applique les gates + résolution
  await db.work.createMany({ data: works, skipDuplicates: true });
  return NextResponse.json({ imported: works.length });
}
```

## 5. Scoring via Claude (`lib/claude.ts`)

```ts
import Anthropic from "@anthropic-ai/sdk";
const anthropic = new Anthropic();

export async function scoreWork(work: any, signals: any) {
  const msg = await anthropic.messages.create({
    model: "claude-opus-4-7",
    max_tokens: 600,
    system: "Tu es expert domaine public + marché POD déco. Réponds UNIQUEMENT en JSON.",
    messages: [{ role: "user", content: JSON.stringify({ work, signals }) }],
  });
  return JSON.parse(msg.content[0].text);   // { scores, score_final, decision, hook }
}
```

## 6. Cron (`vercel.json`)

```json
{ "crons": [{ "path": "/api/cron", "schedule": "0 6 * * *" }] }
```
Le cron du matin : lance le sourcing du jour, score les nouvelles œuvres, met à jour les KPIs. La **validation des gates DP reste manuelle** dans le cockpit (jamais automatisée).

## 7. Restauration (worker séparé)

Les fonctions Vercel ont une limite de durée → le traitement d'images (nanobanana, upscale) tourne hors Vercel : une file de jobs (ex. Upstash QStash) déclenche un service conteneurisé (Railway, Fly.io, ou un endpoint GPU). Le worker lit l'œuvre, restaure, dépose le fichier dans le stockage objet (R2/S3), puis repasse le statut à `restore` via l'API.

## Stack & coûts de démarrage

| Brique | Service | Coût début |
|--------|---------|-----------|
| App + API + Cron | **Vercel** (Hobby/Pro) | gratuit → 20 $/mo |
| Base Postgres | **Neon** ou **Supabase** | gratuit au début |
| Stockage masters | **Cloudflare R2** | quasi nul |
| File de jobs | **Upstash QStash** | gratuit au début |
| Worker restauration | **Railway / Fly.io** | ~5 $/mo |

## Déploiement

```bash
npx create-next-app provenance && cd provenance
npm i @prisma/client @anthropic-ai/sdk && npm i -D prisma
npx prisma init && npx prisma db push          # crée les tables
# coller le cockpit livré dans app/page.tsx, remplacer window.storage par fetch('/api/works')
vercel                                          # déploie
```

Le seul changement côté front : remplacer les appels `store.get/set` par des `fetch("/api/works")`. Toute la logique (gates, scoring, viabilité) est déjà écrite dans le cockpit et se transpose telle quelle.

---

*Démarre en local avec la persistance intégrée du cockpit pour valider l'usage, puis bascule sur ce backend quand tu veux du multi-appareil, des données partagées et le cron. Pas avant d'avoir prouvé le hit-rate en Phase 0.*
