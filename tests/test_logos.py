import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from PIL import Image, ImageDraw, ImageChops
from freeda.models import CaptionMode, LayoutMode, PrintRenderOptions, PrintMargins, WebRenderOptions
from freeda.logos import import_logo, resolve_logo, load_logo, logo_layout
from freeda.render import render_web
from freeda.print_layout import print_layout
from freeda.print_render import render_print
from freeda.crop_grid import crop_grid
from freeda.geometry import frame_geometry_for_total_width


class LogoTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.logo = self.root / "mark.png"
        mark = Image.new("RGBA",(120,60),(0,0,0,0))
        ImageDraw.Draw(mark).rectangle((20,10,100,50),fill=(255,0,255,255))
        mark.save(self.logo)
        self.source = Image.new("RGB",(600,200),"red")

    def test_import_is_relative_preserves_bytes_and_survives_moving(self):
        original = self.logo.read_bytes()
        portable = self.root / "program"
        relative = import_logo(self.logo,portable)
        self.assertFalse(Path(relative).is_absolute())
        self.assertEqual(relative,import_logo(self.logo,portable))
        self.assertEqual(resolve_logo(portable,relative).read_bytes(),original)
        self.assertEqual(hashlib.sha256(self.logo.read_bytes()).digest(),hashlib.sha256(original).digest())
        self.logo.unlink()
        moved = self.root / "moved"
        shutil.move(str(portable),str(moved))
        self.assertEqual(load_logo(resolve_logo(moved,relative)).size,(120,60))

    def test_invalid_empty_and_missing_images_are_explained(self):
        bad = self.root / "bad.png"
        bad.write_text("not an image")
        for path in (None,bad,self.root / "missing.png"):
            with self.assertRaises(ValueError):
                load_logo(path)
        blank = self.root / "blank.png"
        Image.new("RGBA",(10,10)).save(blank)
        with self.assertRaisesRegex(ValueError,"sichtbaren"):
            load_logo(blank)
        for relative in (str(self.logo.resolve()),"../mark.png","logos/../../mark.png"):
            with self.assertRaises(ValueError):
                resolve_logo(self.root,relative)

    def test_width_is_bounded_without_distorting_tall_or_wide_logos(self):
        for size in ((10,100),(100,10),(2000,10)):
            layout = logo_layout(size,60,6)
            self.assertLessEqual(layout.width,54)
            self.assertLessEqual(layout.height,3.6+1e-9)
            self.assertAlmostEqual(layout.width/layout.height,size[0]/size[1])
        for value in (0,-1,float("nan"),float("inf")):
            with self.assertRaises(ValueError):
                logo_layout((10,10),60,height=value)

    def test_web_logo_replaces_caption_and_repeats_identically(self):
        for mode in LayoutMode:
            options = WebRenderOptions(layout=mode,target_long_edge=1200,caption_mode=CaptionMode.LOGO,
                        logo_path=self.logo,caption="This text must not affect the result",frame_color="#123456")
            rendered = render_web(self.source,options)
            self.assertEqual(rendered.width,1200)
            self.assertEqual(rendered.tobytes(),render_web(self.source,replace(options,caption="")).tobytes())
            count = 3 if mode == LayoutMode.LRL else 2
            g = frame_geometry_for_total_width(1200,options.frame_percent,count)
            eye_h = round(g.eye_width * 200/300)
            expected_rows = 2 if mode == LayoutMode.BOTH else 1
            footer = logo_layout((120,60),g.eye_width,options.logo_height_percent)
            band = round(footer.height)+max(1,round(footer.gap_top))+max(1,round(footer.gap_bottom))
            for row in range(expected_rows):
                y = g.frame_px + row*(eye_h+band+g.frame_px) + eye_h
                crops = [rendered.crop((g.frame_px+i*(g.eye_width+g.frame_px),y,
                              g.frame_px+i*(g.eye_width+g.frame_px)+g.eye_width,y+band)) for i in range(count)]
                for image in crops[1:]:
                    self.assertEqual(crops[0].tobytes(),image.tobytes())
                self.assertIn((255,0,255,255),crops[0].get_flattened_data())
                self.assertEqual(crops[0].getpixel((0,0)),(18,52,86,255))

    def test_exact_print_logo_height_and_crop_are_dpi_independent(self):
        base = PrintRenderOptions(width_mm=177.8,height_mm=88.9,margins=PrintMargins(11.9,3.2,1.6,9.5),
                caption_mode=CaptionMode.LOGO,logo_path=self.logo,logo_height_mm=4,
                caption_gap_top_mm=.8,caption_gap_bottom_mm=1.2)
        for dpi in (72,96,300,600):
            options = replace(base,dpi=dpi)
            card = print_layout(options)
            self.assertAlmostEqual(card.eye_width_mm,76.2)
            self.assertAlmostEqual(card.eye_height_mm,76.2)
            self.assertEqual((card.logo_width_mm,card.logo_height_mm),(8,4))
            self.assertEqual(card.caption_lines,())
            result = render_print(self.source,options)
            self.assertIn((255,0,255,255),result.get_flattened_data())
        with self.assertRaisesRegex(ValueError,"Logo passt"):
            print_layout(replace(base,logo_height_mm=20))

    def test_grid_never_crosses_logo_or_changes_export(self):
        for options,render in ((WebRenderOptions(layout=LayoutMode.BOTH,target_long_edge=600,
                   caption_mode=CaptionMode.LOGO,logo_path=self.logo),render_web),
                   (PrintRenderOptions(dpi=96,caption_mode=CaptionMode.LOGO,logo_path=self.logo),render_print)):
            image = render(self.source,options)
            original = image.tobytes()
            grid = crop_grid(image,self.source,options)
            self.assertEqual(image.tobytes(),original)
            self.assertIsNotNone(ImageChops.difference(grid,image).convert("RGB").getbbox())
            for a,b in zip(image.get_flattened_data(),grid.get_flattened_data()):
                if a == (255,0,255,255):
                    self.assertEqual(a,b)

    def test_logo_exif_orientation_is_applied_and_cache_refreshes(self):
        path = self.root/"rotate.jpg"
        exif=Image.Exif();exif[274]=6
        Image.new("RGB",(20,40),"red").save(path,exif=exif)
        self.assertEqual(load_logo(path).size,(40,20))
        Image.new("RGBA",(30,10),"lime").save(self.logo)
        self.assertEqual(load_logo(self.logo).size,(30,10))


if __name__ == "__main__":
    unittest.main()
