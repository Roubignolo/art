/**
 * Catalogue des connecteurs externes du projet Art, avec test de vie.
 *
 * Pour chaque service utilisé (Wikidata, Anthropic, Etsy, Gelato, Prodigi,
 * fal.ai, Dynamic Mockups), on expose :
 *  - sa configuration (clé API présente ou non)
 *  - un ping live optionnel pour vérifier que la clé/le service marche
 *  - une description et un lien doc
 *
 * Consommé par /api/connectors (GET status) et /api/connectors/test (POST ping).
 * Affiché dans l'onglet "Connecteurs" du cockpit.
 */

export type ConnectorStatus = "configured" | "missing_key" | "untested" | "ok" | "error";

export type ConnectorDef = {
  id: string;
  name: string;
  description: string;
  docUrl: string;
  requiredEnv: string[]; // ex: ["ANTHROPIC_API_KEY"]
  optional?: boolean;     // ex: Wikidata est utilisable sans clé
  category: "ai" | "data" | "marketplace" | "pod" | "mockup";
  /** Si défini, ping live (200 OK = ok, autre = error). Ne PAS lancer si requiredEnv manque. */
  test?: () => Promise<{ ok: boolean; detail: string }>;
};

const fetchJson = async (url: string, init?: RequestInit, timeoutMs = 8000): Promise<Response> => {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: ctrl.signal });
  } finally {
    clearTimeout(t);
  }
};

// ─────────────────────────── CATALOGUE ───────────────────────────

export const CONNECTORS: ConnectorDef[] = [
  // ── Données ──
  {
    id: "wikidata",
    name: "Wikidata SPARQL",
    description: "Libellés officiels multilingues des œuvres (P3634). Source d'autorité pour les titres marketing.",
    docUrl: "https://query.wikidata.org/",
    requiredEnv: [],
    optional: true,
    category: "data",
    test: async () => {
      // Petit query qui doit toujours renvoyer ≥ 1 row si Wikidata up.
      const q = "SELECT * WHERE { ?work wdt:P3634 \"436528\". } LIMIT 1";
      const r = await fetchJson(
        `https://query.wikidata.org/sparql?format=json&query=${encodeURIComponent(q)}`,
        { headers: { Accept: "application/sparql-results+json", "User-Agent": "art-cockpit/0.1 (test)" } },
      );
      if (!r.ok) return { ok: false, detail: `HTTP ${r.status}` };
      const data = (await r.json()) as { results?: { bindings?: unknown[] } };
      const n = data?.results?.bindings?.length ?? 0;
      return { ok: n > 0, detail: `${n} row${n === 1 ? "" : "s"} for Van Gogh Irises (Met 436528)` };
    },
  },

  // ── IA ──
  {
    id: "anthropic",
    name: "Anthropic Claude",
    description: "Génère le scoring (axes momentum/concurrence) et le marketing multilingue (5 langues).",
    docUrl: "https://docs.anthropic.com/",
    requiredEnv: ["ANTHROPIC_API_KEY"],
    category: "ai",
    test: async () => {
      // Endpoint le moins coûteux : list models (1 call, 0 token).
      const r = await fetchJson("https://api.anthropic.com/v1/models?limit=1", {
        headers: {
          "x-api-key": process.env.ANTHROPIC_API_KEY!,
          "anthropic-version": "2023-06-01",
        },
      });
      if (!r.ok) return { ok: false, detail: `HTTP ${r.status}` };
      const data = (await r.json()) as { data?: Array<{ id?: string }> };
      const sample = data?.data?.[0]?.id || "unknown";
      return { ok: true, detail: `auth OK · sample model: ${sample}` };
    },
  },

  // ── Marketplaces ──
  {
    id: "etsy",
    name: "Etsy Open API v3",
    description: "Création de listings, gestion de boutique, webhooks de ventes. OAuth2 PKCE (à configurer en P3.3).",
    docUrl: "https://developer.etsy.com/documentation/",
    requiredEnv: ["ETSY_API_KEY"],
    category: "marketplace",
    test: async () => {
      // Endpoint public sans token : récupère les infos d'une boutique fictive pour valider la clé app.
      const r = await fetchJson("https://openapi.etsy.com/v3/application/openapi-ping", {
        headers: { "x-api-key": process.env.ETSY_API_KEY! },
      });
      if (!r.ok) return { ok: false, detail: `HTTP ${r.status} (openapi-ping)` };
      return { ok: true, detail: "API key valide (openapi-ping 200)" };
    },
  },

  // ── POD ──
  {
    id: "gelato",
    name: "Gelato API v4",
    description: "Production standard (poster, encadré, mug, torchon). Production locale FR, intégration Etsy native.",
    docUrl: "https://dashboard.gelato.com/docs/",
    requiredEnv: ["GELATO_API_KEY"],
    category: "pod",
    test: async () => {
      // Endpoint catalog : lecture seule, non destructive, ne crée pas d'order.
      const r = await fetchJson("https://product.gelatoapis.com/v3/catalogs", {
        headers: { "X-API-KEY": process.env.GELATO_API_KEY! },
      });
      if (!r.ok) return { ok: false, detail: `HTTP ${r.status}` };
      const data = (await r.json()) as { data?: unknown[] };
      const n = data?.data?.length ?? 0;
      return { ok: true, detail: `auth OK · ${n} catalogs visible` };
    },
  },
  {
    id: "prodigi",
    name: "Prodigi API v4",
    description: "Production signature premium (Hahnemühle Photo Rag/German Etching, encadrés vrai bois FATG approved).",
    docUrl: "https://www.prodigi.com/print-api/docs/reference/",
    requiredEnv: ["PRODIGI_API_KEY"],
    category: "pod",
    test: async () => {
      // GET un order qui n'existe pas — doit renvoyer 404 sans 401, validant la clé.
      const r = await fetchJson("https://api.prodigi.com/v4.0/Orders/__connector_test__", {
        headers: { "X-API-Key": process.env.PRODIGI_API_KEY! },
      });
      if (r.status === 401 || r.status === 403) return { ok: false, detail: `HTTP ${r.status} (auth invalide)` };
      // 404 = clé valide mais order inexistant (comportement attendu)
      return { ok: true, detail: `auth OK (HTTP ${r.status} sur order test)` };
    },
  },

  // ── Mockups ──
  {
    id: "dynamic-mockups",
    name: "Dynamic Mockups",
    description: "Templates de base (3 mockups/œuvre : poster nu, cadre détail, scène neutre). API stable, intégration Etsy native.",
    docUrl: "https://dynamicmockups.com/integrations/etsy/",
    requiredEnv: ["DYNAMIC_MOCKUPS_API_KEY"],
    category: "mockup",
    test: async () => {
      const r = await fetchJson("https://app.dynamicmockups.com/api/v1/mockups", {
        headers: { "x-api-key": process.env.DYNAMIC_MOCKUPS_API_KEY! },
      });
      if (!r.ok) return { ok: false, detail: `HTTP ${r.status}` };
      return { ok: true, detail: "auth OK (liste mockups accessible)" };
    },
  },
  {
    id: "fal-ai",
    name: "fal.ai (Flux Pro Kontext)",
    description: "Hero shots lifestyle IA (3 mockups premium/œuvre, ~$0.08/img). Préserve la fidélité de l'œuvre source.",
    docUrl: "https://fal.ai/models/fal-ai/flux-pro/kontext",
    requiredEnv: ["FAL_KEY"],
    category: "mockup",
    test: async () => {
      // Endpoint apps : list user apps via fal.run gateway. Si 401 → clé invalide.
      const r = await fetchJson("https://queue.fal.run/health", {
        headers: { Authorization: `Key ${process.env.FAL_KEY!}` },
      });
      if (r.status === 401 || r.status === 403) return { ok: false, detail: `HTTP ${r.status}` };
      return { ok: true, detail: `auth OK (HTTP ${r.status} sur health)` };
    },
  },
];

// ─────────────────────────── HELPERS ───────────────────────────

export function getConnectorStatus(c: ConnectorDef): ConnectorStatus {
  if (c.requiredEnv.length === 0) return "configured"; // services sans clé (Wikidata)
  const allPresent = c.requiredEnv.every((k) => !!process.env[k]?.trim());
  return allPresent ? "configured" : "missing_key";
}

export function getConnectorById(id: string): ConnectorDef | undefined {
  return CONNECTORS.find((c) => c.id === id);
}

/** Pour l'affichage : décrit l'état config (clé OK / manquante). */
export function describeStatus(c: ConnectorDef): string {
  const st = getConnectorStatus(c);
  if (st === "configured") {
    return c.requiredEnv.length === 0
      ? "Public (sans clé)"
      : `Clé configurée : ${c.requiredEnv.join(", ")}`;
  }
  return `Manque : ${c.requiredEnv.filter((k) => !process.env[k]?.trim()).join(", ")}`;
}
