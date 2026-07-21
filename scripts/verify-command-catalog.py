#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


COMMANDS = (
    "Std_New",
    "Std_Open",
    "Std_Save",
    "Std_Undo",
    "Std_Redo",
    "Std_ViewFitAll",
    "Std_ViewIsometric",
    "PartDesign_Body",
    "PartDesign_NewSketch",
    "PartDesign_Pad",
    "PartDesign_Pocket",
    "PartDesign_Fillet",
    "PartDesign_Chamfer",
    "Sketcher_LeaveSketch",
    "Sketcher_Dimension",
    "Sketcher_CompDimensionTools",
    "Sketcher_ConstrainDistanceX",
    "Sketcher_ConstrainDistanceY",
    "Sketcher_ConstrainDistance",
    "Sketcher_ConstrainRadius",
    "Sketcher_ConstrainDiameter",
    "Sketcher_ConstrainAngle",
    "Sketcher_ConstrainLock",
    "Sketcher_CompLine",
    "Sketcher_CompCreateRectangles",
    "Sketcher_CompCreateArc",
    "Sketcher_CompCreateConic",
    "Sketcher_CompSlot",
    "Sketcher_CompCreateBSpline",
    "Sketcher_CompCurveEdition",
    "Sketcher_CompExternal",
    "Sketcher_Offset",
    "Sketcher_Symmetry",
    "Sketcher_Translate",
    "Sketcher_Rotate",
    "Sketcher_SelectConstraints",
    "Sketcher_ValidateSketch",
    "Sketcher_SelectElementsAssociatedWithConstraints",
    "Sketcher_ConstrainCoincidentUnified",
    "Sketcher_CompHorVer",
    "Sketcher_ToggleConstruction",
    "Sketcher_ViewSection",
)

SOURCE_SUFFIXES = {".cpp", ".h", ".py"}


def source_files(root: Path):
    for path in (root / "src").rglob("*"):
        if path.is_file() and path.suffix in SOURCE_SUFFIXES:
            yield path


def verify(root: Path) -> None:
    files = list(source_files(root))
    if not files:
        raise RuntimeError(f"No FreeCAD source files found under {root}")

    contents: list[tuple[Path, str]] = []
    for path in files:
        try:
            contents.append((path, path.read_text(encoding="utf-8", errors="ignore")))
        except OSError as exc:
            raise RuntimeError(f"Could not read {path}: {exc}") from exc

    missing: list[str] = []
    for command in COMMANDS:
        matches = [path for path, text in contents if command in text]
        if not matches:
            missing.append(command)
            continue
        relative = matches[0].relative_to(root)
        print(f"{command}: {relative}")

    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Commands not found in official FreeCAD source: {joined}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the SolidFreeCAD command catalogue against official FreeCAD source"
    )
    parser.add_argument("freecad_source", type=Path)
    args = parser.parse_args()
    verify(args.freecad_source.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
