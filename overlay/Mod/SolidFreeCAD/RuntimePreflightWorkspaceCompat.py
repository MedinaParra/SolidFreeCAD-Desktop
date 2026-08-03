"""Safe alpha.12 preflight loader with alpha.11 recovery."""
from __future__ import annotations

import FreeCAD as App


def show_workspace():
    try:
        from SolidFreeCAD.RuntimePreflightWorkspace import show_workspace as show_alpha12
        return show_alpha12()
    except Exception as exc:
        App.Console.PrintError(f"SolidFreeCAD alpha.12 failed, restoring alpha.11: {exc}\n")
        from SolidFreeCAD.WorkspaceRCCompat import show_workspace as show_alpha11
        return show_alpha11()


def hide_workspace():
    try:
        from SolidFreeCAD.RuntimePreflightWorkspace import hide_workspace as hide_alpha12
        return hide_alpha12()
    except Exception:
        from SolidFreeCAD.WorkspaceRCCompat import hide_workspace as hide_alpha11
        return hide_alpha11()
