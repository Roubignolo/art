import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

// Webhook Gelato. ⚠️ Gelato ne signe PAS en HMAC nativement (cf.
// docs/benchmark-pod-fournisseurs.md §7). Sécurisation via URL signée custom :
// dashboard Gelato → webhook → URL = https://art-cockpit.vercel.app/api/gelato/webhook?secret=XXX
// Le handler refuse toute requête sans le bon secret en query string.
//
// Events Gelato (cf. https://dashboard.gelato.com/docs/webhooks/) :
//   - order_status_updated
//   - order_item_status_updated
//   - order_item_tracking_code_updated

type GelatoEvent = {
  event:              string; // ex: "order_status_updated"
  orderId?:           string; // Gelato order id
  orderReferenceId?:  string; // notre référence (ex: etsy-receipt-12345)
  itemReferenceId?:   string;
  fulfillmentStatus?: string; // created | passed_to_print_provider | in_production | printed | shipped | delivered | canceled
  trackingCode?:      string;
  trackingUrl?:       string;
};

// Mapping Gelato → notre statut Order
function mapStatus(gelato: string | undefined): string | null {
  if (!gelato) return null;
  return {
    created:                  "in_production",
    passed_to_print_provider: "in_production",
    in_production:            "in_production",
    printed:                  "in_production",
    shipped:                  "shipped",
    delivered:                "delivered",
    canceled:                 "canceled",
  }[gelato] ?? null;
}

export async function POST(req: Request) {
  // 1) Sécurisation : secret en query string
  const url = new URL(req.url);
  const providedSecret = url.searchParams.get("secret");
  const expectedSecret = process.env.GELATO_WEBHOOK_SECRET;
  if (expectedSecret && providedSecret !== expectedSecret) {
    return NextResponse.json({ error: "Secret manquant ou invalide" }, { status: 401 });
  }

  // 2) Parse payload
  let event: GelatoEvent;
  try { event = await req.json(); }
  catch { return NextResponse.json({ error: "Body non JSON" }, { status: 400 }); }

  console.log("[gelato/webhook]", event.event, event.orderReferenceId, event.fulfillmentStatus);

  if (!event.orderReferenceId) {
    return NextResponse.json({ ok: true, note: "orderReferenceId absent — événement ignoré" });
  }

  // Extrait le receipt_id Etsy depuis "etsy-receipt-{id}"
  const m = event.orderReferenceId.match(/^etsy-receipt-(\d+)$/);
  if (!m) {
    return NextResponse.json({ ok: true, note: "Référence non-Etsy ignorée" });
  }
  const receiptId = m[1];

  // 3) Update l'Order correspondante
  const newStatus = mapStatus(event.fulfillmentStatus);
  const data: Record<string, unknown> = {};
  if (newStatus) data.status = newStatus;
  if (event.orderId) data.providerOrderId = event.orderId;
  if (event.trackingCode) data.trackingCode = event.trackingCode;
  if (event.trackingUrl) data.trackingUrl = event.trackingUrl;

  if (Object.keys(data).length === 0) {
    return NextResponse.json({ ok: true, note: "Pas de changement à appliquer" });
  }

  const result = await db.order.updateMany({
    where: { marketplace: "etsy", marketplaceOrderId: receiptId, provider: "gelato" },
    data,
  });
  return NextResponse.json({ ok: true, updated: result.count, status: newStatus });
}

export async function GET() {
  return NextResponse.json({ ok: true, note: "Gelato webhook endpoint up" });
}
