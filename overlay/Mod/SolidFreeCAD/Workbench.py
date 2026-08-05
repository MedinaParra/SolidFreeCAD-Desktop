"""SolidFreeCAD professional workbench loaded as a regular Python module."""
from __future__ import annotations

import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_ICON_PATH = os.path.join(_MODULE_DIR, "Resources", "icons", "SolidFreeCAD.svg")


def _available(command_names):
    registered = set(Gui.listCommands())
    return [command for command in command_names if command in registered]


def _apply_window_branding():
    main_window = Gui.getMainWindow()
    main_window.setWindowTitle("SolidFreeCAD Professional alpha.7")
    main_window.setWindowIcon(QtGui.QIcon(_ICON_PATH))


class SolidFreeCADWorkbench(Gui.Workbench):
    MenuText = "SolidFreeCAD"
    ToolTip = "Diseño mecánico paramétrico con entorno profesional integrado"
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

        # A single application menu avoids the duplicate Archivo menu seen in alpha.6.
        commands = _available([
            "SFC_CreatePart", "SFC_CreateDemoPart", "SFC_Open", "SFC_Save",
            "SFC_NewSketch", "SFC_Pad", "SFC_Pocket", "SFC_Revolution",
            "SFC_Fillet", "SFC_Chamfer", "SFC_CreateShaft", "SFC_ShowShaftPanel",
        ])
        if commands:
            self.appendMenu("SolidFreeCAD", commands)

    def Activated(self):
        from SolidFreeCAD.Alpha7Workspace import show_workspace
        from SolidFreeCAD.CommandBridge import patch_command_manager

        _apply_window_branding()
        general = App.ParamGet("User parameter:BaseApp/Preferences/General")
        general.SetString("AutoloadModule", "SolidFreeCADWorkbench")
        general.SetString("LastModule", "SolidFreeCADWorkbench")
        show_workspace()
        patch_command_manager()

    def Deactivated(self):
        from SolidFreeCAD.Alpha7Workspace import hide_workspace
        hide_workspace()

    def GetClassName(self):
        return "Gui::PythonWorkbench"
