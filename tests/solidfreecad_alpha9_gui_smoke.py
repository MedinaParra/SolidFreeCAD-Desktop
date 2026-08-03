"""Manual GUI contract for the source-only SolidFreeCAD alpha.9 workspace."""
from __future__ import annotations

import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

MARKER = os.environ.get("SOLIDFREECAD_ALPHA9_GUI_MARKER", "")
SCREENSHOT = os.environ.get("SOLIDFREECAD_ALPHA9_SCREENSHOT", "")


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
        from SolidFreeCAD.FeatureManagerWorkspace import show_workspace

        show_workspace()
        main = Gui.getMainWindow()
        main.resize(1600, 940)
        main.show()
        QtWidgets.QApplication.processEvents()

        required = {
            "Definition card": main.findChild(QtWidgets.QGroupBox, "SolidFreeCADAlpha9DefinitionCard"),
            "Selection collector": main.findChild(QtWidgets.QGroupBox, "SolidFreeCADAlpha9SelectionCollector"),
            "Selection mode": main.findChild(QtWidgets.QComboBox, "SolidFreeCADAlpha9SelectionMode"),
            "Orientation overlay": main.findChild(QtWidgets.QFrame, "SolidFreeCADAlpha9OrientationWidget"),
            "Feature tree": main.findChild(QtWidgets.QTreeWidget, "SolidFreeCADFeatureTree"),
            "Alpha9 status": main.findChild(QtWidgets.QLabel, "SolidFreeCADAlpha9Status"),
        }
        missing = [name for name, widget in required.items() if widget is None]
        if missing:
            raise RuntimeError("Missing alpha.9 widgets: " + ", ".join(missing))

        tree = required["Feature tree"]
        if tree.columnCount() != 2:
            raise RuntimeError(f"Feature tree must expose Design and State columns, got {tree.columnCount()}")

        selection_mode = required["Selection mode"]
        expected_modes = ["Selección automática", "Caras", "Aristas", "Vértices", "Cuerpos"]
        actual_modes = [selection_mode.itemText(i) for i in range(selection_mode.count())]
        if actual_modes != expected_modes:
            raise RuntimeError(f"Unexpected selection modes: {actual_modes}")

        doc = App.newDocument("Alpha9FeatureManagerTest")
        feature = doc.addObject("PartDesign::Feature", "Pad")
        feature.Label = "Saliente de prueba"
        feature.addProperty("App::PropertyLength", "Length")
        feature.Length = 25.0
        feature.addProperty("App::PropertyBool", "Reversed")
        feature.Reversed = False
        feature.addProperty("App::PropertyBool", "Midplane")
        feature.Midplane = False
        doc.recompute()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(feature)
        QtWidgets.QApplication.processEvents()

        title = main.findChild(QtWidgets.QLabel, "SFCAlpha9FeatureTitle")
        if title is None or "Saliente" not in title.text():
            raise RuntimeError("Dedicated Pad definition profile was not selected")
        form = main.findChild(QtWidgets.QFormLayout, "SolidFreeCADAlpha9DefinitionForm")
        if form is None or form.rowCount() < 2:
            raise RuntimeError("Dedicated Pad property editors were not created")

        if SCREENSHOT:
            os.makedirs(os.path.dirname(SCREENSHOT), exist_ok=True)
            if not main.grab().save(SCREENSHOT):
                raise RuntimeError("Unable to save alpha.9 interface screenshot")

        finish(True, "Alpha.9 dedicated feature managers and design-state contract validated")
    except Exception:
        finish(False, traceback.format_exc())


QtCore.QTimer.singleShot(500, run)
