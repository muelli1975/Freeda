"""Rename only old portable roots, verify all payloads, preserve rollback copies."""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile

REPO = "muelli1975/Freeda"
PLAN = [
  {
    "tag": "v1.0",
    "release_id": 403063646,
    "previous": {
      "Freeda_1.0_Linux_x64.tar.gz": "sha256:943b60fd68a9628407e493fa0ed10ff5259644b4b3be5e35b2d7573fdf40446f",
      "Freeda_1.0_macOS_AppleSilicon.zip": "sha256:1744a27828b5b695b1c21f9b1f33d6219c44c715a1a123f829b665dc9cbb3ae6",
      "Freeda_1.0_macOS_Intel.zip": "sha256:4437428e2bc8a2132b110f54c4b5dbebb6413d1a339627e196c934ed129e5322",
      "Freeda_1.0_Windows_x64.zip": "sha256:e7bcbd0c7570dc9f64d98b638322aedfa2cf87e71662106075720ab297603811",
      "SHA256SUMS.txt": "sha256:676a17867e59a812dd2ad7f67862bc950a24648c80b4829baf990f6dd7f7e2d8"
    },
    "roots": {
      "Freeda_1.0_Linux_x64.tar.gz": "Freeda_1.0_Linux_x64",
      "Freeda_1.0_macOS_AppleSilicon.zip": "Freeda_1.0_macOS_AppleSilicon",
      "Freeda_1.0_macOS_Intel.zip": "Freeda_1.0_macOS_Intel",
      "Freeda_1.0_Windows_x64.zip": "Freeda_1.0_Windows_x64"
    }
  },
  {
    "tag": "v1.1",
    "release_id": 404592654,
    "previous": {
      "Freeda_1.1_Linux_x64.tar.gz": "sha256:9aba4294e623484105319f82203e23aa5409698b0af7513d109e67eba90f8954",
      "Freeda_1.1_macOS_AppleSilicon.zip": "sha256:00f0a1d5f396c5e8b8ef712b6cc30a355899ff554a83b18b91c01c89e718139a",
      "Freeda_1.1_macOS_Intel.zip": "sha256:decc4067118d38cbe0835279bcc329b0e928cf1a005247dcdf611d40f973cac0",
      "Freeda_1.1_Windows_x64.zip": "sha256:df6378028fd6fde4b7b13512324bb66be44b91f7fc862fce9b938242b97d8e84",
      "SHA256SUMS.txt": "sha256:e63c3869389e89a500f3c17a7e57ca4434accfa4a16c303d48db8e6ed5dcc174"
    },
    "roots": {
      "Freeda_1.1_Linux_x64.tar.gz": "Freeda_1.1_Linux_x64",
      "Freeda_1.1_macOS_AppleSilicon.zip": "Freeda_1.1_macOS_AppleSilicon",
      "Freeda_1.1_macOS_Intel.zip": "Freeda_1.1_macOS_Intel",
      "Freeda_1.1_Windows_x64.zip": "Freeda_1.1_Windows_x64"
    }
  }
]

def gh(*args):
    return subprocess.check_output(["gh", *args], text=True)

def api(path):
    return json.loads(gh("api", f"repos/{REPO}/{path}"))

def digest(path):
    with path.open("rb") as stream:
        return "sha256:" + hashlib.file_digest(stream, "sha256").hexdigest()

def rename(name, root):
    name = name.replace("\\", "/")
    if name == root or name.startswith(root + "/"):
        return "Freeda" + name[len(root):]
    prefix = "__MACOSX/" + root
    if name == prefix or name.startswith(prefix + "/"):
        return "__MACOSX/Freeda" + name[len(prefix):]
    prefix = "__MACOSX/._" + root
    if name == prefix:
        return "__MACOSX/._Freeda"
    if name in ("__MACOSX", "__MACOSX/"):
        return name
    raise AssertionError(("Unexpected archive member", name, root))

def mapped_link(link, root):
    normalized = link.replace("\\", "/")
    if normalized == root or normalized.startswith(root + "/"):
        return rename(normalized, root)
    return link

def zip_signature(info, data):
    return (hashlib.sha256(data).hexdigest(), info.date_time, info.compress_type,
            info.create_system, info.external_attr, info.internal_attr, info.comment, info.extra)

def check_zip_extra(extra):
    position = 0
    while position + 4 <= len(extra):
        kind = int.from_bytes(extra[position:position+2], "little")
        length = int.from_bytes(extra[position+2:position+4], "little")
        assert kind != 0x7075, "Unicode path extra requires explicit path migration"
        position += 4 + length
    assert position == len(extra)

def tar_signature(info, data):
    return (hashlib.sha256(data).hexdigest(), info.mode, info.uid, info.gid, info.mtime,
            info.type, info.linkname, info.uname, info.gname, info.pax_headers,
            info.devmajor, info.devminor)

def normalize(source, target, root):
    expected = {}
    if source.name.endswith(".zip"):
        with zipfile.ZipFile(source) as before, zipfile.ZipFile(target, "w", allowZip64=True) as after:
            after.comment = before.comment
            for original in before.infolist():
                assert not original.flag_bits & 1, "Encrypted member"
                check_zip_extra(original.extra)
                info = copy.copy(original)
                info.filename = rename(original.filename, root)
                info.orig_filename = info.filename
                assert info.filename not in expected, "Duplicate normalized path"
                data = before.read(original)
                expected[info.filename] = zip_signature(info, data)
                after.writestr(info, data)
                # zipfile assigns Unix defaults to zero DOS attributes; restore originals
                # before the central directory is written when the archive closes.
                info.external_attr = original.external_attr
        with zipfile.ZipFile(target) as after:
            assert after.testzip() is None
            actual = {info.filename:zip_signature(info, after.read(info)) for info in after.infolist()}
            roots = {name.split("/")[0] for name in actual}
    else:
        with tarfile.open(source, "r:gz") as before, tarfile.open(target, "w:gz", format=tarfile.PAX_FORMAT) as after:
            for original in before.getmembers():
                info = copy.copy(original)
                info.name = rename(original.name, root)
                info.linkname = mapped_link(original.linkname, root)
                info.pax_headers = original.pax_headers.copy()
                if "path" in info.pax_headers:
                    info.pax_headers["path"] = info.name
                if "linkpath" in info.pax_headers:
                    info.pax_headers["linkpath"] = info.linkname
                assert info.name not in expected, "Duplicate normalized path"
                data = before.extractfile(original).read() if original.isfile() else b""
                expected[info.name] = tar_signature(info, data)
                after.addfile(info, io.BytesIO(data) if original.isfile() else None)
        with tarfile.open(target, "r:gz") as after:
            actual = {info.name:tar_signature(info, after.extractfile(info).read() if info.isfile() else b"")
                      for info in after.getmembers()}
            roots = {name.split("/")[0] for name in actual}
    assert actual == expected, "Member bytes or preserved metadata differ"
    assert roots <= {"Freeda", "__MACOSX"} and "Freeda" in roots, roots
    print(source.name, len(actual), "members verified; all payload bytes and permissions preserved; root Freeda", flush=True)

latest_before = api("releases/tags/v1.2")
latest_guard = {a["name"]:a["digest"] for a in latest_before["assets"]}
prepared = []
for item in PLAN:
    tag = item["tag"]
    release = api(f"releases/tags/{tag}")
    assert release["id"] == item["release_id"] and not release["draft"]
    before = {a["name"]:a["digest"] for a in release["assets"]}
    assert before == item["previous"], "Release changed since inspection"
    tag_ref = api(f"git/ref/tags/{tag}")["object"]["sha"]
    original = Path("previous-packages") / tag
    updated = Path("renamed-packages") / tag
    original.mkdir(parents=True)
    updated.mkdir(parents=True)
    for name in before:
        gh("release", "download", tag, "--repo", REPO, "--pattern", name, "--dir", str(original))
        assert digest(original/name) == before[name], "Original download checksum differs"
    listed = {}
    for line in (original/"SHA256SUMS.txt").read_text().splitlines():
        if line.strip():
            checksum, name = line.split(maxsplit=1)
            listed[name.lstrip("*")] = "sha256:" + checksum
    assert listed == {n:d for n,d in before.items() if n != "SHA256SUMS.txt"}, "Original checksum file differs"
    for name, root in item["roots"].items():
        normalize(original/name, updated/name, root)
    sums = "".join(digest(updated/name).removeprefix("sha256:") + "  " + name + "\n"
                   for name in sorted(item["roots"]))
    (updated/"SHA256SUMS.txt").write_text(sums, encoding="ascii")
    expected = {name:digest(updated/name) for name in before}
    prepared.append((item, tag_ref, release["body"], original, updated, expected))

# Validate both releases completely before replacing any download.
for item, tag_ref, body, original, updated, expected in prepared:
    tag = item["tag"]
    current = api(f"releases/tags/{tag}")
    assert {a["name"]:a["digest"] for a in current["assets"]} == item["previous"]
    touched = []
    try:
        for name in expected:
            touched.append(name)
            gh("release", "upload", tag, str(updated/name), "--repo", REPO, "--clobber")
        release = api(f"releases/tags/{tag}")
        assert {a["name"]:a["digest"] for a in release["assets"]} == expected
        assert release["body"] == body and not release["draft"]
        assert api(f"git/ref/tags/{tag}")["object"]["sha"] == tag_ref
        print("NORMALIZED_RELEASE_JSON " + json.dumps({"tag":tag,"checksums":expected}), flush=True)
    except Exception:
        for name in touched:
            gh("release", "upload", tag, str(original/name), "--repo", REPO, "--clobber")
        restored = api(f"releases/tags/{tag}")
        assert {a["name"]:a["digest"] for a in restored["assets"]} == item["previous"], "Rollback differs"
        raise
latest_after = api("releases/tags/v1.2")
assert {a["name"]:a["digest"] for a in latest_after["assets"]} == latest_guard
assert latest_after["body"] == latest_before["body"]
print("Older releases normalized and published checksums verified; current 1.2 retained.", flush=True)
