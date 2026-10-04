from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from freeda.models import LayoutMode, OutputFormat, WebRenderOptions
from freeda.render import render_web, save_render


class RenderTests(unittest.TestCase):
    def source(self):
        left = Image.new("RGB", (300, 200), "#ff0000")
        right = Image.new("RGB", (300, 200), "#00ff00")
        source = Image.new("RGB", (600, 200))
        source.paste(left, (0, 0))
        source.paste(right, (300, 0))
        return source

    def test_parallel_exact_width(self):
        result = render_web(self.source(), WebRenderOptions(
            layout=LayoutMode.PARALLEL, target_width=1280, frame_percent=1.5
        ))
        self.assertEqual(result.width, 1280)

    def test_lrl_order_and_exact_width(self):
        for width in (1280, 1920, 2048):
            image = render_web(self.source(), WebRenderOptions(layout=LayoutMode.LRL, target_width=width))
            self.assertEqual(image.width, width)
            colors = [image.getpixel((round(width * x), image.height // 2))[:3] for x in (1/6, 1/2, 5/6)]
            self.assertEqual(colors, [(255, 0, 0), (0, 255, 0), (255, 0, 0)])

    def test_both_is_taller_than_single(self):
        single = render_web(self.source(), WebRenderOptions(
            layout=LayoutMode.PARALLEL, target_width=1280
        ))
        both = render_web(self.source(), WebRenderOptions(
            layout=LayoutMode.BOTH, target_width=1280
        ))
        self.assertGreater(both.height, single.height)

    def test_png_keeps_alpha_and_jpeg_is_444(self):
        image = render_web(self.source(), WebRenderOptions(
            target_width=1280, outer_radius_percent=3.0, output_format=OutputFormat.PNG
        ))
        self.assertEqual(image.mode, "RGBA")
        self.assertEqual(image.getpixel((0, 0))[3], 0)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "test"
            save_render(image, target, OutputFormat.JPEG)
            self.assertTrue(target.with_suffix(".jpg").is_file())


if __name__ == "__main__":
    unittest.main()
