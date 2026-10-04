from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .fonts import resolve_font
from .cropping import fit_linked_crop
from .geometry import frame_geometry_for_total_width
from .models import Crop, LayoutMode, OutputFormat, WebRenderOptions


def split_full_sbs(image: Image.Image) -> tuple[Image.Image, Image.Image]:
    width, height = image.size
    half = width // 2
    if half < 1:
        raise ValueError("Das Side-by-Side-Bild ist zu schmal.")
    left = image.crop((0, 0, half, height))
    right = image.crop((half, 0, half * 2, height))
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


def _font(family: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    target = resolve_font(family)
    if target:
        try:
            return ImageFont.truetype(target, max(8, int(size)))
        except OSError:
            pass
    return ImageFont.load_default(size=max(8, int(size)))


def _text_height(font: ImageFont.ImageFont, text: str) -> int:
    box = font.getbbox(text or "Ag")
    return max(1, box[3] - box[1])


def _symbol_style(family: str, frame: int, symbol: str):
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
    line_height = _text_height(font, "Ag") + max(2, round(getattr(font, "size", 10) * .2))
    return lines, line_height, len(lines) * line_height


def _draw_caption(draw, text, center, y, font, fill, width):
    lines, step, _ = _caption_metrics(text, font, width)
    for index, line in enumerate(lines):
        _draw_centered(draw, line, center, y + index * step, font, fill)


def _rounded_eye(image: Image.Image, radius: int) -> Image.Image:
    image = image.convert("RGBA")
    if radius <= 0:
        return image
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width - 1, image.height - 1), radius=radius, fill=255)
    image.putalpha(mask)
    return image


def _draw_symbols(draw, positions, eye_w, frame, family, symbol, accent_color):
    markers = [(x + eye_w // 2, symbol) for x in positions]
    if len(positions) == 3:
        markers = [(positions[1] - frame // 2, "II"), (positions[2] - frame // 2, "X")]
    for center, marker in markers:
        font, y = _symbol_style(family, frame, marker)
        if frame >= _text_height(font, marker):
            _draw_centered(draw, marker, center, y, font, accent_color)


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
) -> Image.Image:
    geom = frame_geometry_for_total_width(total_width, frame_percent, eye_count)
    eye_w = geom.eye_width
    frame = geom.frame_px

    aspect = left.height / left.width
    eye_h = max(1, int(round(eye_w * aspect)))
    left = left.resize((eye_w, eye_h), Image.Resampling.LANCZOS)
    right = right.resize((eye_w, eye_h), Image.Resampling.LANCZOS)

    symbol_font, symbol_y = _symbol_style(font_family, frame, symbol)
    caption_font = _font(font_family, max(9, round(eye_w * caption_size_percent / 100)))
    if eye_count == 3:
        caption, caption_font = _fit_lrl_caption(caption, caption_font, font_family, eye_w)
    _, _, caption_h = _caption_metrics(caption, caption_font, eye_w)

    caption_gap = max(frame, round(eye_w * 0.010)) if caption else 0
    caption_band = caption_h + 2 * caption_gap if caption else 0

    height = frame + eye_h + caption_band + frame
    row = Image.new("RGBA", (total_width, height), frame_color)
    draw = ImageDraw.Draw(row)

    positions = [frame + index * (eye_w + frame) for index in range(eye_count)]
    image_y = frame

    radius = max(0, round(eye_w * max(0.0, inner_radius_percent) / 100.0))
    eyes = (left, right, left) if eye_count == 3 else (left, right)
    for x, eye in zip(positions, eyes):
        row.alpha_composite(_rounded_eye(eye, radius), (x, image_y))
    _draw_symbols(draw, positions, eye_w, frame, font_family, symbol, accent_color)

    if caption:
        caption_y = image_y + eye_h + caption_gap
        for x in positions:
            _draw_caption(draw, caption, x + eye_w // 2, caption_y, caption_font, accent_color, eye_w)

    return row


def render_web(source: Image.Image, options: WebRenderOptions) -> Image.Image:
    left, right = split_full_sbs(source)
    crop = fit_linked_crop(left.size, options.crop, options.eye_aspect)
    left = crop_eye(left, crop)
    right = crop_eye(right, crop)

    if options.target_width is None:
        # Preserve the two source-eye widths and add the proportional frame.
        fraction = max(0.0, options.frame_percent) / 100.0
        eye_count = 3 if options.layout == LayoutMode.LRL else 2
        target_width = eye_count * left.width + (eye_count + 1) * round(left.width * fraction)
        if eye_count == 2 and target_width % 2 == 1:
            target_width += 1
    else:
        target_width = int(options.target_width)

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
            eye_count=3 if options.layout == LayoutMode.LRL else 2,
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
        ))

    if options.caption and rows:
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
    if radius > 0:
        mask = Image.new("L", result.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, result.width - 1, result.height - 1), radius=radius, fill=255)
        result.putalpha(mask)

    return result


def save_render(
    image: Image.Image,
    path: Path,
    output_format: OutputFormat,
    *,
    dpi: int | None = None,
    background_color: str = "#111111",
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {}
    if dpi:
        kwargs["dpi"] = (dpi, dpi)
    if output_format == OutputFormat.PNG:
        image.save(path.with_suffix(".png"), format="PNG", optimize=True, **kwargs)
    else:
        # 4:4:4 = subsampling 0.  Alpha is flattened onto the frame colour by
        # the caller/rendering defaults; JPEG itself cannot carry transparency.
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, background_color)
            background.paste(image, mask=image.getchannel("A"))
            image = background
        image.convert("RGB").save(
            path.with_suffix(".jpg"),
            format="JPEG",
            quality=90,
            subsampling=0,
            optimize=True,
            **kwargs,
        )
