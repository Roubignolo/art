import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

// Webhook Prodigi : format CloudEvents v1.0.
// Doc : https://www.prodigi.com/print-api/docs/reference/#webhooks
// Type d'event : com.prodigi.order.status.stage.changed#{Stage}
//   Stage ∈ { InProgress, Complete, Cancelled }
//   + sous-événements de shipment via "com.prodigi.order.shipments.update"
//
// Sécurisation : Prodigi propose une URL signée via dashboard (secret en query).
// On gère aussi un check sur PRODIGI_WEBHOOK_SECRET.

type CloudEvent = {
  specversion: "1.0";
  type:        string;  // ex: "com.prodigi.order.status.stage.changed#InProgress"
  source:      string;  // URL du resource
  id:          string;
  time?:       string;
  data?: {
    order?: {
      id:                string;
      idempotencyKey?:   string;
      merchantReference?: string; // notre référence (etsy-receipt-12345)
      status?: {
        stage?:        string;
        issues?:       Array<{ description?: string }>;
      };
      shipments?: Array<{
        id?:          string;
        carrier?:     { name?: string };
        tracking?:    { number?: string; url?: string };
      }>;
    };
  };
};

function mapStatus(stage: string | undefined, type: string): string | null {
  if (type.includes("Cancelled")) return "canceled";
  if (type.includes("Complete")) return "shipped"; // Complete = a quitté l'usine
  if (stage === "InProgress") return "in_production";
  return null;
}

export async function POST(req: Request) {
  // 1) Sécurisation optionnelle via secret en query string
  const url = new URL(req.url);
  const providedSecret = url.searchParams.get("secret");
  const expectedSecret = process.env.PRODIGI_WEBHOOK_SECRET;
  if (expectedSecret && providedSecret !== expectedSecret) {
    return NextResponse.json({ error: "Secret manquant ou invalide" }, { status: 401 });
  }

  // 2) Parse CloudEvent
  let event: CloudEvent;
  try { event = await req.json(); }
  catch { return NextResponse.json({ error: "Body non JSON" }, { status: 400 }); }

  console.log("[prodigi/webhook]", event.type, event.data?.order?.merchantReference);

  const merchantRef = event.data?.order?.merchantReference;
  if (!merchantRef) {
    return NextResponse.json({ ok: true, note: "merchantReference absent — événement ignoré" });
  }

  const m = merchantRef.match(/^etsy-receipt-(\d+)$/);
  if (!m) return NextResponse.json({ ok: true, note: "Référence non-Etsy ignorée" });
  const receiptId = m[1];

  // 3) Calcul du diff
  const data: Record<string, unknown> = {};
  const newStatus = mapStatus(event.data?.order?.status?.stage, event.type);
  if (newStatus) data.status = newStatus;
  if (event.data?.order?.id) data.providerOrderId = event.data.order.id;

  // Shipment update : récupère tracking
  const ship = event.data?.order?.shipments?.[0];
  if (ship?.tracking?.number) data.trackingCode = ship.tracking.number;
  if (ship?.tracking?.url)    data.trackingUrl  = ship.tracking.url;

  // Issues éventuelles (erreurs production Prodigi)
  const issues = event.data?.order?.status?.issues;
  if (Array.isArray(issues) && issues.length > 0) {
    data.status = "error";
    data.errorMessage = issues.map((i) => i.description).filter(Boolean).join(" · ");
  }

  if (Object.keys(data).length === 0) {
    return NextResponse.json({ ok: true, note: "Pas de changement à appliquer" });
  }

  const result = await db.order.updateMany({
    where: { marketplace: "etsy", marketplaceOrderId: receiptId, provider: "prodigi" },
    data,
  });
  return NextResponse.json({ ok: true, updated: result.count, status: newStatus });
}

export async function GET() {
  return NextResponse.json({ ok: true, note: "Prodigi webhook endpoint up" });
}
