"""GUI commands exposed by the SolidFreeCAD workbench."""

from __future__ import annotations

import os

import FreeCAD as App
import FreeCADGui as Gui

from SolidFreeCAD.ShaftFeature import create_shaft


_ICON = os.path.join(
    os.path.dirname(__file__), "Resources", "icons", "SolidFreeCAD.svg"
)


class CreateShaftCommand:
    def GetResources(self):
        return {
            "Pixmap": _ICON,
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
            "Pixmap": _ICON,
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
            "Pixmap": _ICON,
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
            "Pixmap": _ICON,
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
