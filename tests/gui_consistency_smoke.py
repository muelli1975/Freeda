"""Shared Stereo-Tools output, dialog and processing-state checks."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import customtkinter as ctk
from PIL import Image
from freeda.gui import FreedaApp
from freeda.theme import GOLD, TEXT, TEXT_DISABLED


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    input_dir = root / "input"
    input_dir.mkdir()
    source = input_dir / "one.png"
    Image.new("RGB", (600, 200), "red").save(source)
    output_dir = root / "custom"
    output_dir.mkdir()
    app = FreedaApp(language="de", settings_path=root / "settings.json")
    app.withdraw()
    try:
        assert not app.use_input_output.get()
        assert app.output_dir == app.program_dir / "output"
        assert app.subfolders_checkbox.cget("text") == "Unterordner mitverarbeiten"
        assert app.output_checkbox.cget("text") == "Unterordner im Input-Ordner verwenden"
        with patch("freeda.gui.filedialog.askopenfilenames", return_value=[str(source)]):
            app.choose_files()
        with patch("freeda.gui.filedialog.askdirectory", return_value=str(output_dir)):
            app.choose_output()
        assert not app.use_input_output.get()
        assert app.custom_output_status.cget("text") == str(output_dir)
        assert app.custom_output_status.cget("text_color") == TEXT
        app.use_input_output.set(True)
        app._refresh_output()
        assert app.custom_output_status.cget("text") == str(output_dir)
        assert app.custom_output_status.cget("text_color") == TEXT_DISABLED
        assert app.output_status.cget("text") == str(input_dir / "output")
        with patch("freeda.gui.filedialog.askopenfilenames", return_value=[str(source)]) as dialog:
            app.choose_files()
            assert dialog.call_args.kwargs["initialdir"] == str(input_dir)
        assert app.use_input_output.get() and app.output_dir == output_dir
        with patch("freeda.gui.filedialog.askdirectory", return_value="") as dialog:
            app.choose_output()
            assert dialog.call_args.kwargs["initialdir"] == str(output_dir)
        with patch("freeda.gui.filedialog.askdirectory", return_value="") as dialog:
            app.choose_folder()
            assert dialog.call_args.kwargs["initialdir"] == str(input_dir)

        app.frame_var.set(0)
        app._frame_changed(0)
        original_preset_state = app.preset_menu.cget("state")
        app._set_busy(True)
        assert app._control_states
        assert all(widget.cget("state") == "disabled" for widget in app._control_states
                   if not isinstance(widget, ctk.CTkSegmentedButton))
        assert app.output_checkbox.cget("fg_color") == TEXT_DISABLED
        assert all(widget.cget("button_color") == TEXT_DISABLED
                   for widget in app._control_states if isinstance(widget, ctk.CTkSlider))
        app._set_busy(True)  # repeated calls must not replace saved states
        app._set_busy(False)
        assert app.output_checkbox.cget("state") == "normal"
        assert app.output_checkbox.cget("fg_color") == GOLD
        assert app.preset_menu.cget("state") == original_preset_state
        assert app.show_symbols_checkbox.cget("state") == "disabled"
        assert app.start_button.cget("state") == "normal"
        app.mode_selector.set("Print")
        next(child for child in app.mode_selector.winfo_children()
             if isinstance(child, ctk.CTkButton) and child.cget("text") == "Web").invoke()
        assert app.mode_var.get() == "Web"
        app._language_changed("English")
        assert app.output_checkbox.cget("text") == "Use subfolder in input folder"
        assert app.tr("Horizontal: 50 %") == "Horizontal position: 50 %"
    finally:
        app.destroy()

print("Stereo-Tools output, separate dialog memories and processing-state checks passed")
