import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const order = await db.order.findUnique({
    where: { id: Number(id) },
    include: { work: true },
  });
  if (!order) return NextResponse.json({ error: "Commande introuvable" }, { status: 404 });
  return NextResponse.json(order);
}

// PATCH /api/orders/[id] — update partiel (status, trackingCode, etc.)
// Utilisé par le cockpit (résolution manuelle d'un litige) ET par les webhooks.
export async function PATCH(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const body = await req.json();
  const allowed = [
    "status", "trackingCode", "trackingUrl", "providerOrderId",
    "errorMessage", "customerName", "customerCountry",
  ];
  const data: Record<string, unknown> = {};
  for (const k of allowed) if (k in body) data[k] = body[k];

  const updated = await db.order.update({ where: { id: Number(id) }, data });
  return NextResponse.json(updated);
}
