from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import FreeCADGui
from PySide import QtCore, QtWidgets


TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

expect_classic = os.environ.get("SOLIDFREECAD_EXPECT_CLASSIC") == "1"

main_window = FreeCADGui.getMainWindow()
if main_window is None:
    raise RuntimeError("FreeCAD main window is not available")

main_window.resize(1720, 900)
main_window.show()

application = QtWidgets.QApplication.instance()
if application is None:
    raise RuntimeError("Qt application is not available")
application.processEvents()

module_error: Exception | None = None
if not expect_classic:
    # Build-tree executions do not install the Python InitGui.py workbench registry.
    # Import the compiled modules directly: this registers the same native commands
    # without depending on the legacy workbench selector.
    try:
        import PartDesignGui  # noqa: F401
        import SketcherGui  # noqa: F401

        from workshop_model import create_workshop_part

        model = create_workshop_part("WorkshopGuiPreview")
        gui_document = FreeCADGui.activeDocument()
        if gui_document is None:
            raise RuntimeError("The workshop preview has no active GUI document")
        gui_document.activeView().viewAxonometric()
        gui_document.activeView().fitAll()
    except Exception as exc:  # preserve the screenshot even if module loading regresses
        module_error = exc

# Allow native command registration, deferred layout restoration and
# SolidFreeCAD chrome enforcement timers to finish before validation.
deadline = time.monotonic() + 1.5
while time.monotonic() < deadline:
    application.processEvents()
    time.sleep(0.01)

ribbon = main_window.findChild(QtWidgets.QToolBar, "SolidFreeCADRibbon")
command_search = main_window.findChild(QtWidgets.QLineEdit, "SolidFreeCADCommandSearch")
ribbon_tabs = main_window.findChild(QtWidgets.QTabBar, "SolidFreeCADRibbonTabs")

if expect_classic:
    if ribbon is not None:
        raise RuntimeError("SolidFreeCADRibbon must not be installed in Classic mode")
    if command_search is not None:
        raise RuntimeError("SolidFreeCADCommandSearch must not be installed in Classic mode")
    if ribbon_tabs is not None:
        raise RuntimeError("SolidFreeCADRibbonTabs must not be installed in Classic mode")

    print("SOLIDFREECAD_CLASSIC_SMOKE_OK")
    QtCore.QTimer.singleShot(0, application.quit)
else:
    if ribbon is None:
        raise RuntimeError("SolidFreeCADRibbon was not installed")
    if not ribbon.isVisible():
        raise RuntimeError("SolidFreeCADRibbon is not visible")
    if command_search is None:
        raise RuntimeError("SolidFreeCADCommandSearch was not installed")
    if ribbon_tabs is None:
        raise RuntimeError("SolidFreeCADRibbonTabs was not installed")
    if ribbon_tabs.count() < 8:
        raise RuntimeError(f"Expected at least 8 ribbon tabs, found {ribbon_tabs.count()}")

    screenshot_path = Path(
        os.environ.get("SOLIDFREECAD_SCREENSHOT", "solidfreecad-bootstrap.png")
    ).resolve()
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    application.processEvents()
    if not main_window.grab().save(str(screenshot_path)):
        raise RuntimeError(f"Could not save screenshot to {screenshot_path}")

    if module_error is not None:
        raise RuntimeError(f"Mechanical modules could not be initialized: {module_error}")

    command_toolbars = [ribbon, *ribbon.findChildren(QtWidgets.QToolBar)]
    command_names: set[str] = set()
    visible_actions = 0

    for toolbar in command_toolbars:
        for action in toolbar.actions():
            command_name = action.property("SolidFreeCADCommandName")
            if command_name:
                command_names.add(str(command_name))
            if not action.isSeparator() and action.isVisible():
                visible_actions += 1

    required_commands = {
        "Std_New",
        "Std_Open",
        "Std_Save",
        "Std_ViewFitAll",
        "Std_ViewIsometric",
        "PartDesign_Pad",
        "PartDesign_Pocket",
        "PartDesign_Fillet",
        "PartDesign_Chamfer",
    }
    missing = required_commands.difference(command_names)
    if missing:
        raise RuntimeError(f"Missing ribbon command entries: {sorted(missing)}")

    if visible_actions < 30:
        raise RuntimeError(f"Tabbed ribbon has too few visible actions: {visible_actions}")

    completer = command_search.completer()
    if completer is None or completer.model() is None:
        raise RuntimeError("Command search completer is not available")
    if completer.model().rowCount() == 0:
        raise RuntimeError("Command search catalogue is empty")

    menu_bar = main_window.menuBar()
    if menu_bar is not None and menu_bar.isVisible():
        raise RuntimeError("Classic menu bar should be hidden in SolidFreeCAD mode")

    visible_bottom_docks = [
        dock
        for dock in main_window.findChildren(QtWidgets.QDockWidget)
        if dock.isVisible()
        and main_window.dockWidgetArea(dock) == QtCore.Qt.BottomDockWidgetArea
    ]
    if visible_bottom_docks:
        names = [dock.objectName() or dock.windowTitle() for dock in visible_bottom_docks]
        raise RuntimeError(f"Bottom utility docks should be hidden: {names}")

    print(f"SOLIDFREECAD_GUI_SMOKE_OK screenshot={screenshot_path}")
    QtCore.QTimer.singleShot(0, application.quit)
