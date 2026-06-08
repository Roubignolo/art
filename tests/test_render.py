"""Tests du moteur de rendu (agents/render/)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image  # noqa: E402

from agents.render.frames import PROFILS, encadrer, ombre_portee  # noqa: E402
from agents.render.mockup import comparatif_tailles, poster_nu  # noqa: E402
from agents.render.perspective import coeffs_perspective, coeffs_vers_quad  # noqa: E402
from agents.render.restoration import box_bords, restaurer, rogner_bords  # noqa: E402


def _image_test(w=120, h=90):
    """Petit dégradé non uniforme (évite les cas dégénérés)."""
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = (x % 256, y % 256, (x + y) % 256)
    return img


class TestPerspective(unittest.TestCase):
    def test_identite(self):
        coins = [(0, 0), (100, 0), (100, 80), (0, 80)]
        c = coeffs_perspective(coins, coins)
        # cibles == sources → transformation identité ≈ [1,0,0,0,1,0,0,0]
        attendu = [1, 0, 0, 0, 1, 0, 0, 0]
        for got, exp in zip(c, attendu):
            self.assertAlmostEqual(got, exp, places=5)

    def test_quad_renvoie_8_coeffs(self):
        c = coeffs_vers_quad([(10, 10), (90, 15), (88, 70), (12, 72)], (100, 80))
        self.assertEqual(len(c), 8)

    def test_points_degeneres_levent_erreur(self):
        with self.assertRaises(ValueError):
            coeffs_perspective([(0, 0)] * 4, [(0, 0)] * 4)


class TestRognage(unittest.TestCase):
    def test_supprime_liseré_uniforme(self):
        # fond noir pur 200×200 avec un carré blanc 100×100 au centre
        img = Image.new("RGB", (200, 200), (1, 1, 1))
        img.paste(Image.new("RGB", (100, 100), (255, 255, 255)), (50, 50))
        out = rogner_bords(img)
        self.assertLess(out.width, 200)
        self.assertLess(out.height, 200)
        # ne sur-rogne pas le contenu (garde au moins le carré central)
        self.assertGreaterEqual(out.width, 100)

    def test_image_sans_bord_inchangee(self):
        img = _image_test(150, 150)
        out = rogner_bords(img)
        # un dégradé n'a pas de liseré uniforme → taille conservée
        self.assertEqual(out.size, (150, 150))


class TestCadres(unittest.TestCase):
    def test_encadre_agrandit_et_rgba(self):
        art = _image_test(120, 90)
        for profil in PROFILS:
            piece = encadrer(art, profil)
            self.assertEqual(piece.mode, "RGBA")
            self.assertGreater(piece.width, 120)
            self.assertGreater(piece.height, 90)

    def test_ombre_portee_ajoute_marge(self):
        piece = encadrer(_image_test(100, 100), "chene")
        avec = ombre_portee(piece, marge=40)
        self.assertGreater(avec.width, piece.width)
        self.assertEqual(avec.mode, "RGBA")


class TestRestauration(unittest.TestCase):
    def test_upscale_local_atteint_la_cible(self):
        img = _image_test(60, 40)
        out, rapport = restaurer(img, long_edge_cible=180, debruitage=False)
        self.assertEqual(out.mode, "RGB")
        self.assertGreaterEqual(max(out.size), 180)
        self.assertEqual(rapport.upscale_methode, "lanczos")

    def test_pas_de_downscale(self):
        img = _image_test(400, 300)
        out, rapport = restaurer(img, long_edge_cible=200)
        # déjà au-dessus de la cible → pas d'upscale
        self.assertEqual(rapport.upscale_methode, "aucun")

    def test_image_degeneree_degrade_proprement(self):
        # un côté de 1-2 px ne doit JAMAIS crasher (box_bords → None, pas d'IndexError)
        for size in [(1, 1), (1, 5), (5, 1), (2, 2)]:
            self.assertIsNone(box_bords(Image.new("RGB", size)))
        out, _ = restaurer(Image.new("RGB", (1, 5)), long_edge_cible=20)
        self.assertEqual(out.mode, "RGB")


class TestMockups(unittest.TestCase):
    def test_poster_nu_taille(self):
        out = poster_nu(_image_test(800, 600), sortie=(600, 600))
        self.assertEqual(out.size, (600, 600))

    def test_comparatif_tailles(self):
        out = comparatif_tailles(
            _image_test(800, 600),
            [("A4", 21, 29.7), ("A3", 29.7, 42), ("A2", 42, 59.4)],
            sortie=(900, 700),
        )
        self.assertEqual(out.size, (900, 700))


if __name__ == "__main__":
    unittest.main()
