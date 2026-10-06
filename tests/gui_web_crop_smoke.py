"""Real crop dialogs, per-image state and batch export integration."""
import json, sys, tempfile, time
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
import freeda.gui as gui
from freeda.batch import discover_files
from freeda.models import Crop
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    settings = root / "settings.json"
    settings.write_text(json.dumps({"language":"de", "presets":{"Saved":{"size_var":"1280","aspect_var":"1:1"}}}))
    app = gui.FreedaApp(settings_path=settings)
    app.withdraw()
    real_dialog = gui.CropDialog
    try:
        assert app.language == "de" and app.size_var.get() == "2048"
        assert app.mode_var.get() == "Web" and app.aspect_var.get() == "Original"
        assert app.frame_var.get() == 4 and not app.include_subfolders_var.get()
        assert app.preset_var.get() != "Saved"
        paths = [root / "one.png", root / "two.png"]
        for path, size in zip(paths, [(600,200), (400,300)]):
            Image.new("RGB", size, "red").save(path)
        sub = root / "sub"
        sub.mkdir()
        Image.new("RGB", (600,200)).save(sub / "three.png")
        app.input_root = root
        app.items = discover_files([root], recursive=False)
        app._input_changed()
        assert len(app.items) == 2
        app.include_subfolders_var.set(True)
        app._reload_folder()
        assert len(app.items) == 3
        app.include_subfolders_var.set(False)
        app._reload_folder()
        app.aspect_var.set("1:1")
        app._aspect_changed("1:1")
        dialogs = []
        class Accept(real_dialog):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs)
                self.withdraw()
                dialogs.append(kwargs)
                self.zoom_var.set(1.4)
                self.after(50,self._accept)
        gui.CropDialog = Accept
        app.edit_crop()
        assert len(dialogs)==1 and dialogs[0]["editing"]
        first_crop = app._current_crop("Web")
        assert first_crop != Crop()
        app.navigate(1)
        assert app._current_crop("Web") == Crop()
        app.navigate(-1)
        assert app._current_crop("Web") == first_crop
        app.web_crop_mode_var.set("Gleichen Ausschnitt verwenden")
        before = app.source_index
        app.start_batch()
        deadline = time.monotonic()+20
        def poll():
            if not app._busy or time.monotonic()>deadline:
                app.quit()
            else:
                app.after(20,poll)
        app.after(20,poll)
        app.mainloop()
        assert not app._busy and app.source_index == before
        outputs = list((root/"output/web").glob("*.jpg"))
        assert len(outputs)==2 and len(dialogs)==1
        for path in paths:
            assert app.image_crops["Web"][path.resolve()] == first_crop
        for output in outputs:
            with Image.open(output) as image:
                assert max(image.size) == 2048
        app.save_preset("Web square")
        assert "image_crops" not in app.presets["Web square"]
        app.reset_crop()
        assert app.aspect_var.get()=="1:1" and app._current_crop("Web")==Crop()
        assert app.image_crops['Web'][paths[1].resolve()] == first_crop
        app.aspect_var.set('Benutzerdefiniert');app.custom_aspect_var.set('2:3')
        app.reset_crop()
        assert app.aspect_var.get() == 'Benutzerdefiniert' and app._web_aspect() == 2/3
        app.apply_preset("Web square")
        assert app._web_options().eye_aspect == 1
        # Explicit review with individual crops opens one dialog per selected image.
        app.web_review_var.set(True)
        app.web_crop_mode_var.set("Jedes Bild manuell")
        crops, kept = app._prepare_web_crops(list(app.items), app._web_options())
        assert len(kept)==2 and len(dialogs)==3
        class Cancel(real_dialog):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs)
                self.withdraw()
                self.after(50,self._cancel)
        gui.CropDialog=Cancel
        crops, kept = app._prepare_web_crops(list(app.items),app._web_options())
        assert kept==[] and not app._busy
        # Single images use the preview crop even with a selected aspect ratio.
        with patch('freeda.gui.filedialog.askopenfilenames', return_value=[str(paths[0])]):
            app.choose_files()
        assert not app.batch_mode
        app.web_review_var.set(False)
        app.aspect_var.set('1:1')
        saved = Crop(.1, .1, .7, .7)
        app._store_crop(app.items[0], 'Web', saved)
        with patch('freeda.gui.CropDialog', side_effect=AssertionError('Unexpected crop dialog')):
            crops, kept = app._prepare_web_crops(list(app.items), app._web_options())
            assert len(kept) == 1 and crops[paths[0].resolve()] == saved
            # Print also exports directly and passes the saved crop to rendering.
            app.mode_var.set('Print');app._mode_changed('Print')
            app.dpi_var.set('96')
            app._store_crop(app.items[0], 'Print', saved)
            actual_render = gui.render_print
            rendered_options = []
            def capture(source, options):
                rendered_options.append(options)
                return actual_render(source, options)
            with patch('freeda.gui.render_print', side_effect=capture):
                app.start_batch()
            assert len(rendered_options) == 1 and rendered_options[0].crop == saved
            assert not app._busy and len(list((root/'output/print').glob('*.jpg'))) == 1
        # Review is explicitly opt-in for a single image in each mode.
        gui.CropDialog = Accept
        app.print_review_var.set(True)
        app.start_batch()
        assert len(dialogs) == 4 and not app._busy
        app.mode_var.set('Web');app._mode_changed('Web')
        app.web_review_var.set(True)
        crops, kept = app._prepare_web_crops(list(app.items), app._web_options())
        assert len(dialogs) == 5 and len(kept) == 1
    finally:
        gui.CropDialog=real_dialog
        app.destroy()
print("Startup defaults, optional subfolders, web crop editing/reuse/manual/cancel, real exports and preset separation passed")
