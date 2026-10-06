"""Web export dimensions include the complete card, with matching crop overlays."""
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from PIL import Image, ImageChops
from freeda.models import WebRenderOptions, LayoutMode, CaptionMode, OutputFormat, EyeShape
from freeda.render import render_web, web_geometry
from freeda.crop_grid import crop_grid


class LongEdgeTests(unittest.TestCase):
    def test_all_layouts_and_orientations(self):
        for size in ((600, 200), (400, 800), (400, 200)):
            source = Image.new('RGB', size, '#336699')
            for layout in LayoutMode:
                for edge in (511, 512):
                    with self.subTest(size=size, layout=layout, edge=edge):
                        options = WebRenderOptions(layout=layout, target_long_edge=edge,
                            caption='A caption beneath each image')
                        image = render_web(source, options)
                        self.assertEqual(max(image.size), edge)
                        self.assertEqual(source.size, size)
                        if size == (400, 800):
                            self.assertEqual(image.height, edge)

    def test_logo_is_included_in_long_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'logo.png'
            Image.new('RGBA', (100, 100), 'gold').save(path)
            for layout in LayoutMode:
                options = WebRenderOptions(layout=layout, target_long_edge=513,
                    caption_mode=CaptionMode.LOGO, logo_path=path, logo_height_percent=20)
                image = render_web(Image.new('RGB', (400, 800), 'red'), options)
                self.assertEqual(image.height, 513)

    def test_original_retains_eye_resolution(self):
        source = Image.new('RGB', (600, 200), 'red')
        options = WebRenderOptions(target_long_edge=None, frame_percent=0, show_symbols=False)
        self.assertEqual(render_web(source, options).size, (600, 400))
        self.assertEqual(render_web(source, replace(options, layout=LayoutMode.LRL)).size, (900, 200))

    def test_portrait_grid_stays_in_image_windows(self):
        source = Image.new('RGB', (400, 800), '#336699')
        options = WebRenderOptions(target_long_edge=511, caption='Caption',
            eye_shape=EyeShape.RECTANGLE, outer_radius_percent=3, output_format=OutputFormat.PNG)
        image = render_web(source, options)
        overlay = crop_grid(image, source, options)
        self.assertEqual(overlay.size, image.size)
        self.assertIsNone(ImageChops.difference(image.getchannel('A'), overlay.getchannel('A')).getbbox())
        geom = web_geometry((200, 800), options)
        scale = image.height / geom.native_size[1]
        for x0, y0, x1, y1 in geom.eye_boxes:
            x, y = round((x0 + (x1-x0)/3)*scale), round((y0+(y1-y0)/2)*scale)
            self.assertNotEqual(image.getpixel((x,y)), overlay.getpixel((x,y)))
            footer_y = round((y1+geom.row.band_height/2)*scale)
            self.assertEqual(image.getpixel((x,footer_y)), overlay.getpixel((x,footer_y)))

    def test_invalid_custom_sizes_are_rejected(self):
        for edge in (0, 15, True, 2048.5, '2048'):
            with self.subTest(edge=edge), self.assertRaises(ValueError):
                render_web(Image.new('RGB', (600, 200)), WebRenderOptions(target_long_edge=edge))
