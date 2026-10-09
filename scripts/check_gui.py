"""Run a native GUI check in a fresh process; callback failures fail the check."""
import runpy
import sys
import tkinter as tk
from pathlib import Path

errors = []
original = tk.Tk.report_callback_exception

def failed(self, *error):
    errors.append(error)
    original(self, *error)

tk.Tk.report_callback_exception = failed
script = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(script.parent))
runpy.run_path(str(script), run_name='__main__')
if errors:
    raise RuntimeError(f'{len(errors)} Tk callback error(s) in {script.name}')
