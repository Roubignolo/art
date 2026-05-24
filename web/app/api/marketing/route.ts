import { NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const maxDuration = 60;

const SUPPORTED_LOCALES = ["fr", "en", "de", "it", "es"] as const;
type Locale = (typeof SUPPORTED_LOCALES)[number];

const LOCALE_NAMES: Record<Locale, string> = {
  fr: "français",
  en: "anglais",
  de: "allemand",
  it: "italien",
  es: "espagnol",
};

const SYSTEM_PROMPT = `Tu es expert en copywriting déco/art premium et en SEO marketplace (Etsy, Amazon).
On te donne une œuvre du DOMAINE PUBLIC reproduite à la demande (print-on-demand).
Tu écris la fiche produit dans plusieurs langues, ton premium et factuel — JAMAIS racoleur,
JAMAIS de superlatifs vides ("magnifique", "exceptionnel"). Tu valorises la provenance
(institution, artiste, époque) parce que c'est la différenciation marque.

Règles dures :
- Ne dis JAMAIS "made by" / "fait par" — l'œuvre n'est pas créée par le vendeur. Utilise
  "issu de la collection de…", "tiré du fonds du…", "sourced from…" selon la langue.
- N'invente PAS de détails (couleurs précises, anecdotes, prix) qui ne sont pas fournis.
- Reste sobre, élégant, factuel.

Réponds UNIQUEMENT en JSON strict, sans Markdown, sans préambule, sans commentaires.`;

type Marketing = {
  title: string;
  listingTitle: string;
  description: string;
  hook: string;
  tags: string[];
};

// POST /api/marketing — body : { id, locales? }
// Génère le contenu marketing multilingue pour une œuvre via Claude,
// stocke le résultat dans work.marketing et renvoie l'œuvre mise à jour.
export async function POST(req: Request) {
  if (!process.env.ANTHROPIC_API_KEY) {
    return NextResponse.json(
      { error: "ANTHROPIC_API_KEY non configurée." },
      { status: 503 },
    );
  }

  const body = await req.json();
  const id = Number(body?.id);
  if (!id) return NextResponse.json({ error: "id manquant" }, { status: 400 });

  const requested = Array.isArray(body?.locales) ? (body.locales as string[]) : SUPPORTED_LOCALES;
  const locales = requested.filter((l): l is Locale => (SUPPORTED_LOCALES as readonly string[]).includes(l));
  if (locales.length === 0) {
    return NextResponse.json({ error: "Aucune locale supportée demandée." }, { status: 400 });
  }

  const work = await db.work.findUnique({ where: { id } });
  if (!work) return NextResponse.json({ error: "Œuvre introuvable" }, { status: 404 });

  const localesPretty = locales.map((l) => `${l} (${LOCALE_NAMES[l]})`).join(", ");
  const schemaHint = locales
    .map(
      (l) =>
        `"${l}": { "title": "...", "listingTitle": "...", "description": "...", "hook": "...", "tags": [...] }`,
    )
    .join(",\n  ");

  const userMsg =
    `Œuvre source :\n` +
    `  - titre original : ${work.title}\n` +
    `  - artiste : ${work.artist ?? "anonyme"}${work.artistBio ? ` (${work.artistBio})` : ""}\n` +
    `  - date : ${work.objectDate ?? "—"}\n` +
    `  - classification : ${work.classification ?? "—"}\n` +
    `  - médium : ${work.medium ?? "—"}\n` +
    `  - département : ${work.department ?? "—"}\n` +
    `  - source : ${work.source}\n` +
    `  - URL musée : ${work.objectUrl ?? "—"}\n\n` +
    `Langues à produire : ${localesPretty}.\n\n` +
    `Pour CHAQUE langue, génère :\n` +
    `  - title           : titre court vendeur, ≤ 45 caractères (sans le mot "print/affiche").\n` +
    `  - listingTitle    : titre Etsy long ≤ 130 caractères, optimisé SEO, inclut le type ` +
    `(Affiche/Print/Druck/Stampa/Lámina selon la langue), l'esthétique et l'artiste si connu.\n` +
    `  - description     : 2-3 phrases (≤ 320 caractères), qui est l'artiste, quand, pourquoi ` +
    `cette œuvre, ce qu'elle évoque — ton premium et sobre.\n` +
    `  - hook            : 1 phrase ≤ 110 caractères, accroche de provenance ("issu de la ` +
    `collection du…", équivalent dans la langue cible).\n` +
    `  - tags            : 10 mots-clés SEO en minuscules dans la langue cible, sans accents.\n\n` +
    `Schéma JSON STRICT à respecter :\n{\n  ${schemaHint}\n}`;

  const client = new Anthropic();
  const msg = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 2500,
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content: userMsg }],
  });

  const raw = msg.content
    .map((b) => ("text" in b ? b.text : ""))
    .join("")
    .trim()
    .replace(/^```(?:json)?\s*/i, "")
    .replace(/```$/i, "")
    .trim();

  let parsed: Record<string, Marketing>;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return NextResponse.json(
      { error: "Réponse Claude non parseable", raw: raw.slice(0, 400) },
      { status: 502 },
    );
  }

  // Garde uniquement les locales demandées et présentes dans la réponse, en assainissant.
  const sanitized: Record<string, Marketing> = {};
  for (const l of locales) {
    const v = parsed[l];
    if (!v) continue;
    sanitized[l] = {
      title:        String(v.title ?? "").slice(0, 80),
      listingTitle: String(v.listingTitle ?? "").slice(0, 160),
      description:  String(v.description ?? "").slice(0, 500),
      hook:         String(v.hook ?? "").slice(0, 160),
      tags:         Array.isArray(v.tags)
        ? v.tags.slice(0, 13).map((t) => String(t).toLowerCase().slice(0, 30))
        : [],
    };
  }

  // Merge avec le marketing déjà stocké (préserve les langues qu'on n'a pas régénérées).
  const existing = (work.marketing as Record<string, Marketing> | null) ?? {};
  const merged = { ...existing, ...sanitized };

  // Si le hook racine est vide ou qu'on régénère le français, on synchronise.
  const dataPatch: { marketing: typeof merged; hook?: string } = { marketing: merged };
  if (sanitized.fr?.hook && (!work.hook || locales.includes("fr"))) {
    dataPatch.hook = sanitized.fr.hook;
  }

  const updated = await db.work.update({
    where: { id },
    data: dataPatch,
  });
  return NextResponse.json(updated);
}
