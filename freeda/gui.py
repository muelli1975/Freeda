from __future__ import annotations

import threading
from queue import Queue, Empty
import json
import math
import tkinter as tk
from dataclasses import replace
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw

from . import __version__
from .batch import discover_files, run_batch
from .jobs import Cancelled, check_cancel
from .print_flow import CropBatchMode
from .cropping import parse_aspect, fit_linked_crop
from .crop_storage import load_crops, save_crop
from .crop_grid import crop_grid
from .config import (
    APP_NAME,
    COLOR_PRESETS,
    DEFAULT_ACCENT_COLOR,
    DEFAULT_COLOR_PRESET,
    DEFAULT_FRAME_COLOR,
    LAYOUTS,
    OUTPUT_FORMATS,
    PRINT_FORMAT_PRESETS,
    CARD_TEMPLATES,
    WEB_SIZE_PRESETS,
)
from .fonts import available_fonts
from .presets import ROUNDED_RECTANGLE, migrate_contour
from .i18n import translate
from .models import DEFAULT_LOGO_HEIGHT_PERCENT, BatchItem, CaptionMode, Crop, CuttingGuide, EyeShape, LayoutMode, OutputFormat, PrintMargins, PrintRenderOptions, WebRenderOptions
from .logos import import_logo, resolve_logo, load_logo
from .print_layout import print_layout
from .notifications import play_ready_sound
from .output import export_targets

from .print_render import crop_for_aspect, print_eye_aspect, render_print
from .preview import fit_preview, parse_bleed, parse_dpi, print_preview_options, print_preview_image, preview_export_image
from .render import render_web, split_full_sbs, web_geometry, _font, _fit_lrl_caption
from .resources import resource_path, portable_settings_path
from .window import fit_window
from .theme import (
    BG_MAIN,
    BG_SOFT,
    BORDER,
    BORDER_WIDTH,
    BUTTON_BG,
    BUTTON_HOVER,
    FONT_FAMILY,
    GOLD,
    GOLD_LIGHT,
    INPUT_BG,
    PANEL,
    PANEL_HOVER,
    PREVIEW_BG,
    PROGRESS_TRACK,
    RADIUS_CONTROL,
    RADIUS_PANEL,
    SLIDER_BUTTON,
    SLIDER_BUTTON_HOVER,
    SLIDER_PROGRESS,
    SLIDER_TRACK,
    START_BG,
    START_BORDER,
    START_DISABLED_BG,
    START_DISABLED_BORDER,
    START_DISABLED_TEXT,
    START_HOVER_BG,
    START_HOVER_BORDER,
    START_HOVER_TEXT,
    START_TEXT,
    TEXT,
    TEXT_DISABLED,
    TEXT_MUTED,
)

ctk.set_appearance_mode("dark")

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 860
SIDEBAR_WIDTH = 390

_LAYOUT_TO_MODE = {
    "Parallelblick + Kreuzblick": LayoutMode.BOTH,
    "Parallelblick": LayoutMode.PARALLEL,
    "Kreuzblick": LayoutMode.CROSS,
    "L–R–L": LayoutMode.LRL,
}

_CUTTING_GUIDES = {
    "Keine": CuttingGuide.NONE,
    "Schneidelinie": CuttingGuide.LINE,
    "Schnittmarken": CuttingGuide.MARKS,
}

_CROP_MODES = {
    "Jedes Bild manuell": CropBatchMode.MANUAL_EACH,
    "Gleichen Ausschnitt verwenden": CropBatchMode.REUSE,
}

_EYE_SHAPES = {ROUNDED_RECTANGLE: EyeShape.ROUNDED, "Klassischer Bogen": EyeShape.ARCH}

_NEW_PRESET_VARIABLES = (
    "eye_shape_var", "arch_height_var", "card_template_var", "margin_mode_var",
    "margin_side_var", "margin_top_var", "margin_centre_var", "margin_bottom_var", "margin_row_gap_var",
    "caption_unit_var", "caption_points_var", "caption_gap_top_var", "caption_gap_bottom_var",
    "caption_mode_var", "logo_var", "logo_name_var", "logo_height_var", "logo_unit_var", "logo_mm_var",
    "print_review_var",
    "bottom_radius_var",
)

_PRESET_VARIABLES = (
    "mode_var", "layout_var", "size_var", "custom_width_var", "print_format_var",
    "print_width_var", "print_height_var", "dpi_var", "bleed_var", "show_bleed_var",
    "crop_mode_var", "cutting_var", "frame_var", "outer_radius_var", "inner_radius_var",
    "color_preset_var", "frame_color_var", "accent_color_var", "font_var",
    "caption_size_var", "format_var", "aspect_var", "custom_aspect_var",
    "web_crop_mode_var", "web_review_var",
    "show_symbols_var",
) + _NEW_PRESET_VARIABLES


class LocalisedUI:
    def tr(self, text):
        if text == "PNG":
            text = "PNG (mit Transparenz)"
        return translate(text, self.language)

    def _set_text(self, widget, text):
        self._texts[widget] = text
        widget.configure(text=self.tr(text))

    def _remember_texts(self, root):
        for widget in root.winfo_children():
            if isinstance(widget, (ctk.CTkLabel, ctk.CTkButton, ctk.CTkCheckBox)):
                self._texts.setdefault(widget, widget.cget("text"))
            elif isinstance(widget, ctk.CTkEntry):
                self._placeholders.setdefault(widget, widget.cget("placeholder_text"))
            self._remember_texts(widget)

    def _apply_language(self):
        for widget, text in self._texts.items():
            if widget.winfo_exists():
                widget.configure(text=self.tr(text))
        for widget, text in self._placeholders.items():
            widget.configure(placeholder_text=self.tr(text))
        for menu, variable, display, values in getattr(self, "_localized_options", []):
            menu.configure(values=[self.tr(v) for v in values])
            display.set(self.tr(variable.get()))


class CropDialog(LocalisedUI, ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        source: Image.Image,
        options: PrintRenderOptions,
        *,
        index: int,
        total: int,
        filename: str,
        editing: bool = False,
    ) -> None:
        super().__init__(parent, fg_color=BG_MAIN)
        self.language = parent.language
        self._texts, self._placeholders = {}, {}
        self.title(self.tr(f"Freeda – Ausschnitt {index}/{total}"))
        fit_window(self, (1080, 760), (900, 650))
        self.transient(parent)
        self.grab_set()

        self.source = source.copy()
        self.options = options
        self.editing = editing
        self.result: Crop | None = None
        self.action = "cancel"
        self.preview_photo = None
        self._preview_job = None

        self.grid_var = tk.BooleanVar(value=True)
        self.zoom_var = tk.DoubleVar(value=1.0)
        self.x_var = tk.DoubleVar(value=0.5)
        self.y_var = tk.DoubleVar(value=0.5)
        if options.crop != Crop():
            left, _ = split_full_sbs(source)
            base = crop_for_aspect(left.size, self._target_aspect())
            crop = options.crop.clamped()
            self.zoom_var.set(max(1.0, min(3.0, min(base.width/crop.width, base.height/crop.height))))
            self.x_var.set(crop.x / max(1e-9, 1-crop.width))
            self.y_var.set(crop.y / max(1e-9, 1-crop.height))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0, fg_color=BG_SOFT)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text=f"Bild {index} von {total} — {filename}",
            anchor="w",
            text_color=TEXT,
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", padx=22, pady=(14, 3))
        ctk.CTkLabel(
            header,
            text="Der Ausschnitt wird identisch auf linkes und rechtes Halbbild angewendet.",
            anchor="w",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        ).grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 14))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=18)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, minsize=300)
        body.grid_rowconfigure(0, weight=1)

        preview = ctk.CTkFrame(
            body,
            fg_color=PREVIEW_BG,
            border_width=BORDER_WIDTH,
            border_color=BORDER,
            corner_radius=RADIUS_PANEL,
        )
        preview.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        preview.grid_columnconfigure(0, weight=1)
        preview.grid_rowconfigure(0, weight=1)
        self.preview_label = tk.Label(preview, bg=PREVIEW_BG, fg=TEXT_MUTED)
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        self.preview_label.bind("<Configure>", lambda _e: self.schedule_preview())

        controls = ctk.CTkScrollableFrame(
            body,
            width=280,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=PANEL_HOVER,
            fg_color=PANEL,
            border_width=BORDER_WIDTH,
            border_color=BORDER,
            corner_radius=RADIUS_PANEL,
        )
        controls.grid(row=0, column=1, sticky="nsew")
        controls.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            controls,
            text="Ausschnitt",
            anchor="w",
            text_color=TEXT,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 14))

        self.zoom_label = self._slider_block(
            controls, 1, "Zoom", self.zoom_var, 1.0, 3.0, self._controls_changed
        )
        self.x_label = self._slider_block(
            controls, 2, "Horizontal", self.x_var, 0.0, 1.0, self._controls_changed
        )
        self.y_label = self._slider_block(
            controls, 3, "Vertikal", self.y_var, 0.0, 1.0, self._controls_changed
        )

        ctk.CTkButton(
            controls,
            text="Zurücksetzen",
            command=self._reset,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_HOVER,
            border_width=BORDER_WIDTH,
            border_color=BORDER,
            text_color=TEXT,
            corner_radius=RADIUS_CONTROL,
        ).grid(row=4, column=0, sticky="ew", padx=18, pady=(12, 8))

        buttons = ctk.CTkFrame(controls, fg_color="transparent")
        buttons.grid(row=5, column=0, sticky="sew", padx=18, pady=(18, 18))
        buttons.grid_columnconfigure(0, weight=1)

        accept = ctk.CTkButton(
            buttons,
            text="Übernehmen" if editing else ("Übernehmen & exportieren" if total == 1 else "Übernehmen & weiter"),
            command=self._accept,
            fg_color=START_BG,
            hover_color=START_HOVER_BG,
            border_width=BORDER_WIDTH,
            border_color=START_BORDER,
            text_color=START_TEXT,
            corner_radius=RADIUS_CONTROL,
        )
        accept.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        accept.bind(
            "<Enter>",
            lambda _e: accept.configure(
                fg_color=START_HOVER_BG,
                text_color=START_HOVER_TEXT,
                border_color=START_HOVER_BORDER,
            ),
            add="+",
        )
        accept.bind(
            "<Leave>",
            lambda _e: accept.configure(
                fg_color=START_BG,
                text_color=START_TEXT,
                border_color=START_BORDER,
            ),
            add="+",
        )

        for row, text, command in ((2, "Abbrechen", self._cancel),) if editing else (
            (1, "Überspringen", self._skip),
            (2, "Export abbrechen", self._cancel),
        ):
            ctk.CTkButton(
                buttons,
                text=text,
                command=command,
                fg_color=BUTTON_BG,
                hover_color=BUTTON_HOVER,
                border_width=BORDER_WIDTH,
                border_color=BORDER,
                text_color=TEXT,
                corner_radius=RADIUS_CONTROL,
            ).grid(row=row, column=0, sticky="ew", pady=(0, 8) if row == 1 else 0)

        ctk.CTkCheckBox(controls, text="Drittelraster", variable=self.grid_var,
            command=self.schedule_preview, fg_color=GOLD, hover_color=GOLD_LIGHT,
            border_color=BORDER, checkmark_color=TEXT, text_color=TEXT).grid(
                row=6,column=0,sticky="ew",padx=18,pady=(0,18))

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._refresh_labels()
        self._remember_texts(self)
        self._apply_language()
        self.after(50, self.schedule_preview)

    def _slider_block(self, parent, row, text, variable, from_, to, command):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", padx=18, pady=(0, 14))
        frame.grid_columnconfigure(0, weight=1)
        label = ctk.CTkLabel(
            frame,
            text=text,
            anchor="w",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        )
        label.grid(row=0, column=0, sticky="ew")
        ctk.CTkSlider(
            frame,
            from_=from_,
            to=to,
            variable=variable,
            command=command,
            fg_color=SLIDER_TRACK,
            progress_color=SLIDER_PROGRESS,
            button_color=SLIDER_BUTTON,
            button_hover_color=SLIDER_BUTTON_HOVER,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 0))
        return label

    def _controls_changed(self, _value=None) -> None:
        self._refresh_labels()
        self.schedule_preview()

    def _refresh_labels(self) -> None:
        decimal = "." if self.language == "en" else ","
        self._set_text(self.zoom_label, f"Zoom: {self.zoom_var.get():.2f}×".replace(".", decimal))
        self._set_text(self.x_label, f"Horizontal: {self.x_var.get() * 100:.0f} %")
        self._set_text(self.y_label, f"Vertikal: {self.y_var.get() * 100:.0f} %")

    def _reset(self) -> None:
        self.zoom_var.set(1.0)
        self.x_var.set(0.5)
        self.y_var.set(0.5)
        self._controls_changed()

    def _target_aspect(self):
        if isinstance(self.options, WebRenderOptions):
            left, _ = split_full_sbs(self.source)
            if self.options.eye_aspect is not None:
                return self.options.eye_aspect
            crop = self.options.crop.clamped()
            return left.width * crop.width / (left.height * crop.height)
        return print_eye_aspect(self.options)

    def current_crop(self) -> Crop:
        left, _ = split_full_sbs(self.source)
        return crop_for_aspect(
            left.size,
            self._target_aspect(),
            zoom=self.zoom_var.get(),
            position_x=self.x_var.get(),
            position_y=self.y_var.get(),
        )

    def schedule_preview(self) -> None:
        if self._preview_job is not None:
            try:
                self.after_cancel(self._preview_job)
            except Exception:
                pass
        self._preview_job = self.after(80, self.update_preview)

    def update_preview(self) -> None:
        self._preview_job = None
        try:
            max_w = max(1, self.preview_label.winfo_width() - 10)
            max_h = max(1, self.preview_label.winfo_height() - 10)
            if isinstance(self.options, WebRenderOptions):
                preview_options = replace(self.options, crop=self.current_crop(), target_long_edge=max(16,
                    min(max(max_w, max_h), self.options.target_long_edge or max(self.source.size))))
                rendered = render_web(self.source, preview_options)
                if self.grid_var.get():
                    rendered = crop_grid(rendered, self.source, preview_options)
                rendered = fit_preview(preview_export_image(rendered, preview_options), max_w, max_h)
            else:
                preview_options = print_preview_options(replace(self.options, crop=self.current_crop()), max_w, max_h)
                rendered = render_print(self.source, preview_options)
                if self.grid_var.get():
                    rendered = crop_grid(rendered, self.source, preview_options)
                bleed = round(preview_options.bleed_mm * preview_options.dpi / 25.4)
                trim_w = round(preview_options.width_mm * preview_options.dpi / 25.4)
                trim_h = round(preview_options.height_mm * preview_options.dpi / 25.4)
                rendered = fit_preview(preview_export_image(rendered.crop((bleed,bleed,bleed+trim_w,bleed+trim_h)), preview_options), max_w, max_h)
            self.preview_photo = ImageTk.PhotoImage(rendered)
            self.preview_label.configure(image=self.preview_photo, text="")
        except Exception as exc:
            self.preview_label.configure(image="", text=self.tr(f"Vorschaufehler:\n{exc}"))

    def _accept(self) -> None:
        self.result = self.current_crop()
        self.action = "accept"
        self.destroy()

    def _skip(self) -> None:
        self.action = "skip"
        self.destroy()

    def _cancel(self) -> None:
        self.action = "cancel"
        self.destroy()


class FreedaApp(LocalisedUI, ctk.CTk):
    def __init__(self, *, language=None, settings_path=None, program_dir=None) -> None:
        super().__init__(fg_color=BG_MAIN)
        self._texts, self._placeholders = {}, {}
        self._localized_options = []
        self.settings_path = Path(settings_path) if settings_path is not None else portable_settings_path()
        try:
            self._settings = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if not isinstance(self._settings, dict):
                self._settings = {}
        except (OSError, ValueError, AttributeError):
            self._settings = {}
        raw_presets = self._settings.get("presets", {})
        self.presets = {name: values for name, values in raw_presets.items()
                        if isinstance(name, str) and isinstance(values, dict)} if isinstance(raw_presets, dict) else {}
        saved_language = self._settings.get("language", "de")
        self.language = language or (saved_language if saved_language in ("de", "en") else "de")
        self.title(f"{APP_NAME} {__version__.removesuffix('.0')}")
        fit_window(self, (WINDOW_WIDTH, WINDOW_HEIGHT), (1120, 720))

        icon = resource_path("assets/Freeda.ico")
        if icon.is_file():
            try:
                self.iconbitmap(str(icon))
            except Exception:
                pass

        self.image_crops = {"Web": {}, "Print": {}}
        self.crop_storage_errors = []
        self.items = []
        self.sources = []
        self.source_index = 0
        self.batch_mode = False
        self.program_dir = Path(program_dir) if program_dir is not None else portable_settings_path().parent
        self.output_dir: Path | None = None
        self._events = Queue()
        self._cancel_event = threading.Event()
        self._job_id = 0
        self._active_crop_dialog = None
        self._closing = False
        self._poll_job = None
        self.last_batch_result = None
        self._folder_scan_config = None
        self._scan_running = False
        self.input_root: Path | None = None
        self.last_input_dir: Path | None = None
        self._control_states = {}
        self.preview_photo = None
        self._preview_job = None
        self._busy = False
        self._ui_ready = False

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_container = ctk.CTkFrame(self, width=SIDEBAR_WIDTH + 24, fg_color=PANEL, corner_radius=0)
        self.sidebar_container.grid_propagate(False)
        self.sidebar_container.grid(row=0, column=0, sticky="nsew")
        self.sidebar_container.grid_rowconfigure(0, weight=1)
        self.sidebar_container.grid_columnconfigure(0, weight=1)
        self.footer = ctk.CTkFrame(self.sidebar_container, fg_color=PANEL, corner_radius=0)
        self.footer.grid(row=1, column=0, sticky="ew")
        self.footer.grid_columnconfigure(0, weight=1)
        self.sidebar = ctk.CTkScrollableFrame(
            self.sidebar_container, width=SIDEBAR_WIDTH, fg_color=PANEL, corner_radius=0,
            scrollbar_button_color=BORDER, scrollbar_button_hover_color=PANEL_HOVER,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_columnconfigure(0, weight=1)

        self.preview_panel = ctk.CTkFrame(
            self,
            fg_color=PREVIEW_BG,
            corner_radius=RADIUS_PANEL,
            border_width=BORDER_WIDTH,
            border_color=BORDER,
        )
        self.preview_panel.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self.preview_panel.grid_rowconfigure(0, weight=1)
        self.preview_panel.grid_columnconfigure(0, weight=1)

        self.preview_label = tk.Label(self.preview_panel, bg=PREVIEW_BG, fg=TEXT_MUTED)
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        self.preview_label.bind("<Configure>", lambda _e: self.schedule_preview())
        self.preview_note = ctk.CTkLabel(self.preview_panel, text="", text_color=TEXT_MUTED)
        self.preview_note.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))

        self._build_sidebar()
        self._ui_ready = True
        self._preset_extension_defaults = {key: getattr(self, key).get() for key in _NEW_PRESET_VARIABLES}
        self._refresh_layout_controls()
        self._refresh_print_summary()
        self.bind("<Prior>", lambda e: self.navigate(-1))
        self.bind("<Next>", lambda e: self.navigate(1))
        self._remember_texts(self)
        self._apply_language()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._poll_job = self.after(30, self._poll_events)

    def _label(self, parent, text, *, section=False):
        return ctk.CTkLabel(
            parent,
            text=text,
            anchor="w",
            text_color=TEXT if section else TEXT_MUTED,
            font=(FONT_FAMILY, 15 if section else 13, "bold" if section else "normal"),
        )

    def _button(self, parent, text, command, *, primary=False):
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            corner_radius=RADIUS_CONTROL,
            fg_color=START_BG if primary else BUTTON_BG,
            hover_color=START_HOVER_BG if primary else BUTTON_HOVER,
            border_width=BORDER_WIDTH,
            border_color=START_BORDER if primary else BORDER,
            text_color=START_TEXT if primary else TEXT,
            text_color_disabled=TEXT_DISABLED,
        )
        if primary:
            button.bind("<Enter>", lambda _e: self._set_start_button_hover(), add="+")
            button.bind("<Leave>", lambda _e: self._set_start_button_normal(), add="+")
        return button

    def _entry(self, parent, variable, placeholder=""):
        return ctk.CTkEntry(
            parent,
            textvariable=variable,
            fg_color=INPUT_BG,
            border_color=BORDER,
            text_color=TEXT,
            placeholder_text=placeholder,
            placeholder_text_color=TEXT_MUTED,
            corner_radius=RADIUS_CONTROL,
        )

    def _font_picker(self, parent):
        button = self._button(parent, self.font_var.get(), self._open_fonts)
        self.font_var.trace_add("write", lambda *_: button.configure(text=self.font_var.get()))
        return button

    def _font_preview(self, name):
        text = self.caption_var.get().strip() or "Aa – Freeda 123"
        font = _font(name, 24)
        text, font = _fit_lrl_caption(text, font, name, 364, shrink=False)
        image = Image.new("RGB", (380, 70), BG_MAIN)
        box = font.getbbox(text)
        ImageDraw.Draw(image).text((8 - box[0], (70 - box[3] + box[1]) / 2 - box[1]),
                                  text, font=font, fill=TEXT)
        return image, text

    def _open_fonts(self):
        dialog = ctk.CTkToplevel(self, fg_color=BG_MAIN)
        dialog.title(self.tr("Untertitelschrift"))
        dialog.geometry("420x520")
        dialog.transient(self)
        dialog.grab_set()
        search = tk.StringVar()
        entry = self._entry(dialog, search)
        entry.pack(fill="x", padx=14, pady=14)
        sample = tk.Label(dialog, bg=BG_MAIN, fg=TEXT)
        sample.pack(fill="x", padx=14, pady=(0, 10))
        def show_sample(name):
            image, sample.display_text = self._font_preview(name)
            sample.photo = ImageTk.PhotoImage(image)
            sample.configure(image=sample.photo)
        show_sample(self.font_var.get())
        listing = ctk.CTkScrollableFrame(dialog, fg_color=PANEL,
            scrollbar_button_color=BORDER, scrollbar_button_hover_color=PANEL_HOVER)
        listing.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        names = available_fonts()
        def choose(name):
            self.font_var.set(name)
            dialog.destroy()
            self.schedule_preview()
        def populate(*_):
            for widget in listing.winfo_children():
                widget.destroy()
            listing._parent_canvas.yview_moveto(0)
            for name in names:
                if search.get().casefold() in name.casefold():
                    button = self._button(listing, name, lambda n=name: choose(n))
                    button.pack(fill="x", pady=2)
                    button.bind("<Enter>", lambda e, n=name: show_sample(n), add="+")
        search.trace_add("write", populate)
        populate()
        entry.focus_set()

    def _refresh_navigation(self):
        if not hasattr(self, "previous_button"):
            return
        count = len(self.sources)
        self.previous_button.configure(state="normal" if not self._busy and self.source_index > 0 else "disabled")
        self.next_button.configure(state="normal" if not self._busy and self.source_index + 1 < count else "disabled")
        if count:
            prefix = self.tr("Batch-Vorschau") if self.batch_mode else self.tr("Einzelbild-Vorschau")
            self.navigation_status.configure(text=f"{prefix}: {self.source_index + 1}/{count} · {self.sources[self.source_index].relative_path}")
        else:
            self.navigation_status.configure(text="")

    def navigate(self, offset):
        target = self.source_index + offset
        if self._busy or not 0 <= target < len(self.sources):
            return "break"
        self.source_index = target
        if not self.batch_mode:
            self.items = [self.sources[target]]
        self._refresh_navigation()
        self._refresh_output()
        self.schedule_preview()
        return "break"

    def _option(self, parent, variable, values, command=None):
        values = tuple(values)
        display = tk.StringVar(value=self.tr(variable.get()))
        def selected(value):
            canonical = next(v for v in values if self.tr(v) == value)
            variable.set(canonical)
            if command:
                command(canonical)
        variable.trace_add("write", lambda *_: display.set(self.tr(variable.get())))
        menu = ctk.CTkOptionMenu(
            parent,
            variable=display,
            values=[self.tr(v) for v in values],
            command=selected,
            fg_color=PANEL,
            button_color=PANEL_HOVER,
            button_hover_color=BORDER,
            dropdown_fg_color=BG_SOFT,
            dropdown_hover_color=PANEL_HOVER,
            dropdown_text_color=TEXT,
            text_color=TEXT,
            text_color_disabled=TEXT_DISABLED,
            corner_radius=RADIUS_CONTROL,
        )
        self._localized_options.append((menu, variable, display, values))
        return menu

    def _checkbox(self, parent, text, variable, command=None):
        return ctk.CTkCheckBox(parent, text=text, variable=variable, command=command,
                              fg_color=GOLD, hover_color=GOLD_LIGHT, border_color=BORDER,
                              checkmark_color=TEXT, text_color=TEXT, text_color_disabled=TEXT_DISABLED,
                              corner_radius=4)

    def _language_changed(self, value):
        self.language = "en" if value == "English" else "de"
        self.language_var.set("English" if self.language == "en" else "Deutsch")
        self._apply_language()
        self._refresh_output()
        self._refresh_start()
        self.schedule_preview()
        self._settings["language"] = self.language
        try:
            self._persist_settings()
        except OSError:
            self._set_text(self.status, "Einstellungen konnten nicht gespeichert werden.")

    def _persist_settings(self):
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.settings_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self._settings, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.settings_path)

    def save_preset(self, name):
        name = name.strip()
        if not name:
            raise ValueError(self.tr("Bitte einen Preset-Namen eingeben."))
        if self.mode_var.get() == "Print":
            self._print_options(allow_pending_logo=True)
        else:
            self._web_options(allow_pending_logo=True)
        values = {key: getattr(self, key).get() for key in _PRESET_VARIABLES}
        previous = dict(self.presets)
        self.presets[name] = values
        self._settings["presets"] = self.presets
        try:
            self._persist_settings()
        except OSError:
            self.presets = previous
            self._settings["presets"] = previous
            raise
        self.preset_menu.configure(values=sorted(self.presets, key=str.casefold), state="normal")
        self.preset_var.set(name)
        self._set_text(self.status, "Preset gespeichert")

    def choose_preset_name(self):
        if self._busy:
            return
        dialog = ctk.CTkToplevel(self, fg_color=BG_MAIN)
        dialog.title(self.tr("Preset speichern"))
        fit_window(dialog, (440, 210), (380, 180))
        dialog.transient(self)
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)
        self._label(dialog, self.tr("Name des Presets")).grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        name_var = tk.StringVar(value="")
        entry = self._entry(dialog, name_var)
        entry.grid(row=1, column=0, sticky="ew", padx=20)
        def save():
            try:
                self.save_preset(name_var.get())
            except (OSError, ValueError) as exc:
                messagebox.showerror("Freeda", self.tr(str(exc)), parent=dialog)
                return
            dialog.destroy()
        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        buttons.grid_columnconfigure((0, 1), weight=1)
        self._button(buttons, self.tr("Speichern"), save).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self._button(buttons, self.tr("Abbrechen"), dialog.destroy).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        entry.bind("<Return>", lambda _e: save())
        dialog.bind("<Escape>", lambda _e: dialog.destroy())
        entry.focus_set()
        self.wait_window(dialog)

    def apply_preset(self, name):
        if self._busy or name not in self.presets:
            return
        values = migrate_contour(self.presets[name])
        # A 1.0 preset must not inherit exact margins or a contour from another preset.
        for key, default in self._preset_extension_defaults.items():
            if key not in values:
                getattr(self, key).set(default)
        for key in _PRESET_VARIABLES:
            if key not in values:
                continue
            variable = getattr(self, key)
            value = values[key]
            allowed = next((options for _, var, _, options in self._localized_options if var is variable), None)
            if allowed is not None and key != "font_var" and value not in allowed:
                continue
            if key == "mode_var" and value not in ("Web", "Print"):
                continue
            if isinstance(variable, tk.DoubleVar):
                if not isinstance(value, (float, int)) or not math.isfinite(value):
                    continue
                if key == "frame_var" and not 0 <= value <= 5:
                    continue
                if key == "caption_size_var" and not 1 <= value <= 8:
                    continue
                if key == "logo_height_var" and not 1 <= value <= 20:
                    continue
            elif isinstance(variable, tk.BooleanVar):
                if not isinstance(value, bool):
                    continue
            elif not isinstance(value, str):
                continue
            variable.set(value)
        self.preset_var.set(name)
        self._mode_changed(self.mode_var.get())
        self._size_changed(self.size_var.get())
        self._print_format_changed(self.print_format_var.get())
        self._color_preset_changed(self.color_preset_var.get())
        self._frame_changed(self.frame_var.get())
        self._caption_size_changed(self.caption_size_var.get())
        self._aspect_changed(self.aspect_var.get(), clear=False)
        self._refresh_layout_controls()
        self._set_text(self.status, "Preset geladen")

    def _set_start_button_normal(self) -> None:
        if not hasattr(self, "start_button"):
            return
        if self.start_button.cget("state") == "disabled":
            self._set_start_button_disabled()
            return
        self.start_button.configure(
            fg_color=START_BG,
            hover_color=START_HOVER_BG,
            text_color=START_TEXT,
            border_color=START_BORDER,
        )

    def _set_start_button_hover(self) -> None:
        if not hasattr(self, "start_button") or self.start_button.cget("state") == "disabled":
            return
        self.start_button.configure(
            fg_color=START_HOVER_BG,
            hover_color=START_HOVER_BG,
            text_color=START_HOVER_TEXT,
            border_color=START_HOVER_BORDER,
        )

    def _set_start_button_disabled(self) -> None:
        if not hasattr(self, "start_button"):
            return
        self.start_button.configure(
            fg_color=START_DISABLED_BG,
            hover_color=START_DISABLED_BG,
            text_color=START_DISABLED_TEXT,
            border_color=START_DISABLED_BORDER,
        )

    def _build_sidebar(self) -> None:
        row = 0
        ctk.CTkLabel(
            self.sidebar,
            text="Freeda",
            anchor="w",
            text_color=GOLD_LIGHT,
            font=(FONT_FAMILY, 27, "bold"),
        ).grid(row=row, column=0, sticky="ew", padx=20, pady=(20, 0))
        row += 1
        ctk.CTkLabel(
            self.sidebar,
            text="Freeview Stereo für Web und Print",
            anchor="w",
            text_color=TEXT_MUTED,
            font=(FONT_FAMILY, 12),
        ).grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 18))
        row += 1

        self._label(self.sidebar, "Sprache / Language").grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self.language_var = tk.StringVar(value="English" if self.language == "en" else "Deutsch")
        self._option(self.sidebar, self.language_var, ("Deutsch", "English"), self._language_changed).grid(
            row=row, column=0, sticky="ew", padx=20, pady=(4, 12))
        row += 1

        self._label(self.sidebar, "Eigene Presets", section=True).grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self.preset_var = tk.StringVar(value="—")
        self.preset_menu = ctk.CTkOptionMenu(self.sidebar, variable=self.preset_var,
                                           values=sorted(self.presets, key=str.casefold) or ["—"],
                                           command=self.apply_preset, fg_color=PANEL,
                                           button_color=PANEL_HOVER, button_hover_color=BORDER,
                                           dropdown_fg_color=BG_SOFT, dropdown_hover_color=PANEL_HOVER,
                                           dropdown_text_color=TEXT, text_color=TEXT,
                                           text_color_disabled=TEXT_DISABLED,
                                           corner_radius=RADIUS_CONTROL,
                                           state="normal" if self.presets else "disabled")
        self.preset_menu.grid(row=row, column=0, sticky="ew", padx=20, pady=(4, 6))
        row += 1
        self._button(self.sidebar, "Preset speichern …", self.choose_preset_name).grid(
            row=row, column=0, sticky="ew", padx=20, pady=(0, 12))
        row += 1

        self._label(self.sidebar, "Input", section=True).grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        input_buttons = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        input_buttons.grid(row=row, column=0, sticky="ew", padx=20, pady=(6, 6))
        row += 1
        input_buttons.grid_columnconfigure(0, weight=1)
        input_buttons.grid_columnconfigure(1, weight=1)
        self._button(input_buttons, "Dateien …", self.choose_files).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        self._button(input_buttons, "Ordner …", self.choose_folder).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )
        self.include_subfolders_var = tk.BooleanVar(value=False)
        self.subfolders_checkbox = self._checkbox(self.sidebar, "Unterordner mitverarbeiten", self.include_subfolders_var, self._reload_folder)
        self.subfolders_checkbox.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 8))
        row += 1
        self.input_status = self._label(self.sidebar, "Keine Bilder gewählt")
        self.input_status.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 16))
        row += 1

        self._label(self.sidebar, "Ausgabe", section=True).grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self.mode_var = tk.StringVar(value="Web")
        self.mode_selector = ctk.CTkSegmentedButton(
            self.sidebar,
            values=["Web", "Print"],
            variable=self.mode_var,
            command=self._mode_changed,
            selected_color=GOLD,
            selected_hover_color=GOLD_LIGHT,
            unselected_color=BG_SOFT,
            unselected_hover_color=PANEL_HOVER,
            text_color=TEXT,
            text_color_disabled=TEXT_DISABLED,
        )
        self.mode_selector.grid(row=row, column=0, sticky="ew", padx=20, pady=(6, 10))
        row += 1

        self.layout_var = tk.StringVar(value="Parallelblick + Kreuzblick")
        self._label(self.sidebar, "Ansicht").grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self._option(
            self.sidebar, self.layout_var, LAYOUTS, lambda _v: self._layout_changed()
        ).grid(row=row, column=0, sticky="ew", padx=20, pady=(4, 10))
        row += 1

        self.web_controls = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.web_controls.grid(row=row, column=0, sticky="ew", padx=20)
        self.web_controls.grid_columnconfigure(0, weight=1)
        row += 1
        self.web_size_label = self._label(self.web_controls, "Lange Seite (px)")
        self.web_size_label.grid(row=0, column=0, sticky="ew")
        self.size_var = tk.StringVar(value="2048")
        self.size_menu = self._option(
            self.web_controls, self.size_var, WEB_SIZE_PRESETS, self._size_changed
        )
        self.size_menu.grid(row=1, column=0, sticky="ew", pady=(4, 6))
        self.custom_width_var = tk.StringVar(value="2048")
        self.custom_width = self._entry(
            self.web_controls, self.custom_width_var, "Lange Seite in Pixeln"
        )
        self.custom_width.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.custom_width.grid_remove()
        self.custom_width.bind("<KeyRelease>", lambda _e: self.schedule_preview())

        self.aspect_var = tk.StringVar(value="Original")
        self.custom_aspect_var = tk.StringVar(value="4:3")
        self._label(self.web_controls, "Seitenverhältnis der Halbbilder").grid(row=3, column=0, sticky="ew")
        self._option(self.web_controls, self.aspect_var,
            ("Original", "1:1", "4:3", "3:2", "16:9", "3:4", "2:3", "Benutzerdefiniert"), self._aspect_changed).grid(row=4, column=0, sticky="ew", pady=(4, 6))
        self.custom_aspect_entry = self._entry(self.web_controls, self.custom_aspect_var, "Breite:Höhe, z. B. 4:3")
        self.custom_aspect_entry.grid(row=5, column=0, sticky="ew", pady=(0, 6))
        self.custom_aspect_entry.grid_remove()
        self.custom_aspect_entry.bind("<KeyRelease>", lambda e: self._aspect_changed(self.aspect_var.get()))
        self.web_crop_mode_var = tk.StringVar(value="Jedes Bild manuell")
        self._label(self.web_controls, "Bildausschnitt im Batch").grid(row=6, column=0, sticky="ew")
        self._option(self.web_controls, self.web_crop_mode_var, tuple(_CROP_MODES)).grid(row=7, column=0, sticky="ew", pady=(4, 6))
        self.web_review_var = tk.BooleanVar(value=False)
        self._checkbox(self.web_controls, "Bildausschnitt beim Export prüfen", self.web_review_var).grid(row=8, column=0, sticky="ew", pady=(0, 12))

        self.print_controls = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.print_controls.grid(row=row, column=0, sticky="ew", padx=20)
        self.print_controls.grid_columnconfigure(0, weight=1)
        row += 1

        self._label(self.print_controls, "Druckformat").grid(row=0, column=0, sticky="ew")
        self.print_format_var = tk.StringVar(value="Foto 10 × 15 cm")
        self._option(
            self.print_controls,
            self.print_format_var,
            tuple(PRINT_FORMAT_PRESETS.keys()),
            self._print_format_changed,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 6))

        self.custom_print = ctk.CTkFrame(self.print_controls, fg_color="transparent")
        self.custom_print.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.custom_print.grid_columnconfigure(0, weight=1)
        self.custom_print.grid_columnconfigure(1, weight=1)
        self.print_width_var = tk.StringVar(value="150")
        self.print_height_var = tk.StringVar(value="100")
        for col, label, var in (
            (0, "Breite mm", self.print_width_var),
            (1, "Höhe mm", self.print_height_var),
        ):
            block = ctk.CTkFrame(self.custom_print, fg_color="transparent")
            block.grid(row=0, column=col, sticky="ew", padx=(0, 4) if col == 0 else (4, 0))
            self._label(block, label).pack(fill="x")
            entry = self._entry(block, var)
            entry.pack(fill="x", pady=(3, 0))
            entry.bind("<KeyRelease>", lambda _e: self.schedule_preview())
        self.custom_print.grid_remove()

        print_pair = ctk.CTkFrame(self.print_controls, fg_color="transparent")
        print_pair.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        print_pair.grid_columnconfigure(0, weight=1)
        print_pair.grid_columnconfigure(1, weight=1)

        self.dpi_var = tk.StringVar(value="300")
        dpi_block = ctk.CTkFrame(print_pair, fg_color="transparent")
        dpi_block.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self._label(dpi_block, "Auflösung in dpi").pack(fill="x")
        self.dpi_entry = self._entry(dpi_block, self.dpi_var, "dpi")
        self.dpi_entry.pack(fill="x", pady=(3, 0))
        self.dpi_entry.bind("<KeyRelease>", lambda _e: self.schedule_preview())

        self.bleed_var = tk.StringVar(value="0")
        bleed_block = ctk.CTkFrame(print_pair, fg_color="transparent")
        bleed_block.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self._label(bleed_block, "Beschnittrand in mm").pack(fill="x")
        self.bleed_entry = self._entry(bleed_block, self.bleed_var)
        self.bleed_entry.pack(fill="x", pady=(3, 0))
        self.bleed_entry.bind("<KeyRelease>", lambda _e: self.schedule_preview())

        self.show_bleed_var = tk.BooleanVar(value=True)
        self.show_bleed_checkbox = self._checkbox(self.print_controls, "Beschnittrand in Vorschau zeigen",
                                                  self.show_bleed_var, self.schedule_preview)
        self.show_bleed_checkbox.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        self._label(self.print_controls, "Bildausschnitt im Batch").grid(row=5, column=0, sticky="ew")
        self.crop_mode_var = tk.StringVar(value="Jedes Bild manuell")
        self._option(
            self.print_controls,
            self.crop_mode_var,
            tuple(_CROP_MODES.keys()),
        ).grid(row=6, column=0, sticky="ew", pady=(3, 8))

        self.print_review_var = tk.BooleanVar(value=False)
        self._checkbox(self.print_controls, "Bildausschnitt beim Export prüfen", self.print_review_var).grid(
            row=7, column=0, sticky="ew", pady=(0, 12))

        self._label(self.print_controls, "Schneidehilfe").grid(row=8, column=0, sticky="ew")
        self.cutting_var = tk.StringVar(value="Keine")
        self._option(
            self.print_controls,
            self.cutting_var,
            tuple(_CUTTING_GUIDES.keys()),
            lambda _v: self.schedule_preview(),
        ).grid(row=9, column=0, sticky="ew", pady=(3, 12))
        self._build_print_precision()
        self.print_controls.grid_remove()

        crop_buttons = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        crop_buttons.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 12))
        row += 1
        crop_buttons.grid_columnconfigure(0, weight=1)
        self._button(crop_buttons, "Ausschnitt anpassen …", self.edit_crop).grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self._button(crop_buttons, "Ausschnitt zurücksetzen", self.reset_crop).grid(row=1, column=0, sticky="ew")
        self.remember_crops_var = tk.BooleanVar(value=False)
        self.remember_crops_checkbox = self._checkbox(crop_buttons, "Bildausschnitte merken", self.remember_crops_var, self._remember_crops_changed)
        self.remember_crops_checkbox.grid(row=2, column=0, sticky="ew", pady=(10, 4))
        remember_hint = self._label(crop_buttons, "Im Bilderordner speichern und beim Laden wiederherstellen.")
        remember_hint.configure(wraplength=300, justify="left")
        remember_hint.grid(row=3, column=0, sticky="ew")

        self._label(self.sidebar, "Rahmen", section=True).grid(
            row=row, column=0, sticky="ew", padx=20, pady=(4, 0)
        )
        row += 1
        self.frame_label = self._label(self.sidebar, "Breite: 4,00 % je Halbbild")
        self.frame_label.grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self.frame_var = tk.DoubleVar(value=4.0)
        self.frame_slider = ctk.CTkSlider(
            self.sidebar,
            from_=0.0,
            to=5.0,
            number_of_steps=100,
            variable=self.frame_var,
            command=self._frame_changed,
            progress_color=SLIDER_PROGRESS,
            button_color=SLIDER_BUTTON,
            button_hover_color=SLIDER_BUTTON_HOVER,
            fg_color=SLIDER_TRACK,
        )
        self.frame_slider.grid(row=row, column=0, sticky="ew", padx=20, pady=(2, 10))
        row += 1

        self.show_symbols_var = tk.BooleanVar(value=True)
        self.show_symbols_checkbox = self._checkbox(self.sidebar, "Blicksymbole anzeigen", self.show_symbols_var, self.schedule_preview)
        self.show_symbols_checkbox.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 10))
        row += 1

        self.image_shape_heading = self._label(self.sidebar, "Bildkontur", section=True)
        self.image_shape_heading.grid(row=row, column=0, sticky="ew", padx=20, pady=(4, 0))
        row += 1
        self.eye_shape_var = tk.StringVar(value=ROUNDED_RECTANGLE)
        self.eye_shape_menu = self._option(self.sidebar, self.eye_shape_var, tuple(_EYE_SHAPES),
                     lambda _v: self._layout_changed())
        self.eye_shape_menu.grid(row=row, column=0, sticky="ew", padx=20, pady=(4, 8))
        row += 1
        self.arch_height_var = tk.StringVar(value="18")
        self.arch_controls = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.arch_controls.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 8))
        self.arch_controls.grid_columnconfigure(0, weight=1)
        self.arch_label = self._label(self.arch_controls, "Bogenhöhe")
        self.arch_label.grid(row=0, column=0, sticky="ew")
        self.arch_slider = self._contour_slider(self.arch_controls, self.arch_height_var, .5)
        self.arch_slider.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        self._label(self.arch_controls, "% der Halbbildbreite").grid(row=2, column=0, sticky="ew", pady=(4, 0))
        self.arch_controls.grid_remove()
        row += 1

        self.image_radius_controls = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.image_radius_controls.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 10))
        row += 1
        self.image_radius_controls.grid_columnconfigure((0, 1), weight=1)
        self.inner_radius_var = tk.StringVar(value="0")
        self.inner_radius_label = self._label(self.image_radius_controls, "Radius oben")
        self.inner_radius_label.grid(row=0, column=0, sticky="ew")
        self.inner_radius_slider = self._contour_slider(self.image_radius_controls, self.inner_radius_var, .5)
        self.inner_radius_slider.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(3, 0))
        self.bottom_radius_var = tk.StringVar(value="0")
        self.bottom_radius_label = self._label(self.image_radius_controls, "Radius unten")
        self.bottom_radius_label.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self.bottom_radius_slider = self._contour_slider(self.image_radius_controls, self.bottom_radius_var, .5)
        self.bottom_radius_slider.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=(3, 0))
        self._label(self.image_radius_controls, "% der Halbbildbreite · 0: rechteckig").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        self.outer_radius_var = tk.StringVar(value="0")
        self.outer_radius_label = self._label(self.sidebar, "Radius außen")
        self.outer_radius_label.configure(wraplength=330, justify="left")
        self.outer_radius_label.grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self.outer_radius_slider = self._contour_slider(self.sidebar, self.outer_radius_var, .1)
        self.outer_radius_slider.grid(row=row, column=0, sticky="ew", padx=20, pady=(3, 0))
        row += 1
        self._label(self.sidebar, "% der Gesamtbreite").grid(row=row, column=0, sticky="ew", padx=20, pady=(4, 12))
        row += 1

        self._label(self.sidebar, "Farben", section=True).grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self.color_preset_var = tk.StringVar(value=DEFAULT_COLOR_PRESET)
        self._option(
            self.sidebar,
            self.color_preset_var,
            tuple(COLOR_PRESETS.keys()),
            self._color_preset_changed,
        ).grid(row=row, column=0, sticky="ew", padx=20, pady=(6, 6))
        row += 1

        self.custom_colors = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.custom_colors.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 12))
        row += 1
        self.custom_colors.grid_columnconfigure(0, weight=1)
        self.custom_colors.grid_columnconfigure(1, weight=1)
        self.frame_color_var = tk.StringVar(value=DEFAULT_FRAME_COLOR)
        self.accent_color_var = tk.StringVar(value=DEFAULT_ACCENT_COLOR)
        for col, label, var in (
            (0, "Rahmen", self.frame_color_var),
            (1, "Schrift / II / X", self.accent_color_var),
        ):
            block = ctk.CTkFrame(self.custom_colors, fg_color="transparent")
            block.grid(row=0, column=col, sticky="ew", padx=(0, 4) if col == 0 else (4, 0))
            self._label(block, label).pack(fill="x")
            entry = self._entry(block, var, "#rrggbb")
            entry.pack(fill="x", pady=(3, 0))
            entry.bind("<KeyRelease>", lambda _e: self.schedule_preview())
        self.custom_colors.grid_remove()

        self._label(self.sidebar, "Beschriftung", section=True).grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self.caption_mode_var = tk.StringVar(value="Text")
        self._option(self.sidebar, self.caption_mode_var, ("Text", "Logo"),
                     lambda _v: self._layout_changed()).grid(row=row, column=0, sticky="ew", padx=20, pady=(6, 6))
        row += 1
        caption_start_row = row
        self.caption_var = tk.StringVar(value="")
        caption = self._entry(self.sidebar, self.caption_var, "Optionaler Untertitel")
        caption.grid(row=row, column=0, sticky="ew", padx=20, pady=(6, 6))
        row += 1
        caption.bind("<KeyRelease>", lambda _e: self.schedule_preview())

        self._label(self.sidebar, "Untertitelschrift").grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self.font_var = tk.StringVar(value=available_fonts()[0])
        self._font_picker(self.sidebar).grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 12))
        row += 1

        self.print_caption_controls = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.print_caption_controls.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 8))
        self.print_caption_controls.grid_columnconfigure(0, weight=1)
        self.caption_unit_var = tk.StringVar(value="Prozent")
        self._option(self.print_caption_controls, self.caption_unit_var, ("Prozent", "Punkt (pt)"),
                     lambda _v: self._layout_changed()).grid(row=0, column=0, sticky="ew")
        self.caption_points_var = tk.StringVar(value="9")
        self.caption_points_entry = self._entry(self.print_caption_controls, self.caption_points_var, "Schriftgröße in pt")
        self.caption_points_entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.caption_points_entry.bind("<KeyRelease>", lambda _e: self.schedule_preview())
        self.print_caption_controls.grid_remove()
        row += 1
        self.caption_size_var = tk.DoubleVar(value=4.0)
        self.caption_size_label = self._label(self.sidebar, "Untertitelgröße: 4,00 % je Halbbild")
        self.caption_size_label.grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self.caption_slider = ctk.CTkSlider(self.sidebar, from_=1.0, to=8.0, number_of_steps=140,
                      variable=self.caption_size_var, command=self._caption_size_changed,
                      progress_color=SLIDER_PROGRESS, button_color=SLIDER_BUTTON,
                      button_hover_color=SLIDER_BUTTON_HOVER, fg_color=SLIDER_TRACK)
        self.caption_slider.grid(
            row=row, column=0, sticky="ew", padx=20, pady=(2, 12))
        row += 1

        self.caption_text_widgets = [widget for widget in self.sidebar.winfo_children()
            if widget.grid_info() and caption_start_row <= int(widget.grid_info()["row"]) < row]
        self._build_logo_controls(caption_start_row)
        self._label(self.sidebar, "Dateiformat", section=True).grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self.format_var = tk.StringVar(value="JPEG")
        self._option(
            self.sidebar, self.format_var, OUTPUT_FORMATS, lambda _v: self.schedule_preview()
        ).grid(row=row, column=0, sticky="ew", padx=20, pady=(6, 8))
        row += 1

        self.use_program_output = tk.BooleanVar(value=True)
        self.output_checkbox = self._checkbox(self.sidebar, "Unterordner im Programmordner verwenden",
                                              self.use_program_output, self._output_changed)
        self.output_checkbox.grid(
            row=row, column=0, sticky="ew", padx=20, pady=(0, 8))
        row += 1
        self.custom_output_label = self._label(self.sidebar, "Eigener Ausgabeordner")
        self.custom_output_label.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 3))
        row += 1
        self.choose_output_button = self._button(self.sidebar, "Auswählen", self.choose_output)
        self.choose_output_button.grid(
            row=row, column=0, sticky="ew", padx=20, pady=(0, 5)
        )
        row += 1
        self.custom_output_status = self._label(self.sidebar, "Kein eigener Ausgabeordner gewählt")
        self.custom_output_status.configure(wraplength=330)
        self.custom_output_status.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 8))
        row += 1
        self._label(self.sidebar, "Ausgabeziel").grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self.output_status = self._label(self.sidebar, "output im Programmordner")
        self.output_status.configure(wraplength=330)
        self.output_status.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 14))
        row += 1

        nav = ctk.CTkFrame(self.footer, fg_color="transparent")
        nav.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 8))
        nav.grid_columnconfigure((0, 1), weight=1)
        self.previous_button = self._button(nav, "◀ Vorheriges", lambda: self.navigate(-1))
        self.previous_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.next_button = self._button(nav, "Nächstes ▶", lambda: self.navigate(1))
        self.next_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self.navigation_status = self._label(self.footer, "")
        self.navigation_status.configure(wraplength=SIDEBAR_WIDTH - 40, justify="left", width=SIDEBAR_WIDTH - 40)
        self.navigation_status.grid(row=1, column=0, sticky="ew", padx=20)
        row = 2
        self.start_button = self._button(self.footer, "Bild exportieren", self.start_batch, primary=True)
        self.start_button.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 8))
        row += 1
        self.cancel_button = self._button(self.footer, "Abbrechen", self.cancel_job)
        self.cancel_button.configure(state="disabled")
        self.cancel_button.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 8))
        row += 1
        self.progress = ctk.CTkProgressBar(
            self.footer, progress_color=GOLD, fg_color=PROGRESS_TRACK
        )
        self.progress.set(0)
        self.progress.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 5))
        row += 1
        self.status = self._label(self.footer, "Bereit")
        self.status.configure(wraplength=SIDEBAR_WIDTH - 40, justify="left", width=SIDEBAR_WIDTH - 40)
        self.status.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 22))

        self._mode_changed("Web")

    def _build_print_precision(self):
        for widget in self.print_controls.winfo_children():
            info = widget.grid_info()
            if info:
                widget.grid_configure(row=int(info["row"]) + 4)
        self.custom_print.grid(row=6, column=0, sticky="ew", pady=(0, 8))
        self.custom_print.grid_remove()
        self.card_template_var = tk.StringVar(value="Freies Layout")
        self.margin_mode_var = tk.StringVar(value="Proportional")
        self._label(self.print_controls, "Kartenvorlage").grid(row=0, column=0, sticky="ew")
        self._option(self.print_controls, self.card_template_var, tuple(CARD_TEMPLATES),
                     self._card_template_changed).grid(row=1, column=0, sticky="ew", pady=(4, 6))
        self.print_geometry_label = self._label(self.print_controls, "")
        self.print_geometry_label.configure(wraplength=330, justify="left")
        self.print_geometry_label.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        self.precision_group = ctk.CTkFrame(self.print_controls, fg_color="transparent")
        self.precision_group.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        self.precision_group.grid_columnconfigure(0, weight=1)
        self.precision_button = self._button(self.precision_group, "Ränder und Bildfenster anpassen …", self._toggle_print_precision)
        self.precision_button.grid(row=0, column=0, sticky="ew")
        self.print_precision = ctk.CTkFrame(self.precision_group, fg_color=BG_SOFT, corner_radius=RADIUS_CONTROL)
        self.print_precision.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.print_precision.grid_columnconfigure(0, weight=1)
        self._label(self.print_precision, "Randberechnung").grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 3))
        self._option(self.print_precision, self.margin_mode_var, ("Proportional", "Exakte Ränder in mm"),
                     self._margin_mode_changed).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        self.margin_fields = ctk.CTkFrame(self.print_precision, fg_color="transparent")
        self.margin_fields.grid(row=2, column=0, sticky="ew", padx=12)
        self.margin_fields.grid_columnconfigure((0, 1), weight=1)
        for index, (key, label, default) in enumerate((
            ("side", "Außenrand links/rechts mm", "5"),
            ("centre", "Mittelsteg mm", "2"),
            ("top", "Oberer Rand mm", "3"),
            ("bottom", "Unterer Bereich mm", "8"),
            ("row_gap", "Abstand der Bildzeilen mm", "3"),
        )):
            variable = tk.StringVar(value=default)
            setattr(self, f"margin_{key}_var", variable)
            block = ctk.CTkFrame(self.margin_fields, fg_color="transparent")
            block.grid(row=index // 2, column=index % 2, sticky="ew", padx=(0, 4) if index % 2 == 0 else (4, 0), pady=(0, 8))
            label_widget = self._label(block, label)
            label_widget.configure(wraplength=140, justify="left")
            label_widget.pack(fill="x")
            entry = self._entry(block, variable)
            entry.pack(fill="x", pady=(3, 0))
            entry.bind("<KeyRelease>", lambda _e: self._layout_changed())
            if key == "row_gap":
                self.row_gap_controls = block
        hint = self._label(self.margin_fields, "Unterer Bereich: vom Bildrand zur Schnittkante, einschließlich Text oder Logo; bei zwei Bildzeilen je Zeile.")
        hint.configure(wraplength=300, justify="left")
        hint.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.caption_gap_top_var = tk.StringVar(value="")
        self.caption_gap_bottom_var = tk.StringVar(value="")
        for row, (text, variable) in enumerate((("Textabstand oben mm", self.caption_gap_top_var),
                                                ("Textabstand unten mm", self.caption_gap_bottom_var)), 3):
            label = self._label(self.print_precision, text)
            label.grid(row=row * 2 - 3, column=0, sticky="ew", padx=12)
            setattr(self, "caption_gap_top_label" if row == 3 else "caption_gap_bottom_label", label)
            entry = self._entry(self.print_precision, variable, "Automatisch")
            entry.grid(row=row * 2 - 2, column=0, sticky="ew", padx=12, pady=(3, 8))
            entry.bind("<KeyRelease>", lambda _e: self.schedule_preview())
        automatic_hint = self._label(self.print_precision, "Leere Textabstände: automatisch nach Schriftgröße.")
        self.caption_spacing_hint = automatic_hint
        automatic_hint.configure(wraplength=300, justify="left")
        automatic_hint.grid(row=7, column=0, sticky="ew", padx=12, pady=(0, 8))
        self.reset_template_button = self._button(self.print_precision, "Vorlage zurücksetzen", self._reset_card_template)
        self.reset_template_button.grid(row=8, column=0, sticky="ew", padx=12, pady=(0, 12))
        self.print_precision.grid_remove()
        print_hint = self._label(self.print_controls, "Beim Drucken: 100 % / tatsächliche Größe.")
        print_hint.configure(wraplength=330)
        print_hint.grid(row=14, column=0, sticky="ew", pady=(0, 12))

    def _build_logo_controls(self, row):
        self.logo_var = tk.StringVar(value="")
        self.logo_name_var = tk.StringVar(value="")
        self.logo_height_var = tk.DoubleVar(value=DEFAULT_LOGO_HEIGHT_PERCENT)
        self.logo_unit_var = tk.StringVar(value="Prozent")
        self.logo_mm_var = tk.StringVar(value="4")
        self.logo_controls = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_controls.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 12))
        self.logo_controls.grid_columnconfigure(0, weight=1)
        self._button(self.logo_controls, "Logo wählen …", self.choose_logo).grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.logo_status = self._label(self.logo_controls, "Bitte ein Logo wählen.")
        self.logo_status.configure(width=330, wraplength=330, justify="left")
        self.logo_status.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.logo_unit_menu = self._option(self.logo_controls, self.logo_unit_var, ("Prozent", "Millimeter (mm)"),
                                          lambda _v: self._layout_changed())
        self.logo_unit_menu.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        self.logo_mm_entry = self._entry(self.logo_controls, self.logo_mm_var, "Logohöhe in mm")
        self.logo_mm_entry.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        self.logo_mm_entry.bind("<KeyRelease>", lambda _e: self.schedule_preview())
        self.logo_size_label = self._label(self.logo_controls, "")
        self.logo_size_label.grid(row=4, column=0, sticky="ew")
        self.logo_slider = ctk.CTkSlider(self.logo_controls, from_=1, to=20, number_of_steps=190,
            variable=self.logo_height_var, command=lambda _v: self.schedule_preview(),
            progress_color=SLIDER_PROGRESS, button_color=SLIDER_BUTTON,
            button_hover_color=SLIDER_BUTTON_HOVER, fg_color=SLIDER_TRACK)
        self.logo_slider.grid(row=5, column=0, sticky="ew", pady=(2, 8))
        hint = self._label(self.logo_controls, "Seitenverhältnis bleibt erhalten; maximal 90 % der Halbbildbreite. Eine Kopie liegt im Programmordner logos.")
        hint.configure(wraplength=330, justify="left")
        hint.grid(row=6, column=0, sticky="ew")
        self.logo_controls.grid_remove()

    def choose_logo(self):
        if self._busy:
            return
        path = filedialog.askopenfilename(title=self.tr("Logo wählen"),
            filetypes=[(self.tr("Bilder"), "*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp"), (self.tr("Alle Dateien"), "*.*")])
        if not path:
            return
        try:
            relative = import_logo(path, self.settings_path.parent)
        except OSError:
            messagebox.showerror("Freeda", self.tr("Die Logodatei konnte nicht im Programmordner gespeichert werden."), parent=self)
            return
        except ValueError as exc:
            messagebox.showerror("Freeda", self.tr(str(exc)), parent=self)
            return
        self.logo_var.set(relative)
        self.logo_name_var.set(Path(path).name)
        self.caption_mode_var.set("Logo")
        self._layout_changed()

    def _toggle_print_precision(self):
        if self.print_precision.winfo_manager():
            self.print_precision.grid_remove()
            self._set_text(self.precision_button, "Ränder und Bildfenster anpassen …")
        else:
            self.print_precision.grid()
            self._set_text(self.precision_button, "Genaue Einstellungen einklappen")

    @staticmethod
    def _number(value, message, *, zero=False):
        try:
            number = float(value.strip().replace(",", "."))
        except (ValueError, AttributeError):
            raise ValueError(message) from None
        if not math.isfinite(number) or number < 0 or (number == 0 and not zero):
            raise ValueError(message)
        return number

    def _card_template_changed(self, name):
        template = CARD_TEMPLATES.get(name)
        if template:
            paper, margins, shape = template
            self.print_format_var.set(paper)
            self.margin_mode_var.set("Exakte Ränder in mm")
            for key in ("side", "top", "centre", "bottom", "row_gap"):
                getattr(self, f"margin_{key}_var").set(str(getattr(margins, f"{key}_mm")))
            self.layout_var.set("Parallelblick")
            self.show_symbols_var.set(False)
            self.eye_shape_var.set("Klassischer Bogen" if shape == "Klassischer Bogen" else ROUNDED_RECTANGLE)
            self.inner_radius_var.set("0")
            self.bottom_radius_var.set("0")
            self.arch_height_var.set("18")
            self.outer_radius_var.set("0")
        elif name == "Freies Layout":
            self.margin_mode_var.set("Proportional")
        elif name == "Benutzerdefiniert":
            self._margin_mode_changed("Exakte Ränder in mm")
        self._print_format_changed(self.print_format_var.get())
        self._layout_changed()

    def _reset_card_template(self):
        if not CARD_TEMPLATES.get(self.card_template_var.get()) or self._busy:
            return
        self._card_template_changed(self.card_template_var.get())
        self.caption_gap_top_var.set("")
        self.caption_gap_bottom_var.set("")
        self._layout_changed()

    def _margin_mode_changed(self, value):
        # Convert the visible proportional layout rather than jumping to arbitrary margins.
        if value == "Exakte Ränder in mm":
            try:
                current = print_layout(replace(self._print_options(validate=False, allow_pending_logo=True), margins=None))
                side = current.x_mm[0]
                bottom = current.height_mm - current.y_mm[-1] - current.eye_height_mm
                values = {"side": side, "top": current.y_mm[0], "centre": current.centre_mm,
                          "bottom": bottom, "row_gap": current.symbol_bands_mm[-1]}
                for key, number in values.items():
                    getattr(self, f"margin_{key}_var").set(f"{number:.4f}")
            except ValueError:
                pass
        self.margin_mode_var.set(value)
        self._layout_changed()

    def _layout_changed(self):
        self._refresh_layout_controls()
        self.schedule_preview()

    def _refresh_layout_controls(self):
        if not self._ui_ready:
            return
        is_print = self.mode_var.get() == "Print"
        is_logo = self.caption_mode_var.get() == "Logo"
        self.reset_template_button.configure(state="normal" if not self._busy and
                                             CARD_TEMPLATES.get(self.card_template_var.get()) else "disabled")
        for widget in self.caption_text_widgets:
            widget.grid_remove() if is_logo else widget.grid()
        self.logo_controls.grid() if is_logo else self.logo_controls.grid_remove()
        self.logo_unit_menu.grid() if is_print else self.logo_unit_menu.grid_remove()
        logo_mm = is_print and self.logo_unit_var.get() == "Millimeter (mm)"
        self.logo_mm_entry.grid() if logo_mm else self.logo_mm_entry.grid_remove()
        self.logo_status.configure(text=(self.logo_name_var.get() or Path(self.logo_var.get()).name)
                                   if self.logo_var.get() else self.tr("Bitte ein Logo wählen."))
        logo_percent = f"{self.logo_height_var.get():.2f}".replace(".", ",")
        self._set_text(self.logo_size_label, f"Max. Logohöhe: {self.logo_mm_var.get()} mm" if logo_mm else
                       f"Max. Logohöhe: {logo_percent} % je Halbbild")
        self._set_text(self.caption_gap_top_label, "Logoabstand oben mm" if is_logo else "Textabstand oben mm")
        self._set_text(self.caption_gap_bottom_label, "Logoabstand unten mm" if is_logo else "Textabstand unten mm")
        self._set_text(self.caption_spacing_hint, "Leere Logoabstände: automatisch nach Logohöhe." if is_logo else
                       "Leere Textabstände: automatisch nach Schriftgröße.")
        exact = is_print and self.margin_mode_var.get() == "Exakte Ränder in mm"
        self.margin_fields.grid() if self.margin_mode_var.get() == "Exakte Ränder in mm" else self.margin_fields.grid_remove()
        self.row_gap_controls.grid() if self.layout_var.get() == "Parallelblick + Kreuzblick" else self.row_gap_controls.grid_remove()
        self.arch_controls.grid() if self.eye_shape_var.get() == "Klassischer Bogen" else self.arch_controls.grid_remove()
        rounded = self.eye_shape_var.get() == ROUNDED_RECTANGLE
        self.image_radius_controls.grid() if rounded else self.image_radius_controls.grid_remove()
        self.print_caption_controls.grid() if is_print and not is_logo else self.print_caption_controls.grid_remove()
        points = is_print and self.caption_unit_var.get() == "Punkt (pt)"
        self.caption_points_entry.grid() if points else self.caption_points_entry.grid_remove()
        for slider, disabled in ((self.frame_slider, exact or self._busy), (self.caption_slider, points or self._busy),
                                 (self.logo_slider, logo_mm or self._busy)):
            slider.configure(state="disabled" if disabled else "normal", progress_color=BORDER if disabled else SLIDER_PROGRESS,
                             button_color=TEXT_DISABLED if disabled else SLIDER_BUTTON,
                             button_hover_color=TEXT_DISABLED if disabled else SLIDER_BUTTON_HOVER)
        self.frame_label.configure(text_color=TEXT_DISABLED if exact else TEXT_MUTED)
        self._set_text(self.frame_label, "Rahmen: exakte Ränder in mm" if exact else
                       f"Breite: {self.frame_var.get():.2f} % je Halbbild".replace(".", ","))
        symbol_space = self._float(self.margin_top_var.get()) > 0 if exact else self.frame_var.get() > 0
        if exact and self.layout_var.get() == "Parallelblick + Kreuzblick":
            symbol_space = symbol_space or self._float(self.margin_row_gap_var.get()) > 0
        disabled = self._busy or not symbol_space
        self.show_symbols_checkbox.configure(state="disabled" if disabled else "normal", fg_color=TEXT_DISABLED if disabled else GOLD)
        self._refresh_contour_sliders(rounded)
        self.caption_size_label.configure(text_color=TEXT_DISABLED if points else TEXT_MUTED)
        self._set_text(self.caption_size_label, f"Untertitelgröße: {self.caption_points_var.get()} pt" if points else
                       f"Untertitelgröße: {self.caption_size_var.get():.2f} % je Halbbild".replace(".", ","))

    def _refresh_print_summary(self):
        if not self._ui_ready or self.mode_var.get() != "Print":
            return
        try:
            options = self._print_options(allow_pending_logo=True)
            layout = print_layout(options)
            template = CARD_TEMPLATES.get(self.card_template_var.get())
            margins = options.margins
            if template and margins and options.layout != LayoutMode.BOTH:
                margins = replace(margins, row_gap_mm=template[1].row_gap_mm)
            expected_shape = "Klassischer Bogen" if template and template[2] == "Klassischer Bogen" else ROUNDED_RECTANGLE
            adjusted = template and (margins != template[1] or self.print_format_var.get() != template[0]
                                    or self.eye_shape_var.get() != expected_shape or options.layout != LayoutMode.PARALLEL
                                    or options.inner_radius_percent != 0 or options.bottom_radius_percent != 0
                                    or options.show_symbols or options.arch_height_percent != 18 or options.outer_radius_percent != 0)
            text = f"Bildfenster: {layout.eye_width_mm:.2f} × {layout.eye_height_mm:.2f} mm\nBildmitten: {layout.centre_distance_mm:.2f} mm"
            if adjusted:
                text = "Vorlage angepasst\n" + text
            if self._logo_pending():
                text += "\n" + self.tr("Bitte ein Logo wählen.")
            self._set_text(self.print_geometry_label, text)
        except ValueError as exc:
            self._set_text(self.print_geometry_label, str(exc))

    def _mode_changed(self, value: str) -> None:
        is_web = value == "Web"
        if is_web:
            self.web_controls.grid()
            self.print_controls.grid_remove()
        else:
            self.web_controls.grid_remove()
            self.print_controls.grid()
        self._refresh_output()
        self._refresh_start()
        self._refresh_preview_note()
        self._set_start_button_normal()
        self._refresh_layout_controls()
        self.schedule_preview()

    def _size_changed(self, value: str) -> None:
        if value == "Benutzerdefiniert":
            self.custom_width.grid()
        else:
            self.custom_width.grid_remove()
        self.schedule_preview()

    def _print_format_changed(self, value: str) -> None:
        if value == "Benutzerdefiniert":
            self.custom_print.grid()
        else:
            self.custom_print.grid_remove()
        self.schedule_preview()

    def _frame_changed(self, value: float) -> None:
        self._refresh_layout_controls()
        self.schedule_preview()

    def _refresh_preview_note(self):
        if self._logo_pending():
            self._set_text(self.preview_note, "Bitte ein Logo wählen.")
            return
        if self.mode_var.get() == "Print":
            self._set_text(self.preview_note, "Vorschau mit Beschnittrand" if self.show_bleed_var.get()
                           else "Vorschau: fertiges Schnittformat ohne Beschnittrand")
        else:
            self._set_text(self.preview_note, "")

    def _caption_size_changed(self, value: float) -> None:
        self._refresh_layout_controls()
        self.schedule_preview()

    def _color_preset_changed(self, value: str) -> None:
        preset = COLOR_PRESETS.get(value)
        if preset is None:
            self.custom_colors.grid()
        else:
            self.custom_colors.grid_remove()
            self.frame_color_var.set(preset[0])
            self.accent_color_var.set(preset[1])
        self.schedule_preview()

    @staticmethod
    def _hex_color(value: str, fallback: str) -> str:
        value = value.strip()
        if len(value) == 7 and value.startswith("#"):
            try:
                int(value[1:], 16)
                return value.lower()
            except ValueError:
                pass
        return fallback

    @staticmethod
    def _float(value: str, default: float = 0.0) -> float:
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return default

    def _scan_exclusions(self):
        # Also exclude old program/output and every conventional source/output tree.
        paths = [self.program_dir / "output"]
        output = self._effective_output()
        if output:
            paths.append(output)
        return tuple(paths)

    def _reload_folder(self):
        if self._busy or self.input_root is None:
            return
        self._scan_folder(self.input_root)

    def _scan_folder(self, root):
        if self._busy:
            return
        root = Path(root).resolve()
        recursive = self.include_subfolders_var.get()
        exclusions = self._scan_exclusions()
        self._scan_running = True
        previous = self._current_item()
        selected = previous.source.resolve() if previous else None
        self._job_id += 1
        identifier = self._job_id
        self._cancel_event = threading.Event()
        cancel = self._cancel_event
        self._set_busy(True)
        self.progress.set(0)
        self._set_text(self.status, "Bilder werden eingelesen …")
        def scan():
            try:
                items = discover_files([root], recursive=recursive, exclude=exclusions, cancel=cancel)
                check_cancel(cancel)
                self._events.put((identifier, "scan_done", (root, items, selected, recursive)))
            except Cancelled:
                self._events.put((identifier, "scan_cancelled", None))
            except Exception as error:
                self._events.put((identifier, "failed", error))
        threading.Thread(target=scan, daemon=True).start()

    def _output_changed(self):
        self._refresh_output()
        self._reload_folder()

    def cancel_job(self):
        if not self._busy:
            return
        self._cancel_event.set()
        self.cancel_button.configure(state="disabled")
        self._set_text(self.status, "Verarbeitung wird abgebrochen …")
        if self._active_crop_dialog is not None and self._active_crop_dialog.winfo_exists():
            self._active_crop_dialog._cancel()

    def _poll_events(self):
        if self._closing:
            return
        self._poll_job = self.after(30, self._poll_events)
        for _ in range(100):
            try:
                identifier, kind, data = self._events.get_nowait()
            except Empty:
                break
            if identifier != self._job_id:
                continue
            if kind == "scan_done":
                root, items, selected, recursive = data
                if self._cancel_event.is_set():
                    self._scan_cancelled()
                    continue
                self._scan_running = False
                self._folder_scan_config = (recursive, self.output_dir, self.use_program_output.get())
                self.input_root = root
                self.items = items
                self._set_busy(False)
                self._input_changed()
                if selected:
                    self.source_index = next((i for i, item in enumerate(self.sources)
                        if item.source.resolve() == selected), 0)
                    self._refresh_navigation()
                self._set_text(self.status, "Bereit" if items else "Keine unterstützten Bilder gefunden.")
            elif kind == "scan_cancelled":
                self._scan_cancelled()
            elif kind == "progress":
                self._progress_ui(*data)
            elif kind == "crop":
                self._handle_crop_request(data)
            elif kind == "crop_applied":
                item, mode, crop = data
                self._store_crop(item, mode, crop)
            elif kind == "done":
                self._batch_finished(data)
            elif kind == "failed":
                if self._scan_running:
                    self._restore_scan_config()
                self._batch_failed(data)

    def _restore_scan_config(self):
        self._scan_running = False
        if self.input_root is not None and self._folder_scan_config is not None:
            recursive, output, use_program = self._folder_scan_config
            self.include_subfolders_var.set(recursive)
            self.output_dir = output
            self.use_program_output.set(use_program)
            self._refresh_output()

    def _scan_cancelled(self):
        self._restore_scan_config()
        self._set_busy(False)
        self._set_text(self.status, "Einlesen abgebrochen")

    def _handle_crop_request(self, request):
        item, source, options, index, total, ready, response = request
        try:
            if self._cancel_event.is_set():
                response["action"] = "cancel"
                return
            self._set_text(self.status, f"Ausschnitt {index}/{total}: {item.relative_path}")
            dialog = CropDialog(self, source, options, index=index, total=total,
                                filename=str(item.relative_path))
            self._active_crop_dialog = dialog
            self.wait_window(dialog)
            response.update(action=dialog.action, crop=dialog.result)
            if dialog.action == "cancel":
                self._cancel_event.set()
        except Exception as error:
            response["error"] = error
        finally:
            self._active_crop_dialog = None
            ready.set()

    def destroy(self):
        self._closing = True
        if hasattr(self, "_cancel_event"):
            self._cancel_event.set()
        if self._preview_job is not None:
            self.after_cancel(self._preview_job)
            self._preview_job = None
        if self._poll_job is not None:
            self.after_cancel(self._poll_job)
            self._poll_job = None
        super().destroy()

    def _report_crop_storage_error(self, error):
        message = str(error)
        if message not in self.crop_storage_errors:
            self.crop_storage_errors.append(message)
        self._set_text(self.status, "Ausschnitte konnten nicht gespeichert oder geladen werden.")

    def _store_crop(self, item, mode, crop):
        key = item.source.resolve()
        if crop is None:
            self.image_crops[mode].pop(key, None)
        else:
            self.image_crops[mode][key] = crop.clamped()
        if self.remember_crops_var.get():
            try:
                aspect = None
                if crop is not None:
                    with Image.open(item.source) as image:
                        aspect = (image.width // 2) * crop.width / (image.height * crop.height)
                save_crop(item.source, mode, crop, aspect)
            except (OSError, ValueError) as error:
                self._report_crop_storage_error(error)

    def _load_remembered_crops(self):
        if not self.remember_crops_var.get():
            return
        records = {}
        for item in self.sources:
            directory = item.source.parent.resolve()
            if directory not in records:
                try:
                    records[directory] = load_crops(directory)
                except (OSError, ValueError) as error:
                    records[directory] = {}
                    self._report_crop_storage_error(error)
            for mode, crop in records[directory].get(item.source.name, {}).items():
                self.image_crops[mode][item.source.resolve()] = crop
        self.schedule_preview()

    def _remember_crops_changed(self):
        if self._busy:
            return
        self.crop_storage_errors.clear()
        if not self.remember_crops_var.get():
            return
        self._load_remembered_crops()
        for item in self.sources:
            for mode in ("Web", "Print"):
                crop = self.image_crops[mode].get(item.source.resolve())
                if crop is not None:
                    self._store_crop(item, mode, crop)

    def _web_aspect(self):
        return parse_aspect(self.custom_aspect_var.get() if self.aspect_var.get() == "Benutzerdefiniert" else self.aspect_var.get())

    def _aspect_changed(self, value, clear=True):
        if value == "Benutzerdefiniert":
            self.custom_aspect_entry.grid()
        else:
            self.custom_aspect_entry.grid_remove()
        if clear:
            self.image_crops["Web"].clear()
        self.schedule_preview()

    def _current_item(self):
        return self.sources[self.source_index] if self.sources else (self.items[0] if self.items else None)

    def _current_crop(self, mode):
        item = self._current_item()
        return self.image_crops[mode].get(item.source.resolve(), Crop()) if item else Crop()

    def edit_crop(self):
        if self._busy or not self.items:
            return
        mode = self.mode_var.get()
        item = self._current_item()
        try:
            options = self._web_options(allow_pending_logo=True) if mode == "Web" else self._print_options(allow_pending_logo=True)
            with Image.open(item.source) as source:
                dialog = CropDialog(self, source.convert("RGB"), options, index=self.source_index+1,
                    total=len(self.sources) or 1, filename=item.source.name, editing=True)
            self.wait_window(dialog)
            if dialog.action == "accept":
                self._store_crop(item, mode, dialog.result)
                self.schedule_preview()
        except ValueError as error:
            messagebox.showerror("Freeda", self.tr(str(error)))

    def reset_crop(self):
        if self._busy:
            return
        item = self._current_item()
        if item:
            self._store_crop(item, self.mode_var.get(), None)
        self.schedule_preview()

    def choose_files(self) -> None:
        if self._busy:
            return
        names = filedialog.askopenfilenames(
            title=self.tr("Full-SBS-Bilder wählen"),
            initialdir=str(self.last_input_dir) if self.last_input_dir else None,
            filetypes=[
                (self.tr("Bilder"), "*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp"),
                (self.tr("Alle Dateien"), "*.*"),
            ],
        )
        if names:
            self.last_input_dir = Path(names[0]).parent
            self.input_root = None
            self._folder_scan_config = None
            self.items = discover_files([Path(n) for n in names])
            self._input_changed()
            if len(self.items) == 1:
                selected = self.items[0].source.resolve()
                self.sources = [BatchItem(i.source, Path(i.source.name)) for i in
                    discover_files([selected.parent], recursive=False, exclude=self._scan_exclusions())]
                if not any(i.source.resolve() == selected for i in self.sources):
                    self.sources.append(self.items[0])
                self.source_index = next(i for i, item in enumerate(self.sources) if item.source.resolve() == selected)
                self.batch_mode = False
                self._refresh_navigation()
                self._load_remembered_crops()

    def choose_folder(self) -> None:
        if self._busy:
            return
        name = filedialog.askdirectory(title=self.tr("Ordner mit Full-SBS-Bildern wählen"),
                                      initialdir=str(self.last_input_dir) if self.last_input_dir else None)
        if name:
            self.last_input_dir = Path(name)
            self._scan_folder(Path(name))

    def _input_changed(self) -> None:
        self.sources = list(self.items)
        self.source_index = 0
        self.batch_mode = len(self.items) > 1 or self.input_root is not None
        self._refresh_navigation()
        count = len(self.items)
        self._set_text(self.input_status, f"{count} Bild{'er' if count != 1 else ''} gewählt")
        self._refresh_start()
        self._refresh_output()
        self._load_remembered_crops()
        self.schedule_preview()

    def choose_output(self) -> None:
        if self._busy or self.use_program_output.get():
            return
        name = filedialog.askdirectory(title=self.tr("Ausgabeordner wählen"),
                                      initialdir=str(self.output_dir or self.program_dir / "output"))
        if name:
            self.output_dir = Path(name)
            self._output_changed()

    def _effective_output(self):
        return self.program_dir / "output" if self.use_program_output.get() else self.output_dir

    def _refresh_output(self) -> None:
        target = self._effective_output()
        if target is not None and self.input_root:
            target = target / self.input_root.name
        text = str(target) if target is not None else "Kein eigener Ausgabeordner gewählt"
        self._set_text(self.output_status, text)
        self._set_text(self.custom_output_status, str(self.output_dir) if self.output_dir else "–")
        custom_active = not self.use_program_output.get() and not self._busy
        self.custom_output_label.configure(text_color=TEXT_MUTED if custom_active else TEXT_DISABLED)
        self.custom_output_status.configure(text_color=TEXT if custom_active else TEXT_DISABLED)
        self.choose_output_button.configure(state="normal" if custom_active else "disabled")

    def _refresh_start(self) -> None:
        text = f"Batch exportieren ({len(self.items)} Bilder)" if self.batch_mode else "Angezeigtes Bild exportieren"
        self._set_text(self.start_button, text)
        self.start_button.configure(state="disabled" if self._busy or not self.items or self._logo_pending() else "normal")
        self._refresh_navigation()
        self._set_start_button_normal()

    def _export_targets(self, output_format):
        output = self._effective_output()
        if output is None:
            raise ValueError("Bitte einen Ausgabeordner auswählen.")
        return export_targets(list(self.items), output,
                              self.input_root, self.mode_var.get().lower(), output_format)

    def _output_format(self) -> OutputFormat:
        return OutputFormat.PNG if self.format_var.get() == "PNG" else OutputFormat.JPEG

    def _web_options(self, *, allow_pending_logo=False) -> WebRenderOptions:
        size = self.size_var.get()
        if size == "Original":
            target_long_edge = None
        elif size == "Benutzerdefiniert":
            try:
                target_long_edge = int(self.custom_width_var.get().strip())
            except ValueError:
                raise ValueError("Lange Seite: Bitte eine ganze Zahl ab 16 px eingeben.") from None
            if target_long_edge < 16:
                raise ValueError("Lange Seite: Bitte eine ganze Zahl ab 16 px eingeben.")
        else:
            target_long_edge = int(size)

        return WebRenderOptions(
            layout=_LAYOUT_TO_MODE[self.layout_var.get()],
            target_long_edge=target_long_edge,
            eye_aspect=self._web_aspect(),
            crop=self._current_crop("Web"),
            show_symbols=self.show_symbols_var.get(),
            frame_percent=float(self.frame_var.get()),
            frame_color=self._hex_color(self.frame_color_var.get(), DEFAULT_FRAME_COLOR),
            accent_color=self._hex_color(self.accent_color_var.get(), DEFAULT_ACCENT_COLOR),
            outer_radius_percent=self._radius(self.outer_radius_var),
            inner_radius_percent=self._image_radius(),
            bottom_radius_percent=self._bottom_radius(),
            caption="" if self._logo_pending() else self.caption_var.get(),
            font_family=self.font_var.get(),
            caption_size_percent=float(self.caption_size_var.get()),
            output_format=self._output_format(),
            eye_shape=_EYE_SHAPES[self.eye_shape_var.get()],
            arch_height_percent=self._arch_height(),
            **self._logo_options(allow_pending=allow_pending_logo),
        )

    def _contour_slider(self, parent, variable, step):
        def changed(value):
            variable.set(f"{round(value / step) * step:.2f}")
            self.schedule_preview()
        return ctk.CTkSlider(parent, from_=0, to=50, number_of_steps=round(50 / step), command=changed,
                            progress_color=SLIDER_PROGRESS, button_color=SLIDER_BUTTON,
                            button_hover_color=SLIDER_BUTTON_HOVER, fg_color=SLIDER_TRACK)

    def _contour_limits(self):
        try:
            if self.mode_var.get() == "Print":
                options = self._print_options(allow_pending_logo=True)
                layout = print_layout(options)
                eye_w, eye_h = layout.eye_width_mm, layout.eye_height_mm
                width = options.width_mm + 2 * options.bleed_mm
                height = options.height_mm + 2 * options.bleed_mm
                arch = 100 * max(0, eye_h - 25.4 / options.dpi) / eye_w
            else:
                options = self._web_options(allow_pending_logo=True)
                item = self._current_item()
                size = (300, 200)
                if item:
                    with Image.open(item.source) as source:
                        size = (source.width // 2, source.height)
                crop = fit_linked_crop(size, options.crop, options.eye_aspect).clamped()
                eye_size = (max(1, round((crop.x + crop.width) * size[0]) - round(crop.x * size[0])),
                            max(1, round((crop.y + crop.height) * size[1]) - round(crop.y * size[1])))
                geometry = web_geometry(eye_size, options)
                eye_w, eye_h = geometry.row.geometry.eye_width, geometry.row.eye_height
                width, height = geometry.output_size
                arch = 100 * max(0, eye_h - 1) / eye_w
            return 50 * min(1, eye_h / eye_w), 50 * min(1, height / width), arch
        except (ValueError, OSError, ZeroDivisionError):
            return 50, 50, 100

    def _refresh_contour_sliders(self, rounded):
        image_limit, outer_limit, arch_limit = self._contour_limits()
        controls = ((self.inner_radius_slider, self.inner_radius_label, self.inner_radius_var,
                     "Radius oben", 25, image_limit, .5, not rounded),
                    (self.bottom_radius_slider, self.bottom_radius_label, self.bottom_radius_var,
                     "Radius unten", 25, image_limit, .5, not rounded),
                    (self.outer_radius_slider, self.outer_radius_label, self.outer_radius_var,
                     "Radius außen", 5, outer_limit, .1, False),
                    (self.arch_slider, self.arch_label, self.arch_height_var,
                     "Bogenhöhe", 50, arch_limit, .5, rounded))
        for slider, label, variable, name, normal, physical, step, inactive in controls:
            value = self._float(variable.get())
            if not math.isfinite(value) or value < 0:
                value = 0
            # Extend the usual range for stored presets. Moving the pointer
            # never silently changes a preset's original numeric value.
            upper = max(step, math.floor(min(physical, max(normal, value)) / step + 1e-9) * step)
            disabled = self._busy or inactive or physical < step
            slider.configure(from_=0, to=upper, number_of_steps=max(1, round(upper / step)),
                             state="disabled" if disabled else "normal",
                             progress_color=BORDER if disabled else SLIDER_PROGRESS,
                             button_color=TEXT_DISABLED if disabled else SLIDER_BUTTON,
                             button_hover_color=TEXT_DISABLED if disabled else SLIDER_BUTTON_HOVER)
            slider.set(value)
            label.configure(text_color=TEXT_DISABLED if disabled else TEXT_MUTED)
            self._set_text(label, f"{name}: {value:.2f} %".replace(".", ","))

    def _logo_pending(self):
        return self.caption_mode_var.get() == "Logo" and not self.logo_var.get()

    def _radius(self, variable):
        return self._number(variable.get().strip() or "0", "Eckenradius: Bitte einen endlichen Wert ab 0 eingeben.", zero=True)

    def _image_radius(self):
        return self._radius(self.inner_radius_var) if self.eye_shape_var.get() == ROUNDED_RECTANGLE else 0

    def _bottom_radius(self):
        return self._radius(self.bottom_radius_var) if self.eye_shape_var.get() == ROUNDED_RECTANGLE else 0

    def _row_gap(self):
        if self.layout_var.get() == "Parallelblick + Kreuzblick":
            return self._number(self.margin_row_gap_var.get(), "Ränder: Bitte endliche Werte ab 0 mm eingeben.", zero=True)
        value = self._float(self.margin_row_gap_var.get())
        return max(0, value) if math.isfinite(value) else 0

    def _logo_options(self, *, allow_pending=False):
        mode = CaptionMode.LOGO if self.caption_mode_var.get() == "Logo" else CaptionMode.TEXT
        path = None
        if allow_pending and self._logo_pending():
            mode = CaptionMode.TEXT
        if mode == CaptionMode.LOGO:
            path = resolve_logo(self.settings_path.parent, self.logo_var.get())
            load_logo(path)
        return {"caption_mode": mode, "logo_path": path, "logo_height_percent": self.logo_height_var.get()}

    def _arch_height(self):
        if self.eye_shape_var.get() != "Klassischer Bogen":
            return 18.0
        value = self._number(self.arch_height_var.get(), "Bogenhöhe: Bitte einen Wert von 0 bis 100 % eingeben.", zero=True)
        if value > 100:
            raise ValueError("Bogenhöhe: Bitte einen Wert von 0 bis 100 % eingeben.")
        return value

    def _print_options(self, *, preview: bool = False, validate: bool = True, allow_pending_logo=False) -> PrintRenderOptions:
        preset = PRINT_FORMAT_PRESETS.get(self.print_format_var.get())
        if preset is None:
            width_mm = self._number(self.print_width_var.get(), "Kartenmaße: Bitte positive Werte in mm eingeben.")
            height_mm = self._number(self.print_height_var.get(), "Kartenmaße: Bitte positive Werte in mm eingeben.")
        else:
            width_mm, height_mm = preset
        dpi = 96 if preview else parse_dpi(self.dpi_var.get())
        margins = None
        if self.margin_mode_var.get() == "Exakte Ränder in mm":
            margins = PrintMargins(**{f"{key}_mm": self._number(getattr(self, f"margin_{key}_var").get(),
                "Ränder: Bitte endliche Werte ab 0 mm eingeben.", zero=True)
                for key in ("side", "top", "centre", "bottom")}, row_gap_mm=self._row_gap())
        has_caption = not self._logo_pending() and (self.caption_mode_var.get() == "Logo" or bool(self.caption_var.get()))
        gaps = {f"caption_gap_{key}_mm": self._number(getattr(self, f"caption_gap_{key}_var").get(),
                    "Textabstände: Bitte Werte ab 0 mm eingeben.", zero=True)
                if has_caption and getattr(self, f"caption_gap_{key}_var").get().strip() else None for key in ("top", "bottom")}
        options = PrintRenderOptions(
            layout=_LAYOUT_TO_MODE[self.layout_var.get()],
            width_mm=width_mm,
            height_mm=height_mm,
            dpi=dpi,
            bleed_mm=parse_bleed(self.bleed_var.get()),
            frame_percent=float(self.frame_var.get()),
            frame_color=self._hex_color(self.frame_color_var.get(), DEFAULT_FRAME_COLOR),
            accent_color=self._hex_color(self.accent_color_var.get(), DEFAULT_ACCENT_COLOR),
            caption="" if self._logo_pending() else self.caption_var.get(),
            font_family=self.font_var.get(),
            caption_size_percent=float(self.caption_size_var.get()),
            inner_radius_percent=self._image_radius(),
            bottom_radius_percent=self._bottom_radius(),
            output_format=self._output_format(),
            cutting_guide=_CUTTING_GUIDES[self.cutting_var.get()],
            outer_radius_percent=self._radius(self.outer_radius_var),
            crop=self._current_crop("Print"),
            show_symbols=self.show_symbols_var.get(),
            eye_shape=_EYE_SHAPES[self.eye_shape_var.get()],
            arch_height_percent=self._arch_height(),
            margins=margins,
            caption_points=self._number(self.caption_points_var.get(), "Schriftgröße: Bitte einen positiven Wert in pt eingeben.")
                if self.caption_unit_var.get() == "Punkt (pt)" and self.caption_mode_var.get() == "Text" and has_caption else None,
            logo_height_mm=self._number(self.logo_mm_var.get(), "Logohöhe: Bitte einen positiven Wert eingeben.")
                if self.caption_mode_var.get() == "Logo" and self.logo_unit_var.get() == "Millimeter (mm)" and has_caption else None,
            **self._logo_options(allow_pending=allow_pending_logo),
            **gaps,
        )
        if validate:
            print_layout(options)
        return options

    def schedule_preview(self) -> None:
        self._refresh_layout_controls()
        self._refresh_print_summary()
        self._refresh_start()
        if self._preview_job is not None:
            try:
                self.after_cancel(self._preview_job)
            except Exception:
                pass
        self._preview_job = self.after(120, self.update_preview)

    def update_preview(self) -> None:
        self._preview_job = None
        self._refresh_preview_note()
        if not self.items:
            self.preview_label.configure(image="", text=self.tr("Bild wählen"))
            return
        item = self.sources[self.source_index] if self.sources else self.items[0]
        try:
            panel_w = max(1, self.preview_label.winfo_width() - 10)
            panel_h = max(1, self.preview_label.winfo_height() - 10)
            with Image.open(item.source) as image:
                image.load()
                source = image.convert("RGB")
                if self.mode_var.get() == "Web":
                    options = self._web_options(allow_pending_logo=True)
                    preview_width = max(16, min(max(panel_w, panel_h), options.target_long_edge or max(source.size)))
                    rendered = render_web(source, replace(options, target_long_edge=preview_width))
                else:
                    options = print_preview_options(self._print_options(allow_pending_logo=True), panel_w, panel_h)
                    rendered = print_preview_image(source, options, show_bleed=self.show_bleed_var.get())
            rendered = fit_preview(preview_export_image(rendered, options), panel_w, panel_h)
            self.preview_photo = ImageTk.PhotoImage(rendered)
            self.preview_label.configure(image=self.preview_photo, text="")
        except Exception as exc:
            self.preview_label.configure(image="", text=self.tr(f"Vorschaufehler:\n{exc}"))

    def _set_busy(self, busy: bool) -> None:
        if busy == self._busy:
            return
        self._busy = busy
        if busy:
            def lock_controls(parent):
                for widget in parent.winfo_children():
                    if isinstance(widget, (ctk.CTkButton, ctk.CTkEntry, ctk.CTkSlider,
                                           ctk.CTkCheckBox, ctk.CTkOptionMenu, ctk.CTkSegmentedButton)):
                        colors = {}
                        if isinstance(widget, ctk.CTkSlider):
                            colors = {key: widget.cget(key) for key in
                                      ("progress_color", "button_color", "button_hover_color")}
                        elif isinstance(widget, ctk.CTkCheckBox):
                            colors = {"fg_color": widget.cget("fg_color")}
                        # CustomTkinter 5.2 exposes segmented state only on its buttons.
                        state = (next(child.cget("state") for child in widget.winfo_children()
                                      if isinstance(child, ctk.CTkButton))
                                 if isinstance(widget, ctk.CTkSegmentedButton) else widget.cget("state"))
                        self._control_states[widget] = (state, colors)
                        widget.configure(state="disabled")
                        if isinstance(widget, ctk.CTkSlider):
                            widget.configure(progress_color=BORDER, button_color=TEXT_DISABLED,
                                             button_hover_color=TEXT_DISABLED)
                        elif isinstance(widget, ctk.CTkCheckBox):
                            widget.configure(fg_color=TEXT_DISABLED)
                        continue
                    lock_controls(widget)
            lock_controls(self.sidebar_container)
            self._control_states.pop(self.cancel_button, None)
        else:
            for widget, (state, colors) in self._control_states.items():
                if widget.winfo_exists():
                    widget.configure(state=state, **colors)
            self._control_states.clear()
            self._frame_changed(self.frame_var.get())
        self.cancel_button.configure(state="normal" if busy else "disabled")
        self._refresh_output()
        self._refresh_start()
        if busy:
            self._set_start_button_disabled()
        else:
            self._set_start_button_normal()
            self.schedule_preview()

    def start_batch(self) -> None:
        if self._busy:
            return
        if self._logo_pending():
            messagebox.showinfo("Freeda", self.tr("Bitte ein Logo wählen."))
            return
        if not self.items:
            messagebox.showinfo("Freeda", self.tr("Bitte zuerst Bilder oder einen Ordner wählen."))
            return
        if self._effective_output() is None:
            self.choose_output()
            if self.output_dir is None:
                return

        try:
            if self.mode_var.get() == "Print":
                self._start_print_batch()
            else:
                self._start_web_batch()
        except ValueError as exc:
            self._batch_failed(exc)

    def _start_web_batch(self) -> None:
        self._start_export(self._web_options())

    def _start_print_batch(self) -> None:
        self._start_export(self._print_options())

    def _start_export(self, options):
        items = list(self.items)
        targets = self._export_targets(options.output_format)
        mode = self.mode_var.get()
        crops = dict(self.image_crops[mode])
        review = self.web_review_var.get() if mode == "Web" else self.print_review_var.get()
        manual = review or (self.batch_mode and (mode == "Print" or options.eye_aspect is not None))
        reuse = self.batch_mode and (self.web_crop_mode_var.get() if mode == "Web" else
                                    self.crop_mode_var.get()) == "Gleichen Ausschnitt verwenden"
        self._job_id += 1
        identifier = self._job_id
        self._cancel_event = threading.Event()
        cancel = self._cancel_event
        self.crop_storage_errors.clear()
        self.last_batch_result = None
        self._set_busy(True)
        self.progress.set(0)
        self._set_text(self.status, "Export läuft …")

        def choose(item, source, current, index, total):
            ready, response = threading.Event(), {}
            self._events.put((identifier, "crop", (item, source, current, index, total, ready, response)))
            while not ready.wait(0.05):
                check_cancel(cancel)
            check_cancel(cancel)
            if "error" in response:
                raise response["error"]
            return response.get("action", "cancel"), response.get("crop")

        def progress(index, total, item):
            self._events.put((identifier, "progress", (index, total, str(item.relative_path))))

        def worker():
            try:
                result = run_batch(items, targets, replace(options, crop=Crop()), cancel=cancel,
                    crops=crops, review=review, reuse=reuse,
                    choose_crop=choose if manual else None, progress=progress,
                    crop_applied=lambda item, crop: self._events.put((identifier, "crop_applied", (item, mode, crop))))
                self._events.put((identifier, "done", result))
            except Exception as error:
                self._events.put((identifier, "failed", error))
        threading.Thread(target=worker, daemon=True).start()

    def _batch_finished(self, result):
        self.last_batch_result = result
        self._set_busy(False)
        count = len(result.written)
        if not result.cancelled:
            self.progress.set(1)
        status = (f"Export abgebrochen – {count} Dateien exportiert" if result.cancelled else
                  f"Fertig – {count} Datei{'en' if count != 1 else ''}")
        if result.errors or result.skipped:
            status += f" · {len(result.errors)} Fehler · {result.skipped} übersprungen"
        self._set_text(self.status, status)
        if result.errors:
            details = "\n".join(prefix + ": " + self.tr(reason) for prefix, reason in
                (message.split(": ", 1) for message in result.errors[:10]))
            if len(result.errors) > 10:
                details += f"\n… ({len(result.errors)})"
            messagebox.showwarning("Freeda", self.tr("Einige Bilder konnten nicht exportiert werden.") + "\n\n" + details)
        if self.crop_storage_errors:
            messagebox.showwarning("Freeda", self.tr("Ausschnitte konnten nicht gespeichert oder geladen werden.")
                                   + "\n\n" + "\n".join(self.crop_storage_errors[:10]))
        self._report_metadata_warnings(result.warnings, update_status=False)
        if count and not result.cancelled and not result.errors:
            play_ready_sound(resource_path("assets/ready.wav"))

    def _progress_ui(self, index: int, total: int, name: str) -> None:
        self.progress.set(index / max(1, total))
        if not self._cancel_event.is_set():
            self._set_text(self.status, f"Verarbeitung {index}/{total}: {name}")

    def _report_metadata_warnings(self, warnings, *, update_status=True):
        if warnings:
            if update_status:
                self._set_text(self.status, "Export fertig; Metadaten konnten nicht vollständig übernommen werden.")
            details = "\n".join(prefix + ": " + self.tr(reason)
                for prefix, reason in (message.split(": ", 1) for message in warnings[:5]))
            if len(warnings) > 5:
                details += f"\n… ({len(warnings)})"
            messagebox.showwarning("Freeda", self.tr("Die Bilder wurden exportiert. Metadaten konnten nicht vollständig übernommen werden.") + "\n\n" + details)

    def _batch_failed(self, exc: Exception) -> None:
        self._set_busy(False)
        self._set_text(self.status, "Fehler")
        messagebox.showerror("Freeda", self.tr(str(exc)))


def run() -> None:
    app = FreedaApp()
    app.mainloop()
