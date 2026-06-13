/**
 * Mise en page produit — port TypeScript fidèle de `agents/render/layout.py`.
 *
 * Une œuvre de ratio « musée » ne doit JAMAIS être rognée ni déformée : on
 * choisit la taille catalogue POD dont le ratio est le plus proche (bordure
 * minimale) et on comble par une bordure/passe-partout. Ce module permet au
 * cockpit et au constructeur de listing de calculer les variantes FIDÈLES
 * à offrir pour CHAQUE œuvre (selon son ratio), sans appeler Python.
 *
 * Géométrie ENTIÈRE identique à layout.py : taille catalogue, orientation et
 * ouverture/marges en px partagent le même arrondi banquier (`pyRound`). Les
 * valeurs d'AFFICHAGE arrondies (ratio, bordure %) peuvent différer d'un cran
 * sur un demi exact (`toFixed` arrondit away-from-zero, Python `round` vers le
 * pair) — cosmétique, sans incidence sur le choix de taille. Symétrie vérifiée
 * par tests/test_layout_ts_symmetry.py (exécute ce port via Node). Voir
 * docs/decision-encadrement-tailles.md.
 */

export type Fournisseur = "gelato" | "prodigi";

export type TailleCatalogue = {
  label: string;
  courtCm: number; // petit côté
  longCm: number; // grand côté
  fournisseurs: readonly Fournisseur[];
};

export function ratioTaille(t: TailleCatalogue): number {
  // toujours ≥ 1 (grand/petit)
  return t.longCm / t.courtCm;
}

// Tailles murales réelles, convergentes Gelato/Prodigi (cm) — copie de layout.CATALOGUE.
export const CATALOGUE: readonly TailleCatalogue[] = [
  { label: "20×25", courtCm: 20, longCm: 25, fournisseurs: ["prodigi"] }, // 8×10" · 1.25
  { label: "28×36", courtCm: 28, longCm: 35.6, fournisseurs: ["prodigi"] }, // 11×14" · 1.27
  { label: "30×40", courtCm: 30, longCm: 40, fournisseurs: ["gelato", "prodigi"] }, // 12×16" · 1.33
  { label: "A3 30×42", courtCm: 29.7, longCm: 42, fournisseurs: ["gelato"] }, // 1.414
  { label: "40×50", courtCm: 40, longCm: 50, fournisseurs: ["gelato", "prodigi"] }, // 16×20" · 1.25
  { label: "50×70", courtCm: 50, longCm: 70, fournisseurs: ["gelato", "prodigi"] }, // ~20×28" · 1.40
  { label: "A2 42×59", courtCm: 42, longCm: 59.4, fournisseurs: ["gelato"] }, // 1.414
  { label: "61×91", courtCm: 61, longCm: 91.4, fournisseurs: ["gelato", "prodigi"] }, // 24×36" · 1.50
  { label: "30×30", courtCm: 30, longCm: 30, fournisseurs: ["gelato", "prodigi"] }, // carré 1.0
  { label: "50×50", courtCm: 50, longCm: 50, fournisseurs: ["gelato", "prodigi"] }, // carré 1.0
];

export type Orientation = "paysage" | "portrait" | "carré";

export type PlanMiseEnPage = {
  taille: string; // libellé catalogue
  fournisseur: Fournisseur;
  orientation: Orientation;
  ratioOeuvre: number; // grand/petit de l'œuvre
  ratioTaille: number; // grand/petit de la taille catalogue
  margeHFrac: number; // bordure gauche+droite, fraction de la largeur d'œuvre
  margeVFrac: number; // bordure haut+bas, fraction de la hauteur d'œuvre
  bordurePct: number; // part de la surface finale occupée par la bordure (0-100)
  strategie: "bordure-fichier" | "passe-partout";
};

function orientationDe(ratioBrut: number): Orientation {
  if (ratioBrut > 1.05) return "paysage";
  if (ratioBrut < 0.95) return "portrait";
  return "carré";
}

/** round() de Python : arrondi au plus proche, .5 exact → vers le PAIR (Math.round arrondit vers le haut). */
function pyRound(x: number): number {
  const floor = Math.floor(x);
  if (x - floor === 0.5) return floor % 2 === 0 ? floor : floor + 1;
  return Math.round(x);
}

/**
 * Géométrie de l'ouverture (œuvre + passe-partout) au ratio cible exact,
 * contenant l'œuvre + au moins `matMinFrac` du petit côté en marge par bord.
 * Identique à layout.ouverture (jamais de crop), mêmes arrondis que Python.
 */
export function ouverture(
  aw: number,
  ah: number,
  ratioCible: number,
  matMinFrac = 0.08,
): { ow: number; oh: number; margeX: number; margeY: number } {
  const m = Math.floor(Math.min(aw, ah) * matMinFrac);
  let oh = Math.max(ah + 2 * m, Math.ceil((aw + 2 * m) / ratioCible));
  const ow = Math.max(aw + 2 * m, pyRound(ratioCible * oh));
  oh = Math.max(oh, pyRound(ow / ratioCible)); // cohérence après arrondis
  return { ow, oh, margeX: Math.floor((ow - aw) / 2), margeY: Math.floor((oh - ah) / 2) };
}

/** Taille catalogue dont le ratio est le plus proche de l'œuvre (bordure minimale). */
export function meilleureTaille(ratioOeuvre: number, fournisseur?: Fournisseur): TailleCatalogue {
  let cands = CATALOGUE.filter((t) => !fournisseur || t.fournisseurs.includes(fournisseur));
  // exclure le carré sauf si l'œuvre est ~carrée (sinon bordure énorme)
  if (ratioOeuvre > 1.12) {
    const nonCarre = cands.filter((t) => ratioTaille(t) > 1.05);
    if (nonCarre.length) cands = nonCarre;
  }
  return cands.reduce((best, t) =>
    Math.abs(ratioTaille(t) - ratioOeuvre) < Math.abs(ratioTaille(best) - ratioOeuvre) ? t : best,
  );
}

// Arrondi DÉCIMAL d'affichage. toFixed évite l'amplification d'erreur flottante
// de Math.round(x*10)/10 ; il diverge de round() banquier de Python uniquement
// sur un demi exact (away-from-zero vs vers-le-pair) → écart d'un cran possible
// sur ratio/bordure %. Cosmétique : taille/orientation/géométrie px n'en dépendent pas.
const round3 = (n: number) => Number(n.toFixed(3));
const round1 = (n: number) => Number(n.toFixed(1));

/** Plan de mise en page d'une œuvre aw×ah px pour un fournisseur (cf. layout.planifier). */
export function planifier(
  aw: number,
  ah: number,
  fournisseur: Fournisseur = "gelato",
  taille?: TailleCatalogue,
  matMinFrac = 0.08,
): PlanMiseEnPage {
  const ratioBrut = aw / ah;
  const orient = orientationDe(ratioBrut);
  const ratioOeuvre = Math.max(aw, ah) / Math.min(aw, ah);
  const t = taille ?? meilleureTaille(ratioOeuvre, fournisseur);

  let ratioCible = orient === "portrait" ? 1 / ratioTaille(t) : ratioTaille(t);
  if (orient === "carré") ratioCible = 1;
  const { ow, oh, margeX, margeY } = ouverture(aw, ah, ratioCible, matMinFrac);

  return {
    taille: t.label,
    fournisseur,
    orientation: orient,
    ratioOeuvre: round3(ratioOeuvre),
    ratioTaille: round3(ratioTaille(t)),
    margeHFrac: round3((2 * margeX) / aw),
    margeVFrac: round3((2 * margeY) / ah),
    bordurePct: round1(100 * (1 - (aw * ah) / (ow * oh))),
    strategie: fournisseur === "prodigi" ? "passe-partout" : "bordure-fichier",
  };
}

/** Un plan par taille catalogue offerte par le fournisseur (variantes du listing). */
export function plansVariants(aw: number, ah: number, fournisseur: Fournisseur = "gelato"): PlanMiseEnPage[] {
  return CATALOGUE.filter((t) => t.fournisseurs.includes(fournisseur)).map((t) =>
    planifier(aw, ah, fournisseur, t),
  );
}
