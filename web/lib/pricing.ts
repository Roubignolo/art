/**
 * Modèle de prix Gelato — SOURCE DE VÉRITÉ unique (cockpit + /api/etsy/publish).
 * C'est ce fichier qui s'exécute en prod ; docs/economie-gelato.md est la note de
 * calcul (annotée pour matcher ce code : réglementaire 0,47 % + SAV sur prix+port).
 *
 * Tailles = grille musée décidée (docs/decision-encadrement-tailles.md §5.1). Les
 * coûts base/port Gelato sont des médians/extrapolations à confirmer via l'API
 * Gelato (`aConfirmer`). Pour les tailles musée (30×40 / 50×70 / 61×91), le PRIX
 * lui-même est une proposition de départ — l'arbitrage des niveaux est une
 * décision founder (cf. docs/audit-rentabilite.md §T3). Frais Etsy = réel UE 2026.
 */

export type Produit = {
  id: string;
  type: "poster" | "framed" | "canvas" | "giftable";
  label: string;
  format: string;
  prix: number;
  port: number;
  coutBase: number;
  portGelato: number;
  ligne: "standard" | "signature"; // routing POD : standard→Gelato, signature→Prodigi
  aConfirmer?: string[];
};

export const FRAIS_ETSY = {
  transactionPct: 0.065,
  paiementPct: 0.04,
  paiementFixe: 0.3,
  listingAmortiParVente: 0.05,
  reglementairePct: 0.0047, // frais réglementaires (opérations FR/UE) 2026
};

export const HYPOTHESES = {
  provisionSavPct: 0.05,
  insertProvenanceParColis: 0.5,
  changeEurUsd: 0.92,
  mixRealiste: { encadrePct: 0.6, nuPct: 0.4 },
  margeMoyennePonderee: 19.95,
};

export const GELATO_PLUS = {
  coutMensuelEurApprox: 18.5,
  remiseBasePct: 0.25,
  seuilRentabiliteVentesMois: 5,
};

export const SEUIL_HIT_RATE = {
  ancienPrintful: 0.0375,
  gelatoSansPlus: 0.011,
  gelatoAvecPlus: 0.0093,
};

// Catalogue de référence (une œuvre type → ses variantes vendables) : la grille musée
// décidée (decision-encadrement §5.1), en poster nu + encadré chêne. Inclut le 40×50
// (4:5) : ratio art-print DOMINANT sur Etsy, qui matche ~1/4 du catalogue avec bordure
// minimale (cf. docs/audit-ratio-cadres.md). Aligné sur layout.CATALOGUE → chaque
// variante a un plan de mise en page (bordure intégrée, jamais de crop). A4 et toile
// 40×50 retirés (hors grille). « prix » dans aConfirmer = niveau à trancher (founder) ;
// « coutBase/portGelato » = à confirmer via l'API Gelato.
export const PRODUITS: Produit[] = [
  // Posters nus
  { id: "poster-30x40-nu", type: "poster", label: "Affiche 30×40", format: "30×40 cm", prix: 22.9, port: 3.9, coutBase: 7.0, portGelato: 3.5, ligne: "standard", aConfirmer: ["prix", "coutBase", "portGelato"] },
  { id: "poster-a3-nu", type: "poster", label: "Affiche A3", format: "29,7×42 cm", prix: 24.9, port: 3.9, coutBase: 7.5, portGelato: 3.5, ligne: "standard", aConfirmer: ["coutBase", "portGelato"] },
  { id: "poster-40x50-nu", type: "poster", label: "Affiche 40×50", format: "40×50 cm", prix: 29.9, port: 4.5, coutBase: 9.0, portGelato: 4.0, ligne: "standard", aConfirmer: ["prix", "coutBase", "portGelato"] },
  { id: "poster-a2-nu", type: "poster", label: "Affiche A2", format: "42×59,4 cm", prix: 32.9, port: 4.5, coutBase: 10.0, portGelato: 4.0, ligne: "standard", aConfirmer: ["coutBase", "portGelato"] },
  { id: "poster-50x70-nu", type: "poster", label: "Affiche 50×70", format: "50×70 cm", prix: 39.9, port: 4.9, coutBase: 12.0, portGelato: 4.5, ligne: "standard", aConfirmer: ["prix", "coutBase", "portGelato"] },
  { id: "poster-61x91-nu", type: "poster", label: "Affiche 61×91", format: "61×91 cm", prix: 54.9, port: 5.9, coutBase: 16.0, portGelato: 5.5, ligne: "standard", aConfirmer: ["prix", "coutBase", "portGelato"] },
  // Encadrés chêne — la pièce qui porte la rentabilité (marge absolue la plus haute)
  { id: "encadre-30x40-chene", type: "framed", label: "Encadré 30×40 chêne", format: "30×40 cm", prix: 42.9, port: 6.9, coutBase: 16.0, portGelato: 6.5, ligne: "standard", aConfirmer: ["prix", "coutBase", "portGelato"] },
  { id: "encadre-a3-chene", type: "framed", label: "Encadré A3 chêne", format: "29,7×42 cm", prix: 44.9, port: 6.9, coutBase: 18.0, portGelato: 6.5, ligne: "standard", aConfirmer: ["coutBase", "portGelato"] },
  { id: "encadre-40x50-chene", type: "framed", label: "Encadré 40×50 chêne", format: "40×50 cm", prix: 57.9, port: 7.9, coutBase: 24.0, portGelato: 7.5, ligne: "standard", aConfirmer: ["prix", "coutBase", "portGelato"] },
  { id: "encadre-a2-chene", type: "framed", label: "Encadré A2 chêne", format: "42×59,4 cm", prix: 67.9, port: 9.9, coutBase: 28.0, portGelato: 8.5, ligne: "standard", aConfirmer: ["coutBase", "portGelato"] },
  { id: "encadre-50x70-chene", type: "framed", label: "Encadré 50×70 chêne", format: "50×70 cm", prix: 74.9, port: 9.9, coutBase: 34.0, portGelato: 8.5, ligne: "standard", aConfirmer: ["prix", "coutBase", "portGelato"] },
  { id: "encadre-61x91-chene", type: "framed", label: "Encadré 61×91 chêne", format: "61×91 cm", prix: 99.9, port: 11.9, coutBase: 44.0, portGelato: 10.0, ligne: "standard", aConfirmer: ["prix", "coutBase", "portGelato"] },
];

export type Marge = {
  prix: number;
  encaissementBrut: number;
  fraisEtsy: number;
  coutFournisseur: number;
  provisionSav: number;
  margeNette: number;
  margePct: number;
};

/**
 * Marge nette d'une variante. baseCalculFrais = prix + port (les frais Etsy
 * portent aussi sur les frais de port encaissés).
 */
export function calculerMarge(p: Pick<Produit, "prix" | "port" | "coutBase" | "portGelato">, gelatoPlus = false): Marge {
  const encaissementBrut = p.prix + p.port;
  const fraisEtsy =
    encaissementBrut * (FRAIS_ETSY.transactionPct + FRAIS_ETSY.paiementPct + FRAIS_ETSY.reglementairePct) +
    FRAIS_ETSY.paiementFixe +
    FRAIS_ETSY.listingAmortiParVente;
  const coutBase = gelatoPlus ? p.coutBase * (1 - GELATO_PLUS.remiseBasePct) : p.coutBase;
  const coutFournisseur = coutBase + p.portGelato;
  const provisionSav = encaissementBrut * HYPOTHESES.provisionSavPct;
  const margeNette = encaissementBrut - fraisEtsy - coutFournisseur - provisionSav;
  return {
    prix: p.prix,
    encaissementBrut: round2(encaissementBrut),
    fraisEtsy: round2(fraisEtsy),
    coutFournisseur: round2(coutFournisseur),
    provisionSav: round2(provisionSav),
    margeNette: round2(margeNette),
    margePct: round2(margeNette / encaissementBrut),
  };
}

export function matriceVariantes(gelatoPlus = false): Array<Produit & { marge: Marge }> {
  return PRODUITS.map((p) => ({ ...p, marge: calculerMarge(p, gelatoPlus) }));
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}
