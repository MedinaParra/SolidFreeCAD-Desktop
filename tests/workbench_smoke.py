from __future__ import annotations

import time

import FreeCADGui
from PySide import QtWidgets


application = QtWidgets.QApplication.instance()
if application is None:
    raise RuntimeError("Qt application is not available")

main_window = FreeCADGui.getMainWindow()
if main_window is None:
    raise RuntimeError("FreeCAD main window is not available")

main_window.show()
application.processEvents()

available = FreeCADGui.listWorkbenches()
required = ("PartDesignWorkbench", "SketcherWorkbench")
missing = [name for name in required if name not in available]
if missing:
    raise RuntimeError(f"Mechanical workbenches are not registered: {missing}")

for workbench_name in required:
    FreeCADGui.activateWorkbench(workbench_name)
    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        application.processEvents()
        time.sleep(0.01)

    active = FreeCADGui.activeWorkbench()
    if active is None:
        raise RuntimeError(f"No active workbench after activating {workbench_name}")

    active_name = active.name() if hasattr(active, "name") else ""
    if active_name and active_name != workbench_name:
        raise RuntimeError(
            f"Expected active workbench {workbench_name}, got {active_name}"
        )

print(
    "SOLIDFREECAD_WORKBENCH_SMOKE_OK "
    f"registered={','.join(required)}",
    flush=True,
)
application.quit()
