import { NextResponse, type NextRequest } from "next/server";

// HTTP Basic Auth — protection minimale du cockpit pour Phase 0.
// Configuration via env : COCKPIT_PASSWORD (requis), COCKPIT_USER (défaut : "art").
// Si COCKPIT_PASSWORD est absent, l'auth est désactivée (utile en dev local).

export const config = {
  // On laisse passer UNIQUEMENT les assets Next.js (sinon 401 en boucle).
  // Tout le reste — cockpit, API, ET /brand + /renders — est protégé par Basic Auth.
  // (Pour rouvrir un asset au public un jour : ré-exclure son préfixe ici.)
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};

export function middleware(req: NextRequest) {
  const password = process.env.COCKPIT_PASSWORD;
  if (!password) return NextResponse.next();

  const expectedUser = process.env.COCKPIT_USER || "art";
  const auth = req.headers.get("authorization");

  if (auth?.startsWith("Basic ")) {
    try {
      const decoded = atob(auth.slice(6));
      const sep = decoded.indexOf(":");
      const user = decoded.slice(0, sep);
      const pass = decoded.slice(sep + 1);
      if (user === expectedUser && pass === password) {
        return NextResponse.next();
      }
    } catch {
      // En-tête mal formé → on tombe sur le challenge.
    }
  }

  return new NextResponse("Authentification requise", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Provenance Cockpit"' },
  });
}
