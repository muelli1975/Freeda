from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from .fonts import resolve_font, available_fonts
from .cropping import fit_linked_crop
from .geometry import RowGeometry, frame_geometry_for_total_width
from .models import DEFAULT_LOGO_HEIGHT_PERCENT, CaptionMode, Crop, EyeShape, LayoutMode, OutputFormat, WebRenderOptions
from .eye_shapes import shape_eye, round_outer_corners
from .logos import load_logo, logo_layout


def split_full_sbs(image: Image.Image) -> tuple[Image.Image, Image.Image]:
    width, height = image.size
    half = width // 2
    if half < 1:
        raise ValueError("Das Side-by-Side-Bild ist zu schmal.")
    left = image.crop((0, 0, half, height))
    # Match StereoFine's tolerant split: a lone centre pixel is excluded.
    right = image.crop((width - half, 0, width, height))
    return left, right


def crop_eye(image: Image.Image, crop: Crop) -> Image.Image:
    c = crop.clamped()
    width, height = image.size
    left = int(round(c.x * width))
    top = int(round(c.y * height))
    right = int(round((c.x + c.width) * width))
    bottom = int(round((c.y + c.height) * height))
    right = max(left + 1, min(width, right))
    bottom = max(top + 1, min(height, bottom))
    return image.crop((left, top, right, bottom))


@lru_cache(maxsize=128)
def _font(family: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    target = resolve_font(family)
    if target:
        try:
            return ImageFont.truetype(target, max(1, int(size)))
        except OSError:
            pass
    return ImageFont.load_default(size=max(1, int(size)))


def _text_height(font: ImageFont.ImageFont, text: str) -> int:
    box = font.getbbox(text or "Ag")
    return max(1, box[3] - box[1])


def _symbol_style(frame: int, symbol: str):
    family = available_fonts()[0]
    font = _font(family, max(8, frame))
    while _text_height(font, symbol) > max(1, frame - 2) and getattr(font, "size", 8) > 8:
        font = _font(family, font.size - 1)
    return font, max(0, (frame - _text_height(font, symbol)) // 2)


def _draw_centered(draw: ImageDraw.ImageDraw, text: str, center_x: int, y: int, font, fill: str) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    width = box[2] - box[0]
    draw.text((center_x - width / 2, y - box[1]), text, font=font, fill=fill)


def _fit_lrl_caption(text, font, family, width, *, shrink=True):
    """Keep stereo-identical LRL captions in one eye-wide line."""
    text = " ".join(text.split())
    if not text:
        return text, font
    size = getattr(font, "size", 9)
    minimum = max(9, round(size * .75)) if shrink else size
    while font.getlength(text) > width and size > minimum:
        size -= 1
        font = _font(family, size)
    if font.getlength(text) <= width:
        return text, font
    suffix = "…"
    if font.getlength(suffix) > width:
        return "", font
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if font.getlength(text[:middle].rstrip() + suffix) <= width:
            low = middle
        else:
            high = middle - 1
    return text[:low].rstrip() + suffix, font


def _caption_lines(text, font, width):
    lines = []
    width = max(1, width)
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            trial = (line + " " + word).strip()
            if font.getlength(trial) <= width:
                line = trial
                continue
            if line:
                lines.append(line)
                line = ""
            for char in word:
                if line and font.getlength(line + char) > width:
                    lines.append(line)
                    line = ""
                line += char
        lines.append(line)
    return lines if text else []


def _caption_metrics(text, font, width):
    lines = _caption_lines(text, font, width)
    glyph_height = max([_text_height(font, "Ag")] + [_text_height(font, line) for line in lines])
    leading = max(2, round(getattr(font, "size", 10) * .2))
    return lines, glyph_height + leading, len(lines) * glyph_height + max(0, len(lines) - 1) * leading


def _draw_caption(draw, text, center, y, font, fill, width):
    lines, step, _ = _caption_metrics(text, font, width)
    for index, line in enumerate(lines):
        _draw_centered(draw, line, center, y + index * step, font, fill)


def _rounded_eye(image: Image.Image, radius: int) -> Image.Image:
    return shape_eye(image, radius)


def _draw_symbols(draw, positions, eye_w, frame, symbol, accent_color):
    markers = [(x + eye_w // 2, symbol) for x in positions]
    if len(positions) == 3:
        markers = [(positions[1] - frame // 2, "II"), (positions[2] - frame // 2, "X")]
    for center, marker in markers:
        font, y = _symbol_style(frame, marker)
        if frame >= _text_height(font, marker):
            _draw_centered(draw, marker, center, y, font, accent_color)


@dataclass(frozen=True)
class WebRowLayout:
    geometry: RowGeometry
    eye_height: int
    caption: str
    font: object
    gap_top: int
    band_height: int
    logo: Image.Image | None
    logo_size: tuple[int, int] | None

    @property
    def height(self):
        return self.eye_height + self.band_height + 2 * self.geometry.frame_px


def _web_row_layout(eye_size, *, total_width, frame_percent, caption, font_family,
                    caption_size_percent, eye_count=2, caption_mode=CaptionMode.TEXT,
                    logo_path=None, logo_height_percent=DEFAULT_LOGO_HEIGHT_PERCENT):
    geom = frame_geometry_for_total_width(total_width, frame_percent, eye_count)
    eye_h = max(1, round(geom.eye_width * eye_size[1] / eye_size[0]))
    font = _font(font_family, max(9, round(geom.eye_width * caption_size_percent / 100)))
    if eye_count == 3:
        caption, font = _fit_lrl_caption(caption, font, font_family, geom.eye_width)
    _, _, caption_h = _caption_metrics(caption, font, geom.eye_width)
    gap = max(1, round(font.size * .4)) if caption else 0
    band = caption_h + gap + max(1, round(font.size * .6)) if caption else 0
    logo, size = None, None
    if caption_mode == CaptionMode.LOGO:
        logo = load_logo(logo_path)
        footer = logo_layout(logo.size, geom.eye_width, logo_height_percent)
        size = (max(1, round(footer.width)), max(1, round(footer.height)))
        gap = max(1, round(footer.gap_top))
        band = size[1] + gap + max(1, round(footer.gap_bottom))
    return WebRowLayout(geom, eye_h, caption, font, gap, band, logo, size)


@dataclass(frozen=True)
class WebGeometry:
    row: WebRowLayout
    eye_count: int
    rows: int
    native_size: tuple[int, int]
    output_size: tuple[int, int]

    @property
    def eye_boxes(self):
        geom = self.row.geometry
        count = self.eye_count
        boxes = []
        for row in range(self.rows):
            y = geom.frame_px + row * (self.row.height - geom.frame_px)
            for index, x in enumerate(self._positions):
                width = geom.total_width - x if geom.frame_px == 0 and index == count - 1 else geom.eye_width
                boxes.append((x, y, x + width, y + self.row.eye_height))
        return tuple(boxes)

    @property
    def _positions(self):
        geom = self.row.geometry
        return tuple(geom.frame_px + i * (geom.eye_width + geom.frame_px) for i in range(self.eye_count))


def web_geometry(eye_size, options):
    """Measure before resampling the eyes; the final long edge is exact."""
    count = 3 if options.layout == LayoutMode.LRL else 2
    rows = 2 if options.layout == LayoutMode.BOTH else 1
    has_caption = options.caption_mode == CaptionMode.LOGO or bool(options.caption)
    def measure(width):
        row = _web_row_layout(eye_size, total_width=width, frame_percent=options.frame_percent,
            caption=options.caption, font_family=options.font_family, caption_size_percent=options.caption_size_percent,
            eye_count=count, caption_mode=options.caption_mode, logo_path=options.logo_path,
            logo_height_percent=options.logo_height_percent)
        height = rows * row.height - (rows - 1 + int(has_caption)) * row.geometry.frame_px
        return row, (row.geometry.total_width, height)
    edge = options.target_long_edge
    if edge is None:
        width = count * eye_size[0] + (count + 1) * round(eye_size[0] * max(0, options.frame_percent) / 100)
        if count == 2 and width % 2:
            width += 1
        row, size = measure(width)
        return WebGeometry(row, count, rows, size, size)
    if isinstance(edge, bool) or not isinstance(edge, int) or edge < 16:
        raise ValueError("Lange Seite: Bitte eine ganze Zahl ab 16 px eingeben.")
    row, native = measure(edge)
    if native[1] > edge:
        # Font metrics and integer frame widths can add a few pixels. Choose
        # the closest layout, then correct only the remaining pixel rounding.
        best = (row, native)
        low, high = 16, edge - 1
        while low <= high:
            width = (low + high) // 2
            candidate, size = measure(width)
            if abs(size[1] - edge) < abs(best[1][1] - edge):
                best = candidate, size
            if size[1] < edge:
                low = width + 1
            else:
                high = width - 1
        row, native = best
    if native[0] >= native[1]:
        output = (edge, max(1, round(native[1] * edge / native[0])))
    else:
        output = (max(1, round(native[0] * edge / native[1])), edge)
    return WebGeometry(row, count, rows, native, output)


def _row(
    left: Image.Image,
    right: Image.Image,
    *,
    total_width: int,
    frame_percent: float,
    frame_color: str,
    accent_color: str,
    symbol: str,
    caption: str,
    font_family: str,
    caption_size_percent: float,
    inner_radius_percent: float,
    eye_count: int = 2,
    show_symbols: bool = True,
    eye_shape: EyeShape = EyeShape.ROUNDED,
    arch_height_percent: float = 18.0,
    caption_mode: CaptionMode = CaptionMode.TEXT,
    logo_path: Path | None = None,
    logo_height_percent: float = DEFAULT_LOGO_HEIGHT_PERCENT,
    bottom_radius_percent: float | None = None,
) -> Image.Image:
    metrics = _web_row_layout(left.size, total_width=total_width, frame_percent=frame_percent,
        caption=caption, font_family=font_family, caption_size_percent=caption_size_percent,
        eye_count=eye_count, caption_mode=caption_mode, logo_path=logo_path, logo_height_percent=logo_height_percent)
    geom = metrics.geometry
    eye_w = geom.eye_width
    frame = geom.frame_px

    eye_h, caption_font, caption = metrics.eye_height, metrics.font, metrics.caption
    caption_gap, caption_band = metrics.gap_top, metrics.band_height
    logo = metrics.logo.resize(metrics.logo_size, Image.Resampling.LANCZOS) if metrics.logo is not None else None

    height = frame + eye_h + caption_band + frame
    row = Image.new("RGBA", (total_width, height), frame_color)
    draw = ImageDraw.Draw(row)

    positions = [frame + index * (eye_w + frame) for index in range(eye_count)]
    image_y = frame

    radius = max(0, round(eye_w * max(0.0, inner_radius_percent) / 100.0))
    bottom_radius = None if bottom_radius_percent is None else max(0, round(eye_w * bottom_radius_percent / 100))
    eyes = (left, right, left) if eye_count == 3 else (left, right)
    for index, (x, eye) in enumerate(zip(positions, eyes)):
        # Fill integer rounding remainder without introducing an outer strip.
        width = total_width - x if frame == 0 and index == eye_count - 1 else eye_w
        eye = eye.resize((width, eye_h), Image.Resampling.LANCZOS)
        row.alpha_composite(shape_eye(eye, radius, eye_shape, arch_height_percent,
                                     bottom_radius=bottom_radius), (x, image_y))
    if show_symbols and frame > 0:
        _draw_symbols(draw, positions, eye_w, frame, symbol, accent_color)

    if logo is not None:
        for x in positions:
            row.alpha_composite(logo, (x + (eye_w - logo.width) // 2, image_y + eye_h + caption_gap))
    elif caption:
        caption_y = image_y + eye_h + caption_gap
        for x in positions:
            _draw_caption(draw, caption, x + eye_w // 2, caption_y, caption_font, accent_color, eye_w)

    return row


def render_web(source: Image.Image, options: WebRenderOptions) -> Image.Image:
    left, right = split_full_sbs(source)
    crop = fit_linked_crop(left.size, options.crop, options.eye_aspect)
    left = crop_eye(left, crop)
    right = crop_eye(right, crop)

    geometry = web_geometry(left.size, options)
    target_width = geometry.native_size[0]

    rows: list[Image.Image] = []
    if options.layout in (LayoutMode.BOTH, LayoutMode.PARALLEL, LayoutMode.LRL):
        rows.append(_row(
            left, right,
            total_width=target_width,
            frame_percent=options.frame_percent,
            frame_color=options.frame_color,
            accent_color=options.accent_color,
            symbol="II",
            caption=options.caption,
            font_family=options.font_family,
            caption_size_percent=options.caption_size_percent,
            inner_radius_percent=options.inner_radius_percent,
            bottom_radius_percent=options.bottom_radius_percent,
            eye_count=3 if options.layout == LayoutMode.LRL else 2,
            show_symbols=options.show_symbols,
            eye_shape=options.eye_shape,
            arch_height_percent=options.arch_height_percent,
            caption_mode=options.caption_mode,
            logo_path=options.logo_path,
            logo_height_percent=options.logo_height_percent,
        ))
    if options.layout in (LayoutMode.BOTH, LayoutMode.CROSS):
        rows.append(_row(
            right, left,
            total_width=target_width,
            frame_percent=options.frame_percent,
            frame_color=options.frame_color,
            accent_color=options.accent_color,
            symbol="X",
            caption=options.caption,
            font_family=options.font_family,
            caption_size_percent=options.caption_size_percent,
            inner_radius_percent=options.inner_radius_percent,
            bottom_radius_percent=options.bottom_radius_percent,
            show_symbols=options.show_symbols,
            eye_shape=options.eye_shape,
            arch_height_percent=options.arch_height_percent,
            caption_mode=options.caption_mode,
            logo_path=options.logo_path,
            logo_height_percent=options.logo_height_percent,
        ))

    if (options.caption_mode == CaptionMode.LOGO or options.caption) and rows:
        frame = frame_geometry_for_total_width(target_width, options.frame_percent,
            3 if options.layout == LayoutMode.LRL else 2).frame_px
        last = rows[-1]
        rows[-1] = last.crop((0, 0, last.width, last.height - frame))

    if len(rows) == 1:
        result = rows[0]
    else:
        frame = frame_geometry_for_total_width(target_width, options.frame_percent).frame_px
        height = sum(row.height for row in rows) - frame * (len(rows) - 1)
        result = Image.new("RGBA", (target_width, height), options.frame_color)
        y = 0
        for index, row in enumerate(rows):
            result.alpha_composite(row, (0, y))
            y += row.height
            if index + 1 < len(rows):
                y -= frame

    radius = max(0, round(result.width * max(0.0, options.outer_radius_percent) / 100.0))
    result = round_outer_corners(result, radius)
    if result.size != geometry.output_size:
        result = result.resize(geometry.output_size, Image.Resampling.LANCZOS)
    return result


def flatten_for_jpeg(image: Image.Image, background_color: str = "#000000") -> Image.Image:
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, background_color)
        background.paste(image, mask=image.getchannel("A"))
        return background
    return image.convert("RGB")


def save_render(
    image: Image.Image,
    path: Path,
    output_format: OutputFormat,
    *,
    dpi: int | None = None,
    background_color: str = "#000000",
    metadata_source: Path | None = None,
    cancel=None,
):
    import os
    import tempfile
    from .jobs import check_cancel
    path = Path(path).with_suffix(".png" if output_format == OutputFormat.PNG else ".jpg")
    if metadata_source is not None and path.resolve() == Path(metadata_source).resolve():
        raise ValueError("Originaldatei darf nicht verändert werden.")
    check_cancel(cancel)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".freeda-export-", suffix=path.suffix, dir=path.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        kwargs = {"dpi": (dpi, dpi)} if dpi else {}
        if output_format == OutputFormat.PNG:
            image.save(temporary, format="PNG", optimize=True, **kwargs)
        else:
            # 4:4:4 = subsampling 0. JPEG cannot carry transparency.
            image = flatten_for_jpeg(image, background_color)
            image.save(temporary, format="JPEG", quality=90, subsampling=0, optimize=True, **kwargs)
        check_cancel(cancel)
        metadata = None
        if metadata_source is not None:
            from .metadata import copy_metadata
            metadata = copy_metadata(metadata_source, temporary, image.size, dpi=dpi, cancel=cancel)
        check_cancel(cancel)
        os.replace(temporary, path)
        return metadata
    finally:
        temporary.unlink(missing_ok=True)
