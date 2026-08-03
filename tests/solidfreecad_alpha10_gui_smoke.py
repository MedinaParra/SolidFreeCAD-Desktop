"""Manual graphical contract test for SolidFreeCAD alpha.10."""
from __future__ import annotations

import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets


def finish(success: bool, message: str):
    printer = App.Console.PrintMessage if success else App.Console.PrintError
    printer(("PASS: " if success else "FAIL: ") + message + "\n")


def run():
    try:
        from SolidFreeCAD.FeatureBindingWorkspace import show_workspace

        show_workspace()
        main = Gui.getMainWindow()
        required = {
            "operation page": main.findChild(QtWidgets.QWidget, "SolidFreeCADAlpha8OperationPage"),
            "binding panel": main.findChild(QtWidgets.QGroupBox, "SolidFreeCADAlpha10BindingPanel"),
            "end condition": main.findChild(QtWidgets.QGroupBox, "SolidFreeCADAlpha10EndCondition"),
            "selection list": main.findChild(QtWidgets.QListWidget, "SolidFreeCADAlpha10BindingList"),
            "readiness": main.findChild(QtWidgets.QLabel, "SolidFreeCADAlpha10Readiness"),
        }
        missing = [name for name, widget in required.items() if widget is None]
        if missing:
            raise RuntimeError("Missing alpha.10 widgets: " + ", ".join(missing))
        if "FeatureBindingWorkspaceCompat" not in open(
            __import__("SolidFreeCAD.Workbench", fromlist=["__file__"]).__file__,
            encoding="utf-8",
        ).read():
            raise RuntimeError("Workbench does not use alpha.10 compatibility loader")
        finish(True, "alpha.10 native-binding interface contract is present")
    except Exception:
        finish(False, traceback.format_exc())


QtCore.QTimer.singleShot(300, run)
