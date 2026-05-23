import { NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const SYSTEM_PROMPT =
  "Tu es un expert en domaine public (US 95 ans / UE vie+70), en tendances déco " +
  "(Pinterest/Instagram/Etsy) et en marché POD. On te fournit une œuvre déjà " +
  "validée sur les gates DP/marque/source/résolution et un produit cible. " +
  "Tu dois UNIQUEMENT estimer deux axes : " +
  "(a) momentum esthétique (l'esthétique/thème monte-t-il dans la déco mainstream ?), " +
  "(b) espace concurrentiel (cette œuvre est-elle saturée sur Etsy/Amazon ?). " +
  "Puis proposer un angle différenciant si saturé et une accroche de provenance " +
  "(1 phrase, ton premium et factuel). Réponds en JSON strict, sans Markdown. " +
  'Schéma : {"momentum": 0-10, "competition": 0-10, "angle": "...", "hook": "..."}';

type LlmScore = { momentum?: number; competition?: number; angle?: string; hook?: string };

// POST /api/scoring — body : { id, product }
// Score une œuvre via Claude pour les axes "momentum" et "competition",
// persiste les axes + accroche + angle, et renvoie l'œuvre mise à jour.
export async function POST(req: Request) {
  if (!process.env.ANTHROPIC_API_KEY) {
    return NextResponse.json(
      { error: "ANTHROPIC_API_KEY non configurée. Le scoring LLM est désactivé." },
      { status: 503 },
    );
  }

  const { id, product = "poster" } = await req.json();
  if (!id) return NextResponse.json({ error: "id manquant" }, { status: 400 });

  const work = await db.work.findUnique({ where: { id: Number(id) } });
  if (!work) return NextResponse.json({ error: "Œuvre introuvable" }, { status: 404 });

  const userMsg =
    `Œuvre :\n` +
    `  - titre : ${work.title}\n` +
    `  - artiste : ${work.artist ?? "—"} ${work.artistBio ?? ""}\n` +
    `  - date : ${work.objectDate ?? "—"}\n` +
    `  - classification : ${work.classification ?? "—"}\n` +
    `  - médium : ${work.medium ?? "—"}\n` +
    `  - département : ${work.department ?? "—"}\n` +
    `  - source : ${work.source}\n` +
    `Produit cible : ${product}`;

  const client = new Anthropic();
  const msg = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 400,
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content: userMsg }],
  });

  const raw = msg.content
    .map((b) => ("text" in b ? b.text : ""))
    .join("")
    .trim()
    .replace(/^```(?:json)?\s*/i, "")
    .replace(/```$/i, "")
    .trim();

  let est: LlmScore;
  try {
    est = JSON.parse(raw);
  } catch {
    return NextResponse.json({ error: "Réponse Claude non parseable", raw }, { status: 502 });
  }

  const momentum    = clamp(est.momentum, work.momentum);
  const competition = clamp(est.competition, work.competition);
  const sf =
    0.30 * momentum +
    0.20 * work.attribution +
    0.25 * work.translatab +
    0.25 * competition;

  const updated = await db.work.update({
    where: { id: work.id },
    data: {
      momentum,
      competition,
      scoreFinal: Math.round(sf * 100) / 100,
      hook:  est.hook  ?? work.hook,
      angle: est.angle ?? work.angle,
      status: work.status === "gate" ? "score" : work.status,
    },
  });
  return NextResponse.json(updated);
}

function clamp(n: unknown, fallback: number): number {
  const v = Number(n);
  if (Number.isNaN(v)) return fallback;
  return Math.max(0, Math.min(10, Math.round(v)));
}
