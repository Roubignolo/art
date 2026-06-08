/**
 * Constructeur de listing Etsy — assemble un brouillon complet et conforme
 * à partir d'une œuvre (marketing multilingue + provenance + matrice de prix).
 *
 * Aligné sur docs/etsy-listing-system.md (limites 2026 : titre 140c dur /
 * ~70c soft, 13 tags × 20c, attribution « sourced by ») et docs/economie-gelato.md.
 *
 * Le brouillon est consommé par /api/etsy/publish (preview dry-run ou POST réel)
 * et par l'aperçu listing du cockpit.
 */

import { PRODUITS, calculerMarge, type Produit } from "./pricing";

const TITRE_MAX = 140;
const TAGS_MAX = 13;
const TAG_LONGUEUR_MAX = 20;

type MarketingLocale = {
  title?: string;
  listingTitle?: string;
  description?: string;
  hook?: string;
  tags?: string[];
  titleSource?: string;
};

export type WorkLite = {
  id: number;
  title: string;
  artist?: string | null;
  artistBio?: string | null;
  objectDate?: string | null;
  medium?: string | null;
  source?: string | null;
  objectUrl?: string | null;
  creditLine?: string | null;
  hook?: string | null;
  marketing?: unknown;
  line?: string | null;
};

export type EtsyVariant = {
  sku: string;
  label: string;
  format: string;
  prix: number;
  margeNette: number;
  ligne: "standard" | "signature";
  provider: "gelato" | "prodigi";
};

export type EtsyListingDraft = {
  locale: string;
  title: string;
  titleLength: number;
  titleWarning?: string;
  description: string;
  tags: string[];
  materials: string[];
  whoMade: "i_did";
  whenMade: "made_to_order";
  isSupply: false;
  shouldAutoRenew: true;
  taxonomyHint: string; // catégorie Etsy "Art & Collectibles > Prints"
  attributs: Record<string, string>;
  variants: EtsyVariant[];
  prixAffiche: number; // prix de départ ("à partir de")
  galerieHint: string[]; // ordre conseillé des 10 visuels
  conformite: string[]; // garde-fous affichés (sourced by, etc.)
};

function tronquer(s: string, max: number): string {
  if (s.length <= max) return s;
  const coupe = s.slice(0, max);
  return coupe.slice(0, coupe.lastIndexOf(" ") > max * 0.6 ? coupe.lastIndexOf(" ") : max).trim();
}

function nettoyerTags(tags: string[]): string[] {
  const vus = new Set<string>();
  const out: string[] = [];
  for (const t of tags) {
    const tag = t.trim().toLowerCase().slice(0, TAG_LONGUEUR_MAX).trim();
    if (tag && !vus.has(tag)) {
      vus.add(tag);
      out.push(tag);
    }
    if (out.length >= TAGS_MAX) break;
  }
  return out;
}

function getMarketing(work: WorkLite, locale: string): MarketingLocale {
  const m = (work.marketing as Record<string, MarketingLocale> | null) ?? {};
  return m[locale] ?? m["en"] ?? m["fr"] ?? {};
}

/** Sections de description « hyper pro » ajoutées au texte marketing. */
function assemblerDescription(work: WorkLite, ml: MarketingLocale, locale: string): string {
  const fr = locale === "fr";
  const lignes: string[] = [];
  const corps = ml.description?.trim() || ml.hook?.trim() || work.hook?.trim() || "";
  if (corps) lignes.push(corps, "");

  // Provenance
  const provTitre = fr ? "✦ PROVENANCE" : "✦ PROVENANCE";
  lignes.push(provTitre);
  const prov: string[] = [];
  if (work.artist) prov.push(`${work.artist}${work.artistBio ? ` (${work.artistBio})` : ""}`);
  if (work.objectDate) prov.push(work.objectDate);
  if (work.medium) prov.push(work.medium);
  if (prov.length) lignes.push(prov.join(" · "));
  if (work.source) lignes.push(fr ? `Source : ${work.source}` : `Source: ${work.source}`);
  if (work.creditLine) lignes.push(work.creditLine);
  lignes.push("");

  // Specs
  lignes.push(fr ? "✦ IMPRESSION & FINITION" : "✦ PRINT & FINISH");
  lignes.push(
    fr
      ? "Fichier haute résolution préparé avec soin : gestion colorimétrique (sRGB fidèle à l'original du musée), pas de retouche des couleurs de l'artiste. Impression à la demande sur papiers et supports de qualité galerie, production locale FR/UE (3-5 j ouvrés)."
      : "High-resolution file carefully prepared: colour-managed (sRGB faithful to the museum original), the artist's colours left untouched. Made to order on gallery-grade papers and supports, local EU production (3-5 business days).",
  );
  lignes.push("");

  // Attribution obligatoire
  lignes.push(
    fr
      ? "Œuvre du domaine public, sélectionnée et préparée pour l'impression par Vellum & Cie (« sourced by », jamais « made by »). Nous vendons la curation, la provenance documentée et un tirage fidèle — l'image, elle, appartient à tous."
      : 'Public-domain work, selected and prepared for print by Vellum & Cie ("sourced by," never "made by"). We sell curation, documented provenance and a faithful print — the image itself belongs to everyone.',
  );
  return lignes.join("\n");
}

export function construireListing(work: WorkLite, locale = "fr"): EtsyListingDraft {
  const ml = getMarketing(work, locale);

  const titreBrut = (ml.listingTitle || ml.title || work.title || "").trim();
  const title = tronquer(titreBrut, TITRE_MAX);
  const titleWarning =
    title.length > 70
      ? "Titre > 70 caractères : au-delà, l'algorithme Etsy pénalise le bourrage de mots-clés (cf. etsy-listing-system.md)."
      : title.length < 20
        ? "Titre court : enrichir avec sujet + style + pièce + format pour le SEO longue traîne."
        : undefined;

  const tags = nettoyerTags(ml.tags ?? []);

  const ligneSignature = work.line === "signature";
  const variants: EtsyVariant[] = PRODUITS.filter((p) =>
    ligneSignature ? true : p.ligne === "standard",
  ).map((p: Produit) => ({
    sku: `${work.id}-${p.id}`,
    label: p.label,
    format: p.format,
    prix: p.prix,
    margeNette: calculerMarge(p).margeNette,
    ligne: p.ligne,
    provider: ligneSignature && p.type !== "giftable" ? "prodigi" : "gelato",
  }));

  const prixAffiche = Math.min(...variants.map((v) => v.prix));

  const materials =
    locale === "fr"
      ? ["domaine public", "papier qualité galerie", "impression giclée", "couleur fidèle"]
      : ["public domain", "gallery-grade paper", "giclée print", "faithful colour"];

  return {
    locale,
    title,
    titleLength: title.length,
    titleWarning,
    description: assemblerDescription(work, ml, locale),
    tags,
    materials,
    whoMade: "i_did",
    whenMade: "made_to_order",
    isSupply: false,
    shouldAutoRenew: true,
    taxonomyHint: "Art & Collectibles › Prints › Giclée",
    attributs: {
      orientation: "paysage/portrait (selon l'œuvre)",
      style: "vintage, classique, muséal",
      piece: locale === "fr" ? "salon, chambre, bureau, entrée" : "living room, bedroom, office",
    },
    variants,
    prixAffiche,
    galerieHint: [
      "01 — tirage nu sur mur neutre",
      "02 — encadré chêne (vue principale)",
      "03 — détail texture (haute définition)",
      "04 — options de cadres",
      "05 — comparatif des tailles",
      "06 — scène lifestyle galerie",
      "07 — scène lifestyle scandinave",
      "08 — scène lifestyle atelier",
      "09 — carte de provenance (recto)",
      "10 — carte de provenance (verso)",
    ],
    conformite: [
      'Attribution « sourced by » présente dans la description.',
      tags.length < TAGS_MAX ? `Seulement ${tags.length}/13 tags — en ajouter pour le SEO.` : "13/13 tags utilisés.",
      "who_made=i_did + production partner Gelato/Prodigi à déclarer dans Shop Manager.",
      "Vérifier le gate DP (G1 US+UE) validé humain avant publication.",
    ],
  };
}
