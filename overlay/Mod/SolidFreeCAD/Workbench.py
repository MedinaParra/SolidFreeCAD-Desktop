"""SolidFreeCAD workbench implementation loaded as a regular Python module."""
from __future__ import annotations

import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtWidgets

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_ICON_PATH = os.path.join(_MODULE_DIR, "Resources", "icons", "SolidFreeCAD.svg")


def _available(command_names):
    registered = set(Gui.listCommands())
    return [command for command in command_names if command in registered]


def _apply_window_branding():
    main_window = Gui.getMainWindow()
    main_window.setWindowTitle("SolidFreeCAD Desktop alpha.8 · Interaction Prototype")
    main_window.setWindowIcon(QtGui.QIcon(_ICON_PATH))
    status_label = main_window.findChild(QtWidgets.QLabel, "SolidFreeCADStatusBrand")
    if status_label is None:
        status_label = QtWidgets.QLabel("SolidFreeCAD · Mechanical CAD · Windows")
        status_label.setObjectName("SolidFreeCADStatusBrand")
        status_label.setStyleSheet("font-weight: 600; padding: 0 8px;")
        main_window.statusBar().addPermanentWidget(status_label)


class SolidFreeCADWorkbench(Gui.Workbench):
    MenuText = "SolidFreeCAD"
    ToolTip = "Diseño mecánico paramétrico con flujo integrado"
    Icon = _ICON_PATH

    def Initialize(self):
        for module_name in ("PartDesignGui", "SketcherGui", "PartGui"):
            try:
                __import__(module_name)
            except ImportError:
                pass

        from SolidFreeCAD.ClassicIcons import ensure_icon_pack

        ensure_icon_pack()
        from SolidFreeCAD import Commands  # noqa: F401

        file_commands = _available([
            "SFC_CreatePart", "SFC_CreateDemoPart", "SFC_Open", "SFC_Save", "Std_Undo", "Std_Redo"
        ])
        workflow_commands = _available([
            "SFC_NewSketch", "SFC_Pad", "SFC_Pocket", "SFC_Revolution",
            "SFC_Fillet", "SFC_Chamfer", "SFC_CreateShaft", "SFC_ShowShaftPanel",
        ])
        if file_commands:
            self.appendMenu("Archivo", file_commands)
        if workflow_commands:
            self.appendMenu("SolidFreeCAD", workflow_commands)

    def Activated(self):
        from SolidFreeCAD.InteractionWorkspaceCompat import show_workspace
        from SolidFreeCAD.CommandBridge import patch_command_manager

        _apply_window_branding()
        general = App.ParamGet("User parameter:BaseApp/Preferences/General")
        general.SetString("AutoloadModule", "SolidFreeCADWorkbench")
        general.SetString("LastModule", "SolidFreeCADWorkbench")
        show_workspace()
        patch_command_manager()

    def Deactivated(self):
        from SolidFreeCAD.InteractionWorkspaceCompat import hide_workspace

        hide_workspace()

    def GetClassName(self):
        return "Gui::PythonWorkbench"
