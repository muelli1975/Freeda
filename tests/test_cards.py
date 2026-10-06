"""Physical card dimensions, caption limits and shared image contours."""
import unittest
from dataclasses import replace
from PIL import Image, ImageChops
from freeda.config import CARD_TEMPLATES, COLOR_PRESETS, PRINT_FORMAT_PRESETS
from freeda.models import EyeShape, LayoutMode, PrintMargins, PrintRenderOptions, WebRenderOptions
from freeda.print_layout import print_layout
from freeda.print_render import render_print
from freeda.render import render_web, _caption_metrics, _font
from freeda.eye_shapes import eye_mask
from freeda.crop_grid import crop_grid
from freeda.i18n import translate


class CardTests(unittest.TestCase):
    def holmes(self, **changes):
        paper, margins, _ = CARD_TEMPLATES["Holmes-Karte"]
        w, h = PRINT_FORMAT_PRESETS[paper]
        return replace(PrintRenderOptions(width_mm=w, height_mm=h, margins=margins,
                       show_symbols=False, eye_shape=EyeShape.ARCH), **changes)

    def test_holmes_dimensions_are_physical_at_every_resolution(self):
        source = Image.new("RGB", (600, 200), "red")
        for dpi in (72, 96, 300, 600):
            options = self.holmes(dpi=dpi)
            card = print_layout(options)
            self.assertAlmostEqual(card.eye_width_mm, 76.2)
            self.assertAlmostEqual(card.eye_height_mm, 76.2)
            self.assertAlmostEqual(card.centre_distance_mm, 77.8)
            image = render_print(source, options)
            self.assertEqual(image.size, (7 * dpi, round(3.5 * dpi)))
            for x0, y0, x1, y1 in card.eye_boxes(dpi):
                self.assertEqual(image.getpixel(((x0+x1)//2, y0)), (255, 0, 0, 255))
                self.assertEqual(image.getpixel((x0, y0)), (17, 17, 17, 255))
                self.assertEqual(image.getpixel((x0, y1-1)), (255, 0, 0, 255))
            self.assertEqual(image.getpixel((0, 0)), (17, 17, 17, 255))

    def test_templates_are_distinct_true_layouts(self):
        for name, expected in (("Stereokarte 18 × 9 cm", (180, 90, 76.2, 76.2, 78.8)),
                               ("Raumbildkarte 13 × 6 cm", (130, 60, 59, 52, 61))):
            paper, margins, _ = CARD_TEMPLATES[name]
            w, h = PRINT_FORMAT_PRESETS[paper]
            card = print_layout(PrintRenderOptions(width_mm=w, height_mm=h, margins=margins))
            for actual, target in zip((w,h,card.eye_width_mm,card.eye_height_mm,card.centre_distance_mm), expected):
                self.assertAlmostEqual(actual, target)

    def test_caption_keeps_exact_window_and_wraps_independently_of_dpi(self):
        empty = print_layout(self.holmes())
        layouts = [print_layout(self.holmes(dpi=dpi, caption="ÄÖÜ é g", caption_points=9,
                       caption_gap_top_mm=1, caption_gap_bottom_mm=1.5)) for dpi in (72,96,300,600)]
        for card in layouts:
            self.assertEqual((card.eye_width_mm, card.eye_height_mm), (empty.eye_width_mm, empty.eye_height_mm))
            self.assertEqual(card.caption_lines, layouts[0].caption_lines)
            self.assertAlmostEqual(card.caption_font_mm, 9 * 25.4 / 72, delta=25.4 / 600)
            self.assertEqual(card.caption_top_mm, 1)
            self.assertEqual(card.caption_bottom_mm, 1.5)
        with self.assertRaisesRegex(ValueError, "Untertitel passt"):
            print_layout(self.holmes(caption="A\nB\nC\nD", caption_points=20))

    def test_bad_physical_values_do_not_silently_change_layout(self):
        for value in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                print_layout(self.holmes(margins=PrintMargins(side_mm=value)))
        for options in (self.holmes(width_mm=0), self.holmes(margins=PrintMargins(side_mm=90)),
                        self.holmes(margins=PrintMargins(bottom_mm=90)),
                        self.holmes(caption_points=0), self.holmes(caption_gap_bottom_mm=-1)):
            with self.assertRaises(ValueError):
                print_layout(options)

    def test_exact_rows_and_lrl_have_requested_gaps_and_order(self):
        source = Image.new("RGB", (400, 100), "red")
        source.paste("lime", (200, 0, 400, 100))
        margins = PrintMargins(side_mm=4, top_mm=3, centre_mm=2, bottom_mm=7, row_gap_mm=5)
        for mode, colours in ((LayoutMode.BOTH, ("red", "lime", "lime", "red")),
                              (LayoutMode.LRL, ("red", "lime", "red"))):
            options = PrintRenderOptions(width_mm=130, height_mm=90, layout=mode, margins=margins,
                        eye_shape=EyeShape.RECTANGLE, show_symbols=False)
            card = print_layout(options)
            result = render_print(source, options)
            for box, colour in zip(card.eye_boxes(options.dpi), colours):
                x0,y0,x1,y1 = box
                self.assertEqual(result.getpixel(((x0+x1)//2, (y0+y1)//2)), Image.new("RGBA",(1,1),colour).getpixel((0,0)))
            if mode == LayoutMode.BOTH:
                self.assertAlmostEqual(card.y_mm[1] - card.y_mm[0] - card.eye_height_mm, 12)

    def test_contours_keep_square_bottom_and_smooth_top(self):
        size = (200,160)
        for shape in (EyeShape.TOP_ROUNDED, EyeShape.ARCH):
            mask = eye_mask(size, 24, shape, 18)
            self.assertEqual(mask.getpixel((0,0)), 0)
            self.assertEqual(mask.getpixel((100,0)), 255)
            self.assertEqual(mask.getpixel((0,159)), 255)
            self.assertTrue(any(0 < value < 255 for value in mask.get_flattened_data()))
        rounded = eye_mask(size, 24, EyeShape.ROUNDED)
        self.assertEqual(rounded.getpixel((0,159)), 0)
        for shape, radius, arch in ((EyeShape.RECTANGLE,24,18),(EyeShape.TOP_ROUNDED,0,18),(EyeShape.ARCH,0,0)):
            self.assertEqual(eye_mask(size,radius,shape,arch).getextrema(), (255,255))

    def test_grid_is_clipped_to_arch_in_web_and_print(self):
        source = Image.new("RGB", (600,200), "red")
        for options in (WebRenderOptions(layout=LayoutMode.PARALLEL, target_width=600, eye_shape=EyeShape.ARCH),
                        self.holmes(dpi=96, arch_height_percent=50)):
            original = render_web(source,options) if isinstance(options,WebRenderOptions) else render_print(source,options)
            grid = crop_grid(original,source,options)
            diff = ImageChops.difference(original,grid)
            self.assertIsNotNone(diff.convert("RGB").getbbox())
            # Background remains exactly the frame colour everywhere the arch is fully transparent.
            bg = Image.new("RGBA",original.size,options.frame_color)
            original_pixels, grid_pixels, bg_pixels = original.get_flattened_data(), grid.get_flattened_data(), bg.get_flattened_data()
            for a,b,c in zip(original_pixels,grid_pixels,bg_pixels):
                if a == c:
                    self.assertEqual(a,b)

    def test_colour_presets_are_dark_first_then_light(self):
        presets = list(COLOR_PRESETS.items())
        self.assertEqual(presets[0][0], "Nachtgold")
        self.assertEqual(presets[-1], ("Benutzerdefiniert",None))
        self.assertEqual(len(presets)-1,16)
        self.assertIn("Creme",COLOR_PRESETS)
        self.assertNotIn("Elfenbein",COLOR_PRESETS)
        brightness = [sum(int(colours[0][i:i+2],16) for i in (1,3,5))/3 for _,colours in presets[:-1]]
        self.assertTrue(all(v < 80 for v in brightness[:9]))
        self.assertTrue(all(v > 150 for v in brightness[9:]))

    def test_compact_caption_has_leading_only_between_lines(self):
        font = _font("Segoe UI",30)
        _,step,one = _caption_metrics("ÄÖÜ",font,600)
        _,_,two = _caption_metrics("ÄÖÜ\nÄÖÜ",font,600)
        self.assertEqual(two,one+step)
        self.assertGreater(step,one)

    def test_english_new_controls_and_summary(self):
        self.assertEqual(translate("Stereokarte 7 × 3½ Zoll","en"),"Stereo card 7 × 3½ inches")
        for text in ("Creme","Bildkontur","Prozent","Kartenvorlage","Exakte Ränder in mm"):
            self.assertNotEqual(translate(text,"en"),text)
        self.assertEqual(translate("Vorlage angepasst\nBildfenster: 76,20 × 76,20 mm\nBildmitten: 77,80 mm","en"),
                        "Template adjusted\nImage windows: 76.20 × 76.20 mm\nImage centres: 77.80 mm")


if __name__ == "__main__":
    unittest.main()
