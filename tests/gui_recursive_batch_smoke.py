"""Real folder selection, output exclusions, crop pause and responsive cancellation."""
from pathlib import Path
import sys
import tempfile
from threading import Event
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from gui_helpers import wait_for_job
import freeda.batch as batch
import freeda.gui as gui
from freeda.crop_storage import FILENAME, load_crops, save_crop
from freeda.models import Crop
from freeda.theme import GOLD

with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    folder = base / "Urlaub"
    paths = [folder / "Tag1/bild.png", folder / "Tag2/tief/bild.png"]
    for path in paths:
        path.parent.mkdir(parents=True)
        Image.new("RGB", (600, 200), "red").save(path)
    originals = {p: p.read_bytes() for p in paths}
    crops = [Crop(.1, .1, .7, .7), Crop(.2, .2, .5, .5)]
    for path, crop in zip(paths, crops):
        save_crop(path, "Web", crop)
        save_crop(path, "Print", crop)
    notices = []
    errors = []
    app = gui.FreedaApp(settings_path=base / "program/settings.json", program_dir=base / "program")
    app.withdraw()
    try:
        assert app.output_dir == base / "program/output"
        assert not app.use_input_output.get() and not app.include_subfolders_var.get()
        assert app.subfolders_checkbox.cget("fg_color") == GOLD
        app.remember_crops_var.set(True)
        app.include_subfolders_var.set(True)
        with patch("freeda.gui.filedialog.askdirectory", return_value=str(folder)):
            app.choose_folder(); wait_for_job(app)
        assert len(app.items) == 2 and app.batch_mode
        assert app.output_status.cget("text") == str(base / "program/output/Urlaub")
        assert app.image_crops["Web"][paths[0].resolve()] == crops[0]
        assert app.image_crops["Web"][paths[1].resolve()] == crops[1]
        app.size_var.set("640")
        app.aspect_var.set("1:1")
        with (patch("freeda.gui.messagebox.showwarning", side_effect=lambda *a: notices.append(a)),
              patch("freeda.gui.messagebox.showerror", side_effect=lambda *a: errors.append(a))):
            with patch("freeda.gui.CropDialog", side_effect=AssertionError("Saved crop should be reused")):
                app.start_batch(); wait_for_job(app)
            assert not app.last_batch_result.errors and len(app.last_batch_result.written) == 2
            assert [p.parent for p in app.last_batch_result.written] == [
                base / "program/output/Urlaub/Tag1", base / "program/output/Urlaub/Tag2/tief"]
            # Changing output to a source subfolder must rescan and exclude that entire tree.
            output = folder / "fertige Karten"
            output.mkdir()
            Image.new("RGB", (600, 200)).save(output / "foreign-source.png")
            with patch("freeda.gui.filedialog.askdirectory", return_value=str(output)):
                app.choose_output(); wait_for_job(app)
            assert len(app.items) == 2
            app.start_batch(); wait_for_job(app)
            previous = {p: p.read_bytes() for p in app.last_batch_result.written}
            app._reload_folder(); wait_for_job(app)
            assert len(app.items) == 2
            # Keep distinct relative paths visible for equal filenames.
            app.navigate(1)
            assert "Tag2" in app.navigation_status.cget("text")
            app.mode_var.set("Print"); app._mode_changed("Print")
            app.dpi_var.set("96")
            app.print_review_var.set(True)
            dialogs = []
            real = gui.CropDialog
            class Accept(real):
                def __init__(self, *a, **kw):
                    super().__init__(*a, **kw)
                    self.withdraw()
                    assert app._busy and app.cancel_button.cget("state") == "normal"
                    dialogs.append(kw)
                    self.zoom_var.set(1.2)
                    self.after(50, self._accept)
            with patch("freeda.gui.CropDialog", Accept):
                app.start_batch(); wait_for_job(app)
            assert len(dialogs) == 2 and len(app.last_batch_result.written) == 2
            for path in paths:
                assert load_crops(path.parent)[path.name]["Print"] == app.image_crops["Print"][path.resolve()]
            assert not (output / FILENAME).exists()
            class Cancel(real):
                def __init__(self, *a, **kw):
                    super().__init__(*a, **kw)
                    self.withdraw()
                    self.after(50, self._cancel)
            with patch("freeda.gui.CropDialog", Cancel):
                app.start_batch(); wait_for_job(app)
            assert app.last_batch_result.cancelled and not app.last_batch_result.written
            # Cancel while a renderer is busy; Tk keeps handling the cancel button.
            app.mode_var.set("Web"); app._mode_changed("Web")
            started = Event()
            render = batch.render_web
            def delayed(source, options):
                started.set()
                assert app._cancel_event.wait(5), "UI did not deliver cancellation"
                return render(source, options)
            def cancel_when_running():
                if started.is_set():
                    assert app.cancel_button.cget("state") == "normal"
                    app.cancel_button.invoke()
                else:
                    app.after(10, cancel_when_running)
            with patch("freeda.batch.render_web", side_effect=delayed):
                app.start_batch()
                app.after(10, cancel_when_running)
                wait_for_job(app)
            assert app.last_batch_result.cancelled and not app.last_batch_result.written
            assert {p: p.read_bytes() for p in previous} == previous
            assert not list(output.rglob(".freeda-export-*"))
            assert app.cancel_button.cget("state") == "disabled"
            # A corrupt input is reported with its folder and does not stop healthy inputs.
            (folder / "broken.png").write_bytes(b"broken image")
            app._reload_folder(); wait_for_job(app)
            app.start_batch(); wait_for_job(app)
            assert len(app.last_batch_result.errors) == 1 and len(app.last_batch_result.written) == 2
            assert "broken.png" in notices[-1][1] and not errors
            # Cancelled rescans retain the last complete snapshot and matching options.
            previous_items = list(app.items)
            scanned = Event()
            def delayed_scan(*a, **kw):
                scanned.set()
                assert kw["cancel"].wait(5)
                return []
            def cancel_scan():
                if scanned.is_set():
                    app.cancel_button.invoke()
                else:
                    app.after(10, cancel_scan)
            app.include_subfolders_var.set(False)
            with patch("freeda.gui.discover_files", side_effect=delayed_scan):
                app._reload_folder()
                app.after(10, cancel_scan)
                wait_for_job(app)
            assert app.items == previous_items and app.include_subfolders_var.get()
            app._language_changed("English")
            assert app.subfolders_checkbox.cget("text") == "Include subfolders"
            assert app.cancel_button.cget("text") == "Cancel"
            assert app.status.cget("text") == "Reading cancelled"
        assert {p: p.read_bytes() for p in paths} == originals
    finally:
        app.destroy()
print("Nested folder snapshots, program/custom output, source crop records, Print pauses, UI cancellation and error summary passed")
