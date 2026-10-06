"""Identical, antialiased image-window masks for Web, Print and crop grids."""
from PIL import Image, ImageDraw, ImageChops
from .models import EyeShape


def eye_mask(size, radius=0, shape=EyeShape.ROUNDED, arch_height_percent=18.0):
    width, height = size
    if shape == EyeShape.RECTANGLE or (shape != EyeShape.ARCH and radius <= 0):
        return Image.new("L", size, 255)
    # Keep large print masks within a reasonable working-memory budget.
    scale = 4 if width * height <= 2_000_000 else 2
    w, h = width * scale, height * scale
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    if shape == EyeShape.ARCH:
        depth = min(max(0, h - scale), max(0, round(width * arch_height_percent / 100 * scale)))
        if depth == 0:
            return Image.new("L", size, 255)
        draw.ellipse((0, 0, w - 1, 2 * depth - 1), fill=255)
        draw.rectangle((0, depth, w - 1, h - 1), fill=255)
    else:
        r = min(max(0, round(radius * scale)), w // 2, h // 2)
        draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
        if shape == EyeShape.TOP_ROUNDED:
            draw.rectangle((0, r, w - 1, h - 1), fill=255)
    return mask.resize(size, Image.Resampling.LANCZOS)


def shape_eye(image, radius=0, shape=EyeShape.ROUNDED, arch_height_percent=18.0):
    result = image.convert("RGBA")
    result.putalpha(eye_mask(result.size, radius, shape, arch_height_percent))
    return result


def round_outer_corners(image, radius):
    if radius <= 0:
        return image
    result = image.convert("RGBA")
    result.putalpha(ImageChops.multiply(result.getchannel("A"), eye_mask(result.size, radius)))
    return result
