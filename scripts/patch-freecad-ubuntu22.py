#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


FEATURE_PATH = Path("src/Mod/PartDesign/App/Feature.cpp")
MARKER_NAME = "SOLIDFREECAD_UBUNTU22_COMPAT_PATCHED"

INCLUDE_ANCHOR = """#include <gp_Pln.hxx>
#include <gp_Pnt.hxx>
#include <ShapeFix_Solid.hxx>
#include <Standard_Failure.hxx>
"""

INCLUDE_REPLACEMENT = """#include <gp_Pln.hxx>
#include <gp_Pnt.hxx>
#include <Message_ProgressRange.hxx>
#include <ShapeFix_Solid.hxx>
#include <Standard_Failure.hxx>
#include <Standard_Version.hxx>
"""

STATUS_ANCHOR = """        BRepCheck_Solid bs(solid);
        if (bs.IsStatusOnShape(solid)) {
            const auto& listOfStatus = bs.StatusOnShape(solid);
            if (listOfStatus.Contains(BRepCheck_EnclosedRegion)) {
                fixSolids.emplace_back(solid);
            }
        }
"""

STATUS_REPLACEMENT = """        BRepCheck_Solid bs(solid);
#if OCC_VERSION_HEX >= 0x070600
        if (!bs.IsStatusOnShape(solid)) {
            continue;
        }
#endif
        const auto& listOfStatus = bs.StatusOnShape(solid);
        if (listOfStatus.Contains(BRepCheck_EnclosedRegion)) {
            fixSolids.emplace_back(solid);
        }
"""


def replace_once(text: str, anchor: str, replacement: str, label: str) -> str:
    if replacement in text:
        return text
    count = text.count(anchor)
    if count != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {count}")
    return text.replace(anchor, replacement, 1)


def patch(source_root: Path) -> None:
    source_root = source_root.resolve()
    feature = source_root / FEATURE_PATH
    if not feature.is_file():
        raise RuntimeError(f"FreeCAD PartDesign source not found: {feature}")

    text = feature.read_text(encoding="utf-8")
    text = replace_once(text, INCLUDE_ANCHOR, INCLUDE_REPLACEMENT, "include")
    text = replace_once(text, STATUS_ANCHOR, STATUS_REPLACEMENT, "OCCT status API")
    feature.write_text(text, encoding="utf-8")

    marker = source_root / MARKER_NAME
    marker.write_text(
        "FreeCAD 1.1.1 compatibility patch for Ubuntu 22.04 system OCCT 7.5.\n",
        encoding="utf-8",
    )
    print(f"Patched FreeCAD PartDesign for OCCT 7.5 compatibility: {feature}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Patch official FreeCAD 1.1.1 PartDesign for Ubuntu 22.04 OCCT 7.5"
    )
    parser.add_argument("freecad_source", type=Path)
    args = parser.parse_args()
    patch(args.freecad_source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
