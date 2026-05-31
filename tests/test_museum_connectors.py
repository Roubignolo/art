"""Tests des connecteurs musées AIC + Cleveland (logique de gate _normalize).

Schémas calqués sur les réponses API réelles (vérifiées le 2026-05-31).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.sources import artic, cleveland  # noqa: E402


class TestArtic(unittest.TestCase):
    def _obj(self, **over):
        base = {
            "id": 28560,
            "title": "The Bedroom",
            "artist_title": "Vincent van Gogh",
            "artist_display": "Vincent van Gogh\nDutch, 1853–1890",
            "date_display": "1889",
            "date_end": 1889,
            "medium_display": "Oil on canvas",
            "dimensions": "73 × 92 cm",
            "credit_line": "Helen Birch Bartlett",
            "is_public_domain": True,
            "classification_title": "Painting",
            "department_title": "European Painting",
            "image_id": "abc-123",
        }
        base.update(over)
        return base

    def test_candidat_domaine_public(self):
        r = artic._normalize(self._obj())
        self.assertEqual(r["decision"], "CANDIDAT")
        self.assertEqual(r["objectID"], 28560 + artic.ID_OFFSET)
        self.assertTrue(r["gate_g1_ue"])
        self.assertIn("/iiif/2/abc-123/", r["image_url"])
        self.assertEqual(r["artist_death"], 1890)

    def test_non_domaine_public_rejet(self):
        r = artic._normalize(self._obj(is_public_domain=False))
        self.assertEqual(r["decision"], "REJET")

    def test_sans_image_rejet(self):
        r = artic._normalize(self._obj(image_id=None))
        self.assertEqual(r["decision"], "REJET")

    def test_oeuvre_recente_rejet(self):
        # œuvre datée 2001, décès auteur indéterminé → fin > 1900 → non DP → REJET
        r = artic._normalize(self._obj(artist_display="Jane Doe (American, born 1950)", date_end=2001))
        self.assertFalse(r["gate_g1_ue"])
        self.assertEqual(r["decision"], "REJET")

    def test_dates_inconnues_passe_en_review(self):
        # ni décès ni année de fin → indéterminé → validation humaine
        r = artic._normalize(self._obj(artist_display="Anonyme", date_end=None, date_display=""))
        self.assertIsNone(r["gate_g1_ue"])
        self.assertEqual(r["decision"], "REVIEW")

    def test_marque_rejet(self):
        r = artic._normalize(self._obj(title="Mickey Mouse study", artist_title="Disney"))
        self.assertFalse(r["gate_g2_marque"])
        self.assertEqual(r["decision"], "REJET")


class TestCleveland(unittest.TestCase):
    def _obj(self, **over):
        base = {
            "id": 125249,
            "accession_number": "1947.209",
            "share_license_status": "CC0",
            "title": "The Large Plane Trees",
            "creation_date": "1889",
            "creation_date_latest": 1889,
            "type": "Painting",
            "technique": "oil on fabric",
            "measurements": "73.4 x 91.8 cm",
            "department": "Modern European Painting",
            "creators": [{"description": "Vincent van Gogh (Dutch, 1853–1890)", "role": "artist",
                          "birth_year": 1853, "death_year": 1890}],
            "images": {"full": {"url": "https://cdn/full.tif", "width": 4000, "height": 3200}},
            "url": "https://clevelandart.org/art/1947.209",
        }
        base.update(over)
        return base

    def test_candidat_cc0_haute_res(self):
        r = cleveland._normalize(self._obj(), min_long_edge=3000)
        self.assertEqual(r["decision"], "CANDIDAT")
        self.assertEqual(r["objectID"], 125249 + cleveland.ID_OFFSET)
        self.assertEqual(r["artist"], "Vincent van Gogh")
        self.assertEqual(r["artist_death"], 1890)
        self.assertEqual(r["resolution_px"], 4000)
        self.assertTrue(r["resolution_ok"])

    def test_basse_resolution_rejet(self):
        r = cleveland._normalize(
            self._obj(images={"full": {"url": "https://cdn/x.tif", "width": 1000, "height": 800}}),
            min_long_edge=3000,
        )
        self.assertFalse(r["resolution_ok"])
        self.assertEqual(r["decision"], "REJET")

    def test_non_cc0_rejet(self):
        r = cleveland._normalize(self._obj(share_license_status="Copyrighted"), min_long_edge=3000)
        self.assertEqual(r["decision"], "REJET")

    def test_oeuvre_recente_rejet(self):
        # décès auteur inconnu mais œuvre datée 1990 → fin > 1900 → non DP → REJET
        r = cleveland._normalize(
            self._obj(creators=[{"description": "Jane Doe", "role": "artist", "death_year": None}],
                      creation_date_latest=1990),
            min_long_edge=3000,
        )
        self.assertFalse(r["gate_g1_ue"])
        self.assertEqual(r["decision"], "REJET")

    def test_dates_inconnues_review(self):
        # ni décès ni année de fin → indéterminé → validation humaine
        r = cleveland._normalize(
            self._obj(creators=[{"description": "Anonyme", "role": "artist", "death_year": None}],
                      creation_date=None, creation_date_latest=None),
            min_long_edge=3000,
        )
        self.assertIsNone(r["gate_g1_ue"])
        self.assertEqual(r["decision"], "REVIEW")

    def test_offsets_distincts(self):
        # garantie anti-collision entre bandes d'ID
        self.assertNotEqual(artic.ID_OFFSET, cleveland.ID_OFFSET)
        self.assertGreater(cleveland.ID_OFFSET, artic.ID_OFFSET)


if __name__ == "__main__":
    unittest.main()
