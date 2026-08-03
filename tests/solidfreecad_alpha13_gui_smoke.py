"""Manual GUI contract smoke test for SolidFreeCAD alpha.13.

Run inside a FreeCAD GUI runtime after activating the SolidFreeCAD workbench.
No files are packaged or uploaded by this script.
"""
from __future__ import annotations

import FreeCADGui as Gui
from PySide import QtWidgets

from SolidFreeCAD.RuntimeStabilityWorkspace import RuntimeStabilityRunner, show_workspace


main = Gui.getMainWindow()
show_workspace()
QtWidgets.QApplication.processEvents()

requirements = (
    (QtWidgets.QDockWidget, "SolidFreeCADClassicCommandManager"),
    (QtWidgets.QDockWidget, "SolidFreeCADFeatureManager"),
    (QtWidgets.QDockWidget, "SolidFreeCADAlpha7TaskPane"),
    (QtWidgets.QToolBar, "SolidFreeCADAlpha7ContextBar"),
    (QtWidgets.QToolBar, "SolidFreeCADAlpha11QuickAccess"),
    (QtWidgets.QWidget, "SolidFreeCADAlpha12PreflightPage"),
    (QtWidgets.QWidget, "SolidFreeCADAlpha13StabilityPage"),
    (QtWidgets.QTreeWidget, "SolidFreeCADAlpha13StabilityTree"),
    (QtWidgets.QPushButton, "SolidFreeCADAlpha13Run"),
)

missing = []
duplicated = []
for widget_type, name in requirements:
    matches = main.findChildren(widget_type, name)
    if not matches:
        missing.append(name)
    elif len(matches) > 1:
        duplicated.append(f"{name}:{len(matches)}")

if missing or duplicated:
    raise RuntimeError(
        "alpha13 GUI contract failed; missing=" + repr(missing) + "; duplicated=" + repr(duplicated)
    )

runner = RuntimeStabilityRunner(main)
if runner.MINIMUM_RUNTIME != (1, 1, 3):
    raise RuntimeError("alpha13 must require the maintained FreeCAD 1.1.3 baseline")

print("PASS alpha13 GUI contract")
