from __future__ import annotations

import os
import time
from pathlib import Path

import FreeCAD as App
import Part


vertical_slice = os.environ.get("SOLIDFREECAD_VERTICAL_SLICE")
default_artifact_dir = (
    Path(vertical_slice).resolve().parent / "m3-partdesign"
    if vertical_slice
    else Path("m3-partdesign-artifacts").resolve()
)
ARTIFACT_DIR = Path(
    os.environ.get("SOLIDFREECAD_M3_ARTIFACT_DIR", str(default_artifact_dir))
).resolve()
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def assert_valid_solid(feature, label: str) -> float:
    shape = feature.Shape
    if shape.isNull() or not shape.isValid():
        raise RuntimeError(f"{label} did not create a valid shape")
    volume = float(shape.Volume)
    if volume <= 0.0:
        raise RuntimeError(f"{label} did not create a positive solid volume")
    return volume


def test_revolution() -> None:
    document = App.newDocument("SolidFreeCADM3Revolution")
    body = document.addObject("PartDesign::Body", "Body")
    box = document.addObject("PartDesign::AdditiveBox", "Box")
    body.addObject(box)
    box.Length = 10.0
    box.Width = 10.0
    box.Height = 10.0
    document.recompute()

    revolution = document.addObject("PartDesign::Revolution", "Revolution")
    revolution.Profile = (box, ["Face6"])
    revolution.ReferenceAxis = (document.Y_Axis, [""])
    revolution.Angle = 180.0
    revolution.Reversed = True
    revolution.Midplane = False
    body.addObject(revolution)
    document.recompute()

    volume = assert_valid_solid(revolution, "Revolution")
    if abs(float(revolution.Angle) - 180.0) > 1e-9:
        raise RuntimeError("Revolution angle was not preserved")
    document.saveAs(str(ARTIFACT_DIR / "m3-revolution.FCStd"))
    print(
        f"SOLIDFREECAD_M3_REVOLUTION_OK volume_mm3={volume:.6f} angle_deg={float(revolution.Angle):.3f}",
        flush=True,
    )
    App.closeDocument(document.Name)


def build_fillet_document(document_name: str = "SolidFreeCADM3Fillet"):
    document = App.newDocument(document_name)
    body = document.addObject("PartDesign::Body", "Body")
    box = document.addObject("PartDesign::AdditiveBox", "Box")
    body.addObject(box)
    box.Length = 20.0
    box.Width = 20.0
    box.Height = 20.0
    document.recompute()

    fillet = document.addObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (box, ["Face" + str(index + 1) for index in range(6)])
    fillet.Radius = 2.0
    fillet.UseAllEdges = False
    body.addObject(fillet)
    document.recompute()
    return document, body, box, fillet


def test_fillet_and_step_roundtrip() -> None:
    document, _body, _box, fillet = build_fillet_document()
    source_volume = assert_valid_solid(fillet, "Fillet")
    if source_volume >= 20.0 * 20.0 * 20.0:
        raise RuntimeError("Fillet did not remove material from the source box")

    source_fcstd = ARTIFACT_DIR / "m3-fillet.FCStd"
    step_path = ARTIFACT_DIR / "m3-fillet-roundtrip.step"
    imported_fcstd = ARTIFACT_DIR / "m3-step-imported.FCStd"
    document.saveAs(str(source_fcstd))
    Part.export([fillet], str(step_path))
    if not step_path.exists() or step_path.stat().st_size < 500:
        raise RuntimeError("STEP export did not create a usable file")

    print(
        f"SOLIDFREECAD_M3_FILLET_OK volume_mm3={source_volume:.6f} radius_mm={float(fillet.Radius):.3f}",
        flush=True,
    )
    App.closeDocument(document.Name)

    imported = App.newDocument("SolidFreeCADM3StepImported")
    Part.insert(str(step_path), imported.Name)
    imported.recompute()
    shape_objects = [
        obj
        for obj in imported.Objects
        if hasattr(obj, "Shape") and not obj.Shape.isNull() and obj.Shape.isValid()
    ]
    if not shape_objects:
        raise RuntimeError("STEP import did not create a valid shape object")
    imported_feature = max(shape_objects, key=lambda obj: float(obj.Shape.Volume))
    imported_volume = float(imported_feature.Shape.Volume)
    tolerance = max(1e-5, source_volume * 1e-6)
    if abs(imported_volume - source_volume) > tolerance:
        raise RuntimeError(
            "STEP round trip changed the solid volume: "
            f"source={source_volume} imported={imported_volume} tolerance={tolerance}"
        )
    imported.saveAs(str(imported_fcstd))
    print(
        "SOLIDFREECAD_STEP_ROUNDTRIP_OK "
        f"step={step_path} source_volume_mm3={source_volume:.6f} "
        f"imported_volume_mm3={imported_volume:.6f}",
        flush=True,
    )
    App.closeDocument(imported.Name)


def test_chamfer() -> None:
    document = App.newDocument("SolidFreeCADM3Chamfer")
    body = document.addObject("PartDesign::Body", "Body")
    box = document.addObject("PartDesign::AdditiveBox", "Box")
    body.addObject(box)
    box.Length = 20.0
    box.Width = 20.0
    box.Height = 20.0
    document.recompute()

    chamfer = document.addObject("PartDesign::Chamfer", "Chamfer")
    chamfer.Base = (box, ["Face" + str(index + 1) for index in range(6)])
    chamfer.Size = 2.0
    chamfer.UseAllEdges = False
    body.addObject(chamfer)
    document.recompute()

    volume = assert_valid_solid(chamfer, "Chamfer")
    if volume >= 20.0 * 20.0 * 20.0:
        raise RuntimeError("Chamfer did not remove material from the source box")
    document.saveAs(str(ARTIFACT_DIR / "m3-chamfer.FCStd"))
    print(
        f"SOLIDFREECAD_M3_CHAMFER_OK volume_mm3={volume:.6f} size_mm={float(chamfer.Size):.3f}",
        flush=True,
    )
    App.closeDocument(document.Name)


def process_events(application, seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        application.processEvents()
        time.sleep(0.01)


def test_gui_feature_editor() -> None:
    if not App.GuiUp:
        return

    import FreeCADGui
    from PySide import QtCore, QtWidgets

    main_window = FreeCADGui.getMainWindow()
    application = QtWidgets.QApplication.instance()
    if main_window is None or application is None:
        raise RuntimeError("M3 GUI validation requires the FreeCAD main window")

    ribbon = main_window.findChild(QtWidgets.QToolBar, "SolidFreeCADRibbon")
    tabs = main_window.findChild(QtWidgets.QTabBar, "SolidFreeCADRibbonTabs")
    if ribbon is None or tabs is None:
        raise RuntimeError("SolidFreeCAD ribbon is unavailable during M3 validation")
    tab_titles = [tabs.tabText(index) for index in range(tabs.count())]
    if "Simulación" in tab_titles or "Simulation" in tab_titles:
        raise RuntimeError("The out-of-scope Simulation tab is still visible")
    if not bool(ribbon.property("SolidFreeCADSimulationRemoved")):
        raise RuntimeError("The ribbon does not report the Simulation scope removal")

    document, _body, _box, fillet = build_fillet_document("SolidFreeCADM3GuiEditor")
    App.setActiveDocument(document.Name)
    FreeCADGui.Selection.clearSelection()
    FreeCADGui.Selection.addSelection(document.Name, fillet.Name)
    process_events(application, 0.8)

    panel = main_window.findChild(QtWidgets.QWidget, "SolidFreeCADPropertyManagerWidget")
    group = main_window.findChild(QtWidgets.QGroupBox, "SolidFreeCADM3FeatureGroup")
    value_editor = main_window.findChild(
        QtWidgets.QDoubleSpinBox, "SolidFreeCADAdvancedValueEditor"
    )
    use_all = main_window.findChild(QtWidgets.QCheckBox, "SolidFreeCADUseAllEdges")
    apply_button = main_window.findChild(
        QtWidgets.QPushButton, "SolidFreeCADApplyAdvancedFeature"
    )
    if panel is None or group is None or value_editor is None or apply_button is None:
        raise RuntimeError("The guided Part Design Property Manager was not installed")
    if not group.isVisible() or str(panel.property("SolidAdvancedFeatureKind")) != "Fillet":
        raise RuntimeError("The guided editor did not recognize the selected Fillet")
    if use_all is None or abs(value_editor.value() - 2.0) > 1e-9:
        raise RuntimeError("The guided Fillet properties were not loaded")

    previous_volume = float(fillet.Shape.Volume)
    value_editor.setValue(2.5)
    apply_button.click()
    process_events(application, 0.8)
    if abs(float(fillet.Radius) - 2.5) > 1e-9:
        raise RuntimeError("The guided editor did not apply the new Fillet radius")
    updated_volume = assert_valid_solid(fillet, "GUI Fillet")
    if abs(updated_volume - previous_volume) < 1e-6:
        raise RuntimeError("The Fillet shape did not recompute after the guided edit")

    gui_document = FreeCADGui.getDocument(document.Name)
    active_view = gui_document.activeView()
    active_view.viewAxonometric()
    active_view.fitAll()
    active_view.redraw()
    process_events(application, 0.25)

    screenshot_path = ARTIFACT_DIR / "solidfreecad-m3-partdesign.png"
    screen = application.primaryScreen()
    if screen is None:
        raise RuntimeError("No Qt screen is available for the M3 screenshot")
    screenshot = screen.grabWindow(int(main_window.winId()))
    if screenshot.isNull() or not screenshot.save(str(screenshot_path)):
        raise RuntimeError(f"Could not save the M3 screenshot to {screenshot_path}")

    print(
        "SOLIDFREECAD_M3_GUI_EDITOR_OK "
        f"radius_mm={float(fillet.Radius):.3f} screenshot={screenshot_path}",
        flush=True,
    )
    FreeCADGui.Selection.clearSelection()
    App.closeDocument(document.Name)


def main() -> None:
    test_revolution()
    test_fillet_and_step_roundtrip()
    test_chamfer()
    test_gui_feature_editor()
    print(f"SOLIDFREECAD_M3_PARTDESIGN_SMOKE_OK artifacts={ARTIFACT_DIR}", flush=True)


if __name__ == "__main__":
    main()
