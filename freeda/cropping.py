"""Linked stereo crops and validated per-eye aspect ratios."""
import math
from .models import Crop

def parse_aspect(value):
    if value == "Original":
        return None
    try:
        parts = value.strip().replace(",", ".").split(":")
        numbers = [float(part) for part in parts]
        if any(not math.isfinite(number) or number <= 0 for number in numbers):
            raise ValueError
        ratio = numbers[0] / numbers[1] if len(numbers) == 2 else numbers[0]
        if len(parts) > 2 or not math.isfinite(ratio) or ratio <= 0:
            raise ValueError
        return ratio
    except (ValueError, ZeroDivisionError):
        raise ValueError("Seitenverhältnis: Bitte positive Werte eingeben, z. B. 4:3.") from None

def fit_linked_crop(image_size, crop, aspect):
    crop = crop.clamped()
    if aspect is None:
        return crop
    w, h = image_size
    actual = w * crop.width / (h * crop.height)
    if actual > aspect:
        width = crop.width * aspect / actual
        return Crop(crop.x + (crop.width-width)/2, crop.y, width, crop.height)
    height = crop.height * actual / aspect
    return Crop(crop.x, crop.y + (crop.height-height)/2, crop.width, height)
