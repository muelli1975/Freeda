"""New 1.1 controls: templates, physical margins, migration and language."""
import sys
import tempfile
from pathlib import Path
from dataclasses import replace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from freeda.gui import FreedaApp, CropDialog, _PRESET_VARIABLES, _NEW_PRESET_VARIABLES
from freeda.print_layout import print_layout
from freeda.models import EyeShape, PrintMargins

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    app = FreedaApp(language="de", settings_path=root / "settings.json")
    app.withdraw()
    try:
        assert app.caption_size_var.get() == 4
        assert not app.print_precision.winfo_manager()
        assert app._web_options().eye_shape == EyeShape.ROUNDED
        assert app.image_radius_controls.winfo_manager() == 'grid'
        app.inner_radius_var.set('5')
        app.outer_radius_var.set('2')
        app.eye_shape_var.set('Rechteckig');app._layout_changed()
        assert not app.image_radius_controls.winfo_manager()
        assert app.outer_radius_entry.cget('state') == 'normal'
        assert app._web_options().inner_radius_percent == 0
        assert app._web_options().outer_radius_percent == 2
        app.inner_radius_var.set('nan')
        assert app._web_options().inner_radius_percent == 0
        app.eye_shape_var.set('Nur obere Ecken gerundet');app._layout_changed()
        assert app.image_radius_controls.winfo_manager() == 'grid'
        try:
            app._web_options()
            raise AssertionError('An active NaN radius was accepted')
        except ValueError:
            pass
        app.inner_radius_var.set('0');app.outer_radius_var.set('0')
        app.eye_shape_var.set('Alle Ecken gerundet');app._layout_changed()
        old = {key: getattr(app,key).get() for key in _PRESET_VARIABLES if key not in _NEW_PRESET_VARIABLES}
        app.mode_var.set("Print")
        app._mode_changed("Print")
        app.caption_unit_var.set('Punkt (pt)');app.caption_points_var.set('nan')
        app.caption_gap_top_var.set('nan');app.caption_gap_bottom_var.set('nan')
        assert not app._print_options().caption
        app.caption_var.set('Text')
        try:
            app._print_options()
            raise AssertionError('Active invalid text settings were accepted')
        except ValueError:
            pass
        app.caption_unit_var.set('Prozent');app.caption_points_var.set('9')
        app.caption_gap_top_var.set('');app.caption_gap_bottom_var.set('')
        colours = (app.frame_color_var.get(),app.accent_color_var.get())
        app.caption_var.set("Freiburg")
        app.card_template_var.set("Holmes-Karte")
        app._card_template_changed("Holmes-Karte")
        card = print_layout(app._print_options())
        assert abs(card.eye_width_mm-76.2)<1e-8 and abs(card.eye_height_mm-76.2)<1e-8
        assert (app.frame_color_var.get(),app.accent_color_var.get()) == colours
        assert app.caption_var.get() == "Freiburg"
        assert app.frame_slider.cget("state") == "disabled"
        assert app.inner_radius_entry.cget("state") == "disabled"
        assert not app.show_symbols_var.get()
        assert "76.20" in app.print_geometry_label.cget("text")
        assert 'Vorlage angepasst' not in app.print_geometry_label.cget('text')
        app.margin_row_gap_var.set('nan');app._layout_changed()
        assert app._print_options().margins.row_gap_mm == 0
        assert not app.row_gap_controls.winfo_manager()
        assert 'Vorlage angepasst' not in app.print_geometry_label.cget('text')
        app.layout_var.set('Parallelblick + Kreuzblick');app._layout_changed()
        try:
            app._print_options()
            raise AssertionError('An active NaN row gap was accepted')
        except ValueError:
            pass
        app.margin_row_gap_var.set('3');app.margin_top_var.set('0');app._layout_changed()
        assert app.show_symbols_checkbox.cget('state') == 'normal'
        app.layout_var.set('Parallelblick');app._layout_changed()
        assert app.show_symbols_checkbox.cget('state') == 'disabled'
        app.margin_top_var.set('3.2');app._layout_changed()
        assert not app.print_precision.winfo_manager()
        app._toggle_print_precision()
        assert app.print_precision.winfo_manager() == "grid"
        app.margin_side_var.set("12,9")
        app._layout_changed()
        assert "Vorlage angepasst" in app.print_geometry_label.cget("text")
        app._reset_card_template()
        assert app._print_options().margins.side_mm == 11.9
        app.caption_unit_var.set("Punkt (pt)")
        app.caption_points_var.set("9,5")
        app._layout_changed()
        assert app._print_options().caption_points == 9.5
        assert app.caption_slider.cget("state") == "disabled"
        app._set_busy(True)
        app._set_busy(False)
        assert app.frame_slider.cget("state") == "disabled"
        assert app.caption_slider.cget("state") == "disabled"
        app.save_preset("Holmes")
        app.presets["Legacy"] = old
        app.apply_preset("Legacy")
        assert app.mode_var.get() == "Web"
        assert app.margin_mode_var.get() == "Proportional"
        assert app.card_template_var.get() == "Freies Layout"
        assert app.eye_shape_var.get() == "Alle Ecken gerundet"
        app.apply_preset("Holmes")
        assert app._print_options().margins == PrintMargins(11.9,3.2,1.6,9.5)
        assert app.caption_unit_var.get() == "Punkt (pt)"
        # Conversion retains the current crop geometry, including two rows.
        app.card_template_var.set("Freies Layout")
        app._card_template_changed("Freies Layout")
        app.layout_var.set("Parallelblick + Kreuzblick")
        before = print_layout(app._print_options())
        app._margin_mode_changed("Exakte Ränder in mm")
        after = print_layout(app._print_options())
        assert abs(before.eye_height_mm-after.eye_height_mm)<.001
        assert abs(before.eye_width_mm-after.eye_width_mm)<.001
        assert abs(before.y_mm[-1]-after.y_mm[-1])<.001
        app._language_changed("English")
        assert app.outer_radius_label.cget('text') == 'Outer radius % of total width'
        assert app.inner_radius_label.cget('text') == 'Image radius % of view width'
        assert "Image windows" in app.print_geometry_label.cget("text")
        assert app.tr("Creme") == "Cream"
        # Invalid edited fields block an export and appear in the English summary.
        app.margin_bottom_var.set("nan")
        app._layout_changed()
        assert "Margins:" in app.print_geometry_label.cget("text")
        try:
            app._print_options()
            raise AssertionError("Invalid margins were accepted")
        except ValueError:
            pass
        app.apply_preset("Holmes")
        for shape in ("Nur obere Ecken gerundet","Klassischer Bogen"):
            app.eye_shape_var.set(shape)
            app.inner_radius_var.set("5")
            app._layout_changed()
            dialog = CropDialog(app,Image.new("RGB",(600,200),"red"),app._print_options(),index=1,total=1,filename="test.png",editing=True)
            dialog.withdraw()
            dialog.grid_var.set(True)
            dialog.update_preview()
            assert dialog.preview_photo is not None
            dialog.destroy()
    finally:
        app.destroy()

print("1.1 templates, exact margins, preset migration, contours and English controls passed")
