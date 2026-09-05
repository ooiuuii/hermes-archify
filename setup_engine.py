"""Explicitly install the checksum-pinned official Archify release, not npm latest."""

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import tempfile
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parent


def install(archive=None, destination=None):
    lock = json.loads((ROOT / "engine-lock.json").read_text(encoding="utf-8"))
    parent = Path(destination).resolve() if destination else ROOT / ".engine"
    target = parent / "archify"
    if target.exists():
        raise ValueError(f"Engine directory already exists: {target}. It was not changed.")
    if archive:
        data = Path(archive).read_bytes()
    else:
        request = urllib.request.Request(lock["url"], headers={"User-Agent": "hermes-archify/0.1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read(lock["bytes"] + 1)
    if len(data) != lock["bytes"] or hashlib.sha256(data).hexdigest() != lock["sha256"]:
        raise ValueError("Archive size or SHA-256 does not match engine-lock.json; nothing was installed.")
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="archify-install-", dir=parent) as staging:
        staging_path = Path(staging).resolve()
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            members = package.infolist()
            if sum(member.file_size for member in members) > 50 * 1024 * 1024:
                raise ValueError("Unexpected uncompressed engine size.")
            for member in members:
                raw_name = member.orig_filename
                path = PurePosixPath(raw_name)
                if (path.is_absolute() or ".." in path.parts or "\\" in raw_name
                        or ":" in raw_name or "\x00" in raw_name or not path.parts or path.parts[0] != "archify"
                        or stat.S_ISLNK(member.external_attr >> 16)):
                    raise ValueError(f"Unsafe archive member: {member.filename}")
                resolved = (staging_path / member.filename).resolve()
                if not resolved.is_relative_to(staging_path):
                    raise ValueError("Archive member leaves the installation directory.")
            package.extractall(staging_path)
        unpacked = staging_path / "archify"
        for required in ("bin/archify.mjs", "package.json", "LICENSE"):
            if not (unpacked / required).is_file():
                raise ValueError(f"Pinned package is missing {required}.")
        package_metadata = json.loads((unpacked / "package.json").read_text(encoding="utf-8"))
        if "v" + package_metadata["version"] != lock["version"]:
            raise ValueError("Engine package version does not match the lock.")
        (unpacked / "hermes-install-receipt.json").write_text(
            json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        # The fresh target is never merged into or substituted for an existing engine.
        unpacked.rename(target)
    return {"ok": True, "engine_dir": str(target), "version": lock["version"], "sha256": lock["sha256"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", help="Offline copy of the exact official archify.zip; checksum is still required")
    parser.add_argument("--destination", help="Engine parent directory; defaults to this plugin's .engine")
    args = parser.parse_args()
    try:
        print(json.dumps(install(**vars(args)), indent=2))
        return 0
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
