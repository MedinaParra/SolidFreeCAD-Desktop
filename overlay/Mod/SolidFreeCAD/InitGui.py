"""Register SolidFreeCAD through a regular Python module.

FreeCAD executes InitGui.py with loader-specific globals, so the workbench
implementation intentionally lives in SolidFreeCAD.Workbench.
"""

import FreeCADGui as Gui

from SolidFreeCAD.Workbench import SolidFreeCADWorkbench

Gui.addWorkbench(SolidFreeCADWorkbench())
