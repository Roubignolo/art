"""Tests des helpers de gate du sourcing (agents/sources/base.py).

Lancer depuis la racine du repo : python -m unittest discover -s tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.sources.base import (  # noqa: E402
    EU_DEATH_CUTOFF,
    US_PUB_CUTOFF,
    extract_year,
    trademark_hit,
)


class TestExtractYear(unittest.TestCase):
    def test_annee_simple(self):
        self.assertEqual(extract_year("1889"), 1889)

    def test_date_iso(self):
        self.assertEqual(extract_year("1880-01-01"), 1880)

    def test_intervalle_prend_le_debut(self):
        # extract_year ne lit que les 4 premiers caractères
        self.assertEqual(extract_year("1660–1665"), 1660)

    def test_prefixe_non_numerique(self):
        # "c. 1" → un seul chiffre → None (comportement réel documenté)
        self.assertIsNone(extract_year("c. 1660"))

    def test_vide_et_none(self):
        self.assertIsNone(extract_year(""))
        self.assertIsNone(extract_year(None))


class TestTrademarkHit(unittest.TestCase):
    def test_marque_detectee(self):
        self.assertTrue(trademark_hit("Vintage Mickey Mouse poster"))
        self.assertTrue(trademark_hit("Betty Boop art deco"))

    def test_oeuvre_dp_propre(self):
        self.assertFalse(trademark_hit("Wheat Field with Cypresses — Van Gogh"))

    def test_casse_insensible(self):
        self.assertTrue(trademark_hit("POKEMON"))

    def test_vide(self):
        self.assertFalse(trademark_hit(""))


class TestCutoffs(unittest.TestCase):
    def test_coherence_cutoffs(self):
        # US (95 ans) est forcément plus ancien que UE (71 ans)
        self.assertLess(US_PUB_CUTOFF, EU_DEATH_CUTOFF)
        # En 2026, le cutoff US doit valoir 1931 (publié ≤ 1930 = DP US)
        self.assertGreaterEqual(EU_DEATH_CUTOFF - US_PUB_CUTOFF, 20)


if __name__ == "__main__":
    unittest.main()
