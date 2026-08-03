"""Windows evidence entry point for SolidFreeCAD alpha.13.

Runs alpha.12 geometry/UI preflight and alpha.13 runtime stability checks in an
existing official FreeCAD runtime. It writes evidence only and closes FreeCAD.
"""
from __future__ import annotations

import json
import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

MARKER = os.environ.get("SOLIDFREECAD_ALPHA13_MARKER", "")
OUTPUT = os.environ.get("SOLIDFREECAD_ALPHA13_OUTPUT", "")
RUNTIME_ASSET = os.environ.get("SOLIDFREECAD_RUNTIME_ASSET", "")
RUNTIME_DIGEST = os.environ.get("SOLIDFREECAD_RUNTIME_DIGEST", "")


def finish(success: bool, payload: dict):
    message = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    if MARKER:
        os.makedirs(os.path.dirname(MARKER), exist_ok=True)
        with open(MARKER, "w", encoding="utf-8") as handle:
            handle.write(("PASS" if success else "FAIL") + "\n" + message + "\n")
    printer = App.Console.PrintMessage if success else App.Console.PrintError
    printer(message + "\n")
    main = Gui.getMainWindow()
    QtCore.QTimer.singleShot(600, main.close)
    QtCore.QTimer.singleShot(2500, QtWidgets.QApplication.instance().quit)


def run():
    try:
        import PartDesignGui  # noqa: F401
        import SketcherGui  # noqa: F401
        import PartGui  # noqa: F401
        from SolidFreeCAD import Commands  # noqa: F401
        from SolidFreeCAD.RuntimePreflightWorkspace import PreflightRunner
        from SolidFreeCAD.RuntimeStabilityWorkspace import RuntimeStabilityRunner, show_workspace

        output = OUTPUT or os.path.join(os.getcwd(), "alpha13-evidence")
        os.makedirs(output, exist_ok=True)

        show_workspace()
        main = Gui.getMainWindow()
        main.resize(1500, 900)
        main.show()
        QtWidgets.QApplication.processEvents()

        preflight = PreflightRunner(main)
        preflight.folder = output
        preflight.report_path = os.path.join(output, "solidfreecad-alpha12-preflight.json")
        preflight.screenshot_path = os.path.join(output, "solidfreecad-alpha13-interface.png")
        preflight_report = preflight.run()

        stability = RuntimeStabilityRunner(main, output)
        stability_report = stability.run()
        stability_report.setdefault("runtime_source", {})
        stability_report["runtime_source"].update({
            "asset": RUNTIME_ASSET,
            "digest": RUNTIME_DIGEST,
        })
        with open(stability.report_path, "w", encoding="utf-8") as handle:
            json.dump(stability_report, handle, ensure_ascii=False, indent=2)

        passed = bool(preflight_report.get("summary", {}).get("passed")) and bool(
            stability_report.get("summary", {}).get("passed")
        )
        combined = {
            "passed": passed,
            "preflight": preflight_report.get("summary", {}),
            "stability": stability_report.get("summary", {}),
            "runtime_asset": RUNTIME_ASSET,
            "runtime_digest": RUNTIME_DIGEST,
        }
        with open(os.path.join(output, "solidfreecad-alpha13-combined.json"), "w", encoding="utf-8") as handle:
            json.dump(combined, handle, ensure_ascii=False, indent=2)
        finish(passed, combined)
    except Exception:
        finish(False, {"passed": False, "exception": traceback.format_exc()})


QtCore.QTimer.singleShot(700, run)
