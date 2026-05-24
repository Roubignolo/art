/**
 * Récupère les libellés officiels d'une œuvre du Met dans plusieurs langues
 * via Wikidata. Source faisant autorité — JAMAIS d'invention de traduction.
 *
 * Wikidata référence les œuvres du Metropolitan Museum of Art via la propriété
 * P3634 ("MMOA work ID"). Beaucoup d'œuvres célèbres y ont des labels
 * multilingues officiels (ex: "Irises" → "Les Iris" en français).
 *
 * Si l'œuvre n'est PAS dans Wikidata, ou si une langue donnée n'a PAS de
 * label, on renvoie `undefined` pour cette langue — l'appelant doit alors
 * garder le titre original tel quel (pas de paraphrase).
 */

import type { Locale } from "./locales";
import { SUPPORTED_LOCALES } from "./locales";

export type OfficialLabels = Partial<Record<Locale, string>> & {
  wikidataId?: string; // ex: "Q19911667"
};

const SPARQL_ENDPOINT = "https://query.wikidata.org/sparql";

/** Quote and escape a string for safe inclusion in a SPARQL VALUES clause. */
function sparqlString(s: string): string {
  return `"${s.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

function buildQuery(metId: number): string {
  const lines = SUPPORTED_LOCALES
    .map((l) => `  OPTIONAL { ?work rdfs:label ?${l} FILTER(LANG(?${l}) = "${l}") }`)
    .join("\n");
  const vars = SUPPORTED_LOCALES.map((l) => `?${l}`).join(" ");
  return `SELECT ?work ${vars} WHERE {
  ?work wdt:P3634 ${sparqlString(String(metId))}.
${lines}
}`;
}

type SparqlBinding = Record<string, { value: string }>;

/**
 * Interroge Wikidata. Renvoie `null` si l'œuvre n'a pas d'entrée Wikidata
 * (cas normal : œuvres mineures). Lève une erreur en cas de panne réseau.
 */
export async function fetchOfficialLabels(metId: number): Promise<OfficialLabels | null> {
  const url = `${SPARQL_ENDPOINT}?format=json&query=${encodeURIComponent(buildQuery(metId))}`;
  const r = await fetch(url, {
    headers: {
      Accept: "application/sparql-results+json",
      "User-Agent": "art-cockpit/0.1 (https://art-cockpit.vercel.app)",
    },
    // Wikidata est cacheable côté CDN, on ne force pas no-cache.
    next: { revalidate: 86400 }, // 24h
  });
  if (!r.ok) throw new Error(`Wikidata SPARQL ${r.status}`);
  const data = (await r.json()) as { results?: { bindings?: SparqlBinding[] } };
  const rows = data?.results?.bindings ?? [];
  if (rows.length === 0) return null;

  // Une œuvre peut techniquement avoir plusieurs entrées Wikidata (rare).
  // On prend la première, c'est suffisant pour notre usage Phase 0.
  const row = rows[0];
  const out: OfficialLabels = {};
  for (const l of SUPPORTED_LOCALES) {
    const v = row[l]?.value;
    if (v) out[l] = v;
  }
  const workUri = row.work?.value;
  if (workUri) {
    const m = workUri.match(/Q\d+$/);
    if (m) out.wikidataId = m[0];
  }
  return out;
}
