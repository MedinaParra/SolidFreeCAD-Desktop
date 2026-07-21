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

GUI_MODEL_DOCK_OLD = (
    '        and (dock.objectName() == "Model" or dock.windowTitle() == "Modelo")\n'
)
GUI_MODEL_DOCK_NEW = (
    '        and (dock.objectName() == "Model"\n'
    '             or dock.windowTitle() in {"Modelo", "Historial del modelo"})\n'
)

GUI_POLISH_ANCHOR = '    stage("ribbon-validated")\n'
GUI_POLISH_INSERT = GUI_POLISH_ANCHOR + '''

    ribbon_pages = main_window.findChild(
        QtWidgets.QStackedWidget, "SolidFreeCADRibbonPages"
    )
    context_badge = main_window.findChild(
        QtWidgets.QLabel, "SolidFreeCADContextBadge"
    )
    if ribbon_pages is None or context_badge is None or context_badge.text() != "PIEZA":
        raise RuntimeError("The polished SolidFreeCAD workspace badge is missing")
    if ribbon_tabs.geometry().top() >= ribbon_pages.geometry().top():
        raise RuntimeError("Ribbon tabs were not moved above the command pages")

    primary_buttons = [
        button
        for button in ribbon.findChildren(QtWidgets.QToolButton)
        if bool(button.property("SolidFreeCADPrimaryCommand"))
    ]
    if len(primary_buttons) < 4:
        raise RuntimeError(
            f"Too few primary modeling commands were highlighted: {len(primary_buttons)}"
        )

    workspace_icon_actions = [
        action
        for toolbar in ribbon.findChildren(
            QtWidgets.QToolBar, "SolidFreeCADQuickAccess"
        )
        for action in toolbar.actions()
        if bool(action.property("SolidFreeCADWorkspaceIcon"))
    ]
    if len(workspace_icon_actions) < 5:
        raise RuntimeError(
            f"Quick access icon set is incomplete: {len(workspace_icon_actions)}"
        )
    if any(action.icon().isNull() for action in workspace_icon_actions):
        raise RuntimeError("A polished quick access icon is null")
    stage(
        f"workspace-polish-validated-primary-{len(primary_buttons)}-"
        f"quick-icons-{len(workspace_icon_actions)}"
    )
'''

GUI_SCREENSHOT_ANCHOR = '    stage("capture-modeling-start")\n'
GUI_SCREENSHOT_INSERT = '''    FreeCADGui.Selection.clearSelection()
    FreeCADGui.Selection.addSelection(active_document.Name, pad.Name)
    process_for(0.35)
    stage("capture-modeling-start")
'''


def insert_once(text: str, anchor: str, insertion: str, description: str) -> str:
    if insertion in text:
        return text
    if anchor not in text:
        raise RuntimeError(f"Could not find {description} anchor")
    return text.replace(anchor, insertion, 1)


def replace_once(text: str, old: str, new: str, description: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Could not find {description} text")
    return text.replace(old, new, 1)


def apply(repo_root: Path, freecad_root: Path) -> None:
    source_overlay = repo_root / "src" / "Gui" / "SolidFreeCAD"
    destination_overlay = freecad_root / "src" / "Gui" / "SolidFreeCAD"
    cmake_file = freecad_root / "src" / "Gui" / "CMakeLists.txt"
    main_window_file = freecad_root / "src" / "Gui" / "MainWindow.cpp"
    sketch_view_file = (
        freecad_root / "src" / "Mod" / "Sketcher" / "Gui" / "ViewProviderSketch.cpp"
    )
    gui_smoke_file = repo_root / "tests" / "gui_smoke.py"

    for required in (
        source_overlay,
        cmake_file,
        main_window_file,
        sketch_view_file,
        gui_smoke_file,
    ):
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

    gui_smoke_text = gui_smoke_file.read_text(encoding="utf-8")
    gui_smoke_text = replace_once(
        gui_smoke_text,
        GUI_MODEL_DOCK_OLD,
        GUI_MODEL_DOCK_NEW,
        "polished model dock title",
    )
    gui_smoke_text = insert_once(
        gui_smoke_text,
        GUI_POLISH_ANCHOR,
        GUI_POLISH_INSERT,
        "workspace polish assertions",
    )
    gui_smoke_text = insert_once(
        gui_smoke_text,
        GUI_SCREENSHOT_ANCHOR,
        GUI_SCREENSHOT_INSERT,
        "selected feature screenshot",
    )
    gui_smoke_file.write_text(gui_smoke_text, encoding="utf-8")

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
