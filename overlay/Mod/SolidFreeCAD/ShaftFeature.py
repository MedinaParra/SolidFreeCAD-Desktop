"""Parametric mechanical shaft feature for SolidFreeCAD."""

from __future__ import annotations

import FreeCAD as App
import Part


FEATURE_KIND = "SteppedShaft"


class ShaftProxy:
    """Creates a two-diameter stepped shaft aligned to the global X axis."""

    def __init__(self, obj):
        obj.addProperty(
            "App::PropertyString",
            "SolidFreeCADFeature",
            "SolidFreeCAD",
            "Internal SolidFreeCAD feature identifier.",
        )
        obj.setEditorMode("SolidFreeCADFeature", 1)
        obj.SolidFreeCADFeature = FEATURE_KIND

        obj.addProperty(
            "App::PropertyLength",
            "MainLength",
            "Shaft",
            "Length of the main cylindrical section.",
        )
        obj.addProperty(
            "App::PropertyLength",
            "MainDiameter",
            "Shaft",
            "Diameter of the main cylindrical section.",
        )
        obj.addProperty(
            "App::PropertyLength",
            "ShoulderLength",
            "Shaft",
            "Length of the larger shoulder section.",
        )
        obj.addProperty(
            "App::PropertyLength",
            "ShoulderDiameter",
            "Shaft",
            "Diameter of the larger shoulder section.",
        )
        obj.addProperty(
            "App::PropertyBool",
            "AddKeyway",
            "Keyway",
            "Cut a rectangular keyway in the main section.",
        )
        obj.addProperty(
            "App::PropertyLength",
            "KeywayWidth",
            "Keyway",
            "Keyway width.",
        )
        obj.addProperty(
            "App::PropertyLength",
            "KeywayDepth",
            "Keyway",
            "Radial keyway depth.",
        )
        obj.addProperty(
            "App::PropertyLength",
            "KeywayLength",
            "Keyway",
            "Keyway length measured along the shaft axis.",
        )
        obj.addProperty(
            "App::PropertyLength",
            "KeywayOffset",
            "Keyway",
            "Distance from the start of the main section.",
        )

        obj.MainLength = 160.0
        obj.MainDiameter = 60.0
        obj.ShoulderLength = 40.0
        obj.ShoulderDiameter = 85.0
        obj.AddKeyway = True
        obj.KeywayWidth = 18.0
        obj.KeywayDepth = 6.0
        obj.KeywayLength = 70.0
        obj.KeywayOffset = 55.0
        obj.Proxy = self

    def execute(self, obj):
        main_length = max(float(obj.MainLength), 0.1)
        main_diameter = max(float(obj.MainDiameter), 0.1)
        shoulder_length = max(float(obj.ShoulderLength), 0.0)
        shoulder_diameter = max(float(obj.ShoulderDiameter), main_diameter)

        axis = App.Vector(1.0, 0.0, 0.0)
        main = Part.makeCylinder(main_diameter / 2.0, main_length, App.Vector(), axis)
        shape = main

        if shoulder_length > 0.0:
            shoulder = Part.makeCylinder(
                shoulder_diameter / 2.0,
                shoulder_length,
                App.Vector(main_length, 0.0, 0.0),
                axis,
            )
            shape = shape.fuse(shoulder)

        if bool(obj.AddKeyway):
            width = min(max(float(obj.KeywayWidth), 0.1), main_diameter * 0.9)
            depth = min(max(float(obj.KeywayDepth), 0.1), main_diameter * 0.45)
            length = min(max(float(obj.KeywayLength), 0.1), main_length)
            offset = min(max(float(obj.KeywayOffset), 0.0), main_length - length)
            radius = main_diameter / 2.0

            keyway = Part.makeBox(
                length,
                width,
                depth,
                App.Vector(offset, -width / 2.0, radius - depth),
            )
            shape = shape.cut(keyway)

        obj.Shape = shape.removeSplitter()

    def onDocumentRestored(self, obj):
        obj.Proxy = self
        if "SolidFreeCADFeature" not in obj.PropertiesList:
            obj.addProperty(
                "App::PropertyString",
                "SolidFreeCADFeature",
                "SolidFreeCAD",
                "Internal SolidFreeCAD feature identifier.",
            )
        obj.SolidFreeCADFeature = FEATURE_KIND
        obj.setEditorMode("SolidFreeCADFeature", 1)


def is_shaft(obj):
    """Return True when *obj* is a SolidFreeCAD stepped shaft."""

    return bool(
        obj
        and "SolidFreeCADFeature" in getattr(obj, "PropertiesList", [])
        and obj.SolidFreeCADFeature == FEATURE_KIND
    )


def create_shaft(document=None, name="SolidFreeCADShaft"):
    """Create and recompute a default editable shaft feature."""

    doc = document or App.ActiveDocument or App.newDocument("SolidFreeCADPart")
    obj = doc.addObject("Part::FeaturePython", name)
    obj.Label = "Eje paramétrico"
    ShaftProxy(obj)
    doc.recompute()
    return obj
