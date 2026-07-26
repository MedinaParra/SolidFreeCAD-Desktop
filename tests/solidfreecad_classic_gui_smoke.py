"""Graphical smoke test for the SolidFreeCAD classic Windows workspace.

Run with FreeCAD.exe, not FreeCADCmd.exe or FreeCAD.exe --console.
"""
from __future__ import annotations

import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

MARKER = os.environ.get("SOLIDFREECAD_GUI_SMOKE_MARKER", "")


def finish(success: bool, message: str):
    if MARKER:
        with open(MARKER, "w", encoding="utf-8") as handle:
            handle.write(("PASS" if success else "FAIL") + "\n" + message + "\n")
    if not success:
        App.Console.PrintError(message + "\n")
    QtCore.QTimer.singleShot(500, Gui.getMainWindow().close)


def run():
    try:
        import PartDesignGui  # noqa: F401
        import SketcherGui  # noqa: F401
        from SolidFreeCAD import Commands  # noqa: F401
        from SolidFreeCAD.ClassicIcons import ensure_icon_pack
        from SolidFreeCAD.ClassicWorkspace import show_workspace

        icon_root = ensure_icon_pack()
        if not os.path.isdir(icon_root):
            raise RuntimeError("Classic icon directory was not created")

        show_workspace()
        main = Gui.getMainWindow()
        command_manager = main.findChild(
            QtWidgets.QDockWidget, "SolidFreeCADClassicCommandManager"
        )
        property_manager = main.findChild(
            QtWidgets.QDockWidget, "SolidFreeCADClassicPropertyManager"
        )
        tabs = main.findChild(QtWidgets.QTabWidget, "SolidFreeCADCommandTabs")
        if command_manager is None:
            raise RuntimeError("Classic CommandManager was not created")
        if property_manager is None:
            raise RuntimeError("Classic PropertyManager was not created")
        if tabs is None:
            raise RuntimeError("CommandManager tabs were not created")

        expected_tabs = ["Operaciones", "Croquis", "Superficies", "Evaluar", "Eje"]
        actual_tabs = [tabs.tabText(index) for index in range(tabs.count())]
        if actual_tabs != expected_tabs:
            raise RuntimeError(f"Unexpected CommandManager tabs: {actual_tabs}")

        doc = App.newDocument("ClassicWorkflowSmoke")
        body = doc.addObject("PartDesign::Body", "Body")
        body.Label = "Pieza de prueba"
        doc.recompute()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(body)
        QtWidgets.QApplication.processEvents()

        property_manager.refresh_selection()
        if property_manager.selection_label.text() == "Sin selección":
            raise RuntimeError("PropertyManager did not track the selected Body")

        output = os.environ.get("SOLIDFREECAD_CLASSIC_SMOKE_FCSTD", "")
        if output:
            doc.saveAs(output)
            if not os.path.exists(output):
                raise RuntimeError("Classic workflow FCStd example was not saved")

        command_manager.show()
        property_manager.show()
        main.show()
        QtWidgets.QApplication.processEvents()
        finish(True, "Classic CommandManager, PropertyManager and piece flow validated")
    except Exception:
        finish(False, traceback.format_exc())


Gui.showMainWindow()
QtCore.QTimer.singleShot(1500, run)
