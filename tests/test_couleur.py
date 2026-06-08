"""Tests de la gestion colorimétrique ICC (agents/render/couleur.py).

Couvre : conversion ICC→sRGB (passthrough sRGB, conversion d'un profil large-gamut,
robustesse aux profils illisibles), octets sRGB de tagging, et le soft-proof gamut
(vrai soft-proof ICC + heuristique de chroma).
"""

import glob
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageCms  # noqa: E402

from agents.render.couleur import (  # noqa: E402
    assurer_srgb,
    rapport_gamut,
    srgb_icc_bytes,
)


def _profil_large_gamut():
    """Octets + description d'un profil RGB large-gamut système (P3/AdobeRGB/ROMM/
    ProPhoto), ou None si la machine n'en expose aucun (→ test sauté, jamais faussé)."""
    motifs = [
        "/System/Library/ColorSync/Profiles/*.icc",
        "/System/Library/ColorSync/Profiles/*.icm",
        "/Library/ColorSync/Profiles/*.icc",
        "/usr/share/color/icc/**/*.icc",
        "/usr/share/color/icc/*.icc",
    ]
    for motif in motifs:
        for chemin in glob.glob(motif, recursive=True):
            try:
                desc = ImageCms.getProfileDescription(ImageCms.getOpenProfile(chemin)).strip()
            except Exception:
                continue
            if any(k in desc for k in ("Display P3", "Adobe RGB", "ProPhoto", "ROMM")):
                with open(chemin, "rb") as f:
                    return f.read(), desc
    return None


def _profil_cmyk():
    """Octets d'un profil CMYK système, ou None (→ test sauté, jamais faussé)."""
    motifs = [
        "/System/Library/ColorSync/Profiles/*CMYK*.icc",
        "/usr/share/color/icc/**/*CMYK*.icc",
        "/usr/share/color/icc/**/*coated*.icc",
    ]
    for motif in motifs:
        for chemin in glob.glob(motif, recursive=True):
            try:
                ImageCms.getProfileDescription(ImageCms.getOpenProfile(chemin))
                with open(chemin, "rb") as f:
                    return f.read()
            except Exception:
                continue
    return None


class TestAssurerSrgb(unittest.TestCase):
    def test_sans_profil_suppose_srgb(self):
        out, info = assurer_srgb(Image.new("RGB", (32, 32), (120, 90, 60)))
        self.assertFalse(info["converti"])
        self.assertEqual(out.mode, "RGB")

    def test_profil_srgb_pas_de_conversion(self):
        img = Image.new("RGB", (32, 32), (120, 90, 60))
        img.info["icc_profile"] = srgb_icc_bytes()
        out, info = assurer_srgb(img)
        self.assertFalse(info["converti"])
        self.assertIn("srgb", info["espace_source"].lower())

    def test_profil_illisible_est_gracieux(self):
        img = Image.new("RGB", (32, 32), (120, 90, 60))
        img.info["icc_profile"] = b"ceci n'est pas un profil ICC"
        out, info = assurer_srgb(img)  # ne doit pas lever
        self.assertFalse(info["converti"])
        self.assertEqual(out.mode, "RGB")

    def test_profil_large_gamut_est_converti(self):
        prof = _profil_large_gamut()
        if not prof:
            self.skipTest("aucun profil large-gamut système disponible")
        icc, _desc = prof
        img = Image.new("RGB", (48, 48), (220, 30, 30))  # rouge saturé
        img.info["icc_profile"] = icc
        out, info = assurer_srgb(img)
        self.assertTrue(info["converti"])
        self.assertEqual(out.mode, "RGB")
        self.assertEqual(out.size, (48, 48))
        # un rouge large-gamut ne reste pas identique une fois ramené en sRGB
        self.assertNotEqual(out.getpixel((24, 24)), (220, 30, 30))

    def test_source_cmyk_convertie_depuis_le_mode_natif(self):
        icc = _profil_cmyk()
        if not icc:
            self.skipTest("aucun profil CMYK système disponible")
        img = Image.new("CMYK", (40, 40), (30, 200, 200, 5))
        img.info["icc_profile"] = icc
        out, info = assurer_srgb(img)
        self.assertTrue(info["converti"])
        self.assertEqual(out.mode, "RGB")
        self.assertEqual(out.size, (40, 40))

    def test_cmyk_sans_profil_est_etiquete_honnetement(self):
        # un CMYK sans profil subit un convert('RGB') non géré → ne PAS mentir « sRGB »
        img = Image.new("CMYK", (16, 16), (10, 200, 200, 0))
        out, info = assurer_srgb(img)
        self.assertEqual(out.mode, "RGB")
        self.assertNotIn("sRGB présumé", info["espace_source"])
        self.assertIn("CMYK", info["espace_source"])
        self.assertTrue(info["converti"])


class TestSrgbBytes(unittest.TestCase):
    def test_octets_reparsables_en_srgb(self):
        b = srgb_icc_bytes()
        self.assertGreater(len(b), 100)
        desc = ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(b))).strip()
        self.assertIn("srgb", desc.lower())


class TestGamut(unittest.TestCase):
    @staticmethod
    def _uni(color):
        return Image.new("RGB", (160, 120), color)

    def test_softproof_icc_papier_srgb_est_quasi_zero(self):
        # papier = sRGB → tout reproductible → ~0 % hors-gamut (valide la plomberie)
        chemin = "/tmp/_srgb_test_paper.icc"
        with open(chemin, "wb") as f:
            f.write(srgb_icc_bytes())
        try:
            g = rapport_gamut(self._uni((180, 120, 40)), profil_papier=chemin)
            self.assertEqual(g["methode"], "icc-softproof")
            self.assertLess(g["hors_gamut_pct"], 1.0)
            self.assertLess(g["delta_e_max"], 1.0)
        finally:
            os.remove(chemin)

    def test_heuristique_sans_profil(self):
        g = rapport_gamut(self._uni((180, 120, 40)))
        self.assertEqual(g["methode"], "heuristique-chroma")
        self.assertIn("teinte_a_risque", g)
        self.assertIn("chroma_max", g)
        # honnêteté : l'heuristique porte un avertissement « pas un gamut »
        self.assertIn("avertissement", g)
        self.assertIn("saturation", g["avertissement"].lower())

    def test_satur_e_plus_a_risque_que_neutre(self):
        sature = rapport_gamut(self._uni((20, 40, 200)))    # bleu très saturé
        neutre = rapport_gamut(self._uni((128, 128, 128)))  # gris neutre
        self.assertGreater(sature["chroma_max"], neutre["chroma_max"] + 20)


if __name__ == "__main__":
    unittest.main()
