"""Graphical smoke test for the SolidFreeCAD classic Windows workspace.

The hosted Windows runner exposes only OpenGL 1.1, so this test validates Qt
widgets and command registration without creating a 3D document view. Native
piece and FCStd creation are validated separately with FreeCADCmd.
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
    QtCore.QTimer.singleShot(150, Gui.getMainWindow().close)


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

        buttons = command_manager.findChildren(QtWidgets.QToolButton)
        if len(buttons) < 25:
            raise RuntimeError(f"Expected at least 25 classic command buttons, found {len(buttons)}")
        if not property_manager.message.text():
            raise RuntimeError("PropertyManager workflow message is empty")
        if "SFC_CreatePart" not in set(Gui.listCommands()):
            raise RuntimeError("SFC_CreatePart was not registered")

        command_manager.show()
        property_manager.show()
        QtWidgets.QApplication.processEvents()
        finish(True, "Classic CommandManager, PropertyManager and command registration validated")
    except Exception:
        finish(False, traceback.format_exc())


QtCore.QTimer.singleShot(250, run)
