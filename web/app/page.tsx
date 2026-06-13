"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import {
  Archive, LayoutGrid, ListChecks, Calculator, Upload, Check, X,
  ChevronRight, Tag, Image as ImageIcon, ShieldCheck, AlertTriangle,
  Sparkles, RefreshCw, Wand2, Languages, Plug, Package, Truck, ExternalLink,
} from "lucide-react";

/* ---------- Types ---------- */
type MarketingItem = {
  title: string;
  listingTitle: string;
  description: string;
  hook: string;
  tags: string[];
  titleSource?: "wikidata" | "original";
};

type MockupSet = { templates: string[]; lifestyle: string[]; generatedAt: string };

type ListingVariant = { sku: string; label: string; format: string; prix: number; margeNette: number; provider: string };
type ListingDraft = {
  locale: string; title: string; titleLength: number; titleWarning?: string;
  description: string; tags: string[]; materials: string[]; taxonomyHint: string;
  variants: ListingVariant[]; prixAffiche: number; galerieHint: string[]; conformite: string[];
};
type ListingResult = { workId: number; mode: string; reason?: string; draft: ListingDraft };

type PreviewWork = {
  id: number;
  title: string;
  artist: string | null;
  source?: string | null;
  dpEvidence?: string | null;
  wikidataUrl?: string | null;
  dir: string; // ex: "/renders/436965"
  encadre?: string | null; // chemin réel du mockup encadré (nom dépend du 1er profil)
  // Audit de fidélité colorimétrique (cf. agents/render/fidelity.py)
  fidelite?: { verdict: string; deltaE: number; chroma: number; dominante: number } | null;
  // Gestion couleur ICC (cf. agents/render/couleur.py)
  couleur?: { espaceSource: string | null; convertiSrgb: boolean | null } | null;
  gamut?: {
    methode: string | null; teinteARisque: string | null; chromaMax: number | null;
    pctChromaElevee: number | null; horsGamutPct: number | null; profilPapier: string | null;
  } | null;
  // Collections (cf. agents/tagging.py + agents/render/palette.py)
  tags?: { sujet: string[]; mouvement: string | null; palette: string[]; collections: string[] } | null;
  palette?: { tags: string[]; swatches: string[]; famille: string; chaleur: number } | null;
  // Mise en page produit — format catalogue fidèle au ratio (cf. agents/render/layout.py · web/lib/layout.ts)
  layout?: {
    taille: string; orientation: string; ratioOeuvre: number; bordurePct: number;
    variants: { taille: string; bordurePct: number }[];
  } | null;
  // Curation (cf. scripts/build_collections.py + docs/audit-rentabilite.md §T2)
  curation?: {
    deprioritized?: boolean; raison?: string;
    nouveau?: boolean; dpAValider?: boolean; source?: string;
  } | null;
};

type Work = {
  id: number;
  title: string;
  artist: string | null;
  artistBio: string | null;
  artistDeath: number | null;
  objectDate: string | null;
  department: string | null;
  classification: string | null;
  medium: string | null;
  dimensions: string | null;
  source: string;
  imageUrl: string | null;
  resolutionPx: number;
  gateUsSource: boolean;
  gateUe: boolean | null;
  gateNoTm: boolean;
  artistBirth: number | null;
  objectBeginYear: number | null;
  accessionNumber: string | null;
  rightsStatement: string | null;
  wikidataUrl: string | null;
  dpEvidence: string | null;
  momentum: number;
  attribution: number;
  translatab: number;
  competition: number;
  scoreFinal: number | null;
  hook: string | null;
  angle: string | null;
  marketing: Record<string, MarketingItem> | null;
  mockups: Record<string, MockupSet> | null;
  line: "standard" | "signature" | null;
  etsyListingId: string | null;
  status: string;
};

type Connector = {
  id: string;
  name: string;
  description: string;
  docUrl: string;
  category: "ai" | "data" | "marketplace" | "pod" | "mockup" | "render";
  status: "configured" | "missing_key" | "ok" | "error";
  configHint: string;
  requiredEnv: string[];
  hasTest: boolean;
  ordersLast30: number | null;
  // Champs locaux (résultat du dernier test live)
  lastTest?: { ok: boolean; detail: string; durationMs: number; at: string };
};

type Order = {
  id: number;
  workId: number;
  marketplace: string;
  marketplaceOrderId: string;
  provider: "gelato" | "prodigi";
  providerOrderId: string | null;
  product: string;
  quantity: number;
  amount: number;
  currency: string;
  status: string;
  trackingCode: string | null;
  trackingUrl: string | null;
  customerName: string | null;
  customerCountry: string | null;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
  work?: { id: number; title: string; artist: string | null; imageUrl: string | null; line: string | null };
};

type Config = {
  prix: number; port: number; base: number; coutDesign: number;
  designs: number; ventesGagnant: number; fixes: number; hitrate: number;
};

/* ---------- Constantes (alignées sur docs/moteur-scoring.md) ---------- */
const WEIGHTS = { momentum: 0.30, attribution: 0.20, translatab: 0.25, competition: 0.25 };
const THRESHOLD = 6.5;
const STAGES = [
  { key: "source",  label: "Sourcé",          icon: Archive },
  { key: "gate",    label: "Gate à valider",  icon: ShieldCheck },
  { key: "score",   label: "Scoré",           icon: Sparkles },
  { key: "restore", label: "Restauré",        icon: ImageIcon },
  { key: "publish", label: "Publié",          icon: Check },
];

const LOCALES = [
  { code: "fr", flag: "🇫🇷", label: "Français" },
  { code: "en", flag: "🇬🇧", label: "English" },
  { code: "de", flag: "🇩🇪", label: "Deutsch" },
  { code: "it", flag: "🇮🇹", label: "Italiano" },
  { code: "es", flag: "🇪🇸", label: "Español" },
] as const;

const DEFAULTS: Config = { prix: 25, port: 5, base: 16, coutDesign: 0.5, designs: 1000, ventesGagnant: 3, fixes: 150, hitrate: 5 };
const CFG_KEY = "provenance.cfg.v1";

function weighted(w: Work) {
  return w.momentum * WEIGHTS.momentum
       + w.attribution * WEIGHTS.attribution
       + w.translatab * WEIGHTS.translatab
       + w.competition * WEIGHTS.competition;
}
function gateFail(w: Work) {
  return w.gateUsSource === false || w.gateUe === false || w.gateNoTm === false;
}
function decide(w: Work): { d: string; c: string } {
  if (gateFail(w)) return { d: "REJET", c: "var(--ox)" };
  if (w.gateUe === null) return { d: "À VALIDER", c: "var(--brass)" };
  const sc = weighted(w);
  if (sc >= THRESHOLD) return { d: "PRODUIRE", c: "var(--sage)" };
  if (sc >= 5) return { d: "FILE D'ATTENTE", c: "var(--brass)" };
  return { d: "REJET", c: "var(--ox)" };
}

/* ---------- App ---------- */
export default function App() {
  const [works, setWorks] = useState<Work[] | null>(null);
  const [cfg, setCfg] = useState<Config>(DEFAULTS);
  const [tab, setTab] = useState<"pilotage" | "oeuvres" | "apercus" | "viabilite" | "import" | "connecteurs" | "commandes">("pilotage");
  const [sel, setSel] = useState<number | null>(null);
  const [imp, setImp] = useState("");
  const [busy, setBusy] = useState(false);
  const [busyMkt, setBusyMkt] = useState(false);
  const [busyMockup, setBusyMockup] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [lang, setLang] = useState<string>("fr");
  const [connectors, setConnectors] = useState<Connector[] | null>(null);
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [listing, setListing] = useState<ListingResult | null>(null);
  const [busyListing, setBusyListing] = useState(false);
  const [collection, setCollection] = useState<PreviewWork[] | null>(null);
  const [collFiltre, setCollFiltre] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const r = await fetch("/api/works");
      if (!r.ok) throw new Error(`API ${r.status}`);
      setWorks(await r.json());
      setErr(null);
    } catch (e) {
      setErr((e as Error).message);
      setWorks([]);
    }
  }, []);

  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    try { const c = localStorage.getItem(CFG_KEY); if (c) setCfg(JSON.parse(c)); } catch {}
  }, []);
  useEffect(() => {
    try { localStorage.setItem(CFG_KEY, JSON.stringify(cfg)); } catch {}
  }, [cfg]);

  const econ = useMemo(() => {
    const enc = cfg.prix + cfg.port;
    const fees = enc * (0.065 + 0.03) + 0.25 + 0.20;
    const marge = enc - fees - cfg.base;
    const seuil = (cfg.designs * cfg.coutDesign + cfg.fixes) / (cfg.designs * cfg.ventesGagnant * marge);
    const res = cfg.designs * (cfg.hitrate / 100) * cfg.ventesGagnant * marge - cfg.designs * cfg.coutDesign - cfg.fixes;
    return { marge, seuil: seuil * 100, res };
  }, [cfg]);

  /** Patch optimiste local + PATCH API. Revert si l'API échoue. */
  const patchWork = useCallback(async (id: number, patch: Partial<Work>) => {
    if (!works) return;
    const prev = works;
    setWorks(works.map((w) => (w.id === id ? { ...w, ...patch } : w)));
    try {
      const r = await fetch("/api/works", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, ...patch }),
      });
      if (!r.ok) throw new Error(`PATCH ${r.status}`);
      const updated = await r.json();
      setWorks((cur) => (cur || []).map((w) => (w.id === id ? { ...w, ...updated } : w)));
    } catch (e) {
      setErr((e as Error).message);
      setWorks(prev);
    }
  }, [works]);

  /** Scoring LLM : appelle /api/scoring puis remplace l'œuvre par la version mise à jour. */
  const scoreLlm = useCallback(async (id: number, product = "poster") => {
    setBusy(true); setErr(null);
    try {
      const r = await fetch("/api/scoring", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, product }),
      });
      if (r.status === 503) {
        setErr("ANTHROPIC_API_KEY non configurée côté serveur.");
        return;
      }
      if (!r.ok) throw new Error(`Scoring ${r.status}`);
      const updated = await r.json();
      setWorks((cur) => (cur || []).map((w) => (w.id === id ? { ...w, ...updated } : w)));
    } catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }, []);

  /** Marketing multilingue : appelle /api/marketing pour générer les 5 langues. */
  const genMarketing = useCallback(async (id: number) => {
    setBusyMkt(true); setErr(null);
    try {
      const r = await fetch("/api/marketing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, locales: LOCALES.map((l) => l.code) }),
      });
      if (r.status === 503) {
        setErr("ANTHROPIC_API_KEY non configurée côté serveur.");
        return;
      }
      if (!r.ok) {
        const body = await r.json().catch(() => ({}));
        throw new Error(body?.error || `Marketing ${r.status}`);
      }
      const updated = await r.json();
      setWorks((cur) => (cur || []).map((w) => (w.id === id ? { ...w, ...updated } : w)));
    } catch (e) { setErr((e as Error).message); }
    finally { setBusyMkt(false); }
  }, []);

  const importJson = useCallback(async () => {
    setBusy(true); setErr(null);
    try {
      const arr = JSON.parse(imp);
      const r = await fetch("/api/works", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(arr),
      });
      if (!r.ok) throw new Error(`Import ${r.status}`);
      await reload();
      setTab("oeuvres");
      setImp("");
    } catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }, [imp, reload]);

  const removeWork = useCallback(async (id: number) => {
    if (!confirm("Supprimer cette œuvre du registre ?")) return;
    await fetch(`/api/works?id=${id}`, { method: "DELETE" });
    setSel(null);
    await reload();
  }, [reload]);

  /** Charge la liste des connecteurs (statuts configurés). */
  const loadConnectors = useCallback(async () => {
    try {
      const r = await fetch("/api/connectors");
      if (!r.ok) throw new Error(`API ${r.status}`);
      const data = await r.json();
      setConnectors(data.connectors);
    } catch (e) { setErr((e as Error).message); }
  }, []);

  /** Ping live un connecteur. Met à jour son `lastTest` localement. */
  const testConnector = useCallback(async (id: string) => {
    setTestingId(id); setErr(null);
    try {
      const r = await fetch(`/api/connectors/test/${id}`, { method: "POST" });
      const data = await r.json();
      const at = new Date().toISOString();
      setConnectors((cur) => (cur || []).map((c) =>
        c.id === id ? { ...c, lastTest: { ok: !!data.ok, detail: String(data.detail || ""), durationMs: Number(data.durationMs || 0), at } } : c,
      ));
    } catch (e) { setErr((e as Error).message); }
    finally { setTestingId(null); }
  }, []);

  /** Charge la liste des commandes. */
  const loadOrders = useCallback(async () => {
    try {
      const r = await fetch("/api/orders");
      if (!r.ok) throw new Error(`API ${r.status}`);
      setOrders(await r.json());
    } catch (e) { setErr((e as Error).message); }
  }, []);

  /** Charge l'index des aperçus générés (web/public/renders/collection.json). */
  const loadCollection = useCallback(async () => {
    try {
      const r = await fetch("/renders/collection.json", { cache: "no-store" });
      if (!r.ok) throw new Error(`renders ${r.status}`);
      setCollection(await r.json());
    } catch {
      setCollection([]); // pas encore de collection générée
    }
  }, []);

  /** Génère les mockups (templates + lifestyle IA) pour une œuvre. */
  const genMockups = useCallback(async (id: number, product = "framed_a2_oak") => {
    setBusyMockup(true); setErr(null);
    try {
      const r = await fetch("/api/mockup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, product }),
      });
      const data = await r.json();
      if (!r.ok && r.status !== 202) throw new Error(data?.error || `Mockup ${r.status}`);
      if (data?.warning) setErr(data.warning);
      if (data?.work) setWorks((cur) => (cur || []).map((w) => (w.id === id ? { ...w, ...data.work } : w)));
    } catch (e) { setErr((e as Error).message); }
    finally { setBusyMockup(false); }
  }, []);

  /** Aperçu du listing Etsy (dry-run) : titre/tags/description + matrice variantes×prix. */
  const previewListing = useCallback(async (id: number, locale: string) => {
    setBusyListing(true); setErr(null);
    try {
      const r = await fetch("/api/etsy/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, locale, dryRun: true }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data?.error || `Listing ${r.status}`);
      setListing({ workId: id, ...data });
    } catch (e) { setErr((e as Error).message); }
    finally { setBusyListing(false); }
  }, []);

  // Auto-load au changement d'onglet
  useEffect(() => {
    if (tab === "connecteurs" && connectors === null) loadConnectors();
    if (tab === "commandes" && orders === null) loadOrders();
    if (tab === "apercus" && collection === null) loadCollection();
  }, [tab, connectors, orders, collection, loadConnectors, loadOrders, loadCollection]);

  if (!works) {
    return <div style={{ padding: 40, fontFamily: "system-ui", color: "#5C5345" }}>Chargement…</div>;
  }

  const selected = sel ? works.find((w) => w.id === sel) : null;

  const css = `
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,900&family=Newsreader:ital,opsz@0,6..72;1,6..72&family=JetBrains+Mono:wght@400;600&display=swap');
  :root{
    /* Palette papier (signature de la marque) */
    --paper:#F2EBDD; --paper2:#EAE0CC; --paper3:#FCF9F1;
    --card:#FBF7EE;
    --ink:#211C15; --ink2:#5C5345; --ink3:#867864;
    --line:#D8CBB0; --line-strong:#BFAE8B;
    --brass:#A9803F; --brass-hover:#C09653; --brass-press:#8C6A33;
    --sage:#4F6B4A; --sage-soft:#E7EDE5;
    --ox:#8A3A30; --ox-soft:#FBEAE5;
    --warn-soft:#F5EDDC;
    /* Tokens (inspirés de Linear : letter-spacing négatif sur display, scale 4/8/12/16/24/32/48) */
    --sp-xxs:4px; --sp-xs:8px; --sp-sm:12px; --sp-md:16px; --sp-lg:24px; --sp-xl:32px;
    --r-xs:2px; --r-sm:4px; --r-md:6px; --r-pill:9999px;
    --t-fast:120ms; --t-base:180ms;
    --shadow-1:0 1px 0 rgba(33,28,21,.04);
    --shadow-2:0 1px 2px rgba(33,28,21,.06), 0 1px 0 rgba(33,28,21,.04);
    --shadow-3:0 4px 12px rgba(33,28,21,.10), 0 1px 0 rgba(33,28,21,.04);
    --ring:0 0 0 2px rgba(169,128,63,.35);
  }
  *{box-sizing:border-box}
  html,body{margin:0;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}

  /* Fonts ─────────────────────── */
  .serif{font-family:'Fraunces',serif;letter-spacing:-0.012em}
  .body{font-family:'Newsreader',serif}
  .mono{font-family:'JetBrains Mono',monospace}

  /* Hiérarchie typographique (display Fraunces avec letter-spacing négatif comme Linear) */
  .h-page{font:600 26px/1.15 'Fraunces',serif;letter-spacing:-0.022em;color:var(--ink);margin:0 0 4px}
  .h-section{font:600 17px/1.2 'Fraunces',serif;letter-spacing:-0.015em;color:var(--ink);margin:0 0 12px}
  .eyebrow{font:500 10px/1.3 'JetBrains Mono',monospace;letter-spacing:.08em;color:var(--ink2);text-transform:uppercase;display:inline-block}
  .caption{font:400 12px/1.4 'Newsreader',serif;color:var(--ink2)}
  .sub{font:400 14px/1.5 'Newsreader',serif;color:var(--ink2);margin:0 0 18px}

  /* Cards ─────────────────────── */
  .cd{background:var(--card);border:1px solid var(--line);border-radius:var(--r-xs);box-shadow:var(--shadow-1);transition:box-shadow var(--t-base) ease,transform var(--t-base) ease,border-color var(--t-base) ease}
  .cd-hover:hover{box-shadow:var(--shadow-3);transform:translateY(-1px);border-color:var(--line-strong)}

  /* Sidebar ─────────────────────── */
  .navi{display:flex;align-items:center;gap:10px;padding:9px 14px;cursor:pointer;border-left:2px solid transparent;color:var(--ink2);font:400 14px 'Newsreader',serif;transition:background var(--t-fast) ease,color var(--t-fast) ease,border-color var(--t-fast) ease}
  .navi:hover{background:var(--paper2);color:var(--ink)}
  .navi.on{border-left-color:var(--brass);color:var(--ink);background:var(--paper2);font-weight:500}
  .nav-section{padding:14px 14px 4px;color:var(--ink3);font:500 9px/1 'JetBrains Mono',monospace;letter-spacing:.14em;text-transform:uppercase}
  .nav-divider{height:1px;background:var(--line);margin:10px 0;opacity:.5}

  /* Badges / Pills (Linear status-badge pattern, palette papier) ────── */
  .pill{font:500 10px/1 'JetBrains Mono',monospace;letter-spacing:.04em;padding:3px 8px;border-radius:var(--r-pill);border:1px solid currentColor;display:inline-block;white-space:nowrap}
  .badge{font:500 10px/1 'JetBrains Mono',monospace;letter-spacing:.04em;padding:3px 8px;border-radius:var(--r-pill);display:inline-block;white-space:nowrap}
  .badge-success{background:var(--sage-soft);color:var(--sage)}
  .badge-warning{background:var(--warn-soft);color:var(--brass)}
  .badge-danger{background:var(--ox-soft);color:var(--ox)}
  .badge-neutral{background:var(--paper2);color:var(--ink2)}

  /* Row hover ────────────────── */
  .wrow{cursor:pointer;transition:background var(--t-fast) ease}
  .wrow:hover{background:var(--paper2)}

  /* Inputs ─────────────────────── */
  input[type=range]{accent-color:var(--brass);width:100%}
  .inp{font:400 13px 'JetBrains Mono',monospace;background:var(--paper);border:1px solid var(--line);border-radius:var(--r-xs);padding:8px 10px;width:100%;color:var(--ink);transition:border-color var(--t-fast) ease,box-shadow var(--t-fast) ease}
  .inp:hover{border-color:var(--line-strong)}
  .inp:focus{outline:none;border-color:var(--brass);box-shadow:var(--ring)}

  /* Buttons (variants Linear) ───────────── */
  .btn{font:500 11px/1 'JetBrains Mono',monospace;letter-spacing:.05em;padding:7px 12px;border-radius:var(--r-xs);cursor:pointer;border:1px solid var(--line);background:var(--paper);color:var(--ink);transition:all var(--t-fast) ease;display:inline-flex;align-items:center;gap:6px;white-space:nowrap}
  .btn:hover{background:var(--paper2);border-color:var(--line-strong)}
  .btn:active{transform:translateY(0.5px)}
  .btn:focus-visible{outline:none;box-shadow:var(--ring)}
  .btn:disabled{opacity:.45;cursor:not-allowed;background:var(--paper);transform:none}
  .btn-primary{background:var(--brass);border-color:var(--brass);color:#fff}
  .btn-primary:hover{background:var(--brass-hover);border-color:var(--brass-hover);color:#fff}
  .btn-primary:active{background:var(--brass-press);border-color:var(--brass-press)}
  .btn-ghost{background:transparent;border-color:transparent;color:var(--ink2)}
  .btn-ghost:hover{background:var(--paper2);color:var(--ink);border-color:transparent}
  .btn-danger{color:var(--ox);border-color:var(--ox)}
  .btn-danger:hover{background:var(--ox-soft);border-color:var(--ox);color:var(--ox)}

  /* Interface tabs (≠ sidebar) ────────── */
  .tab{font:500 11px/1 'JetBrains Mono',monospace;padding:6px 12px;border:1px solid var(--line);background:var(--paper);cursor:pointer;border-radius:var(--r-xs);color:var(--ink2);transition:all var(--t-fast) ease}
  .tab:hover{border-color:var(--line-strong);color:var(--ink)}
  .tab.on{border-color:var(--brass);color:var(--brass);background:var(--card)}

  /* Tags marketing ─────────── */
  .mtag{font:500 10px/1 'JetBrains Mono',monospace;background:var(--paper2);color:var(--ink2);padding:3px 7px;border-radius:var(--r-xs);margin:0 4px 4px 0;display:inline-block}

  /* Images ──────────────────── */
  .thumb{width:48px;height:48px;object-fit:cover;border-radius:var(--r-xs);border:1px solid var(--line);background:var(--paper);flex-shrink:0;transition:border-color var(--t-fast) ease}
  .thumb:hover{border-color:var(--line-strong)}
  .thumb-empty{display:flex;align-items:center;justify-content:center;color:var(--ink3)}
  .preview{width:100%;max-height:280px;object-fit:contain;background:var(--paper);border:1px solid var(--line);border-radius:var(--r-xs)}

  /* Data table (sticky header + zebra subtile) ────────── */
  .dt{width:100%;border-collapse:collapse;font-size:13px}
  .dt thead th{position:sticky;top:0;background:var(--paper2);text-align:left;padding:10px 14px;font:500 10px/1 'JetBrains Mono',monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);box-shadow:inset 0 -1px 0 var(--line);z-index:1}
  .dt tbody td{padding:10px 14px;border-bottom:1px solid var(--paper2);color:var(--ink);font-size:13px}
  .dt tbody tr:hover{background:var(--paper2)}
  .dt tbody tr:last-child td{border-bottom:none}

  /* Error banner ───────────── */
  .err{font:500 11px 'JetBrains Mono',monospace;color:var(--ox);padding:10px 14px;border-top:1px solid var(--line);background:var(--ox-soft)}

  /* KPI label color override (calme) ─────── */
  .kpi-label{font:500 10px 'JetBrains Mono',monospace;letter-spacing:.08em;color:var(--ink3);text-transform:uppercase}

  /* Anim utility ───────────── */
  .fade{animation:fadeIn 200ms ease}
  @keyframes fadeIn{from{opacity:0;transform:translateY(2px)}to{opacity:1;transform:none}}
  `;

  const Kpi = ({ k, v, sub, tone }: { k: string; v: string | number; sub?: string; tone?: string }) => (
    <div className="cd" style={{ padding: 16 }}>
      <div className="mono" style={{ fontSize: 10, letterSpacing: ".08em", color: "var(--ink2)", textTransform: "uppercase" }}>{k}</div>
      <div className="serif" style={{ fontSize: 30, fontWeight: 600, color: tone || "var(--ink)", lineHeight: 1.1, marginTop: 6 }}>{v}</div>
      {sub && <div className="body" style={{ fontSize: 12, color: "var(--ink2)", marginTop: 2 }}>{sub}</div>}
    </div>
  );

  return (
    <div className="body" style={{ background: "var(--paper)", color: "var(--ink)", minHeight: "100vh", display: "flex" }}>
      <style>{css}</style>

      {/* RAIL */}
      <aside style={{ width: 210, borderRight: "1px solid var(--line)", background: "var(--paper)", flexShrink: 0 }}>
        <div style={{ padding: "18px 16px", borderBottom: "1px solid var(--line)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/brand/sceau.png" alt="Vellum & Cie" width={26} height={26} style={{ display: "block" }} />
            <div>
              <div className="serif" style={{ fontWeight: 600, fontSize: 17, letterSpacing: "-.01em", lineHeight: 1.05 }}>
                VELLUM <span style={{ color: "var(--brass)", fontStyle: "italic", fontWeight: 500 }}>&amp; Cie</span>
              </div>
            </div>
          </div>
          <div className="mono" style={{ fontSize: 8.5, letterSpacing: ".16em", color: "var(--ink2)", marginTop: 6 }}>ÉDITIONS · DOMAINE PUBLIC</div>
        </div>
        {/* Section : vue d'ensemble */}
        <div className={"navi " + (tab === "pilotage" ? "on" : "")} onClick={() => setTab("pilotage")}>
          <LayoutGrid size={15} /> <span>Pilotage</span>
        </div>

        {/* Section : catalogue */}
        <div className="nav-section">Catalogue</div>
        <div className={"navi " + (tab === "oeuvres" ? "on" : "")} onClick={() => setTab("oeuvres")}>
          <ListChecks size={15} /> <span>Œuvres</span>
        </div>
        <div className={"navi " + (tab === "apercus" ? "on" : "")} onClick={() => setTab("apercus")}>
          <ImageIcon size={15} /> <span>Aperçus</span>
        </div>
        <div className={"navi " + (tab === "import" ? "on" : "")} onClick={() => setTab("import")}>
          <Upload size={15} /> <span>Import</span>
        </div>

        {/* Section : opérations */}
        <div className="nav-section">Opérations</div>
        <div className={"navi " + (tab === "connecteurs" ? "on" : "")} onClick={() => setTab("connecteurs")}>
          <Plug size={15} /> <span>Connecteurs</span>
        </div>
        <div className={"navi " + (tab === "commandes" ? "on" : "")} onClick={() => setTab("commandes")}>
          <Package size={15} /> <span>Commandes</span>
        </div>

        {/* Section : outils */}
        <div className="nav-section">Outils</div>
        <div className={"navi " + (tab === "viabilite" ? "on" : "")} onClick={() => setTab("viabilite")}>
          <Calculator size={15} /> <span>Viabilité</span>
        </div>
        <div className="navi" onClick={reload}>
          <RefreshCw size={15} /> <span>Recharger</span>
        </div>
        <div style={{ padding: 14, marginTop: 12 }}>
          <div className="cd" style={{ padding: 12 }}>
            <div className="mono" style={{ fontSize: 9, color: "var(--ink2)", letterSpacing: ".08em" }}>SEUIL DE RENTABILITÉ</div>
            <div className="serif" style={{ fontSize: 22, fontWeight: 600, color: cfg.hitrate >= econ.seuil ? "var(--sage)" : "var(--ox)" }}>{econ.seuil.toFixed(2)}%</div>
            <div className="body" style={{ fontSize: 11, color: "var(--ink2)" }}>hit-rate actuel {cfg.hitrate}% {cfg.hitrate >= econ.seuil ? "✓ rentable" : "✗ sous le seuil"}</div>
          </div>
        </div>
        {err && <div className="err">⚠ {err}</div>}
      </aside>

      {/* MAIN */}
      <main style={{ flex: 1, padding: 24, overflow: "auto" }}>
        {tab === "pilotage" && (
          <>
            <h1 className="serif" style={{ fontSize: 26, fontWeight: 600, margin: "0 0 4px" }}>Pilotage</h1>
            <p className="body" style={{ color: "var(--ink2)", margin: "0 0 18px", fontSize: 14 }}>Vue d'ensemble de la collection et de sa viabilité.</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 22 }}>
              <Kpi k="Marge nette / vente" v={`${econ.marge.toFixed(2)} $`} sub={`prix ${cfg.prix}$ · base ${cfg.base}$`} />
              <Kpi k="Seuil hit-rate" v={`${econ.seuil.toFixed(2)}%`} tone={cfg.hitrate >= econ.seuil ? "var(--sage)" : "var(--ox)"} sub="point mort" />
              <Kpi k="Résultat mensuel" v={`${Math.round(econ.res)} $`} tone={econ.res >= 0 ? "var(--sage)" : "var(--ox)"} sub={`@ ${cfg.hitrate}% hit-rate`} />
              <Kpi k="Œuvres en pipeline" v={works.length} sub={`${works.filter((w) => w.status === "publish").length} publiées`} />
            </div>

            <h2 className="serif" style={{ fontSize: 17, fontWeight: 600, margin: "0 0 12px" }}>Pipeline de production</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 10 }}>
              {STAGES.map((st) => {
                const items = works.filter((w) => w.status === st.key);
                const I = st.icon;
                return (
                  <div key={st.key} className="cd" style={{ padding: 10, minHeight: 180 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8, paddingBottom: 6, borderBottom: "1px solid var(--line)" }}>
                      <I size={13} color="var(--brass)" />
                      <span className="mono" style={{ fontSize: 10, letterSpacing: ".04em", textTransform: "uppercase" }}>{st.label}</span>
                      <span className="mono" style={{ fontSize: 10, color: "var(--ink2)", marginLeft: "auto" }}>{items.length}</span>
                    </div>
                    {items.map((w) => {
                      const dc = decide(w);
                      return (
                        <div key={w.id} className="wrow" onClick={() => { setSel(w.id); setTab("oeuvres"); }} style={{ padding: "6px 4px", borderBottom: "1px solid var(--paper2)" }}>
                          <div className="body" style={{ fontSize: 12, lineHeight: 1.25 }}>{w.title}</div>
                          <span className="pill" style={{ color: dc.c, marginTop: 3 }}>{dc.d}</span>
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </>
        )}

        {tab === "oeuvres" && (
          <div style={{ display: "flex", gap: 18 }}>
            <div style={{ flex: selected ? "0 0 46%" : "1" }}>
              <h1 className="serif" style={{ fontSize: 26, fontWeight: 600, margin: "0 0 14px" }}>Œuvres <span className="mono" style={{ fontSize: 12, color: "var(--ink2)" }}>({works.length})</span></h1>
              {works.length === 0 ? (
                <div className="cd" style={{ padding: 24 }}>
                  <div className="body" style={{ fontSize: 13, color: "var(--ink2)" }}>
                    Aucune œuvre dans le registre. Va dans <strong>Import</strong> pour coller le JSON produit par <code>agents/sourcing_agent.py</code>.
                  </div>
                </div>
              ) : (
                <div className="cd">
                  {works.map((w) => {
                    const dc = decide(w);
                    return (
                      <div key={w.id} className="wrow" onClick={() => setSel(w.id)} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 14px", borderBottom: "1px solid var(--paper2)", background: sel === w.id ? "var(--paper2)" : "" }}>
                        {w.imageUrl ? (
                          /* eslint-disable-next-line @next/next/no-img-element */
                          <img className="thumb" src={w.imageUrl} alt={w.title} loading="lazy" />
                        ) : (
                          <div className="thumb thumb-empty"><ImageIcon size={18} /></div>
                        )}
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div className="body" style={{ fontSize: 14, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{w.title}</div>
                          <div className="mono" style={{ fontSize: 10, color: "var(--ink2)" }}>{w.artist || "—"} · {w.objectDate || "—"} · {w.resolutionPx}px {w.marketing ? "· 🌍" : ""}</div>
                        </div>
                        <span className="pill" style={{ color: dc.c }}>{dc.d}</span>
                        <ChevronRight size={14} color="var(--ink2)" />
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {selected && (
              <div style={{ flex: 1 }}>
                <div className="cd" style={{ padding: 18 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                    <div>
                      <h2 className="serif" style={{ fontSize: 20, fontWeight: 600, margin: 0 }}>{selected.title}</h2>
                      <div className="mono" style={{ fontSize: 11, color: "var(--ink2)", marginTop: 3 }}>#{selected.id} · {selected.department || "—"}</div>
                    </div>
                    <X size={18} style={{ cursor: "pointer" }} onClick={() => setSel(null)} />
                  </div>

                  {/* Aperçu image */}
                  {selected.imageUrl && (
                    <div style={{ marginTop: 14 }}>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img className="preview" src={selected.imageUrl} alt={selected.title} loading="lazy" />
                    </div>
                  )}

                  {/* Provenance */}
                  <div style={{ marginTop: 14, fontSize: 13, lineHeight: 1.7 }} className="body">
                    <Row l="Artiste" v={`${selected.artist || "—"}${selected.artistDeath ? ` (†${selected.artistDeath})` : ""}`} />
                    <Row l="Date" v={selected.objectDate || "—"} />
                    <Row l="Médium" v={selected.medium || "—"} />
                    <Row l="Résolution" v={`${selected.resolutionPx} px ${selected.resolutionPx >= 3000 ? "✓" : "✗ insuffisant"}`} />
                    <Row l="Source" v={selected.source} />
                  </div>

                  {/* Gates */}
                  <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--line)" }}>
                    <div className="mono" style={{ fontSize: 10, letterSpacing: ".08em", color: "var(--ink2)", marginBottom: 8 }}>GATES DE CONFORMITÉ</div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <Gate ok={selected.gateUsSource} label="DP US" />
                      <Gate ok={selected.gateUe} label="DP UE" />
                      <Gate ok={selected.gateNoTm} label="Sans marque" />
                      <Gate ok={selected.resolutionPx >= 3000} label="Résolution" />
                    </div>
                    {selected.gateUe === null && (
                      <div style={{ marginTop: 10, padding: 10, background: "var(--paper2)", borderRadius: 2 }}>
                        <div className="body" style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 6 }}>
                          <AlertTriangle size={14} color="var(--brass)" /> Date de l'auteur inconnue — validation humaine requise.
                        </div>
                        <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
                          <button className="btn" style={{ color: "var(--sage)" }} onClick={() => patchWork(selected.id, { gateUe: true, status: "score" })}><Check size={11} style={{ display: "inline" }} /> Valider DP</button>
                          <button className="btn" style={{ color: "var(--ox)" }} onClick={() => patchWork(selected.id, { gateUe: false })}><X size={11} style={{ display: "inline" }} /> Rejeter</button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* === Preuve domaine public (v2) === */}
                  {(selected.dpEvidence || selected.rightsStatement || selected.wikidataUrl || selected.artistDeath || selected.accessionNumber) && (
                    <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--line)" }}>
                      <div className="mono" style={{ fontSize: 10, letterSpacing: ".08em", color: "var(--ink2)", marginBottom: 8 }}>
                        <ShieldCheck size={11} style={{ display: "inline", marginRight: 4, verticalAlign: "middle" }} />
                        PREUVE DOMAINE PUBLIC
                      </div>
                      {selected.dpEvidence && (
                        <div className="body" style={{ fontSize: 12, lineHeight: 1.6, padding: 10, background: "var(--paper2)", borderLeft: "3px solid var(--sage)", borderRadius: "0 2px 2px 0" }}>
                          {selected.dpEvidence}
                        </div>
                      )}
                      <div style={{ marginTop: 8, fontSize: 12, lineHeight: 1.7 }} className="body">
                        {(selected.artistBirth || selected.artistDeath) && <Row l="Auteur (naissance–décès)" v={`${selected.artistBirth ?? "?"} – ${selected.artistDeath ?? "?"}`} />}
                        {selected.objectBeginYear && <Row l="Année de l'œuvre" v={String(selected.objectBeginYear)} />}
                        {selected.rightsStatement && <Row l="Droits (institution)" v={selected.rightsStatement} />}
                        {selected.accessionNumber && <Row l="N° d'accession" v={selected.accessionNumber} />}
                      </div>
                      {selected.wikidataUrl && (
                        <a href={selected.wikidataUrl} target="_blank" rel="noreferrer" className="btn" style={{ marginTop: 8, textDecoration: "none", color: "var(--brass)" }}>
                          <ExternalLink size={11} style={{ display: "inline", marginRight: 4 }} /> Référence Wikidata
                        </a>
                      )}
                    </div>
                  )}

                  {/* Scoring */}
                  {!gateFail(selected) && selected.gateUe !== null && (
                    <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--line)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                        <span className="mono" style={{ fontSize: 10, letterSpacing: ".08em", color: "var(--ink2)" }}>SCORING (4 AXES)</span>
                        <span className="serif" style={{ fontSize: 22, fontWeight: 600, color: decide(selected).c }}>{weighted(selected).toFixed(1)}<span style={{ fontSize: 12, color: "var(--ink2)" }}>/10</span></span>
                      </div>
                      {([
                        ["momentum",    "Momentum esthétique",     "30%"],
                        ["attribution", "Attribution / récit",     "20%"],
                        ["translatab",  "Traduisibilité produit",  "25%"],
                        ["competition", "Espace concurrentiel",    "25%"],
                      ] as const).map(([k, l, p]) => (
                        <div key={k} style={{ marginBottom: 9 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }} className="body">
                            <span>{l} <span className="mono" style={{ fontSize: 9, color: "var(--ink2)" }}>{p}</span></span>
                            <span className="mono">{selected[k]}</span>
                          </div>
                          <input type="range" min="0" max="10" value={selected[k]} onChange={(e) => patchWork(selected.id, { [k]: +e.target.value } as Partial<Work>)} />
                        </div>
                      ))}
                      <textarea className="inp body" rows={2} placeholder="Accroche provenance (storytelling FR rapide)…" value={selected.hook ?? ""} onChange={(e) => patchWork(selected.id, { hook: e.target.value })} style={{ marginTop: 6, resize: "vertical" }} />
                      {selected.angle && (
                        <div className="body" style={{ marginTop: 6, fontSize: 12, color: "var(--ink2)" }}>
                          <strong>Angle recommandé :</strong> {selected.angle}
                        </div>
                      )}

                      <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
                        <button className="btn" disabled={busy} style={{ color: "var(--brass)" }} onClick={() => scoreLlm(selected.id)}>
                          <Wand2 size={11} style={{ display: "inline", marginRight: 4 }} />
                          {busy ? "Scoring…" : "Scoring Claude"}
                        </button>
                        {STAGES.map((s) => (
                          <button key={s.key} className="btn" style={{ borderColor: selected.status === s.key ? "var(--brass)" : "var(--line)", color: selected.status === s.key ? "var(--brass)" : "var(--ink2)" }} onClick={() => patchWork(selected.id, { status: s.key })}>{s.label}</button>
                        ))}
                        <button className="btn" style={{ color: "var(--ox)", marginLeft: "auto" }} onClick={() => removeWork(selected.id)}>Supprimer</button>
                      </div>
                    </div>
                  )}

                  {/* Routing POD : ligne produit (standard → Gelato, signature → Prodigi) */}
                  {!gateFail(selected) && selected.gateUe !== null && (
                    <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--line)" }}>
                      <div className="mono" style={{ fontSize: 10, letterSpacing: ".08em", color: "var(--ink2)", marginBottom: 8 }}>
                        ROUTING POD
                      </div>
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                        {([
                          ["standard", "🇫🇷 Standard → Gelato",  "var(--sage)"],
                          ["signature", "🇬🇧 Signature → Prodigi", "var(--brass)"],
                          [null,       "Non décidé",              "var(--ink2)"],
                        ] as const).map(([val, label, color]) => (
                          <button
                            key={String(val)}
                            className="btn"
                            onClick={() => patchWork(selected.id, { line: val })}
                            style={{
                              borderColor: selected.line === val ? color : "var(--line)",
                              color: selected.line === val ? color : "var(--ink2)",
                            }}
                          >
                            {label}
                          </button>
                        ))}
                      </div>
                      <div className="body" style={{ fontSize: 11, color: "var(--ink2)", marginTop: 6 }}>
                        {selected.line === "signature"
                          ? "→ Prodigi : Hahnemühle Photo Rag, encadrés FATG, white-label intégral"
                          : selected.line === "standard"
                          ? "→ Gelato : production locale FR, intégration Etsy stable, ~10-20% moins cher"
                          : "Choisis une ligne pour activer le routing automatique des commandes."}
                      </div>

                      {/* Bouton Génération mockups */}
                      <div style={{ marginTop: 10, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                        <button
                          className="btn"
                          disabled={busyMockup}
                          style={{ color: "var(--brass)" }}
                          onClick={() => genMockups(selected.id)}
                        >
                          <Wand2 size={11} style={{ display: "inline", marginRight: 4 }} />
                          {busyMockup ? "Génération mockups…" : selected.mockups ? "Régénérer mockups" : "Générer mockups (templates + IA)"}
                        </button>
                        {selected.etsyListingId && (
                          <a
                            href={`https://www.etsy.com/listing/${selected.etsyListingId}`}
                            target="_blank"
                            rel="noreferrer"
                            className="btn"
                            style={{ textDecoration: "none", color: "var(--brass)" }}
                          >
                            <ExternalLink size={11} style={{ display: "inline", marginRight: 4 }} />
                            Voir sur Etsy
                          </a>
                        )}
                      </div>
                      <div className="body" style={{ fontSize: 11, color: "var(--ink2)", marginTop: 6 }}>
                        Sans clé : moteur local gratuit (10 visuels + carte provenance) →{" "}
                        <code style={{ fontSize: 10 }}>python -m agents.render --met-id {selected.id} --out web/public/renders/{selected.id}</code>
                      </div>

                      {/* Affichage des mockups générés */}
                      {selected.mockups && Object.entries(selected.mockups).map(([product, set]) => (
                        <div key={product} style={{ marginTop: 10 }}>
                          <div className="mono" style={{ fontSize: 10, color: "var(--ink2)", marginBottom: 4 }}>
                            {product.toUpperCase()} · généré {new Date(set.generatedAt).toLocaleString("fr-FR")}
                          </div>
                          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 6 }}>
                            {[...set.templates, ...set.lifestyle].slice(0, 6).map((url, i) => (
                              /* eslint-disable-next-line @next/next/no-img-element */
                              <img key={i} src={url} alt={`mockup ${i + 1}`} style={{ width: "100%", aspectRatio: "1 / 1", objectFit: "cover", border: "1px solid var(--line)", borderRadius: 2 }} loading="lazy" />
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Marketing multilingue */}
                  <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--line)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                      <span className="mono" style={{ fontSize: 10, letterSpacing: ".08em", color: "var(--ink2)" }}>
                        <Languages size={11} style={{ display: "inline", marginRight: 4, verticalAlign: "middle" }} />
                        MARKETING — 5 LANGUES
                      </span>
                      <button className="btn" disabled={busyMkt} style={{ color: "var(--brass)" }} onClick={() => genMarketing(selected.id)}>
                        <Wand2 size={11} style={{ display: "inline", marginRight: 4 }} />
                        {busyMkt ? "Génération…" : selected.marketing ? "Régénérer (FR/EN/DE/IT/ES)" : "Générer (FR/EN/DE/IT/ES)"}
                      </button>
                    </div>

                    {!selected.marketing ? (
                      <div className="body" style={{ fontSize: 12, color: "var(--ink2)", padding: 10, background: "var(--paper2)", borderRadius: 2 }}>
                        Aucun contenu marketing généré. Clique sur le bouton ci-dessus — Claude écrira en 1 appel les 5 versions linguistiques (titre court, titre Etsy SEO, description, accroche provenance, 10 tags).
                      </div>
                    ) : (
                      <>
                        <div style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap" }}>
                          {LOCALES.map((loc) => {
                            const has = !!selected.marketing?.[loc.code];
                            return (
                              <button
                                key={loc.code}
                                className={"tab " + (lang === loc.code ? "on" : "")}
                                onClick={() => setLang(loc.code)}
                                style={{ opacity: has ? 1 : 0.4 }}
                                title={has ? loc.label : `${loc.label} — non généré`}
                              >
                                {loc.flag} {loc.code.toUpperCase()}
                              </button>
                            );
                          })}
                        </div>
                        {(() => {
                          const m = selected.marketing?.[lang];
                          if (!m) {
                            return <div className="body" style={{ fontSize: 12, color: "var(--ink2)" }}>Pas de contenu pour cette langue. Relance la génération.</div>;
                          }
                          const srcBadge = m.titleSource === "wikidata"
                            ? { color: "var(--sage)", text: "✓ titre officiel Wikidata" }
                            : { color: "var(--ink2)", text: "titre original conservé (non traduit)" };
                          return (
                            <div className="body" style={{ fontSize: 13, lineHeight: 1.55 }}>
                              <Mfield l="Titre court" v={m.title} sub={srcBadge.text} subColor={srcBadge.color} />
                              <Mfield l="Titre listing Etsy (SEO)" v={m.listingTitle} mono />
                              <Mfield l="Description" v={m.description} block />
                              <Mfield l="Accroche provenance" v={m.hook} block />
                              <div style={{ marginTop: 8 }}>
                                <div className="mono" style={{ fontSize: 10, color: "var(--ink2)", marginBottom: 4, letterSpacing: ".06em" }}>TAGS SEO</div>
                                {m.tags.map((t, i) => <span key={i} className="mtag">{t}</span>)}
                              </div>
                            </div>
                          );
                        })()}
                      </>
                    )}
                  </div>

                  {/* === Aperçu listing Etsy (v2) === */}
                  <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--line)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                      <span className="mono" style={{ fontSize: 10, letterSpacing: ".08em", color: "var(--ink2)" }}>
                        <Tag size={11} style={{ display: "inline", marginRight: 4, verticalAlign: "middle" }} />
                        APERÇU LISTING ETSY
                      </span>
                      <button className="btn" disabled={busyListing} style={{ color: "var(--brass)" }} onClick={() => previewListing(selected.id, lang)}>
                        <Wand2 size={11} style={{ display: "inline", marginRight: 4 }} />
                        {busyListing ? "Assemblage…" : `Aperçu (${lang.toUpperCase()})`}
                      </button>
                    </div>
                    {listing && listing.workId === selected.id ? (
                      <div className="body" style={{ fontSize: 13 }}>
                        {listing.mode === "preview" && listing.reason && (
                          <div className="mono" style={{ fontSize: 9, color: "var(--ink2)", marginBottom: 8 }}>aperçu — {listing.reason}</div>
                        )}
                        <div style={{ marginBottom: 10 }}>
                          <div className="mono" style={{ fontSize: 10, color: "var(--ink2)" }}>TITRE · {listing.draft.titleLength}/140</div>
                          <div className="serif" style={{ fontSize: 15, lineHeight: 1.35 }}>{listing.draft.title}</div>
                          {listing.draft.titleWarning && <div className="body" style={{ fontSize: 11, color: "var(--brass)", marginTop: 2 }}>⚠ {listing.draft.titleWarning}</div>}
                        </div>
                        <div style={{ marginBottom: 10 }}>
                          <div className="mono" style={{ fontSize: 10, color: "var(--ink2)", marginBottom: 4 }}>TAGS · {listing.draft.tags.length}/13</div>
                          {listing.draft.tags.map((t, i) => <span key={i} className="mtag">{t}</span>)}
                        </div>
                        <div style={{ marginBottom: 10 }}>
                          <div className="mono" style={{ fontSize: 10, color: "var(--ink2)", marginBottom: 4 }}>VARIANTES · prix → marge nette</div>
                          <table className="dt" style={{ width: "100%", fontSize: 12 }}>
                            <tbody>
                              {listing.draft.variants.map((v) => (
                                <tr key={v.sku}>
                                  <td style={{ padding: "3px 6px" }}>{v.label} <span className="mono" style={{ fontSize: 9, color: "var(--ink2)" }}>{v.format}</span></td>
                                  <td className="mono" style={{ padding: "3px 6px", textAlign: "right" }}>{v.prix.toFixed(2)}€</td>
                                  <td className="mono" style={{ padding: "3px 6px", textAlign: "right", color: "var(--sage)" }}>+{v.margeNette.toFixed(2)}€</td>
                                  <td className="mono" style={{ padding: "3px 6px", fontSize: 9, color: "var(--ink2)" }}>{v.provider}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <details>
                          <summary className="mono" style={{ fontSize: 10, color: "var(--ink2)", cursor: "pointer" }}>DESCRIPTION COMPLÈTE ↓</summary>
                          <div className="body" style={{ whiteSpace: "pre-wrap", fontSize: 12, marginTop: 6, lineHeight: 1.6 }}>{listing.draft.description}</div>
                        </details>
                        <div style={{ marginTop: 10, padding: 8, background: "var(--paper2)", borderRadius: 2 }}>
                          {listing.draft.conformite.map((c, i) => <div key={i} className="body" style={{ fontSize: 11, color: "var(--ink2)" }}>• {c}</div>)}
                        </div>
                      </div>
                    ) : (
                      <div className="body" style={{ fontSize: 12, color: "var(--ink2)", padding: 10, background: "var(--paper2)", borderRadius: 2 }}>
                        Assemble un brouillon Etsy complet (titre SEO ≤140c, 13 tags, description avec provenance + « sourced by », matrice variantes×prix Gelato avec marges). Génère d'abord le marketing pour un titre optimal.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {tab === "connecteurs" && (
          <>
            <h1 className="serif" style={{ fontSize: 26, fontWeight: 600, margin: "0 0 4px" }}>Connecteurs</h1>
            <p className="body" style={{ color: "var(--ink2)", margin: "0 0 18px", fontSize: 14 }}>
              Statut des intégrations externes (clés API, services). Clique sur <strong>Tester</strong> pour pinger le service en live.
            </p>
            <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
              <button className="btn" onClick={loadConnectors}><RefreshCw size={11} style={{ display: "inline", marginRight: 4 }} />Recharger</button>
              <button className="btn" disabled={!connectors || !!testingId} onClick={async () => {
                if (!connectors) return;
                for (const c of connectors.filter((x) => x.hasTest && x.status === "configured")) {
                  await testConnector(c.id);
                }
              }}>Tout tester</button>
            </div>

            {!connectors ? (
              <div className="body" style={{ color: "var(--ink2)" }}>Chargement…</div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(420px, 1fr))", gap: 12 }}>
                {connectors.map((c) => {
                  const badgeClass =
                    c.status === "configured" ? "badge badge-success" :
                    c.status === "missing_key" ? "badge badge-danger" :
                    "badge badge-warning";
                  const cat = {
                    ai: "🧠 IA",
                    data: "📚 Données",
                    marketplace: "🏪 Marketplace",
                    pod: "🖨️ POD",
                    mockup: "🖼️ Mockup",
                    render: "🎨 Rendu",
                  }[c.category];
                  return (
                    <div key={c.id} className="cd cd-hover" style={{ padding: 16 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", gap: 8 }}>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div className="eyebrow">{cat}</div>
                          <div className="serif" style={{ fontSize: 17, fontWeight: 600, letterSpacing: "-0.015em", marginTop: 2 }}>{c.name}</div>
                          <a href={c.docUrl} target="_blank" rel="noreferrer" className="mono" style={{ fontSize: 10, color: "var(--brass)", textDecoration: "none" }}>
                            doc ↗
                          </a>
                        </div>
                        <span className={badgeClass}>
                          {c.status === "configured" ? "✓ Configuré" : c.status === "missing_key" ? "✗ Clé manquante" : c.status}
                        </span>
                      </div>

                      <div className="body" style={{ fontSize: 12, color: "var(--ink2)", margin: "8px 0", lineHeight: 1.5 }}>
                        {c.description}
                      </div>

                      <div className="mono" style={{ fontSize: 10, color: "var(--ink2)" }}>
                        {c.configHint}
                        {c.ordersLast30 !== null && <> · <strong style={{ color: "var(--ink)" }}>{c.ordersLast30}</strong> commandes / 30j</>}
                      </div>

                      {c.lastTest && (
                        <div style={{ marginTop: 8, padding: 8, borderRadius: 2, background: c.lastTest.ok ? "#E7EDE5" : "#FBEAE5" }}>
                          <div className="mono" style={{ fontSize: 10, color: c.lastTest.ok ? "var(--sage)" : "var(--ox)" }}>
                            {c.lastTest.ok ? "✓ OK" : "✗ ERREUR"} · {c.lastTest.durationMs} ms · {new Date(c.lastTest.at).toLocaleTimeString("fr-FR")}
                          </div>
                          <div className="body" style={{ fontSize: 11, color: "var(--ink)", marginTop: 2 }}>{c.lastTest.detail}</div>
                        </div>
                      )}

                      {c.hasTest && (
                        <div style={{ marginTop: 10, display: "flex", gap: 6 }}>
                          <button
                            className="btn"
                            disabled={c.status === "missing_key" || testingId === c.id}
                            onClick={() => testConnector(c.id)}
                            style={{ color: c.status === "missing_key" ? "var(--ink2)" : "var(--brass)" }}
                          >
                            {testingId === c.id ? "Test…" : "Tester maintenant"}
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}

        {tab === "apercus" && (
          <>
            <h1 className="serif" style={{ fontSize: 26, fontWeight: 600, margin: "0 0 4px" }}>Aperçus</h1>
            <p className="body" style={{ color: "var(--ink2)", margin: "0 0 18px", fontSize: 14 }}>
              Galeries générées par le moteur de rendu local (préparation print fidèle + mockups + carte de provenance).
              Chaque master passe l&apos;audit de fidélité colorimétrique vs l&apos;original du musée.
              {collection && collection.length > 0 ? ` ${collection.length} œuvre${collection.length > 1 ? "s" : ""}.` : ""}
            </p>
            {collection === null ? (
              <div className="body" style={{ color: "var(--ink2)" }}>Chargement…</div>
            ) : collection.length === 0 ? (
              <div className="cd" style={{ padding: 24 }}>
                <div className="body" style={{ fontSize: 13, color: "var(--ink2)" }}>
                  Aucun aperçu généré. Lance <code>python scripts/build_previews.py met &quot;Monet&quot; 4</code> puis commit/push.
                </div>
              </div>
            ) : (() => {
              const compteur = (sel: (w: PreviewWork) => string[]) => {
                const m = new Map<string, number>();
                for (const w of collection) for (const t of sel(w)) m.set(t, (m.get(t) || 0) + 1);
                return [...m.entries()].sort((a, b) => b[1] - a[1]);
              };
              const axes: [string, [string, number][]][] = [
                ["Sujet", compteur((w) => w.tags?.sujet ?? [])],
                ["Mouvement", compteur((w) => (w.tags?.mouvement ? [w.tags.mouvement] : []))],
                ["Palette", compteur((w) => w.palette?.tags ?? [])],
              ];
              // Tri curation : œuvres « à valider DP » en tête (à traiter), dépriorisées en fin.
              const rangCuration = (w: PreviewWork) =>
                w.curation?.nouveau ? -1 : w.curation?.deprioritized ? 1 : 0;
              const visibles = (collFiltre
                ? collection.filter((w) => (w.tags?.collections ?? []).includes(collFiltre))
                : collection
              )
                .slice()
                .sort((a, b) => rangCuration(a) - rangCuration(b));
              return (
                <>
                  <div className="cd" style={{ padding: 14, marginBottom: 18 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                      <span className="mono" style={{ fontSize: 10, letterSpacing: ".08em", color: "var(--ink2)" }}>COLLECTIONS</span>
                      {collFiltre && (
                        <button className="btn btn-ghost" onClick={() => setCollFiltre(null)} style={{ fontSize: 10 }}>
                          ✕ {collFiltre} ({visibles.length} œuvre{visibles.length > 1 ? "s" : ""})
                        </button>
                      )}
                    </div>
                    {axes.map(([axe, tags]) => tags.length ? (
                      <div key={axe} style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center", marginBottom: 8 }}>
                        <span className="mono" style={{ fontSize: 9, color: "var(--ink3)", width: 78, flexShrink: 0 }}>{axe}</span>
                        {tags.map(([t, n]) => (
                          <button key={t} className={"tab " + (t === collFiltre ? "on" : "")} onClick={() => setCollFiltre(t === collFiltre ? null : t)}>
                            {t} <span style={{ opacity: 0.55 }}>{n}</span>
                          </button>
                        ))}
                      </div>
                    ) : null)}
                    {(() => {
                      // Équilibre de palette = critère de curation (audit §T2 « casser le mur doré »).
                      const fam = new Map<string, number>();
                      for (const w of collection) { const f = w.palette?.famille; if (f) fam.set(f, (fam.get(f) ?? 0) + 1); }
                      if (!fam.size) return null;
                      const FAM: Record<string, string> = { doré: "#c9a44a", vert: "#5f8a5f", olive: "#8a8a4a", orange: "#cc8844", bleu: "#46689f", turquoise: "#4aa8a0", rose: "#c87a90", sépia: "#9a7b54" };
                      const total = collection.length || 1;
                      const dorePct = Math.round((100 * (fam.get("doré") ?? 0)) / total);
                      const ordered = [...fam.entries()].sort((a, b) => b[1] - a[1]);
                      return (
                        <div style={{ marginTop: 4 }}>
                          <div className="mono" style={{ fontSize: 9, color: dorePct > 45 ? "var(--brass)" : "var(--ink3)", marginBottom: 4 }}>
                            ÉQUILIBRE PALETTE — {dorePct}% doré{dorePct > 45 ? " · mur doré à diversifier (audit §T2)" : ""}
                          </div>
                          <div style={{ display: "flex", height: 10, borderRadius: 3, overflow: "hidden", border: "1px solid var(--line)" }} title={ordered.map(([f, n]) => `${f} ${n}`).join(" · ")}>
                            {ordered.map(([f, n]) => (
                              <span key={f} title={`${f} · ${n} (${Math.round((100 * n) / total)}%)`} style={{ width: `${(100 * n) / total}%`, background: FAM[f] ?? "var(--ink3)" }} />
                            ))}
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                  {visibles.map((w) => {
                const imgs: [string, string][] = [
                  [w.encadre || "catalogue/02_encadre_chene.jpg", "Encadré"],
                  ["lifestyle/galerie.jpg", "Scène galerie"],
                  ["lifestyle/scandinave.jpg", "Scène scandinave"],
                  ["lifestyle/atelier.jpg", "Scène atelier"],
                  ["catalogue/01_poster_nu.jpg", "Tirage nu"],
                  ["catalogue/03_detail.jpg", "Détail texture"],
                  ["catalogue/04_cadres.jpg", "Options cadres"],
                  ["catalogue/05_tailles.jpg", "Comparatif tailles"],
                  ["provenance_recto.png", "Provenance · recto"],
                  ["provenance_verso.png", "Provenance · verso"],
                ];
                const dep = w.curation?.deprioritized;
                return (
                  <div key={w.id} className="cd" style={{ padding: 18, marginBottom: 18, opacity: dep ? 0.55 : 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12 }}>
                      <div>
                        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                          <h2 className="serif" style={{ fontSize: 20, fontWeight: 600, margin: 0 }}>{w.title}</h2>
                          {w.curation?.dpAValider && (
                            <span className="badge" title={`Œuvre fraîchement sourcée${w.curation?.source ? ` (${w.curation.source})` : ""} — valider le gate domaine public + marque AVANT toute publication (jamais automatisé).`} style={{ background: "var(--warn-soft)", color: "var(--brass)" }}>
                              ⚠ À VALIDER DP
                            </span>
                          )}
                          {dep && (
                            <span className="badge" title={w.curation?.raison || "Œuvre dépriorisée (audit rentabilité §T2)"} style={{ background: "var(--paper2)", color: "var(--ink2)" }}>
                              ⬇ dépriorisée
                            </span>
                          )}
                        </div>
                        <div className="mono" style={{ fontSize: 11, color: "var(--ink2)", marginTop: 3 }}>
                          #{w.id} · {w.artist || "—"}{w.source ? ` · ${w.source}` : ""}
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
                        {w.fidelite && (
                          <span
                            className="badge"
                            title={`ΔE2000 ${w.fidelite.deltaE} · chroma ${Math.round(w.fidelite.chroma * 100)}% · dominante ${Math.round(w.fidelite.dominante * 100)}% (vs original musée)`}
                            style={
                              w.fidelite.verdict === "FIDÈLE"
                                ? { background: "var(--sage-soft)", color: "var(--sage)" }
                                : w.fidelite.verdict === "INFIDÈLE"
                                ? { background: "var(--ox-soft)", color: "var(--ox)" }
                                : { background: "var(--warn-soft)", color: "var(--brass)" }
                            }
                          >
                            {w.fidelite.verdict === "FIDÈLE" ? "✓ FIDÈLE" : w.fidelite.verdict} · ΔE {w.fidelite.deltaE}
                          </span>
                        )}
                        {w.wikidataUrl && (
                          <a href={w.wikidataUrl} target="_blank" rel="noreferrer" className="btn" style={{ textDecoration: "none", color: "var(--brass)" }}>
                            <ExternalLink size={11} style={{ display: "inline", marginRight: 4 }} />Wikidata
                          </a>
                        )}
                      </div>
                    </div>
                    {w.dpEvidence && (
                      <div className="body" style={{ fontSize: 12, lineHeight: 1.6, padding: 10, marginTop: 10, background: "var(--paper2)", borderLeft: "3px solid var(--sage)", borderRadius: "0 2px 2px 0" }}>
                        <ShieldCheck size={12} style={{ display: "inline", marginRight: 4, verticalAlign: "middle" }} />{w.dpEvidence}
                      </div>
                    )}
                    {(w.couleur || w.gamut) && (
                      <div className="mono" style={{ fontSize: 10, color: "var(--ink2)", marginTop: 8, display: "flex", gap: 14, flexWrap: "wrap" }}>
                        {w.couleur?.espaceSource && (
                          <span>
                            Couleur : {w.couleur.convertiSrgb ? `${w.couleur.espaceSource} → sRGB (ICC)` : "sRGB (livraison directe)"}
                          </span>
                        )}
                        {w.gamut && (w.gamut.methode === "icc-softproof" ? (
                          <span title="Soft-proof ICC — le RIP du POD fait le mapping final vers le papier">
                            Soft-proof ICC : {w.gamut.horsGamutPct}% hors-gamut{w.gamut.profilPapier ? ` (${w.gamut.profilPapier})` : ""}
                          </span>
                        ) : (
                          <span title="Pré-écran de chroma approximatif — PAS un vrai soft-proof. Fournir un profil papier pour une mesure ICC exacte ; le RIP du POD fait le mapping final.">
                            Saturation (approx.) : zone la + saturée {w.gamut.teinteARisque} (C* {w.gamut.chromaMax}) · {w.gamut.pctChromaElevee}% très saturé
                          </span>
                        ))}
                      </div>
                    )}
                    {w.layout && (
                      <div
                        className="mono"
                        style={{ fontSize: 10, color: "var(--ink2)", marginTop: 8 }}
                        title={`Taille catalogue la plus fidèle au ratio ${w.layout.ratioOeuvre} de l'œuvre (jamais de crop ni d'étirement — la bordure/passe-partout comble l'écart au format POD). Autres formats offerts : ${w.layout.variants.map((v) => `${v.taille} (bordure ${v.bordurePct}%)`).join(" · ")}.`}
                      >
                        Format fidèle : {w.layout.taille} ({w.layout.orientation}) · bordure {w.layout.bordurePct}% · {w.layout.variants.length} formats offerts
                      </div>
                    )}
                    {((w.tags?.collections?.length ?? 0) > 0 || (w.palette?.swatches?.length ?? 0) > 0) && (
                      <div style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                        {w.palette?.swatches?.length ? (
                          <div style={{ display: "flex", borderRadius: 3, overflow: "hidden", border: "1px solid var(--line)" }} title={`Palette — ${w.palette.famille}`}>
                            {w.palette.swatches.slice(0, 5).map((hex, i) => (
                              <span key={i} title={hex} style={{ width: 20, height: 20, background: hex, display: "inline-block" }} />
                            ))}
                          </div>
                        ) : null}
                        {(w.tags?.collections ?? []).map((t) => (
                          <button
                            key={t}
                            className="mtag"
                            onClick={() => setCollFiltre(t === collFiltre ? null : t)}
                            style={{ cursor: "pointer", border: t === collFiltre ? "1px solid var(--brass)" : "1px solid var(--line)", color: t === collFiltre ? "var(--brass)" : "var(--ink2)" }}
                          >
                            {t}
                          </button>
                        ))}
                      </div>
                    )}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))", gap: 10, marginTop: 14 }}>
                      {imgs.map(([file, label]) => (
                        <a key={file} href={`${w.dir}/${file}`} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}>
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img src={`${w.dir}/${file}`} alt={label} loading="lazy" style={{ width: "100%", aspectRatio: "1 / 1", objectFit: "cover", border: "1px solid var(--line)", borderRadius: 3, background: "var(--paper2)" }} />
                          <div className="mono" style={{ fontSize: 9, color: "var(--ink2)", marginTop: 3 }}>{label}</div>
                        </a>
                      ))}
                    </div>
                  </div>
                );
              })}
                </>
              );
            })()}
          </>
        )}

        {tab === "commandes" && (
          <>
            <h1 className="serif" style={{ fontSize: 26, fontWeight: 600, margin: "0 0 4px" }}>Commandes</h1>
            <p className="body" style={{ color: "var(--ink2)", margin: "0 0 18px", fontSize: 14 }}>
              Toutes les ventes Etsy avec leur statut de production et d'expédition. Routées automatiquement vers Gelato (standard) ou Prodigi (signature) selon la ligne de l'œuvre.
            </p>
            <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
              <button className="btn" onClick={loadOrders}><RefreshCw size={11} style={{ display: "inline", marginRight: 4 }} />Recharger</button>
            </div>

            {!orders ? (
              <div className="body" style={{ color: "var(--ink2)" }}>Chargement…</div>
            ) : orders.length === 0 ? (
              <div className="cd" style={{ padding: 24 }}>
                <div className="body" style={{ fontSize: 13, color: "var(--ink2)" }}>
                  Aucune commande pour le moment. Les ventes Etsy apparaîtront ici dès que le webhook <code>/api/etsy/webhook</code> sera connecté (cf. roadmap P3.4).
                </div>
              </div>
            ) : (
              <div className="cd" style={{ padding: 0, overflow: "hidden" }}>
                <table className="dt">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Œuvre</th>
                      <th>Produit</th>
                      <th>Fournisseur</th>
                      <th>Statut</th>
                      <th style={{ textAlign: "right" }}>Montant</th>
                      <th>Tracking</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((o) => {
                      const badgeClass = {
                        paid:          "badge badge-neutral",
                        in_production: "badge badge-warning",
                        shipped:       "badge badge-warning",
                        delivered:     "badge badge-success",
                        canceled:      "badge badge-danger",
                        error:         "badge badge-danger",
                      }[o.status] || "badge badge-neutral";
                      return (
                        <tr key={o.id}>
                          <td className="mono">{new Date(o.createdAt).toLocaleDateString("fr-FR")}</td>
                          <td>{o.work?.title || `#${o.workId}`}</td>
                          <td className="mono" style={{ fontSize: 12 }}>{o.product}</td>
                          <td className="mono" style={{ fontSize: 12 }}>
                            {o.provider === "gelato" ? "🇫🇷 Gelato" : "🇬🇧 Prodigi"}
                          </td>
                          <td><span className={badgeClass}>{o.status}</span></td>
                          <td className="mono" style={{ textAlign: "right" }}>{o.amount.toFixed(2)} {o.currency}</td>
                          <td className="mono" style={{ fontSize: 11 }}>
                            {o.trackingUrl ? (
                              <a href={o.trackingUrl} target="_blank" rel="noreferrer" style={{ color: "var(--brass)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: 4 }}>
                                <Truck size={11} />{o.trackingCode || "voir"} <ExternalLink size={9} />
                              </a>
                            ) : o.trackingCode || "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {tab === "viabilite" && (
          <>
            <h1 className="serif" style={{ fontSize: 26, fontWeight: 600, margin: "0 0 4px" }}>Viabilité</h1>
            <p className="body" style={{ color: "var(--ink2)", margin: "0 0 18px", fontSize: 14 }}>Mêmes calculs que le calculateur Excel — ajuste, le seuil se recalcule.</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, maxWidth: 760 }}>
              <div className="cd" style={{ padding: 16 }}>
                {([
                  ["prix",          "Prix de vente moyen ($)"],
                  ["port",          "Port encaissé ($)"],
                  ["base",          "Base fournisseur + envoi ($)"],
                  ["coutDesign",    "Coût chargé / design ($)"],
                  ["designs",       "Designs produits / mois"],
                  ["ventesGagnant", "Ventes / gagnant / mois"],
                  ["fixes",         "Frais fixes mensuels ($)"],
                  ["hitrate",       "Hit-rate (%)"],
                ] as const).map(([k, l]) => (
                  <label key={k} style={{ display: "block", marginBottom: 10 }}>
                    <span className="body" style={{ fontSize: 12, color: "var(--ink2)" }}>{l}</span>
                    <input className="inp" type="number" value={cfg[k]} onChange={(e) => setCfg({ ...cfg, [k]: +e.target.value })} />
                  </label>
                ))}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <Kpi k="Marge nette / vente" v={`${econ.marge.toFixed(2)} $`} />
                <Kpi k="Seuil de rentabilité" v={`${econ.seuil.toFixed(2)}%`} tone={cfg.hitrate >= econ.seuil ? "var(--sage)" : "var(--ox)"} sub={cfg.hitrate >= econ.seuil ? "rentable au hit-rate actuel" : "sous le seuil — augmenter marge ou hit-rate"} />
                <Kpi k="Résultat mensuel projeté" v={`${Math.round(econ.res)} $`} tone={econ.res >= 0 ? "var(--sage)" : "var(--ox)"} sub={`${Math.round(econ.res * 12)} $ / an`} />
              </div>
            </div>
          </>
        )}

        {tab === "import" && (
          <>
            <h1 className="serif" style={{ fontSize: 26, fontWeight: 600, margin: "0 0 4px" }}>Import du registre</h1>
            <p className="body" style={{ color: "var(--ink2)", margin: "0 0 16px", fontSize: 14 }}>
              Colle le JSON produit par <code>agents/sourcing_agent.py</code> (<code>registre_provenance.json</code>).
              Les lignes <code>REJET</code> sont automatiquement filtrées ; les lignes <code>REVIEW</code> arrivent avec <code>gateUe = null</code> pour validation humaine.
            </p>
            <textarea className="inp mono" rows={10} placeholder='[ { "objectID": 12345, "title": "...", ... } ]' value={imp} onChange={(e) => setImp(e.target.value)} style={{ maxWidth: 760, fontSize: 12 }} />
            <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
              <button className="btn btn-primary" disabled={busy || !imp.trim()} onClick={importJson}>
                {busy ? "Import…" : "Importer le JSON"}
              </button>
              <button className="btn" onClick={() => { setImp(""); }}>Vider le champ</button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

function Row({ l, v }: { l: string; v: string | null }) {
  return <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}><span style={{ color: "var(--ink2)" }}>{l}</span><span style={{ textAlign: "right" }}>{v || "—"}</span></div>;
}
function Gate({ ok, label }: { ok: boolean | null; label: string }) {
  const c = ok === true ? "var(--sage)" : ok === false ? "var(--ox)" : "var(--brass)";
  const t = ok === true ? "✓" : ok === false ? "✗" : "?";
  return <span className="pill" style={{ color: c }}>{t} {label}</span>;
}
function Mfield({ l, v, mono, block, sub, subColor }: { l: string; v: string; mono?: boolean; block?: boolean; sub?: string; subColor?: string }) {
  return (
    <div style={{ marginTop: 8 }}>
      <div className="mono" style={{ fontSize: 10, color: "var(--ink2)", letterSpacing: ".06em", marginBottom: 2 }}>
        {l.toUpperCase()} <span style={{ color: "var(--ink2)" }}>· {v.length} chars</span>
        {sub && <span style={{ color: subColor || "var(--ink2)", marginLeft: 8 }}>· {sub}</span>}
      </div>
      <div className={mono ? "mono" : "body"} style={{ fontSize: mono ? 12 : 13, padding: block ? "4px 0" : 0, color: "var(--ink)" }}>
        {v || <span style={{ color: "var(--ink2)" }}>—</span>}
      </div>
    </div>
  );
}
