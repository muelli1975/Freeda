"""Native Linux/macOS packages, run on their respective build hosts."""
import argparse
import platform
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--label', required=True)
args = parser.parse_args()
labels = {'Linux_x64': ('Linux', 'x86_64'), 'macOS_AppleSilicon': ('Darwin', 'arm64'), 'macOS_Intel': ('Darwin', 'x86_64')}
if labels.get(args.label) != (platform.system(), platform.machine()):
    raise SystemExit('Build label does not match the native host architecture.')
command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--windowed',
    '--name', 'Freeda', '--collect-data', 'customtkinter', '--hidden-import', 'PIL._tkinter_finder',
    '--add-data', 'assets:assets']
if sys.platform == 'darwin':
    command += ['--icon', 'assets/Freeda.icns', '--osx-bundle-identifier', 'org.stereotools.freeda']
subprocess.run(command + ['Freeda.py'], cwd=root, check=True)
release = root / 'release'
release.mkdir(exist_ok=True)
name = 'Freeda_1.0_' + args.label
if sys.platform == 'darwin':
    package = release / name
    package.mkdir(exist_ok=True)
    tool_destination = root / 'dist/Freeda.app/Contents/MacOS/tools'
else:
    package = root / 'dist/Freeda'
    tool_destination = package / 'tools'
if not (root / 'tools/exiftool').is_file():
    raise SystemExit('Run scripts/prepare_exiftool.py before building.')
shutil.copytree(root / 'tools', tool_destination, dirs_exist_ok=True)
if sys.platform == 'darwin':
    bundle = root / 'dist/Freeda.app'
    subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(bundle)], check=True)
    # ditto preserves framework symlinks AND signature xattrs on ExifTool scripts.
    subprocess.run(['ditto', str(bundle), str(package / 'Freeda.app')], check=True)
    for signed_bundle in (bundle, package / 'Freeda.app'):
        subprocess.run(['codesign', '--verify', '--deep', '--strict', str(signed_bundle)], check=True)
for filename in ('README.md', 'README_DE.md', 'README_EN.md', 'QUICKSTART.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md'):
    shutil.copy2(root / filename, package / filename)
shutil.copytree(root / 'licenses', package / 'licenses', dirs_exist_ok=True)
shutil.copytree(root / 'docs/screenshots', package / 'docs/screenshots', dirs_exist_ok=True)
if sys.platform == 'darwin':
    subprocess.run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(package), str(release / (name + '.zip'))], check=True)
else:
    with tarfile.open(release / (name + '.tar.gz'), 'w:gz') as archive:
        archive.add(package, arcname=name)
print('Created native package:', name)
