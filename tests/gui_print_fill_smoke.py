"""Print format stays filled even when loading presets from the withdrawn option."""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from gui_helpers import wait_for_job
import freeda.gui as gui
from freeda.batch import discover_files
from freeda.print_render import print_eye_aspect
from freeda.geometry import print_canvas_px

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp).resolve()
    settings=root/'settings.json'
    settings.write_text(json.dumps({'presets': {'Old Print': {
        'mode_var':'Print', 'print_aspect_var':'Benutzerdefiniert',
        'custom_print_aspect_var':'2:3', 'font_var':'Arial'}}}))
    app=gui.FreedaApp(settings_path=settings)
    app.withdraw()
    app.output_dir = root / "output"
    app.use_program_output.set(False)
    real_dialog=gui.CropDialog
    try:
        assert app.title()=='Freeda 1.1'
        assert app.frame_var.get()==4 and app.show_symbols_var.get()
        assert not hasattr(app,'print_aspect_var')
        app.apply_preset('Old Print')
        assert app.mode_var.get()=='Print' and app.font_var.get()=='Arial'
        assert app.tr('Untertitelschrift')=='Untertitelschrift'
        for name,size in (('one.png',(800,300)),('two.png',(600,400))):
            Image.new('RGB',size,'red').save(root/name)
        app.input_root=root
        app.items=discover_files([root],recursive=False)
        app._input_changed()
        app.dpi_var.set('96')
        app.bleed_var.set('2.5')
        app.color_preset_var.set('Benutzerdefiniert')
        app._color_preset_changed('Benutzerdefiniert')
        app.frame_color_var.set('#225533')
        app.print_format_var.set('Benutzerdefiniert')
        app.print_width_var.set('100')
        app.print_height_var.set('150')
        app._print_format_changed('Benutzerdefiniert')
        before=print_eye_aspect(app._print_options())
        app.print_width_var.set('150')
        app.print_height_var.set('100')
        assert print_eye_aspect(app._print_options())!=before
        app.frame_var.set(0)
        app._frame_changed(0)
        app.show_symbols_var.set(False)
        assert app.show_symbols_checkbox.cget('state')=='disabled'
        app.save_preset('Plain card')
        app.frame_var.set(4)
        app._frame_changed(4)
        app.show_symbols_var.set(True)
        assert app.show_symbols_checkbox.cget('state')=='normal'
        app.apply_preset('Plain card')
        assert app.frame_var.get()==0 and not app.show_symbols_var.get()
        assert app._print_options().frame_percent==0 and not app._print_options().show_symbols
        assert app._web_options().frame_percent==0 and not app._web_options().show_symbols
        dialogs=[]
        class Accept(real_dialog):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs)
                self.withdraw()
                assert self._target_aspect()==print_eye_aspect(self.options)
                self.zoom_var.set(1.2)
                assert self.grid_var.get()
                dialogs.append(self.current_crop())
                self.after(50,self._accept)
        gui.CropDialog=Accept
        app.crop_mode_var.set('Gleichen Ausschnitt verwenden')
        app.start_batch()
        wait_for_job(app)
        assert not app._busy and len(dialogs)==1
        outputs=list((root/'output'/root.name).glob('*.jpg'))
        assert len(outputs)==2
        for output in outputs:
            with Image.open(output) as image:
                assert image.size==print_canvas_px(150,100,96,2.5)
                assert max(abs(a-b) for a,b in zip(image.getpixel((0,0)),(34,85,51)))<=2
        app._language_changed('English')
        assert app.tr('Untertitelschrift')=='Caption font'
        assert app.tr('Blicksymbole anzeigen')=='Show viewing symbols'
        app.aspect_var.set('1:1')
        assert app._web_options().eye_aspect==1
        app.save_preset('Final Print')
        assert 'print_aspect_var' not in app.presets['Final Print']
        reloaded=gui.FreedaApp(settings_path=settings)
        reloaded.withdraw()
        try:
            assert reloaded.frame_var.get()==4 and reloaded.show_symbols_var.get()
            reloaded.apply_preset('Plain card')
            assert reloaded.frame_var.get()==0 and not reloaded.show_symbols_var.get()
        finally:
            reloaded.destroy()
    finally:
        gui.CropDialog=real_dialog
        app.destroy()
print('Print fills paper, bleed matches frame, old presets migrate, crop grid and independent caption selection passed')
