// Adaptateurs entre le registre brut produit par le sous-agent Sourcing
// (sortie de agents/sourcing_agent.py — clés snake_case) et le modèle Prisma.

import type { Prisma } from "@prisma/client";

export type SourcingRecord = {
  objectID: number | string;
  title?: string | null;
  artist?: string | null;
  artist_bio?: string | null;
  artist_death?: string | number | null;
  object_date?: string | null;
  object_end_year?: string | number | null;
  department?: string | null;
  classification?: string | null;
  medium?: string | null;
  dimensions?: string | null;
  credit_line?: string | null;
  source?: string | null;
  object_url?: string | null;
  image_url?: string | null;
  resolution_px?: number | null;
  width?: number | null;
  height?: number | null;
  resolution_ok?: boolean | null;
  gate_g1_us_g3?: boolean | null;
  gate_g1_ue?: boolean | null;
  gate_g2_marque?: boolean | null;
  local_file?: string | null;
  decision?: string | null;
  // Preuve de domaine public (cf. agents/sources/base.py)
  artist_birth?: string | number | null;
  object_begin_year?: string | number | null;
  accession_number?: string | null;
  rights_statement?: string | null;
  wikidata_url?: string | null;
  wikidata_copyright_status?: string | null;
  dp_evidence?: string | null;
};

function asInt(v: unknown): number | null {
  if (v === null || v === undefined || v === "") return null;
  const m = String(v).match(/\d{1,4}/);
  return m ? parseInt(m[0], 10) : null;
}

/** Convertit une ligne sourcing → données Prisma pour upsert. */
export function toWorkUpsert(rec: SourcingRecord) {
  const id = typeof rec.objectID === "number" ? rec.objectID : parseInt(String(rec.objectID), 10);
  if (Number.isNaN(id)) throw new Error(`objectID invalide: ${rec.objectID}`);

  const base = {
    title:          rec.title ?? "Sans titre",
    artist:         rec.artist ?? null,
    artistBio:      rec.artist_bio ?? null,
    artistDeath:    asInt(rec.artist_death),
    objectDate:     rec.object_date ?? null,
    department:     rec.department ?? null,
    classification: rec.classification ?? null,
    medium:         rec.medium ?? null,
    dimensions:     rec.dimensions ?? null,
    creditLine:     rec.credit_line ?? null,
    source:         rec.source ?? "The Metropolitan Museum of Art (Open Access, CC0)",
    objectUrl:      rec.object_url ?? null,
    imageUrl:       rec.image_url ?? null,
    localFile:      rec.local_file ?? null,
    resolutionPx:   rec.resolution_px ?? 0,
    width:          rec.width ?? null,
    height:         rec.height ?? null,
    gateUsSource:   rec.gate_g1_us_g3 ?? false,
    gateUe:         rec.gate_g1_ue ?? null,
    gateNoTm:       rec.gate_g2_marque ?? true,
    resolutionOk:   rec.resolution_ok ?? null,
    // Preuve de domaine public
    artistBirth:       asInt(rec.artist_birth),
    objectBeginYear:   asInt(rec.object_begin_year),
    accessionNumber:   rec.accession_number ?? null,
    rightsStatement:   rec.rights_statement ?? null,
    wikidataUrl:       rec.wikidata_url ?? null,
    dpEvidence:        rec.dp_evidence ?? null,
  } satisfies Partial<Prisma.WorkUncheckedCreateInput>;

  return {
    where:  { id },
    update: base,
    create: { id, ...base, status: "gate" as const },
  };
}
