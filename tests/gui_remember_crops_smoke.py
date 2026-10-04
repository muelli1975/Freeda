import json, shutil, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
from freeda.gui import FreedaApp
from freeda.batch import discover_files
from freeda.models import Crop
from freeda.crop_storage import FILENAME, load_crops
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    folder=root/"pictures"
    folder.mkdir()
    source=folder/"one.png"
    Image.new("RGB",(600,200),"red").save(source)
    crop=Crop(.1,.2,.7,.6)
    app=FreedaApp(settings_path=root/"settings.json")
    app.withdraw()
    try:
        assert not app.remember_crops_var.get()
        app.items=discover_files([source])
        app._input_changed()
        app._store_crop(app.items[0],"Web",crop)
        assert not (folder/FILENAME).exists()
        app.remember_crops_var.set(True)
        app._remember_crops_changed()
        assert load_crops(folder)[source.name]["Web"] == crop
        app._store_crop(app.items[0],"Print",Crop(.2,.1,.5,.8))
        app.remember_crops_var.set(False)
        app._remember_crops_changed()
        before=(folder/FILENAME).read_bytes()
        app._store_crop(app.items[0],"Web",Crop())
        assert (folder/FILENAME).read_bytes()==before
        assert app._current_crop("Web")==Crop()
        app.remember_crops_var.set(True)
        app._remember_crops_changed()
        assert app._current_crop("Web")==crop
        app.mode_var.set("Web")
        app.reset_crop()
        assert "Web" not in load_crops(folder)[source.name]
        assert "Print" in load_crops(folder)[source.name]
        app._store_crop(app.items[0],"Web",crop)
        moved=root/"moved"
        shutil.move(str(folder),str(moved))
        # Open a fresh session: loading is opt-in and independent of program location.
        fresh=FreedaApp(settings_path=root/"new-program"/"settings.json")
        fresh.withdraw()
        try:
            fresh.items=discover_files([moved/source.name])
            fresh._input_changed()
            assert fresh._current_crop("Web")==Crop()
            assert fresh.language=="de" and fresh.size_var.get()=="2048"
            fresh.remember_crops_var.set(True)
            fresh._remember_crops_changed()
            assert fresh._current_crop("Web")==crop
            fresh._language_changed("English")
            assert fresh.remember_crops_checkbox.cget("text")=="Remember image crops"
        finally:
            fresh.destroy()
        assert not app.crop_storage_errors
    finally:
        app.destroy()
print("Optional crop storage, off/on, separate modes, reset, moved folders and German startup defaults passed")
