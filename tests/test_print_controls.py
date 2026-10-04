import unittest
from dataclasses import replace

from PIL import Image

from freeda.geometry import print_canvas_px
from freeda.i18n import translate
from freeda.models import LayoutMode, PrintRenderOptions, WebRenderOptions
from freeda.preview import fit_preview, parse_bleed, print_preview_options, print_preview_image
from freeda.geometry import frame_geometry_for_total_width, mm_to_px
from freeda.print_render import print_eye_aspect, render_print
from freeda.render import render_web


class PrintControlTests(unittest.TestCase):
    def test_arbitrary_bleed_decimal_comma_and_zero(self):
        for text, expected in (("0", 0), ("2,5", 2.5), (" 4.25 ", 4.25), ("12", 12)):
            self.assertEqual(parse_bleed(text), expected)
        for text in ("", "text", "-1", "nan", "inf"):
            with self.assertRaises(ValueError):
                parse_bleed(text)

    def test_custom_bleed_produces_exact_print_canvas(self):
        source = Image.new("RGB", (600, 200), "red")
        for dpi in (300, 600):
            options = PrintRenderOptions(width_mm=130, height_mm=60, dpi=dpi, bleed_mm=2.5)
            self.assertEqual(render_print(source, options).size, print_canvas_px(130, 60, dpi, 2.5))

    def test_preview_upscales_and_fits_without_distortion(self):
        image = Image.new("RGB", (300, 200))
        self.assertEqual(fit_preview(image, 900, 700).size, (900, 600))
        self.assertEqual(fit_preview(image, 120, 50).size, (75, 50))
        self.assertEqual(fit_preview(image, 0, 0).size, (1, 1))

    def test_preview_dpi_tracks_panel_without_changing_export(self):
        options = PrintRenderOptions(dpi=600, bleed_mm=2.5, caption="Caption", caption_size_percent=5)
        small = print_preview_options(options, 400, 300)
        large = print_preview_options(options, 1000, 800)
        self.assertGreater(large.dpi, small.dpi)
        self.assertEqual(options.dpi, 600)
        self.assertEqual(replace(large, dpi=600), options)

    def test_caption_size_grows_web_band_and_print_crop(self):
        source = Image.new("RGB", (600, 200), "red")
        small = WebRenderOptions(layout=LayoutMode.PARALLEL, caption="Caption", caption_size_percent=2)
        large = replace(small, caption_size_percent=6)
        self.assertGreater(render_web(source, large).height, render_web(source, small).height)
        small_print = PrintRenderOptions(caption="Caption", caption_size_percent=2)
        large_print = replace(small_print, caption_size_percent=6)
        self.assertGreater(print_eye_aspect(large_print), print_eye_aspect(small_print))
        self.assertEqual(render_print(source, small_print).size, render_print(source, large_print).size)

    def test_english_messages_and_choices(self):
        self.assertEqual(translate("Kreuzblick", "en"), "Cross-eyed viewing")
        self.assertEqual(translate("Parallelblick", "de"), "Parallelblick")
        self.assertEqual(translate("Fertig – 1 Datei", "en"), "Done – 1 file")
        self.assertEqual(translate("2 Bilder gewählt", "en"), "2 images selected")
        self.assertEqual(translate("Untertitelgröße: 3,50 % je Halbbild", "en"), "Caption size: 3.50 % per view")
        self.assertEqual(translate("Bild 1 von 2 — Aufnahme.png", "en"), "Image 1 of 2 — Aufnahme.png")

    def test_print_frame_fraction_matches_web_at_every_dpi(self):
        for dpi in (96, 300, 600):
            width = mm_to_px(150, dpi)
            geometry = frame_geometry_for_total_width(width, 3)
            self.assertAlmostEqual(geometry.frame_px / geometry.eye_width, 0.03, delta=0.004)
            source = Image.new("RGB", (600, 200), "red")
            options = PrintRenderOptions(width_mm=150, height_mm=100, dpi=dpi, bleed_mm=3, frame_percent=3)
            trim = print_preview_image(source, options)
            self.assertEqual(trim.size, (width, mm_to_px(100, dpi)))
            self.assertEqual(trim.getpixel((geometry.frame_px - 1, geometry.frame_px + 10)), (17, 17, 17, 255))
            self.assertEqual(trim.getpixel((geometry.frame_px, geometry.frame_px + 10)), (255, 0, 0, 255))
            full = print_preview_image(source, options, show_bleed=True)
            self.assertEqual(full.size, render_print(source, options).size)
            self.assertGreater(full.width, trim.width)


if __name__ == "__main__":
    unittest.main()


class FreeDpiTests(unittest.TestCase):
    def test_custom_dpi(self):
        from freeda.preview import parse_dpi
        for value in ("72", "240", "450", "1200", " 360 "):
            self.assertEqual(parse_dpi(value), int(value))
        for value in ("", "0", "-1", "300.5", "nan", "abc"):
            with self.assertRaises(ValueError):
                parse_dpi(value)
