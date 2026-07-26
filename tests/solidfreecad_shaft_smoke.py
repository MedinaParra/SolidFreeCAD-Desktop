"""Headless runtime validation for the SolidFreeCAD shaft feature."""

from __future__ import annotations

import os

import FreeCAD as App

from SolidFreeCAD.ShaftFeature import create_shaft


def assert_valid_solid(obj, stage):
    shape = obj.Shape
    if shape.isNull():
        raise RuntimeError(f"{stage}: shaft shape is null")
    if not shape.isValid():
        raise RuntimeError(f"{stage}: shaft shape is invalid")
    if len(shape.Solids) != 1:
        raise RuntimeError(f"{stage}: expected one solid, got {len(shape.Solids)}")
    if shape.Volume <= 0.0:
        raise RuntimeError(f"{stage}: shaft has no volume")


doc = App.newDocument("SolidFreeCADShaftSmoke")
shaft = create_shaft(doc)
assert_valid_solid(shaft, "default")
initial_volume = shaft.Shape.Volume

shaft.MainLength = 220.0
shaft.MainDiameter = 70.0
shaft.ShoulderLength = 55.0
shaft.ShoulderDiameter = 105.0
shaft.KeywayWidth = 20.0
shaft.KeywayDepth = 7.0
shaft.KeywayLength = 90.0
shaft.KeywayOffset = 60.0
doc.recompute()
assert_valid_solid(shaft, "resized-with-keyway")

if shaft.Shape.Volume <= initial_volume:
    raise RuntimeError("Resized shaft volume did not increase as expected")

shaft.AddKeyway = False
doc.recompute()
assert_valid_solid(shaft, "without-keyway")

output = os.environ.get("SOLIDFREECAD_SMOKE_FCSTD")
if output:
    doc.saveAs(output)

print(
    "SolidFreeCAD shaft smoke test passed: "
    f"volume={shaft.Shape.Volume:.3f} mm^3, faces={len(shaft.Shape.Faces)}"
)

App.closeDocument(doc.Name)
