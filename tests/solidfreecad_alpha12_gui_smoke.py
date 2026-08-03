"""Manual graphical contract test for SolidFreeCAD alpha.12 preflight source."""
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
        from SolidFreeCAD.RuntimePreflightWorkspace import show_workspace

        show_workspace()
        main = Gui.getMainWindow()
        required = {
            "preflight page": main.findChild(QtWidgets.QWidget, "SolidFreeCADAlpha12PreflightPage"),
            "preflight tree": main.findChild(QtWidgets.QTreeWidget, "SolidFreeCADAlpha12PreflightTree"),
            "preflight summary": main.findChild(QtWidgets.QLabel, "SolidFreeCADAlpha12PreflightSummary"),
            "preflight run": main.findChild(QtWidgets.QPushButton, "SolidFreeCADAlpha12Run"),
            "verification tabs": main.findChild(QtWidgets.QTabWidget, "SolidFreeCADAlpha11VerificationTabs"),
        }
        missing = [name for name, widget in required.items() if widget is None]
        if missing:
            raise RuntimeError("Missing alpha.12 widgets: " + ", ".join(missing))
        tabs = required["verification tabs"]
        labels = [tabs.tabText(index) for index in range(tabs.count())]
        if "Preflight" not in labels:
            raise RuntimeError("Preflight tab was not installed")
        finish(True, "alpha.12 local runtime-preflight interface contract is present")
    except Exception:
        finish(False, traceback.format_exc())


QtCore.QTimer.singleShot(350, run)
