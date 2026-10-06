"""Portable logo import, switching, actual exports, presets and English UI."""
import sys, json, shutil, tempfile, time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image,ImageDraw
import freeda.gui as gui
from freeda.models import CaptionMode
from freeda.batch import discover_files

with tempfile.TemporaryDirectory() as tmp:
    # Windows runners may spell TEMP with an 8.3 alias; compare resolved paths.
    root = Path(tmp).resolve()
    program = root/'program';program.mkdir()
    source = root/'input';source.mkdir()
    Image.new('RGB',(600,200),'red').save(source/'sbs.png')
    logo = root/("very_long_logo_filename_"*7+'.png')
    mark=Image.new('RGBA',(120,60));ImageDraw.Draw(mark).rectangle((20,10,100,50),fill='magenta');mark.save(logo)
    app=gui.FreedaApp(language='de',settings_path=program/'settings.json')
    app.withdraw()
    original_dialog=gui.CropDialog
    try:
        assert app.caption_mode_var.get()=='Text'
        assert not app.logo_controls.winfo_manager()
        assert app._web_options().caption_mode==CaptionMode.TEXT
        legacy={key:getattr(app,key).get() for key in gui._PRESET_VARIABLES if not key.startswith('logo_') and key!='caption_mode_var'}
        app.items=discover_files([source/'sbs.png']);app._input_changed()
        app.caption_var.set('Hidden text must not appear in a pending logo preview')
        app.caption_mode_var.set('Logo');app._layout_changed()
        assert app.logo_status.cget('text')=='Bitte ein Logo wählen.'
        assert app.start_button.cget('state')=='disabled'
        pending=app._web_options(allow_pending_logo=True)
        assert pending.caption=='' and pending.logo_path is None
        with patch.object(app.preview_label,'winfo_width',return_value=1000), patch.object(app.preview_label,'winfo_height',return_value=700):
            app.update_preview()
        assert app.preview_photo is not None and app.preview_label.cget('text')==''
        assert app.preview_note.cget('text')=='Bitte ein Logo wählen.'
        with patch('freeda.gui.messagebox.showinfo') as info, patch('freeda.gui.messagebox.showerror') as error:
            app.start_batch()
            assert info.call_args.args[1]=='Bitte ein Logo wählen.'
            error.assert_not_called()
        with patch('freeda.gui.filedialog.askopenfilename',return_value=''):
            app.choose_logo()
        assert app._logo_pending() and app.start_button.cget('state')=='disabled'
        app.mode_var.set('Print');app._mode_changed('Print')
        app.logo_unit_var.set('Millimeter (mm)');app.logo_mm_var.set('not a number');app._layout_changed()
        assert 'Bildfenster:' in app.print_geometry_label.cget('text')
        assert 'Bitte ein Logo wählen.' in app.print_geometry_label.cget('text')
        app.save_preset('Waiting for logo')
        app.caption_mode_var.set('Text');app._layout_changed()
        assert app.start_button.cget('state')=='normal'
        app.apply_preset('Waiting for logo')
        app._language_changed('English')
        app._refresh_preview_note()
        assert app.logo_status.cget('text')=='Please choose a logo.'
        assert app.preview_note.cget('text')=='Please choose a logo.'
        app._language_changed('Deutsch')
        app.mode_var.set('Web');app._mode_changed('Web')
        app.logo_mm_var.set('4');app.caption_var.set('')
        with patch('freeda.gui.filedialog.askopenfilename',return_value=str(logo)):
            app.choose_logo()
        assert app.start_button.cget('state')=='normal'
        assert app.caption_mode_var.get()=='Logo'
        assert app.logo_controls.winfo_manager()=='grid'
        assert all(not widget.winfo_manager() for widget in app.caption_text_widgets)
        assert app.logo_var.get().startswith('logos/') and not Path(app.logo_var.get()).is_absolute()
        assert app._web_options().logo_path.read_bytes()==logo.read_bytes()
        app._language_changed('English')
        assert app.logo_size_label.cget('text')=='Max. logo height: 6.00 % per view'
        assert app.logo_status.cget('text')==logo.name
        app._language_changed('Deutsch')
        logo.unlink()
        assert app._web_options().logo_path.is_file()
        app.items=discover_files([source/'sbs.png']);app._input_changed()
        app.format_var.set('PNG')
        app.outer_radius_var.set('3')
        app.start_batch()
        deadline=time.monotonic()+20
        def poll():
            if not app._busy or time.monotonic()>deadline:app.quit()
            else:app.after(20,poll)
        app.after(20,poll);app.mainloop()
        assert not app._busy
        with Image.open(source/'output/web/sbs_freeda_web.png') as output:
            assert output.getpixel((0,0))[3]==0
            assert (255,0,255,255) in output.get_flattened_data()
        app.mode_var.set('Print');app._mode_changed('Print')
        app.card_template_var.set('Holmes-Karte');app._card_template_changed('Holmes-Karte')
        app.logo_unit_var.set('Millimeter (mm)');app.logo_mm_var.set('4,5');app._layout_changed()
        assert app._print_options().logo_height_mm==4.5
        assert app.logo_slider.cget('state')=='disabled'
        class Accept(original_dialog):
            def __init__(self,*a,**kw):
                super().__init__(*a,**kw);self.withdraw();self.after(50,self._accept)
        gui.CropDialog=Accept
        app.dpi_var.set('96');app.start_batch()
        assert not app._busy
        with Image.open(source/'output/print/sbs_freeda_print.png') as output:
            assert (255,0,255,255) in output.get_flattened_data()
            assert abs(output.info['dpi'][0]-96)<.1
        app.save_preset('Logo card')
        saved=json.loads((program/'settings.json').read_text(encoding='utf-8'))['presets']['Logo card']
        assert saved['logo_var'].startswith('logos/')
        app.presets['Legacy 1.1']=legacy;app.apply_preset('Legacy 1.1')
        assert app.caption_mode_var.get()=='Text' and not app.logo_var.get()
        app.apply_preset('Logo card')
        app._set_busy(True);app._set_busy(False)
        assert app.logo_slider.cget('state')=='disabled'
        app._language_changed('English')
        assert app.logo_size_label.cget('text')=='Max. logo height: 4.5 mm'
        assert app.caption_gap_top_label.cget('text')=='Logo padding above mm'
        app.caption_var.set('Keep this text when switching')
        app.caption_mode_var.set('Text');app._layout_changed()
        assert not app.logo_controls.winfo_manager()
        assert app.caption_var.get()=='Keep this text when switching'
        app.caption_mode_var.set('Logo');app._layout_changed()
        moved=root/'moved'
        shutil.copytree(program,moved)
        reloaded=gui.FreedaApp(settings_path=moved/'settings.json')
        reloaded.withdraw()
        try:
            assert reloaded.caption_mode_var.get()=='Text'
            reloaded.apply_preset('Logo card')
            assert reloaded._print_options().logo_path.parent==moved/'logos'
            assert reloaded._print_options().logo_height_mm==4.5
        finally:reloaded.destroy()
        app.logo_var.set('logos/missing.png')
        app._layout_changed()
        assert 'Could not read the logo' in app.print_geometry_label.cget('text')
    finally:
        gui.CropDialog=original_dialog
        app.destroy()

print('Portable logo import, real Web/Print exports, moved presets, defaults and English controls passed')
