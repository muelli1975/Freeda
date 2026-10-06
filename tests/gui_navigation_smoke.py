from pathlib import Path
import sys, tempfile
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from freeda.gui import FreedaApp
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    paths = [root / f"{i}.png" for i in range(3)]
    for path in paths:
        Image.new("RGB", (600, 200), "red").save(path)
    app = FreedaApp(settings_path=root / "settings.json")
    app.update()
    with patch("freeda.gui.filedialog.askopenfilenames", return_value=[str(paths[1])]):
        app.choose_files()
    assert app.source_index == 1 and len(app.sources) == 3 and len(app.items) == 1
    app.navigate(1)
    assert app.items[0].source.resolve() == paths[2].resolve() and app.next_button.cget("state") == "disabled"
    app.navigate(1)
    assert app.source_index == 2
    with patch("freeda.gui.filedialog.askopenfilenames", return_value=[str(p) for p in paths]):
        app.choose_files()
    batch = list(app.items)
    app.navigate(1)
    assert app.items == batch and app.source_index == 1
    app._set_busy(True)
    app.navigate(1)
    assert app.source_index == 1
    app._set_busy(False)
    original = 'Freiburg – Blick auf die Stadt'
    app.caption_var.set(original)
    image, text = app._font_preview(app.font_var.get())
    assert text == original and image.size == (380, 70)
    original = 'Ein sehr langer Untertitel mit Umlauten äöü und vielen Worten ' * 12
    app.caption_var.set(original)
    image, text = app._font_preview(app.font_var.get())
    assert text.endswith('…') and len(text) < len(original)
    from freeda.render import _font
    assert _font(app.font_var.get(), 24).getlength(text) <= 364
    assert app.caption_var.get() == original
    app.caption_var.set('  ')
    assert app._font_preview(app.font_var.get())[1] == 'Aa – Freeda 123'
    app.caption_var.set(original)
    app._open_fonts()
    app.update()
    dialog = next(w for w in app.winfo_children() if w.winfo_class() == "Toplevel")
    import customtkinter as ctk
    def descendants(widget):
        for child in widget.winfo_children():
            yield child
            yield from descendants(child)
    sample = next(w for w in descendants(dialog) if hasattr(w, 'display_text'))
    assert sample.display_text.endswith('…') and app.caption_var.get() == original
    listing = next(w for w in descendants(dialog) if isinstance(w, ctk.CTkScrollableFrame))
    canvas = listing._parent_canvas
    before = canvas.yview()
    listing.event_generate("<MouseWheel>", delta=-120)
    app.update()
    after = canvas.yview()
    assert after[0] > before[0], (before, after)
    app.destroy()
print("Single/batch navigation, boundaries, busy state and font-list mouse wheel passed")
