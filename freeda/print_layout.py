"""One physical layout shared by print export, preview, crops and measurements."""
from dataclasses import dataclass, fields
import math
from .geometry import mm_to_px
from .models import LayoutMode, PrintRenderOptions
from .render import _font, _fit_lrl_caption, _caption_metrics

REFERENCE_DPI = 600


@dataclass(frozen=True)
class PrintLayout:
    width_mm: float
    height_mm: float
    eye_width_mm: float
    eye_height_mm: float
    x_mm: tuple[float, ...]
    y_mm: tuple[float, ...]
    symbol_bands_mm: tuple[float, ...]
    caption_lines: tuple[str, ...]
    caption_font_mm: float
    caption_step_mm: float
    caption_top_mm: float
    caption_bottom_mm: float
    centre_mm: float

    @property
    def eye_aspect(self):
        return self.eye_width_mm / self.eye_height_mm

    @property
    def centre_distance_mm(self):
        return self.eye_width_mm + self.centre_mm

    def eye_boxes(self, dpi, bleed_mm=0):
        offset = mm_to_px(bleed_mm, dpi)
        return tuple((offset + mm_to_px(x, dpi), offset + mm_to_px(y, dpi),
                      offset + mm_to_px(x + self.eye_width_mm, dpi),
                      offset + mm_to_px(y + self.eye_height_mm, dpi))
                     for y in self.y_mm for x in self.x_mm)


def _positive(value, message, *, zero=False):
    if not math.isfinite(value) or value < 0 or (not zero and value == 0):
        raise ValueError(message)
    return value


def print_layout(options: PrintRenderOptions) -> PrintLayout:
    width = _positive(options.width_mm, "Kartenmaße: Bitte positive Werte in mm eingeben.")
    height = _positive(options.height_mm, "Kartenmaße: Bitte positive Werte in mm eingeben.")
    count = 3 if options.layout == LayoutMode.LRL else 2
    rows = 2 if options.layout == LayoutMode.BOTH else 1
    if options.margins is not None:
        m = options.margins
        for field in fields(m):
            _positive(getattr(m, field.name), "Ränder: Bitte endliche Werte ab 0 mm eingeben.", zero=True)
        side, top, centre, bottom, row_gap = m.side_mm, m.top_mm, m.centre_mm, m.bottom_mm, m.row_gap_mm
    else:
        fraction = _positive(options.frame_percent, "Rahmenbreite: Bitte einen Wert ab 0 eingeben.", zero=True) / 100
        side = centre = width * fraction / (count + (count + 1) * fraction)
        top = side
        row_gap = side
        bottom = side
    eye_width = (width - 2 * side - (count - 1) * centre) / count
    if eye_width <= 0:
        raise ValueError("Die Ränder lassen keinen Platz für die Bildfenster.")
    ref_width = max(1, mm_to_px(eye_width, REFERENCE_DPI))
    if options.caption_points is not None:
        size_mm = _positive(options.caption_points, "Schriftgröße: Bitte einen positiven Wert in pt eingeben.") * 25.4 / 72
    else:
        size_mm = eye_width * _positive(options.caption_size_percent,
                    "Untertitelgröße: Bitte einen positiven Wert eingeben.") / 100
    font = _font(options.font_family, max(1, mm_to_px(size_mm, REFERENCE_DPI)))
    text = options.caption
    if count == 3:
        text, font = _fit_lrl_caption(text, font, options.font_family, ref_width)
    lines, step, caption_height = _caption_metrics(text, font, ref_width)
    font_mm = font.size * 25.4 / REFERENCE_DPI
    caption_height_mm = caption_height * 25.4 / REFERENCE_DPI
    gap_top = font_mm * .4 if options.caption_gap_top_mm is None else _positive(
        options.caption_gap_top_mm, "Textabstände: Bitte Werte ab 0 mm eingeben.", zero=True)
    gap_bottom = font_mm * .6 if options.caption_gap_bottom_mm is None else _positive(
        options.caption_gap_bottom_mm, "Textabstände: Bitte Werte ab 0 mm eingeben.", zero=True)
    caption_band = caption_height_mm + gap_top + gap_bottom if text else 0
    if options.margins is not None:
        if caption_band > bottom + 1e-9:
            raise ValueError("Der Untertitel passt nicht in den unteren Bereich. Bereich vergrößern oder Schrift/Text verkleinern.")
        eye_height = (height - top - rows * bottom - (rows - 1) * row_gap) / rows
        y = tuple(top + i * (eye_height + bottom + row_gap) for i in range(rows))
        symbols = (top,) + (row_gap,) * (rows - 1)
    else:
        # The last caption ends with text padding, without another outer frame.
        eye_height = (height - (rows + 1) * side - rows * caption_band + (side if text else 0)) / rows
        y = tuple(side + i * (eye_height + caption_band + side) for i in range(rows))
        symbols = (side,) * rows
    if eye_height <= 0:
        raise ValueError("Das gewählte Druckformat ist für Rahmen und Beschriftung zu niedrig.")
    if min(mm_to_px(eye_width, options.dpi), mm_to_px(eye_height, options.dpi)) < 1:
        raise ValueError("Die Auflösung ist für die Bildfenster zu niedrig.")
    x = tuple(side + i * (eye_width + centre) for i in range(count))
    return PrintLayout(width, height, eye_width, eye_height, x, y, symbols,
                       tuple(lines), font_mm, step * 25.4 / REFERENCE_DPI,
                       gap_top, gap_bottom, centre)
