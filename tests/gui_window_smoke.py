"""Check the real maximized window against the Windows taskbar work area."""
import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if sys.platform != "win32":
    print("Windows taskbar check: not applicable on this platform")
    raise SystemExit(0)

from freeda.gui import FreedaApp


class MonitorInfo(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("monitor", wintypes.RECT),
                ("work", wintypes.RECT), ("flags", wintypes.DWORD)]


app = FreedaApp(language="de")
try:
    app.state("zoomed")
    app.after(500, app.quit)
    app.mainloop()
    user32 = ctypes.WinDLL("user32")
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND
    user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.MonitorFromWindow.restype = wintypes.HANDLE
    user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MonitorInfo)]
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    hwnd = user32.GetAncestor(app.winfo_id(), 2)
    info = MonitorInfo()
    info.size = ctypes.sizeof(info)
    assert user32.GetMonitorInfoW(user32.MonitorFromWindow(hwnd, 2), ctypes.byref(info))
    rect = wintypes.RECT()
    assert user32.GetClientRect(hwnd, ctypes.byref(rect))
    origin = wintypes.POINT(0, 0)
    assert user32.ClientToScreen(hwnd, ctypes.byref(origin))
    assert origin.y + rect.bottom <= info.work.bottom
    assert origin.x + rect.right <= info.work.right
    print("Maximized client area fits above the Windows taskbar.")
finally:
    app.destroy()
