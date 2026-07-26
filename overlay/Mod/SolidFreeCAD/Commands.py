"""GUI commands exposed by the SolidFreeCAD workbench."""

from __future__ import annotations

import os

import FreeCAD as App
import FreeCADGui as Gui

from SolidFreeCAD.ShaftFeature import create_shaft


_MODULE_DIR = os.path.dirname(__file__)
_ICON_ROOT = os.path.join(_MODULE_DIR, "Resources", "icons")


def _icon(*parts: str) -> str:
    path = os.path.join(_ICON_ROOT, *parts)
    if os.path.exists(path):
        return path
    return os.path.join(_ICON_ROOT, "SolidFreeCAD.svg")


def _native_available(command_name: str) -> bool:
    return command_name in set(Gui.listCommands())


class NativeCommand:
    """Expose a native FreeCAD command with SolidFreeCAD resources."""

    def __init__(
        self,
        native_command: str,
        menu_text: str,
        tooltip: str,
        icon_parts: tuple[str, ...],
        requires_document: bool = False,
    ):
        self.native_command = native_command
        self.menu_text = menu_text
        self.tooltip = tooltip
        self.icon_parts = icon_parts
        self.requires_document = requires_document

    def GetResources(self):
        return {
            "Pixmap": _icon(*self.icon_parts),
            "MenuText": self.menu_text,
            "ToolTip": self.tooltip,
        }

    def IsActive(self):
        if self.requires_document and App.ActiveDocument is None:
            return False
        return _native_available(self.native_command)

    def Activated(self):
        if not _native_available(self.native_command):
            App.Console.PrintError(
                f"SolidFreeCAD: command not available: {self.native_command}\n"
            )
            return
        Gui.runCommand(self.native_command, 0)


class CreateShaftCommand:
    def GetResources(self):
        return {
            "Pixmap": _icon("shaft", "shaft_create.svg"),
            "MenuText": "Crear eje paramétrico",
            "ToolTip": (
                "Crea un eje escalonado editable con diámetros, longitudes "
                "y chavetero configurables desde el panel de propiedades."
            ),
        }

    def IsActive(self):
        return True

    def Activated(self):
        from SolidFreeCAD.PropertyPanel import show_panel

        obj = create_shaft()
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.activeDocument().activeView().fitAll()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(obj)
        show_panel()


class CreatePartCommand:
    def GetResources(self):
        return {
            "Pixmap": _icon("file", "file_new.svg"),
            "MenuText": "Nueva pieza mecánica",
            "ToolTip": "Crea un documento y un Body de Part Design.",
        }

    def IsActive(self):
        return True

    def Activated(self):
        doc = App.newDocument("SolidFreeCADPart")
        body = doc.addObject("PartDesign::Body", "Body")
        body.Label = "Pieza"
        doc.recompute()
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(body)


class ShowShaftPanelCommand:
    def GetResources(self):
        return {
            "Pixmap": _icon("shaft", "shaft_edit.svg"),
            "MenuText": "Panel de propiedades del eje",
            "ToolTip": "Muestra el editor simplificado de ejes SolidFreeCAD.",
        }

    def IsActive(self):
        return True

    def Activated(self):
        from SolidFreeCAD.PropertyPanel import show_panel

        show_panel()


class FitAndAxonometricCommand:
    def GetResources(self):
        return {
            "Pixmap": _icon("view", "view_fit.svg"),
            "MenuText": "Vista isométrica ajustada",
            "ToolTip": "Cambia a vista isométrica y ajusta el modelo a la pantalla.",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        view = Gui.activeDocument().activeView()
        view.viewAxonometric()
        view.fitAll()


Gui.addCommand("SFC_CreateShaft", CreateShaftCommand())
Gui.addCommand("SFC_CreatePart", CreatePartCommand())
Gui.addCommand("SFC_ShowShaftPanel", ShowShaftPanelCommand())
Gui.addCommand("SFC_FitAxonometric", FitAndAxonometricCommand())

_NATIVE_COMMANDS = {
    "SFC_Open": NativeCommand(
        "Std_Open", "Abrir", "Abre un archivo CAD.", ("file", "file_open.svg")
    ),
    "SFC_Save": NativeCommand(
        "Std_Save",
        "Guardar",
        "Guarda el documento activo.",
        ("file", "file_save.svg"),
        True,
    ),
    "SFC_NewSketch": NativeCommand(
        "Sketcher_NewSketch",
        "Nuevo croquis",
        "Crea un croquis en el soporte seleccionado.",
        ("sketch", "sketch_new.svg"),
        True,
    ),
    "SFC_Pad": NativeCommand(
        "PartDesign_Pad",
        "Extruir saliente",
        "Extruye un croquis para agregar material.",
        ("feature", "feature_pad.svg"),
        True,
    ),
    "SFC_Pocket": NativeCommand(
        "PartDesign_Pocket",
        "Corte por extrusión",
        "Extruye un croquis para quitar material.",
        ("feature", "feature_pocket.svg"),
        True,
    ),
    "SFC_Revolution": NativeCommand(
        "PartDesign_Revolution",
        "Revolución",
        "Crea material mediante revolución de un perfil.",
        ("feature", "feature_revolve.svg"),
        True,
    ),
    "SFC_Fillet": NativeCommand(
        "PartDesign_Fillet",
        "Redondeo",
        "Aplica un radio a las aristas seleccionadas.",
        ("feature", "feature_fillet.svg"),
        True,
    ),
    "SFC_Chamfer": NativeCommand(
        "PartDesign_Chamfer",
        "Chaflán",
        "Aplica un chaflán a las aristas seleccionadas.",
        ("feature", "feature_chamfer.svg"),
        True,
    ),
}

for _name, _command in _NATIVE_COMMANDS.items():
    Gui.addCommand(_name, _command)
