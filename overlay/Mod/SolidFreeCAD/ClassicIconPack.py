"""Materialize the user-approved SolidFreeCAD classic SVG icon package."""
from __future__ import annotations

import base64
import io
import os
from pathlib import Path, PurePosixPath
import zipfile

_PACK_VERSION = "3.0.0"
_ARCHIVE_TEXT = Path(__file__).resolve().parent / "Resources" / "ClassicIconPack-v3.zip.b64"


def _target_root() -> Path:
    return Path(__file__).resolve().parent / "Resources" / "icons" / "classic"


def ensure_classic_icons(force: bool = False) -> Path:
    target = _target_root()
    marker = target / ".solidfreecad-classic-v3"
    existing = list(target.rglob("*.svg")) if target.exists() else []
    if not force and marker.is_file() and len(existing) >= 70:
        return target
    if not _ARCHIVE_TEXT.is_file():
        raise RuntimeError(f"Classic icon archive is missing: {_ARCHIVE_TEXT}")

    target.mkdir(parents=True, exist_ok=True)
    archive = base64.b64decode(_ARCHIVE_TEXT.read_text(encoding="ascii"))
    written = 0
    with zipfile.ZipFile(io.BytesIO(archive), "r") as package:
        for member in package.infolist():
            if member.is_dir():
                continue
            parts = PurePosixPath(member.filename).parts
            if "icons" not in parts:
                continue
            index = parts.index("icons")
            relative = Path(*parts[index + 1 :])
            if relative.suffix.lower() != ".svg":
                continue
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(package.read(member))
            written += 1

    if written < 70:
        raise RuntimeError(f"Classic icon archive produced only {written} SVG files")
    marker.write_text(_PACK_VERSION, encoding="ascii")
    return target


if __name__ == "__main__":
    root = ensure_classic_icons(force="--force" in os.sys.argv)
    print(f"Materialized {len(list(root.rglob('*.svg')))} classic SVG icons at {root}")
