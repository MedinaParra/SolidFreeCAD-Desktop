from __future__ import annotations

from dataclasses import dataclass

import FreeCAD as App
import Part
import PartDesign  # noqa: F401 - registers Part Design document types
import Sketcher


@dataclass(frozen=True)
class WorkshopModel:
    document: object
    body: object
    sketch: object
    pad: object


def create_workshop_part(
    document_name: str = "WorkshopVerticalSlice",
    *,
    width: float = 100.0,
    height: float = 60.0,
    pad_length: float = 20.0,
) -> WorkshopModel:
    """Create the first production-oriented vertical slice.

    The model intentionally uses only official FreeCAD document objects:
    Body -> fully dimensioned rectangular Sketch -> Pad.
    """

    if width <= 0 or height <= 0 or pad_length <= 0:
        raise ValueError("Workshop model dimensions must be positive")

    if document_name in App.listDocuments():
        App.closeDocument(document_name)

    document = App.newDocument(document_name)
    document.Label = "Pieza de taller"

    body = document.addObject("PartDesign::Body", "Body")
    body.Label = "Pieza"

    sketch = document.addObject("Sketcher::SketchObject", "Sketch")
    sketch.Label = "Croquis base"
    sketch.AttachmentSupport = (document.XY_Plane, [""])
    sketch.MapMode = "FlatFace"
    body.addObject(sketch)

    x0 = -width / 2.0
    x1 = width / 2.0
    y0 = -height / 2.0
    y1 = height / 2.0

    geometry = [
        Part.LineSegment(App.Vector(x0, y0, 0), App.Vector(x1, y0, 0)),
        Part.LineSegment(App.Vector(x1, y0, 0), App.Vector(x1, y1, 0)),
        Part.LineSegment(App.Vector(x1, y1, 0), App.Vector(x0, y1, 0)),
        Part.LineSegment(App.Vector(x0, y1, 0), App.Vector(x0, y0, 0)),
    ]
    sketch.addGeometry(geometry, False)

    for first, second in ((0, 1), (1, 2), (2, 3), (3, 0)):
        sketch.addConstraint(Sketcher.Constraint("Coincident", first, 2, second, 1))

    sketch.addConstraint(Sketcher.Constraint("Horizontal", 0))
    sketch.addConstraint(Sketcher.Constraint("Horizontal", 2))
    sketch.addConstraint(Sketcher.Constraint("Vertical", 1))
    sketch.addConstraint(Sketcher.Constraint("Vertical", 3))

    # Anchor the lower-left corner and expose the two primary dimensions.
    sketch.addConstraint(Sketcher.Constraint("DistanceX", 3, 2, x0))
    sketch.addConstraint(Sketcher.Constraint("DistanceY", 3, 2, y0))
    sketch.addConstraint(Sketcher.Constraint("Distance", 0, width))
    sketch.addConstraint(Sketcher.Constraint("Distance", 1, height))

    document.recompute()

    pad = document.addObject("PartDesign::Pad", "Pad")
    pad.Label = "Extrusión base"
    pad.Profile = sketch
    pad.Length = pad_length
    body.addObject(pad)
    document.recompute()

    expected_volume = width * height * pad_length
    if pad.Shape.isNull() or not pad.Shape.isValid():
        raise RuntimeError("The workshop Pad did not produce a valid solid")
    if abs(pad.Shape.Volume - expected_volume) > max(1e-6, expected_volume * 1e-8):
        raise RuntimeError(
            f"Unexpected Pad volume: {pad.Shape.Volume}, expected {expected_volume}"
        )

    return WorkshopModel(document=document, body=body, sketch=sketch, pad=pad)
