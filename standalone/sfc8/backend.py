"""Native FreeCAD modelling, transactions and file exchange for SolidFreeCAD.

All features remain native parametric objects. A preview is an open document
transaction: acceptance commits it and cancellation rolls it back completely.
"""
from __future__ import annotations

import math
import os
from contextlib import contextmanager

import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher

from .sketch_geometry import arc_through_points, distance, TOLERANCE

FEATURES = {
    "pad": ("PartDesign::Pad", "Pad", "Saliente/Base"),
    "pocket": ("PartDesign::Pocket", "Pocket", "Corte extruido"),
    "revolution": ("PartDesign::Revolution", "Revolution", "Revolución"),
    "fillet": ("PartDesign::Fillet", "Fillet", "Redondeo"),
    "chamfer": ("PartDesign::Chamfer", "Chamfer", "Chaflán"),
    "linear_pattern": ("PartDesign::LinearPattern", "LinearPattern", "Patrón lineal"),
    "polar_pattern": ("PartDesign::PolarPattern", "PolarPattern", "Patrón circular"),
}
PATTERNS = ("linear_pattern", "polar_pattern")
_editing_sketch = None


def active_document():
    return App.ActiveDocument


def object_by_name(name, doc=None):
    doc = doc or active_document()
    return doc.getObject(name) if doc is not None and name else None


def selected_object():
    selected = Gui.Selection.getSelection()
    return selected[0] if selected else None


def select_object(name):
    obj = object_by_name(name)
    Gui.Selection.clearSelection()
    if obj is not None:
        Gui.Selection.addSelection(obj)
    return obj


@contextmanager
def transaction(doc, label):
    doc.openTransaction(label)
    try:
        yield
        doc.recompute()
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise


def set_object_label(name, label):
    obj = object_by_name(name)
    if obj is not None and label:
        with transaction(obj.Document, "Cambiar nombre"):
            obj.Label = label
    return obj


def set_object_visibility(name, visible):
    obj = object_by_name(name)
    if obj is not None:
        with transaction(obj.Document, "Mostrar / ocultar"):
            obj.Visibility = bool(visible)
    return obj


def remove_object(name):
    obj = object_by_name(name)
    if obj is None:
        return False
    # Never leave dependent parametric features with broken references.
    dependents = [o.Label for o in obj.InList if o.TypeId not in ("PartDesign::Body", "App::Part")]
    if dependents:
        raise ValueError("Primero elimine las operaciones dependientes: " + ", ".join(dependents))
    with transaction(obj.Document, "Eliminar elemento"):
        Gui.Selection.clearSelection()
        obj.Document.removeObject(obj.Name)
    return True


def body_of(obj):
    if obj is None:
        return None
    if obj.TypeId == "PartDesign::Body":
        return obj
    for parent in obj.InList:
        if parent.TypeId == "PartDesign::Body":
            return parent
    return None


def active_body():
    selected = selected_object()
    body = body_of(selected)
    if body is not None:
        return body
    doc = active_document()
    bodies = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"] if doc else []
    if len(bodies) > 1:
        raise ValueError("Seleccione el cuerpo que desea editar en el árbol.")
    return bodies[0] if bodies else None


def active_sketch():
    doc = active_document()
    if doc is None:
        return None
    if _editing_sketch and _editing_sketch[0] == doc.Name:
        return doc.getObject(_editing_sketch[1])
    for obj in Gui.Selection.getSelection():
        if obj.TypeId == "Sketcher::SketchObject":
            return obj
        profile = getattr(obj, "Profile", None)
        if isinstance(profile, tuple):
            profile = profile[0]
        if profile is not None and profile.TypeId == "Sketcher::SketchObject":
            return profile
    # Only use an unconsumed profile in the selected body.
    body = active_body()
    candidates = list(body.Group) if body else doc.Objects
    for obj in reversed(candidates):
        if obj.TypeId == "Sketcher::SketchObject" and not any(
            o.TypeId in {spec[0] for spec in FEATURES.values()} for o in obj.InList
        ):
            return obj
    return None


def ensure_document():
    return active_document() or App.newDocument("SolidFreeCADPart")


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
    doc.UndoMode = 1
    body = doc.addObject("PartDesign::Body", "Body")
    body.Label = "Pieza"
    doc.recompute()
    axonometric_view()
    return doc, body


def selected_planar_face():
    for selection in Gui.Selection.getSelectionEx():
        for name in selection.SubElementNames:
            if name.startswith("Face"):
                face = selection.Object.Shape.getElement(name)
                if not isinstance(face.Surface, Part.Plane):
                    raise ValueError("Seleccione una cara plana para crear el croquis.")
                return selection.Object, name
    return None


def new_sketch(plane="XY", face=None):
    body = body_of(face[0]) if face else ensure_body()
    if body is None:
        raise ValueError("La cara debe pertenecer a un cuerpo Part Design.")
    sketch = body.newObject("Sketcher::SketchObject", "Sketch")
    sketch.Label = "Croquis"
    if face:
        prop = "AttachmentSupport" if "AttachmentSupport" in sketch.PropertiesList else "Support"
        setattr(sketch, prop, (face[0], [face[1]]))
        sketch.MapMode = "FlatFace"
    elif plane == "XZ":
        sketch.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), 90)
    elif plane == "YZ":
        sketch.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 90)
    elif plane != "XY":
        raise ValueError("Plano de croquis desconocido.")
    sketch.Document.recompute()
    select_object(sketch.Name)
    prepare_sketch_view(sketch)
    return sketch


class SketchSession:
    def __init__(self, sketch=None, plane="XY", face=None):
        global _editing_sketch
        if sketch is None:
            ensure_body()
        self.doc = sketch.Document if sketch is not None else active_document()
        self.document_name = self.doc.Name
        self.doc.UndoMode = 1
        self.doc.openTransaction("Editar croquis" if sketch is not None else "Crear croquis")
        self.closed = False
        self.visibility = _visibility(self.doc)
        try:
            self.sketch = sketch if sketch is not None else new_sketch(plane, face)
            if sketch is not None:
                for dependent in sketch.InListRecursive:
                    if dependent.TypeId in {spec[0] for spec in FEATURES.values()}:
                        dependent.Visibility = False
            elif face is None:
                # A reference plane can lie inside the existing solid. Keep its
                # new profile visible; restore the model on accept or cancel.
                for member in body_of(self.sketch).Group:
                    if member != self.sketch and hasattr(member, "Shape"):
                        member.Visibility = False
            self.sketch.Visibility = True
            _editing_sketch = (self.doc.Name, self.sketch.Name)
            prepare_sketch_view(self.sketch)
        except Exception:
            self.cancel()
            raise

    def accept(self):
        global _editing_sketch
        self.doc.recompute()
        if self.sketch.solve() != 0:
            raise ValueError("El croquis contiene restricciones incompatibles.")
        _validate_dependents(self.sketch)
        self.doc.commitTransaction()
        self.closed = True
        _editing_sketch = None
        _restore_visibility(self.doc, self.visibility)
        if not self.visibility.get(self.sketch.Name, True):
            self.sketch.Visibility = False
        return self.sketch

    def cancel(self):
        global _editing_sketch
        if not self.closed and self.document_name in App.listDocuments():
            self.doc.abortTransaction()
            self.doc.recompute()
            _restore_visibility(self.doc, self.visibility)
            self.closed = True
        _editing_sketch = None


def _visibility(doc):
    return {o.Name: bool(o.Visibility) for o in doc.Objects if hasattr(o, "Visibility")}


def _restore_visibility(doc, values):
    for name, visible in values.items():
        obj = doc.getObject(name)
        if obj is not None and hasattr(obj, "Visibility"):
            obj.Visibility = visible


def _valid_number(value, maximum=None):
    value = float(value)
    if not math.isfinite(value) or value <= 1e-7 or (maximum is not None and value > maximum):
        raise ValueError("Introduzca una medida positiva válida.")
    return value


def _append_rectangle(sketch, p0, p1, dimensions=False):
    x0, y0 = map(float, p0)
    x1, y1 = map(float, p1)
    w, h = _valid_number(abs(x1 - x0)), _valid_number(abs(y1 - y0))
    points = [App.Vector(x0, y0, 0), App.Vector(x1, y0, 0), App.Vector(x1, y1, 0), App.Vector(x0, y1, 0)]
    indices = [sketch.addGeometry(Part.LineSegment(points[i], points[(i + 1) % 4]), False) for i in range(4)]
    for i in range(4):
        sketch.addConstraint(Sketcher.Constraint("Coincident", indices[i], 2, indices[(i + 1) % 4], 1))
    for index in (indices[0], indices[2]):
        sketch.addConstraint(Sketcher.Constraint("Horizontal", index))
    for index in (indices[1], indices[3]):
        sketch.addConstraint(Sketcher.Constraint("Vertical", index))
    if dimensions:
        sketch.addConstraint(Sketcher.Constraint("Distance", indices[0], w))
        sketch.addConstraint(Sketcher.Constraint("Distance", indices[1], h))
    sketch.Document.recompute()
    return indices


def add_rectangle(width, height):
    sketch = active_sketch()
    if sketch is None:
        raise ValueError("Abra un croquis antes de dibujar.")
    w, h = _valid_number(width), _valid_number(height)
    _append_rectangle(sketch, (-w / 2, -h / 2), (w / 2, h / 2), dimensions=True)
    fit_view()
    return sketch


def add_rectangle_points(first_point, second_point):
    sketch = active_sketch()
    _append_rectangle(sketch, first_point, second_point)
    return sketch


def _append_circle(sketch, center, radius, dimensions=False):
    radius = _valid_number(radius)
    index = sketch.addGeometry(Part.Circle(App.Vector(*center, 0), App.Vector(0, 0, 1), radius), False)
    if dimensions:
        sketch.addConstraint(Sketcher.Constraint("Radius", index, radius))
    sketch.Document.recompute()
    return index


def add_circle(radius):
    sketch = active_sketch()
    if sketch is None:
        raise ValueError("Abra un croquis antes de dibujar.")
    _append_circle(sketch, (0.0, 0.0), radius, dimensions=True)
    fit_view()
    return sketch


def add_circle_points(center, rim_point):
    sketch = active_sketch()
    _append_circle(sketch, center, math.hypot(rim_point[0] - center[0], rim_point[1] - center[1]))
    return sketch


def add_line_points(first, second):
    _valid_number(distance(first, second))
    sketch = active_sketch()
    if sketch is None:
        raise ValueError("Abra un croquis antes de dibujar.")
    # Snapped endpoints become persistent solver relations, so later dimensions
    # cannot silently open a polyline that initially looked closed.
    references = [_coincident_reference(sketch, p) for p in (first, second)]
    geometry, count = sketch.Geometry, sketch.ConstraintCount
    try:
        index = sketch.addGeometry(Part.LineSegment(App.Vector(*first, 0), App.Vector(*second, 0)), False)
        for position, reference in enumerate(references, 1):
            if reference is not None:
                sketch.addConstraint(Sketcher.Constraint("Coincident", index, position, *reference))
        if abs(first[1] - second[1]) < TOLERANCE:
            sketch.addConstraint(Sketcher.Constraint("Horizontal", index))
        elif abs(first[0] - second[0]) < TOLERANCE:
            sketch.addConstraint(Sketcher.Constraint("Vertical", index))
        if sketch.solve() != 0 or not _sketch_geometry_valid(sketch):
            raise ValueError("La línea produce relaciones redundantes o incompatibles.")
    except Exception:
        while sketch.ConstraintCount > count:
            sketch.delConstraint(sketch.ConstraintCount - 1)
        while sketch.GeometryCount > len(geometry):
            sketch.delGeometry(sketch.GeometryCount - 1)
        sketch.Geometry = geometry
        sketch.solve()
        sketch.Document.recompute()
        raise
    sketch.Document.recompute()
    return sketch, index


def _coincident_reference(sketch, point):
    if distance(point, (0, 0)) <= TOLERANCE:
        return -1, 1
    for index, geometry in enumerate(sketch.Geometry):
        for position, attribute in ((1, "StartPoint"), (2, "EndPoint"), (3, "Center")):
            candidate = getattr(geometry, attribute, None)
            if candidate is not None and distance(point, (candidate.x, candidate.y)) <= TOLERANCE:
                return index, position
    return None


def add_arc_points(start, middle, end):
    arc_through_points(start, middle, end)
    sketch = active_sketch()
    if sketch is None:
        raise ValueError("Abra un croquis antes de dibujar.")
    geometry = Part.Arc(App.Vector(*start, 0), App.Vector(*middle, 0), App.Vector(*end, 0))
    index = sketch.addGeometry(geometry, False)
    sketch.Document.recompute()
    return sketch, index


def add_slot(length, width):
    """A straight obround with native tangent, radius and length constraints."""
    length, width = _valid_number(length), _valid_number(width)
    if length <= width + TOLERANCE:
        raise ValueError("La longitud total de la ranura debe ser mayor que su ancho.")
    sketch = active_sketch()
    if sketch is None:
        raise ValueError("Abra un croquis antes de dibujar.")
    r, half = width / 2, (length - width) / 2
    # Sketcher stores circular arcs counterclockwise about the sketch normal.
    # Trace the whole wire in that direction so endpoint tangencies stay exact.
    p = [App.Vector(half, r, 0), App.Vector(-half, r, 0), App.Vector(-half, -r, 0), App.Vector(half, -r, 0)]
    before_geometry, before_constraints = sketch.GeometryCount, sketch.ConstraintCount
    try:
        indices = sketch.addGeometry([
            Part.LineSegment(p[0], p[1]),
            Part.ArcOfCircle(Part.Circle(App.Vector(-half, 0, 0), App.Vector(0, 0, 1), r), math.pi / 2, 3 * math.pi / 2),
            Part.LineSegment(p[2], p[3]),
            Part.ArcOfCircle(Part.Circle(App.Vector(half, 0, 0), App.Vector(0, 0, 1), r), -math.pi / 2, math.pi / 2),
        ], False)
        for i in range(4):
            sketch.addConstraint(Sketcher.Constraint("Tangent", indices[i], 2, indices[(i + 1) % 4], 1))
        sketch.addConstraint(Sketcher.Constraint("Horizontal", indices[0]))
        sketch.addConstraint(Sketcher.Constraint("Horizontal", indices[2]))
        sketch.addConstraint(Sketcher.Constraint("Radius", indices[1], r))
        sketch.addConstraint(Sketcher.Constraint("Distance", indices[0], length - width))
        if sketch.solve() != 0:
            raise ValueError("No se pudo resolver la geometría de la ranura.")
        sketch.Document.recompute()
    except Exception:
        while sketch.ConstraintCount > before_constraints:
            sketch.delConstraint(sketch.ConstraintCount - 1)
        while sketch.GeometryCount > before_geometry:
            sketch.delGeometry(sketch.GeometryCount - 1)
        sketch.solve()
        sketch.Document.recompute()
        raise
    fit_view()
    return sketch, indices


def geometry_kind(geometry):
    if isinstance(geometry, Part.ArcOfCircle):
        return "Arco"
    if isinstance(geometry, Part.Circle):
        return "Círculo"
    if isinstance(geometry, Part.LineSegment):
        return "Línea"
    return "Geometría"


def nearest_geometry(point, tolerance):
    sketch = active_sketch()
    if sketch is None:
        raise ValueError("Abra un croquis antes de recortar.")
    vertex = Part.Vertex(App.Vector(*point, 0))
    candidates = []
    for index, geometry in enumerate(sketch.Geometry):
        if not sketch.getConstruction(index):
            candidates.append((geometry.toShape().distToShape(vertex)[0], index))
    if not candidates or min(candidates)[0] > tolerance:
        raise ValueError("Seleccione un tramo del croquis para recortar.")
    return min(candidates)[1]


def trim_geometry(index, point):
    sketch = active_sketch()
    if sketch is None or not 0 <= index < sketch.GeometryCount:
        raise ValueError("Seleccione una entidad del croquis activo.")
    sketch.trim(index, App.Vector(*point, 0))
    sketch.Document.recompute()
    return sketch


def _constraint_value(kind, value):
    if kind == "Angle":
        value = float(value)
        if not math.isfinite(value) or not 0 <= value < 360:
            raise ValueError("El ángulo debe estar entre 0° y 360° sin incluir 360°.")
        return value
    if kind in ("Radius", "Diameter", "Distance"):
        value = _valid_number(value)
        return value
    return None


def _set_datum(sketch, index, kind, value):
    unit = "deg" if kind == "Angle" else "mm"
    sketch.setDatum(index, App.Units.Quantity(f"{value} {unit}"))


def _sketch_geometry_valid(sketch):
    # A numerical solution may collapse unconstrained lines to zero length to
    # satisfy contradictory relations. solve() alone does not catch that case.
    try:
        for geometry in sketch.Geometry:
            shape = geometry.toShape()
            if shape.isNull() or not shape.isValid():
                return False
            if isinstance(geometry, (Part.LineSegment, Part.ArcOfCircle, Part.Circle)) and shape.Length <= TOLERANCE:
                return False
    except Exception:
        return False
    return True


def _add_solved_constraint(sketch, constraint):
    geometry, count = sketch.Geometry, sketch.ConstraintCount
    try:
        index = sketch.addConstraint(constraint)
        if sketch.solve() != 0 or not _sketch_geometry_valid(sketch):
            raise ValueError("Restricción redundante, incompatible o con geometría degenerada.")
        sketch.Document.recompute()
        return index
    except Exception:
        while sketch.ConstraintCount > count:
            sketch.delConstraint(sketch.ConstraintCount - 1)
        sketch.Geometry = geometry
        sketch.solve()
        sketch.Document.recompute()
        raise


def constrain_geometry(sketch, index, kind, value=None):
    value = _constraint_value(kind, value)
    # Editing an existing dimension changes its datum instead of adding a conflict.
    for i, constraint in enumerate(sketch.Constraints):
        if constraint.Type == kind and constraint.First == index:
            if value is not None:
                old = math.degrees(constraint.Value) if kind == "Angle" else constraint.Value
                geometry = sketch.Geometry
                try:
                    _set_datum(sketch, i, kind, value)
                    if sketch.solve() != 0 or not _sketch_geometry_valid(sketch):
                        raise ValueError("La cota entra en conflicto con otras restricciones.")
                except Exception:
                    _set_datum(sketch, i, kind, old)
                    sketch.Geometry = geometry
                    sketch.solve()
                    sketch.Document.recompute()
                    raise
            sketch.Document.recompute()
            return i
    native_value = math.radians(value) if kind == "Angle" else value
    args = (kind, index) if value is None else (kind, index, native_value)
    return _add_solved_constraint(sketch, Sketcher.Constraint(*args))


def constrain_pair(sketch, first, second, kind):
    if first is None or second is None or first == second:
        raise ValueError("Seleccione dos entidades distintas.")
    if kind == "Concentric":
        if any(not hasattr(sketch.Geometry[i], "Radius") for i in (first, second)):
            raise ValueError("La concentricidad requiere dos círculos o arcos.")
        constraint = Sketcher.Constraint("Coincident", first, 3, second, 3)
    elif kind in ("Tangent", "Parallel", "Perpendicular", "Equal"):
        constraint = Sketcher.Constraint(kind, first, second)
    else:
        raise ValueError("Relación de dos entidades no admitida.")
    return _add_solved_constraint(sketch, constraint)


def selected_edges():
    source, edges = None, []
    for selection in Gui.Selection.getSelectionEx():
        picked = [n for n in selection.SubElementNames if n.startswith("Edge")]
        if not picked:
            continue
        obj = selection.Object
        if obj.TypeId == "PartDesign::Body":
            obj = obj.Tip
        if source is not None and obj != source:
            raise ValueError("Seleccione aristas de una sola operación.")
        source = obj
        edges.extend(picked)
    if source is None or not edges:
        raise ValueError("Seleccione una o más aristas del sólido con Ctrl + clic.")
    return source, list(dict.fromkeys(edges))


def selected_pattern_source():
    source = selected_object()
    if source is not None and source.TypeId == "PartDesign::Body":
        source = source.Tip
    if source is None or source.TypeId not in ("PartDesign::Pad", "PartDesign::Pocket", "PartDesign::Revolution"):
        raise ValueError("Seleccione en el árbol un Saliente, Corte o Revolución para repetir.")
    return source


def body_axis_reference(body, name):
    if name not in ("X", "Y", "Z"):
        raise ValueError("Seleccione el eje X, Y o Z del cuerpo.")
    axis = next((o for o in body.Origin.OriginFeatures if getattr(o, "Role", "") == name + "_Axis"), None)
    if axis is None:
        raise ValueError("No se encontró el eje del cuerpo.")
    return axis, [""]


def _validate_pattern_instances(feature, kind, value, count, axis, reverse):
    """Native cuts can silently skip copies outside the support solid."""
    direction = {"X": App.Vector(1, 0, 0), "Y": App.Vector(0, 1, 0), "Z": App.Vector(0, 0, 1)}[axis]
    sign = -1 if reverse else 1
    for source in feature.Originals:
        tool = source.AddSubShape.copy()
        tool.transformShape((feature.Placement.inverse() * source.Placement).toMatrix())
        tolerance = max(1e-7, tool.Volume * 1e-7)
        support = None
        if source.TypeId == "PartDesign::Pocket":
            # Restore the original removed material to the current support, so
            # overlapping copies are allowed but copies in empty space are not.
            removed = source.BaseFeature.Shape.cut(source.Shape)
            removed.transformShape((feature.Placement.inverse() * source.Placement).toMatrix())
            support = feature.BaseFeature.Shape.fuse(removed)
        for occurrence in range(1, count):
            copy = tool.copy()
            if kind == "linear_pattern":
                copy.translate(direction * (sign * value * occurrence))
            else:
                step = value / (count if math.isclose(value, 360, abs_tol=1e-7) else count - 1)
                copy.rotate(App.Vector(), direction, sign * step * occurrence)
            if support is not None:
                missing = copy.common(support).Volume <= tolerance
            else:
                missing = copy.cut(feature.Shape).Volume > tolerance
            if missing:
                raise ValueError(f"La instancia {occurrence + 1} no se puede aplicar al cuerpo. Revise separación, eje o dirección.")


def _validate_dependents(obj):
    for dependent in obj.InListRecursive:
        if dependent.TypeId not in {spec[0] for spec in FEATURES.values()}:
            continue
        if "Invalid" in dependent.State:
            raise ValueError("La modificación invalida una operación posterior: " + dependent.Label)
        kind = next((k for k in PATTERNS if FEATURES[k][0] == dependent.TypeId), None)
        if kind is None or str(dependent.TransformMode) != "Features" or str(dependent.Mode) != "Extent":
            continue
        reference = getattr(dependent, "Direction" if kind == "linear_pattern" else "Axis")
        role = getattr(reference[0], "Role", "") if reference and reference[0] is not None else ""
        if role not in ("X_Axis", "Y_Axis", "Z_Axis") or len(dependent.Originals) != 1:
            continue
        if dependent.Originals[0].TypeId not in ("PartDesign::Pad", "PartDesign::Pocket", "PartDesign::Revolution"):
            continue
        second = getattr(dependent, "Direction2", None)
        if second and second[0] is not None:
            continue
        count = int(dependent.Occurrences)
        if not 2 <= count <= 100:
            continue
        value = float(dependent.Length) / (count - 1) if kind == "linear_pattern" else float(dependent.Angle)
        try:
            _validate_pattern_instances(dependent, kind, value, count, role[0], bool(dependent.Reversed))
        except ValueError as exc:
            raise ValueError(dependent.Label + ": " + str(exc)) from exc


class FeatureSession:
    """One reversible native feature, including its debounced live preview."""
    def __init__(self, kind, profile=None, edge_selection=None, feature=None, pattern_source=None):
        if kind not in FEATURES:
            raise ValueError("Operación desconocida.")
        self.kind = kind
        self.editing = feature is not None
        reference = feature or pattern_source or profile or (edge_selection[0] if edge_selection else None)
        if reference is None or body_of(reference) is None:
            raise ValueError("Seleccione un perfil o sólido dentro de un cuerpo Part Design.")
        if kind in PATTERNS:
            originals = feature.Originals if feature is not None else [pattern_source]
            if len(originals) != 1 or originals[0] is None or originals[0].TypeId not in ("PartDesign::Pad", "PartDesign::Pocket", "PartDesign::Revolution"):
                raise ValueError("Esta versión repite una operación Saliente, Corte o Revolución.")
            if feature is not None:
                direction = getattr(feature, "Direction" if kind == "linear_pattern" else "Axis")
                native_axes = body_of(feature).Origin.OriginFeatures
                second = getattr(feature, "Direction2", None)
                if (str(feature.Mode) != "Extent" or str(feature.TransformMode) != "Features"
                        or direction[0] not in native_axes or (second and second[0] is not None)
                        or not 2 <= int(feature.Occurrences) <= 100):
                    raise ValueError("Edición disponible para patrones de una dirección, 2–100 instancias, modo Extensión y eje X/Y/Z del cuerpo.")
        self.doc = reference.Document
        self.document_name = self.doc.Name
        self.body = body_of(reference)
        self.visibility = _visibility(self.doc)
        self.old_tip = self.body.Tip
        self.closed = False
        self.valid = False
        self.error = "Defina los parámetros de la operación."
        self.doc.UndoMode = 1
        self.doc.openTransaction("Editar " + FEATURES[kind][2] if feature is not None else "Crear " + FEATURES[kind][2])
        try:
            self.feature = feature if feature is not None else self.body.newObject(FEATURES[kind][0], FEATURES[kind][1])
            if feature is None:
                self.feature.Label = FEATURES[kind][2]
                if profile is not None:
                    self.feature.Profile = profile
                if edge_selection:
                    self.feature.Base = (edge_selection[0], edge_selection[1])
                if pattern_source is not None:
                    self.feature.TransformMode = "Features"
                    self.feature.Originals = [pattern_source]
                    if kind == "linear_pattern":
                        self.feature.Occurrences = 3
                        self.feature.Length = 40
                    else:
                        self.feature.Occurrences = 6
                        self.feature.Angle = 360
            if "Refine" in self.feature.PropertiesList:
                self.feature.Refine = True
            if profile is not None:
                profile.Visibility = False
            if self.old_tip is not None and self.old_tip != self.feature:
                self.old_tip.Visibility = False
            self.body.Tip = self.feature if feature is None else self.old_tip
            self.feature.Visibility = True
        except Exception:
            self.cancel()
            raise

    def update(self, value=20.0, reverse=False, symmetric=False, through=False, axis="V_Axis", preview=True, count=3, pattern_axis="X"):
        try:
            value = _valid_number(value, 360 if self.kind in ("revolution", "polar_pattern") else None)
            obj = self.feature
            if self.kind in ("pad", "pocket"):
                obj.Type = "ThroughAll" if self.kind == "pocket" and through else "Length"
                obj.Length = value
                obj.Reversed = reverse
                _set_symmetric(obj, symmetric)
            elif self.kind == "revolution":
                obj.Angle = value
                obj.ReferenceAxis = (obj.Profile[0] if isinstance(obj.Profile, tuple) else obj.Profile, [axis])
                obj.Reversed = reverse
                _set_symmetric(obj, symmetric)
            elif self.kind == "fillet":
                obj.Radius = value
            elif self.kind == "chamfer":
                obj.Size = value
            elif self.kind in PATTERNS:
                if int(count) != count or not 2 <= count <= 100:
                    raise ValueError("El patrón admite entre 2 y 100 instancias, incluida la original.")
                obj.Mode = "Extent"
                obj.Occurrences = int(count)
                obj.Reversed = reverse
                reference = body_axis_reference(self.body, pattern_axis)
                if self.kind == "linear_pattern":
                    obj.Direction = reference
                    obj.Length = value * (int(count) - 1)
                else:
                    obj.Axis = reference
                    obj.Angle = value
            self.doc.recompute()
            shape = obj.Shape
            states = list(obj.State)
            self.valid = not shape.isNull() and shape.isValid() and len(shape.Solids) == 1 and "Invalid" not in states
            if not self.valid:
                raise ValueError("La operación no genera un sólido válido. Revise perfil, dirección, intersección o medida.")
            if self.kind in PATTERNS:
                _validate_pattern_instances(obj, self.kind, value, int(count), pattern_axis, reverse)
            _validate_dependents(obj)
            self.error = ""
        except Exception as exc:
            self.valid = False
            self.error = str(exc)
        self.feature.Visibility = bool(preview and self.valid)
        # Invalid or disabled previews must not leave stale geometry visible.
        if self.old_tip is not None and self.old_tip != self.feature:
            self.old_tip.Visibility = not (preview and self.valid)
        return self.valid

    def accept(self):
        if not self.valid:
            raise ValueError(self.error)
        if self.editing:
            _restore_visibility(self.doc, self.visibility)
        else:
            self.feature.Visibility = True
            if self.old_tip is not None and self.old_tip != self.feature:
                self.old_tip.Visibility = False
        self.doc.commitTransaction()
        self.closed = True
        select_object(self.feature.Name)
        return self.feature

    def cancel(self):
        if not self.closed and self.document_name in App.listDocuments():
            self.doc.abortTransaction()
            self.doc.recompute()
            _restore_visibility(self.doc, self.visibility)
            self.closed = True


def _set_symmetric(obj, enabled):
    if "SideType" in obj.PropertiesList:
        obj.SideType = "Symmetric" if enabled else "One side"
    elif "Midplane" in obj.PropertiesList:
        obj.Midplane = enabled


def pad_sketch(length):
    session = FeatureSession("pad", profile=active_sketch())
    try:
        session.update(length)
        return session.accept()
    except Exception:
        session.cancel()
        raise


def open_document(path):
    if path.lower().endswith(".fcstd"):
        doc = App.openDocument(path)
    else:
        import Import
        doc = App.newDocument("ImportedPart")
        doc.Label = os.path.splitext(os.path.basename(path))[0]
        try:
            Import.insert(path, doc.Name)
        except Exception:
            App.closeDocument(doc.Name)
            raise
    doc.UndoMode = 1
    axonometric_view()
    fit_view()
    return doc


def save_document(path=None):
    doc = active_document()
    if doc is None:
        raise ValueError("No hay un documento activo.")
    if path:
        doc.saveAs(path)
    elif doc.FileName:
        doc.save()
    else:
        raise ValueError("Seleccione un nombre de archivo.")
    return doc


def export_step(path):
    import Import
    doc = active_document()
    if doc is None:
        raise ValueError("No hay un documento activo.")
    objects = [o for o in doc.Objects if o.TypeId == "PartDesign::Body" and o.Tip is not None]
    objects.extend(o for o in doc.Objects if hasattr(o, "Shape") and o.Visibility and body_of(o) is None and not o.Shape.isNull())
    if not objects:
        raise ValueError("El documento no contiene sólidos para exportar.")
    Import.export(objects, path)


def _view():
    return Gui.activeDocument().activeView() if Gui.activeDocument() else None


def axonometric_view():
    if _view():
        _view().viewAxonometric()


def front_view():
    if _view():
        _view().viewFront()


def top_view():
    if _view():
        _view().viewTop()


def fit_view():
    if _view():
        _view().fitAll()


def prepare_sketch_view(sketch=None):
    sketch = sketch or active_sketch()
    if _view() and sketch is not None:
        _view().setCameraOrientation(sketch.getGlobalPlacement().Rotation.Q)


def pointer_in_sketch(point, sketch=None):
    sketch = sketch or active_sketch()
    local = sketch.getGlobalPlacement().inverse().multVec(point)
    return float(local.x), float(local.y)


def set_light_background():
    params = App.ParamGet("User parameter:BaseApp/Preferences/View")
    params.SetBool("Simple", False)
    params.SetBool("UseBackgroundColorMid", False)
    params.SetUnsigned("BackgroundColor", 0xDCE4EDFF)
    params.SetUnsigned("BackgroundColor2", 0xFAFBFDFF)
    params.SetUnsigned("SelectionColor", 0xF59C32FF)
