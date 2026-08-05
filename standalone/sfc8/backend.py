"""FreeCAD document and geometry backend for the alpha.8 shell."""
from __future__ import annotations

import os

import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher


def active_document():
    return App.ActiveDocument


def active_body():
    doc = active_document()
    if doc is None:
        return None
    return next((o for o in doc.Objects if o.TypeId == "PartDesign::Body"), None)


def active_sketch():
    doc = active_document()
    if doc is None:
        return None
    for obj in Gui.Selection.getSelection():
        if getattr(obj, "TypeId", "") == "Sketcher::SketchObject":
            return obj
    sketches = [o for o in doc.Objects if o.TypeId == "Sketcher::SketchObject"]
    return sketches[-1] if sketches else None


def ensure_document():
    doc = active_document()
    if doc is None:
        doc = App.newDocument("SolidFreeCADPart")
        Gui.activeDocument().activeView().viewAxonometric()
    return doc


def ensure_body():
    doc = ensure_document()
    body = active_body()
    if body is None:
        body = doc.addObject("PartDesign::Body", "Body")
        body.Label = "Pieza"
        doc.recompute()
    return body


def new_part():
    doc = App.newDocument("SolidFreeCADPart")
    body = doc.addObject("PartDesign::Body", "Body")
    body.Label = "Pieza"
    doc.recompute()
    Gui.activeDocument().activeView().viewAxonometric()
    return doc, body


def new_sketch():
    doc = ensure_document()
    body = ensure_body()
    sketch = doc.addObject("Sketcher::SketchObject", "Sketch")
    sketch.Label = "Croquis"
    body.addObject(sketch)
    doc.recompute()
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(sketch)
    return sketch


def add_rectangle(width, height):
    sketch = active_sketch() or new_sketch()
    w, h = float(width), float(height)
    x0, y0 = -w / 2.0, -h / 2.0
    points = (
        App.Vector(x0, y0, 0),
        App.Vector(x0 + w, y0, 0),
        App.Vector(x0 + w, y0 + h, 0),
        App.Vector(x0, y0 + h, 0),
    )
    geometries = (
        Part.LineSegment(points[0], points[1]),
        Part.LineSegment(points[1], points[2]),
        Part.LineSegment(points[2], points[3]),
        Part.LineSegment(points[3], points[0]),
    )
    indices = [sketch.addGeometry(geometry, False) for geometry in geometries]
    for i in range(4):
        sketch.addConstraint(
            Sketcher.Constraint(
                "Coincident", indices[i], 2, indices[(i + 1) % 4], 1
            )
        )
    sketch.addConstraint(Sketcher.Constraint("Horizontal", indices[0]))
    sketch.addConstraint(Sketcher.Constraint("Horizontal", indices[2]))
    sketch.addConstraint(Sketcher.Constraint("Vertical", indices[1]))
    sketch.addConstraint(Sketcher.Constraint("Vertical", indices[3]))
    sketch.Document.recompute()
    fit_view()
    return sketch


def add_circle(radius):
    sketch = active_sketch() or new_sketch()
    r = float(radius)
    sketch.addGeometry(
        Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False
    )
    sketch.Document.recompute()
    fit_view()
    return sketch


def pad_sketch(length):
    sketch = active_sketch()
    if sketch is None:
        raise ValueError("Cree o seleccione un croquis cerrado.")
    doc = sketch.Document
    doc.recompute()
    wires = list(sketch.Shape.Wires)
    if not wires:
        raise ValueError("El croquis no contiene un perfil cerrado.")
    face = Part.Face(wires[0])
    value = float(length)
    solid = face.extrude(App.Vector(0, 0, value))
    body = active_body() or ensure_body()
    feature = body.newObject("PartDesign::Feature", "Pad")
    feature.Label = "Saliente/Base"
    feature.addProperty("App::PropertyLength", "Length", "SolidFreeCAD")
    feature.Length = value
    feature.addProperty("App::PropertyLink", "Profile", "SolidFreeCAD")
    feature.Profile = sketch
    feature.Shape = solid
    sketch.Visibility = False
    doc.recompute()
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(feature)
    axonometric_view()
    fit_view()
    return feature


def open_document(path):
    if path.lower().endswith(".fcstd"):
        return App.openDocument(path)
    import Import
    doc = App.newDocument(os.path.splitext(os.path.basename(path))[0])
    Import.insert(path, doc.Name)
    fit_view()
    return doc


def save_document(path=None):
    doc = active_document()
    if doc is None:
        return None
    if path:
        doc.saveAs(path)
    elif doc.FileName:
        doc.save()
    return doc


def _view():
    return Gui.activeDocument().activeView() if Gui.activeDocument() else None


def axonometric_view():
    view = _view()
    if view:
        view.viewAxonometric()


def front_view():
    view = _view()
    if view:
        view.viewFront()


def top_view():
    view = _view()
    if view:
        view.viewTop()


def fit_view():
    view = _view()
    if view:
        view.fitAll()


def set_light_background():
    params = App.ParamGet("User parameter:BaseApp/Preferences/View")
    params.SetBool("Simple", False)
    params.SetBool("UseBackgroundColorMid", False)
    params.SetUnsigned("BackgroundColor", 0xEEF2F7FF)
    params.SetUnsigned("BackgroundColor2", 0xFFFFFFFF)
    params.SetUnsigned("BackgroundColor3", 0xFFFFFFFF)
