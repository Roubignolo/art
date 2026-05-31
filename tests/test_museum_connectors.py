"""Tests des connecteurs musées AIC + Cleveland (logique de gate _normalize).

Schémas calqués sur les réponses API réelles (vérifiées le 2026-05-31).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.sources import artic, base, cleveland, europeana, smithsonian  # noqa: E402


class TestArtic(unittest.TestCase):
    def _obj(self, **over):
        base = {
            "id": 28560,
            "title": "The Bedroom",
            "artist_title": "Vincent van Gogh",
            "artist_display": "Vincent van Gogh\nDutch, 1853–1890",
            "date_display": "1889",
            "date_start": 1889,
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
        # preuve DP : naissance parsée + énoncé de droits
        self.assertEqual(r["artist_birth"], 1853)
        self.assertEqual(r["object_begin_year"], 1889)
        self.assertIn("CC0", r["rights_statement"])

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
        # preuve DP : naissance structurée + accession + licence
        self.assertEqual(r["artist_birth"], 1853)
        self.assertEqual(r["accession_number"], "1947.209")
        self.assertEqual(r["rights_statement"], "CC0")

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


class TestSmithsonian(unittest.TestCase):
    def _row(self, **over):
        media = over.pop("media", [{"type": "Images", "usage": {"access": "CC0"},
                                    "idsId": "FS-7011_03",
                                    "content": "https://ids.si.edu/ids/deliveryService?id=FS-7011_03"}])
        name = over.pop("name", [{"label": "Maker", "content": "Katsushika Hokusai (1760-1849)"}])
        date = over.pop("date", [{"label": "Date", "content": "Edo period, 1830"}])
        row = {
            "id": "edanmdm-fsg_F1903", "title": "Bridge at Yedo", "unitCode": "FSG", "type": "edanmdm",
            "content": {
                "descriptiveNonRepeating": {
                    "title": {"content": "Bridge at Yedo"},
                    "record_link": "http://n2t.net/ark:/65665/x",
                    "online_media": {"media": media},
                },
                "freetext": {"name": name, "date": date},
            },
        }
        row.update(over)
        return row

    def test_candidat_cc0(self):
        r = smithsonian._normalize(self._row())
        self.assertEqual(r["decision"], "CANDIDAT")
        self.assertEqual(r["artist_death"], 1849)
        self.assertTrue(r["gate_g1_us_g3"])
        self.assertIn("/iiif/", r["image_url"])
        self.assertTrue(smithsonian.ID_OFFSET <= r["objectID"] < smithsonian.ID_OFFSET + 90_000_000)

    def test_sans_media_rejet(self):
        r = smithsonian._normalize(self._row(media=[]))
        self.assertFalse(r["gate_g1_us_g3"])
        self.assertEqual(r["decision"], "REJET")

    def test_media_non_cc0_rejet(self):
        r = smithsonian._normalize(self._row(media=[{"type": "Images", "usage": {"access": "Restricted"},
                                                     "idsId": "X", "content": "u"}]))
        self.assertEqual(r["decision"], "REJET")

    def test_id_stable(self):
        a = smithsonian._normalize(self._row())["objectID"]
        b = smithsonian._normalize(self._row())["objectID"]
        self.assertEqual(a, b)  # hash déterministe


class TestEuropeana(unittest.TestCase):
    def _item(self, **over):
        base = {
            "id": "/90402/SK_A_3262",
            "title": ["Sunflowers"],
            "dataProvider": ["Van Gogh Museum"],
            "rights": ["http://creativecommons.org/publicdomain/mark/1.0/"],
            "edmIsShownBy": ["https://img/full.jpg"],
            "edmPreview": ["https://thumb"],
            "year": ["1889"],
            "dcCreator": ["Vincent van Gogh"],
            "guid": "https://europeana.eu/item/90402/SK_A_3262",
            "country": ["Netherlands"],
        }
        base.update(over)
        return base

    def test_candidat_domaine_public(self):
        r = europeana._normalize(self._item())
        self.assertEqual(r["decision"], "CANDIDAT")
        self.assertTrue(r["gate_g1_us_g3"])
        self.assertEqual(r["image_url"], "https://img/full.jpg")
        self.assertTrue(europeana.ID_OFFSET <= r["objectID"] < europeana.ID_OFFSET + 90_000_000)

    def test_droits_cc_by_rejet(self):
        r = europeana._normalize(self._item(rights=["http://creativecommons.org/licenses/by/4.0/"]))
        self.assertFalse(r["gate_g1_us_g3"])
        self.assertEqual(r["decision"], "REJET")

    def test_noc_accepte(self):
        r = europeana._normalize(self._item(rights=["http://rightsstatements.org/vocab/NoC-OKLR/1.0/"]))
        self.assertTrue(r["gate_g1_us_g3"])

    def test_oeuvre_recente_rejet(self):
        r = europeana._normalize(self._item(year=["1975"]))
        self.assertFalse(r["gate_g1_ue"])
        self.assertEqual(r["decision"], "REJET")

    def test_annee_inconnue_review(self):
        r = europeana._normalize(self._item(year=[]))
        self.assertIsNone(r["gate_g1_ue"])
        self.assertEqual(r["decision"], "REVIEW")

    def test_bandes_offsets_toutes_distinctes(self):
        offs = {artic.ID_OFFSET, cleveland.ID_OFFSET, smithsonian.ID_OFFSET, europeana.ID_OFFSET}
        self.assertEqual(len(offs), 4)  # aucune collision de bande


class TestPreuveDP(unittest.TestCase):
    def test_evidence_complete(self):
        rec = {
            "artist": "Vincent van Gogh", "artist_death": 1890, "object_begin_year": 1889,
            "gate_g1_us_g3": True, "is_public_domain": True, "rights_statement": "CC0",
            "wikidata_copyright_status": "public domain",
            "wikidata_url": "https://www.wikidata.org/wiki/Q18689458", "accession_number": "1993.132",
        }
        ev, conf = base.build_dp_evidence(rec)
        self.assertIn("† 1890", ev)
        self.assertIn("1889", ev)
        self.assertIn("CC0", ev)
        self.assertIn("public domain", ev)
        self.assertIn("1993.132", ev)
        self.assertGreaterEqual(len(conf), 2)  # institution + wikidata

    def test_deces_inconnu_signale_review(self):
        ev, _ = base.build_dp_evidence({"artist": "X", "gate_g1_ue": None})
        self.assertIn("vérification humaine", ev)

    def test_auteur_encore_protege(self):
        ev, _ = base.build_dp_evidence({"artist": "Z", "artist_death": 1990, "gate_g1_us_g3": True})
        self.assertIn("ENCORE PROTÉGÉ", ev)

    def test_finalize_remplit_defauts_et_evidence(self):
        rec = {"artist": "Y", "artist_death": 1880}
        base.finalize_record(rec)
        for k in base.DP_FIELDS:
            self.assertIn(k, rec)
        self.assertIsInstance(rec["dp_confirmations"], list)
        self.assertTrue(rec["dp_evidence"])


if __name__ == "__main__":
    unittest.main()
