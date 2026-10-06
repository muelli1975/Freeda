"""Windows GUI integration smoke test; run directly from the repository root."""
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from freeda.gui import FreedaApp
import freeda.gui as gui
from freeda.batch import discover_files
from freeda.models import LayoutMode
from freeda.geometry import print_canvas_px
from freeda.theme import GOLD, GOLD_LIGHT, BORDER, TEXT


app = FreedaApp(language="de")
app.withdraw()
try:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        app.settings_path = root / "settings.json"
        image = Image.new("RGB", (600, 200), "red")
        image.paste(Image.new("RGB", (300, 200), "lime"), (300, 0))
        image.save(root / "one.png")
        assert app.frame_var.get() == 4
        assert app.size_var.get() == "2048"
        assert app._web_options().target_width == 2048
        assert app.output_checkbox.cget("fg_color") == GOLD
        assert app.output_checkbox.cget("hover_color") == GOLD_LIGHT
        assert app.output_checkbox.cget("border_color") == BORDER
        assert app.output_checkbox.cget("checkmark_color") == TEXT
        assert app.start_button.cget("state") == "disabled"
        app.items = discover_files([root])
        app.input_root = None
        app._input_changed()
        assert app.start_button.cget("text") == "Angezeigtes Bild exportieren"
        assert app.start_button.cget("state") == "normal"
        assert app.output_status.cget("text") == str(root / "output/web")
        app.mode_var.set("Print")
        app._mode_changed("Print")
        assert app.show_bleed_var.get()
        assert app.bleed_var.get() == "0"
        assert app._print_options().bleed_mm == 0
        app._refresh_preview_note()
        assert "mit Beschnittrand" in app.preview_note.cget("text")
        assert app.start_button.cget("text") == "Angezeigtes Bild exportieren"
        assert app.output_status.cget("text") == str(root / "output/print")
        image.save(root / "two.png")
        app.items = discover_files([root])
        app._input_changed()
        assert app.start_button.cget("text") == "Batch exportieren (2 Bilder)"
        app.mode_var.set("Web")
        app._mode_changed("Web")
        app.outer_radius_var.set("5")
        app.start_batch()
        import time
        deadline = time.monotonic() + 20
        def poll():
            if not app._busy or time.monotonic() >= deadline:
                app.quit()
            else:
                app.after(20, poll)
        app.after(20, poll)
        app.mainloop()
        assert not app._busy
        assert len(list((root / "output/web").glob("*.jpg"))) == 2
        for output in (root / "output/web").glob("*.jpg"):
            with Image.open(output) as web:
                assert max(web.getpixel((0,0))) < 3
        assert app.status.cget("text") == "Fertig – 2 Dateien"
        app.input_root = None
        app.items = app.items[:1]
        app._input_changed()
        app.mode_var.set("Print")
        app._mode_changed("Print")
        real_dialog = gui.CropDialog
        class AcceptDialog(real_dialog):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.withdraw()
                assert "Zurücksetzen" in [widget.cget("text") for widget in self._texts]
                self.zoom_var.set(2)
                self.x_var.set(.9)
                self._reset()
                assert self.zoom_var.get() == 1 and self.x_var.get() == .5
                self.after(100, self._accept)
        gui.CropDialog = AcceptDialog
        app.dpi_var.set("450")
        assert app._print_options().dpi == 450
        app.start_batch()
        outputs = list((root / "output/print").glob("*.jpg"))
        assert len(outputs) == 1
        with Image.open(outputs[0]) as printed:
            assert round(printed.info["dpi"][0]) == 450
            assert min(printed.getpixel((0,0))) > 252
        app.dpi_var.set("300")
        assert app.status.cget("text") == "Fertig – 1 Datei"
        class CancelDialog(real_dialog):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.withdraw()
                self.after(100, self._cancel)
        gui.CropDialog = CancelDialog
        app.start_batch()
        assert not app._busy
        assert app.status.cget("text").startswith("Export abgebrochen")
        assert len(list((root / "output/print").glob("*.jpg"))) == 1
        gui.CropDialog = real_dialog
        app.caption_var.set("Mein eigener Untertitel")
        app.caption_size_var.set(5.0)
        app._caption_size_changed(5.0)
        app.bleed_var.set("2,5")
        assert app._print_options().bleed_mm == 2.5
        assert app._print_options().caption_size_percent == 5
        app._language_changed("English")
        assert app.start_button.cget("text") == "Export displayed image"
        assert app.caption_var.get() == "Mein eigener Untertitel"
        assert app.caption_size_label.cget("text") == "Caption size: 5.00 % per view"
        assert app.language == "en"
        for menu, variable, display, values in app._localized_options:
            if variable is app.layout_var:
                menu.cget("command")("Cross-eyed viewing")
                assert app._print_options().layout == LayoutMode.CROSS
                assert display.get() == "Cross-eyed viewing"
            if variable is app.print_format_var:
                menu.cget("command")("Photo 10 × 15 cm")
                assert app._print_options().width_mm == 150
        class EnglishAcceptDialog(real_dialog):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.withdraw()
                texts = [widget.cget("text") for widget in self._texts]
                assert "Apply and export" in texts
                assert "Cancel export" in texts
                assert "Crop" in texts
                self.after(100, self._accept)
        gui.CropDialog = EnglishAcceptDialog
        app.start_batch()
        assert app.status.cget("text") == "Done – 1 file"
        outputs = sorted((root / "output/print").glob("*.jpg"))
        assert len(outputs) == 1
        with Image.open(outputs[-1]) as printed:
            assert printed.size == print_canvas_px(150, 100, 300, 2.5)
        gui.CropDialog = real_dialog
        app._language_changed("Deutsch")
        assert app.start_button.cget("text") == "Angezeigtes Bild exportieren"
        assert app.layout_var.get() == "Kreuzblick"
        assert app.caption_var.get() == "Mein eigener Untertitel"
        assert app.bleed_var.get() == "2,5"
        before_items = list(app.items)
        before_root = app.input_root
        app.save_preset("Mein Druckpreset")
        app.bleed_var.set("0")
        app.caption_size_var.set(2)
        app.mode_var.set("Web")
        app._mode_changed("Web")
        app.caption_var.set("Neuer bildbezogener Untertitel")
        app._language_changed("English")
        app.apply_preset("Mein Druckpreset")
        assert app.mode_var.get() == "Print"
        assert app.bleed_var.get() == "2,5"
        assert app.caption_size_var.get() == 5
        assert app.caption_var.get() == "Neuer bildbezogener Untertitel"
        assert app.items == before_items and app.input_root == before_root
        assert app.language == "en"
        assert app.status.cget("text") == "Preset loaded"
        reloaded = FreedaApp(settings_path=app.settings_path)
        reloaded.withdraw()
        try:
            assert reloaded.language == "en"
            assert reloaded.size_var.get() == "2048"
            assert "Mein Druckpreset" in reloaded.presets
            reloaded.apply_preset("Mein Druckpreset")
            assert reloaded._print_options().bleed_mm == 2.5
            assert reloaded._print_options().caption_size_percent == 5
        finally:
            reloaded.destroy()
        print("GUI feedback, DE/EN switches, custom bleed, caption size, real web/print exports and cancellation passed")
finally:
    app.destroy()
