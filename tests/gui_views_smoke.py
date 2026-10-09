"""Crop viewing shortcuts, stable crop and asynchronous main/dialog previews."""
import sys, time, tempfile, base64, io, json
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from PIL import Image, ImageGrab
from freeda.gui import FreedaApp, CropDialog
from freeda.models import LayoutMode
import customtkinter as ctk
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
    settings_path=root/'settings.json'
    settings_path.write_text(json.dumps({'unrelated_preference': 'keep me'}),encoding='utf-8')
    app=FreedaApp(settings_path=settings_path,language='en')
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
        assert app.crop_view is None and app.crop_grid is True
        for layout,expected in ((LayoutMode.PARALLEL,'parallel'),(LayoutMode.CROSS,'cross')):
            initial=CropDialog(app,image,replace(app._web_options(),layout=layout),
                index=1,total=1,filename='one.png',editing=True)
            app.update()
            assert initial.view==expected and initial.grid_var.get() is True
            initial._cancel();app.update()
        assert 'crop_view' not in json.loads(settings_path.read_text(encoding='utf-8'))
        dialog=CropDialog(app,image,app._web_options(),index=1,total=1,filename='two.png',editing=True)
        app.update()
        dialog.zoom_var.set(1.4);dialog._controls_changed()
        crop=dialog.current_crop();original_options=dialog.options
        for enabled in (False,True,False):
            before=dialog.preview_photo
            dialog.grid_checkbox.invoke()
            wait(app,lambda:dialog.preview_photo is not None and dialog.preview_photo is not before)
            assert dialog.grid_var.get() is enabled and app.crop_grid is enabled
            assert dialog.current_crop()==crop and dialog.options==original_options
            saved=json.loads(settings_path.read_text(encoding='utf-8'))
            assert saved['crop_grid'] is enabled and saved['unrelated_preference']=='keep me'
        assert app.image_crops=={'Web':{},'Print':{}}
        for key,view in [('x','cross'),('a','anaglyph'),('p','parallel')]:
            dialog.focus_force();app.update()
            before=dialog.preview_photo
            dialog._key(SimpleNamespace(keysym=key,state=0))
            wait(app,lambda:dialog.preview_photo is not None and dialog.preview_photo is not before)
            assert dialog.view==view and dialog.current_crop()==crop and dialog.options==original_options
            assert dialog.preview_photo.width() <= dialog.preview_label.winfo_width()
            saved=json.loads(settings_path.read_text(encoding='utf-8'))
            assert saved['crop_view']==view and saved['unrelated_preference']=='keep me'
            assert app.image_crops=={'Web':{},'Print':{}}
        assert dialog.view_buttons['cross'].cget('text')=='Cross view (X)'
        assert_family_palette(dialog)
        dialog._cancel();app.update()
        for view in ('parallel','cross','anaglyph'):
            next_options=replace(app._web_options(),layout=LayoutMode.CROSS)
            next_dialog=CropDialog(app,image,next_options,index=2,total=2,filename='two.png')
            app.update()
            assert next_dialog.view==app.crop_view and next_dialog.grid_var.get() is False
            before_crop=next_dialog.current_crop()
            next_dialog.view_buttons[view].invoke()
            assert next_dialog.view==view and next_dialog.options==next_options
            assert next_dialog.current_crop()==before_crop
            next_dialog._cancel();app.update()
            reopened=CropDialog(app,image,replace(next_options,layout=LayoutMode.PARALLEL),
                index=1,total=2,filename='one.png',editing=True)
            app.update()
            assert reopened.view==view and reopened.grid_var.get() is False
            reopened._cancel();app.update()
        for language in ('de','en'):
            app.language=language
            for scale in (1.,1.5):
                ctk.set_widget_scaling(scale)
                ctk.set_window_scaling(scale)
                dialog=CropDialog(app,image,app._web_options(),index=1,total=1,
                    filename='two.png',editing=True)
                app.update()
                dialog.grid_var.set(False)
                dialog._set_view('anaglyph')
                wait(app,lambda:dialog.preview_photo is not None)
                expected_heading='Ansicht zur Ausschnittwahl' if language=='de' else 'View for crop selection'
                expected_hint='Die Ansicht beeinflusst nur die Vorschau.' if language=='de' else 'This view only affects the preview.'
                assert dialog.view_heading.cget('text')==expected_heading
                assert dialog.view_hint.cget('text')==expected_hint
                assert next(child for child in dialog.view_heading.winfo_children() if isinstance(child, tk.Label)).winfo_reqwidth() <= dialog.view_heading.winfo_width()
                assert next(child for child in dialog.view_hint.winfo_children() if isinstance(child, tk.Label)).winfo_reqwidth() <= dialog.view_hint.winfo_width()
                app.update_idletasks()
                if language in ('de', 'en'):
                    bbox=(dialog.winfo_rootx(),dialog.winfo_rooty(),
                          dialog.winfo_rootx()+dialog.winfo_width(),dialog.winfo_rooty()+dialog.winfo_height())
                    buffer=io.BytesIO()
                    ImageGrab.grab(bbox=bbox).save(buffer,format='PNG')
                    print('CROP_REVIEW_JSON '+json.dumps({'name':f'Freeda-crop-{language}-{scale}.png',
                        'data':base64.b64encode(buffer.getvalue()).decode()}),flush=True)
                dialog._cancel()
                app.update()
        ctk.set_widget_scaling(1.)
        ctk.set_window_scaling(1.)
    finally:app.destroy()
    restarted=FreedaApp(settings_path=settings_path,language='en')
    restarted.update()
    try:
        assert restarted.crop_view=='anaglyph' and restarted.crop_grid is False
        for options in (restarted._web_options(),restarted._print_options()):
            options=replace(options,layout=LayoutMode.CROSS)
            dialog=CropDialog(restarted,image,options,index=1,total=1,filename='one.png',editing=True)
            restarted.update()
            assert dialog.view=='anaglyph' and dialog.options==options and dialog.grid_var.get() is False
            dialog._cancel();restarted.update()
        assert restarted.image_crops=={'Web':{},'Print':{}}
        assert json.loads(settings_path.read_text(encoding='utf-8'))['unrelated_preference']=='keep me'
        dialog=CropDialog(restarted,image,restarted._web_options(),index=1,total=1,filename='one.png')
        restarted.update()
        dialog.grid_checkbox.invoke()
        assert dialog.grid_var.get() is True and restarted.crop_grid is True
        dialog._cancel();restarted.update()
    finally:restarted.destroy()
    restarted=FreedaApp(settings_path=settings_path,language='en')
    restarted.update()
    try:
        assert restarted.crop_grid is True and restarted.crop_view=='anaglyph'
        dialog=CropDialog(restarted,image,restarted._web_options(),index=1,total=1,filename='two.png')
        restarted.update()
        assert dialog.grid_var.get() is True
        dialog._cancel();restarted.update()
    finally:restarted.destroy()
    for invalid in ('unknown', ['anaglyph']):
        settings_path.write_text(json.dumps({'crop_view':invalid,'crop_grid':invalid}),encoding='utf-8')
        app=FreedaApp(settings_path=settings_path,language='en')
        app.update()
        try:
            assert app.crop_view is None and app.crop_grid is True
            dialog=CropDialog(app,image,replace(app._web_options(),layout=LayoutMode.CROSS),
                index=1,total=1,filename='one.png',editing=True)
            app.update()
            assert dialog.view=='cross' and dialog.grid_var.get() is True
            dialog._cancel();app.update()
        finally:app.destroy()
print('Remembered crop views and grid on/off across images/restarts, stable crop/export, P-X-A and navigation focus guards passed')
