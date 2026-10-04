from __future__ import annotations

APP_NAME = "Freeda"
APP_VERSION = "0.1.0"

WEB_WIDTH_PRESETS = ("Original", "1280", "1600", "1920", "2048", "3840", "Benutzerdefiniert")
LAYOUTS = ("Parallel + Kreuz", "Parallel", "Kreuz")
OUTPUT_FORMATS = ("JPEG", "PNG")

DEFAULT_FRAME_PERCENT = 1.5
DEFAULT_FRAME_COLOR = "#111111"
DEFAULT_ACCENT_COLOR = "#c6a95e"
DEFAULT_JPEG_QUALITY = 90
DEFAULT_FONT_FAMILY = "Segoe UI"


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
