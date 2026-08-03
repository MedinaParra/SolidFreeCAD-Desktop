"""Manual graphical validation for the alpha.7 interface-only prototype.

This test is intentionally not connected to a packaging workflow.  It can be
executed later inside a validated FreeCAD Windows runtime before the project is
allowed to produce portable or installer artifacts.
"""
from __future__ import annotations

import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

MARKER = os.environ.get("SOLIDFREECAD_ALPHA7_GUI_MARKER", "")
SCREENSHOT = os.environ.get("SOLIDFREECAD_ALPHA7_SCREENSHOT", "")


def finish(success: bool, message: str):
    if MARKER:
        with open(MARKER, "w", encoding="utf-8") as handle:
            handle.write(("PASS" if success else "FAIL") + "\n" + message + "\n")
    if not success:
        App.Console.PrintError(message + "\n")
    QtCore.QTimer.singleShot(250, Gui.getMainWindow().close)


def run():
    try:
        import PartDesignGui  # noqa: F401
        import SketcherGui  # noqa: F401
        from SolidFreeCAD import Commands  # noqa: F401
        from SolidFreeCAD.ProfessionalWorkspaceCompat import show_workspace

        show_workspace()
        main = Gui.getMainWindow()
        main.resize(1600, 950)
        main.show()
        QtWidgets.QApplication.processEvents()

        required = {
            "alpha.6 CommandManager": main.findChild(
                QtWidgets.QDockWidget, "SolidFreeCADClassicCommandManager"
            ),
            "FeatureManager": main.findChild(
                QtWidgets.QDockWidget, "SolidFreeCADFeatureManager"
            ),
            "context bar": main.findChild(
                QtWidgets.QToolBar, "SolidFreeCADAlpha7ContextBar"
            ),
            "command search": main.findChild(
                QtWidgets.QLineEdit, "SolidFreeCADAlpha7CommandSearch"
            ),
            "document selector": main.findChild(
                QtWidgets.QComboBox, "SolidFreeCADAlpha7DocumentSelector"
            ),
            "task pane": main.findChild(
                QtWidgets.QDockWidget, "SolidFreeCADAlpha7TaskPane"
            ),
            "task tabs": main.findChild(
                QtWidgets.QTabWidget, "SolidFreeCADAlpha7TaskTabs"
            ),
            "parameter editor": main.findChild(
                QtWidgets.QWidget, "SolidFreeCADAlpha7ParameterForm"
            ),
            "design library": main.findChild(
                QtWidgets.QTreeWidget, "SolidFreeCADAlpha7DesignLibrary"
            ),
        }
        missing = [name for name, widget in required.items() if widget is None]
        if missing:
            raise RuntimeError("Missing alpha.7 widgets: " + ", ".join(missing))

        task_tabs = required["task tabs"]
        labels = [task_tabs.tabText(index) for index in range(task_tabs.count())]
        expected = ["Tareas", "Biblioteca", "Apariencias", "Recursos"]
        if labels != expected:
            raise RuntimeError(f"Unexpected alpha.7 task tabs: {labels}")

        if App.ActiveDocument is None:
            App.newDocument("Alpha7InterfaceValidation")
        QtWidgets.QApplication.processEvents()

        search = required["command search"]
        search.setText("Vista isométrica")
        if search.text() != "Vista isométrica":
            raise RuntimeError("Command search cannot retain user input")
        search.clear()

        if SCREENSHOT:
            os.makedirs(os.path.dirname(SCREENSHOT), exist_ok=True)
            if not main.grab().save(SCREENSHOT):
                raise RuntimeError("Unable to save alpha.7 GUI screenshot")

        finish(
            True,
            "Alpha.7 context bar, command search, task pane, appearance controls and library validated",
        )
    except Exception:
        finish(False, traceback.format_exc())


QtCore.QTimer.singleShot(350, run)
