"""Keep existing contour presets visually identical in the simplified controls."""

ROUNDED_RECTANGLE = "Rechteck / gerundete Ecken"


def migrate_contour(values):
    result = dict(values)
    shape = result.get("eye_shape_var", "Alle Ecken gerundet")
    if shape == "Rechteckig":
        result.update(eye_shape_var=ROUNDED_RECTANGLE, inner_radius_var="0", bottom_radius_var="0")
    elif shape in ("Alle Ecken gerundet", "Nur obere Ecken gerundet"):
        radius = result.get("inner_radius_var", "0")
        result.update(eye_shape_var=ROUNDED_RECTANGLE, inner_radius_var=radius,
                      bottom_radius_var=radius if shape == "Alle Ecken gerundet" else "0")
    return result
