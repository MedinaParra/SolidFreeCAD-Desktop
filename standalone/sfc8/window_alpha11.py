"""Compatibility import for alpha.11 launchers; the current window is alpha.12."""
from .window_alpha12 import SolidFreeCADWindow, show_standalone

__all__ = ["SolidFreeCADWindow", "show_standalone"]
