from __future__ import annotations

# Shared Stereo-Tools palette, kept in sync with SplatTricia.
BG_MAIN = "#111111"
BG_SOFT = "#181818"
PANEL = "#202020"
PANEL_HOVER = "#282828"
BORDER = "#333333"

TEXT = "#f2f2f2"
TEXT_MUTED = "#b8b8b8"
TEXT_DISABLED = "#727272"

GOLD = "#9c7c38"
GOLD_LIGHT = "#c6a95e"

INPUT_BG = BG_SOFT
BUTTON_BG = BG_SOFT
BUTTON_HOVER = PANEL_HOVER

SLIDER_TRACK = BORDER
SLIDER_PROGRESS = GOLD
SLIDER_BUTTON = GOLD_LIGHT
SLIDER_BUTTON_HOVER = GOLD_LIGHT
SLIDER_DISABLED_PROGRESS = BORDER
SLIDER_DISABLED_BUTTON = TEXT_DISABLED
CHECKBOX_DISABLED = TEXT_DISABLED
PROGRESS_TRACK = BORDER

START_BG = BUTTON_BG
START_HOVER_BG = GOLD_LIGHT
START_TEXT = GOLD_LIGHT
START_HOVER_TEXT = BG_MAIN
START_BORDER = GOLD
START_HOVER_BORDER = GOLD_LIGHT
START_DISABLED_BG = BUTTON_BG
START_DISABLED_TEXT = TEXT_DISABLED
START_DISABLED_BORDER = BORDER

LANGUAGE_BG = PANEL
LANGUAGE_BUTTON_BG = PANEL_HOVER
LANGUAGE_HOVER = BORDER
LANGUAGE_DROPDOWN_BG = BG_SOFT
LANGUAGE_DROPDOWN_HOVER = PANEL_HOVER

DANGER = "#7f3939"
DANGER_HOVER = "#944545"

PREVIEW_BG = "#000000"

FONT_FAMILY = "Segoe UI"
RADIUS_CONTROL = 8
RADIUS_PANEL = 12
BORDER_WIDTH = 1

# Backward-compatible names used by the initial Freeda code.
APP_BG = BG_MAIN
SECONDARY_BG = BG_SOFT
PANEL_BG = PANEL
HOVER_BG = PANEL_HOVER
TEXT_PRIMARY = TEXT
TEXT_SECONDARY = TEXT_MUTED
GOLD_DARK = GOLD
CONTROL_RADIUS = RADIUS_CONTROL
PANEL_RADIUS = RADIUS_PANEL


def configure_theme():
    """Use the Stereo-Tools palette for explicit and inherited widget colors."""
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    styles = {
        "CTk": dict(fg_color=BG_MAIN),
        "CTkToplevel": dict(fg_color=BG_MAIN),
        "CTkFrame": dict(fg_color=BG_SOFT, top_fg_color=PANEL, border_color=BORDER),
        "CTkScrollableFrame": dict(label_fg_color=BG_SOFT),
        "CTkLabel": dict(text_color=TEXT),
        "CTkEntry": dict(fg_color=INPUT_BG, border_color=BORDER, text_color=TEXT,
                         placeholder_text_color=TEXT_MUTED, corner_radius=RADIUS_CONTROL),
        "CTkButton": dict(fg_color=BUTTON_BG, hover_color=BUTTON_HOVER, border_color=BORDER,
                          border_width=BORDER_WIDTH, text_color=TEXT,
                          text_color_disabled=TEXT_DISABLED, corner_radius=RADIUS_CONTROL),
        "CTkCheckBox": dict(fg_color=GOLD, hover_color=GOLD_LIGHT, border_color=BORDER,
                            text_color=TEXT, text_color_disabled=TEXT_DISABLED, checkmark_color=TEXT),
        "CTkOptionMenu": dict(fg_color=PANEL, button_color=PANEL_HOVER, button_hover_color=BORDER,
                              text_color=TEXT, text_color_disabled=TEXT_DISABLED, corner_radius=RADIUS_CONTROL),
        "DropdownMenu": dict(fg_color=BG_SOFT, hover_color=PANEL_HOVER, text_color=TEXT),
        "CTkSegmentedButton": dict(fg_color=BORDER, selected_color=GOLD, selected_hover_color=GOLD_LIGHT,
                                   unselected_color=BG_SOFT, unselected_hover_color=PANEL_HOVER,
                                   text_color=TEXT, text_color_disabled=TEXT_DISABLED),
        "CTkSlider": dict(fg_color=BORDER, progress_color=GOLD, button_color=GOLD_LIGHT,
                          button_hover_color=GOLD_LIGHT),
        "CTkProgressBar": dict(fg_color=BORDER, progress_color=GOLD, border_color=BORDER),
        "CTkScrollbar": dict(button_color=BORDER, button_hover_color=PANEL_HOVER),
    }
    for name, style in styles.items():
        ctk.ThemeManager.theme[name].update(style)
