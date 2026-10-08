"""Pump the native UI while asynchronous discovery, cropping and export run."""
import time


def wait_for_job(app, timeout=40):
    deadline = time.monotonic() + timeout
    def poll():
        if not app._busy or time.monotonic() >= deadline:
            app.quit()
        else:
            app.after(20, poll)
    app.after(20, poll)
    app.mainloop()
    assert not app._busy, "Processing did not finish within the test deadline"


def assert_family_palette(root):
    """Inspect actual widget colors, including hidden controls and disabled states."""
    import tkinter as tk
    palette = {"#111111", "#181818", "#202020", "#282828", "#333333", "#f2f2f2",
               "#b8b8b8", "#727272", "#9c7c38", "#c6a95e", "#000000", "#7f3939", "#944545"}
    def visit(widget):
        if type(widget).__name__.startswith("CTk"):
            for option in ("fg_color", "bg_color", "border_color", "hover_color", "text_color",
                           "text_color_disabled", "button_color", "button_hover_color", "progress_color",
                           "scrollbar_button_color", "scrollbar_button_hover_color", "placeholder_text_color",
                           "dropdown_fg_color", "dropdown_hover_color", "dropdown_text_color"):
                try:
                    if option == "border_color" and widget.cget("border_width") == 0:
                        continue
                    color = widget.cget(option)
                except (ValueError, AttributeError, tk.TclError):
                    continue
                if isinstance(color, (list, tuple)):
                    color = color[-1]
                if not color or color == "transparent":
                    continue
                rgb = "#" + "".join(f"{part//257:02x}" for part in root.winfo_rgb(color))
                assert rgb in palette, (type(widget).__name__, option, color, rgb)
        for child in widget.winfo_children():
            visit(child)
    visit(root)
