import { NextResponse } from "next/server";
import { getConnectorById, getConnectorStatus } from "@/lib/connectors";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

// POST /api/connectors/test/[id] — ping live un connecteur précis.
// Retourne { ok: bool, detail: string, durationMs: number }.
export async function POST(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const c = getConnectorById(id);
  if (!c) return NextResponse.json({ error: "Connecteur inconnu" }, { status: 404 });

  if (!c.test) {
    return NextResponse.json(
      { ok: false, detail: "Ce connecteur n'a pas de test live défini." },
      { status: 400 },
    );
  }

  const cfg = getConnectorStatus(c);
  if (cfg === "missing_key") {
    return NextResponse.json(
      { ok: false, detail: `Clés manquantes : ${c.requiredEnv.join(", ")}` },
      { status: 400 },
    );
  }

  const start = Date.now();
  try {
    const r = await c.test();
    return NextResponse.json({ ...r, durationMs: Date.now() - start });
  } catch (e) {
    const detail = e instanceof Error ? e.message : String(e);
    return NextResponse.json({ ok: false, detail, durationMs: Date.now() - start }, { status: 200 });
  }
}
