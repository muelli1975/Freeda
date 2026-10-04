from __future__ import annotations

import threading
import tkinter as tk
from dataclasses import replace
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk

from . import __version__
from .batch import discover_files, render_web_batch
from .config import (
    APP_NAME,
    COLOR_PRESETS,
    DEFAULT_ACCENT_COLOR,
    DEFAULT_COLOR_PRESET,
    DEFAULT_FRAME_COLOR,
    LAYOUTS,
    OUTPUT_FORMATS,
    PRINT_FORMAT_PRESETS,
    WEB_WIDTH_PRESETS,
)
from .fonts import available_fonts
from .models import Crop, CuttingGuide, LayoutMode, OutputFormat, PrintRenderOptions, WebRenderOptions
from .notifications import play_ready_sound
from .print_flow import CropBatchMode, PrintBatchSession
from .print_render import crop_for_aspect, print_eye_aspect, render_print
from .render import render_web, save_render, split_full_sbs
from .resources import resource_path
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
    "Parallel + Kreuz": LayoutMode.BOTH,
    "Parallel": LayoutMode.PARALLEL,
    "Kreuz": LayoutMode.CROSS,
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


class CropDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        source: Image.Image,
        options: PrintRenderOptions,
        *,
        index: int,
        total: int,
        filename: str,
    ) -> None:
        super().__init__(parent, fg_color=BG_MAIN)
        self.title(f"Freeda – Ausschnitt {index}/{total}")
        self.geometry("1080x760")
        self.minsize(900, 650)
        self.transient(parent)
        self.grab_set()

        self.source = source.copy()
        self.options = options
        self.result: Crop | None = None
        self.action = "cancel"
        self.preview_photo = None
        self._preview_job = None

        self.zoom_var = tk.DoubleVar(value=1.0)
        self.x_var = tk.DoubleVar(value=0.5)
        self.y_var = tk.DoubleVar(value=0.5)

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

        controls = ctk.CTkFrame(
            body,
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
            text="Zentrieren",
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
            text="Übernehmen & weiter",
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

        for row, text, command in (
            (1, "Überspringen", self._skip),
            (2, "Batch abbrechen", self._cancel),
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

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._refresh_labels()
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
        self.zoom_label.configure(text=f"Zoom: {self.zoom_var.get():.2f}×".replace(".", ","))
        self.x_label.configure(text=f"Horizontal: {self.x_var.get() * 100:.0f} %")
        self.y_label.configure(text=f"Vertikal: {self.y_var.get() * 100:.0f} %")

    def _reset(self) -> None:
        self.zoom_var.set(1.0)
        self.x_var.set(0.5)
        self.y_var.set(0.5)
        self._controls_changed()

    def current_crop(self) -> Crop:
        left, _ = split_full_sbs(self.source)
        return crop_for_aspect(
            left.size,
            print_eye_aspect(self.options),
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
            preview_options = replace(
                self.options,
                dpi=96,
                crop=self.current_crop(),
            )
            rendered = render_print(self.source, preview_options)
            max_w = max(500, self.preview_label.winfo_width() - 10)
            max_h = max(400, self.preview_label.winfo_height() - 10)
            rendered.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(rendered)
            self.preview_label.configure(image=self.preview_photo, text="")
        except Exception as exc:
            self.preview_label.configure(image="", text=f"Vorschaufehler:\n{exc}")

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


class FreedaApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__(fg_color=BG_MAIN)
        self.title(f"{APP_NAME} {__version__}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(1120, 720)

        icon = resource_path("assets/Freeda.ico")
        if icon.is_file():
            try:
                self.iconbitmap(str(icon))
            except Exception:
                pass

        self.items = []
        self.output_dir: Path | None = None
        self.preview_photo = None
        self._preview_job = None
        self._busy = False

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkScrollableFrame(
            self, width=SIDEBAR_WIDTH, fg_color=PANEL, corner_radius=0
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

        self._build_sidebar()

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

    def _option(self, parent, variable, values, command=None):
        return ctk.CTkOptionMenu(
            parent,
            variable=variable,
            values=list(values),
            command=command,
            fg_color=PANEL,
            button_color=PANEL_HOVER,
            button_hover_color=BORDER,
            dropdown_fg_color=BG_SOFT,
            dropdown_hover_color=PANEL_HOVER,
            dropdown_text_color=TEXT,
            text_color=TEXT,
            corner_radius=RADIUS_CONTROL,
        )

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
            text="Free-view Stereo für Web und Print",
            anchor="w",
            text_color=TEXT_MUTED,
            font=(FONT_FAMILY, 12),
        ).grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 18))
        row += 1

        self._label(self.sidebar, "Eingabe", section=True).grid(row=row, column=0, sticky="ew", padx=20)
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
        )
        self.mode_selector.grid(row=row, column=0, sticky="ew", padx=20, pady=(6, 10))
        row += 1

        self.layout_var = tk.StringVar(value="Parallel + Kreuz")
        self._label(self.sidebar, "Ansicht").grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self._option(
            self.sidebar, self.layout_var, LAYOUTS, lambda _v: self.schedule_preview()
        ).grid(row=row, column=0, sticky="ew", padx=20, pady=(4, 10))
        row += 1

        self.web_controls = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.web_controls.grid(row=row, column=0, sticky="ew", padx=20)
        self.web_controls.grid_columnconfigure(0, weight=1)
        row += 1
        self._label(self.web_controls, "Web-Breite").grid(row=0, column=0, sticky="ew")
        self.size_var = tk.StringVar(value="1920")
        self.size_menu = self._option(
            self.web_controls, self.size_var, WEB_WIDTH_PRESETS, self._size_changed
        )
        self.size_menu.grid(row=1, column=0, sticky="ew", pady=(4, 6))
        self.custom_width_var = tk.StringVar(value="1920")
        self.custom_width = self._entry(
            self.web_controls, self.custom_width_var, "Breite in Pixel"
        )
        self.custom_width.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.custom_width.grid_remove()
        self.custom_width.bind("<KeyRelease>", lambda _e: self.schedule_preview())

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
        self._label(dpi_block, "Auflösung").pack(fill="x")
        self._option(dpi_block, self.dpi_var, ("300", "600"), lambda _v: self.schedule_preview()).pack(
            fill="x", pady=(3, 0)
        )

        self.bleed_var = tk.StringVar(value="3")
        bleed_block = ctk.CTkFrame(print_pair, fg_color="transparent")
        bleed_block.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self._label(bleed_block, "Beschnitt").pack(fill="x")
        self._option(
            bleed_block, self.bleed_var, ("0", "3"), lambda _v: self.schedule_preview()
        ).pack(fill="x", pady=(3, 0))

        self._label(self.print_controls, "Crop im Batch").grid(row=4, column=0, sticky="ew")
        self.crop_mode_var = tk.StringVar(value="Jedes Bild manuell")
        self._option(
            self.print_controls,
            self.crop_mode_var,
            tuple(_CROP_MODES.keys()),
        ).grid(row=5, column=0, sticky="ew", pady=(3, 8))

        self._label(self.print_controls, "Schneidehilfe").grid(row=6, column=0, sticky="ew")
        self.cutting_var = tk.StringVar(value="Keine")
        self._option(
            self.print_controls,
            self.cutting_var,
            tuple(_CUTTING_GUIDES.keys()),
            lambda _v: self.schedule_preview(),
        ).grid(row=7, column=0, sticky="ew", pady=(3, 12))
        self.print_controls.grid_remove()

        self._label(self.sidebar, "Rahmen", section=True).grid(
            row=row, column=0, sticky="ew", padx=20, pady=(4, 0)
        )
        row += 1
        self.frame_label = self._label(self.sidebar, "Breite: 1,50 % je Halbbild")
        self.frame_label.grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self.frame_var = tk.DoubleVar(value=1.5)
        ctk.CTkSlider(
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
        ).grid(row=row, column=0, sticky="ew", padx=20, pady=(2, 10))
        row += 1

        radius_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        radius_frame.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 10))
        row += 1
        radius_frame.grid_columnconfigure(0, weight=1)
        radius_frame.grid_columnconfigure(1, weight=1)
        self.outer_radius_var = tk.StringVar(value="0")
        self.inner_radius_var = tk.StringVar(value="0")
        for col, label, var in (
            (0, "Außenradius %", self.outer_radius_var),
            (1, "Innenradius %", self.inner_radius_var),
        ):
            block = ctk.CTkFrame(radius_frame, fg_color="transparent")
            block.grid(row=0, column=col, sticky="ew", padx=(0, 4) if col == 0 else (4, 0))
            self._label(block, label).pack(fill="x")
            entry = self._entry(block, var)
            entry.pack(fill="x", pady=(3, 0))
            entry.bind("<KeyRelease>", lambda _e: self.schedule_preview())

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
        self.caption_var = tk.StringVar(value="")
        caption = self._entry(self.sidebar, self.caption_var, "Optionaler Untertitel")
        caption.grid(row=row, column=0, sticky="ew", padx=20, pady=(6, 6))
        row += 1
        caption.bind("<KeyRelease>", lambda _e: self.schedule_preview())

        self.font_var = tk.StringVar(value="Segoe UI")
        self._option(
            self.sidebar, self.font_var, available_fonts(), lambda _v: self.schedule_preview()
        ).grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 12))
        row += 1

        self._label(self.sidebar, "Dateiformat", section=True).grid(row=row, column=0, sticky="ew", padx=20)
        row += 1
        self.format_var = tk.StringVar(value="JPEG")
        self._option(
            self.sidebar, self.format_var, OUTPUT_FORMATS, lambda _v: self.schedule_preview()
        ).grid(row=row, column=0, sticky="ew", padx=20, pady=(6, 8))
        row += 1

        self._button(self.sidebar, "Ausgabeordner …", self.choose_output).grid(
            row=row, column=0, sticky="ew", padx=20, pady=(0, 5)
        )
        row += 1
        self.output_status = self._label(self.sidebar, "Noch kein Ausgabeordner gewählt")
        self.output_status.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 14))
        row += 1

        self.start_button = self._button(self.sidebar, "Batch starten", self.start_batch, primary=True)
        self.start_button.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 8))
        row += 1
        self.progress = ctk.CTkProgressBar(
            self.sidebar, progress_color=GOLD, fg_color=PROGRESS_TRACK
        )
        self.progress.set(0)
        self.progress.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 5))
        row += 1
        self.status = self._label(self.sidebar, "Bereit")
        self.status.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 22))

        self._mode_changed("Web")

    def _mode_changed(self, value: str) -> None:
        is_web = value == "Web"
        if is_web:
            self.web_controls.grid()
            self.print_controls.grid_remove()
            self.start_button.configure(text="Batch starten")
        else:
            self.web_controls.grid_remove()
            self.print_controls.grid()
            self.start_button.configure(text="Print-Batch starten")
        self._set_start_button_normal()
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
        self.frame_label.configure(text=f"Breite: {value:.2f} % je Halbbild".replace(".", ","))
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

    def choose_files(self) -> None:
        names = filedialog.askopenfilenames(
            title="Full-SBS-Bilder wählen",
            filetypes=[
                ("Bilder", "*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if names:
            self.items = discover_files([Path(n) for n in names])
            self._input_changed()

    def choose_folder(self) -> None:
        name = filedialog.askdirectory(title="Ordner mit Full-SBS-Bildern wählen")
        if name:
            self.items = discover_files([Path(name)], recursive=True)
            self._input_changed()

    def _input_changed(self) -> None:
        count = len(self.items)
        self.input_status.configure(text=f"{count} Bild{'er' if count != 1 else ''} gewählt")
        self.schedule_preview()

    def choose_output(self) -> None:
        name = filedialog.askdirectory(title="Ausgabeordner wählen")
        if name:
            self.output_dir = Path(name)
            self.output_status.configure(text=str(self.output_dir))

    def _output_format(self) -> OutputFormat:
        return OutputFormat.PNG if self.format_var.get() == "PNG" else OutputFormat.JPEG

    def _web_options(self) -> WebRenderOptions:
        size = self.size_var.get()
        if size == "Original":
            target_width = None
        elif size == "Benutzerdefiniert":
            try:
                target_width = max(320, int(self.custom_width_var.get()))
            except ValueError:
                target_width = 1920
        else:
            target_width = int(size)

        return WebRenderOptions(
            layout=_LAYOUT_TO_MODE[self.layout_var.get()],
            target_width=target_width,
            frame_percent=float(self.frame_var.get()),
            frame_color=self._hex_color(self.frame_color_var.get(), DEFAULT_FRAME_COLOR),
            accent_color=self._hex_color(self.accent_color_var.get(), DEFAULT_ACCENT_COLOR),
            outer_radius_percent=max(0.0, self._float(self.outer_radius_var.get())),
            inner_radius_percent=max(0.0, self._float(self.inner_radius_var.get())),
            caption=self.caption_var.get(),
            font_family=self.font_var.get(),
            output_format=self._output_format(),
        )

    def _print_options(self, *, preview: bool = False) -> PrintRenderOptions:
        preset = PRINT_FORMAT_PRESETS.get(self.print_format_var.get())
        if preset is None:
            width_mm = max(20.0, self._float(self.print_width_var.get(), 150.0))
            height_mm = max(20.0, self._float(self.print_height_var.get(), 100.0))
        else:
            width_mm, height_mm = preset
        dpi = 96 if preview else int(self.dpi_var.get())
        return PrintRenderOptions(
            layout=_LAYOUT_TO_MODE[self.layout_var.get()],
            width_mm=width_mm,
            height_mm=height_mm,
            dpi=dpi,
            bleed_mm=max(0.0, self._float(self.bleed_var.get(), 3.0)),
            frame_percent=float(self.frame_var.get()),
            frame_color=self._hex_color(self.frame_color_var.get(), DEFAULT_FRAME_COLOR),
            accent_color=self._hex_color(self.accent_color_var.get(), DEFAULT_ACCENT_COLOR),
            caption=self.caption_var.get(),
            font_family=self.font_var.get(),
            inner_radius_percent=max(0.0, self._float(self.inner_radius_var.get())),
            output_format=self._output_format(),
            cutting_guide=_CUTTING_GUIDES[self.cutting_var.get()],
        )

    def schedule_preview(self) -> None:
        if self._preview_job is not None:
            try:
                self.after_cancel(self._preview_job)
            except Exception:
                pass
        self._preview_job = self.after(120, self.update_preview)

    def update_preview(self) -> None:
        self._preview_job = None
        if not self.items:
            self.preview_label.configure(image="", text="Bild wählen")
            return
        item = self.items[0]
        try:
            with Image.open(item.source) as image:
                image.load()
                source = image.convert("RGB")
                if self.mode_var.get() == "Web":
                    options = self._web_options()
                    panel_w = max(500, self.preview_label.winfo_width() - 10)
                    preview_width = min(panel_w, options.target_width or source.width)
                    rendered = render_web(source, replace(options, target_width=preview_width))
                else:
                    rendered = render_print(source, self._print_options(preview=True))
            panel_w = max(500, self.preview_label.winfo_width() - 10)
            panel_h = max(400, self.preview_label.winfo_height() - 10)
            rendered.thumbnail((panel_w, panel_h), Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(rendered)
            self.preview_label.configure(image=self.preview_photo, text="")
        except Exception as exc:
            self.preview_label.configure(image="", text=f"Vorschaufehler:\n{exc}")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.start_button.configure(state="disabled" if busy else "normal")
        if busy:
            self._set_start_button_disabled()
        else:
            self._set_start_button_normal()

    def start_batch(self) -> None:
        if self._busy:
            return
        if not self.items:
            messagebox.showinfo("Freeda", "Bitte zuerst Bilder oder einen Ordner wählen.")
            return
        if self.output_dir is None:
            self.choose_output()
            if self.output_dir is None:
                return

        if self.mode_var.get() == "Print":
            self._start_print_batch()
        else:
            self._start_web_batch()

    def _start_web_batch(self) -> None:
        options = self._web_options()
        self._set_busy(True)
        self.progress.set(0)
        self.status.configure(text="Batch läuft …")

        def progress(index, total, item):
            self.after(0, lambda: self._progress_ui(index, total, item.source.name))

        def worker():
            try:
                written = render_web_batch(self.items, self.output_dir, options, progress=progress)
                self.after(0, lambda: self._batch_done(len(written)))
            except Exception as exc:
                self.after(0, lambda: self._batch_failed(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _start_print_batch(self) -> None:
        options = self._print_options()
        session = PrintBatchSession(
            list(self.items),
            mode=_CROP_MODES[self.crop_mode_var.get()],
        )
        written = 0
        self._set_busy(True)
        self.progress.set(0)

        try:
            total = len(session.items)
            while not session.finished:
                item = session.current
                if item is None:
                    break
                index = session.index + 1
                self.status.configure(text=f"Bild {index}/{total}: {item.source.name}")
                self.progress.set((index - 1) / max(1, total))
                self.update_idletasks()

                with Image.open(item.source) as image:
                    image.load()
                    source = image.convert("RGB")

                if session.needs_manual_crop:
                    dialog = CropDialog(
                        self,
                        source,
                        options,
                        index=index,
                        total=total,
                        filename=item.source.name,
                    )
                    self.wait_window(dialog)
                    if dialog.action == "cancel":
                        self.status.configure(text="Print-Batch abgebrochen")
                        break
                    if dialog.action == "skip":
                        session.skip()
                        continue
                    crop = dialog.result or Crop()
                else:
                    crop = session.suggested_crop()

                session.accept(crop)
                current = replace(options, crop=crop)
                rendered = render_print(source, current)
                stem = item.relative_path.stem + "_print"
                target = self.output_dir / item.relative_path.with_name(stem)
                save_render(
                    rendered,
                    target,
                    current.output_format,
                    dpi=current.dpi,
                    background_color=current.frame_color,
                )
                written += 1
                self.progress.set(session.index / max(1, total))
                self.update_idletasks()

            if written:
                self._batch_done(written)
            elif session.finished:
                self._batch_done(0)
            else:
                self._set_busy(False)
        except Exception as exc:
            self._batch_failed(exc)

    def _progress_ui(self, index: int, total: int, name: str) -> None:
        self.progress.set(index / max(1, total))
        self.status.configure(text=f"{index}/{total}: {name}")

    def _batch_done(self, count: int) -> None:
        self._set_busy(False)
        self.progress.set(1)
        self.status.configure(text=f"Fertig – {count} Datei{'en' if count != 1 else ''}")
        play_ready_sound(resource_path("assets/ready.wav"))

    def _batch_failed(self, exc: Exception) -> None:
        self._set_busy(False)
        self.status.configure(text="Fehler")
        messagebox.showerror("Freeda", str(exc))


def run() -> None:
    app = FreedaApp()
    app.mainloop()
