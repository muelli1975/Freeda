"""Publish packages only from the exact successful native build, with rollback."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile

def gh(*args):
    return subprocess.check_output(["gh", *args], text=True)

def api(path):
    return json.loads(gh("api", path))

def digest(path):
    with path.open("rb") as stream:
        return "sha256:" + hashlib.file_digest(stream, "sha256").hexdigest()

plan = json.loads(Path("scripts/verified-package-update.json").read_text())
repo, app, tag = plan["repo"], plan["app"], plan["tag"]
run = api(f"repos/{repo}/actions/runs/{plan['run']}")
assert run["repository"]["full_name"] == repo and run["head_sha"] == plan["commit"]
assert run["head_branch"] == "main" and run["event"] == "push"
assert run["status"] == "completed" and run["conclusion"] == "success", "Native build is not green"
release = api(f"repos/{repo}/releases/tags/{tag}")
assert release["id"] == plan["release_id"] and not release["draft"]
before = {asset["name"]:asset for asset in release["assets"]}
assert {name:asset["digest"] for name,asset in before.items()} == plan["previous"]
tag_before = api(f"repos/{repo}/git/ref/tags/{tag}")["object"]["sha"]
artifacts = Path("verified-packages")
backup = Path("previous-packages")
artifacts.mkdir(exist_ok=True)
backup.mkdir(exist_ok=True)
for name in plan["packages"]:
    artifact_name = name.removesuffix(".tar.gz").removesuffix(".zip")
    gh("run", "download", str(plan["run"]), "--repo", repo, "--name", artifact_name, "--dir", str(artifacts))
gui_response = api(f"repos/{repo}/contents/{plan['gui']}?ref={plan['commit']}")
expected_gui = base64.b64decode(gui_response["content"])
notes_response = api(f"repos/{repo}/contents/{plan['notes']}?ref={plan['commit']}")
Path("verified-release-notes.md").write_bytes(base64.b64decode(notes_response["content"]))
for name in plan["packages"]:
    path = artifacts / name
    if name.endswith(".zip"):
        archive = zipfile.ZipFile(path)
        members = {n.replace("\\","/"):n for n in archive.namelist()}
        read = lambda n: archive.read(members[n])
    else:
        archive = tarfile.open(path, "r:gz")
        members = {n.name.replace("\\","/"):n for n in archive.getmembers()}
        read = lambda n: archive.extractfile(members[n]).read()
    try:
        roots = {n.split("/")[0] for n in members}
        assert roots <= {app,"__MACOSX"} and app in roots, (name, roots)
        assert read(f"{app}/source/{plan['gui']}") == expected_gui, "Packaged source differs from tested source"
        info = json.loads(read(f"{app}/BUILD_INFO.json"))
        assert info["commit"] == plan["commit"], info
        forbidden = {f"{app}/settings.json",f"{app}/presets.json"}
        assert not forbidden.intersection(members), "Package contains local preferences"
        if app == "AnaChroma":
            originals = [n for n in members if n.endswith("/assets/anachroma.jpg")]
            assert originals
            for n in originals:
                data = read(n)
                git_hash = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
                assert git_hash == plan["image_blob"], "Original SBS asset changed"
        print(name, "stable root, exact tested source and build commit verified", flush=True)
    finally:
        archive.close()
checksums = "".join(digest(artifacts/name).removeprefix("sha256:") + "  " + name + "\n"
                    for name in sorted(plan["packages"]))
(artifacts / "SHA256SUMS.txt").write_text(checksums, encoding="ascii")
for name,asset in before.items():
    gh("release", "download", tag, "--repo", repo, "--pattern", name, "--dir", str(backup))
    assert digest(backup/name) == asset["digest"], "Previous package checksum differs"
expected = {name:digest(artifacts/name) for name in plan["packages"] + ["SHA256SUMS.txt"]}
updated = []
try:
    for name in expected:
        gh("release", "upload", tag, str(artifacts/name), "--repo", repo, "--clobber")
        updated.append(name)
    current = api(f"repos/{repo}/releases/tags/{tag}")
    actual = {a["name"]:a["digest"] for a in current["assets"]}
    assert actual == expected, "Published asset digest set differs"
    assert api(f"repos/{repo}/git/ref/tags/{tag}")["object"]["sha"] == tag_before, "Existing tag changed"
    gh("release","edit",tag,"--repo",repo,"--notes-file","verified-release-notes.md")
    print("All published asset checksums verified:", json.dumps(expected), flush=True)
except Exception:
    for name in updated:
        gh("release","upload",tag,str(backup/name),"--repo",repo,"--clobber")
    raise
