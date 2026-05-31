import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const maxDuration = 60;

// POST /api/mockup — Génère les mockups d'une œuvre (3 templates + 3 lifestyle IA).
// Body : { id, product?: "framed_a2_oak" | ..., scenes?: ["scandinavian", "wabi-sabi", ...] }
//
// Workflow hybride à 2 étages (cf. docs/process-vente-production.md §4) :
//   Étage 1 : Dynamic Mockups Pro (templates) — 3 mockups à ~$0.05 chacun
//   Étage 2 : Flux Pro Kontext sur fal.ai (lifestyle IA) + compositing — 3 mockups à ~$0.08 chacun
//
// Architecture prête, mais les appels externes sont stub-és pour le moment
// (à activer quand DYNAMIC_MOCKUPS_API_KEY et FAL_KEY sont en place).

type MockupRequest = {
  id: number;
  product?: string;
  scenes?: string[];
};

type MockupsByProduct = {
  [product: string]: {
    templates: string[];   // URLs des mockups Dynamic Mockups
    lifestyle: string[];   // URLs des mockups Flux Pro Kontext
    generatedAt: string;
  };
};

export async function POST(req: Request) {
  const body = (await req.json()) as MockupRequest;
  if (!body?.id) return NextResponse.json({ error: "id manquant" }, { status: 400 });

  const work = await db.work.findUnique({ where: { id: Number(body.id) } });
  if (!work) return NextResponse.json({ error: "Œuvre introuvable" }, { status: 404 });
  if (!work.imageUrl) {
    return NextResponse.json({ error: "image_url manquante sur l'œuvre — sourcing incomplet" }, { status: 422 });
  }

  const product = body.product || "framed_a2_oak";
  const scenes  = body.scenes || ["scandinavian", "wabi-sabi", "creative-bureau"];

  // Étage 1 — Dynamic Mockups (templates)
  // (TODO P3.2 : vrais appels API quand DYNAMIC_MOCKUPS_API_KEY configuré)
  let templates: string[] = [];
  if (process.env.DYNAMIC_MOCKUPS_API_KEY) {
    templates = await generateDynamicMockups(work.imageUrl, product);
  }

  // Étage 2 — Flux Pro Kontext (lifestyle IA)
  // (TODO P3.2 : vrais appels API quand FAL_KEY configuré)
  let lifestyle: string[] = [];
  if (process.env.FAL_KEY) {
    lifestyle = await generateLifestyleMockups(work.imageUrl, product, scenes);
  }

  // Si aucune clé n'est configurée : on renvoie l'image source en fallback ET on
  // pointe vers le MOTEUR LOCAL (Pillow, gratuit) qui génère la galerie complète
  // sans aucune clé (10 visuels + carte de provenance).
  if (templates.length === 0 && lifestyle.length === 0) {
    return NextResponse.json({
      warning: "Aucune clé mockup (DYNAMIC_MOCKUPS_API_KEY / FAL_KEY) — utiliser le moteur LOCAL gratuit.",
      commandeLocale: `python -m agents.render --met-id ${work.id} --out web/public/renders/${work.id}`,
      product,
      mockups: { templates: [work.imageUrl], lifestyle: [] },
    }, { status: 202 });
  }

  // Persiste dans work.mockups (merge avec produits existants)
  const existing = (work.mockups as MockupsByProduct | null) ?? {};
  const merged: MockupsByProduct = {
    ...existing,
    [product]: {
      templates,
      lifestyle,
      generatedAt: new Date().toISOString(),
    },
  };

  const updated = await db.work.update({
    where: { id: work.id },
    data: { mockups: merged },
  });

  return NextResponse.json({
    ok: true,
    product,
    templates: templates.length,
    lifestyle: lifestyle.length,
    work: updated,
  });
}

// ─────────────────────────── Appels externes (cloud) ───────────────────────────

// Templates Dynamic Mockups pré-configurés (uuids), depuis l'env (csv).
// Chaque template doit avoir un smart object dont on remplace l'asset par l'œuvre.
async function generateDynamicMockups(sourceUrl: string, _product: string): Promise<string[]> {
  const key = process.env.DYNAMIC_MOCKUPS_API_KEY!;
  const templateIds = (process.env.DYNAMIC_MOCKUPS_TEMPLATE_IDS || "")
    .split(",").map((s) => s.trim()).filter(Boolean);
  if (templateIds.length === 0) return [];

  const out: string[] = [];
  for (const mockupUuid of templateIds) {
    try {
      const r = await fetch("https://app.dynamicmockups.com/api/v1/renders", {
        method: "POST",
        headers: { "x-api-key": key, "Content-Type": "application/json" },
        body: JSON.stringify({
          mockup_uuid: mockupUuid,
          export_options: { image_format: "jpg", image_size: 1500 },
          smart_objects: [{ uuid: "auto", asset: { url: sourceUrl } }],
        }),
      });
      const data = (await r.json()) as { data?: { export_path?: string } };
      if (r.ok && data?.data?.export_path) out.push(data.data.export_path);
    } catch {
      // on continue : un template qui échoue ne bloque pas les autres
    }
  }
  return out;
}

// Prompts lifestyle par scène (alignés sur les scènes du moteur local).
const SCENE_PROMPTS: Record<string, string> = {
  scandinavian:
    "framed art print hanging on a warm chalk-white wall, scandinavian living room, light oak floor, soft natural side light, eucalyptus branch, editorial interior photography, photorealistic",
  "wabi-sabi":
    "framed art print on a warm clay plaster wall, wabi-sabi interior, wooden console, raking warm light, minimal, photorealistic editorial photography",
  "creative-bureau":
    "framed art print on a gallery wall above a wooden desk, creative studio, natural daylight, photorealistic editorial interior",
  galerie:
    "framed art print centered on a soft chalk wall, museum gallery lighting, photorealistic editorial photography",
};

// fal.ai Flux Pro Kontext — API en file d'attente : submit → poll → image.
async function falKontext(prompt: string, imageUrl: string): Promise<string | null> {
  const key = process.env.FAL_KEY!;
  try {
    const submit = await fetch("https://queue.fal.run/fal-ai/flux-pro/kontext", {
      method: "POST",
      headers: { Authorization: `Key ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, image_url: imageUrl, guidance_scale: 3.5, num_images: 1 }),
    });
    const sub = (await submit.json()) as { status_url?: string; response_url?: string };
    if (!submit.ok || !sub.status_url) return null;

    // poll (max ~45s, en deçà de maxDuration=60)
    for (let i = 0; i < 22; i++) {
      await new Promise((res) => setTimeout(res, 2000));
      const st = await fetch(sub.status_url, { headers: { Authorization: `Key ${key}` } });
      const stData = (await st.json()) as { status?: string };
      if (stData.status === "COMPLETED") break;
      if (stData.status === "FAILED") return null;
    }
    const resp = await fetch(sub.response_url!, { headers: { Authorization: `Key ${key}` } });
    const data = (await resp.json()) as { images?: Array<{ url?: string }> };
    return data?.images?.[0]?.url ?? null;
  } catch {
    return null;
  }
}

async function generateLifestyleMockups(
  sourceUrl: string,
  _product: string,
  scenes: string[],
): Promise<string[]> {
  const out: string[] = [];
  for (const scene of scenes) {
    const prompt = SCENE_PROMPTS[scene] || SCENE_PROMPTS.galerie;
    const url = await falKontext(prompt, sourceUrl);
    if (url) out.push(url);
  }
  return out;
}
