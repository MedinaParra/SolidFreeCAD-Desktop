"""Headless validation of the classic native piece workflow."""
from __future__ import annotations

import os

import FreeCAD as App

output = os.environ.get("SOLIDFREECAD_CLASSIC_SMOKE_FCSTD", "")
if not output:
    raise SystemExit("SOLIDFREECAD_CLASSIC_SMOKE_FCSTD is required")

# The graphical New Part command delegates to this same native document model.
doc = App.newDocument("ClassicWorkflowSmoke")
body = doc.addObject("PartDesign::Body", "Body")
body.Label = "Pieza de prueba"
doc.recompute()

if body.TypeId != "PartDesign::Body":
    raise SystemExit(f"Unexpected body TypeId: {body.TypeId}")
if doc.getObject("Body") is not body:
    raise SystemExit("Native Body was not registered in the document")

# Add a simple native feature so the FCStd contains actual geometry.
feature = body.newObject("PartDesign::Feature", "ClassicBaseFeature")
import Part
feature.Shape = Part.makeBox(40.0, 30.0, 12.0)
feature.Label = "Saliente base de prueba"
doc.recompute()

if feature.Shape.isNull() or not feature.Shape.isValid():
    raise SystemExit("Classic base feature produced an invalid shape")
if abs(feature.Shape.Volume - 14400.0) > 1e-6:
    raise SystemExit(f"Unexpected feature volume: {feature.Shape.Volume}")

doc.saveAs(output)
if not os.path.exists(output):
    raise SystemExit("Classic workflow FCStd was not saved")

App.closeDocument(doc.Name)
reopened = App.openDocument(output)
reopened_feature = reopened.getObject("ClassicBaseFeature")
if reopened_feature is None or reopened_feature.Shape.isNull():
    raise SystemExit("Saved classic feature could not be reopened")
if not reopened_feature.Shape.isValid():
    raise SystemExit("Reopened classic feature is invalid")

print(f"Classic native piece workflow validated: {output}")
