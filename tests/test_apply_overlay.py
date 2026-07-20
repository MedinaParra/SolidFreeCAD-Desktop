from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
APPLY_SCRIPT = REPOSITORY_ROOT / "scripts" / "apply-overlay.py"


class ApplyOverlayTest(unittest.TestCase):
    def create_fake_freecad_tree(self, root: Path) -> Path:
        gui = root / "src" / "Gui"
        gui.mkdir(parents=True)

        (gui / "CMakeLists.txt").write_text(
            "add_library(FreeCADGui SHARED)\n"
            "target_link_libraries(FreeCADGui PRIVATE FreeCADApp)\n",
            encoding="utf-8",
        )

        (gui / "MainWindow.cpp").write_text(
            '#include "MainWindow.h"\n'
            "\n"
            "MainWindow::MainWindow(QWidget* parent, Qt::WindowFlags flags)\n"
            "{\n"
            '    statusBar()->showMessage(tr("Ready"), 2001);\n'
            "}\n"
            "\n"
            "MainWindow::~MainWindow()\n"
            "{\n"
            "}\n",
            encoding="utf-8",
        )
        return root

    def run_apply(self, freecad_root: Path) -> None:
        subprocess.run(
            [sys.executable, str(APPLY_SCRIPT), str(freecad_root)],
            cwd=REPOSITORY_ROOT,
            check=True,
        )

    def test_overlay_applies_required_files_and_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            freecad_root = self.create_fake_freecad_tree(Path(directory))
            self.run_apply(freecad_root)

            gui = freecad_root / "src" / "Gui"
            self.assertTrue((gui / "SolidFreeCAD" / "SolidGuiManager.cpp").is_file())
            self.assertTrue((freecad_root / "SOLIDFREECAD_OVERLAY_APPLIED").is_file())

            cmake = (gui / "CMakeLists.txt").read_text(encoding="utf-8")
            main_window = (gui / "MainWindow.cpp").read_text(encoding="utf-8")

            self.assertIn("add_subdirectory(SolidFreeCAD)", cmake)
            self.assertIn('#include "SolidFreeCAD/SolidGuiBootstrap.h"', main_window)
            self.assertIn("SolidFreeCAD::installGui(this);", main_window)
            self.assertIn("SolidFreeCAD::uninstallGui();", main_window)

    def test_overlay_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            freecad_root = self.create_fake_freecad_tree(Path(directory))
            self.run_apply(freecad_root)
            self.run_apply(freecad_root)

            gui = freecad_root / "src" / "Gui"
            cmake = (gui / "CMakeLists.txt").read_text(encoding="utf-8")
            main_window = (gui / "MainWindow.cpp").read_text(encoding="utf-8")

            self.assertEqual(cmake.count("add_subdirectory(SolidFreeCAD)"), 1)
            self.assertEqual(main_window.count("SolidFreeCAD::installGui(this);"), 1)
            self.assertEqual(main_window.count("SolidFreeCAD::uninstallGui();"), 1)


if __name__ == "__main__":
    unittest.main()
