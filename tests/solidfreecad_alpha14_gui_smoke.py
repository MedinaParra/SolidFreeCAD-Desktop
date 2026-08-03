"""Manual GUI contract smoke test for SolidFreeCAD alpha.14."""
from __future__ import annotations

import FreeCADGui as Gui
from PySide import QtWidgets

from SolidFreeCAD.InteractiveAcceptanceWorkspace import _DEFINITIONS, show_workspace


main = Gui.getMainWindow()
show_workspace()
QtWidgets.QApplication.processEvents()

requirements = (
    (QtWidgets.QDockWidget, "SolidFreeCADClassicCommandManager"),
    (QtWidgets.QDockWidget, "SolidFreeCADFeatureManager"),
    (QtWidgets.QWidget, "SolidFreeCADAlpha12PreflightPage"),
    (QtWidgets.QWidget, "SolidFreeCADAlpha13StabilityPage"),
    (QtWidgets.QWidget, "SolidFreeCADAlpha14AcceptancePage"),
    (QtWidgets.QTreeWidget, "SolidFreeCADAlpha14AcceptanceTree"),
    (QtWidgets.QPushButton, "SolidFreeCADAlpha14Start"),
    (QtWidgets.QPushButton, "SolidFreeCADAlpha14Capture"),
)

missing = []
duplicated = []
for widget_type, name in requirements:
    matches = main.findChildren(widget_type, name)
    if not matches:
        missing.append(name)
    elif len(matches) > 1:
        duplicated.append(f"{name}:{len(matches)}")

keys = [definition.key for definition in _DEFINITIONS]
if len(keys) != len(set(keys)):
    raise RuntimeError("alpha14 acceptance step keys are not unique")
if len(keys) < 16:
    raise RuntimeError("alpha14 acceptance gate is incomplete")
if missing or duplicated:
    raise RuntimeError(
        "alpha14 GUI contract failed; missing=" + repr(missing) + "; duplicated=" + repr(duplicated)
    )

print("PASS alpha14 interactive acceptance GUI contract")
