"""Verify ExifTool from the actual executable-side tools folder, without PATH fallback."""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
from freeda.metadata import find_exiftool_path
from freeda.models import OutputFormat
from freeda.render import save_render

parser=argparse.ArgumentParser()
parser.add_argument('executable',type=Path)
args=parser.parse_args()
tools=args.executable.resolve().parent/'tools'
with patch('sys.frozen',True,create=True), patch('sys.executable',str(args.executable.resolve())):
    tool=find_exiftool_path()
    if tool is None or tool.parent.resolve()!=tools:
        raise RuntimeError('Packaged ExifTool not found beside executable.')
    version=subprocess.run([str(tool),'-ver'],capture_output=True,text=True,check=True).stdout.strip()
    if version!='13.59':
        raise RuntimeError('Packaged ExifTool version differs.')
    with tempfile.TemporaryDirectory() as folder:
        source=Path(folder)/'source.jpg'
        target=Path(folder)/'target.png'
        exif=Image.Exif()
        exif[271]='Packaged test camera'
        Image.new('RGB',(60,20),'red').save(source,exif=exif)
        result=save_render(Image.new('RGBA',(90,50),'red'),target,OutputFormat.PNG,dpi=240,metadata_source=source)
        if not result.success:
            raise RuntimeError(result.message)
        meta=json.loads(subprocess.run([str(tool),'-j','-G1','-n',str(target)],capture_output=True,
            encoding='utf-8',check=True).stdout)[0]
        if meta['IFD0:Make']!='Packaged test camera' or meta['IFD0:XResolution']!=240 or meta['ExifIFD:ExifImageWidth']!=90:
            raise RuntimeError('Packaged metadata export is incorrect.')
print('Packaged tools/ExifTool version, runtime and real metadata export verified.')
