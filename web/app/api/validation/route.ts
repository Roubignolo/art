import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

// Validation HUMAINE du gate DP/marque des œuvres de la galerie (Aperçus / collection.json).
// Règle dure : rien n'est publié sans cette décision humaine ; ce n'est jamais automatisé.
// La clé `workId` = champ `id` de collection.json (objectID musée).

const STATUTS = new Set(["valide", "rejete"]);

// GET /api/validation → map { [workId]: { status, note, decidedAt } }
export async function GET() {
  const rows = await db.curationDecision.findMany();
  const map: Record<string, { status: string; note: string | null; decidedAt: string }> = {};
  for (const r of rows) map[String(r.workId)] = { status: r.status, note: r.note, decidedAt: r.decidedAt.toISOString() };
  return NextResponse.json(map);
}

// POST /api/validation { workId, status: "valide"|"rejete", note? } → upsert la décision.
export async function POST(req: Request) {
  let body: { workId?: unknown; status?: unknown; note?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "JSON invalide" }, { status: 400 });
  }
  const workId = Number(body.workId);
  const status = String(body.status ?? "");
  const note = typeof body.note === "string" ? body.note.slice(0, 500) : null;
  if (!Number.isInteger(workId)) return NextResponse.json({ error: "workId entier requis" }, { status: 400 });
  if (!STATUTS.has(status)) return NextResponse.json({ error: "status doit être 'valide' ou 'rejete'" }, { status: 400 });

  const row = await db.curationDecision.upsert({
    where: { workId },
    create: { workId, status, note },
    update: { status, note, decidedAt: new Date() },
  });
  return NextResponse.json({ workId: String(row.workId), status: row.status, note: row.note, decidedAt: row.decidedAt.toISOString() });
}

// DELETE /api/validation?workId=123 → annule la décision (retour à « à valider »).
export async function DELETE(req: Request) {
  const workId = Number(new URL(req.url).searchParams.get("workId"));
  if (!Number.isInteger(workId)) return NextResponse.json({ error: "workId entier requis" }, { status: 400 });
  await db.curationDecision.deleteMany({ where: { workId } });
  return NextResponse.json({ ok: true });
}
