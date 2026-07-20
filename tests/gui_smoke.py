from __future__ import annotations

import os
from pathlib import Path

import FreeCADGui
from PySide import QtCore, QtWidgets


expect_classic = os.environ.get("SOLIDFREECAD_EXPECT_CLASSIC") == "1"

main_window = FreeCADGui.getMainWindow()
if main_window is None:
    raise RuntimeError("FreeCAD main window is not available")

main_window.resize(1440, 900)
main_window.show()

application = QtWidgets.QApplication.instance()
if application is None:
    raise RuntimeError("Qt application is not available")
application.processEvents()

ribbon = main_window.findChild(QtWidgets.QToolBar, "SolidFreeCADRibbon")
command_search = main_window.findChild(QtWidgets.QLineEdit, "SolidFreeCADCommandSearch")

if expect_classic:
    if ribbon is not None:
        raise RuntimeError("SolidFreeCADRibbon must not be installed in Classic mode")
    if command_search is not None:
        raise RuntimeError("SolidFreeCADCommandSearch must not be installed in Classic mode")

    print("SOLIDFREECAD_CLASSIC_SMOKE_OK")
    QtCore.QTimer.singleShot(0, application.quit)
else:
    if ribbon is None:
        raise RuntimeError("SolidFreeCADRibbon was not installed")
    if not ribbon.isVisible():
        raise RuntimeError("SolidFreeCADRibbon is not visible")
    if command_search is None:
        raise RuntimeError("SolidFreeCADCommandSearch was not installed")

    native_action_names = {
        action.objectName()
        for action in ribbon.actions()
        if action.objectName()
    }
    required_commands = {
        "Std_New",
        "Std_Open",
        "Std_Save",
        "Std_Undo",
        "Std_Redo",
        "Std_ViewFitAll",
        "Std_ViewIsometric",
    }
    missing = required_commands.difference(native_action_names)
    if missing:
        raise RuntimeError(f"Missing native ribbon commands: {sorted(missing)}")

    completer = command_search.completer()
    if completer is None or completer.model() is None:
        raise RuntimeError("Command search completer is not available")
    if completer.model().rowCount() == 0:
        raise RuntimeError("Command search catalogue is empty")

    screenshot_path = Path(
        os.environ.get("SOLIDFREECAD_SCREENSHOT", "solidfreecad-bootstrap.png")
    ).resolve()
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    if not main_window.grab().save(str(screenshot_path)):
        raise RuntimeError(f"Could not save screenshot to {screenshot_path}")

    print(f"SOLIDFREECAD_GUI_SMOKE_OK screenshot={screenshot_path}")
    QtCore.QTimer.singleShot(0, application.quit)
