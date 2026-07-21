#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


CMAKE_ANCHOR = "add_library(FreeCADGui SHARED)\n"
CMAKE_INSERT = CMAKE_ANCHOR + "add_subdirectory(SolidFreeCAD)\n"

INCLUDE_ANCHOR = '#include "MainWindow.h"\n'
INCLUDE_LINE = '#include "SolidFreeCAD/SolidGuiBootstrap.h"\n'

INSTALL_ANCHOR = '    statusBar()->showMessage(tr("Ready"), 2001);\n'
INSTALL_LINE = "    SolidFreeCAD::installGui(this);\n\n"

DESTRUCTOR_ANCHOR = "MainWindow::~MainWindow()\n{\n"
DESTRUCTOR_INSERT = DESTRUCTOR_ANCHOR + "    SolidFreeCAD::uninstallGui();\n"

PROPERTY_SELECTION_ANCHOR = (
    "    const auto selection = "
    "Gui::Selection().getCompleteSelection(Gui::ResolveMode::NoResolve);\n"
    "    return selection.size() == 1 ? selection.front().pObject : nullptr;\n"
)
PROPERTY_SELECTION_INSERT = (
    "    const auto selection = "
    "Gui::Selection().getCompleteSelection(Gui::ResolveMode::NoResolve);\n"
    "    if (selection.size() != 1) {\n"
    "        return nullptr;\n"
    "    }\n\n"
    "    const auto& selected = selection.front();\n"
    "    return selected.pResolvedObject ? selected.pResolvedObject : selected.pObject;\n"
)

SKETCH_EDIT_ANCHOR = "    Workbench::enterEditMode();\n\n"
SKETCH_EDIT_INSERT = (
    SKETCH_EDIT_ANCHOR
    + "    // SolidFreeCAD: rebuild and display native faces for closed profiles while editing.\n"
    + "    const auto& solidFreeCADProfileShape = getSketchObject()->InternalShape.getValue();\n"
    + "    setupCoinGeometry(\n"
    + "        solidFreeCADProfileShape,\n"
    + "        pcSketchFaces,\n"
    + "        this->Deviation.getValue(),\n"
    + "        this->AngularDeflection.getValue()\n"
    + "    );\n"
    + "    pcSketchFacesToggle->on = true;\n\n"
)

SKETCH_UNSET_ANCHOR = (
    "    if (ModNum != ViewProviderSketch::Default) {\n"
    "        return PartGui::ViewProvider2DObject::unsetEdit(ModNum);\n"
    "    }\n\n"
)
SKETCH_UNSET_INSERT = (
    SKETCH_UNSET_ANCHOR
    + "    // SolidFreeCAD: leave profile shading with the normal object visibility lifecycle.\n"
    + "    pcSketchFacesToggle->on = Visibility.getValue();\n\n"
)


def insert_once(text: str, anchor: str, insertion: str, description: str) -> str:
    if insertion in text:
        return text
    if anchor not in text:
        raise RuntimeError(f"Could not find {description} anchor")
    return text.replace(anchor, insertion, 1)


def apply(repo_root: Path, freecad_root: Path) -> None:
    source_overlay = repo_root / "src" / "Gui" / "SolidFreeCAD"
    destination_overlay = freecad_root / "src" / "Gui" / "SolidFreeCAD"
    cmake_file = freecad_root / "src" / "Gui" / "CMakeLists.txt"
    main_window_file = freecad_root / "src" / "Gui" / "MainWindow.cpp"
    sketch_view_file = (
        freecad_root / "src" / "Mod" / "Sketcher" / "Gui" / "ViewProviderSketch.cpp"
    )

    for required in (source_overlay, cmake_file, main_window_file, sketch_view_file):
        if not required.exists():
            raise FileNotFoundError(required)

    if destination_overlay.exists():
        shutil.rmtree(destination_overlay)
    shutil.copytree(source_overlay, destination_overlay)

    property_manager_file = destination_overlay / "SolidPropertyManager.cpp"
    property_manager_text = property_manager_file.read_text(encoding="utf-8")
    property_manager_text = insert_once(
        property_manager_text,
        PROPERTY_SELECTION_ANCHOR,
        PROPERTY_SELECTION_INSERT,
        "Property Manager resolved selection",
    )
    property_manager_file.write_text(property_manager_text, encoding="utf-8")

    cmake_text = cmake_file.read_text(encoding="utf-8")
    cmake_text = insert_once(
        cmake_text,
        CMAKE_ANCHOR,
        CMAKE_INSERT,
        "FreeCADGui target",
    )
    cmake_file.write_text(cmake_text, encoding="utf-8")

    main_text = main_window_file.read_text(encoding="utf-8")
    if INCLUDE_LINE not in main_text:
        main_text = insert_once(
            main_text,
            INCLUDE_ANCHOR,
            INCLUDE_ANCHOR + INCLUDE_LINE,
            "MainWindow include",
        )
    if "SolidFreeCAD::installGui(this);" not in main_text:
        main_text = insert_once(
            main_text,
            INSTALL_ANCHOR,
            INSTALL_LINE + INSTALL_ANCHOR,
            "MainWindow constructor",
        )
    if "SolidFreeCAD::uninstallGui();" not in main_text:
        main_text = insert_once(
            main_text,
            DESTRUCTOR_ANCHOR,
            DESTRUCTOR_INSERT,
            "MainWindow destructor",
        )
    main_window_file.write_text(main_text, encoding="utf-8")

    sketch_text = sketch_view_file.read_text(encoding="utf-8")
    sketch_text = insert_once(
        sketch_text,
        SKETCH_EDIT_ANCHOR,
        SKETCH_EDIT_INSERT,
        "Sketcher edit-mode profile shading",
    )
    sketch_text = insert_once(
        sketch_text,
        SKETCH_UNSET_ANCHOR,
        SKETCH_UNSET_INSERT,
        "Sketcher unset-edit profile shading",
    )
    sketch_view_file.write_text(sketch_text, encoding="utf-8")

    marker = freecad_root / "SOLIDFREECAD_OVERLAY_APPLIED"
    marker.write_text("SolidFreeCAD GUI overlay applied\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply the SolidFreeCAD GUI overlay to official FreeCAD 1.1.1 source"
    )
    parser.add_argument("freecad_source", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    apply(repo_root, args.freecad_source.resolve())
    print(f"SolidFreeCAD overlay applied to {args.freecad_source.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
