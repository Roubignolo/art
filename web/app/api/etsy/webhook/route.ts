import { NextResponse } from "next/server";
import { createHmac, timingSafeEqual } from "node:crypto";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

// Webhook Etsy v3 (GA depuis 2025).
// Events : order.paid, order.canceled, order.shipped, order.delivered.
// Signature HMAC-SHA256 dans l'en-tête X-Etsy-Signature, clé `whsec_...` (base64-decodée).
//
// Doc : https://developers.etsy.com/documentation/essentials/webhooks/

function verifySignature(raw: string, signatureHeader: string | null): boolean {
  const secret = process.env.ETSY_WEBHOOK_SECRET;
  if (!secret || !signatureHeader) return false;
  // Etsy envoie soit "sha256=<hex>" soit le hex brut selon les versions
  const provided = signatureHeader.replace(/^sha256=/, "");
  const keyBytes = Buffer.from(secret.replace(/^whsec_/, ""), "base64");
  const computed = createHmac("sha256", keyBytes).update(raw).digest("hex");
  try {
    return timingSafeEqual(Buffer.from(provided, "hex"), Buffer.from(computed, "hex"));
  } catch {
    return false;
  }
}

type EtsyEvent = {
  event_type: "order.paid" | "order.canceled" | "order.shipped" | "order.delivered";
  resource_url: string; // ex: https://openapi.etsy.com/v3/.../receipts/{receipt_id}
  shop_id: number;
};

// POST /api/etsy/webhook — réception des événements de vente Etsy.
export async function POST(req: Request) {
  const raw = await req.text();
  const sig = req.headers.get("x-etsy-signature");

  if (process.env.ETSY_WEBHOOK_SECRET && !verifySignature(raw, sig)) {
    return NextResponse.json({ error: "Signature invalide" }, { status: 401 });
  }

  let event: EtsyEvent;
  try { event = JSON.parse(raw); }
  catch { return NextResponse.json({ error: "Body non JSON" }, { status: 400 }); }

  // En attendant d'avoir les tokens OAuth Etsy : on log l'événement et on crée
  // une Order draft à partir des infos minimales du payload. Le détail complet
  // sera fetch depuis resource_url une fois les tokens disponibles.
  console.log("[etsy/webhook]", event.event_type, event.resource_url);

  // Extrait le receipt_id de l'URL
  const receiptMatch = event.resource_url?.match(/receipts\/(\d+)/);
  if (!receiptMatch) {
    return NextResponse.json({ ok: true, note: "resource_url sans receipt_id" });
  }
  const receiptId = receiptMatch[1];

  if (event.event_type === "order.paid") {
    // Pour le moment, on ne peut pas appeler resource_url (pas de token OAuth).
    // On stocke un marqueur pour qu'un job futur enrichisse la commande.
    // Si l'order existe déjà, on l'ignore (idempotent).
    const existing = await db.order.findFirst({
      where: { marketplace: "etsy", marketplaceOrderId: receiptId },
    });
    if (existing) {
      return NextResponse.json({ ok: true, note: "Order déjà créée (idempotent)" });
    }
    return NextResponse.json({
      ok: true,
      note: "Order non créée — OAuth Etsy non configuré (P3.3). Webhook reçu et validé.",
      receiptId,
    });
  }

  // order.shipped / delivered / canceled : update du status
  const newStatus = {
    "order.shipped":   "shipped",
    "order.delivered": "delivered",
    "order.canceled":  "canceled",
  }[event.event_type];
  if (!newStatus) {
    return NextResponse.json({ ok: true, note: `Event ${event.event_type} ignoré` });
  }
  await db.order.updateMany({
    where: { marketplace: "etsy", marketplaceOrderId: receiptId },
    data: { status: newStatus },
  });
  return NextResponse.json({ ok: true, status: newStatus, receiptId });
}

// GET (utile pour Etsy webhook verification challenge si l'API en utilise un)
export async function GET() {
  return NextResponse.json({ ok: true, note: "Etsy webhook endpoint up" });
}
