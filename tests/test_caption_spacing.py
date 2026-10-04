import unittest
from PIL import Image
from freeda.models import LayoutMode, WebRenderOptions, PrintRenderOptions
from freeda.geometry import frame_geometry_for_total_width, mm_to_px
from freeda.render import render_web, _row
from freeda.print_render import render_print

class CaptionSpacingTests(unittest.TestCase):
    def test_web_final_caption_is_one_frame_shorter(self):
        source=Image.new("RGB",(600,200),"red")
        eye=source.crop((0,0,300,200))
        for layout in LayoutMode:
            count=3 if layout==LayoutMode.LRL else 2
            options=WebRenderOptions(layout=layout,target_width=2048,caption="Untertitel")
            geom=frame_geometry_for_total_width(2048,options.frame_percent,count)
            row=_row(eye,eye,total_width=2048,frame_percent=options.frame_percent,
                frame_color=options.frame_color,accent_color=options.accent_color,symbol="II",
                caption=options.caption,font_family=options.font_family,
                caption_size_percent=options.caption_size_percent,inner_radius_percent=0,eye_count=count)
            expected=row.height-geom.frame_px
            if layout==LayoutMode.BOTH:
                expected=2*row.height-2*geom.frame_px
            self.assertEqual(render_web(source,options).height,expected)

    def test_print_keeps_format_and_equal_image_heights(self):
        source=Image.new("RGB",(600,200),"red")
        options=PrintRenderOptions(layout=LayoutMode.BOTH,width_mm=150,height_mm=100,
            dpi=150,bleed_mm=0,caption="Untertitel")
        image=render_print(source,options)
        width,height=mm_to_px(150,150),mm_to_px(100,150)
        self.assertEqual(image.size,(width,height))
        frame=frame_geometry_for_total_width(width,options.frame_percent).frame_px
        runs=[]
        current=0
        for y in range(height):
            if image.getpixel((frame+5,y))[:3]==(255,0,0):
                current+=1
            elif current:
                runs.append(current)
                current=0
        if current:
            runs.append(current)
        self.assertEqual(len(runs),2)
        self.assertLessEqual(abs(runs[0]-runs[1]),1)
