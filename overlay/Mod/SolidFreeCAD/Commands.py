"""GUI commands exposed by the SolidFreeCAD workbench."""
from __future__ import annotations

import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets

from SolidFreeCAD.ClassicIcons import ensure_icon_pack
from SolidFreeCAD.DemoPartFeature import create_demo_part
from SolidFreeCAD.ShaftFeature import create_shaft

_MODULE_DIR = os.path.dirname(__file__)
_ICON_ROOT = os.path.join(_MODULE_DIR, "Resources", "icons")
_CLASSIC_ROOT = os.path.join(_ICON_ROOT, "classic")


def _icon(*parts: str) -> str:
    ensure_icon_pack()
    classic_path = os.path.join(_CLASSIC_ROOT, *parts)
    if os.path.exists(classic_path):
        return classic_path
    old_path = os.path.join(_ICON_ROOT, *parts)
    if os.path.exists(old_path):
        return old_path
    return os.path.join(_ICON_ROOT, "SolidFreeCAD.svg")


def _native_available(command_name: str) -> bool:
    return command_name in set(Gui.listCommands())


def _refresh_command_buttons():
    """Refresh buttons that may have been disabled before a document existed."""
    manager = Gui.getMainWindow().findChild(
        QtWidgets.QDockWidget, "SolidFreeCADClassicCommandManager"
    )
    if manager is None:
        return
    for button in manager.findChildren(QtWidgets.QToolButton):
        command_available = button.property("sfcCommandAvailable")
        if command_available is not None:
            button.setEnabled(bool(command_available))
        elif App.ActiveDocument is not None:
            button.setEnabled(True)


def _show_alpha6_manager(mode: str):
    try:
        from SolidFreeCAD.MechanicalWorkspace import show_feature_manager

        manager = show_feature_manager()
        manager.set_mode(mode)
        manager.refresh_tree(force=True)
        manager.refresh_selection()
    except Exception as exc:
        App.Console.PrintMessage(f"SolidFreeCAD: manager refresh skipped: {exc}\n")


class NativeCommand:
    """Expose a native FreeCAD command with SolidFreeCAD resources."""

    def __init__(self, native_commands, menu_text, tooltip, icon_parts, requires_document=False):
        if isinstance(native_commands, str):
            native_commands = (native_commands,)
        self.native_commands = tuple(native_commands)
        self.menu_text = menu_text
        self.tooltip = tooltip
        self.icon_parts = icon_parts
        self.requires_document = requires_document

    def _resolved(self):
        for command in self.native_commands:
            if _native_available(command):
                return command
        return None

    def GetResources(self):
        return {"Pixmap": _icon(*self.icon_parts), "MenuText": self.menu_text, "ToolTip": self.tooltip}

    def IsActive(self):
        if self.requires_document and App.ActiveDocument is None:
            return False
        return self._resolved() is not None

    def Activated(self):
        command = self._resolved()
        if not command:
            App.Console.PrintError(
                "SolidFreeCAD: command not available: " + ", ".join(self.native_commands) + "\n"
            )
            return
        Gui.runCommand(command, 0)


class CreatePartCommand:
    def GetResources(self):
        return {
            "Pixmap": _icon("archivo", "nuevo.svg"),
            "MenuText": "Nueva pieza",
            "ToolTip": "Crea un documento de pieza con un Body de Part Design.",
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
        _refresh_command_buttons()
        _show_alpha6_manager("part")


class CreateDemoPartCommand:
    """Create a validated parametric part used by alpha.6 onboarding and CI."""

    def GetResources(self):
        return {
            "Pixmap": _icon("operaciones", "agujero.svg"),
            "MenuText": "Pieza demostrativa alpha.6",
            "ToolTip": "Crea una placa paramétrica con agujero y bolsillo para probar el flujo completo.",
        }

    def IsActive(self):
        return True

    def Activated(self):
        feature = create_demo_part()
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.activeDocument().activeView().fitAll()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(feature)
        _refresh_command_buttons()
        _show_alpha6_manager("part")


class CreateShaftCommand:
    def GetResources(self):
        return {
            "Pixmap": _icon("eje_parametrico", "crear_eje.svg"),
            "MenuText": "Crear eje paramétrico",
            "ToolTip": "Crea un eje escalonado editable con chavetero configurable.",
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
        _refresh_command_buttons()
        show_panel()
        _show_alpha6_manager("shaft")


class ShowShaftPanelCommand:
    def GetResources(self):
        return {
            "Pixmap": _icon("eje_parametrico", "editar_eje.svg"),
            "MenuText": "Editar eje",
            "ToolTip": "Muestra el editor simplificado del eje seleccionado.",
        }

    def IsActive(self):
        return True

    def Activated(self):
        from SolidFreeCAD.PropertyPanel import show_panel

        show_panel()
        _show_alpha6_manager("shaft")


class FitAndAxonometricCommand:
    def GetResources(self):
        return {
            "Pixmap": _icon("vistas", "ajustar.svg"),
            "MenuText": "Isométrica ajustada",
            "ToolTip": "Cambia a vista isométrica y ajusta el modelo.",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        view = Gui.activeDocument().activeView()
        view.viewAxonometric()
        view.fitAll()


Gui.addCommand("SFC_CreatePart", CreatePartCommand())
Gui.addCommand("SFC_CreateDemoPart", CreateDemoPartCommand())
Gui.addCommand("SFC_CreateShaft", CreateShaftCommand())
Gui.addCommand("SFC_ShowShaftPanel", ShowShaftPanelCommand())
Gui.addCommand("SFC_FitAxonometric", FitAndAxonometricCommand())

_NATIVE_COMMANDS = {
    "SFC_Open": NativeCommand("Std_Open", "Abrir", "Abre un archivo CAD.", ("archivo", "abrir.svg")),
    "SFC_Save": NativeCommand("Std_Save", "Guardar", "Guarda el documento activo.", ("archivo", "guardar.svg"), True),
    "SFC_NewSketch": NativeCommand(
        "Sketcher_NewSketch", "Nuevo croquis", "Crea un croquis sobre el plano o la cara seleccionada.",
        ("croquis", "nuevo_croquis.svg"), True,
    ),
    "SFC_Pad": NativeCommand("PartDesign_Pad", "Saliente/Base", "Agrega material extruyendo un croquis.", ("operaciones", "saliente_base.svg"), True),
    "SFC_Pocket": NativeCommand("PartDesign_Pocket", "Corte-Extruir", "Quita material extruyendo un croquis.", ("operaciones", "corte_extruir.svg"), True),
    "SFC_Revolution": NativeCommand("PartDesign_Revolution", "Revolución", "Crea una operación por revolución.", ("operaciones", "revolucion.svg"), True),
    "SFC_Fillet": NativeCommand("PartDesign_Fillet", "Redondeo", "Redondea aristas seleccionadas.", ("operaciones", "redondeo.svg"), True),
    "SFC_Chamfer": NativeCommand("PartDesign_Chamfer", "Chaflán", "Chaflana aristas seleccionadas.", ("operaciones", "chaflan.svg"), True),
    "SFC_Hole": NativeCommand("PartDesign_Hole", "Agujero", "Crea un agujero de Part Design.", ("operaciones", "agujero.svg"), True),
    "SFC_LinearPattern": NativeCommand("PartDesign_LinearPattern", "Patrón lineal", "Repite una operación linealmente.", ("operaciones", "patron_lineal.svg"), True),
    "SFC_PolarPattern": NativeCommand("PartDesign_PolarPattern", "Patrón circular", "Repite una operación circularmente.", ("operaciones", "patron_circular.svg"), True),
    "SFC_Mirrored": NativeCommand("PartDesign_Mirrored", "Simetría", "Crea una operación simétrica.", ("operaciones", "simetria.svg"), True),
}

for _name, _command in _NATIVE_COMMANDS.items():
    Gui.addCommand(_name, _command)
