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
from freeda.models import WebRenderOptions, LayoutMode, Crop
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
        options=WebRenderOptions(layout=LayoutMode.BOTH, crop=Crop(.1,.1,.8,.8))
        left,right=split_full_sbs(image)
        left,right=crop_eye(left,options.crop),crop_eye(right,options.crop)
        expected=Image.fromarray(make_anaglyph(np.asarray(left),np.asarray(right)))
        actual=render_preview(image,PreviewRequest(image,options,*left.size,view='anaglyph'))
        self.assertTrue(np.array_equal(np.asarray(expected),np.asarray(actual)))
        for view in ('parallel','cross'):
            self.assertEqual(render_preview(image,PreviewRequest(image,options,400,200,view=view)).size,(400,141))
        self.assertEqual(options.layout,LayoutMode.BOTH)
        self.assertEqual(options.crop,Crop(.1,.1,.8,.8))

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
