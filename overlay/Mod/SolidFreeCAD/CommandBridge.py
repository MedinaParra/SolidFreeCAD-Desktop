"""Route the validated alpha.5 ribbon into the alpha.6 integrated manager."""
from __future__ import annotations

import FreeCADGui as Gui
from PySide import QtWidgets

from SolidFreeCAD.ClassicWorkspace import _run_candidates


def patch_command_manager():
    """Redirect every existing CommandManager button to the alpha.6 PropertyManager."""
    main = Gui.getMainWindow()
    manager = main.findChild(QtWidgets.QDockWidget, "SolidFreeCADClassicCommandManager")
    if manager is None or bool(manager.property("sfcAlpha6Patched")):
        return manager

    def execute(spec):
        if _run_candidates(spec.candidates) and spec.next_mode:
            from SolidFreeCAD.MechanicalWorkspace import show_feature_manager

            feature_manager = show_feature_manager()
            feature_manager.set_mode(spec.next_mode, spec.title)
            feature_manager.refresh_tree(force=True)

    manager.execute = execute
    manager.setProperty("sfcAlpha6Patched", True)
    return manager
