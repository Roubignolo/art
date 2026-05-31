import { NextResponse } from "next/server";
import crypto from "crypto";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

// Helper de configuration OAuth2 PKCE pour Etsy Open API v3 (P3.3).
//
// GET /api/etsy/oauth?action=authorize
//   → renvoie { authorizeUrl, codeVerifier, state }. Ouvre authorizeUrl, autorise,
//     récupère le ?code= du redirect, puis appelle le callback ci-dessous.
//
// GET /api/etsy/oauth?code=...&state=...&codeVerifier=...
//   → échange le code contre un access/refresh token (à placer en
//     ETSY_OAUTH_TOKEN / ETSY_REFRESH_TOKEN dans Vercel).
//
// Scaffold volontairement stateless (pas de store de session) : c'est un outil
// de setup ponctuel, pas un flux end-user. Nécessite ETSY_API_KEY + ETSY_REDIRECT_URI.

const SCOPES = ["listings_r", "listings_w", "transactions_r", "shops_r"];

function base64url(buf: Buffer): string {
  return buf.toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const apiKey = process.env.ETSY_API_KEY;
  const redirect = process.env.ETSY_REDIRECT_URI;

  if (!apiKey || !redirect) {
    return NextResponse.json(
      { error: "Configurer ETSY_API_KEY et ETSY_REDIRECT_URI d'abord." },
      { status: 503 },
    );
  }

  // Étape 1 — générer l'URL d'autorisation + PKCE
  if (url.searchParams.get("action") === "authorize") {
    const codeVerifier = base64url(crypto.randomBytes(32));
    const challenge = base64url(crypto.createHash("sha256").update(codeVerifier).digest());
    const state = base64url(crypto.randomBytes(16));
    const authorizeUrl =
      "https://www.etsy.com/oauth/connect?" +
      new URLSearchParams({
        response_type: "code",
        client_id: apiKey,
        redirect_uri: redirect,
        scope: SCOPES.join(" "),
        state,
        code_challenge: challenge,
        code_challenge_method: "S256",
      }).toString();
    return NextResponse.json({
      authorizeUrl,
      codeVerifier,
      state,
      note: "Conserve codeVerifier ; rappelle ce endpoint avec ?code=...&codeVerifier=... après autorisation.",
    });
  }

  // Étape 2 — échange du code contre les tokens
  const code = url.searchParams.get("code");
  const codeVerifier = url.searchParams.get("codeVerifier");
  if (code && codeVerifier) {
    const r = await fetch("https://api.etsy.com/v3/public/oauth/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "authorization_code",
        client_id: apiKey,
        redirect_uri: redirect,
        code,
        code_verifier: codeVerifier,
      }).toString(),
    });
    const data = (await r.json()) as Record<string, unknown>;
    if (!r.ok) return NextResponse.json({ error: `Etsy HTTP ${r.status}`, detail: data }, { status: 502 });
    return NextResponse.json({
      ok: true,
      note: "Place access_token → ETSY_OAUTH_TOKEN et refresh_token → ETSY_REFRESH_TOKEN dans Vercel.",
      tokens: data,
    });
  }

  return NextResponse.json(
    { error: "Usage : ?action=authorize puis ?code=...&codeVerifier=..." },
    { status: 400 },
  );
}
