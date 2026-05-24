"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import {
  Archive, LayoutGrid, ListChecks, Calculator, Upload, Check, X,
  ChevronRight, Leaf, Image as ImageIcon, ShieldCheck, AlertTriangle,
  Sparkles, RefreshCw, Wand2, Languages,
} from "lucide-react";

/* ---------- Types ---------- */
type MarketingItem = {
  title: string;
  listingTitle: string;
  description: string;
  hook: string;
  tags: string[];
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
  momentum: number;
  attribution: number;
  translatab: number;
  competition: number;
  scoreFinal: number | null;
  hook: string | null;
  angle: string | null;
  marketing: Record<string, MarketingItem> | null;
  status: string;
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
  const [tab, setTab] = useState<"pilotage" | "oeuvres" | "viabilite" | "import">("pilotage");
  const [sel, setSel] = useState<number | null>(null);
  const [imp, setImp] = useState("");
  const [busy, setBusy] = useState(false);
  const [busyMkt, setBusyMkt] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [lang, setLang] = useState<string>("fr");

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

  if (!works) {
    return <div style={{ padding: 40, fontFamily: "system-ui", color: "#5C5345" }}>Chargement…</div>;
  }

  const selected = sel ? works.find((w) => w.id === sel) : null;

  const css = `
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,900&family=Newsreader:ital,opsz@0,6..72;1,6..72&family=JetBrains+Mono:wght@400;600&display=swap');
  :root{--paper:#F2EBDD;--paper2:#EAE0CC;--card:#FBF7EE;--ink:#211C15;--ink2:#5C5345;--line:#D8CBB0;--brass:#A9803F;--sage:#4F6B4A;--ox:#8A3A30;}
  *{box-sizing:border-box}
  .cd{background:var(--card);border:1px solid var(--line);border-radius:2px;box-shadow:0 1px 0 rgba(33,28,21,.04)}
  .serif{font-family:'Fraunces',serif} .body{font-family:'Newsreader',serif} .mono{font-family:'JetBrains Mono',monospace}
  .navi{display:flex;align-items:center;gap:10px;padding:10px 14px;cursor:pointer;border-left:2px solid transparent;color:var(--ink2);font-size:14px}
  .navi:hover{background:var(--paper2)} .navi.on{border-left-color:var(--brass);color:var(--ink);background:var(--paper2)}
  .pill{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.04em;padding:2px 7px;border-radius:999px;border:1px solid currentColor;display:inline-block}
  .wrow{cursor:pointer} .wrow:hover{background:var(--paper2)}
  input[type=range]{accent-color:var(--brass);width:100%}
  .inp{font-family:'JetBrains Mono',monospace;background:var(--paper);border:1px solid var(--line);border-radius:2px;padding:6px 8px;width:100%;color:var(--ink);font-size:13px}
  .btn{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.05em;padding:6px 10px;border-radius:2px;cursor:pointer;border:1px solid var(--line);background:var(--paper)}
  .btn:hover{background:var(--paper2)} .btn:disabled{opacity:.5;cursor:not-allowed}
  .err{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--ox);padding:8px 14px;border-top:1px solid var(--line);background:#FBEAE5}
  .thumb{width:46px;height:46px;object-fit:cover;border-radius:2px;border:1px solid var(--line);background:var(--paper);flex-shrink:0}
  .thumb-empty{display:flex;align-items:center;justify-content:center;color:var(--ink2)}
  .preview{width:100%;max-height:280px;object-fit:contain;background:var(--paper);border:1px solid var(--line);border-radius:2px}
  .tab{font-family:'JetBrains Mono',monospace;font-size:11px;padding:5px 10px;border:1px solid var(--line);background:var(--paper);cursor:pointer;border-radius:2px}
  .tab.on{border-color:var(--brass);color:var(--brass);background:var(--card)}
  .mtag{font-family:'JetBrains Mono',monospace;font-size:10px;background:var(--paper2);color:var(--ink2);padding:2px 6px;border-radius:2px;margin:0 4px 4px 0;display:inline-block}
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
        <div style={{ padding: "20px 16px", borderBottom: "1px solid var(--line)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Leaf size={18} color="var(--brass)" />
            <span className="serif" style={{ fontWeight: 900, fontSize: 19, letterSpacing: "-.01em" }}>PROVENANCE</span>
          </div>
          <div className="mono" style={{ fontSize: 9, letterSpacing: ".18em", color: "var(--ink2)", marginTop: 4 }}>POSTE DE PILOTAGE</div>
        </div>
        {([["pilotage", "Pilotage", LayoutGrid], ["oeuvres", "Œuvres", ListChecks], ["viabilite", "Viabilité", Calculator], ["import", "Import", Upload]] as const).map(([k, l, I]) => (
          <div key={k} className={"navi " + (tab === k ? "on" : "")} onClick={() => setTab(k)}>
            <I size={15} /> <span>{l}</span>
          </div>
        ))}
        <div className="navi" onClick={reload}><RefreshCw size={15} /> <span>Recharger</span></div>
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
                          return (
                            <div className="body" style={{ fontSize: 13, lineHeight: 1.55 }}>
                              <Mfield l="Titre court" v={m.title} />
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
                </div>
              </div>
            )}
          </div>
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
              <button className="btn" disabled={busy || !imp.trim()} style={{ color: "var(--sage)" }} onClick={importJson}>
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
function Mfield({ l, v, mono, block }: { l: string; v: string; mono?: boolean; block?: boolean }) {
  return (
    <div style={{ marginTop: 8 }}>
      <div className="mono" style={{ fontSize: 10, color: "var(--ink2)", letterSpacing: ".06em", marginBottom: 2 }}>
        {l.toUpperCase()} <span style={{ color: "var(--ink2)" }}>· {v.length} chars</span>
      </div>
      <div className={mono ? "mono" : "body"} style={{ fontSize: mono ? 12 : 13, padding: block ? "4px 0" : 0, color: "var(--ink)" }}>
        {v || <span style={{ color: "var(--ink2)" }}>—</span>}
      </div>
    </div>
  );
}
