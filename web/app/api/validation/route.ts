import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

// État de catalogue d'une œuvre de la galerie (Aperçus / collection.json), clé = `id`.
//  - status  : gate DP/marque HUMAIN — "valide" | "rejete" | null (à valider). Règle dure.
//  - active  : présence dans le CATALOGUE COMMERCIAL (en vente). Activable seulement si validée.
// Rien n'est publié sans validation humaine ; jamais automatisé.

const STATUTS = new Set(["valide", "rejete"]);

// GET /api/validation → map { [workId]: { status, active, note } }
export async function GET() {
  const rows = await db.curationDecision.findMany();
  const map: Record<string, { status: string | null; active: boolean; note: string | null }> = {};
  for (const r of rows) map[String(r.workId)] = { status: r.status, active: r.active, note: r.note };
  return NextResponse.json(map);
}

// POST /api/validation { workId, status?, active?, note? } → met à jour les champs fournis.
export async function POST(req: Request) {
  let body: { workId?: unknown; status?: unknown; active?: unknown; note?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "JSON invalide" }, { status: 400 });
  }
  const workId = Number(body.workId);
  if (!Number.isInteger(workId)) return NextResponse.json({ error: "workId entier requis" }, { status: 400 });

  const hasStatus = body.status !== undefined;
  const hasActive = body.active !== undefined;
  if (!hasStatus && !hasActive && body.note === undefined)
    return NextResponse.json({ error: "rien à mettre à jour (status, active ou note)" }, { status: 400 });

  const status = hasStatus ? (body.status === null ? null : String(body.status)) : undefined;
  if (status !== undefined && status !== null && !STATUTS.has(status))
    return NextResponse.json({ error: "status doit être 'valide', 'rejete' ou null" }, { status: 400 });
  const active = hasActive ? Boolean(body.active) : undefined;
  const note = body.note !== undefined ? (typeof body.note === "string" ? body.note.slice(0, 500) : null) : undefined;

  // Invariant : une œuvre rejetée (ou dé-validée) ne peut pas rester en vente.
  const update: { status?: string | null; active?: boolean; note?: string | null; decidedAt: Date } = { decidedAt: new Date() };
  if (status !== undefined) update.status = status;
  if (active !== undefined) update.active = active;
  if (note !== undefined) update.note = note;
  if (status === "rejete" || status === null) update.active = false;

  const row = await db.curationDecision.upsert({
    where: { workId },
    create: { workId, status: status ?? null, active: update.active ?? false, note: note ?? null },
    update,
  });
  return NextResponse.json({ workId: String(row.workId), status: row.status, active: row.active, note: row.note });
}

// DELETE /api/validation?workId=123 → annule tout (retour à « à valider », hors catalogue).
export async function DELETE(req: Request) {
  const workId = Number(new URL(req.url).searchParams.get("workId"));
  if (!Number.isInteger(workId)) return NextResponse.json({ error: "workId entier requis" }, { status: 400 });
  await db.curationDecision.deleteMany({ where: { workId } });
  return NextResponse.json({ ok: true });
}
