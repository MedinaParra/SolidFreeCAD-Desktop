"""Headless end-to-end validation for the SolidFreeCAD alpha.6 demo part."""
from __future__ import annotations

import os

import FreeCAD as App
import Part

from SolidFreeCAD.DemoPartFeature import create_demo_part

fcstd_path = os.environ.get("SOLIDFREECAD_ALPHA6_FCSTD", "")
step_path = os.environ.get("SOLIDFREECAD_ALPHA6_STEP", "")
if not fcstd_path or not step_path:
    raise SystemExit("SOLIDFREECAD_ALPHA6_FCSTD and SOLIDFREECAD_ALPHA6_STEP are required")

feature = create_demo_part()
doc = feature.Document
initial_volume = feature.Shape.Volume
if feature.Shape.isNull() or not feature.Shape.isValid():
    raise SystemExit("Alpha.6 demo part produced an invalid initial BRep")
if feature.ValidationStatus != "Valid BRep":
    raise SystemExit(f"Unexpected validation status: {feature.ValidationStatus}")

feature.HoleDiameter = 30.0
doc.recompute()
updated_volume = feature.Shape.Volume
if feature.Shape.isNull() or not feature.Shape.isValid():
    raise SystemExit("Edited alpha.6 demo part produced an invalid BRep")
if not updated_volume < initial_volume:
    raise SystemExit(
        f"Parametric edit did not reduce volume: initial={initial_volume}, updated={updated_volume}"
    )

doc.saveAs(fcstd_path)
if not os.path.exists(fcstd_path):
    raise SystemExit("Alpha.6 FCStd file was not saved")
Part.export([feature], step_path)
if not os.path.exists(step_path) or os.path.getsize(step_path) == 0:
    raise SystemExit("Alpha.6 STEP file was not exported")

doc_name = doc.Name
App.closeDocument(doc_name)
reopened = App.openDocument(fcstd_path)
restored = reopened.getObject("Alpha6DemoPlate")
if restored is None:
    raise SystemExit("Alpha.6 demo feature was not restored from FCStd")
reopened.recompute()
if restored.Shape.isNull() or not restored.Shape.isValid():
    raise SystemExit("Reopened alpha.6 BRep is invalid")
if abs(float(restored.HoleDiameter) - 30.0) > 1e-6:
    raise SystemExit(f"Edited parameter was not preserved: {restored.HoleDiameter}")
if restored.ValidationStatus != "Valid BRep":
    raise SystemExit(f"Restored validation status is not valid: {restored.ValidationStatus}")

print(
    "SolidFreeCAD alpha.6 parametric demo validated: "
    f"initial_volume={initial_volume:.3f}, updated_volume={updated_volume:.3f}, "
    f"fcstd={fcstd_path}, step={step_path}"
)
