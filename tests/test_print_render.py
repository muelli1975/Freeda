from __future__ import annotations

import unittest

from PIL import Image

from freeda.geometry import mm_to_px, print_canvas_px
from freeda.models import CuttingGuide, LayoutMode, PrintRenderOptions
from freeda.print_render import crop_for_aspect, render_print


class PrintRenderTests(unittest.TestCase):
    def source(self):
        left = Image.new("RGB", (600, 400), "#ff0000")
        right = Image.new("RGB", (600, 400), "#00ff00")
        source = Image.new("RGB", (1200, 400))
        source.paste(left, (0, 0))
        source.paste(right, (600, 0))
        return source

    def test_print_canvas_includes_bleed(self):
        options = PrintRenderOptions(
            layout=LayoutMode.PARALLEL,
            width_mm=150,
            height_mm=100,
            dpi=300,
            bleed_mm=3,
        )
        result = render_print(self.source(), options)
        self.assertEqual(result.size, print_canvas_px(150, 100, 300, 3))

    def test_cutting_line_keeps_canvas_size(self):
        base = PrintRenderOptions(width_mm=130, height_mm=90, dpi=300, bleed_mm=3)
        plain = render_print(self.source(), base)
        lined = render_print(
            self.source(),
            PrintRenderOptions(
                width_mm=130,
                height_mm=90,
                dpi=300,
                bleed_mm=3,
                cutting_guide=CuttingGuide.LINE,
            ),
        )
        self.assertEqual(plain.size, lined.size)

    def test_cutting_line_is_gray_for_light_and_dark_frames(self):
        for frame in ("#ffffff", "#111111"):
            options = PrintRenderOptions(width_mm=130, height_mm=90, dpi=150,
                bleed_mm=3, frame_color=frame, cutting_guide=CuttingGuide.LINE)
            image = render_print(self.source(), options)
            bleed = mm_to_px(3, 150)
            self.assertEqual(image.getpixel((bleed, bleed))[:3], (128, 128, 128))

    def test_lrl_print_order(self):
        options = PrintRenderOptions(layout=LayoutMode.LRL, width_mm=150, height_mm=100, dpi=150, bleed_mm=0)
        image = render_print(self.source(), options)
        self.assertEqual(image.size, print_canvas_px(150, 100, 150, 0))
        colors = [image.getpixel((round(image.width*x), image.height//2))[:3] for x in (1/6, 1/2, 5/6)]
        self.assertEqual(colors, [(255, 0, 0), (0, 255, 0), (255, 0, 0)])

    def test_crop_for_aspect_is_linkable_and_clamped(self):
        crop = crop_for_aspect((1920, 1280), 1.2, zoom=2.0, position_x=1.0, position_y=0.0)
        self.assertGreater(crop.width, 0)
        self.assertGreater(crop.height, 0)
        self.assertLessEqual(crop.x + crop.width, 1.0)
        self.assertLessEqual(crop.y + crop.height, 1.0)

    def test_combined_print_uses_exact_trim_plus_bleed(self):
        options = PrintRenderOptions(
            layout=LayoutMode.BOTH,
            width_mm=177.8,
            height_mm=88.9,
            dpi=300,
            bleed_mm=0,
        )
        result = render_print(self.source(), options)
        self.assertEqual(result.width, mm_to_px(177.8, 300))
        self.assertEqual(result.height, mm_to_px(88.9, 300))


if __name__ == "__main__":
    unittest.main()
