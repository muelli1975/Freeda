"""Real GUI Web/Print exports and nonfatal metadata warning behaviour."""
import json, subprocess, sys, tempfile, time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
from gui_helpers import wait_for_job
import freeda.gui as gui
from freeda.batch import discover_files
from freeda.metadata import find_exiftool_path

with tempfile.TemporaryDirectory() as folder:
    root=Path(folder).resolve()
    source=root/'Aufnahme ä 測試.jpg'
    exif=Image.Exif()
    exif[271]='Test Camera'
    exif[274]=6
    Image.new('RGB',(600,200),'red').save(source,exif=exif)
    original=source.read_bytes()
    app=gui.FreedaApp(settings_path=root/'settings.json')
    app.withdraw()
    app.output_dir = root / "output"
    app.use_program_output.set(False)
    real_dialog=gui.CropDialog
    notices=[]
    errors=[]
    tool=find_exiftool_path()
    assert tool is not None
    def read(path):
        arguments='-j\n-G1\n-n\n'+str(path)+'\n'
        result=subprocess.run([str(tool),'-charset','filename=UTF8','-@','-'],input=arguments,
            capture_output=True,text=True,encoding='utf-8',timeout=30,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        assert result.returncode==0,result.stderr
        return json.loads(result.stdout)[0]
    def wait_for_export():
        deadline=time.monotonic()+30
        def poll():
            if not app._busy or time.monotonic()>=deadline:
                app.quit()
            else:
                app.after(20,poll)
        app.after(20,poll)
        app.mainloop()
        assert not app._busy and not errors,errors
    try:
        app.items=discover_files([source])
        app._input_changed()
        with (patch('freeda.gui.messagebox.showwarning',side_effect=lambda *args: notices.append(args)),
              patch('freeda.gui.messagebox.showerror',side_effect=lambda *args: errors.append(args))):
            app.start_batch()
            wait_for_job(app)
            wait_for_export()
            web=next((root/'output').glob('*.jpg'))
            meta=read(web)
            assert meta['IFD0:Make']=='Test Camera' and 'IFD0:Orientation' not in meta
            with Image.open(web) as actual:
                assert meta['ExifIFD:ExifImageWidth']==actual.width
                assert meta['ExifIFD:ExifImageHeight']==actual.height
                assert max(actual.size)==2048
            class Accept(real_dialog):
                def __init__(self,*args,**kwargs):
                    super().__init__(*args,**kwargs)
                    self.withdraw()
                    self.after(50,self._accept)
            gui.CropDialog=Accept
            app.mode_var.set('Print')
            app._mode_changed('Print')
            app.dpi_var.set('240')
            app.format_var.set('PNG')
            app.start_batch()
            wait_for_job(app)
            output=next((root/'output').glob('*.png'))
            meta=read(output)
            assert meta['IFD0:Make']=='Test Camera'
            assert meta['IFD0:XResolution']==240 and 'IFD0:Orientation' not in meta
            assert notices==[]
            app._language_changed('English')
            with patch('freeda.metadata.find_exiftool_path',return_value=None):
                app.start_batch()
                wait_for_job(app)
            assert not app._busy and output.is_file() and len(notices)==1 and not errors
            assert 'The images were exported.' in notices[0][1]
            assert 'ExifTool not found.' in notices[0][1]
            app.mode_var.set('Web')
            app._mode_changed('Web')
            with patch('freeda.metadata.find_exiftool_path',return_value=None):
                app.start_batch()
                wait_for_job(app)
                wait_for_export()
            assert len(notices)==2 and 'ExifTool not found.' in notices[1][1]
            with Image.open(output) as image:
                image.load()
            assert source.read_bytes()==original
    finally:
        gui.CropDialog=real_dialog
        app.destroy()
print('GUI Web/Print metadata exports, preserved dpi and source, and English nonfatal warning passed')
