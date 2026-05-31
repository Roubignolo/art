/**
 * Modèle de prix Gelato — source unique partagée cockpit + /api/etsy/publish.
 *
 * Aligné sur docs/economie-gelato.md (bloc JSON §4). Les coûts base/port Gelato
 * sont des MÉDIANS de fourchettes documentées, à confirmer via l'API Gelato
 * (champ `aConfirmer`). Les frais Etsy sont les frais France réels 2026.
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

// Catalogue de référence (une œuvre type → ses variantes vendables).
export const PRODUITS: Produit[] = [
  { id: "poster-a4-nu", type: "poster", label: "Affiche A4", format: "21×29,7 cm", prix: 16.9, port: 3.5, coutBase: 4.5, portGelato: 3.0, ligne: "standard", aConfirmer: ["coutBase", "portGelato"] },
  { id: "poster-a3-nu", type: "poster", label: "Affiche A3", format: "29,7×42 cm", prix: 24.9, port: 3.9, coutBase: 7.5, portGelato: 3.5, ligne: "standard", aConfirmer: ["coutBase", "portGelato"] },
  { id: "poster-a2-nu", type: "poster", label: "Affiche A2", format: "42×59,4 cm", prix: 32.9, port: 4.5, coutBase: 10.0, portGelato: 4.0, ligne: "standard", aConfirmer: ["coutBase", "portGelato"] },
  { id: "encadre-a3-chene", type: "framed", label: "Encadré A3 chêne", format: "29,7×42 cm", prix: 44.9, port: 6.9, coutBase: 18.0, portGelato: 6.5, ligne: "standard", aConfirmer: ["coutBase", "portGelato"] },
  { id: "encadre-a2-chene", type: "framed", label: "Encadré A2 chêne", format: "42×59,4 cm", prix: 67.9, port: 9.9, coutBase: 28.0, portGelato: 8.5, ligne: "standard", aConfirmer: ["coutBase", "portGelato"] },
  { id: "toile-40x50", type: "canvas", label: "Toile 40×50", format: "40×50 cm", prix: 54.9, port: 7.9, coutBase: 22.0, portGelato: 7.5, ligne: "standard", aConfirmer: ["coutBase", "portGelato"] },
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
