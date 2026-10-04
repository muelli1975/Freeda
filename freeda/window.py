"""Keep window sizing within the monitor work area, including display scaling."""
import sys


def window_sizes(work_width, work_height, scaling, preferred, minimum):
    scaling = max(0.5, float(scaling))
    # Allow for non-client borders and the title bar; work area excludes taskbar.
    available_w = max(1, int(work_width / scaling) - 24)
    available_h = max(1, int(work_height / scaling) - 48)
    initial = (min(preferred[0], available_w), min(preferred[1], available_h))
    smallest = (min(minimum[0], initial[0]), min(minimum[1], initial[1]))
    return initial, smallest


def fit_window(window, preferred, minimum):
    width, height = window.winfo_screenwidth(), window.winfo_screenheight()
    left, top = 0, 0
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        class MonitorInfo(ctypes.Structure):
            _fields_ = [("size", wintypes.DWORD), ("monitor", wintypes.RECT),
                        ("work", wintypes.RECT), ("flags", wintypes.DWORD)]
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
        user32.MonitorFromWindow.restype = wintypes.HANDLE
        user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MonitorInfo)]
        user32.GetMonitorInfoW.restype = wintypes.BOOL
        monitor = user32.MonitorFromWindow(window.winfo_id(), 2)
        info = MonitorInfo()
        info.size = ctypes.sizeof(info)
        if user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            width, height = info.work.right - info.work.left, info.work.bottom - info.work.top
            left, top = info.work.left, info.work.top
    scale = window._get_window_scaling()
    initial, smallest = window_sizes(width, height, scale, preferred, minimum)
    window.minsize(*smallest)
    window.geometry(f"{initial[0]}x{initial[1]}")
    # Geometry sizes are scaled by CTk; offsets remain screen coordinates.
    window.geometry(f"+{left + 12}+{top + 12}")
