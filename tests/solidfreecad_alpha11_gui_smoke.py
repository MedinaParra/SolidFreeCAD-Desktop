"""Manual graphical contract test for SolidFreeCAD alpha.11 source RC."""
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
        from SolidFreeCAD.WorkspaceRC import show_workspace

        show_workspace()
        main = Gui.getMainWindow()
        required = {
            "quick access": main.findChild(QtWidgets.QToolBar, "SolidFreeCADAlpha11QuickAccess"),
            "layout profile": main.findChild(QtWidgets.QComboBox, "SolidFreeCADAlpha11LayoutProfile"),
            "density": main.findChild(QtWidgets.QComboBox, "SolidFreeCADAlpha11Density"),
            "theme": main.findChild(QtWidgets.QComboBox, "SolidFreeCADAlpha11Theme"),
            "verification": main.findChild(QtWidgets.QWidget, "SolidFreeCADAlpha11VerificationPage"),
            "diagnostics": main.findChild(QtWidgets.QTreeWidget, "SolidFreeCADAlpha11Diagnostics"),
            "coverage": main.findChild(QtWidgets.QTreeWidget, "SolidFreeCADAlpha11Coverage"),
            "release gate": main.findChild(QtWidgets.QListWidget, "SolidFreeCADAlpha11ReleaseChecklist"),
        }
        missing = [name for name, widget in required.items() if widget is None]
        if missing:
            raise RuntimeError("Missing alpha.11 widgets: " + ", ".join(missing))
        tabs = main.findChild(QtWidgets.QTabWidget, "SolidFreeCADAlpha7TaskTabs")
        labels = [tabs.tabText(index) for index in range(tabs.count())] if tabs else []
        if "Verificación" not in labels:
            raise RuntimeError("Verification task tab was not installed")
        finish(True, "alpha.11 source release-candidate interface contract is present")
    except Exception:
        finish(False, traceback.format_exc())


QtCore.QTimer.singleShot(350, run)
