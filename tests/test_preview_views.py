import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event, current_thread
import numpy as np
from PIL import Image, ImageOps
from freeda.inputs import load_image, image_size
from freeda.preview import render_preview
from freeda.preview_worker import PreviewRequest, PreviewWorker
from freeda.models import WebRenderOptions, PrintRenderOptions, PrintMargins, OutputFormat, EyeShape, LayoutMode, Crop
from freeda.anaglyph import make_anaglyph
from freeda.render import split_full_sbs, crop_eye


class PreviewChecks(unittest.TestCase):
    def test_orientation_all_tags_and_formats(self):
        with TemporaryDirectory() as folder:
            image=Image.fromarray(np.arange(24*16*3,dtype=np.uint8).reshape(16,24,3))
            for extension in ('jpg','png','tiff','webp'):
                for orientation in range(1,9):
                    with self.subTest(extension=extension, orientation=orientation):
                        exif=Image.Exif();exif[274]=orientation
                        path=Path(folder)/f'image.{extension}';image.save(path,exif=exif)
                        with Image.open(path) as raw: expected=ImageOps.exif_transpose(raw).convert('RGB')
                        loaded=load_image(path)
                        self.assertEqual(loaded.size,expected.size)
                        self.assertEqual(image_size(path),expected.size)
                        self.assertTrue(np.array_equal(np.asarray(loaded),np.asarray(expected)))

    def test_anaglyph_reference_and_view_switch_keep_crop(self):
        rng=np.random.default_rng(42)
        image=Image.fromarray(rng.integers(0,256,(80,240,3),dtype=np.uint8))
        options=WebRenderOptions(layout=LayoutMode.BOTH, crop=Crop(.1,.1,.8,.8), frame_percent=0)
        left,right=split_full_sbs(image)
        left,right=crop_eye(left,options.crop),crop_eye(right,options.crop)
        expected=Image.fromarray(make_anaglyph(np.asarray(left),np.asarray(right)))
        actual=render_preview(image,PreviewRequest(image,options,*left.size,view='anaglyph'))
        self.assertTrue(np.array_equal(np.asarray(expected),np.asarray(actual)))
        for view in ('parallel','cross'):
            framed_options=replace(options,frame_percent=4)
            self.assertEqual(render_preview(image,PreviewRequest(image,framed_options,400,200,view=view)).size,(400,141))
        self.assertEqual(options.layout,LayoutMode.BOTH)
        self.assertEqual(options.crop,Crop(.1,.1,.8,.8))


    def test_framed_anaglyph_has_no_viewing_symbols_and_keeps_export(self):
        from freeda.render import render_web
        source=Image.new('RGB',(800,240),'white')
        original=np.asarray(source).copy()
        for layout in LayoutMode:
            with self.subTest(layout=layout):
                options=WebRenderOptions(layout=layout, frame_percent=5,
                    frame_color='#67421f', caption='Caption', crop=Crop(.1,0,.8,1),
                    output_format=OutputFormat.PNG)
                before=np.asarray(render_web(source,options))
                image=render_preview(source,PreviewRequest(source,options,800,600,view='anaglyph'))
                no_symbols=render_preview(source,PreviewRequest(source,replace(options,show_symbols=False),
                    800,600,view='anaglyph'))
                self.assertTrue(np.array_equal(np.asarray(image),np.asarray(no_symbols)))
                self.assertEqual(image.getpixel((0,image.height//2)),(103,66,31,255))
                self.assertEqual(image.getpixel((image.width//2,0)),(103,66,31,255))
                self.assertNotEqual(image.getpixel((image.width//2,image.height//2)),(103,66,31,255))
                self.assertTrue(np.array_equal(before,np.asarray(render_web(source,options))))
        self.assertTrue(np.array_equal(original,np.asarray(source)))

    def test_anaglyph_contour_grid_and_outer_transparency(self):
        source=Image.new('RGB',(800,400),'white')
        options=WebRenderOptions(layout=LayoutMode.PARALLEL, frame_percent=5,
            frame_color='#67421f', eye_shape=EyeShape.TOP_ROUNDED,
            inner_radius_percent=20, bottom_radius_percent=0, output_format=OutputFormat.PNG)
        plain=render_preview(source,PreviewRequest(source,options,840,840,view='anaglyph'))
        grid=render_preview(source,PreviewRequest(source,options,840,840,view='anaglyph',grid=True))
        self.assertTrue(np.array_equal(np.asarray(plain)[0],np.asarray(grid)[0]))
        self.assertTrue(np.array_equal(np.asarray(plain)[:,0],np.asarray(grid)[:,0]))
        self.assertFalse(np.array_equal(np.asarray(plain),np.asarray(grid)))
        # Inside the top image corners, the chosen contour leaves visible frame.
        border=round(plain.width*.05/1.1)
        self.assertEqual(plain.getpixel((border+2,border+2)),(103,66,31,255))
        rounded=render_preview(source,PreviewRequest(source,replace(options,outer_radius_percent=3),
            840,840,view='anaglyph'))
        self.assertEqual(rounded.getpixel((0,0))[3],0)

    def test_print_anaglyph_uses_selected_margins_without_symbols(self):
        from freeda.print_render import render_print
        source=Image.new('RGB',(800,400),'white')
        for layout in (LayoutMode.PARALLEL,LayoutMode.BOTH,LayoutMode.LRL):
            with self.subTest(layout=layout):
                options=PrintRenderOptions(layout=layout, frame_color='#67421f',
                    margins=PrintMargins(side_mm=8,top_mm=3,centre_mm=2,bottom_mm=12,row_gap_mm=4),
                    output_format=OutputFormat.PNG)
                before=np.asarray(render_print(source,options))
                image=render_preview(source,PreviewRequest(source,options,640,640,view='anaglyph'))
                no_symbols=render_preview(source,PreviewRequest(source,replace(options,show_symbols=False),
                    640,640,view='anaglyph'))
                self.assertTrue(np.array_equal(np.asarray(image),np.asarray(no_symbols)))
                self.assertEqual(image.getpixel((0,image.height//2)),(103,66,31,255))
                self.assertEqual(image.getpixel((image.width//2,0)),(103,66,31,255))
                self.assertEqual(image.getpixel((image.width//2,image.height-1)),(103,66,31,255))
                self.assertNotEqual(image.getpixel((image.width//2,image.height//2)),(103,66,31,255))
                self.assertTrue(np.array_equal(before,np.asarray(render_print(source,options))))

    def test_latest_request_worker_runs_off_caller_thread(self):
        received=[];done=Event();thread=current_thread()
        def completed(identifier,image,error):
            received.append((identifier,image,error,current_thread()))
            if identifier == 11: done.set()
        worker=PreviewWorker(completed)
        try:
            image=Image.new('RGB',(60,20),'red')
            for index in range(12):worker.request(index,PreviewRequest(image,WebRenderOptions(),120,100))
            self.assertTrue(done.wait(5))
            self.assertEqual(received[-1][0],11)
            self.assertIsNone(received[-1][2])
            self.assertIsNot(received[-1][3],thread)
        finally:worker.close();worker.thread.join(5)
        self.assertFalse(worker.thread.is_alive())
