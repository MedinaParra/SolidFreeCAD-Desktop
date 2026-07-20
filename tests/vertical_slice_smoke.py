from __future__ import annotations

import os
import sys
from pathlib import Path

import FreeCAD as App
import FreeCADGui
from PySide import QtCore, QtWidgets


TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from workshop_model import create_workshop_part  # noqa: E402


artifact_path = Path(
    os.environ.get("SOLIDFREECAD_VERTICAL_SLICE", "workshop-vertical-slice.FCStd")
).resolve()
artifact_path.parent.mkdir(parents=True, exist_ok=True)

model = create_workshop_part()
model.document.saveAs(str(artifact_path))

expected_volume = float(model.pad.Shape.Volume)
App.closeDocument(model.document.Name)

reopened = App.openDocument(str(artifact_path))
if reopened is None:
    raise RuntimeError("The vertical-slice FCStd file could not be reopened")

body = reopened.getObject("Body")
sketch = reopened.getObject("Sketch")
pad = reopened.getObject("Pad")

if body is None or body.TypeId != "PartDesign::Body":
    raise RuntimeError("Reopened document is missing the Part Design Body")
if sketch is None or sketch.TypeId != "Sketcher::SketchObject":
    raise RuntimeError("Reopened document is missing the base Sketch")
if pad is None or pad.TypeId != "PartDesign::Pad":
    raise RuntimeError("Reopened document is missing the Pad")

reopened.recompute()
if pad.Shape.isNull() or not pad.Shape.isValid():
    raise RuntimeError("Reopened Pad is not a valid solid")
if abs(float(pad.Shape.Volume) - expected_volume) > max(1e-6, expected_volume * 1e-8):
    raise RuntimeError("Reopened Pad volume changed after FCStd persistence")

print(
    "SOLIDFREECAD_VERTICAL_SLICE_OK "
    f"path={artifact_path} volume_mm3={pad.Shape.Volume:.3f}"
)

application = QtWidgets.QApplication.instance()
if application is not None:
    QtCore.QTimer.singleShot(0, application.quit)
