"""Manual graphical contract test for the source-only alpha.8 interface.

This script is intentionally not connected to a packaging workflow. Run it only
inside a validated FreeCAD 1.1.1 Windows runtime while refining the interface.
"""
from __future__ import annotations

import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

MARKER = os.environ.get("SOLIDFREECAD_ALPHA8_GUI_MARKER", "")
SCREENSHOT = os.environ.get("SOLIDFREECAD_ALPHA8_SCREENSHOT", "")


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
        from SolidFreeCAD.InteractionWorkspace import show_workspace

        show_workspace()
        main = Gui.getMainWindow()
        main.resize(1600, 940)
        main.show()
        QtWidgets.QApplication.processEvents()

        required = {
            "CommandManager": main.findChild(QtWidgets.QTabWidget, "SolidFreeCADCommandTabs"),
            "Feature hierarchy": main.findChild(QtWidgets.QTreeWidget, "SolidFreeCADFeatureTree"),
            "Context bar": main.findChild(QtWidgets.QToolBar, "SolidFreeCADAlpha7ContextBar"),
            "Operation page": main.findChild(QtWidgets.QWidget, "SolidFreeCADAlpha8OperationPage"),
            "Confirmation corner": main.findChild(QtWidgets.QFrame, "SolidFreeCADAlpha8ConfirmationCorner"),
            "Display style": main.findChild(QtWidgets.QComboBox, "SolidFreeCADAlpha8DisplayStyle"),
            "Alpha8 status": main.findChild(QtWidgets.QLabel, "SolidFreeCADAlpha8Status"),
        }
        missing = [name for name, widget in required.items() if widget is None]
        if missing:
            raise RuntimeError("Missing alpha.8 widgets: " + ", ".join(missing))

        tabs = main.findChild(QtWidgets.QTabWidget, "SolidFreeCADAlpha7TaskTabs")
        if tabs is None or "Operación" not in [tabs.tabText(i) for i in range(tabs.count())]:
            raise RuntimeError("Contextual Operation tab is missing")

        doc = App.newDocument("Alpha8InteractionTest")
        body = doc.addObject("PartDesign::Body", "Body")
        body.Label = "Pieza de prueba"
        sketch = doc.addObject("PartDesign::Feature", "FeaturePlaceholder")
        sketch.Label = "Operación de prueba"
        doc.recompute()
        QtWidgets.QApplication.processEvents()

        tree = main.findChild(QtWidgets.QTreeWidget, "SolidFreeCADFeatureTree")
        if tree.topLevelItemCount() == 0:
            raise RuntimeError("Hierarchical feature tree did not populate")

        display = main.findChild(QtWidgets.QComboBox, "SolidFreeCADAlpha8DisplayStyle")
        expected_styles = ["Sombreado con aristas", "Sombreado", "Alámbrico"]
        actual_styles = [display.itemText(i) for i in range(display.count())]
        if actual_styles != expected_styles:
            raise RuntimeError(f"Unexpected display styles: {actual_styles}")

        if SCREENSHOT:
            os.makedirs(os.path.dirname(SCREENSHOT), exist_ok=True)
            if not main.grab().save(SCREENSHOT):
                raise RuntimeError("Unable to save alpha.8 interface screenshot")

        finish(True, "Alpha.8 interaction shell and source-only interface contract validated")
    except Exception:
        finish(False, traceback.format_exc())


QtCore.QTimer.singleShot(450, run)
