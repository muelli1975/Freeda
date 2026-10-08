import sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
from freeda.gui import FreedaApp
from freeda.batch import discover_files
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp).resolve()
    short=root/"short.png"
    long=root/("very_long_stereo_filename_"*8+".png")
    for path in (short,long):
        Image.new("RGB",(600,200),"red").save(path)
    app=FreedaApp(settings_path=root/"settings.json")
    try:
        app.items=discover_files([short])
        app._input_changed()
        app.update()
        initial=app.sidebar_container.winfo_width()
        app.items=discover_files([long])
        app._input_changed()
        app.update()
        assert app.sidebar_container.winfo_width()==initial
        assert app.preview_panel.winfo_width()>500
        assert app.navigation_status.cget("wraplength")>0
    finally:
        app.destroy()
print("Long filenames cannot widen the sidebar")
