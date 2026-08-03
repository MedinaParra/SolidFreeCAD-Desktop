"""Automated Windows preflight entry point for an existing FreeCAD runtime."""
from __future__ import annotations

import json
import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

MARKER = os.environ.get("SOLIDFREECAD_ALPHA12_MARKER", "")
OUTPUT = os.environ.get("SOLIDFREECAD_ALPHA12_OUTPUT", "")


def finish(success: bool, message: str):
    if MARKER:
        os.makedirs(os.path.dirname(MARKER), exist_ok=True)
        with open(MARKER, "w", encoding="utf-8") as handle:
            handle.write(("PASS" if success else "FAIL") + "\n" + message + "\n")
    printer = App.Console.PrintMessage if success else App.Console.PrintError
    printer(message + "\n")
    QtCore.QTimer.singleShot(400, Gui.getMainWindow().close)


def run():
    try:
        import PartDesignGui  # noqa: F401
        import SketcherGui  # noqa: F401
        import PartGui  # noqa: F401
        from SolidFreeCAD import Commands  # noqa: F401
        from SolidFreeCAD.RuntimePreflightWorkspace import PreflightRunner, show_workspace

        show_workspace()
        main = Gui.getMainWindow()
        main.resize(1500, 900)
        main.show()
        QtWidgets.QApplication.processEvents()

        runner = PreflightRunner(main)
        if OUTPUT:
            os.makedirs(OUTPUT, exist_ok=True)
            runner.folder = OUTPUT
            runner.report_path = os.path.join(OUTPUT, "solidfreecad-alpha12-preflight.json")
            runner.screenshot_path = os.path.join(OUTPUT, "solidfreecad-alpha12-interface.png")
        report = runner.run()
        summary = report.get("summary", {})
        message = json.dumps(summary, ensure_ascii=False, sort_keys=True)
        finish(bool(summary.get("passed")), message)
    except Exception:
        finish(False, traceback.format_exc())


QtCore.QTimer.singleShot(500, run)
