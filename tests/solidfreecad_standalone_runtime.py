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


def feature(kind, profile=None, edges=None, source=None, **parameters):
    session = b.FeatureSession(kind, profile=profile, edge_selection=edges, pattern_source=source)
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
    path = OUTPUT / "SolidFreeCAD-alpha13-validation.FCStd"
    b.save_document(str(path))
    step = OUTPUT / "SolidFreeCAD-alpha13-validation.step"
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
    px, py = b.pointer_in_sketch(point)
    check("local_plane_coordinates", near(px, 8) and near(py, 20), coordinates=[px, py])
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


def sketch_and_pattern_checks():
    slot_doc, _ = part()
    s = b.SketchSession()
    b.add_slot(60, 20)
    check("slot_native_tangent_wire", s.sketch.solve() == 0 and s.sketch.Shape.Wires[0].isClosed() and sum(c.Type == "Tangent" for c in s.sketch.Constraints) == 4)
    s.accept()
    slot_pad = feature("pad", profile=s.sketch, value=10)
    check("slot_analytic_volume", near(slot_pad.Shape.Volume, (40 * 20 + math.pi * 100) * 10), volume=slot_pad.Shape.Volume)
    edit = b.SketchSession(sketch=s.sketch)
    b.constrain_geometry(s.sketch, 1, "Radius", 15)
    slot_doc.recompute()
    check("slot_driving_radius", near(slot_pad.Shape.Volume, (40 * 30 + math.pi * 225) * 10))
    count = s.sketch.GeometryCount
    for length, width in ((20, 20), (10, 20), (-1, 5)):
        try:
            b.add_slot(length, width)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid slot accepted")
    check("invalid_slot_preserves_sketch", s.sketch.GeometryCount == count and s.sketch.solve() == 0)
    edit.cancel()
    check("slot_edit_cancel", near(slot_pad.Shape.Volume, (40 * 20 + math.pi * 100) * 10))

    _, _ = part()
    s = b.SketchSession()
    for points in (((-10, 0), (0, 10), (10, 0)), ((30, 0), (40, -10), (50, 0))):
        b.add_arc_points(*points)
    from sfc8.sketch_geometry import arc_through_points
    samples = arc_through_points((-10, 0), (0, 10), (10, 0))
    shape = s.sketch.Geometry[0].toShape()
    check("three_point_arcs_both_directions", all(near(g.Radius, 10) and near(g.toShape().Length, 10 * math.pi) for g in s.sketch.Geometry))
    check("arc_preview_matches_native_curve", all(shape.distToShape(Part.Vertex(App.Vector(*p, 0)))[0] < 1e-6 for p in samples))
    for points in (((0, 0), (0, 0), (10, 10)), ((0, 0), (5, 5), (10, 10))):
        try:
            b.add_arc_points(*points)
        except ValueError:
            pass
        else:
            raise AssertionError("Degenerate arc accepted")
    check("invalid_arc_preserves_sketch", s.sketch.GeometryCount == 2 and s.sketch.solve() == 0)
    s.cancel()
    s = b.SketchSession()
    b.add_line_points((0, 0), (10, 0))
    try:
        b.add_line_points((10, 0), (0, 0))
    except ValueError:
        pass
    else:
        raise AssertionError("Redundant snapped line accepted")
    check("invalid_snapped_line_rolls_back", s.sketch.GeometryCount == 1 and s.sketch.solve() == 0 and near(s.sketch.Geometry[0].toShape().Length, 10))
    s.cancel()

    s = b.SketchSession()
    b.add_line_points((10, 10), (30, 20))
    b.add_line_points((10, 40), (30, 55))
    b.constrain_pair(s.sketch, 0, 1, "Parallel")
    b.constrain_pair(s.sketch, 0, 1, "Equal")
    a, c = s.sketch.Geometry
    va, vc = a.EndPoint - a.StartPoint, c.EndPoint - c.StartPoint
    check("parallel_and_equal_relations", va.cross(vc).Length < 1e-6 and near(va.Length, vc.Length))
    count = s.sketch.ConstraintCount
    try:
        b.constrain_pair(s.sketch, 0, 1, "Perpendicular")
    except ValueError:
        pass
    else:
        raise AssertionError("Conflicting relation accepted")
    check("conflicting_relation_rolls_back", s.sketch.ConstraintCount == count and s.sketch.solve() == 0)
    s.cancel()

    s = b.SketchSession()
    b.add_line_points((10, 10), (30, 20))
    b.add_line_points((10, 40), (30, 55))
    b.constrain_pair(s.sketch, 0, 1, "Perpendicular")
    a, c = s.sketch.Geometry
    check("perpendicular_relation", abs((a.EndPoint - a.StartPoint).dot(c.EndPoint - c.StartPoint)) < 1e-6)
    s.cancel()
    s = b.SketchSession()
    b.add_circle_points((0, 0), (5, 0))
    b.add_circle_points((20, 10), (29, 10))
    b.constrain_pair(s.sketch, 0, 1, "Concentric")
    b.constrain_pair(s.sketch, 0, 1, "Equal")
    b.constrain_geometry(s.sketch, 0, "Diameter", 18)
    b.constrain_geometry(s.sketch, 0, "Diameter", 24)
    a, c = s.sketch.Geometry
    check("concentric_and_equal_circles", (a.Center - c.Center).Length < 1e-6 and near(a.Radius, 12) and near(c.Radius, 12))
    check("diameter_updates_existing_dimension", sum(c.Type == "Diameter" for c in s.sketch.Constraints) == 1)
    s.cancel()
    s = b.SketchSession()
    b.add_line_points((-15, 10), (15, 10))
    b.add_circle_points((0, 0), (5, 0))
    b.constrain_pair(s.sketch, 0, 1, "Tangent")
    a, c = s.sketch.Geometry
    check("line_circle_tangency", near(abs(c.Center.y - a.StartPoint.y), c.Radius))
    s.cancel()
    s = b.SketchSession()
    b.add_line_points((10, 10), (30, 20))
    b.constrain_geometry(s.sketch, 0, "Angle", 45)
    b.constrain_geometry(s.sketch, 0, "Angle", 60)
    vector = s.sketch.Geometry[0].EndPoint - s.sketch.Geometry[0].StartPoint
    check("angle_uses_degrees_and_updates_datum", near(math.degrees(math.atan2(vector.y, vector.x)), 60) and s.sketch.ConstraintCount == 1)
    s.cancel()
    s = b.SketchSession()
    b.add_line_points((-10, 0), (10, 0))
    b.add_line_points((0, -10), (0, 10))
    s.accept()
    edit = b.SketchSession(sketch=s.sketch)
    b.trim_geometry(0, (5, 0))
    check("native_trim_at_intersection", near(s.sketch.Geometry[0].EndPoint.x, 0) and near(s.sketch.Geometry[0].StartPoint.x, -10))
    edit.cancel()
    check("trim_cancel_restores_entity", near(s.sketch.Geometry[0].EndPoint.x, 10) and s.sketch.solve() == 0)

    linear_doc, linear_body = part()
    s = b.SketchSession()
    b.add_rectangle(160, 100)
    s.accept()
    feature("pad", profile=s.sketch, value=10)
    s = b.SketchSession()
    s.sketch.Placement.Base = App.Vector(0, 0, 10)
    b.add_circle_points((-40, 0), (-35, 0))
    s.accept()
    pocket = feature("pocket", profile=s.sketch, value=10, through=True)
    pattern = feature("linear_pattern", source=pocket, value=40, count=3, pattern_axis="X")
    volume = 160000 - 3 * math.pi * 25 * 10
    check("native_linear_pattern", pattern.TypeId == "PartDesign::LinearPattern" and pattern.Originals == [pocket] and near(pattern.Shape.Volume, volume), volume=pattern.Shape.Volume)
    edit = b.FeatureSession("linear_pattern", feature=pattern)
    check("linear_pattern_axis_y", edit.update(value=20, count=3, pattern_axis="Y") and near(pattern.Shape.Volume, volume))
    check("linear_pattern_reverse", edit.update(value=20, count=2, pattern_axis="X", reverse=True) and near(pattern.Shape.Volume, 160000 - 2 * math.pi * 25 * 10))
    check("missing_pattern_instances_rejected", not edit.update(value=1000, count=3, pattern_axis="X") and "instancia" in edit.error, error=edit.error)
    check("invalid_pattern_count_rejected", not edit.update(value=20, count=101, pattern_axis="X"))
    edit.cancel()
    check("pattern_cancel_restores_parameters_and_tip", near(pattern.Shape.Volume, volume) and int(pattern.Occurrences) == 3 and near(float(pattern.Length), 80) and linear_body.Tip == pattern and pattern.Visibility)
    edit = b.FeatureSession("linear_pattern", feature=pattern)
    check("pattern_count_preview", edit.update(value=20, count=4, pattern_axis="X") and near(pattern.Shape.Volume, 160000 - 4 * math.pi * 25 * 10))
    edit.accept()
    linear_doc.undo(); linear_doc.recompute()
    check("pattern_undo", near(pattern.Shape.Volume, volume) and int(pattern.Occurrences) == 3)
    linear_doc.redo(); linear_doc.recompute()
    check("pattern_redo", int(pattern.Occurrences) == 4 and near(pattern.Shape.Volume, 160000 - 4 * math.pi * 25 * 10))
    linear_doc.undo(); linear_doc.recompute()
    linear_body.Placement = App.Placement(App.Vector(200, -100, 50), App.Rotation(App.Vector(0, 0, 1), 35))
    edit = b.FeatureSession("linear_pattern", feature=pattern)
    check("pattern_on_placed_body", edit.update(value=40, count=3, pattern_axis="X") and near(pattern.Shape.Volume, volume), error=edit.error)
    edit.cancel()
    linear_body.Placement = App.Placement()
    linear_doc.recompute()
    path = OUTPUT / "SolidFreeCAD-alpha13-linear-pattern.FCStd"
    b.save_document(str(path))
    linear_name = linear_doc.Name
    App.closeDocument(linear_name)
    linear_doc = b.open_document(str(path))
    created.append(linear_doc.Name)
    pattern = linear_doc.getObject("LinearPattern")
    check("pattern_fcstd_native_history", pattern.Originals[0].TypeId == "PartDesign::Pocket" and int(pattern.Occurrences) == 3 and near(pattern.Shape.Volume, volume))
    edit = b.FeatureSession("linear_pattern", feature=pattern)
    check("pattern_edit_after_reopen", edit.update(value=20, count=4, pattern_axis="X"))
    edit.cancel()
    edit = b.FeatureSession("linear_pattern", feature=pattern)
    edit.update(value=20, count=2, pattern_axis="X", reverse=True)
    edit.accept()
    prior_volume = pattern.Shape.Volume
    edit = b.SketchSession(sketch=linear_doc.getObject("Sketch"))
    b.constrain_geometry(edit.sketch, 0, "Distance", 110)
    try:
        edit.accept()
    except ValueError as exc:
        check("upstream_edit_rejects_missing_pattern_copy", "instancia" in str(exc), error=str(exc))
    else:
        raise AssertionError("Upstream edit silently removed a pattern instance")
    edit.cancel()
    check("upstream_pattern_cancel_restores_solid", near(pattern.Shape.Volume, prior_volume) and near(linear_doc.getObject("Sketch").Geometry[0].toShape().Length, 160))
    edit = b.FeatureSession("linear_pattern", feature=pattern)
    edit.update(value=40, count=3, pattern_axis="X")
    edit.accept()
    pattern.Mode = "Spacing"
    linear_doc.recompute()
    try:
        b.FeatureSession("linear_pattern", feature=pattern)
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported external pattern mode was silently converted")
    check("unsupported_pattern_mode_preserved", str(pattern.Mode) == "Spacing")
    pattern.Mode = "Extent"
    linear_doc.recompute()

    polar_doc, polar_body = part()
    polar_doc.Label = "Brida · Patrón circular paramétrico"
    s = b.SketchSession()
    b.add_circle(60)
    s.accept()
    feature("pad", profile=s.sketch, value=10)
    s = b.SketchSession()
    s.sketch.Placement.Base = App.Vector(0, 0, 10)
    b.add_circle_points((35, 0), (40, 0))
    s.accept()
    pocket = feature("pocket", profile=s.sketch, value=10, through=True)
    polar = feature("polar_pattern", source=pocket, value=360, count=6, pattern_axis="Z")
    volume = math.pi * (3600 - 6 * 25) * 10
    check("native_full_polar_pattern", polar.TypeId == "PartDesign::PolarPattern" and near(polar.Shape.Volume, volume) and int(polar.Occurrences) == 6, volume=polar.Shape.Volume)
    edit = b.FeatureSession("polar_pattern", feature=polar)
    check("partial_polar_pattern_includes_endpoints", edit.update(value=180, count=4, pattern_axis="Z") and near(polar.Shape.Volume, math.pi * (3600 - 4 * 25) * 10))
    check("partial_polar_pattern_reverse", edit.update(value=180, count=4, pattern_axis="Z", reverse=True) and near(polar.Shape.Volume, math.pi * (3600 - 4 * 25) * 10))
    edit.cancel()
    step = OUTPUT / "SolidFreeCAD-alpha13-polar-pattern.step"
    b.export_step(str(step))
    exported = Part.read(str(step))
    check("pattern_step_round_trip", exported.isValid() and len(exported.Solids) == 1 and near(exported.Volume, volume))
    b.save_document(str(OUTPUT / "SolidFreeCAD-alpha13-polar-pattern.FCStd"))
    old_count = len(polar_doc.Objects)
    invalid = b.FeatureSession("linear_pattern", pattern_source=pocket)
    valid = invalid.update(value=1000, count=3, pattern_axis="X")
    try:
        invalid.accept()
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid pattern committed")
    invalid.cancel()
    check("invalid_new_pattern_rollback", not valid and len(polar_doc.Objects) == old_count and polar_body.Tip == polar and polar.Visibility)

    boss_doc, _ = part()
    boss_doc.Label = "Placa · Patrón de salientes"
    s = b.SketchSession()
    b.add_rectangle(160, 80)
    s.accept()
    feature("pad", profile=s.sketch, value=5)
    s = b.SketchSession()
    s.sketch.Placement.Base = App.Vector(0, 0, 5)
    b.add_rectangle_points((-45, -5), (-35, 5))
    s.accept()
    boss = feature("pad", profile=s.sketch, value=10)
    trial = b.FeatureSession("linear_pattern", pattern_source=boss)
    check("additive_pattern_material", trial.update(value=40, count=3, pattern_axis="X") and near(trial.feature.Shape.Volume, 67000), error=trial.error)
    check("disconnected_additive_copies_rejected", not trial.update(value=1000, count=3, pattern_axis="X"), error=trial.error)
    trial.cancel()
    return linear_doc, polar_doc, boss_doc


def gui_checks(doc, pattern_docs):
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
        window.grab().save(str(OUTPUT / f"SolidFreeCAD-alpha13-{width}.png"))
    window.resize(1440, 900)
    window.new_sketch(plane="XY")
    sketch_name = window.session.sketch.Name
    check("reference_plane_sketch_visible_inside_solid", not doc.getObject("Chamfer").Visibility and window.session.sketch.Visibility)
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
    check("cancel_restores_solid_visibility", doc.getObject("Chamfer").Visibility)
    b.select_object("Pad")
    window.edit_selected()
    window.manager.value.setValue(50)
    window.preview_feature()
    check("property_manager_native_preview", near(float(doc.getObject("Pad").Length), 50) and window.session.valid)
    QtWidgets.QApplication.processEvents()
    window.grab().save(str(OUTPUT / "SolidFreeCAD-alpha13-property-manager.png"))
    window.cancel_manager_operation()
    check("property_manager_cancel", near(float(doc.getObject("Pad").Length), 40))
    window.manager.filter.setText("Corte")
    check("feature_tree_filter", window.manager.tree.items_by_name["Pad"].isHidden() and not window.manager.tree.items_by_name["Pocket"].isHidden())
    window.manager.filter.clear()
    window.search.setText("isometrica")
    window.run_search()
    check("command_search", window.search.text() == "")
    check("single_manager", len(window.findChildren(QtWidgets.QDockWidget)) == 1 and window.ribbon.count() == 4)
    new_gui_checks(window, pattern_docs)
    window.close()
    check("host_restored_on_close", window.host.centralWidget() is not None and not window.timer.isActive() and not window.preview_timer.isActive())
    QtWidgets.QApplication.processEvents()


def new_gui_checks(window, pattern_docs):
    window.new_sketch(plane="XY")
    controller = window.sketch_interaction
    scene = Gui.activeDocument().activeView().getSceneGraph()
    nodes = scene.getNumChildren()
    window.start_tool("polyline")
    for point in ((60, 60), (100, 60), (100, 90), (60, 90), (60, 60)):
        controller.place_point(point)
    sketch = window.session.sketch
    check("interactive_polyline_closes_and_cleans_callbacks", sketch.GeometryCount == 4 and not controller.active and scene.getNumChildren() == nodes)
    b.constrain_geometry(sketch, 0, "Distance", 50)
    check("polyline_dimension_preserves_closed_wire", sketch.solve() == 0 and len(sketch.Shape.Wires) == 1 and sketch.Shape.Wires[0].isClosed() and near(sketch.Geometry[0].toShape().Length, 50))
    window.cancel_manager_operation()
    window.new_sketch(plane="XY")
    window.start_tool("polyline")
    controller.place_point((60, 60)); controller.place_point((80, 60))
    controller._on_key({"State": "DOWN", "Key": "RETURN"})
    check("enter_finishes_open_polyline", not controller.active and window.session.sketch.GeometryCount == 1 and not controller.callbacks)
    window.start_tool("arc")
    controller.place_point((60, 60)); controller.place_point((70, 70))
    controller._update_preview((80, 60))
    check("transient_three_point_arc_preview", controller.preview_coords.point.getNum() == 49)
    controller.place_point((80, 60))
    check("interactive_arc_commit", window.session.sketch.GeometryCount == 2 and b.geometry_kind(window.session.sketch.Geometry[1]) == "Arco" and not controller.active)
    b.add_line_points((100, 100), (120, 100))
    b.add_line_points((110, 90), (110, 110))
    window.start_tool("trim")
    controller.pick_tolerance = .1
    controller.place_point((115, 100))
    check("interactive_trim_stays_active", controller.active and near(window.session.sketch.Geometry[2].EndPoint.x, 110))
    window.escape_operation()
    check("trim_escape_keeps_sketch", not controller.active and window.session is not None and not controller.callbacks)
    window.cancel_manager_operation()
    window.new_sketch(plane="XY")
    window.manager.slot_length.setValue(60)
    window.manager.slot_width.setValue(20)
    window.add_slot()
    check("slot_property_manager", window.session.sketch.GeometryCount == 4 and window.manager.geometry.count() == 4 and "Arco" in window.manager.geometry.itemText(1))
    window.manager.constraint.setCurrentIndex(window.manager.constraint.findData("Angle"))
    check("angle_editor_units", window.manager.dimension_value.suffix().strip() == "°" and not window.manager.geometry2.isVisible())
    window.manager.constraint.setCurrentIndex(window.manager.constraint.findData("Tangent"))
    check("pair_relation_editor", window.manager.geometry2.isVisible() and not window.manager.dimension_value.isEnabled())
    window.resize(1366, 768)
    b.fit_view()
    QtWidgets.QApplication.processEvents()
    window.grab().save(str(OUTPUT / "SolidFreeCAD-alpha13-sketch.png"))
    check("new_commands_have_original_icons", all(not window.actions[key].icon().isNull() for key in ("polyline", "arc", "slot", "trim", "linear_pattern", "polar_pattern")))
    window.cancel_manager_operation()
    linear_doc, polar_doc, boss_doc = pattern_docs
    App.setActiveDocument(linear_doc.Name)
    window.refresh(True)
    window.edit_object("LinearPattern")
    check("linear_property_manager_loads_spacing", window.manager.pattern_count.value() == 3 and near(window.manager.value.value(), 40) and window.manager.pattern_axis.currentData() == "X")
    window.manager.value.setValue(1000)
    window.preview_feature()
    check("invalid_pattern_disables_accept", not window.manager.accept.isEnabled() and "instancia" in window.manager.message.text())
    window.cancel_manager_operation()
    App.setActiveDocument(boss_doc.Name)
    b.select_object("Pad001")
    window.refresh(True)
    window.begin_feature("linear_pattern")
    window.manager.value.setValue(40)
    window.manager.pattern_count.setValue(3)
    window.manager.pattern_axis.setCurrentIndex(window.manager.pattern_axis.findData("X"))
    window.accept_manager_operation()
    check("gui_creates_native_pattern", window.session is None and boss_doc.getObject("LinearPattern").TypeId == "PartDesign::LinearPattern" and near(boss_doc.getObject("LinearPattern").Shape.Volume, 67000))
    App.setActiveDocument(polar_doc.Name)
    window.refresh(True)
    window.edit_object("PolarPattern")
    check("polar_property_manager_loads_native_axis", window.manager.pattern_count.value() == 6 and near(window.manager.value.value(), 360) and window.manager.pattern_axis.currentData() == "Z" and window.manager.value.suffix().strip() == "°")
    window.resize(1440, 900)
    b.axonometric_view(); b.fit_view()
    Gui.Selection.clearSelection()
    QtWidgets.QApplication.processEvents()
    window.grab().save(str(OUTPUT / "SolidFreeCAD-alpha13-polar-pattern.png"))
    window.cancel_manager_operation()


def run():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = dict(runtime=App.Version(), platform=sys.platform)
    try:
        doc = model_checks()
        pattern_docs = sketch_and_pattern_checks()
        gui_checks(doc, pattern_docs)
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
