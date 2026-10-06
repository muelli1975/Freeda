import unittest
from PIL import Image
from freeda.models import WebRenderOptions, PrintRenderOptions, LayoutMode
from freeda.render import render_web
from freeda.print_render import render_print
from freeda.crop_grid import crop_grid
from freeda.geometry import frame_geometry_for_total_width

class CropGridTests(unittest.TestCase):
    def test_grid_is_confined_and_does_not_modify_export(self):
        source=Image.new("RGB",(600,200),"red")
        for layout in LayoutMode:
            for options in (WebRenderOptions(layout=layout,target_long_edge=1200,caption="Caption"),
                            PrintRenderOptions(layout=layout,dpi=100,caption="Caption")):
                rendered=render_web(source,options) if isinstance(options,WebRenderOptions) else render_print(source,options)
                original=rendered.tobytes()
                gridded=crop_grid(rendered,source,options)
                self.assertEqual(rendered.tobytes(),original)
                self.assertNotEqual(gridded.tobytes(),original)
                self.assertEqual(rendered.getpixel((0,0)),gridded.getpixel((0,0)))
                self.assertEqual(rendered.getpixel((rendered.width//2,rendered.height-1)),gridded.getpixel((rendered.width//2,rendered.height-1)))

    def test_vertical_thirds_repeat_for_every_eye(self):
        source=Image.new("RGB",(600,200),"red")
        options=WebRenderOptions(layout=LayoutMode.LRL,target_long_edge=1200)
        rendered=render_web(source,options)
        grid=crop_grid(rendered,source,options)
        geometry=frame_geometry_for_total_width(1200,options.frame_percent,3)
        for index in range(3):
            x=geometry.frame_px+index*(geometry.eye_width+geometry.frame_px)
            for fraction in (1/3,2/3):
                self.assertNotEqual(grid.getpixel((round(x+geometry.eye_width*fraction),geometry.frame_px+10)),rendered.getpixel((round(x+geometry.eye_width*fraction),geometry.frame_px+10)))
