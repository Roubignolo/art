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

  // Si aucune clé n'est configurée, on renvoie l'URL Met telle quelle comme fallback
  // (avec un avertissement). Comme ça la fiche œuvre reste fonctionnelle.
  if (templates.length === 0 && lifestyle.length === 0) {
    return NextResponse.json({
      warning: "Aucune clé mockup configurée (DYNAMIC_MOCKUPS_API_KEY ou FAL_KEY) — fallback sur l'image source.",
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

// ─────────────────────────── Stubs des appels externes ───────────────────────────

async function generateDynamicMockups(_sourceUrl: string, _product: string): Promise<string[]> {
  // TODO P3.2 — implémentation réelle :
  // 1) POST https://app.dynamicmockups.com/api/v1/renders avec template_id + image_url
  // 2) Polling ou callback → récupérer les URLs des mockups générés
  // 3) Retourner 3 URLs
  // Pour l'instant on retourne un tableau vide : le front voit "templates: 0" et
  // sait qu'il manque la clé / config.
  return [];
}

async function generateLifestyleMockups(
  _sourceUrl: string,
  _product: string,
  _scenes: string[],
): Promise<string[]> {
  // TODO P3.2 — implémentation réelle :
  // Pour chaque scène :
  // 1) POST https://queue.fal.run/fal-ai/flux-pro/kontext/text-to-image avec
  //    image_url=sourceUrl + prompt="poster framed on wall, ${scene} interior, ..."
  // 2) Récupérer l'image générée
  // 3) Compositing PIL/Sharp : insérer l'œuvre HD dans le cadre via perspective warp
  // 4) Upload du résultat sur R2/S3 ou Vercel Blob → retourner l'URL
  return [];
}
