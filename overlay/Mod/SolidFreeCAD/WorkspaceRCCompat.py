"""Safe alpha.11 source-RC loader with alpha.10 recovery."""
from __future__ import annotations

import FreeCAD as App


def show_workspace():
    try:
        from SolidFreeCAD.WorkspaceRC import show_workspace as show_alpha11
        return show_alpha11()
    except Exception as exc:
        App.Console.PrintError(f"SolidFreeCAD alpha.11 failed, restoring alpha.10: {exc}\n")
        from SolidFreeCAD.FeatureBindingWorkspaceCompat import show_workspace as show_alpha10
        return show_alpha10()


def hide_workspace():
    try:
        from SolidFreeCAD.WorkspaceRC import hide_workspace as hide_alpha11
        return hide_alpha11()
    except Exception:
        from SolidFreeCAD.FeatureBindingWorkspaceCompat import hide_workspace as hide_alpha10
        return hide_alpha10()
