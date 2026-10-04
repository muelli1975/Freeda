from __future__ import annotations

import unittest

from freeda.config import PRINT_FORMAT_PRESETS
from freeda.geometry import frame_geometry_for_total_width, mm_to_px, print_canvas_px


class GeometryTests(unittest.TestCase):
    def test_web_presets_are_exact_width(self):
        for width in (1280, 1600, 1920, 2048, 3840):
            geometry = frame_geometry_for_total_width(width, 1.5)
            self.assertEqual(2 * geometry.eye_width + 3 * geometry.frame_px, width)
            self.assertEqual(geometry.eye_width, int(geometry.eye_width))

    def test_frame_is_relative_to_one_eye(self):
        geometry = frame_geometry_for_total_width(1920, 1.5)
        measured = geometry.frame_px / geometry.eye_width * 100
        self.assertAlmostEqual(measured, 1.5, delta=0.15)

    def test_photo_lab_presets_are_landscape(self):
        for label in ("Foto 9 × 13 cm", "Foto 10 × 15 cm", "Foto 11 × 17 cm",
                      "Foto 13 × 18 cm", "Foto 15 × 20 cm", "Foto 20 × 30 cm"):
            width, height = PRINT_FORMAT_PRESETS[label]
            self.assertGreater(width, height)

    def test_print_conversion(self):
        self.assertEqual(mm_to_px(25.4, 300), 300)
        self.assertEqual(print_canvas_px(148, 105, 300, 3), (1819, 1311))


if __name__ == "__main__":
    unittest.main()
