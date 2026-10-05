"""Fetch the official, checksum-pinned ExifTool distribution used by StereoFine."""
import hashlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

VERSION = "13.59"
ROOT = Path(__file__).resolve().parents[1]
ARCHIVES = {
    "windows": (f"exiftool-{VERSION}_64.zip", "44b512b25af500724ba579d0a53c8fc5851628b692dd5e5d94ae4a15c2cba9ec"),
    "unix": (f"Image-ExifTool-{VERSION}.tar.gz", "668ea3acececb7235fbd0f4900e72d5f12c9b07e5c778fd36cb1e9b5828fd65a"),
}


def main():
    windows = sys.platform.startswith("win")
    name, checksum = ARCHIVES["windows" if windows else "unix"]
    downloads = ROOT / "downloads"
    downloads.mkdir(exist_ok=True)
    archive = downloads / name
    if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != checksum:
        subprocess.run(["curl.exe" if windows else "curl", "-fL", "--retry", "3",
            f"https://sourceforge.net/projects/exiftool/files/{name}/download", "-o", str(archive)], check=True)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != checksum:
        raise RuntimeError("Official ExifTool archive checksum mismatch.")
    tools = ROOT / "tools"
    tools.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=downloads) as folder:
        if windows:
            with zipfile.ZipFile(archive) as package:
                package.extractall(folder)
        else:
            with tarfile.open(archive) as package:
                package.extractall(folder, filter="data")
        source = next(path for path in Path(folder).iterdir() if path.is_dir())
        shutil.copytree(source, tools, dirs_exist_ok=True)
    if windows:
        (tools / "exiftool(-k).exe").replace(tools / "exiftool.exe")
        command = [str(tools / "exiftool.exe"), "-ver"]
    else:
        (tools / "exiftool").chmod(0o755)
        command = ["perl", str(tools / "exiftool"), "-ver"]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    if result.stdout.strip() != VERSION:
        raise RuntimeError("Unexpected bundled ExifTool version.")
    print(f"Verified official ExifTool {VERSION} in tools/ (distribution and notices preserved).")


if __name__ == "__main__":
    main()
