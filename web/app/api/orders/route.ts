import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

// GET /api/orders — liste des commandes (les plus récentes en premier).
// Query params : ?status=paid|in_production|shipped|...  &provider=gelato|prodigi  &workId=N
export async function GET(req: Request) {
  const url = new URL(req.url);
  const status = url.searchParams.get("status") || undefined;
  const provider = url.searchParams.get("provider") || undefined;
  const workId = url.searchParams.get("workId");

  const orders = await db.order.findMany({
    where: {
      ...(status ? { status } : {}),
      ...(provider ? { provider } : {}),
      ...(workId ? { workId: Number(workId) } : {}),
    },
    include: { work: { select: { id: true, title: true, artist: true, imageUrl: true, line: true } } },
    orderBy: { createdAt: "desc" },
    take: 200,
  });
  return NextResponse.json(orders);
}

// POST /api/orders — création manuelle d'une commande (utile en test ou pour
// les ventes non capturées par webhook). En prod : c'est le webhook /api/etsy
// qui crée les orders, pas cette route.
export async function POST(req: Request) {
  const body = await req.json();
  if (!body?.workId || !body?.marketplaceOrderId || !body?.product) {
    return NextResponse.json({ error: "Champs requis : workId, marketplaceOrderId, product" }, { status: 400 });
  }
  const work = await db.work.findUnique({ where: { id: Number(body.workId) } });
  if (!work) return NextResponse.json({ error: "Œuvre introuvable" }, { status: 404 });

  // Routing automatique : si l'œuvre a une `line` définie, on l'utilise pour
  // décider du provider POD. Sinon, défaut Gelato (standard).
  const provider: "gelato" | "prodigi" = work.line === "signature" ? "prodigi" : "gelato";

  const order = await db.order.create({
    data: {
      workId:             work.id,
      marketplace:        body.marketplace || "etsy",
      marketplaceOrderId: String(body.marketplaceOrderId),
      provider,
      product:            String(body.product),
      quantity:           Number(body.quantity || 1),
      amount:             Number(body.amount || 0),
      currency:           String(body.currency || "EUR"),
      status:             "paid",
      customerName:       body.customerName ?? null,
      customerCountry:    body.customerCountry ?? null,
    },
  });
  return NextResponse.json(order, { status: 201 });
}
