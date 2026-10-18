"""Qt compatibility for FreeCAD's PySide facade and standalone UI checks."""
try:
    from PySide import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtGui, QtWidgets

Action = getattr(QtGui, "QAction", None) or QtWidgets.QAction
Shortcut = getattr(QtGui, "QShortcut", None) or QtWidgets.QShortcut

__all__ = ["QtCore", "QtGui", "QtWidgets", "Action", "Shortcut"]
