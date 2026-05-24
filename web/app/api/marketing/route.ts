import { NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { db } from "@/lib/db";
import { fetchOfficialLabels } from "@/lib/wikidata";
import { LOCALE_NAMES, SUPPORTED_LOCALES, type Locale } from "@/lib/locales";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const maxDuration = 60;

/**
 * Règle dure du projet : pas d'invention.
 * - Le `title` (et `listingTitle`) ne sont JAMAIS écrits par Claude. Pour
 *   chaque langue, on cherche le libellé officiel sur Wikidata via la
 *   propriété P3634 (MMOA work ID). Si présent → on l'utilise tel quel.
 *   Sinon → on garde le titre original (anglais Met) sans traduction.
 *   `titleSource` indique l'origine : "wikidata" ou "original".
 * - Pour `description`, `hook`, `tags` : Claude peut écrire en se basant
 *   UNIQUEMENT sur les faits fournis dans les métadonnées de l'œuvre.
 *   Le prompt système interdit explicitement d'inventer un fait
 *   (lieu, anecdote, raison, sentiment) qui n'est pas dans la source.
 */

const SYSTEM_PROMPT = `Tu es expert en copywriting déco/art premium et en SEO marketplace.
On te donne une œuvre du DOMAINE PUBLIC reproduite à la demande (print-on-demand).

RÈGLES DURES (non négociables) :
1. N'invente AUCUN fait : pas de lieu, pas d'anecdote, pas de sentiment, pas de
   raison de création, pas de nombre. Tu écris uniquement ce qui est attesté
   dans les métadonnées fournies (artiste, dates, classification, médium, source).
2. Ne traduis JAMAIS le titre de l'œuvre. Pour chaque langue, tu DOIS reprendre
   EXACTEMENT la valeur de titleByLocale fournie dans le contexte utilisateur.
3. Le listingTitle peut être enrichi avec le type de produit (Affiche, Print,
   Druck, Stampa, Lámina) et l'esthétique, mais doit contenir le title EXACT.
4. Ne dis JAMAIS "made by"/"créé par"/"par notre artiste" — l'œuvre est
   reproduite, pas créée. Utilise "issu de la collection de…", "tiré du fonds
   du…", "sourced from…" selon la langue.
5. Ton sobre, factuel, premium — pas de superlatifs vides.

Réponds UNIQUEMENT en JSON strict, sans Markdown, sans préambule, sans commentaires.`;

type MarketingItem = {
  title: string;
  listingTitle: string;
  description: string;
  hook: string;
  tags: string[];
  titleSource: "wikidata" | "original";
};

type MarketingDict = Record<string, MarketingItem>;

// POST /api/marketing — body : { id, locales? }
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
  const locales = requested.filter(
    (l): l is Locale => (SUPPORTED_LOCALES as readonly string[]).includes(l),
  );
  if (locales.length === 0) {
    return NextResponse.json({ error: "Aucune locale supportée demandée." }, { status: 400 });
  }

  const work = await db.work.findUnique({ where: { id } });
  if (!work) return NextResponse.json({ error: "Œuvre introuvable" }, { status: 404 });

  // 1) Source faisant autorité : Wikidata.
  let wikidata: Awaited<ReturnType<typeof fetchOfficialLabels>> = null;
  try {
    wikidata = await fetchOfficialLabels(work.id);
  } catch (e) {
    // Wikidata down → on continue avec uniquement le titre original.
    console.warn("Wikidata fetch failed:", (e as Error).message);
  }

  // 2) Construire le mapping titre → langue, et tracer la source.
  const titleByLocale: Record<Locale, { title: string; source: "wikidata" | "original" }> = {} as never;
  for (const l of locales) {
    const official = wikidata?.[l];
    titleByLocale[l] = official
      ? { title: official, source: "wikidata" }
      : { title: work.title, source: "original" };
  }

  // 3) Prompt Claude. On lui passe les titres déjà figés, il les recopie tels quels.
  const titleMap = locales
    .map((l) => `  - ${l}: ${JSON.stringify(titleByLocale[l].title)}  (${titleByLocale[l].source})`)
    .join("\n");

  const userMsg =
    `Œuvre source (métadonnées attestées) :\n` +
    `  - titre original : ${work.title}\n` +
    `  - artiste : ${work.artist ?? "anonyme"}${work.artistBio ? ` (${work.artistBio})` : ""}\n` +
    `  - date : ${work.objectDate ?? "—"}\n` +
    `  - classification : ${work.classification ?? "—"}\n` +
    `  - médium : ${work.medium ?? "—"}\n` +
    `  - département : ${work.department ?? "—"}\n` +
    `  - source : ${work.source}\n` +
    `  - URL musée : ${work.objectUrl ?? "—"}\n` +
    `  - URL Wikidata : ${wikidata?.wikidataId ? `https://www.wikidata.org/wiki/${wikidata.wikidataId}` : "non référencée"}\n\n` +
    `Titres OFFICIELS à utiliser tels quels (NE PAS MODIFIER, NE PAS TRADUIRE) :\n` +
    `${titleMap}\n\n` +
    `Langues à produire : ${locales.map((l) => `${l} (${LOCALE_NAMES[l]})`).join(", ")}.\n\n` +
    `Pour CHAQUE langue, génère :\n` +
    `  - title           : recopie EXACTEMENT la valeur de titleByLocale[langue]. Aucune modification.\n` +
    `  - listingTitle    : titre Etsy ≤ 130 chars, qui contient le title EXACT, enrichi du type ` +
    `(Affiche/Print/Druck/Stampa/Lámina selon la langue) et de 2-3 mots-clés esthétiques.\n` +
    `  - description     : 2-3 phrases (≤ 320 caractères), uniquement basée sur les faits ci-dessus.\n` +
    `  - hook            : 1 phrase ≤ 110 caractères, accroche de provenance ("issu de la ` +
    `collection du…", équivalent dans la langue cible).\n` +
    `  - tags            : 10 mots-clés SEO en minuscules dans la langue cible, sans accents.\n\n` +
    `Schéma JSON STRICT :\n` +
    `{\n` +
    locales
      .map(
        (l) =>
          `  "${l}": { "title": "...", "listingTitle": "...", "description": "...", "hook": "...", "tags": [...] }`,
      )
      .join(",\n") +
    `\n}`;

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

  let parsed: Record<string, Omit<MarketingItem, "titleSource">>;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return NextResponse.json(
      { error: "Réponse Claude non parseable", raw: raw.slice(0, 400) },
      { status: 502 },
    );
  }

  // 4) Override : on impose le titre Wikidata/original quoi qu'ait dit Claude.
  const sanitized: MarketingDict = {};
  for (const l of locales) {
    const v = parsed[l];
    if (!v) continue;
    const enforcedTitle = titleByLocale[l].title;
    let listingTitle = String(v.listingTitle ?? "").slice(0, 160);
    // Garantit que le titre exact apparaît bien dans le listing — sinon on le préfixe.
    if (!listingTitle.includes(enforcedTitle)) {
      listingTitle = `${enforcedTitle} — ${listingTitle}`.slice(0, 160);
    }
    sanitized[l] = {
      title: enforcedTitle,
      titleSource: titleByLocale[l].source,
      listingTitle,
      description: String(v.description ?? "").slice(0, 500),
      hook: String(v.hook ?? "").slice(0, 160),
      tags: Array.isArray(v.tags)
        ? v.tags.slice(0, 13).map((t) => String(t).toLowerCase().slice(0, 30))
        : [],
    };
  }

  // 5) Merge avec le marketing déjà stocké pour préserver les langues non régénérées.
  const existing = (work.marketing as MarketingDict | null) ?? {};
  const merged: MarketingDict = { ...existing, ...sanitized };

  const dataPatch: { marketing: MarketingDict; hook?: string } = { marketing: merged };
  if (sanitized.fr?.hook && (!work.hook || locales.includes("fr"))) {
    dataPatch.hook = sanitized.fr.hook;
  }

  const updated = await db.work.update({ where: { id }, data: dataPatch });
  return NextResponse.json(updated);
}
