from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk

from . import __version__
from .batch import discover_files, render_web_batch
from .config import (
    APP_NAME, LAYOUTS, OUTPUT_FORMATS, WEB_WIDTH_PRESETS,
    COLOR_PRESETS, DEFAULT_COLOR_PRESET, DEFAULT_FRAME_COLOR, DEFAULT_ACCENT_COLOR,
)
from .fonts import available_fonts
from .models import LayoutMode, OutputFormat, WebRenderOptions
from .notifications import play_ready_sound
from .render import render_web
from .resources import resource_path
from .theme import (
    BG_MAIN, BG_SOFT, PANEL, PANEL_HOVER, BORDER,
    TEXT, TEXT_MUTED, TEXT_DISABLED,
    GOLD, GOLD_LIGHT,
    INPUT_BG, BUTTON_BG, BUTTON_HOVER,
    SLIDER_TRACK, SLIDER_PROGRESS, SLIDER_BUTTON, SLIDER_BUTTON_HOVER,
    PROGRESS_TRACK,
    START_BG, START_HOVER_BG, START_TEXT, START_HOVER_TEXT,
    START_BORDER, START_HOVER_BORDER,
    START_DISABLED_BG, START_DISABLED_TEXT, START_DISABLED_BORDER,
    PREVIEW_BG, FONT_FAMILY, RADIUS_CONTROL, RADIUS_PANEL, BORDER_WIDTH,
)

ctk.set_appearance_mode("dark")

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 860
SIDEBAR_WIDTH = 370

_LAYOUT_TO_MODE = {
    "Parallel + Kreuz": LayoutMode.BOTH,
    "Parallel": LayoutMode.PARALLEL,
    "Kreuz": LayoutMode.CROSS,
}


class FreedaApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__(fg_color=BG_MAIN)
        self.title(f"{APP_NAME} {__version__}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(1120, 720)

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
            self, fg_color=PREVIEW_BG, corner_radius=RADIUS_PANEL,
            border_width=BORDER_WIDTH, border_color=BORDER
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
            parent, text=text, anchor="w",
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
        title = ctk.CTkLabel(
            self.sidebar, text="Freeda", anchor="w",
            text_color=GOLD_LIGHT, font=(FONT_FAMILY, 27, "bold")
        )
        title.grid(row=row, column=0, sticky="ew", padx=20, pady=(20, 0)); row += 1
        ctk.CTkLabel(
            self.sidebar, text="Free-view Stereo für Web und Print",
            anchor="w", text_color=TEXT_MUTED, font=(FONT_FAMILY, 12)
        ).grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 18)); row += 1

        self._label(self.sidebar, "Eingabe", section=True).grid(row=row, column=0, sticky="ew", padx=20); row += 1
        input_buttons = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        input_buttons.grid(row=row, column=0, sticky="ew", padx=20, pady=(6, 6)); row += 1
        input_buttons.grid_columnconfigure(0, weight=1)
        input_buttons.grid_columnconfigure(1, weight=1)
        self._button(input_buttons, "Dateien …", self.choose_files).grid(row=0, column=0, sticky="ew", padx=(0,4))
        self._button(input_buttons, "Ordner …", self.choose_folder).grid(row=0, column=1, sticky="ew", padx=(4,0))
        self.input_status = self._label(self.sidebar, "Keine Bilder gewählt")
        self.input_status.grid(row=row, column=0, sticky="ew", padx=20, pady=(0,16)); row += 1

        self._label(self.sidebar, "Ausgabe", section=True).grid(row=row, column=0, sticky="ew", padx=20); row += 1
        self.mode_var = tk.StringVar(value="Web")
        self.mode_selector = ctk.CTkSegmentedButton(
            self.sidebar, values=["Web", "Print"], variable=self.mode_var,
            command=self._mode_changed,
            selected_color=GOLD, selected_hover_color=GOLD_LIGHT,
            unselected_color=BG_SOFT, unselected_hover_color=PANEL_HOVER,
            text_color=TEXT,
        )
        self.mode_selector.grid(row=row, column=0, sticky="ew", padx=20, pady=(6,10)); row += 1

        self.layout_var = tk.StringVar(value="Parallel + Kreuz")
        self._label(self.sidebar, "Ansicht").grid(row=row, column=0, sticky="ew", padx=20); row += 1
        self._option(self.sidebar, self.layout_var, LAYOUTS, lambda _v: self.schedule_preview()).grid(
            row=row, column=0, sticky="ew", padx=20, pady=(4,10)); row += 1

        self.size_label = self._label(self.sidebar, "Web-Breite")
        self.size_label.grid(row=row, column=0, sticky="ew", padx=20); row += 1
        self.size_var = tk.StringVar(value="1920")
        self.size_menu = self._option(self.sidebar, self.size_var, WEB_WIDTH_PRESETS, self._size_changed)
        self.size_menu.grid(row=row, column=0, sticky="ew", padx=20, pady=(4,6)); row += 1
        self.custom_width_var = tk.StringVar(value="1920")
        self.custom_width = ctk.CTkEntry(
            self.sidebar, textvariable=self.custom_width_var, fg_color=INPUT_BG,
            border_color=BORDER, text_color=TEXT, placeholder_text="Breite in Pixel"
        )
        self.custom_width.grid(row=row, column=0, sticky="ew", padx=20, pady=(0,12)); row += 1
        self.custom_width.grid_remove()
        self.custom_width.bind("<KeyRelease>", lambda _e: self.schedule_preview())

        self._label(self.sidebar, "Rahmen", section=True).grid(row=row, column=0, sticky="ew", padx=20, pady=(4,0)); row += 1
        self.frame_label = self._label(self.sidebar, "Breite: 1,50 % je Halbbild")
        self.frame_label.grid(row=row, column=0, sticky="ew", padx=20); row += 1
        self.frame_var = tk.DoubleVar(value=1.5)
        ctk.CTkSlider(
            self.sidebar, from_=0.0, to=5.0, number_of_steps=100,
            variable=self.frame_var, command=self._frame_changed,
            progress_color=SLIDER_PROGRESS, button_color=SLIDER_BUTTON,
            button_hover_color=SLIDER_BUTTON_HOVER, fg_color=SLIDER_TRACK
        ).grid(row=row, column=0, sticky="ew", padx=20, pady=(2,10)); row += 1

        radius_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        radius_frame.grid(row=row, column=0, sticky="ew", padx=20, pady=(0,10)); row += 1
        radius_frame.grid_columnconfigure(0, weight=1)
        radius_frame.grid_columnconfigure(1, weight=1)
        self.outer_radius_var = tk.StringVar(value="0")
        self.inner_radius_var = tk.StringVar(value="0")
        for col, label, var in ((0,"Außenradius %",self.outer_radius_var),(1,"Innenradius %",self.inner_radius_var)):
            block = ctk.CTkFrame(radius_frame, fg_color="transparent")
            block.grid(row=0, column=col, sticky="ew", padx=(0,4) if col==0 else (4,0))
            self._label(block, label).pack(fill="x")
            entry = ctk.CTkEntry(block, textvariable=var, fg_color=BG_SOFT, border_color=BORDER)
            entry.pack(fill="x", pady=(3,0))
            entry.bind("<KeyRelease>", lambda _e: self.schedule_preview())

        self._label(self.sidebar, "Farben", section=True).grid(row=row, column=0, sticky="ew", padx=20); row += 1
        self.color_preset_var = tk.StringVar(value=DEFAULT_COLOR_PRESET)
        self._option(
            self.sidebar,
            self.color_preset_var,
            tuple(COLOR_PRESETS.keys()),
            self._color_preset_changed,
        ).grid(row=row, column=0, sticky="ew", padx=20, pady=(6,6)); row += 1

        self.custom_colors = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.custom_colors.grid(row=row, column=0, sticky="ew", padx=20, pady=(0,12)); row += 1
        self.custom_colors.grid_columnconfigure(0, weight=1)
        self.custom_colors.grid_columnconfigure(1, weight=1)

        self.frame_color_var = tk.StringVar(value=DEFAULT_FRAME_COLOR)
        self.accent_color_var = tk.StringVar(value=DEFAULT_ACCENT_COLOR)
        for col, label, var in (
            (0, "Rahmen", self.frame_color_var),
            (1, "Schrift / II / X", self.accent_color_var),
        ):
            block = ctk.CTkFrame(self.custom_colors, fg_color="transparent")
            block.grid(row=0, column=col, sticky="ew", padx=(0,4) if col == 0 else (4,0))
            self._label(block, label).pack(fill="x")
            entry = ctk.CTkEntry(
                block,
                textvariable=var,
                fg_color=INPUT_BG,
                border_color=BORDER,
                text_color=TEXT,
                placeholder_text="#rrggbb",
            )
            entry.pack(fill="x", pady=(3,0))
            entry.bind("<KeyRelease>", lambda _e: self.schedule_preview())
        self.custom_colors.grid_remove()

        self._label(self.sidebar, "Beschriftung", section=True).grid(row=row, column=0, sticky="ew", padx=20); row += 1
        self.caption_var = tk.StringVar(value="")
        caption = ctk.CTkEntry(
            self.sidebar, textvariable=self.caption_var, fg_color=BG_SOFT,
            border_color=BORDER, text_color=TEXT, placeholder_text="Optionaler Untertitel"
        )
        caption.grid(row=row, column=0, sticky="ew", padx=20, pady=(6,6)); row += 1
        caption.bind("<KeyRelease>", lambda _e: self.schedule_preview())

        self.font_var = tk.StringVar(value="Segoe UI")
        self._option(self.sidebar, self.font_var, available_fonts(), lambda _v: self.schedule_preview()).grid(
            row=row, column=0, sticky="ew", padx=20, pady=(0,12)); row += 1

        self._label(self.sidebar, "Dateiformat", section=True).grid(row=row, column=0, sticky="ew", padx=20); row += 1
        self.format_var = tk.StringVar(value="JPEG")
        self._option(self.sidebar, self.format_var, OUTPUT_FORMATS, lambda _v: self.schedule_preview()).grid(
            row=row, column=0, sticky="ew", padx=20, pady=(6,8)); row += 1

        self._button(self.sidebar, "Ausgabeordner …", self.choose_output).grid(
            row=row, column=0, sticky="ew", padx=20, pady=(0,5)); row += 1
        self.output_status = self._label(self.sidebar, "Noch kein Ausgabeordner gewählt")
        self.output_status.grid(row=row, column=0, sticky="ew", padx=20, pady=(0,14)); row += 1

        self.start_button = self._button(self.sidebar, "Batch starten", self.start_batch, primary=True)
        self.start_button.grid(row=row, column=0, sticky="ew", padx=20, pady=(0,8)); row += 1
        self.progress = ctk.CTkProgressBar(
            self.sidebar, progress_color=GOLD, fg_color=PROGRESS_TRACK
        )
        self.progress.set(0)
        self.progress.grid(row=row, column=0, sticky="ew", padx=20, pady=(0,5)); row += 1
        self.status = self._label(self.sidebar, "Bereit")
        self.status.grid(row=row, column=0, sticky="ew", padx=20, pady=(0,22))

        self._mode_changed("Web")

    def _mode_changed(self, value: str) -> None:
        is_web = value == "Web"
        self.size_label.configure(text="Web-Breite" if is_web else "Print (in Aufbau)")
        self.start_button.configure(
            state="normal" if is_web else "disabled",
            text="Batch starten" if is_web else "Print-Batch folgt",
        )
        if is_web:
            self._set_start_button_normal()
        else:
            self._set_start_button_disabled()
        self.schedule_preview()

    def _size_changed(self, value: str) -> None:
        if value == "Benutzerdefiniert":
            self.custom_width.grid()
        else:
            self.custom_width.grid_remove()
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

    def choose_files(self) -> None:
        names = filedialog.askopenfilenames(
            title="Full-SBS-Bilder wählen",
            filetypes=[("Bilder", "*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp"), ("Alle Dateien", "*.*")]
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

    def _float(self, value: str, default: float = 0.0) -> float:
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return default

    def _options(self) -> WebRenderOptions:
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
            output_format=OutputFormat.PNG if self.format_var.get() == "PNG" else OutputFormat.JPEG,
        )

    def schedule_preview(self) -> None:
        if self._preview_job is not None:
            self.after_cancel(self._preview_job)
        self._preview_job = self.after(120, self.update_preview)

    def update_preview(self) -> None:
        self._preview_job = None
        if not self.items or self.mode_var.get() != "Web":
            self.preview_label.configure(
                image="", text="Bild wählen" if not self.items else "Print-Vorschau wird als Nächstes ergänzt"
            )
            return
        item = self.items[0]
        try:
            with Image.open(item.source) as image:
                image.load()
                options = self._options()
                # Preview needs only screen resolution, not a full 3840 px render.
                panel_w = max(500, self.preview_label.winfo_width() - 10)
                preview_width = min(panel_w, options.target_width or image.width)
                preview_options = WebRenderOptions(**{**options.__dict__, "target_width": preview_width})
                rendered = render_web(image.convert("RGB"), preview_options)
            panel_h = max(400, self.preview_label.winfo_height() - 10)
            rendered.thumbnail((panel_w, panel_h), Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(rendered)
            self.preview_label.configure(image=self.preview_photo, text="")
        except Exception as exc:
            self.preview_label.configure(image="", text=f"Vorschaufehler:\\n{exc}")

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
        if self.mode_var.get() != "Web":
            return
        if not self.items:
            messagebox.showinfo("Freeda", "Bitte zuerst Bilder oder einen Ordner wählen.")
            return
        if self.output_dir is None:
            self.choose_output()
            if self.output_dir is None:
                return

        options = self._options()
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
