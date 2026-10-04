from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RowGeometry:
    total_width: int
    eye_width: int
    frame_px: int


def frame_geometry_for_total_width(total_width: int, frame_percent: float, eye_count: int = 2) -> RowGeometry:
    """Return exact row geometry for two or three equally wide eye images.

    The outer left/right frame and centre bar have the same width.  Frame width
    is defined as a percentage of ONE rendered eye image, not of the whole row.
    """
    total_width = max(16, int(total_width))
    if eye_count not in (2, 3):
        raise ValueError("Unsupported eye count")
    bars = eye_count + 1
    fraction = max(0.0, float(frame_percent)) / 100.0
    if fraction == 0:
        return RowGeometry(total_width, total_width // eye_count, 0)

    ideal = total_width * fraction / (eye_count + bars * fraction) if fraction else 0.0
    centre = max(0, int(round(ideal)))

    # Need (total_width - 3*frame) to be even so both eye images are identical.
    candidates = [max(0, centre + delta) for delta in (0, -1, 1, -2, 2, -3, 3)]
    valid = [b for b in candidates if total_width - bars * b >= eye_count and (total_width - bars * b) % eye_count == 0]
    if not valid:
        valid = [0]
    frame = min(valid, key=lambda b: abs(b - ideal))
    eye = (total_width - bars * frame) // eye_count
    return RowGeometry(total_width=total_width, eye_width=eye, frame_px=frame)


def mm_to_px(mm: float, dpi: int) -> int:
    return int(round(float(mm) / 25.4 * int(dpi)))


def print_canvas_px(width_mm: float, height_mm: float, dpi: int, bleed_mm: float = 0.0) -> tuple[int, int]:
    return (
        mm_to_px(width_mm + 2.0 * bleed_mm, dpi),
        mm_to_px(height_mm + 2.0 * bleed_mm, dpi),
    )
