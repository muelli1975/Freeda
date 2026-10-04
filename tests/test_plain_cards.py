import unittest
from dataclasses import replace
from PIL import Image
from freeda.geometry import frame_geometry_for_total_width, print_canvas_px
from freeda.models import LayoutMode, WebRenderOptions, PrintRenderOptions
from freeda.render import render_web
from freeda.print_render import render_print


class PlainCardTests(unittest.TestCase):
    def setUp(self):
        self.source=Image.new('RGB',(600,200),'red')
        self.source.paste('blue',(300,0,600,200))

    def test_zero_frame_has_no_strip_for_every_layout_even_and_odd_widths(self):
        for layout in LayoutMode:
            for width in (512,513,514):
                options=WebRenderOptions(layout=layout,target_width=width,frame_percent=0)
                result=render_web(self.source,options)
                self.assertEqual(result.width,width)
                self.assertEqual(frame_geometry_for_total_width(width,0,3 if layout==LayoutMode.LRL else 2).frame_px,0)
                self.assertEqual({colour for _,colour in result.getcolors(4)},{(255,0,0,255),(0,0,255,255)})
                self.assertEqual(result.tobytes(),render_web(self.source,replace(options,show_symbols=False)).tobytes())

    def test_plain_print_fills_paper_without_symbols_or_caption_band(self):
        for layout in LayoutMode:
            for dpi in (96,97):
                options=PrintRenderOptions(layout=layout,dpi=dpi,width_mm=150,height_mm=100,frame_percent=0)
                result=render_print(self.source,options)
                self.assertEqual(result.size,print_canvas_px(150,100,dpi))
                self.assertEqual({colour for _,colour in result.getcolors(4)},{(255,0,0,255),(0,0,255,255)})
                self.assertEqual(result.tobytes(),render_print(self.source,replace(options,show_symbols=False)).tobytes())

    def test_symbols_can_be_hidden_without_changing_geometry_or_captions(self):
        for layout in LayoutMode:
            for options, render in ((WebRenderOptions(layout=layout,target_width=1200,caption='Caption'),render_web),
                (PrintRenderOptions(layout=layout,dpi=150,caption='Caption'),render_print)):
                shown=render(self.source,options)
                hidden=render(self.source,replace(options,show_symbols=False))
                self.assertEqual(shown.size,hidden.size)
                self.assertNotEqual(shown.tobytes(),hidden.tobytes())
                frame=frame_geometry_for_total_width(shown.width,options.frame_percent,3 if layout==LayoutMode.LRL else 2).frame_px
                self.assertEqual({colour for _,colour in hidden.crop((0,0,hidden.width,frame)).getcolors(4)},{(17,17,17,255)})
                # Symbols occupy only the upper frame, so captions are unchanged.
                if layout!=LayoutMode.BOTH:
                    self.assertEqual(shown.crop((0,shown.height//2,shown.width,shown.height)).tobytes(),
                        hidden.crop((0,hidden.height//2,hidden.width,hidden.height)).tobytes())
