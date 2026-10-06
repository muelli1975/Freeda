"""JPEG backgrounds, preserved PNG alpha and antialiased outer edges."""
import unittest
import tempfile
from pathlib import Path
from dataclasses import replace
from PIL import Image
from freeda.models import OutputFormat, LayoutMode, WebRenderOptions, PrintRenderOptions
from freeda.render import render_web, save_render
from freeda.print_render import render_print
from freeda.preview import preview_export_image
from freeda.crop_grid import crop_grid


class CornerTests(unittest.TestCase):
    def test_preview_and_saved_corners_match_output_format(self):
        source = Image.new("RGB", (600,200), "red")
        with tempfile.TemporaryDirectory() as tmp:
            for kind, base, render, bg in (
                ("web",WebRenderOptions(target_width=600,layout=LayoutMode.PARALLEL),render_web,(0,0,0)),
                ("print",PrintRenderOptions(dpi=96),render_print,(255,255,255))):
                for output in OutputFormat:
                    options = replace(base, outer_radius_percent=5,frame_color="#eee5d3",output_format=output)
                    image = render(source,options)
                    self.assertEqual(image.getpixel((0,0))[3],0)
                    self.assertTrue(any(0<v<255 for v in image.getchannel("A").get_flattened_data()))
                    shown = preview_export_image(image,options)
                    target = Path(tmp)/f"{kind}_{output.value}"
                    save_render(image,target,output,background_color="#ffffff" if kind=="print" else "#000000")
                    suffix = ".png" if output == OutputFormat.PNG else ".jpg"
                    with Image.open(target.with_suffix(suffix)) as saved:
                        if output == OutputFormat.PNG:
                            self.assertEqual(saved.mode,"RGBA")
                            self.assertEqual(saved.getpixel((0,0))[3],0)
                            self.assertEqual(shown.getpixel((0,0))[3],0)
                        else:
                            self.assertEqual(saved.mode,"RGB")
                            self.assertEqual(shown.getpixel((0,0)),bg)
                            self.assertTrue(all(abs(a-b)<3 for a,b in zip(saved.getpixel((0,0)),bg)))
                    gridded = crop_grid(image,source,options)
                    self.assertEqual(gridded.getchannel("A").tobytes(),image.getchannel("A").tobytes())

    def test_inner_corners_stay_frame_coloured(self):
        source = Image.new("RGB",(600,200),"red")
        options = WebRenderOptions(target_width=600,inner_radius_percent=10,frame_color="#eee5d3")
        image = render_web(source,options)
        from freeda.geometry import frame_geometry_for_total_width
        f = frame_geometry_for_total_width(600,4).frame_px
        self.assertEqual(image.getpixel((f,f)),(238,229,211,255))


if __name__ == "__main__":
    unittest.main()
