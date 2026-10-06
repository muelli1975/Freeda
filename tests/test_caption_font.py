import unittest
from dataclasses import replace
from PIL import Image
from freeda.models import LayoutMode, PrintRenderOptions, WebRenderOptions
from freeda.geometry import frame_geometry_for_total_width, mm_to_px
from freeda.print_render import render_print
from freeda.render import render_web
from freeda.fonts import available_fonts


class CaptionFontTests(unittest.TestCase):
    def test_changing_caption_font_preserves_symbols_and_changes_captions(self):
        source=Image.new('RGB',(800,300),'red')
        fonts=available_fonts()
        if len(fonts)<2:
            self.skipTest('Two fonts required')
        alternate=next((name for name in fonts if 'mono' in name.lower()), fonts[-1])
        for layout in (LayoutMode.PARALLEL,LayoutMode.LRL):
            for options,render in ((WebRenderOptions(layout=layout,target_long_edge=1400,caption='Caption Abc 123'),render_web),
                (PrintRenderOptions(layout=layout,dpi=150,caption='Caption Abc 123'),render_print)):
                first=render(source,replace(options,font_family=fonts[0]))
                second=render(source,replace(options,font_family=alternate))
                frame=frame_geometry_for_total_width(first.width,options.frame_percent,3 if layout==LayoutMode.LRL else 2).frame_px
                self.assertEqual(first.crop((0,0,first.width,frame)).tobytes(),
                    second.crop((0,0,second.width,frame)).tobytes())
                self.assertNotEqual(first.tobytes(),second.tobytes())

    def test_print_and_bleed_fill_frame_colour_for_all_layouts(self):
        source=Image.new('RGB',(800,300),'red')
        for layout in LayoutMode:
            options=PrintRenderOptions(layout=layout,dpi=96,bleed_mm=2.5,frame_color='#225533')
            result=render_print(source,options)
            bleed=mm_to_px(options.bleed_mm,options.dpi)
            for position in ((0,0),(result.width-1,result.height-1),(bleed,bleed)):
                self.assertEqual(result.getpixel(position),(34,85,51,255))
