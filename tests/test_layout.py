"""Tests de la mise en page produit (agents/render/layout.py).

Garantie centrale : une œuvre n'est JAMAIS rognée — l'ouverture contient toujours
l'œuvre entière, et son ratio atteint la taille catalogue par une bordure/mat.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.render import layout  # noqa: E402


class TestOuverture(unittest.TestCase):
    def test_jamais_de_crop(self):
        for aw, ah in [(1000, 800), (800, 1000), (3000, 1000), (1000, 3000), (1000, 1000)]:
            for r in (1.0, 1.25, 1.333, 1.414, 1.5):
                ow, oh, mwx, mwy = layout.ouverture(aw, ah, r)
                self.assertGreaterEqual(ow, aw)   # l'œuvre tient en largeur
                self.assertGreaterEqual(oh, ah)   # et en hauteur
                self.assertGreaterEqual(mwx, 0)
                self.assertGreaterEqual(mwy, 0)

    def test_ratio_ouverture_atteint_la_cible(self):
        ow, oh, _, _ = layout.ouverture(1000, 800, 1.5)
        self.assertAlmostEqual(ow / oh, 1.5, delta=0.01)

    def test_marge_minimale_respectee(self):
        aw, ah = 1000, 800
        _, _, mwx, mwy = layout.ouverture(aw, ah, 1.25, mat_min_frac=0.08)
        m = int(min(aw, ah) * 0.08)
        self.assertGreaterEqual(mwx, m)
        self.assertGreaterEqual(mwy, m)


class TestPlan(unittest.TestCase):
    def test_paysage_portrait_carré(self):
        self.assertEqual(layout.planifier(1200, 800).orientation, "paysage")
        self.assertEqual(layout.planifier(800, 1200).orientation, "portrait")
        self.assertEqual(layout.planifier(1000, 1000).orientation, "carré")

    def test_marges_positives_et_bordure_sensée(self):
        p = layout.planifier(3000, 2380, "gelato")  # ratio ~1.26
        self.assertGreaterEqual(p.marge_h_frac, 0)
        self.assertGreaterEqual(p.marge_v_frac, 0)
        self.assertTrue(0 < p.bordure_pct < 70)

    def test_choix_taille_par_ratio(self):
        # œuvre ~1.5 → taille de ratio ~1.5 ; carré → taille carrée
        self.assertAlmostEqual(layout.planifier(3000, 2000).ratio_taille, 1.5, delta=0.05)
        self.assertEqual(layout.planifier(1000, 1000).ratio_taille, 1.0)

    def test_prodigi_recommande_fit_sans_crop(self):
        p = layout.planifier(3000, 2000, "prodigi")
        self.assertIn("fit", p.sizing_prodigi.lower())
        self.assertEqual(p.strategie, "passe-partout")

    def test_gelato_bordure_fichier(self):
        p = layout.planifier(3000, 2000, "gelato")
        self.assertEqual(p.strategie, "bordure-fichier")

    def test_variants_un_par_taille_fournisseur(self):
        plans = layout.plans_variants(3000, 2000, "gelato")
        n_gelato = sum(1 for t in layout.CATALOGUE if "gelato" in t.fournisseurs)
        self.assertEqual(len(plans), n_gelato)

    def test_offre_gelato_inclut_le_4_5(self):
        # Œuvre rectangulaire (ratio 1.5) → 6 tailles, dont le 40×50 (4:5), sans carrés.
        offre = layout.variants_offre(3000, 2000, "gelato")
        labels = {p.taille for p in offre}
        self.assertEqual(labels, {"30×40", "40×50", "A3 30×42", "50×70", "A2 42×59", "61×91"})
        self.assertNotIn("30×30", labels)  # pas de carré pour une œuvre rectangulaire
        plein = {p.taille for p in layout.plans_variants(3000, 2000, "gelato")}
        self.assertTrue(labels <= plein)  # offre ⊆ catalogue productible

    def test_offre_carre_seulement_si_oeuvre_carree(self):
        # Œuvre ~carrée (ratio 1.08) → les carrés entrent dans l'offre.
        offre = layout.variants_offre(1080, 1000, "gelato")
        labels = {p.taille for p in offre}
        self.assertIn("30×30", labels)
        self.assertIn("50×50", labels)

    def test_offre_prodigi_signature(self):
        offre = layout.variants_offre(3000, 2000, "prodigi")
        self.assertEqual({p.taille for p in offre}, {"30×40", "40×50", "50×70", "61×91"})

    def test_encadrable_ratio_standard_vs_extreme(self):
        # ratio standard (3:2) → bien encadrable ; kakemono ultra-allongé → non.
        self.assertTrue(layout.encadrable(3000, 2000))          # ratio 1.5
        self.assertTrue(layout.encadrable(3000, 2380))          # ratio ~1.26 (4:5)
        self.assertFalse(layout.encadrable(3000, 900))          # ratio 3.33 (kakemono)
        self.assertLess(layout.bordure_min_offre(3000, 2000), 30)
        self.assertGreater(layout.bordure_min_offre(3000, 900), 50)


if __name__ == "__main__":
    unittest.main()
