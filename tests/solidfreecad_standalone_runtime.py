"""End-to-end checks on the real FreeCAD 1.1.1 GUI and geometry engine.

Launch with FreeCAD.exe (or Linux freecad), not the system Python interpreter.
SOLIDFREECAD_TEST_OUTPUT selects the directory for JSON, CAD files and images.
"""
from pathlib import Path
import json
import math
import os
import sys
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtWidgets

ROOT = Path(os.environ.get("SOLIDFREECAD_SOURCE_ROOT", Path(__file__).resolve().parents[1]))
OUTPUT = Path(os.environ.get("SOLIDFREECAD_TEST_OUTPUT", ROOT / "dist" / "standalone-validation"))
sys.path.insert(0, str(ROOT / "standalone"))
from sfc8 import backend as b

checks = []
created = []
live_window = None


def check(name, condition, **evidence):
    if not condition:
        raise AssertionError(name + ": " + repr(evidence))
    checks.append(dict(name=name, status="PASS", **evidence))


def near(a, b):
    return math.isclose(a, b, rel_tol=1e-7, abs_tol=1e-5)


def part():
    doc, body = b.new_part()
    created.append(doc.Name)
    return doc, body


def feature(kind, profile=None, edges=None, **parameters):
    session = b.FeatureSession(kind, profile=profile, edge_selection=edges)
    if not session.update(**parameters):
        message = session.error
        session.cancel()
        raise AssertionError(kind + ": " + message)
    return session.accept()


def model_checks():
    doc, body = part()
    sketch = b.SketchSession()
    b.add_rectangle(100, 60)
    sketch.accept()
    pad = feature("pad", profile=sketch.sketch, value=20)
    check("native_pad_volume", pad.TypeId == "PartDesign::Pad" and near(pad.Shape.Volume, 120000), volume=pad.Shape.Volume)
    edit = b.FeatureSession("pad", feature=pad)
    check("symmetric_preview", edit.update(value=30, symmetric=True), error=edit.error)
    check("symmetric_geometry", near(pad.Shape.BoundBox.ZMin, -15) and near(pad.Shape.BoundBox.ZMax, 15))
    edit.cancel()
    check("cancel_restores_parameters", near(float(pad.Length), 20) and near(pad.Shape.Volume, 120000))
    edit = b.FeatureSession("pad", feature=pad)
    edit.update(value=30)
    edit.accept()
    check("parametric_edit", near(pad.Shape.Volume, 180000))
    doc.undo(); doc.recompute()
    check("native_undo", near(pad.Shape.Volume, 120000))
    doc.redo(); doc.recompute()
    check("native_redo", near(pad.Shape.Volume, 180000))
    # A supported sketch must follow the selected top face rather than global XY.
    top_face = next(i for i, f in enumerate(pad.Shape.Faces, 1) if isinstance(f.Surface, Part.Plane) and f.normalAt(0, 0).z > .99)
    hole = b.SketchSession(face=(pad, "Face" + str(top_face)))
    b.add_circle(10)
    hole.accept()
    check("planar_face_support", near(hole.sketch.getGlobalPlacement().Base.z, 30))
    pocket = feature("pocket", profile=hole.sketch, value=10)
    check("pocket_depth", near(pocket.Shape.Volume, 180000 - math.pi * 100 * 10), volume=pocket.Shape.Volume)
    edit = b.FeatureSession("pocket", feature=pocket)
    check("through_all_preview", edit.update(value=10, through=True), error=edit.error)
    edit.accept()
    check("through_all_volume", near(pocket.Shape.Volume, 180000 - math.pi * 100 * 30), volume=pocket.Shape.Volume)
    old_count = len(doc.Objects)
    invalid = b.FeatureSession("fillet", edge_selection=(pocket, ["Edge1"]))
    check("invalid_preview_rejected", not invalid.update(value=10000))
    invalid.cancel()
    check("invalid_preview_rollback", len(doc.Objects) == old_count and body.Tip == pocket and pocket.Visibility)
    edge = next(i for i, edge in enumerate(pocket.Shape.Edges, 1) if isinstance(edge.Curve, Part.Line) and near(edge.Length, 30))
    fillet = feature("fillet", edges=(pocket, ["Edge" + str(edge)]), value=2)
    check("native_fillet", fillet.TypeId == "PartDesign::Fillet" and fillet.Shape.isValid() and fillet.Shape.Volume < pocket.Shape.Volume, volume=fillet.Shape.Volume)
    edge = next(i for i, edge in enumerate(fillet.Shape.Edges, 1) if isinstance(edge.Curve, Part.Circle) and near(edge.Curve.Radius, 10))
    chamfer = feature("chamfer", edges=(fillet, ["Edge" + str(edge)]), value=1)
    check("native_chamfer", chamfer.TypeId == "PartDesign::Chamfer" and chamfer.Shape.isValid() and chamfer.Shape.Volume < fillet.Shape.Volume, volume=chamfer.Shape.Volume)
    edit = b.FeatureSession("pad", feature=pad)
    check("upstream_edit_preview", edit.update(value=40))
    edit.accept()
    check("downstream_recompute", chamfer.Shape.isValid() and chamfer.Shape.Volume > 220000 and body.Tip == chamfer and chamfer.Visibility and not pad.Visibility, volume=chamfer.Shape.Volume)
    volume = chamfer.Shape.Volume
    path = OUTPUT / "SolidFreeCAD-alpha12-validation.FCStd"
    b.save_document(str(path))
    step = OUTPUT / "SolidFreeCAD-alpha12-validation.step"
    b.export_step(str(step))
    exported = Part.read(str(step))
    check("step_round_trip", exported.isValid() and len(exported.Solids) == 1 and near(exported.Volume, volume), volume=exported.Volume)
    name = doc.Name
    App.closeDocument(name)
    reopened = b.open_document(str(path))
    created.append(reopened.Name)
    check("fcstd_native_history", all(reopened.getObject(name) is not None for name in ("Sketch", "Pad", "Pocket", "Fillet", "Chamfer")) and near(reopened.getObject("Chamfer").Shape.Volume, volume))
    reopened.getObject("Pad").Length = 45
    reopened.recompute()
    check("fcstd_edit_after_reopen", reopened.getObject("Chamfer").Shape.isValid() and reopened.getObject("Chamfer").Shape.Volume > volume)
    reopened.getObject("Pad").Length = 40
    reopened.recompute()
    # Multiple wires (including holes) must all participate in a native Pad.
    other, other_body = part()
    s = b.SketchSession()
    b.add_rectangle(100, 60)
    b.add_circle(10)
    s.accept()
    multi = feature("pad", profile=s.sketch, value=20)
    check("pad_preserves_inner_wire", near(multi.Shape.Volume, (6000 - math.pi * 100) * 20), volume=multi.Shape.Volume)
    # An arbitrary sketch plane must give a correctly oriented native revolution.
    rev_doc, rev_body = part()
    s = b.SketchSession(plane="XZ")
    b.add_rectangle_points((5, 0), (15, 40))
    local = App.Vector(8, 20, 0)
    point = s.sketch.getGlobalPlacement().multVec(local)
    check("local_plane_coordinates", b.pointer_in_sketch(point) == (8, 20))
    s.accept()
    rev = feature("revolution", profile=s.sketch, value=360)
    check("native_revolution", rev.TypeId == "PartDesign::Revolution" and near(rev.Shape.Volume, math.pi * (225 - 25) * 40), volume=rev.Shape.Volume)
    edit = b.FeatureSession("revolution", feature=rev)
    check("partial_reversed_revolution", edit.update(value=180, reverse=True), error=edit.error)
    edit.accept()
    check("partial_revolution_volume", near(rev.Shape.Volume, math.pi * (225 - 25) * 20))
    # A cancelled edit reverts entities AND dimensions as one transaction.
    App.setActiveDocument(other.Name)
    target = other.getObject("Sketch")
    count, constraints, old_volume = target.GeometryCount, target.ConstraintCount, multi.Shape.Volume
    edit = b.SketchSession(sketch=target)
    b.constrain_geometry(target, 0, "Distance", 110)
    b.add_line_points((150, 0), (160, 0))
    edit.cancel()
    check("cancel_sketch_restores_geometry_and_dimensions", target.GeometryCount == count and target.ConstraintCount == constraints and near(multi.Shape.Volume, old_volume))
    edit = b.SketchSession(sketch=target)
    b.constrain_geometry(target, 0, "Distance", 110)
    edit.accept()
    check("driving_dimension_updates_solid", near(multi.Shape.Volume, (6600 - math.pi * 100) * 20))
    try:
        b.remove_object(target.Name)
    except ValueError:
        pass
    else:
        raise AssertionError("Deletion must protect dependent features")
    check("dependent_references_protected", other.getObject(target.Name) is not None and multi.Shape.isValid())
    line_doc, _ = part()
    line_sketch = b.SketchSession(plane="YZ")
    _, index = b.add_line_points((0, 0), (10, 10))
    b.constrain_geometry(line_sketch.sketch, index, "Horizontal", 25)
    line_sketch.accept()
    geometry = line_sketch.sketch.Geometry[index]
    check("native_horizontal_relation", near(geometry.StartPoint.y, geometry.EndPoint.y))
    return reopened


def gui_checks(doc):
    global live_window
    from pivy import coin  # noqa: F401 -- load SWIG before asking for the scene graph.
    from sfc8.window_alpha12 import SolidFreeCADWindow
    App.setActiveDocument(doc.Name)
    doc.Label = "Brida · Validación paramétrica"
    window = SolidFreeCADWindow()
    live_window = window
    window.show()
    window.host.hide()
    window.refresh(True)
    Gui.Selection.clearSelection()
    b.axonometric_view()
    b.fit_view()
    QtWidgets.QApplication.processEvents()
    for width, height in ((1366, 768), (1920, 1080)):
        window.resize(width, height)
        QtWidgets.QApplication.processEvents()
        check(f"layout_{width}", window.centralWidget().width() > 700 and window.centralWidget().height() > 450 and window.ribbon.width() > width - 80, viewport=[window.centralWidget().width(), window.centralWidget().height()])
        window.grab().save(str(OUTPUT / f"SolidFreeCAD-alpha12-{width}.png"))
    window.resize(1440, 900)
    window.new_sketch(plane="XY")
    sketch_name = window.session.sketch.Name
    scene = Gui.activeDocument().activeView().getSceneGraph()
    nodes = scene.getNumChildren()
    window.start_tool("rectangle")
    check("preview_callback_registration", window.sketch_interaction.active and len(window.sketch_interaction.callbacks) == 3 and scene.getNumChildren() == nodes + 1)
    window.sketch_interaction.first_point = (60, 60)
    window.sketch_interaction._update_preview((100, 90))
    check("transient_rectangle_preview", window.sketch_interaction.preview_coords.point.getNum() == 5)
    window.escape_operation()
    check("escape_removes_transient_preview", not window.sketch_interaction.active and scene.getNumChildren() == nodes and window.session is not None)
    window.start_tool("circle")
    window.sketch_interaction.first_point = (60, 60)
    window.sketch_interaction._commit((70, 60))
    check("interactive_circle_commit", window.session.sketch.GeometryCount == 1 and not window.sketch_interaction.active)
    window.cancel_manager_operation()
    check("cancel_removes_new_sketch", doc.getObject(sketch_name) is None)
    b.select_object("Pad")
    window.edit_selected()
    window.manager.value.setValue(50)
    window.preview_feature()
    check("property_manager_native_preview", near(float(doc.getObject("Pad").Length), 50) and window.session.valid)
    QtWidgets.QApplication.processEvents()
    window.grab().save(str(OUTPUT / "SolidFreeCAD-alpha12-property-manager.png"))
    window.cancel_manager_operation()
    check("property_manager_cancel", near(float(doc.getObject("Pad").Length), 40))
    window.manager.filter.setText("Corte")
    check("feature_tree_filter", window.manager.tree.items_by_name["Pad"].isHidden() and not window.manager.tree.items_by_name["Pocket"].isHidden())
    window.manager.filter.clear()
    window.search.setText("isometrica")
    window.run_search()
    check("command_search", window.search.text() == "")
    check("single_manager", len(window.findChildren(QtWidgets.QDockWidget)) == 1 and window.ribbon.count() == 4)
    window.close()
    check("host_restored_on_close", window.host.centralWidget() is not None and not window.timer.isActive() and not window.preview_timer.isActive())
    QtWidgets.QApplication.processEvents()


def run():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = dict(runtime=App.Version(), platform=sys.platform)
    try:
        doc = model_checks()
        gui_checks(doc)
        report.update(status="PASS", checks=checks, count=len(checks))
    except Exception:
        report.update(status="FAIL", checks=checks, count=len(checks), error=traceback.format_exc())
        App.Console.PrintError(report["error"] + "\n")
    finally:
        if live_window is not None and not live_window._closed:
            live_window.close()
        for name in list(App.listDocuments()):
            if name in created:
                App.closeDocument(name)
        QtWidgets.QApplication.processEvents()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
        (OUTPUT / "runtime-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        QtCore.QTimer.singleShot(200, QtWidgets.QApplication.instance().quit)


QtCore.QTimer.singleShot(500, run)
