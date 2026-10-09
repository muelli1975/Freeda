"""Run a native GUI check in a fresh process; callback failures fail the check."""
import faulthandler
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
print(f'Native GUI check: {script.name}', flush=True)
faulthandler.dump_traceback_later(120, exit=True)
try:
    runpy.run_path(str(script), run_name='__main__')
finally:
    faulthandler.cancel_dump_traceback_later()
if errors:
    raise RuntimeError(f'{len(errors)} Tk callback error(s) in {script.name}')
