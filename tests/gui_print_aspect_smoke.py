"""Exercise Print ratio controls, real crop dialogs, presets and batch exports."""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
import freeda.gui as gui
from freeda.batch import discover_files
from freeda.models import Crop

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    settings = root / 'settings.json'
    app = gui.FreedaApp(settings_path=settings)
    app.withdraw()
    real_dialog = gui.CropDialog
    try:
        assert app.print_aspect_var.get() == 'Druckformat ausfüllen'
        assert app.title() == 'Freeda 1.0'
        assert app._print_options().fit_to_paper
        for name, size in (('one.png', (800,300)), ('two.png', (600,400))):
            Image.new('RGB',size,'red').save(root/name)
        app.input_root = root
        app.items = discover_files([root], recursive=False)
        app._input_changed()
        app.mode_var.set('Print')
        app._mode_changed('Print')
        app.dpi_var.set('96')
        app.print_aspect_var.set('Benutzerdefiniert')
        app.custom_print_aspect_var.set('2:3')
        app._print_aspect_changed('Benutzerdefiniert')
        assert app._print_options().eye_aspect == 2/3
        assert not app._print_options().fit_to_paper
        app.save_preset('Portrait eyes')
        app.print_aspect_var.set('Original')
        app._print_aspect_changed('Original')
        assert app._print_options().eye_aspect is None
        assert not app._print_options().fit_to_paper
        app.apply_preset('Portrait eyes')
        assert app.print_aspect_var.get() == 'Benutzerdefiniert'
        assert app._print_options().eye_aspect == 2/3
        app.print_format_var.set('Benutzerdefiniert')
        app.print_width_var.set('100')
        app.print_height_var.set('150')
        app._print_format_changed('Benutzerdefiniert')
        assert app._print_options().eye_aspect == 2/3
        dialogs=[]
        class Accept(real_dialog):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs)
                self.withdraw()
                assert self._target_aspect() == 2/3
                self.zoom_var.set(1.2)
                dialogs.append(self.current_crop())
                self.after(50, self._accept)
        gui.CropDialog=Accept
        app.edit_crop()
        assert app._current_crop('Print') != Crop()
        app.crop_mode_var.set('Gleichen Ausschnitt verwenden')
        app.start_batch()
        assert not app._busy
        outputs=list((root/'output/print').glob('*.jpg'))
        assert len(outputs)==2 and len(dialogs)==2
        for output in outputs:
            with Image.open(output) as image:
                assert image.size == (378,567)
                assert min(image.getpixel((0,0))) >= 250
        app.custom_print_aspect_var.set('0:3')
        try:
            app._print_options()
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid Print ratio accepted')
        app._language_changed('English')
        assert app.tr('Druckformat ausfüllen') == 'Fill paper format'
        assert json.loads(settings.read_text())['presets']['Portrait eyes']['custom_print_aspect_var']=='2:3'
    finally:
        gui.CropDialog=real_dialog
        app.destroy()
print('Print aspect selection, custom ratio validation, paper independence, presets, crop dialog and batch exports passed')
