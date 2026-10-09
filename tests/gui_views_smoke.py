"""Crop viewing shortcuts, stable crop and asynchronous main/dialog previews."""
import sys, time, tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from PIL import Image
from freeda.gui import FreedaApp, CropDialog
from gui_helpers import assert_family_palette


def wait(app, condition):
    until=time.monotonic()+15
    while time.monotonic()<until:
        app.update()
        if condition():return
        time.sleep(.01)
    raise AssertionError('Preview timeout')

with tempfile.TemporaryDirectory() as folder:
    root=Path(folder)
    image=Image.fromarray(np.random.default_rng(3).integers(0,256,(200,600,3),dtype=np.uint8))
    paths=[root/'one.png',root/'two.png']
    for path in paths:image.save(path)
    app=FreedaApp(settings_path=root/'settings.json',language='en')
    app.update()
    try:
        with patch('freeda.gui.filedialog.askopenfilenames',return_value=[str(paths[0])]):app.choose_files()
        wait(app,lambda:app.preview_photo is not None)
        app.caption_mode_var.set('Text'); app._layout_changed()
        import tkinter as tk
        def entries(parent):
            for child in parent.winfo_children():
                if isinstance(child, tk.Entry) and child.winfo_ismapped(): yield child
                yield from entries(child)
        next(entries(app)).focus_force()
        app.update();app._key(SimpleNamespace(keysym='Next',state=0));assert app.source_index==0
        app.preview_label.focus_force();app.update()
        app._key(SimpleNamespace(keysym='Next',state=0));assert app.source_index==1
        dialog=CropDialog(app,image,app._web_options(),index=1,total=1,filename='two.png',editing=True)
        app.update()
        dialog.zoom_var.set(1.4);dialog._controls_changed()
        crop=dialog.current_crop();original_options=dialog.options
        for key,view in [('x','cross'),('a','anaglyph'),('p','parallel')]:
            dialog.focus_force();app.update()
            before=dialog.preview_photo
            dialog._key(SimpleNamespace(keysym=key,state=0))
            wait(app,lambda:dialog.preview_photo is not None and dialog.preview_photo is not before)
            assert dialog.view==view and dialog.current_crop()==crop and dialog.options==original_options
            assert dialog.preview_photo.width() <= dialog.preview_label.winfo_width()
        assert dialog.view_buttons['cross'].cget('text')=='Cross view (X)'
        assert_family_palette(dialog)
        dialog._cancel();app.update()
    finally:app.destroy()
print('View buttons/P-X-A, stable crop, threaded previews and navigation focus guards passed')
