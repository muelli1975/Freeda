"""Verify the packaged application stays alive through native GUI startup."""
import subprocess
import sys
import time
from pathlib import Path

executable = Path(sys.argv[1]).resolve()
startup = None
if sys.platform == 'win32':
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
process = subprocess.Popen([str(executable)], cwd=executable.parent, stdout=subprocess.PIPE,
    stderr=subprocess.PIPE, startupinfo=startup)
try:
    time.sleep(4)
    if process.poll() is not None:
        output, error = process.communicate()
        raise SystemExit(f'Native startup exited ({process.returncode}): {error.decode(errors="replace")}')
    print('Native GUI startup passed:', executable.name)
finally:
    if process.poll() is None:
        process.terminate()
    process.communicate(timeout=15)
