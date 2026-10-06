import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from freeda.metadata import copy_metadata, find_exiftool_path
from freeda.models import OutputFormat, PrintRenderOptions, WebRenderOptions
from freeda.render import render_web, save_render
from freeda.print_render import render_print
from freeda.batch import discover_files, render_web_batch


class MetadataFailureTests(unittest.TestCase):
    def test_missing_tool_keeps_successfully_exported_image_and_warns(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/'source.png'
            Image.new('RGB',(600,200),'red').save(source)
            original=source.read_bytes()
            warnings=[]
            with patch('freeda.metadata.find_exiftool_path',return_value=None):
                written=render_web_batch(discover_files([source]),root/'output',WebRenderOptions(),metadata_warnings=warnings)
            self.assertEqual(len(written),1)
            with Image.open(written[0]) as result:
                self.assertEqual(result.width,2048)
            self.assertEqual(warnings,['source.png: ExifTool nicht gefunden.'])
            self.assertEqual(source.read_bytes(),original)

    def test_timeout_and_process_error_are_nonfatal(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.jpg'
            target=Path(folder)/'target.jpg'
            for path in (source,target):
                Image.new('RGB',(20,10)).save(path)
            original=target.read_bytes()
            for failure in (subprocess.TimeoutExpired('exiftool',120),OSError('missing runtime')):
                with (patch('freeda.metadata.find_exiftool_path',return_value=Path('exiftool')),
                    patch('freeda.metadata.subprocess.run',side_effect=failure)):
                    self.assertFalse(copy_metadata(source,target,(20,10)).success)
                self.assertEqual(target.read_bytes(),original)

    def test_original_file_cannot_be_metadata_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.jpg'
            Image.new('RGB',(20,10)).save(source)
            original=source.read_bytes()
            self.assertFalse(copy_metadata(source,source,(20,10)).success)
            self.assertEqual(source.read_bytes(),original)


class RealMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool=find_exiftool_path()
        if cls.tool is None:
            raise unittest.SkipTest('Run scripts/prepare_exiftool.py for real integration tests')

    def tool_run(self,*arguments):
        # Windows ExifTool's launcher does not preserve non-ASCII tag values in argv.
        with tempfile.TemporaryDirectory() as folder:
            argfile=Path(folder)/'arguments.txt'
            argfile.write_text('\n'.join(map(str,arguments))+'\n',encoding='utf-8')
            result=subprocess.run([str(self.tool),'-charset','filename=UTF8','-@',str(argfile)],capture_output=True,text=True,
                encoding='utf-8',errors='replace',timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(result.returncode,0,result.stderr)
        return result.stdout

    def read(self,path):
        return json.loads(self.tool_run('-j','-G1','-n',path))[0]

    def source(self,root):
        path=root/'Quelle mit Umlaut ä 測試.jpg'
        Image.new('RGB',(600,200),'red').save(path)
        thumb=root/'thumb.jpg'
        Image.new('RGB',(60,20),'blue').save(thumb)
        self.tool_run('-overwrite_original','-Make=Test Camera','-Model=Stereo source',
            '-DateTimeOriginal=2024:03:05 12:34:56','-FocalLength=35',
            '-Copyright=Christoph Müller','-GPSLatitude=48.0','-GPSLatitudeRef=N',
            '-Orientation#=6','-XResolution=72','-YResolution=72','-ResolutionUnit=inches',
            '-ExifImageWidth=600','-ExifImageHeight=200',f'-ThumbnailImage<={thumb}',path)
        return path

    def test_web_preserves_capture_data_excludes_orientation_preview_and_updates_dimensions(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=self.source(root)
            original=source.read_bytes()
            for format in OutputFormat:
                options=WebRenderOptions(target_long_edge=900,output_format=format,outer_radius_percent=3)
                rendered=render_web(Image.open(source),options)
                target=root/('web.'+('jpg' if format==OutputFormat.JPEG else 'png'))
                result=save_render(rendered,target,format,metadata_source=source)
                self.assertTrue(result.success,result.message)
                meta=self.read(target)
                self.assertEqual(meta['IFD0:Make'],'Test Camera')
                self.assertEqual(meta['IFD0:Copyright'],'Christoph Müller')
                self.assertEqual(meta['ExifIFD:DateTimeOriginal'],'2024:03:05 12:34:56')
                self.assertEqual(meta['ExifIFD:FocalLength'],35)
                self.assertEqual(meta['GPS:GPSLatitude'],48)
                self.assertEqual(meta['ExifIFD:ExifImageWidth'],rendered.width)
                self.assertEqual(meta['ExifIFD:ExifImageHeight'],rendered.height)
                self.assertFalse(any(key.endswith(':Orientation') or key.endswith(':ThumbnailImage') or key.startswith('MPF:') for key in meta))
                with Image.open(target) as exported:
                    self.assertEqual(exported.size,rendered.size)
                    if format==OutputFormat.PNG:
                        self.assertEqual(exported.getpixel((0,0))[3],0)
            self.assertEqual(source.read_bytes(),original)
            self.assertFalse(list(root.glob('*_original')))

    def test_print_keeps_selected_dpi_and_actual_dimensions_in_jpeg_and_png(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=self.source(root)
            for dpi in (240,450):
                for format in OutputFormat:
                    options=PrintRenderOptions(dpi=dpi,width_mm=100,height_mm=60,bleed_mm=2.5)
                    rendered=render_print(Image.open(source),options)
                    target=root/(f'print-{dpi}.'+('jpg' if format==OutputFormat.JPEG else 'png'))
                    result=save_render(rendered,target,format,dpi=dpi,metadata_source=source)
                    self.assertTrue(result.success,result.message)
                    meta=self.read(target)
                    self.assertEqual(meta['IFD0:XResolution'],dpi)
                    self.assertEqual(meta['IFD0:YResolution'],dpi)
                    self.assertEqual(meta['IFD0:ResolutionUnit'],2)
                    self.assertEqual(meta['ExifIFD:ExifImageWidth'],rendered.width)
                    self.assertEqual(meta['ExifIFD:ExifImageHeight'],rendered.height)
                    with Image.open(target) as exported:
                        self.assertEqual(exported.size,rendered.size)
                        for actual in exported.info['dpi']:
                            self.assertAlmostEqual(actual,dpi,delta=.02)
