from __future__ import annotations

APP_NAME = "Freeda"
from . import __version__

APP_VERSION = __version__

WEB_WIDTH_PRESETS = ("Original", "1280", "1600", "1920", "2048", "3840", "Benutzerdefiniert")
LAYOUTS = ("Parallelblick + Kreuzblick", "Parallelblick", "Kreuzblick", "L–R–L")
OUTPUT_FORMATS = ("JPEG", "PNG")

DEFAULT_FRAME_PERCENT = 4.0
DEFAULT_FRAME_COLOR = "#111111"
DEFAULT_ACCENT_COLOR = "#c6a95e"
DEFAULT_JPEG_QUALITY = 90
DEFAULT_FONT_FAMILY = "Segoe UI"

COLOR_PRESETS = {
    "Nachtgold": ("#111111", "#c6a95e"),
    "Schwarzweiß": ("#000000", "#f2f2f2"),
    "Beige": ("#d8cbb8", "#2b2520"),
    "Bordeauxgold": ("#2b161a", "#d8b56a"),
    "Petrolsand": ("#102629", "#d7c39a"),
    "Nachtblau": ("#101826", "#d9e1eb"),
    "Waldgrün": ("#16231b", "#ddd6c4"),
    "Anthrazitkupfer": ("#1e1e1e", "#c9895b"),
    "Rosé": ("#3a2328", "#e8c9cc"),
    "Sepia": ("#2b2119", "#e0c7a0"),
    "Benutzerdefiniert": None,
}
DEFAULT_COLOR_PRESET = "Nachtgold"


# Nominal print sizes in millimetres. Labels follow common German photo-lab
# naming (short side x long side), while values are stored landscape (width, height).
PRINT_FORMAT_PRESETS = {
    "DIN A6 (14,8 × 10,5 cm)": (148.0, 105.0),
    "Foto 9 × 13 cm": (130.0, 90.0),
    "Foto 10 × 15 cm": (150.0, 100.0),
    "Foto 11 × 17 cm": (170.0, 110.0),
    "Foto 13 × 18 cm": (180.0, 130.0),
    "Foto 15 × 20 cm": (200.0, 150.0),
    "Foto 20 × 30 cm": (300.0, 200.0),
    "Stereokarte 7 × 3½ Zoll": (177.8, 88.9),
    "Stereokarte 18 × 9 cm": (180.0, 90.0),
    "Raumbildkarte 13 × 6 cm": (130.0, 60.0),
    "Benutzerdefiniert": None,
}
