"""Parametric alpha.6 demonstration part for end-to-end validation."""
from __future__ import annotations

import FreeCAD as App
import Part


FEATURE_KIND = "Alpha6DemoPlate"


class DemoPlateProxy:
    """Build a plate with a through-hole and a rectangular pocket."""

    def __init__(self, obj):
        self._ensure_properties(obj)
        obj.Proxy = self

    @staticmethod
    def _ensure_properties(obj):
        definitions = (
            ("App::PropertyString", "SolidFreeCADFeature", "SolidFreeCAD", "Internal feature identifier"),
            ("App::PropertyLink", "DesignBody", "SolidFreeCAD", "Associated Part Design Body"),
            ("App::PropertyLength", "Length", "Dimensions", "Overall plate length"),
            ("App::PropertyLength", "Width", "Dimensions", "Overall plate width"),
            ("App::PropertyLength", "Thickness", "Dimensions", "Plate thickness"),
            ("App::PropertyLength", "HoleDiameter", "Features", "Through-hole diameter"),
            ("App::PropertyLength", "PocketLength", "Features", "Pocket length"),
            ("App::PropertyLength", "PocketWidth", "Features", "Pocket width"),
            ("App::PropertyLength", "PocketDepth", "Features", "Pocket depth"),
            ("App::PropertyString", "ValidationStatus", "Validation", "Last geometry validation result"),
        )
        for type_name, name, group, description in definitions:
            if name not in obj.PropertiesList:
                obj.addProperty(type_name, name, group, description)

        obj.SolidFreeCADFeature = FEATURE_KIND
        obj.setEditorMode("SolidFreeCADFeature", 1)
        defaults = {
            "Length": 120.0,
            "Width": 80.0,
            "Thickness": 16.0,
            "HoleDiameter": 22.0,
            "PocketLength": 46.0,
            "PocketWidth": 24.0,
            "PocketDepth": 6.0,
        }
        for name, value in defaults.items():
            if float(getattr(obj, name)) <= 0.0:
                setattr(obj, name, value)
        if not obj.ValidationStatus:
            obj.ValidationStatus = "Pending recompute"

    def execute(self, obj):
        length = max(float(obj.Length), 10.0)
        width = max(float(obj.Width), 10.0)
        thickness = max(float(obj.Thickness), 2.0)
        hole_diameter = min(max(float(obj.HoleDiameter), 1.0), min(length, width) * 0.75)
        pocket_length = min(max(float(obj.PocketLength), 1.0), length * 0.8)
        pocket_width = min(max(float(obj.PocketWidth), 1.0), width * 0.8)
        pocket_depth = min(max(float(obj.PocketDepth), 0.1), thickness * 0.9)

        base = Part.makeBox(length, width, thickness)
        hole = Part.makeCylinder(
            hole_diameter / 2.0,
            thickness + 2.0,
            App.Vector(length / 2.0, width / 2.0, -1.0),
        )
        shape = base.cut(hole)

        pocket_x = (length - pocket_length) / 2.0
        pocket_y = (width - pocket_width) / 2.0
        pocket = Part.makeBox(
            pocket_length,
            pocket_width,
            pocket_depth + 1.0,
            App.Vector(pocket_x, pocket_y, thickness - pocket_depth),
        )
        shape = shape.cut(pocket).removeSplitter()

        obj.Shape = shape
        obj.ValidationStatus = "Valid BRep" if shape.isValid() and not shape.isNull() else "Invalid BRep"

    def onDocumentRestored(self, obj):
        self._ensure_properties(obj)
        obj.Proxy = self


def create_demo_part(document=None):
    """Create a native FCStd document, Body and persistent parametric feature."""
    doc = document or App.ActiveDocument or App.newDocument("SolidFreeCADAlpha6Demo")
    body = doc.getObject("Body")
    if body is None:
        body = doc.addObject("PartDesign::Body", "Body")
        body.Label = "Pieza demostrativa"

    feature = doc.getObject("Alpha6DemoPlate")
    if feature is None:
        # Part::FeaturePython is the persistence pattern already validated by the
        # SolidFreeCAD shaft feature. The native Body remains available for the
        # sketch/Part Design workflow and is explicitly linked to this feature.
        feature = doc.addObject("Part::FeaturePython", "Alpha6DemoPlate")
        feature.Label = "Placa paramétrica alpha.6"
        DemoPlateProxy(feature)
        feature.DesignBody = body
    elif not isinstance(getattr(feature, "Proxy", None), DemoPlateProxy):
        DemoPlateProxy(feature)
        feature.DesignBody = body

    doc.recompute()
    return feature
