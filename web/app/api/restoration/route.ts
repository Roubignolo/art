import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const maxDuration = 30;

// POST /api/restoration — Lance la restauration HD d'une œuvre.
// Body : { id, scale?: 2|4 }
//
// Deux chemins :
//  • REPLICATE_API_TOKEN présent → super-résolution Real-ESRGAN (cloud), retourne
//    l'id de prédiction à poller (ou à recevoir via webhook).
//  • Sinon → 202 + commande du moteur LOCAL (Pillow, zéro coût) à exécuter :
//    `python -m agents.render --met-id <id> --out web/public/renders/<id>`
//    Le moteur local fait déjà rognage + colorimétrie + accentuation + upscale Lanczos.

type Body = { id?: number; scale?: number };

const REAL_ESRGAN_VERSION =
  "f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa";

export async function POST(req: Request) {
  const body = (await req.json().catch(() => ({}))) as Body;
  if (!body?.id) return NextResponse.json({ error: "id manquant" }, { status: 400 });

  const work = await db.work.findUnique({ where: { id: Number(body.id) } });
  if (!work) return NextResponse.json({ error: "Œuvre introuvable" }, { status: 404 });
  if (!work.imageUrl) {
    return NextResponse.json({ error: "image_url manquante — sourcing incomplet" }, { status: 422 });
  }

  const token = process.env.REPLICATE_API_TOKEN;
  const scale = body.scale === 2 ? 2 : 4;

  if (!token) {
    return NextResponse.json(
      {
        mode: "local",
        message: "Aucune clé Replicate — utiliser le moteur de rendu LOCAL (gratuit).",
        commande: `python -m agents.render --met-id ${work.id} --out web/public/renders/${work.id}`,
        note: "Le moteur local applique rognage des bords, colorimétrie, accentuation, upscale Lanczos, puis génère la galerie (10 visuels) + carte de provenance.",
      },
      { status: 202 },
    );
  }

  try {
    const r = await fetch("https://api.replicate.com/v1/predictions", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        version: REAL_ESRGAN_VERSION,
        input: { image: work.imageUrl, scale, face_enhance: false },
      }),
    });
    const data = (await r.json()) as { id?: string; status?: string; urls?: { get?: string }; error?: string };
    if (!r.ok) return NextResponse.json({ error: `Replicate HTTP ${r.status}`, detail: data }, { status: 502 });
    return NextResponse.json({
      mode: "replicate",
      predictionId: data.id,
      status: data.status,
      pollUrl: data.urls?.get,
      note: "Poller pollUrl jusqu'à status=succeeded, puis téléverser la sortie comme master print.",
    });
  } catch (e) {
    return NextResponse.json({ error: "Échec Replicate", detail: String(e) }, { status: 502 });
  }
}
