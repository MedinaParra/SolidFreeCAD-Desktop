"""Graphical validation of the SolidFreeCAD alpha.6 mechanical workspace."""
from __future__ import annotations

import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

MARKER = os.environ.get("SOLIDFREECAD_ALPHA6_GUI_MARKER", "")
SCREENSHOT = os.environ.get("SOLIDFREECAD_ALPHA6_SCREENSHOT", "")


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
        from SolidFreeCAD.MechanicalWorkspace import show_workspace

        show_workspace()
        main = Gui.getMainWindow()
        main.resize(1500, 900)
        main.show()
        QtWidgets.QApplication.processEvents()

        command_manager = main.findChild(
            QtWidgets.QDockWidget, "SolidFreeCADClassicCommandManager"
        )
        feature_manager = main.findChild(
            QtWidgets.QDockWidget, "SolidFreeCADFeatureManager"
        )
        manager_tabs = main.findChild(QtWidgets.QTabWidget, "SolidFreeCADManagerTabs")
        feature_tree = main.findChild(QtWidgets.QTreeWidget, "SolidFreeCADFeatureTree")
        heads_up = main.findChild(QtWidgets.QToolBar, "SolidFreeCADHeadsUpToolbar")
        command_tabs = main.findChild(QtWidgets.QTabWidget, "SolidFreeCADCommandTabs")

        required = {
            "CommandManager": command_manager,
            "FeatureManager": feature_manager,
            "Manager tabs": manager_tabs,
            "Feature tree": feature_tree,
            "Heads-Up toolbar": heads_up,
            "Command tabs": command_tabs,
        }
        missing = [name for name, widget in required.items() if widget is None]
        if missing:
            raise RuntimeError("Missing alpha.6 widgets: " + ", ".join(missing))

        expected_command_tabs = [
            "Operaciones", "Croquis", "Superficies", "Evaluar", "Eje",
            "Chapa metálica", "Ensamblaje",
        ]
        actual_command_tabs = [
            command_tabs.tabText(index) for index in range(command_tabs.count())
        ]
        if actual_command_tabs != expected_command_tabs:
            raise RuntimeError(f"Unexpected alpha.6 command tabs: {actual_command_tabs}")

        expected_manager_tabs = ["Modelo", "Propiedades", "Configuraciones"]
        actual_manager_tabs = [manager_tabs.tabText(index) for index in range(manager_tabs.count())]
        if actual_manager_tabs != expected_manager_tabs:
            raise RuntimeError(f"Unexpected manager tabs: {actual_manager_tabs}")

        if main.findChild(QtWidgets.QToolButton, "SFCAlpha6Accept") is None:
            raise RuntimeError("Alpha.6 accept button is missing")
        if main.findChild(QtWidgets.QToolButton, "SFCAlpha6Cancel") is None:
            raise RuntimeError("Alpha.6 cancel button is missing")
        if "SFC_CreateDemoPart" not in set(Gui.listCommands()):
            raise RuntimeError("SFC_CreateDemoPart was not registered")
        if command_tabs.count() < 7 or len(command_manager.findChildren(QtWidgets.QToolButton)) < 30:
            raise RuntimeError("Alpha.6 CommandManager is incomplete")

        command_manager.show()
        feature_manager.show()
        heads_up.show()
        QtWidgets.QApplication.processEvents()
        if SCREENSHOT:
            os.makedirs(os.path.dirname(SCREENSHOT), exist_ok=True)
            if not main.grab().save(SCREENSHOT):
                raise RuntimeError("Unable to save alpha.6 GUI screenshot")

        finish(True, "Alpha.6 CommandManager, FeatureManager, PropertyManager and Heads-Up toolbar validated")
    except Exception:
        finish(False, traceback.format_exc())


QtCore.QTimer.singleShot(350, run)
