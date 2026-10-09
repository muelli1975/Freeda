"""Compare actual Tk widgets with pinned SplatTricia and StereoFine sources."""
from pathlib import Path
import ast
import json
import sys
import tempfile
import time
import urllib.request
from unittest.mock import patch
from PIL import Image, ImageGrab
import customtkinter as ctk

root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root), str(root / "src")]
app_name = "AnaChroma" if (root / "src/anachroma").is_dir() else "Freeda"
references = (
    ("SplatTricia", "fe5cbc9fdc437011470130242fc490c2cf3984a3", "src/splattricia/theme.py",
     {"bg":"BUTTON_BG", "hover":"BUTTON_HOVER", "text":"TEXT", "disabled":"TEXT_DISABLED",
      "start":"START_BG", "start_hover":"START_HOVER_BG", "start_text":"START_TEXT",
      "hover_text":"START_HOVER_TEXT", "border":"START_BORDER", "hover_border":"START_HOVER_BORDER"}),
    ("StereoFine", "fe849fcbac4da4aa403b47e62c0ae9ab5040cea9", "stereofine/theme.py",
     {"bg":"SECONDARY_BG", "hover":"HOVER_BG", "text":"TEXT_PRIMARY", "disabled":"TEXT_DISABLED",
      "start":"SECONDARY_BG", "start_hover":"GOLD_LIGHT", "start_text":"GOLD_LIGHT",
      "hover_text":"APP_BG", "border":"GOLD_DARK", "hover_border":"GOLD_LIGHT"}),
)
palettes = []
for repository, commit, filename, keys in references:
    url = f"https://raw.githubusercontent.com/muelli1975/{repository}/{commit}/{filename}"
    source = urllib.request.urlopen(url, timeout=30).read().decode()
    values = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            value = node.value
            if isinstance(value, ast.Constant):
                values[node.targets[0].id] = value.value
            elif isinstance(value, ast.Name) and value.id in values:
                values[node.targets[0].id] = values[value.id]
    palettes.append({key:values[name] for key,name in keys.items()})
assert palettes[0] == palettes[1], palettes
palette = palettes[0]
print("Reference colors verified against both pinned GUI theme sources:", json.dumps(palette))

if app_name == "AnaChroma":
    from anachroma import gui
else:
    from freeda import gui

screens = root / "build/family-ui"
screens.mkdir(parents=True, exist_ok=True)

def wait(app, condition):
    end = time.monotonic() + 30
    while time.monotonic() < end:
        app.update()
        if condition():
            return
        time.sleep(.01)
    raise AssertionError("GUI did not become ready")

def fill(button):
    return button._canvas.itemcget("inner_parts", "fill").lower()

def colors(button, background, text, border):
    assert button.cget("fg_color") == background
    assert fill(button) == background, (fill(button), background)
    assert button.cget("text_color") == text
    assert button.cget("border_color") == border

with tempfile.TemporaryDirectory() as directory:
    base = Path(directory)
    image = Image.new("RGB", (640, 200), "#986040")
    image.paste("#407090", (320, 0, 640, 200))
    source = base / "pair.png"
    image.save(source)
    with patch.object(gui.messagebox, "showwarning"), patch.object(gui.messagebox, "showerror"):
        if app_name == "AnaChroma":
            with patch.object(gui, "user_dir", return_value=base):
                app = gui.AnaChromaApp()
            app.load_input(source)
            wait(app, lambda: app.inputs is not None and not app.scanning and app.preview_photo is not None)
            primary = app.action_button
            secondary = app.file_button
            set_busy = lambda value: (setattr(app, "batch_running", value), app._state())
        else:
            app = gui.FreedaApp(settings_path=base / "settings.json", program_dir=base)
            with patch.object(gui.filedialog, "askopenfilenames", return_value=[str(source)]):
                app.choose_files()
            wait(app, lambda: app.preview_photo is not None)
            primary = app.start_button
            secondary = app.previous_button
            set_busy = app._set_busy
        try:
            assert app.title() == app_name + (" 1.0" if app_name == "AnaChroma" else " 1.2")
            for scale in (1., 1.5):
                ctk.set_widget_scaling(scale)
                ctk.set_window_scaling(scale)
                for size in ((940,680), (1180,820)) if app_name == "AnaChroma" else ((1000,700),(1280,860)):
                    app.geometry(f"{size[0]}x{size[1]}")
                    for language in ("Deutsch","English"):
                        app._language_changed(language)
                        app.update()
                        primary._canvas.event_generate("<Leave>")
                        app.update()
                        colors(primary, palette["start"], palette["start_text"], palette["border"])
                        assert secondary.cget("fg_color") == palette["bg"]
                        assert secondary.cget("hover_color") == palette["hover"]
                        assert secondary.cget("text_color_disabled") == palette["disabled"]
                        hint = app.shortcuts_button
                        assert hint.winfo_ismapped()
                        assert hint.winfo_rootx() >= app.winfo_rootx()
                        assert hint.winfo_rootx()+hint.winfo_width() <= app.winfo_rootx()+app.winfo_width()
                        assert hint.winfo_rooty()+hint.winfo_height() <= app.winfo_rooty()+app.winfo_height()
                        assert hint._text_label.winfo_reqwidth() <= hint.winfo_width()-10
                        with patch.object(gui.messagebox, "showinfo") as info:
                            hint.invoke()
                            title, body = info.call_args.args
                            assert title == ("Tastenkürzel" if language == "Deutsch" else "Keyboard shortcuts")
                            assert ("Bild auf" if language == "Deutsch" else "Page Up") in body
                            assert ("Strg" if language == "Deutsch" else "Ctrl") in body if app_name == "AnaChroma" else "P:" in body and "X:" in body and "A:" in body
                        primary._canvas.event_generate("<Enter>")
                        app.update()
                        colors(primary, palette["start_hover"], palette["hover_text"], palette["hover_border"])
                        name = f"{app_name}-{language}-{size[0]}-{scale}-hover.png"
                        ImageGrab.grab().save(screens / name)
                        set_busy(True)
                        app.update()
                        colors(primary, palette["start"], palette["disabled"], "#333333")
                        assert primary.cget("state") == "disabled"
                        assert hint.cget("state") == "disabled"
                        assert secondary.cget("state") == "disabled"
                        primary._canvas.event_generate("<Enter>")
                        app.update()
                        colors(primary, palette["start"], palette["disabled"], "#333333")
                        set_busy(False)
                        primary._canvas.event_generate("<Leave>")
                        app.update()
                        colors(primary, palette["start"], palette["start_text"], palette["border"])
            app._language_changed("English")
            with patch.object(gui.filedialog, "askdirectory", return_value=str(base / "custom-output")):
                app.choose_output()
            app.size_var.set("1080p" if app_name == "AnaChroma" else "Original")
            if app_name == "AnaChroma":
                app.recursive.set(True)
                app._persist_settings()
            else:
                app.include_subfolders_var.set(True)
                app._save_preferences()
            print(app_name, "real Enter/Leave rendering, busy recovery, German/English shortcuts, small/large windows and 100/150% scaling passed")
        finally:
            if app_name == "AnaChroma":
                app.close()
                end = time.monotonic() + 5
                while time.monotonic() < end:
                    try:
                        app.update()
                        if not app.winfo_exists():
                            break
                    except gui.tk.TclError:
                        break
                    time.sleep(.01)
            else:
                app.destroy()
            ctk.set_widget_scaling(1.)
            ctk.set_window_scaling(1.)

        if app_name == "AnaChroma":
            with patch.object(gui, "user_dir", return_value=base):
                reopened = gui.AnaChromaApp()
        else:
            reopened = gui.FreedaApp(settings_path=base / "settings.json", program_dir=base)
        try:
            reopened.update()
            assert reopened.language == "en"
            assert not reopened.use_program_output.get()
            assert reopened._effective_output() == base / "custom-output"
            assert reopened.size_var.get() == ("2048 lange Seite" if app_name == "AnaChroma" else "2048")
            if app_name == "AnaChroma":
                assert not reopened.recursive.get() and reopened.inputs is None
                assert reopened.settings.last_input == str(base)
            else:
                assert not reopened.include_subfolders_var.get() and not reopened.items
                assert reopened.last_input_dir == base
            print(app_name, "restart restores language and separate dialog/output preferences, resets processing to 2048, and does not reopen old inputs")
        finally:
            if app_name == "AnaChroma":
                reopened.close()
                end = time.monotonic()+5
                while time.monotonic()<end:
                    try:
                        reopened.update()
                        if not reopened.winfo_exists():
                            break
                    except gui.tk.TclError:
                        break
                    time.sleep(.01)
            else:
                reopened.destroy()
