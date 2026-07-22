from __future__ import annotations

import os
import time
from pathlib import Path

import FreeCAD as App
import FreeCADGui
from PySide import QtWidgets


application = QtWidgets.QApplication.instance()
if application is None:
    raise RuntimeError("Qt application is not available")

main_window = FreeCADGui.getMainWindow()
if main_window is None:
    raise RuntimeError("FreeCAD main window is not available")

main_window.resize(1720, 900)
main_window.show()
application.processEvents()


def process_for(seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        application.processEvents()
        time.sleep(0.01)


available = FreeCADGui.listWorkbenches()
required = ("PartDesignWorkbench", "SketcherWorkbench")
missing = [name for name in required if name not in available]
if missing:
    raise RuntimeError(f"Mechanical workbenches are not registered: {missing}")

for workbench_name in required:
    FreeCADGui.activateWorkbench(workbench_name)
    process_for(1.0)

    active = FreeCADGui.activeWorkbench()
    if active is None:
        raise RuntimeError(f"No active workbench after activating {workbench_name}")

    active_name = active.name() if hasattr(active, "name") else ""
    if active_name and active_name != workbench_name:
        raise RuntimeError(
            f"Expected active workbench {workbench_name}, got {active_name}"
        )

process_for(1.0)

property_dock = main_window.findChild(
    QtWidgets.QDockWidget, "SolidFreeCADPropertyManager"
)
property_panel = main_window.findChild(
    QtWidgets.QWidget, "SolidFreeCADPropertyManagerWidget"
)
if property_dock is None or property_panel is None or not property_dock.isVisible():
    raise RuntimeError("SolidFreeCAD Property Manager is not installed and visible")

model_trees = [
    tree
    for tree in main_window.findChildren(QtWidgets.QTreeView)
    if bool(tree.property("SolidFreeCADModelTree"))
]
if not model_trees:
    raise RuntimeError("The official model tree was not enhanced by SolidFreeCAD")
if not all(tree.alternatingRowColors() and tree.uniformRowHeights() for tree in model_trees):
    raise RuntimeError("The enhanced model tree did not retain its compact history settings")

from workshop_model import create_workshop_part

model = create_workshop_part("SolidPropertyManagerProbe")
App.setActiveDocument(model.document.Name)
model.document.recompute()
process_for(0.25)


def expect_feature_kind(obj: object, expected: str) -> None:
    FreeCADGui.Selection.clearSelection()
    process_for(0.05)
    FreeCADGui.Selection.addSelection(obj.Document.Name, obj.Name)
    process_for(0.4)
    actual = str(property_panel.property("SolidFeatureKind"))
    panel_object = str(property_panel.property("SolidObjectName"))
    if actual != expected:
        properties = ",".join(sorted(str(name) for name in obj.PropertiesList))
        raise RuntimeError(
            "Property Manager classification mismatch: "
            f"expected={expected} actual={actual} "
            f"requested={obj.Document.Name}/{obj.Name} "
            f"panel_object={panel_object} type_id={obj.TypeId} "
            f"properties={properties}"
        )


expect_feature_kind(model.sketch, "Sketch")
expect_feature_kind(model.pad, "Pad")

length_editor = main_window.findChild(
    QtWidgets.QDoubleSpinBox, "SolidFreeCADLengthEditor"
)
apply_button = main_window.findChild(
    QtWidgets.QPushButton, "SolidFreeCADApplyProperties"
)
if length_editor is None or apply_button is None:
    raise RuntimeError("Pad Property Manager controls are missing")

new_length = float(model.pad.Length.Value) + 5.0
length_editor.setValue(new_length)
apply_button.click()
process_for(0.4)
if abs(float(model.pad.Length.Value) - new_length) > 1e-9:
    raise RuntimeError("Property Manager did not update the Pad length")
if model.pad.Shape.isNull() or not model.pad.Shape.isValid():
    raise RuntimeError("Property Manager produced an invalid Pad after recompute")

pocket_document = App.newDocument("SolidPropertyManagerPocketProbe")
pocket = pocket_document.addObject("PartDesign::Pocket", "PocketProbe")
pocket.Label = "Pocket probe"
expect_feature_kind(pocket, "Pocket")

FreeCADGui.Selection.clearSelection()
App.closeDocument(pocket_document.Name)
App.closeDocument(model.document.Name)
process_for(0.1)

workspace_root = os.environ.get("GITHUB_WORKSPACE")
if workspace_root:
    m3_artifact_dir = Path(workspace_root) / "build" / "artifacts" / "m3-partdesign"
elif Path("/results").is_dir():
    m3_artifact_dir = Path("/results") / "m3-partdesign"
else:
    m3_artifact_dir = Path.cwd() / "m3-partdesign-artifacts"
os.environ["SOLIDFREECAD_M3_ARTIFACT_DIR"] = str(m3_artifact_dir)

from m3_partdesign_smoke import main as run_m3_partdesign_smoke

run_m3_partdesign_smoke()
process_for(0.1)

print(
    "SOLIDFREECAD_WORKBENCH_SMOKE_OK "
    f"registered={','.join(required)} "
    "property_manager=Sketch,Pad,Pocket,Revolution,Fillet,Chamfer "
    f"pad_length_mm={new_length} m3_artifacts={m3_artifact_dir}",
    flush=True,
)
application.quit()
