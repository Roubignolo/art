"""Tests du moteur de scoring (agents/scoring_agent.py)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.scoring_agent import (  # noqa: E402
    THRESH_FILE_ATTENTE,
    THRESH_PRODUIRE,
    decide,
    keep_record,
    score_attribution,
    score_traduisibilite,
)


class TestScoreAttribution(unittest.TestCase):
    def test_rec_complet_plafonne_a_10(self):
        rec = {
            "artist": "Vincent van Gogh", "artist_bio": "Dutch, 1853–1890",
            "object_date": "1889", "medium": "Oil on canvas",
            "dimensions": "73×93 cm", "credit_line": "Annenberg",
            "classification": "Paintings", "department": "European Paintings",
        }
        self.assertEqual(score_attribution(rec), 10.0)

    def test_rec_vide_donne_zero(self):
        self.assertEqual(score_attribution({}), 0.0)

    def test_artiste_anonyme_ne_compte_pas(self):
        self.assertEqual(score_attribution({"artist": "Unknown"}), 0.0)
        self.assertEqual(score_attribution({"artist": "Anonyme"}), 0.0)

    def test_artiste_nomme_compte(self):
        self.assertEqual(score_attribution({"artist": "Hokusai"}), 2.0)


class TestDecide(unittest.TestCase):
    def test_seuils(self):
        self.assertEqual(decide(7.0), "produire")
        self.assertEqual(decide(THRESH_PRODUIRE), "produire")
        self.assertEqual(decide(5.5), "file_attente")
        self.assertEqual(decide(THRESH_FILE_ATTENTE), "file_attente")
        self.assertEqual(decide(4.9), "rejet")
        self.assertEqual(decide(0.0), "rejet")


class TestTraduisibilite(unittest.TestCase):
    def test_borne_0_10(self):
        rec = {"width": 4000, "height": 5600, "resolution_px": 5600, "classification": "Prints"}
        v = score_traduisibilite(rec, "poster")
        self.assertGreaterEqual(v, 0.0)
        self.assertLessEqual(v, 10.0)

    def test_haute_resolution_mieux_que_basse(self):
        bonne = {"width": 4000, "height": 5600, "resolution_px": 5600, "classification": "Prints"}
        faible = {"width": 800, "height": 1100, "resolution_px": 1100, "classification": "Prints"}
        self.assertGreater(
            score_traduisibilite(bonne, "poster"),
            score_traduisibilite(faible, "poster"),
        )


class TestKeepRecord(unittest.TestCase):
    def test_rejet_exclu(self):
        self.assertFalse(keep_record({"decision": "REJET"}, include_review=False))

    def test_review_selon_flag(self):
        self.assertFalse(keep_record({"decision": "REVIEW"}, include_review=False))
        self.assertTrue(keep_record({"decision": "REVIEW"}, include_review=True))

    def test_candidat_garde(self):
        self.assertTrue(keep_record({"decision": "CANDIDAT"}, include_review=False))

    def test_resolution_ko_exclue(self):
        self.assertFalse(keep_record({"decision": "CANDIDAT", "resolution_ok": False}, include_review=False))


if __name__ == "__main__":
    unittest.main()
