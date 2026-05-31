import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { construireListing, type WorkLite } from "@/lib/etsy-listing";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const maxDuration = 30;

// POST /api/etsy/publish — Assemble et (optionnellement) publie un listing Etsy.
// Body : { id, locale?: "fr"|"en"|..., dryRun?: boolean }
//
// Sans ETSY_OAUTH_TOKEN + ETSY_SHOP_ID (ou dryRun=true) : renvoie le BROUILLON
// complet (preview) sans rien publier — c'est l'aperçu utilisé par le cockpit.
// Avec les credentials : crée un listing en brouillon (draft) sur la boutique.
//
// La publication réelle reste manuelle/validée (jamais auto avant gate DP humain).

type Body = { id?: number; locale?: string; dryRun?: boolean };

export async function POST(req: Request) {
  const body = (await req.json().catch(() => ({}))) as Body;
  if (!body?.id) return NextResponse.json({ error: "id manquant" }, { status: 400 });

  const work = await db.work.findUnique({ where: { id: Number(body.id) } });
  if (!work) return NextResponse.json({ error: "Œuvre introuvable" }, { status: 404 });

  // Garde-fou conformité : ne jamais publier si le gate DP UE n'est pas tranché.
  if (work.gateUe === null && !body.dryRun) {
    return NextResponse.json(
      { error: "Gate DP UE non validé (gateUe=null) — validation humaine requise avant publication." },
      { status: 422 },
    );
  }

  const locale = body.locale || "fr";
  const draft = construireListing(work as unknown as WorkLite, locale);

  const token = process.env.ETSY_OAUTH_TOKEN;
  const apiKey = process.env.ETSY_API_KEY;
  const shopId = process.env.ETSY_SHOP_ID;

  // Mode preview (par défaut tant que l'OAuth Etsy n'est pas posé)
  if (body.dryRun || !token || !apiKey || !shopId) {
    return NextResponse.json({
      mode: "preview",
      reason: !token || !apiKey || !shopId
        ? "Credentials Etsy absents (ETSY_OAUTH_TOKEN / ETSY_API_KEY / ETSY_SHOP_ID) — aperçu seul."
        : "dryRun demandé.",
      draft,
    });
  }

  // Publication réelle : création d'un listing en brouillon (draft).
  try {
    const form = new URLSearchParams();
    form.set("quantity", "999");
    form.set("title", draft.title);
    form.set("description", draft.description);
    form.set("price", String(draft.prixAffiche));
    form.set("who_made", draft.whoMade);
    form.set("when_made", draft.whenMade);
    form.set("taxonomy_id", process.env.ETSY_TAXONOMY_ID || "68887"); // Prints
    form.set("type", "physical");
    form.set("should_auto_renew", "true");
    draft.tags.forEach((t) => form.append("tags", t));
    draft.materials.forEach((m) => form.append("materials", m));

    const r = await fetch(`https://openapi.etsy.com/v3/application/shops/${shopId}/listings`, {
      method: "POST",
      headers: {
        "x-api-key": apiKey,
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: form.toString(),
    });
    const data = (await r.json()) as { listing_id?: number; error?: string };
    if (!r.ok) {
      return NextResponse.json({ error: `Etsy HTTP ${r.status}`, detail: data }, { status: 502 });
    }

    if (data.listing_id) {
      await db.work.update({
        where: { id: work.id },
        data: { etsyListingId: String(data.listing_id), status: "publish" },
      });
    }
    return NextResponse.json({ mode: "published", listingId: data.listing_id, draft });
  } catch (e) {
    return NextResponse.json({ error: "Échec publication Etsy", detail: String(e) }, { status: 502 });
  }
}
