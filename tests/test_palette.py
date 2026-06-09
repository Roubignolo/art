"""Tests de l'analyse de palette (agents/render/palette.py)."""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image  # noqa: E402

from agents.render.palette import analyser_palette  # noqa: E402


def _uni(color, w=160, h=120):
    return Image.new("RGB", (w, h), color)


class TestPalette(unittest.TestCase):
    def test_vert_sature_est_nature(self):
        p = analyser_palette(_uni((40, 140, 60)))
        self.assertIn("Verts & nature", p["tags"])
        self.assertEqual(p["famille_dominante"], "vert")

    def test_orange_est_tons_orangés(self):
        p = analyser_palette(_uni((200, 90, 30)))
        self.assertIn("Tons orangés", p["tags"])

    def test_bleu_profond(self):
        p = analyser_palette(_uni((30, 50, 150)))
        self.assertIn("Bleus profonds", p["tags"])

    def test_quasi_gris_est_sepia_neutres(self):
        p = analyser_palette(_uni((128, 126, 124)))
        self.assertIn("Sépia & neutres", p["tags"])
        # une œuvre neutre ne reçoit pas de tag couleur vif
        self.assertNotIn("Vif & saturé", p["tags"])

    def test_swatches_sont_des_hex(self):
        p = analyser_palette(_uni((120, 80, 160)))
        self.assertTrue(p["swatches"])
        for hx in p["swatches"]:
            self.assertRegex(hx, r"^#[0-9a-f]{6}$")

    def test_toujours_un_tag(self):
        # toute œuvre obtient au moins un tag de palette
        for col in [(40, 140, 60), (200, 90, 30), (30, 50, 150), (128, 126, 124), (210, 180, 90)]:
            self.assertTrue(analyser_palette(_uni(col))["tags"])


if __name__ == "__main__":
    unittest.main()
