"""Compatibility loader for SolidFreeCAD alpha.14 interactive acceptance."""
from __future__ import annotations

import FreeCAD as App


def show_workspace():
    try:
        from SolidFreeCAD.InteractiveAcceptanceWorkspace import show_workspace as show_alpha14

        return show_alpha14()
    except Exception as exc:
        App.Console.PrintError(f"SolidFreeCAD alpha.14 initialization failed: {exc}\n")
        from SolidFreeCAD.RuntimeStabilityWorkspaceCompat import show_workspace as show_alpha13

        return show_alpha13()


def hide_workspace():
    try:
        from SolidFreeCAD.InteractiveAcceptanceWorkspace import hide_workspace as hide_alpha14

        return hide_alpha14()
    except Exception:
        from SolidFreeCAD.RuntimeStabilityWorkspaceCompat import hide_workspace as hide_alpha13

        return hide_alpha13()
