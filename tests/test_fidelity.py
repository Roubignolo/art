"""Tests de l'audit de fidélité colorimétrique (agents/render/fidelity.py).

Couvre : exactitude de ΔE2000 (vecteurs de référence Sharma 2005), conversion
Lab, et la capacité du garde-fou à (a) valider une copie fidèle, (b) détecter la
neutralisation gray-world qui avait délavé la nappe de Cézanne.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image  # noqa: E402

from agents.render.fidelity import (  # noqa: E402
    auditer_fidelite,
    delta_e_2000,
    rgb_to_lab,
)
from agents.render.restoration import equilibrer_blancs, restaurer  # noqa: E402


def _toile_froide(w=160, h=120):
    """Toile au parti-pris FROID (bleu dominant), comme un Cézanne/Caillebotte :
    chaque pixel a B > G > R → un nuage chromatique décalé vers le bleu."""
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = (70 + (x % 30), 110 + (y % 25), 150 + ((x + y) % 35))
    return img


class TestDeltaE2000(unittest.TestCase):
    """Vecteurs de test publiés par Sharma, Wu & Dalal (2005)."""

    CAS = [
        ((50, 2.6772, -79.7751), (50, 0, -82.7485), 2.0425),
        ((50, 3.1571, -77.2803), (50, 0, -82.7485), 2.8615),
        ((50, 2.5, 0), (50, 0, -2.5), 4.3065),
        ((50, 2.5, 0), (73, 25, -18), 27.1492),
        ((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387), 1.2644),
        ((22.7233, 20.0904, -46.6940), (23.0331, 14.9730, -42.5619), 2.0373),
        ((2.0776, 0.0795, -1.1350), (0.9033, -0.0636, -0.5514), 0.9082),
    ]

    def test_vecteurs_reference(self):
        for lab1, lab2, attendu in self.CAS:
            self.assertAlmostEqual(delta_e_2000(lab1, lab2), attendu, places=3)

    def test_symetrie_et_identite(self):
        a, b = (53.2, 80.1, 67.2), (52.0, 78.0, 65.0)
        self.assertAlmostEqual(delta_e_2000(a, a), 0.0, places=6)
        self.assertAlmostEqual(delta_e_2000(a, b), delta_e_2000(b, a), places=6)


class TestLab(unittest.TestCase):
    def test_blanc_et_noir(self):
        lb = rgb_to_lab((255, 255, 255))
        self.assertAlmostEqual(lb[0], 100.0, places=1)
        self.assertAlmostEqual(lb[1], 0.0, places=1)
        self.assertAlmostEqual(lb[2], 0.0, places=1)
        self.assertAlmostEqual(rgb_to_lab((0, 0, 0))[0], 0.0, places=3)

    def test_gris_est_neutre(self):
        a, b = rgb_to_lab((128, 128, 128))[1:]
        self.assertAlmostEqual(a, 0.0, places=1)
        self.assertAlmostEqual(b, 0.0, places=1)


class TestAudit(unittest.TestCase):
    def test_copie_identique_est_fidele(self):
        img = _toile_froide()
        rep = auditer_fidelite(img, img.copy())
        self.assertTrue(rep.ok)
        self.assertEqual(rep.verdict, "FIDÈLE")
        self.assertLess(rep.delta_e_moyen, 1.0)
        self.assertGreater(rep.chroma_ratio, 0.98)
        self.assertGreater(rep.dominante_ratio, 0.95)

    def test_gray_world_detecte_comme_infidele(self):
        """Le scénario Cézanne : gray-world neutralise la dominante froide."""
        img = _toile_froide()
        delave = equilibrer_blancs(img)  # exactement l'étape incriminée
        rep = auditer_fidelite(img, delave)
        self.assertNotEqual(rep.verdict, "FIDÈLE")
        # la dominante voulue est largement effacée
        self.assertLess(rep.dominante_ratio, 0.85)

    def test_profil_fidele_preserve_la_dominante(self):
        """Le profil par défaut ne déplace pas la teinte : dominante conservée."""
        img = _toile_froide()
        master, rapport = restaurer(img, long_edge_cible=max(img.size), profil="fidele")
        ref = img.crop(rapport.box_rognage) if rapport.box_rognage else img
        rep = auditer_fidelite(ref, master)
        self.assertFalse(rapport.deplace_teinte)
        self.assertGreater(rep.dominante_ratio, 0.9)
        self.assertGreater(rep.chroma_ratio, 0.9)

    def test_profil_archive_active_la_couleur(self):
        img = _toile_froide()
        _, rapport = restaurer(img, long_edge_cible=max(img.size), profil="archive")
        self.assertTrue(rapport.equilibrage_blancs)
        self.assertTrue(rapport.deplace_teinte)

    def test_n_grille_invalide_est_borne(self):
        # un n_grille 0/négatif accidentel doit dégrader, pas lever une erreur Pillow
        img = _toile_froide()
        for n in (0, -3):
            rep = auditer_fidelite(img, img.copy(), n_grille=n)
            self.assertEqual(rep.verdict, "FIDÈLE")

    def test_methode_nom_canonique(self):
        rep = auditer_fidelite(_toile_froide(), _toile_froide())
        self.assertEqual(rep.methode, "ciede2000")  # pas « ciede76 » par défaut


if __name__ == "__main__":
    unittest.main()
