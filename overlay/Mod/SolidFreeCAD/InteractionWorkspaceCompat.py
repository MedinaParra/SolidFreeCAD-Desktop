"""Compatibility loader for the SolidFreeCAD alpha.8 source-only workspace."""
from __future__ import annotations

import FreeCAD as App


def show_workspace():
    try:
        from SolidFreeCAD.InteractionWorkspace import show_workspace as show_alpha8

        return show_alpha8()
    except Exception as exc:
        App.Console.PrintError(
            "SolidFreeCAD alpha.8 no pudo iniciar; se recuperará alpha.7: "
            f"{exc}\n"
        )
        from SolidFreeCAD.ProfessionalWorkspaceCompat import show_workspace as show_alpha7

        return show_alpha7()


def hide_workspace():
    try:
        from SolidFreeCAD.InteractionWorkspace import hide_workspace as hide_alpha8

        return hide_alpha8()
    except Exception as exc:
        App.Console.PrintWarning(
            "SolidFreeCAD alpha.8 no pudo cerrar completamente; se cerrará alpha.7: "
            f"{exc}\n"
        )
        from SolidFreeCAD.ProfessionalWorkspaceCompat import hide_workspace as hide_alpha7

        return hide_alpha7()
