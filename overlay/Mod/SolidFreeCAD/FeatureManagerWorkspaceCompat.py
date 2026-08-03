"""Safe loader for the SolidFreeCAD alpha.9 feature-manager prototype."""
from __future__ import annotations

import FreeCAD as App


def show_workspace():
    try:
        from SolidFreeCAD.FeatureManagerWorkspace import show_workspace as show_alpha9

        return show_alpha9()
    except Exception as exc:
        App.Console.PrintError(
            "SolidFreeCAD alpha.9 no pudo iniciar; se recuperará alpha.8: "
            f"{exc}\n"
        )
        from SolidFreeCAD.InteractionWorkspaceCompat import show_workspace as show_alpha8

        return show_alpha8()


def hide_workspace():
    try:
        from SolidFreeCAD.FeatureManagerWorkspace import hide_workspace as hide_alpha9

        return hide_alpha9()
    except Exception as exc:
        App.Console.PrintWarning(
            "SolidFreeCAD alpha.9 no pudo cerrar completamente; se cerrará alpha.8: "
            f"{exc}\n"
        )
        from SolidFreeCAD.InteractionWorkspaceCompat import hide_workspace as hide_alpha8

        return hide_alpha8()
