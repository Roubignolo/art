import { PrismaClient } from "@prisma/client";

// Évite de créer plusieurs clients en dev (HMR Next.js).
const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient };

export const db = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = db;
