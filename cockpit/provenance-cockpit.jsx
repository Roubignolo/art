import React, { useState, useEffect, useMemo } from "react";
import { Archive, LayoutGrid, ListChecks, Calculator, Upload, Check, X, ChevronRight, Leaf, Image as ImageIcon, ShieldCheck, AlertTriangle, Sparkles } from "lucide-react";

/* ---------- persistance réelle (window.storage), repli mémoire ---------- */
const mem = {};
const store = {
  async get(k) {
    try { if (window.storage) { const r = await window.storage.get(k, false); return r ? JSON.parse(r.value) : null; } } catch (e) {}
    return k in mem ? mem[k] : null;
  },
  async set(k, v) {
    const s = JSON.stringify(v);
    try { if (window.storage) { await window.storage.set(k, s, false); return; } } catch (e) {}
    mem[k] = v;
  },
};

/* ---------- données d'exemple (style API du Met) ---------- */
const SAMPLE = [
  { id: 363854, title: "Fritillaria (planche botanique)", artist: "Pierre-Joseph Redouté", death: 1840, date: "1827", dept: "Drawings and Prints", medium: "Stipple engraving", res: 5400, gates: { us: true, ue: true, g2: true }, status: "score", scores: { mom: 8, attr: 9, trad: 9, sat: 5 }, hook: "Gravure de Redouté, le « Raphaël des fleurs », pour l'impératrice Joséphine." },
  { id: 419242, title: "Étude de fougères", artist: "Anonyme", death: null, date: "1885", dept: "Photographs", medium: "Albumen print", res: 3800, gates: { us: true, ue: true, g2: true }, status: "gate", scores: { mom: 7, attr: 5, trad: 8, sat: 6 }, hook: "" },
  { id: 339001, title: "Iris, planche d'herbier", artist: "Mary Vaux Walcott", death: 1940, date: "1925", dept: "Drawings and Prints", medium: "Watercolor", res: 6200, gates: { us: true, ue: true, g2: true }, status: "restore", scores: { mom: 9, attr: 8, trad: 9, sat: 4 }, hook: "Aquarelle d'une botaniste pionnière de la Smithsonian." },
  { id: 209837, title: "Magnolia grandiflora", artist: "Georg D. Ehret", death: 1770, date: "1750", dept: "Drawings and Prints", medium: "Hand-colored engraving", res: 4800, gates: { us: true, ue: true, g2: true }, status: "publish", scores: { mom: 8, attr: 9, trad: 10, sat: 6 }, hook: "Ehret, maître de l'illustration botanique du XVIIIe siècle." },
  { id: 110055, title: "Composition florale (étude)", artist: "Auteur inconnu", death: null, date: "1912", dept: "Drawings and Prints", medium: "Lithograph", res: 2400, gates: { us: true, ue: null, g2: true }, status: "gate", scores: { mom: 6, attr: 4, trad: 7, sat: 7 }, hook: "" },
];

const WEIGHTS = { mom: 0.30, attr: 0.20, trad: 0.25, sat: 0.25 };
const THRESHOLD = 6.5;
const STAGES = [
  { key: "source", label: "Sourcé", icon: Archive },
  { key: "gate", label: "Gate à valider", icon: ShieldCheck },
  { key: "score", label: "Scoré", icon: Sparkles },
  { key: "restore", label: "Restauré", icon: ImageIcon },
  { key: "publish", label: "Publié", icon: Check },
];

function weighted(s) { return s.mom * WEIGHTS.mom + s.attr * WEIGHTS.attr + s.trad * WEIGHTS.trad + s.sat * WEIGHTS.sat; }
function gateFail(g) { return g.us === false || g.ue === false || g.g2 === false; }
function decide(w) {
  if (gateFail(w.gates)) return { d: "REJET", c: "var(--ox)" };
  if (w.gates.ue === null) return { d: "À VALIDER", c: "var(--brass)" };
  const sc = weighted(w.scores);
  if (sc >= THRESHOLD) return { d: "PRODUIRE", c: "var(--sage)" };
  if (sc >= 5) return { d: "FILE D'ATTENTE", c: "var(--brass)" };
  return { d: "REJET", c: "var(--ox)" };
}

const DEFAULTS = { prix: 25, port: 5, base: 16, coutDesign: 0.5, designs: 1000, ventesGagnant: 3, fixes: 150, hitrate: 5 };

export default function App() {
  const [works, setWorks] = useState(null);
  const [cfg, setCfg] = useState(DEFAULTS);
  const [tab, setTab] = useState("pilotage");
  const [sel, setSel] = useState(null);
  const [imp, setImp] = useState("");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    (async () => {
      const w = await store.get("works"); const c = await store.get("cfg");
      setWorks(w || SAMPLE); setCfg(c || DEFAULTS); setLoaded(true);
    })();
  }, []);
  useEffect(() => { if (loaded && works) store.set("works", works); }, [works, loaded]);
  useEffect(() => { if (loaded) store.set("cfg", cfg); }, [cfg, loaded]);

  const econ = useMemo(() => {
    const enc = cfg.prix + cfg.port;
    const fees = enc * (0.065 + 0.03) + 0.25 + 0.20;
    const marge = enc - fees - cfg.base;
    const seuil = (cfg.designs * cfg.coutDesign + cfg.fixes) / (cfg.designs * cfg.ventesGagnant * marge);
    const res = cfg.designs * (cfg.hitrate / 100) * cfg.ventesGagnant * marge - cfg.designs * cfg.coutDesign - cfg.fixes;
    return { marge, seuil: seuil * 100, res };
  }, [cfg]);

  if (!works) return null;

  const setW = (id, patch) => setWorks(works.map((w) => (w.id === id ? { ...w, ...patch } : w)));
  const selected = works.find((w) => w.id === sel);

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
  .btn:hover{background:var(--paper2)}
  `;

  const Kpi = ({ k, v, sub, tone }) => (
    <div className="cd" style={{ padding: 16 }}>
      <div className="mono" style={{ fontSize: 10, letterSpacing: ".08em", color: "var(--ink2)", textTransform: "uppercase" }}>{k}</div>
      <div className="serif" style={{ fontSize: 30, fontWeight: 600, color: tone || "var(--ink)", lineHeight: 1.1, marginTop: 6 }}>{v}</div>
      {sub && <div className="body" style={{ fontSize: 12, color: "var(--ink2)", marginTop: 2 }}>{sub}</div>}
    </div>
  );

  return (
    <div className="body" style={{ background: "var(--paper)", color: "var(--ink)", minHeight: 640, display: "flex" }}>
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
        {[["pilotage", "Pilotage", LayoutGrid], ["oeuvres", "Œuvres", ListChecks], ["viabilite", "Viabilité", Calculator], ["import", "Import", Upload]].map(([k, l, I]) => (
          <div key={k} className={"navi " + (tab === k ? "on" : "")} onClick={() => setTab(k)}>
            <I size={15} /> <span>{l}</span>
          </div>
        ))}
        <div style={{ padding: 14, marginTop: 12 }}>
          <div className="cd" style={{ padding: 12, background: econ.hitActual >= 0 ? "var(--card)" : "var(--card)" }}>
            <div className="mono" style={{ fontSize: 9, color: "var(--ink2)", letterSpacing: ".08em" }}>SEUIL DE RENTABILITÉ</div>
            <div className="serif" style={{ fontSize: 22, fontWeight: 600, color: cfg.hitrate >= econ.seuil ? "var(--sage)" : "var(--ox)" }}>{econ.seuil.toFixed(2)}%</div>
            <div className="body" style={{ fontSize: 11, color: "var(--ink2)" }}>hit-rate actuel {cfg.hitrate}% {cfg.hitrate >= econ.seuil ? "✓ rentable" : "✗ sous le seuil"}</div>
          </div>
        </div>
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
              <h1 className="serif" style={{ fontSize: 26, fontWeight: 600, margin: "0 0 14px" }}>Œuvres</h1>
              <div className="cd">
                {works.map((w) => {
                  const dc = decide(w);
                  return (
                    <div key={w.id} className="wrow" onClick={() => setSel(w.id)} style={{ display: "flex", alignItems: "center", gap: 10, padding: "11px 14px", borderBottom: "1px solid var(--paper2)", background: sel === w.id ? "var(--paper2)" : "" }}>
                      <div style={{ flex: 1 }}>
                        <div className="body" style={{ fontSize: 14 }}>{w.title}</div>
                        <div className="mono" style={{ fontSize: 10, color: "var(--ink2)" }}>{w.artist} · {w.date} · {w.res}px</div>
                      </div>
                      <span className="pill" style={{ color: dc.c }}>{dc.d}</span>
                      <ChevronRight size={14} color="var(--ink2)" />
                    </div>
                  );
                })}
              </div>
            </div>

            {selected && (
              <div style={{ flex: 1 }}>
                <div className="cd" style={{ padding: 18 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                    <div>
                      <h2 className="serif" style={{ fontSize: 20, fontWeight: 600, margin: 0 }}>{selected.title}</h2>
                      <div className="mono" style={{ fontSize: 11, color: "var(--ink2)", marginTop: 3 }}>#{selected.id} · {selected.dept}</div>
                    </div>
                    <X size={18} style={{ cursor: "pointer" }} onClick={() => setSel(null)} />
                  </div>

                  {/* Provenance */}
                  <div style={{ marginTop: 14, fontSize: 13, lineHeight: 1.7 }} className="body">
                    <Row l="Artiste" v={`${selected.artist}${selected.death ? ` (†${selected.death})` : ""}`} />
                    <Row l="Date" v={selected.date} />
                    <Row l="Médium" v={selected.medium} />
                    <Row l="Résolution" v={`${selected.res} px ${selected.res >= 3000 ? "✓" : "✗ insuffisant"}`} />
                    <Row l="Source" v="The Met — Open Access (CC0)" />
                  </div>

                  {/* Gates */}
                  <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--line)" }}>
                    <div className="mono" style={{ fontSize: 10, letterSpacing: ".08em", color: "var(--ink2)", marginBottom: 8 }}>GATES DE CONFORMITÉ</div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <Gate ok={selected.gates.us} label="DP US" />
                      <Gate ok={selected.gates.ue} label="DP UE" />
                      <Gate ok={selected.gates.g2} label="Sans marque" />
                      <Gate ok={selected.res >= 3000} label="Résolution" />
                    </div>
                    {selected.gates.ue === null && (
                      <div style={{ marginTop: 10, padding: 10, background: "var(--paper2)", borderRadius: 2 }}>
                        <div className="body" style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 6 }}>
                          <AlertTriangle size={14} color="var(--brass)" /> Date de l'auteur inconnue — validation humaine requise.
                        </div>
                        <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
                          <button className="btn" style={{ color: "var(--sage)" }} onClick={() => setW(selected.id, { gates: { ...selected.gates, ue: true }, status: "score" })}><Check size={11} style={{ display: "inline" }} /> Valider DP</button>
                          <button className="btn" style={{ color: "var(--ox)" }} onClick={() => setW(selected.id, { gates: { ...selected.gates, ue: false } })}><X size={11} style={{ display: "inline" }} /> Rejeter</button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Scoring */}
                  {!gateFail(selected.gates) && selected.gates.ue !== null && (
                    <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--line)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                        <span className="mono" style={{ fontSize: 10, letterSpacing: ".08em", color: "var(--ink2)" }}>SCORING (4 AXES)</span>
                        <span className="serif" style={{ fontSize: 22, fontWeight: 600, color: decide(selected).c }}>{weighted(selected.scores).toFixed(1)}<span style={{ fontSize: 12, color: "var(--ink2)" }}>/10</span></span>
                      </div>
                      {[["mom", "Momentum esthétique", "30%"], ["attr", "Attribution / récit", "20%"], ["trad", "Traduisibilité produit", "25%"], ["sat", "Espace concurrentiel", "25%"]].map(([k, l, p]) => (
                        <div key={k} style={{ marginBottom: 9 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }} className="body">
                            <span>{l} <span className="mono" style={{ fontSize: 9, color: "var(--ink2)" }}>{p}</span></span>
                            <span className="mono">{selected.scores[k]}</span>
                          </div>
                          <input type="range" min="0" max="10" value={selected.scores[k]} onChange={(e) => setW(selected.id, { scores: { ...selected.scores, [k]: +e.target.value } })} />
                        </div>
                      ))}
                      <textarea className="inp body" rows={2} placeholder="Accroche provenance (storytelling de la fiche produit)…" value={selected.hook} onChange={(e) => setW(selected.id, { hook: e.target.value })} style={{ marginTop: 6, resize: "vertical" }} />
                      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                        {STAGES.map((s) => (
                          <button key={s.key} className="btn" style={{ borderColor: selected.status === s.key ? "var(--brass)" : "var(--line)", color: selected.status === s.key ? "var(--brass)" : "var(--ink2)" }} onClick={() => setW(selected.id, { status: s.key })}>{s.label}</button>
                        ))}
                      </div>
                    </div>
                  )}
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
                {[["prix", "Prix de vente moyen ($)"], ["port", "Port encaissé ($)"], ["base", "Base fournisseur + envoi ($)"], ["coutDesign", "Coût chargé / design ($)"], ["designs", "Designs produits / mois"], ["ventesGagnant", "Ventes / gagnant / mois"], ["fixes", "Frais fixes mensuels ($)"], ["hitrate", "Hit-rate (%)"]].map(([k, l]) => (
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
            <p className="body" style={{ color: "var(--ink2)", margin: "0 0 16px", fontSize: 14 }}>Colle le JSON produit par le sous-agent Sourcing (registre_provenance.json), ou recharge l'exemple.</p>
            <textarea className="inp mono" rows={10} placeholder='[ { "objectID": 12345, "title": "...", ... } ]' value={imp} onChange={(e) => setImp(e.target.value)} style={{ maxWidth: 760, fontSize: 12 }} />
            <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
              <button className="btn" style={{ color: "var(--sage)" }} onClick={() => {
                try {
                  const arr = JSON.parse(imp);
                  const mapped = arr.map((o) => ({
                    id: o.objectID || o.id || Math.random(), title: o.title || "Sans titre", artist: o.artist || "—",
                    death: o.artist_death ? +String(o.artist_death).slice(0, 4) : null, date: o.object_date || o.date || "—",
                    dept: o.department || "—", medium: o.medium || "—", res: o.resolution_px || o.res || 0,
                    gates: { us: o.gate_g1_us_g3 ?? true, ue: o.gate_g1_ue ?? null, g2: o.gate_g2_marque ?? true },
                    status: "gate", scores: { mom: 5, attr: 5, trad: 5, sat: 5 }, hook: "",
                  }));
                  setWorks(mapped); setTab("oeuvres");
                } catch (e) { alert("JSON invalide : " + e.message); }
              }}>Importer le JSON</button>
              <button className="btn" onClick={() => { setWorks(SAMPLE); setTab("oeuvres"); }}>Recharger l'exemple</button>
              <button className="btn" style={{ color: "var(--ox)" }} onClick={() => setWorks([])}>Vider</button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

function Row({ l, v }) {
  return <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}><span style={{ color: "var(--ink2)" }}>{l}</span><span style={{ textAlign: "right" }}>{v}</span></div>;
}
function Gate({ ok, label }) {
  const c = ok === true ? "var(--sage)" : ok === false ? "var(--ox)" : "var(--brass)";
  const t = ok === true ? "✓" : ok === false ? "✗" : "?";
  return <span className="pill" style={{ color: c }}>{t} {label}</span>;
}
