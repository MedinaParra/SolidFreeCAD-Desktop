"""Original SolidFreeCAD vector icons, shared by ribbon, menus and tree."""
from pathlib import Path
from .qt import QtGui

def icon(name):
    return QtGui.QIcon(str(Path(__file__).parent / "resources" / "icons" / (name + ".svg")))
