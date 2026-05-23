import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { toWorkUpsert, type SourcingRecord } from "@/lib/works";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

// GET /api/works — liste complète (Phase 0 : volume faible, pas de pagination).
export async function GET() {
  const works = await db.work.findMany({ orderBy: { updatedAt: "desc" } });
  return NextResponse.json(works);
}

// POST /api/works — import du registre brut produit par le sourcing.
// Body : tableau de SourcingRecord (sortie de agents/sourcing_agent.py).
export async function POST(req: Request) {
  const body = await req.json();
  if (!Array.isArray(body)) {
    return NextResponse.json({ error: "Body doit être un tableau d'œuvres." }, { status: 400 });
  }
  const records = body as SourcingRecord[];
  const eligible = records.filter((r) => (r.decision ?? "").toUpperCase() !== "REJET");

  const ops = eligible.map((r) => db.work.upsert(toWorkUpsert(r)));
  const result = await db.$transaction(ops);

  return NextResponse.json({
    imported:  result.length,
    skipped:   records.length - eligible.length,
    received:  records.length,
  });
}

// PATCH /api/works — met à jour une œuvre (gate, scoring, statut, hook, angle).
// Body : { id, ...patch }
export async function PATCH(req: Request) {
  const body = await req.json();
  const id = Number(body?.id);
  if (!id) return NextResponse.json({ error: "id manquant" }, { status: 400 });
  const { id: _drop, ...patch } = body as Record<string, unknown>;

  // Recalcule scoreFinal côté serveur si les 4 axes sont présents/mis à jour.
  const existing = await db.work.findUnique({ where: { id } });
  if (!existing) return NextResponse.json({ error: "Œuvre introuvable" }, { status: 404 });

  const merged: Record<string, unknown> = { ...existing, ...patch };
  const num = (k: string, fb: number) => {
    const v = merged[k];
    return typeof v === "number" ? v : fb;
  };
  const sf =
    0.30 * num("momentum",    5) +
    0.20 * num("attribution", 5) +
    0.25 * num("translatab",  5) +
    0.25 * num("competition", 5);

  const updated = await db.work.update({
    where: { id },
    data: { ...(patch as Record<string, unknown>), scoreFinal: Math.round(sf * 100) / 100 } as never,
  });
  return NextResponse.json(updated);
}

// DELETE /api/works?id=123 — supprime une œuvre (et ses ventes en cascade).
export async function DELETE(req: Request) {
  const url = new URL(req.url);
  const id = Number(url.searchParams.get("id"));
  if (!id) return NextResponse.json({ error: "id manquant" }, { status: 400 });
  await db.work.delete({ where: { id } });
  return NextResponse.json({ deleted: id });
}
