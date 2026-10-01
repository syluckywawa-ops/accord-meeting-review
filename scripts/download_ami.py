#!/usr/bin/env python3
"""Download and safely extract the checksum-pinned public AMI annotations."""
from __future__ import annotations

import hashlib
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
URL = "https://groups.inf.ed.ac.uk/ami/AMICorpusAnnotations/ami_public_manual_1.6.2.zip"
SHA256 = "b56e5babb2496b8795deeeda7e71178d7fbc9963f94276cf2a3f4b56ebbc9f9d"
DESTINATION = ROOT / "data_raw/ami_public_manual_1.6.2"


def safe_members(archive):
    members = archive.infolist()
    if len(members) > 100000 or sum(x.file_size for x in members) > 512 * 1024 * 1024:
        raise ValueError("Archive exceeds extraction limits")
    for member in members:
        name = PurePosixPath(member.filename)
        mode = member.external_attr >> 16
        if name.is_absolute() or ".." in name.parts or "\\" in member.filename or (mode & 0o170000) == 0o120000:
            raise ValueError("Unsafe archive entry")
    return members


def main():
    if DESTINATION.exists():
        raise SystemExit(f"Source directory already exists; preserved without overwriting: {DESTINATION}")
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="actionai-ami-", dir=DESTINATION.parent) as temporary:
        temporary = Path(temporary)
        downloaded = temporary / "source.zip"
        request = urllib.request.Request(URL, headers={"User-Agent": "ActionAI-course-project/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response, downloaded.open("wb") as target:
            digest = hashlib.sha256()
            size = 0
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > 32 * 1024 * 1024:
                    raise ValueError("Download exceeds expected size limit")
                digest.update(chunk)
                target.write(chunk)
        if digest.hexdigest() != SHA256:
            raise ValueError("AMI checksum mismatch; source was not installed")
        extracted = temporary / "extracted"
        with zipfile.ZipFile(downloaded) as archive:
            archive.extractall(extracted, members=safe_members(archive))
        # Official archives may contain a top-level directory.
        candidates = [extracted, *[x for x in extracted.iterdir() if x.is_dir()]]
        source = next((x for x in candidates if (x / "words").is_dir() and (x / "segments").is_dir()), None)
        if source is None:
            raise ValueError("Archive does not contain the expected AMI words/segments layout")
        shutil.move(str(source), str(DESTINATION))
    print(f"Verified and installed AMI source: {DESTINATION}")
    print("Next: .venv/bin/python scripts/prepare_ami.py --source data_raw/ami_public_manual_1.6.2 --manifest data/data_manifest.csv --output data/derived")


if __name__ == "__main__":
    main()
