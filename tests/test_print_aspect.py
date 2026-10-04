import unittest
from dataclasses import replace
from PIL import Image, ImageChops
from freeda.models import PrintRenderOptions, LayoutMode, Crop
from freeda.print_render import print_content, print_eye_aspect, render_print
from freeda.geometry import frame_geometry_for_total_width, print_canvas_px, mm_to_px
from freeda.crop_grid import crop_grid
from freeda.render import render_web


class PrintAspectTests(unittest.TestCase):
    def setUp(self):
        self.source = Image.new('RGB', (800, 300), 'red')
        self.source.paste('blue', (400, 0, 800, 300))

    def test_ratio_independent_of_paper_dpi_layout_and_caption(self):
        for layout in LayoutMode:
            for dpi, paper in ((96, (150, 100)), (240, (100, 150))):
                options = PrintRenderOptions(layout=layout, dpi=dpi, width_mm=paper[0],
                    height_mm=paper[1], eye_aspect=1, caption='A caption')
                content, web, offset = print_content(self.source, options)
                geom = frame_geometry_for_total_width(content.width, options.frame_percent,
                    3 if layout == LayoutMode.LRL else 2)
                self.assertEqual(print_eye_aspect(options), 1)
                image = render_print(self.source, options)
                self.assertEqual(image.size, print_canvas_px(*paper, dpi))
                self.assertGreaterEqual(min(offset), 0)
                self.assertEqual(image.crop((offset[0], offset[1], offset[0]+content.width,
                    offset[1]+content.height)).tobytes(), render_web(self.source, web).tobytes())
                # The eye is square, even when the paper is portrait or captions grow.
                eye = image.crop((offset[0]+geom.frame_px, offset[1]+geom.frame_px,
                    offset[0]+geom.frame_px+geom.eye_width, offset[1]+geom.frame_px+geom.eye_width))
                expected = (0, 0, 255, 255) if layout == LayoutMode.CROSS else (255, 0, 0, 255)
                self.assertEqual(eye.getpixel((eye.width//2, eye.height-1)), expected)

    def test_original_keeps_source_or_saved_crop_ratio(self):
        options = PrintRenderOptions(fit_to_paper=False)
        self.assertEqual(print_eye_aspect(options, (400, 300)), 4/3)
        cropped = replace(options, crop=Crop(width=.5, height=.5))
        self.assertEqual(print_eye_aspect(cropped, (400, 300)), 4/3)
        content, web, _ = print_content(self.source, options)
        self.assertIsNone(web.eye_aspect)
        self.assertEqual(content.tobytes(), render_web(self.source, web).tobytes())

    def test_white_paper_bleed_and_grid_only_touch_graphic(self):
        options = PrintRenderOptions(dpi=96, bleed_mm=2.5, eye_aspect=2/3)
        image = render_print(self.source, options)
        content, _, offset = print_content(self.source, options)
        self.assertEqual(image.size, print_canvas_px(options.width_mm, options.height_mm, 96, 2.5))
        self.assertEqual(image.getpixel((0, 0)), (255,255,255,255))
        grid = crop_grid(image, self.source, options)
        self.assertNotEqual(grid.tobytes(), image.tobytes())
        box = ImageChops.difference(grid.convert('RGB'), image.convert('RGB')).getbbox()
        bleed = mm_to_px(options.bleed_mm, options.dpi)
        self.assertGreaterEqual(box[0], bleed + offset[0])
        self.assertGreaterEqual(box[1], bleed + offset[1])
        self.assertLessEqual(box[2], bleed + offset[0] + content.width)
        self.assertLessEqual(box[3], bleed + offset[1] + content.height)
