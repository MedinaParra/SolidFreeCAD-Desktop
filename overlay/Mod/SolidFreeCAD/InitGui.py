"""SolidFreeCAD mechanical-design workbench registration."""

from __future__ import annotations

import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtWidgets


_MODULE_DIR = os.path.dirname(__file__)
_ICON_PATH = os.path.join(_MODULE_DIR, "Resources", "icons", "SolidFreeCAD.svg")


def _available(command_names):
    registered = set(Gui.listCommands())
    return [command for command in command_names if command in registered]


def _apply_window_branding():
    main_window = Gui.getMainWindow()
    main_window.setWindowTitle("SolidFreeCAD Desktop")
    main_window.setWindowIcon(QtGui.QIcon(_ICON_PATH))

    status_label = main_window.findChild(QtWidgets.QLabel, "SolidFreeCADStatusBrand")
    if status_label is None:
        status_label = QtWidgets.QLabel("SolidFreeCAD · Mechanical CAD")
        status_label.setObjectName("SolidFreeCADStatusBrand")
        status_label.setStyleSheet("font-weight: 600; padding: 0 8px;")
        main_window.statusBar().addPermanentWidget(status_label)


class SolidFreeCADWorkbench(Gui.Workbench):
    MenuText = "SolidFreeCAD"
    ToolTip = "Diseño mecánico paramétrico basado en FreeCAD"
    Icon = _ICON_PATH

    def Initialize(self):
        # Register native command sets before creating SolidFreeCAD wrappers.
        try:
            import PartDesignGui  # noqa: F401
        except ImportError:
            pass

        try:
            import SketcherGui  # noqa: F401
        except ImportError:
            pass

        from SolidFreeCAD import Commands  # noqa: F401

        file_commands = _available(
            [
                "SFC_CreatePart",
                "SFC_Open",
                "SFC_Save",
                "Std_Undo",
                "Std_Redo",
            ]
        )
        mechanical_commands = _available(
            [
                "SFC_NewSketch",
                "SFC_Pad",
                "SFC_Pocket",
                "SFC_Revolution",
                "SFC_Fillet",
                "SFC_Chamfer",
                "SFC_CreateShaft",
                "SFC_ShowShaftPanel",
            ]
        )
        view_commands = _available(
            [
                "SFC_FitAxonometric",
                "ViewFit",
                "ViewAxonometric",
                "Std_ViewFront",
                "Std_ViewTop",
                "Std_ViewRight",
            ]
        )

        if file_commands:
            self.appendToolbar("Archivo", file_commands)
            self.appendMenu("Archivo", file_commands)

        if mechanical_commands:
            self.appendToolbar("Modelado mecánico", mechanical_commands)
            self.appendMenu("SolidFreeCAD", mechanical_commands)

        if view_commands:
            self.appendToolbar("Vista", view_commands)
            self.appendMenu("Vista", view_commands)

    def Activated(self):
        from SolidFreeCAD.PropertyPanel import show_panel

        _apply_window_branding()
        general = App.ParamGet("User parameter:BaseApp/Preferences/General")
        general.SetString("AutoloadModule", "SolidFreeCADWorkbench")
        general.SetString("LastModule", "SolidFreeCADWorkbench")
        show_panel()

    def Deactivated(self):
        from SolidFreeCAD.PropertyPanel import hide_panel

        hide_panel()

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(SolidFreeCADWorkbench())
