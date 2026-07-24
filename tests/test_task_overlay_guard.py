from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TaskOverlayGuardContract(unittest.TestCase):
    def test_guard_uses_official_overlay_manager(self) -> None:
        source = (ROOT / "src/Gui/SolidFreeCAD/SolidTaskOverlayGuard.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn("#include <Gui/OverlayManager.h>", source)
        self.assertIn("OverlayManager::instance()", source)
        self.assertIn("unsetupDockWidget", source)
        self.assertIn('getDockWindow("Tasks")', source)
        self.assertIn('QStringLiteral("TaskView")', source)

    def test_guard_keeps_tasks_contextual(self) -> None:
        source = (ROOT / "src/Gui/SolidFreeCAD/SolidTaskOverlayGuard.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn("activeSketch()", source)
        self.assertIn("Qt::LeftDockWidgetArea", source)
        self.assertIn("setMaximumWidth(440)", source)
        self.assertIn("SolidFreeCADTaskOverlayDisabled", source)
        self.assertIn("SolidFreeCADTaskDockActive", source)

    def test_guard_is_compiled_and_installed(self) -> None:
        cmake = (ROOT / "src/Gui/SolidFreeCAD/CMakeLists.txt").read_text(encoding="utf-8")
        bootstrap = (ROOT / "src/Gui/SolidFreeCAD/SolidGuiBootstrap.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn("SolidTaskOverlayGuard.cpp", cmake)
        self.assertIn("SolidTaskOverlayGuard.h", cmake)
        self.assertIn('#include "SolidTaskOverlayGuard.h"', bootstrap)
        self.assertIn("std::unique_ptr<SolidTaskOverlayGuard>", bootstrap)
        self.assertIn("taskOverlayGuard->install(mainWindow)", bootstrap)

    def test_duplicate_badges_are_synchronized(self) -> None:
        source = (ROOT / "src/Gui/SolidFreeCAD/SolidTaskOverlayGuard.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn("synchronizeContextBadges", source)
        self.assertIn('QStringLiteral("SolidFreeCADContextBadge")', source)
        self.assertIn('tr("EDITANDO CROQUIS")', source)
        self.assertIn('tr("PIEZA")', source)


if __name__ == "__main__":
    unittest.main()
