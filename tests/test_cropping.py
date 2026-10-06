import unittest
from PIL import Image
from freeda.cropping import parse_aspect, fit_linked_crop
from freeda.models import Crop, LayoutMode, WebRenderOptions
from freeda.render import render_web, _caption_metrics, _font

class CroppingTests(unittest.TestCase):
    def test_aspect_validation(self):
        self.assertIsNone(parse_aspect("Original"))
        self.assertAlmostEqual(parse_aspect("4:3"), 4/3)
        self.assertEqual(parse_aspect("1,5"), 1.5)
        for value in ("0", "-1", "nan", "inf", "1:0", "4:3:2", "abc", "-1:-1", "1:inf"):
            with self.assertRaises(ValueError):
                parse_aspect(value)

    def test_reuse_crop_fits_different_source_ratios(self):
        for size in ((300, 200), (200, 300)):
            crop = fit_linked_crop(size, Crop(.1, .2, .8, .6), 4/3)
            self.assertAlmostEqual(size[0]*crop.width/(size[1]*crop.height), 4/3)
            self.assertGreaterEqual(crop.x, .1)
            self.assertGreaterEqual(crop.y, .2)
            self.assertLessEqual(crop.x+crop.width, .9)
            self.assertLessEqual(crop.y+crop.height, .8)

    def test_web_crop_preserves_width_and_linked_order(self):
        source = Image.new("RGB", (600, 200), "red")
        source.paste(Image.new("RGB", (300, 200), "lime"), (300, 0))
        original = render_web(source, WebRenderOptions(layout=LayoutMode.LRL))
        square = render_web(source, WebRenderOptions(layout=LayoutMode.LRL, eye_aspect=1))
        self.assertEqual(square.width, 2048)
        self.assertGreater(square.height, original.height)
        colors = [square.getpixel((round(square.width*x),square.height//2))[:3] for x in (1/6,1/2,5/6)]
        self.assertEqual(colors, [(255,0,0),(0,255,0),(255,0,0)])

    def test_long_caption_stays_within_eye(self):
        font = _font("Segoe UI", 25)
        lines, step, height = _caption_metrics("Ein langer Untertitel " * 8, font, 200)
        self.assertGreater(len(lines), 1)
        self.assertLess(height, len(lines)*step)  # No trailing line gap below the last line.
        self.assertGreater(height, (len(lines)-1)*step)
        for line in lines:
            self.assertLessEqual(font.getlength(line), 200)


class LrlCaptionTests(unittest.TestCase):
    def test_lrl_ellipsis_and_font_limit(self):
        from freeda.render import _fit_lrl_caption
        font = _font("Segoe UI", 40)
        text, fitted = _fit_lrl_caption("Ein wirklich sehr langer Untertitel " * 10, font, "Segoe UI", 300)
        self.assertTrue(text.endswith("…"))
        self.assertNotIn("\n", text)
        self.assertLessEqual(fitted.getlength(text), 300)
        self.assertGreaterEqual(fitted.size, 30)
        short, same = _fit_lrl_caption("Kurz", font, "Segoe UI", 300)
        self.assertEqual(short, "Kurz")
        self.assertEqual(same.size, 40)

    def test_lrl_long_caption_does_not_grow_web_height(self):
        source = Image.new("RGB", (600, 200), "red")
        short = render_web(source, WebRenderOptions(layout=LayoutMode.LRL, caption="Kurz"))
        long = render_web(source, WebRenderOptions(layout=LayoutMode.LRL, caption="Langer Untertitel " * 30))
        self.assertLessEqual(long.height, short.height)
