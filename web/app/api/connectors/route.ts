import { NextResponse } from "next/server";
import { CONNECTORS, describeStatus, getConnectorStatus } from "@/lib/connectors";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

// GET /api/connectors — liste tous les connecteurs avec leur statut config
// (clé présente / manquante) + dernière interaction observable (orders récentes
// pour les POD, etc.). Ne fait PAS de ping live (pour ça : /api/connectors/test/[id]).
export async function GET() {
  // Pour les POD : compter les orders récentes par provider (dernier signe de vie côté business)
  const recentByProvider = await db.order.groupBy({
    by: ["provider"],
    _count: { id: true },
    where: { createdAt: { gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) } },
  });
  const ordersCount = Object.fromEntries(recentByProvider.map((r) => [r.provider, r._count.id]));

  const rows = CONNECTORS.map((c) => ({
    id:           c.id,
    name:         c.name,
    description:  c.description,
    docUrl:       c.docUrl,
    category:     c.category,
    status:       getConnectorStatus(c),
    configHint:   describeStatus(c),
    requiredEnv:  c.requiredEnv,
    hasTest:      !!c.test,
    // Stats business pour les POD : nb d'orders sur 30j
    ordersLast30: c.category === "pod" ? ordersCount[c.id] ?? 0 : null,
  }));

  return NextResponse.json({ connectors: rows });
}
