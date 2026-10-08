"""Native crop dialogs, saved per-image state and asynchronous exports."""
import json, sys, tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from gui_helpers import wait_for_job
import freeda.gui as gui
from freeda.models import Crop

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    folder = root / "pictures"
    folder.mkdir()
    paths = [folder / "one.png", folder / "two.png"]
    for path, size in zip(paths, [(600, 200), (400, 300)]):
        Image.new("RGB", size, "red").save(path)
    sub = folder / "sub"
    sub.mkdir()
    Image.new("RGB", (600, 200)).save(sub / "three.png")
    settings = root / "settings.json"
    settings.write_text(json.dumps({"language": "de", "presets": {"Saved": {"size_var": "1280", "aspect_var": "1:1"}}}))
    app = gui.FreedaApp(settings_path=settings, program_dir=root / "program")
    app.withdraw()
    real_dialog = gui.CropDialog
    dialogs = []
    class Accept(real_dialog):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.withdraw()
            dialogs.append(kwargs)
            self.zoom_var.set(1.4)
            self.after(50, self._accept)
    class Cancel(real_dialog):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.withdraw()
            self.after(50, self._cancel)
    try:
        assert app.language == "de" and app.size_var.get() == "2048"
        assert app.mode_var.get() == "Web" and app.aspect_var.get() == "Original"
        assert app.frame_var.get() == 4 and not app.include_subfolders_var.get()
        assert not app.use_input_output.get()
        with patch("freeda.gui.filedialog.askdirectory", return_value=str(folder)):
            app.choose_folder()
            wait_for_job(app)
        assert len(app.items) == 2 and app.batch_mode
        app.include_subfolders_var.set(True)
        app._reload_folder(); wait_for_job(app)
        assert len(app.items) == 3
        app.include_subfolders_var.set(False)
        app._reload_folder(); wait_for_job(app)
        app.aspect_var.set("1:1")
        app._aspect_changed("1:1")
        gui.CropDialog = Accept
        app.edit_crop()
        assert len(dialogs) == 1 and dialogs[0]["editing"]
        first_crop = app._current_crop("Web")
        assert first_crop != Crop()
        app.navigate(1)
        assert app._current_crop("Web") == Crop()
        app.navigate(-1)
        app.web_crop_mode_var.set("Gleichen Ausschnitt verwenden")
        app.start_batch(); wait_for_job(app)
        assert len(dialogs) == 1
        assert len(app.last_batch_result.written) == 2
        for path in paths:
            assert app.image_crops["Web"][path.resolve()] == first_crop
        assert all(p.parent == root / "program/output/pictures" for p in app.last_batch_result.written)
        app.save_preset("Web square")
        assert "image_crops" not in app.presets["Web square"]
        app.reset_crop()
        assert app.aspect_var.get() == "1:1" and paths[1].resolve() in app.image_crops["Web"]
        app.web_review_var.set(True)
        app.web_crop_mode_var.set("Jedes Bild manuell")
        app.start_batch(); wait_for_job(app)
        assert len(dialogs) == 3
        gui.CropDialog = Cancel
        app.start_batch(); wait_for_job(app)
        assert app.last_batch_result.cancelled and not app.last_batch_result.written
        with patch("freeda.gui.filedialog.askopenfilenames", return_value=[str(paths[0])]):
            app.choose_files()
        assert not app.batch_mode and len(app.items) == 1
        app.web_review_var.set(False)
        saved = Crop(.1, .1, .7, .7)
        app._store_crop(app.items[0], "Web", saved)
        with patch("freeda.gui.CropDialog", side_effect=AssertionError("Unexpected crop dialog")):
            app.start_batch(); wait_for_job(app)
            assert app.image_crops["Web"][paths[0].resolve()] == saved
            assert app.last_batch_result.written[0].parent == root / "program/output"
            app.mode_var.set("Print"); app._mode_changed("Print")
            app.dpi_var.set("96")
            app._store_crop(app.items[0], "Print", saved)
            import freeda.batch as batch
            actual_render = batch.render_print
            rendered_options = []
            def capture(source, options):
                rendered_options.append(options)
                return actual_render(source, options)
            with patch("freeda.batch.render_print", side_effect=capture):
                app.start_batch(); wait_for_job(app)
            assert len(rendered_options) == 1 and rendered_options[0].crop == saved
        gui.CropDialog = Accept
        app.print_review_var.set(True)
        app.start_batch(); wait_for_job(app)
        assert len(dialogs) == 4
        app.mode_var.set("Web"); app._mode_changed("Web")
        app.web_review_var.set(True)
        app.start_batch(); wait_for_job(app)
        assert len(dialogs) == 5
    finally:
        gui.CropDialog = real_dialog
        app.destroy()
print("Folder checkbox, native manual/reuse/cancel cropping, single image exports and preset separation passed")
