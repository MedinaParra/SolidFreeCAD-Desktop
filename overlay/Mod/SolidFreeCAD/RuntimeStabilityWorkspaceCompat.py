"""Compatibility loader for SolidFreeCAD alpha.13 runtime stabilization."""
from __future__ import annotations

import FreeCAD as App


def show_workspace():
    try:
        from SolidFreeCAD.RuntimeStabilityWorkspace import show_workspace as show_alpha13

        return show_alpha13()
    except Exception as exc:
        App.Console.PrintError(f"SolidFreeCAD alpha.13 initialization failed: {exc}\n")
        from SolidFreeCAD.RuntimePreflightWorkspaceCompat import show_workspace as show_alpha12

        return show_alpha12()


def hide_workspace():
    try:
        from SolidFreeCAD.RuntimeStabilityWorkspace import hide_workspace as hide_alpha13

        return hide_alpha13()
    except Exception:
        from SolidFreeCAD.RuntimePreflightWorkspaceCompat import hide_workspace as hide_alpha12

        return hide_alpha12()
