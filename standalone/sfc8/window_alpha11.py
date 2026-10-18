"""Compatibility import for alpha.11 launchers; loads the current standalone window."""
from .window_alpha12 import SolidFreeCADWindow, show_standalone

__all__ = ["SolidFreeCADWindow", "show_standalone"]
