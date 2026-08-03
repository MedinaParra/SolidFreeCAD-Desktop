"""Safe alpha.10 loader with alpha.9 recovery."""
from __future__ import annotations

import FreeCAD as App


def show_workspace():
    try:
        from SolidFreeCAD.FeatureBindingWorkspace import show_workspace as show_alpha10
        return show_alpha10()
    except Exception as exc:
        App.Console.PrintError(f"SolidFreeCAD alpha.10 failed, restoring alpha.9: {exc}\n")
        from SolidFreeCAD.FeatureManagerWorkspaceCompat import show_workspace as show_alpha9
        return show_alpha9()


def hide_workspace():
    try:
        from SolidFreeCAD.FeatureBindingWorkspace import hide_workspace as hide_alpha10
        return hide_alpha10()
    except Exception:
        from SolidFreeCAD.FeatureManagerWorkspaceCompat import hide_workspace as hide_alpha9
        return hide_alpha9()
