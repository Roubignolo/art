"""Symétrie numérique entre le moteur de mise en page Python et son port TS.

`agents/render/layout.py` produit le bloc ``layout`` des manifestes (côté print) ;
`web/lib/layout.ts` recalcule la MÊME géométrie côté cockpit/listing. Si les deux
divergent sur la taille catalogue ou l'orientation, le cockpit afficherait un
produit différent de ce qui part à l'impression. Ce test exécute le VRAI port TS
(via Node, type-stripping) et compare chaque champ.

Contrat vérifié :
  - taille / fournisseur / orientation / strategie : IDENTIQUES (égalité stricte) ;
  - ratio / marges / bordure % : tolérance d'UN cran d'affichage — `toFixed` (TS)
    arrondit les demis exacts away-from-zero, `round()` (Python) vers le pair ;
    l'écart est cosmétique et n'influence jamais le choix de taille.

Le test est ignoré (skip) si Node est absent ou ne strippe pas les types TS
(< 22.6) — JAMAIS un faux échec faute de JS. En revanche, si Node SAIT stripper
les types mais que le port échoue (export renommé, exception, régression), le
test ÉCHOUE (il ne masque pas une vraie panne derrière un skip).
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from agents.render import layout  # noqa: E402

MODULE_TS = os.path.join(ROOT, "web", "lib", "layout.ts")

# Dimensions de test : ratios extrêmes, carré, off-by-one autour des seuils
# d'orientation, formats photo courants + deux paires connues pour exhiber la
# divergence d'arrondi d'affichage (5390×1120 → ratio 4.812/4.813 ;
# 2496×975 → marge_h_frac 0.062/0.063) — pour que la tolérance soit exercée.
DIMS = [
    (1000, 800), (800, 1000), (3000, 1000), (1000, 3000), (1000, 1000),
    (999, 1000), (1001, 1000), (1050, 1000), (950, 1000), (4096, 2731),
    (2731, 4096), (1500, 1499), (3000, 2380), (2000, 3000), (6000, 4000),
    (5390, 1120), (2496, 975),
]

# Champs identiques au cran près (snake_case py -> camelCase ts).
EXACT = {
    "taille": "taille", "fournisseur": "fournisseur",
    "orientation": "orientation", "strategie": "strategie",
}
# Champs d'affichage arrondis : tolérance = un cran (10**-décimales).
TOL = {
    "ratio_oeuvre": ("ratioOeuvre", 1e-3), "ratio_taille": ("ratioTaille", 1e-3),
    "marge_h_frac": ("margeHFrac", 1e-3), "marge_v_frac": ("margeVFrac", 1e-3),
    "bordure_pct": ("bordurePct", 1e-1),
}

# Driver Node : lit les dimensions sur argv[2] (chemin JSON), importe le port TS
# et émet les plans calculés. Node >= 22.6 strippe les types TS nativement.
_DRIVER = r"""
import { planifier, plansVariants } from %(mod)s;
import { readFileSync } from 'node:fs';
const dims = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const out = dims.map(([aw, ah]) => ({
  aw, ah,
  gelato: planifier(aw, ah, 'gelato'),
  prodigi: planifier(aw, ah, 'prodigi'),
  variants_gelato: plansVariants(aw, ah, 'gelato'),
  variants_prodigi: plansVariants(aw, ah, 'prodigi'),
}));
process.stdout.write(JSON.stringify(out));
"""

# Sonde minimale : Node strippe-t-il les types d'un .ts ? Distingue une limite
# d'environnement (→ skip légitime) d'un vrai échec du port (→ failure).
_PROBE_TS = "export const v: number = 41 as number;\n"
_PROBE_DRV = "import { v } from %(mod)s;\nprocess.stdout.write(String(v + 1));\n"


def _node():
    return shutil.which("node")


def _node_supports_ts(node):
    """True si Node exécute un import de .ts trivial (type-stripping disponible)."""
    with tempfile.TemporaryDirectory() as d:
        mod_p = os.path.join(d, "probe.ts")
        drv_p = os.path.join(d, "probe_drv.mjs")
        with open(mod_p, "w") as f:
            f.write(_PROBE_TS)
        with open(drv_p, "w") as f:
            f.write(_PROBE_DRV % {"mod": json.dumps(mod_p)})
        try:
            r = subprocess.run([node, "--no-warnings", drv_p],
                               capture_output=True, text=True, timeout=30)
        except Exception:
            return False
        return r.returncode == 0 and r.stdout.strip() == "42"


def _run_ts(node, dims):
    """Exécute le port TS sur ``dims`` ; (returncode, stdout, stderr)."""
    mod = json.dumps(MODULE_TS)
    with tempfile.TemporaryDirectory() as d:
        dims_p = os.path.join(d, "dims.json")
        drv_p = os.path.join(d, "drv.mjs")
        with open(dims_p, "w") as f:
            json.dump(dims, f)
        with open(drv_p, "w") as f:
            f.write(_DRIVER % {"mod": mod})
        r = subprocess.run([node, "--no-warnings", drv_p, dims_p],
                           capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout, r.stderr


class TestLayoutTsSymmetry(unittest.TestCase):
    def test_port_ts_identique_au_python(self):
        node = _node()
        if not node:
            self.skipTest("Node introuvable — symétrie TS non vérifiée")
        if not _node_supports_ts(node):
            self.skipTest("Node ne strippe pas les types TS (< 22.6) — symétrie non vérifiée")

        # Ici Node SAIT stripper les types : tout échec du driver est une vraie
        # régression du port (export renommé, exception…), pas une limite d'env.
        rc, out, err = _run_ts(node, DIMS)
        self.assertEqual(rc, 0, msg=f"le port TS a échoué (régression ?) :\n{err[:800]}")
        ts = json.loads(out)

        self.assertEqual(len(ts), len(DIMS))
        for (aw, ah), row in zip(DIMS, ts):
            self.assertEqual((row["aw"], row["ah"]), (aw, ah))
            for prov in ("gelato", "prodigi"):
                self._cmp(layout.planifier(aw, ah, prov).to_dict(), row[prov],
                          f"{aw}x{ah}.{prov}")
            for prov, key in (("gelato", "variants_gelato"), ("prodigi", "variants_prodigi")):
                py_v = [p.to_dict() for p in layout.plans_variants(aw, ah, prov)]
                self.assertEqual(len(py_v), len(row[key]), f"{aw}x{ah}.{key} longueur")
                for i, (p, t) in enumerate(zip(py_v, row[key])):
                    self._cmp(p, t, f"{aw}x{ah}.{key}[{i}]")

    def _cmp(self, py, ts, ctx):
        for pk, tk in EXACT.items():
            self.assertEqual(py[pk], ts[tk], msg=f"{ctx}.{pk} (doit être identique)")
        for pk, (tk, tol) in TOL.items():
            self.assertLessEqual(abs(py[pk] - ts[tk]), tol + 1e-9,
                                 msg=f"{ctx}.{pk}: py={py[pk]} ts={ts[tk]} (> 1 cran)")


if __name__ == "__main__":
    unittest.main()
