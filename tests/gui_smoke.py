from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import FreeCAD as App
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


def process_for(seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        application.processEvents()
        time.sleep(0.01)


def capture_window(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    application.processEvents()
    screen = application.primaryScreen()
    if screen is None:
        raise RuntimeError("No Qt screen is available for the GUI screenshot")
    screenshot = screen.grabWindow(int(main_window.winId()))
    if screenshot.isNull() or not screenshot.save(str(path)):
        raise RuntimeError(f"Could not save composited screenshot to {path}")


module_error: Exception | None = None
model = None
if not expect_classic:
    try:
        import PartDesignGui  # noqa: F401
        import SketcherGui  # noqa: F401

        from workshop_model import create_workshop_part

        model = create_workshop_part("WorkshopGuiPreview")
        App.setActiveDocument(model.document.Name)
        model.body.Tip = model.pad
        model.sketch.Visibility = False
        model.pad.Visibility = True
        model.body.Visibility = True
        model.pad.ViewObject.ShapeColor = (0.72, 0.78, 0.86)
        model.pad.ViewObject.LineColor = (0.12, 0.14, 0.16)
        model.document.recompute()

        gui_document = FreeCADGui.getDocument(model.document.Name)
        if gui_document is None:
            raise RuntimeError("The workshop preview has no GUI document")
        application.processEvents()
        active_view = gui_document.activeView()
        active_view.viewAxonometric()
        active_view.fitAll()
        active_view.redraw()
    except Exception as exc:
        module_error = exc

process_for(1.75)

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
    if ribbon is None or not ribbon.isVisible():
        raise RuntimeError("SolidFreeCADRibbon is not visible")
    if command_search is None:
        raise RuntimeError("SolidFreeCADCommandSearch was not installed")
    if ribbon_tabs is None or ribbon_tabs.count() < 8:
        raise RuntimeError("The tabbed SolidFreeCAD ribbon is incomplete")
    if module_error is not None or model is None:
        raise RuntimeError(f"Mechanical modules could not be initialized: {module_error}")

    model_docks = [
        dock
        for dock in main_window.findChildren(QtWidgets.QDockWidget)
        if dock.isVisible()
        and main_window.dockWidgetArea(dock) == QtCore.Qt.LeftDockWidgetArea
        and (dock.objectName() == "Model" or dock.windowTitle() == "Modelo")
    ]
    if not model_docks:
        raise RuntimeError("The SolidFreeCAD model manager is not visible on the left")

    for tree in model_docks[0].findChildren(QtWidgets.QTreeView):
        tree.expandToDepth(2)

    active_document = App.activeDocument()
    if active_document is None:
        raise RuntimeError("The workshop preview document is not active")
    pad = active_document.getObject("Pad")
    if pad is None or pad.Shape.isNull() or not pad.Shape.isValid():
        raise RuntimeError("The workshop Pad is not a valid solid")
    if not pad.ViewObject.Visibility:
        raise RuntimeError("The workshop Pad view provider is hidden")

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
        "Sketcher_LeaveSketch",
        "Sketcher_Dimension",
        "Sketcher_CompLine",
        "Sketcher_CompCreateRectangles",
        "Sketcher_CompCreateArc",
        "Sketcher_CompCurveEdition",
        "Sketcher_CompExternal",
        "Sketcher_Offset",
        "Sketcher_Symmetry",
        "Sketcher_ValidateSketch",
    }
    missing = required_commands.difference(command_names)
    if missing:
        raise RuntimeError(f"Missing ribbon command entries: {sorted(missing)}")

    if visible_actions < 40:
        raise RuntimeError(f"Tabbed ribbon has too few visible actions: {visible_actions}")

    completer = command_search.completer()
    if completer is None or completer.model() is None or completer.model().rowCount() == 0:
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

    gui_document = FreeCADGui.getDocument(active_document.Name)
    active_view = gui_document.activeView()
    active_view.viewAxonometric()
    active_view.fitAll()
    active_view.redraw()
    process_for(0.2)

    modeling_screenshot = Path(
        os.environ.get("SOLIDFREECAD_SCREENSHOT", "solidfreecad-modeling.png")
    ).resolve()
    capture_window(modeling_screenshot)

    sketch_index = next(
        (index for index in range(ribbon_tabs.count()) if ribbon_tabs.tabText(index) == "Croquis"),
        -1,
    )
    if sketch_index < 0:
        raise RuntimeError("The Croquis ribbon tab was not found")
    ribbon_tabs.setCurrentIndex(sketch_index)

    model.pad.Visibility = False
    model.sketch.Visibility = True
    active_document.recompute()
    gui_document.setEdit(model.sketch.Name)
    active_view.viewTop()
    active_view.fitAll()
    active_view.redraw()
    process_for(0.6)

    sketch_screenshot = Path(
        os.environ.get("SOLIDFREECAD_SKETCH_SCREENSHOT", "solidfreecad-sketch.png")
    ).resolve()
    capture_window(sketch_screenshot)

    # Always leave edit mode while the complete Qt/Sketcher object graph still exists.
    # Closing the application with a sketch in edit mode can destroy the event filter
    # after its target widgets in a partial build-tree runtime.
    gui_document.resetEdit()
    model.sketch.Visibility = False
    model.pad.Visibility = True
    active_document.recompute()
    process_for(0.25)

    print(
        "SOLIDFREECAD_GUI_SMOKE_OK "
        f"modeling={modeling_screenshot} sketch={sketch_screenshot}"
    )
    QtCore.QTimer.singleShot(0, application.quit)
