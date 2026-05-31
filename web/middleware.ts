import { NextResponse, type NextRequest } from "next/server";

// HTTP Basic Auth — protection minimale du cockpit pour Phase 0.
// Configuration via env : COCKPIT_PASSWORD (requis), COCKPIT_USER (défaut : "art").
// Si COCKPIT_PASSWORD est absent, l'auth est désactivée (utile en dev local).
//
// Récupération d'accès : il n'y a PAS de base d'utilisateurs ni d'email, donc pas
// de lien de réinitialisation (et un reset en libre-service serait une faille).
// Le mot de passe EST la variable COCKPIT_PASSWORD dans Vercel → Settings → Env Vars.
// La page 401 ci-dessous explique cette procédure (« mot de passe oublié »).

export const config = {
  // On laisse passer les assets Next.js ET les images publiques destinées à Etsy
  // (/brand, /renders) — sinon 401 en boucle / galerie inaccessible.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|brand|renders).*)"],
};

function page401(expectedUser: string): string {
  return `<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vellum & Cie — Accès cockpit</title>
<style>
  :root{--paper:#F4EFE6;--paper2:#FBF7EE;--ink:#2A2622;--ink2:#6B645B;--brass:#A9803F;--line:#E3DBC9}
  *{box-sizing:border-box}
  body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:var(--paper);color:var(--ink);font:15px/1.6 Georgia,'Newsreader',serif;padding:24px}
  .card{max-width:560px;width:100%;background:var(--paper2);border:1px solid var(--line);
    border-radius:6px;padding:34px 38px;box-shadow:0 1px 2px rgba(33,28,21,.06),0 8px 30px rgba(33,28,21,.08)}
  .seal{width:62px;height:62px;border:2px solid var(--brass);border-radius:50%;display:flex;
    align-items:center;justify-content:center;margin-bottom:18px}
  .seal span{font:600 24px Georgia,serif;letter-spacing:-.02em}
  h1{font:600 24px Georgia,serif;letter-spacing:-.02em;margin:0 0 2px}
  .eyebrow{font:600 10px ui-monospace,monospace;letter-spacing:.16em;color:var(--ink2);text-transform:uppercase}
  p{margin:10px 0;color:var(--ink)}
  .muted{color:var(--ink2);font-size:13px}
  ol{margin:14px 0;padding-left:20px}
  li{margin:7px 0}
  code{background:var(--paper);border:1px solid var(--line);border-radius:3px;padding:1px 6px;
    font:13px ui-monospace,monospace;color:var(--ink)}
  .rule{height:1px;background:var(--line);margin:20px 0}
  .hint{background:var(--paper);border-left:3px solid var(--brass);padding:12px 14px;border-radius:0 3px 3px 0;font-size:13.5px}
  a{color:var(--brass)}
</style></head><body>
  <div class="card">
    <div class="seal"><span>V&amp;C</span></div>
    <div class="eyebrow">Vellum &amp; Cie · cockpit</div>
    <h1>Accès restreint</h1>
    <p class="muted">Identifiants demandés par la fenêtre du navigateur. Identifiant&nbsp;: <code>${expectedUser}</code>.</p>
    <div class="rule"></div>
    <p><strong>Mot de passe oublié&nbsp;?</strong></p>
    <p class="muted">Le cockpit n'a pas de compte ni d'email : le mot de passe <em>est</em> une variable d'environnement
    que tu contrôles dans Vercel. Pour le retrouver ou le réinitialiser&nbsp;:</p>
    <ol>
      <li>Vercel → projet <code>art-cockpit</code> → <strong>Settings → Environment Variables</strong>.</li>
      <li>Ouvre / modifie <code>COCKPIT_PASSWORD</code> (identifiant&nbsp;: <code>${expectedUser}</code>, défini par <code>COCKPIT_USER</code>).</li>
      <li>Si tu le changes&nbsp;: <strong>Deployments → ⋯ → Redeploy</strong> pour appliquer.</li>
    </ol>
    <div class="hint">Astuce&nbsp;: génère un mot de passe fort avec <code>openssl rand -base64 24</code>.
    Recharge ensuite cette page&nbsp;: la fenêtre d'authentification réapparaîtra.</div>
  </div>
</body></html>`;
}

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

  // 401 + challenge Basic. Le corps HTML (page « mot de passe oublié ») s'affiche
  // si l'utilisateur annule la fenêtre du navigateur.
  return new NextResponse(page401(expectedUser), {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="Vellum & Cie — Cockpit"',
      "Content-Type": "text/html; charset=utf-8",
    },
  });
}
