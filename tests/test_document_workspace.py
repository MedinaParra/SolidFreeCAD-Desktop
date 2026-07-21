from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUI_DIR = ROOT / "src" / "Gui" / "SolidFreeCAD"


class DocumentWorkspaceContractTests(unittest.TestCase):
    def test_controller_is_compiled_and_installed(self) -> None:
        cmake = (GUI_DIR / "CMakeLists.txt").read_text(encoding="utf-8")
        bootstrap = (GUI_DIR / "SolidGuiBootstrap.cpp").read_text(encoding="utf-8")

        self.assertIn("SolidDocumentWorkspace.cpp", cmake)
        self.assertIn("SolidDocumentWorkspace.h", cmake)
        self.assertIn('#include "SolidDocumentWorkspace.h"', bootstrap)
        self.assertIn("documentWorkspace->install(mainWindow);", bootstrap)
        self.assertIn("documentWorkspace.reset();", bootstrap)

    def test_file_page_uses_native_freecad_commands(self) -> None:
        source = (GUI_DIR / "SolidDocumentWorkspace.cpp").read_text(encoding="utf-8")
        expected_commands = {
            "Std_New",
            "Std_Open",
            "Std_Save",
            "Std_SaveAs",
            "Std_Import",
            "Std_Export",
            "Std_ProjectInfo",
            "Std_Print",
            "Std_CloseActiveWindow",
            "PartDesign_Body",
            "PartDesign_NewSketch",
        }

        for command in expected_commands:
            with self.subTest(command=command):
                self.assertIn(f'{{"{command}",', source)

        self.assertIn('tr("Archivo")', source)
        self.assertIn('QStringLiteral("FileDocument")', source)
        self.assertIn('QStringLiteral("ModelStart")', source)

    def test_document_and_context_states_are_named_for_gui_smoke_tests(self) -> None:
        source = (GUI_DIR / "SolidDocumentWorkspace.cpp").read_text(encoding="utf-8")

        self.assertIn('QStringLiteral("SolidFreeCADDocumentState")', source)
        self.assertIn('tr("SIN DOCUMENTO")', source)
        self.assertIn('tr("NUEVO")', source)
        self.assertIn('tr("GUARDADO")', source)
        self.assertIn('QStringLiteral("SolidFreeCADContextBadge")', source)
        self.assertIn('tr("ARCHIVO")', source)
        self.assertIn('tr("PIEZA")', source)

    def test_official_command_catalog_tracks_document_workflow(self) -> None:
        catalog = (ROOT / "scripts" / "verify-command-catalog.py").read_text(
            encoding="utf-8"
        )
        for command in (
            "Std_SaveAs",
            "Std_Import",
            "Std_Export",
            "Std_ProjectInfo",
            "Std_CloseActiveWindow",
        ):
            with self.subTest(command=command):
                self.assertIn(f'"{command}"', catalog)


if __name__ == "__main__":
    unittest.main()
