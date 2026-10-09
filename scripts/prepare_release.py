from pathlib import Path
import json
import sys
from release_support import prepare
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from freeda import __version__
package = Path(sys.argv[1])
commit = prepare(ROOT, package, {"freeda", "scripts", "assets", "tests", "docs", "licenses",
    "Freeda.py", "Freeda.spec", "build_windows.ps1", "requirements-lock.txt", "requirements-build.txt",
    "README.md", "README_DE.md", "README_EN.md", "QUICKSTART.md", "LICENSE", "THIRD_PARTY_NOTICES.md",
    "RELEASE_NOTES_1.2.md", "DESIGN_STANDARD_STEREOTOOLS.txt", "AGENTS.md"})
(package/"BUILD_INFO.json").write_text(json.dumps({"commit":commit,"version":__version__,
    "python":sys.version,"platform":sys.platform},indent=2)+"\n")
