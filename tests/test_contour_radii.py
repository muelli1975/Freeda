"""Independent image radii, shared render/grid masks and legacy preset migration."""
import unittest
from dataclasses import replace
from PIL import Image, ImageChops, ImageOps
from freeda.eye_shapes import eye_mask
from freeda.models import EyeShape, LayoutMode, WebRenderOptions, PrintRenderOptions
from freeda.presets import ROUNDED_RECTANGLE, migrate_contour
from freeda.render import render_web, web_geometry
from freeda.print_render import render_print
from freeda.print_layout import print_layout
from freeda.crop_grid import crop_grid


class ContourRadiiTests(unittest.TestCase):
    def test_top_and_bottom_are_independent_and_symmetric(self):
        for size in ((200, 160), (193, 127)):
            for top, bottom in ((0, 0), (20, 0), (0, 35), (20, 35), (10000, 10000)):
                with self.subTest(size=size, top=top, bottom=bottom):
                    mask = eye_mask(size, top, bottom_radius=bottom)
                    self.assertEqual(mask.getpixel((0, 0)), 0 if top else 255)
                    self.assertEqual(mask.getpixel((0, size[1]-1)), 0 if bottom else 255)
                    self.assertIsNone(ImageChops.difference(mask, ImageOps.mirror(mask)).getbbox())
                    self.assertEqual(mask.crop((0, size[1]//2, size[0], size[1]//2+1)).getextrema(), (255,255))

    def test_legacy_masks_are_pixel_identical(self):
        size = (193, 127)
        for shape, top, bottom in ((EyeShape.RECTANGLE, 0, 0), (EyeShape.ROUNDED, 23, 23),
                                   (EyeShape.TOP_ROUNDED, 23, 0)):
            legacy = eye_mask(size, 23, shape)
            current = eye_mask(size, top, bottom_radius=bottom)
            self.assertIsNone(ImageChops.difference(legacy, current).getbbox(), shape)

    def test_old_presets_are_migrated_without_modifying_the_original(self):
        for shape, radius, expected in (('Rechteckig', 'nan', ('0','0')),
                ('Alle Ecken gerundet','7',('7','7')), ('Nur obere Ecken gerundet','7',('7','0')),
                (None,'7',('7','7'))):
            values = {'inner_radius_var':radius, 'outer_radius_var':'3'}
            if shape: values['eye_shape_var'] = shape
            before = dict(values)
            migrated = migrate_contour(values)
            self.assertEqual(values, before)
            self.assertEqual(migrated['eye_shape_var'], ROUNDED_RECTANGLE)
            self.assertEqual((migrated['inner_radius_var'],migrated['bottom_radius_var']), expected)
            self.assertEqual(migrated['outer_radius_var'], '3')
        new = {'eye_shape_var':ROUNDED_RECTANGLE,'inner_radius_var':'2','bottom_radius_var':'8'}
        self.assertEqual(migrate_contour(new),new)

    def test_web_and_print_keep_only_the_requested_corners(self):
        source = Image.new('RGB', (600, 200), 'red')
        for top, bottom in ((0,15),(15,0),(10,25)):
            options = WebRenderOptions(layout=LayoutMode.BOTH, target_long_edge=600,
                inner_radius_percent=top,bottom_radius_percent=bottom)
            image = render_web(source,options)
            geometry = web_geometry((300,200),options)
            for x0,y0,x1,y1 in geometry.eye_boxes:
                self.assertEqual(image.getpixel((x0,y0)), (17,17,17,255) if top else (255,0,0,255))
                self.assertEqual(image.getpixel((x0,y1-1)), (17,17,17,255) if bottom else (255,0,0,255))
            options = PrintRenderOptions(dpi=96,inner_radius_percent=top,bottom_radius_percent=bottom)
            image = render_print(source,options)
            for x0,y0,x1,y1 in print_layout(options).eye_boxes(options.dpi):
                self.assertEqual(image.getpixel((x0,y0)), (17,17,17,255) if top else (255,0,0,255))
                self.assertEqual(image.getpixel((x0,y1-1)), (17,17,17,255) if bottom else (255,0,0,255))

    def test_grid_does_not_draw_outside_bottom_rounding(self):
        source = Image.new('RGB',(600,200),'red')
        for options in (WebRenderOptions(layout=LayoutMode.PARALLEL,target_long_edge=600,
                           inner_radius_percent=0,bottom_radius_percent=45),
                        PrintRenderOptions(dpi=96,inner_radius_percent=0,bottom_radius_percent=45)):
            render = render_web if isinstance(options,WebRenderOptions) else render_print
            original = render(source,options)
            grid = crop_grid(original,source,options)
            self.assertIsNotNone(ImageChops.difference(original,grid).convert('RGB').getbbox())
            for a,b in zip(original.get_flattened_data(),grid.get_flattened_data()):
                if a == (17,17,17,255): self.assertEqual(a,b)

    def test_arch_ignores_inactive_corner_radii(self):
        base = eye_mask((200,160),0,EyeShape.ARCH,18)
        changed = eye_mask((200,160),80,EyeShape.ARCH,18,bottom_radius=70)
        self.assertIsNone(ImageChops.difference(base,changed).getbbox())
