"""SolidFreeCAD alpha.12 local runtime preflight.

This source-only layer runs inside an existing FreeCAD runtime. It validates the
interface contract, essential command availability and isolated FCStd/STEP/BRep
round trips in a temporary directory. It writes only local diagnostic files and
never builds, packages or uploads an executable.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
import tempfile
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from SolidFreeCAD.ClassicWorkspace import _first_available
from SolidFreeCAD.WorkspaceRC import _COMMAND_REQUIREMENTS, _object_issues
from SolidFreeCAD.WorkspaceRCCompat import (
    hide_workspace as hide_alpha11_workspace,
    show_workspace as show_alpha11_workspace,
)

_PREFLIGHT_PAGE = "SolidFreeCADAlpha12PreflightPage"
_PREFLIGHT_TREE = "SolidFreeCADAlpha12PreflightTree"
_PREFLIGHT_SUMMARY = "SolidFreeCADAlpha12PreflightSummary"
_PREFLIGHT_RUN = "SolidFreeCADAlpha12Run"
_STATUS = "SolidFreeCADAlpha12Status"
_VERIFICATION_TABS = "SolidFreeCADAlpha11VerificationTabs"

_page = None


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    severity: str = "error"


class PreflightRunner:
    UI_REQUIREMENTS = (
        ("CommandManager", QtWidgets.QDockWidget, "SolidFreeCADClassicCommandManager"),
        ("FeatureManager", QtWidgets.QDockWidget, "SolidFreeCADFeatureManager"),
        ("Task pane", QtWidgets.QDockWidget, "SolidFreeCADAlpha7TaskPane"),
        ("Context bar", QtWidgets.QToolBar, "SolidFreeCADAlpha7ContextBar"),
        ("Quick access", QtWidgets.QToolBar, "SolidFreeCADAlpha11QuickAccess"),
        ("Confirmation corner", QtWidgets.QFrame, "SolidFreeCADAlpha8ConfirmationCorner"),
        ("Native binding panel", QtWidgets.QGroupBox, "SolidFreeCADAlpha10BindingPanel"),
        ("Verification page", QtWidgets.QWidget, "SolidFreeCADAlpha11VerificationPage"),
    )

    def __init__(self, main):
        self.main = main
        self.folder = tempfile.mkdtemp(prefix="SolidFreeCAD-alpha12-")
        self.results: list[CheckResult] = []
        self.report_path = os.path.join(self.folder, "solidfreecad-alpha12-preflight.json")
        self.screenshot_path = os.path.join(self.folder, "solidfreecad-alpha12-interface.png")

    def add(self, name, passed, detail, severity="error"):
        self.results.append(CheckResult(name, bool(passed), str(detail), severity))

    def run(self):
        self.check_interface()
        self.check_commands()
        self.check_active_document()
        self.capture_interface()
        self.check_geometry_roundtrip()
        report = self.build_report()
        with open(self.report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        return report

    def check_interface(self):
        for label, widget_type, object_name in self.UI_REQUIREMENTS:
            widget = self.main.findChild(widget_type, object_name)
            self.add(
                f"UI · {label}",
                widget is not None,
                object_name if widget is not None else f"Falta {object_name}",
            )
        size = self.main.size()
        ratio = getattr(self.main, "devicePixelRatioF", lambda: 1.0)()
        self.add(
            "UI · Ventana",
            size.width() >= 1024 and size.height() >= 650,
            f"{size.width()}×{size.height()} · devicePixelRatio={ratio:.2f}",
            "warning",
        )

    def check_commands(self):
        available = 0
        for requirement in _COMMAND_REQUIREMENTS:
            command = _first_available(requirement.candidates)
            if command:
                available += 1
            self.add(
                f"Comando · {requirement.group} · {requirement.label}",
                command is not None,
                command or "Ninguna variante registrada",
                "error" if requirement.group in {"Archivo", "Croquis", "Operaciones"} else "warning",
            )
        self.add(
            "Comandos · Cobertura esencial",
            available == len(_COMMAND_REQUIREMENTS),
            f"{available}/{len(_COMMAND_REQUIREMENTS)} capacidades disponibles",
            "warning",
        )

    def check_active_document(self):
        doc = App.ActiveDocument
        if doc is None:
            self.add("Documento activo", True, "No había documento activo; se usará prueba aislada.", "info")
            return
        issues = []
        for obj in doc.Objects:
            issues.extend(f"{obj.Label or obj.Name}: {value}" for value in _object_issues(obj))
        self.add(
            "Documento activo · Diagnóstico",
            not issues,
            "Sin advertencias" if not issues else " | ".join(issues[:10]),
            "warning",
        )

    def capture_interface(self):
        try:
            success = self.main.grab().save(self.screenshot_path)
            self.add(
                "Captura local de interfaz",
                success,
                self.screenshot_path if success else "Qt no pudo guardar la captura",
            )
        except Exception as exc:
            self.add("Captura local de interfaz", False, str(exc), "warning")

    def check_geometry_roundtrip(self):
        doc_name = "SFCAlpha12Geometry"
        reopened_name = None
        imported_name = "SFCAlpha12Imported"
        fcstd_path = os.path.join(self.folder, "alpha12-preflight.FCStd")
        step_path = os.path.join(self.folder, "alpha12-preflight.step")
        source_volume = None
        try:
            import Part

            for name in (doc_name, imported_name):
                if name in App.listDocuments():
                    App.closeDocument(name)

            doc = App.newDocument(doc_name)
            base = Part.makeBox(80.0, 50.0, 12.0)
            hole = Part.makeCylinder(6.0, 12.0, App.Vector(18.0, 18.0, 0.0))
            pocket = Part.makeBox(22.0, 16.0, 5.0, App.Vector(45.0, 17.0, 7.0))
            shape = base.cut(hole).cut(pocket)
            feature = doc.addObject("PartDesign::Feature", "PreflightPart")
            feature.Label = "Pieza de preflight"
            feature.Shape = shape
            doc.recompute()
            source_volume = float(feature.Shape.Volume)
            self.add(
                "BRep · Creación aislada",
                not feature.Shape.isNull() and feature.Shape.isValid() and source_volume > 0,
                f"Volumen={source_volume:.6f}",
            )

            doc.saveAs(fcstd_path)
            self.add("FCStd · Guardar", os.path.exists(fcstd_path), fcstd_path)
            Part.export([feature], step_path)
            self.add("STEP · Exportar", os.path.exists(step_path) and os.path.getsize(step_path) > 0, step_path)
            App.closeDocument(doc_name)

            reopened = App.openDocument(fcstd_path)
            reopened_name = reopened.Name
            reopened_feature = reopened.getObject("PreflightPart")
            reopened_valid = bool(
                reopened_feature
                and not reopened_feature.Shape.isNull()
                and reopened_feature.Shape.isValid()
            )
            reopened_volume = float(reopened_feature.Shape.Volume) if reopened_valid else 0.0
            tolerance = max(1e-6, abs(source_volume or 0.0) * 1e-8)
            self.add(
                "FCStd · Cerrar y reabrir",
                reopened_valid and abs(reopened_volume - (source_volume or 0.0)) <= tolerance,
                f"Volumen reabierto={reopened_volume:.6f}",
            )
            App.closeDocument(reopened.Name)
            reopened_name = None

            imported = App.newDocument(imported_name)
            Part.insert(step_path, imported.Name)
            imported.recompute()
            shapes = [
                obj.Shape
                for obj in imported.Objects
                if hasattr(obj, "Shape") and not obj.Shape.isNull()
            ]
            valid_import = bool(shapes) and all(shape.isValid() for shape in shapes)
            imported_volume = sum(float(shape.Volume) for shape in shapes)
            self.add(
                "STEP · Importar y validar",
                valid_import and imported_volume > 0,
                f"Objetos={len(shapes)} · volumen={imported_volume:.6f}",
            )
            App.closeDocument(imported.Name)
        except Exception:
            self.add("Geometría · Round trip", False, traceback.format_exc())
        finally:
            for name in (doc_name, imported_name, reopened_name):
                if name and name in App.listDocuments():
                    try:
                        App.closeDocument(name)
                    except Exception:
                        pass

    def build_report(self):
        failures = [result for result in self.results if not result.passed and result.severity == "error"]
        warnings = [result for result in self.results if not result.passed and result.severity == "warning"]
        return {
            "schema": "solidfreecad-preflight-1",
            "version": "0.1.0-alpha.12-runtime-preflight-source",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "freecad_version": list(App.Version()),
            "executable": App.ConfigGet("ExeName") if hasattr(App, "ConfigGet") else "",
            "working_directory": self.folder,
            "screenshot": self.screenshot_path,
            "summary": {
                "passed": not failures,
                "checks": len(self.results),
                "blocking_failures": len(failures),
                "warnings": len(warnings),
            },
            "checks": [asdict(result) for result in self.results],
        }


class PreflightPage(QtWidgets.QWidget):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.runner = None
        self.report = None
        self.setObjectName(_PREFLIGHT_PAGE)
        root = QtWidgets.QVBoxLayout(self)
        self.summary = QtWidgets.QLabel(
            "Ejecute el preflight dentro de un FreeCAD real. La prueba usa documentos temporales y no publica binarios."
        )
        self.summary.setObjectName(_PREFLIGHT_SUMMARY)
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setObjectName(_PREFLIGHT_TREE)
        self.tree.setHeaderLabels(["Comprobación", "Resultado", "Detalle"])
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        root.addWidget(self.tree, 1)
        row = QtWidgets.QHBoxLayout()
        run_button = QtWidgets.QPushButton("Ejecutar preflight local")
        run_button.setObjectName(_PREFLIGHT_RUN)
        run_button.clicked.connect(self.run_preflight)
        row.addWidget(run_button)
        self.open_button = QtWidgets.QPushButton("Abrir carpeta")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_folder)
        row.addWidget(self.open_button)
        self.copy_button = QtWidgets.QPushButton("Copiar resumen")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy_summary)
        row.addWidget(self.copy_button)
        root.addLayout(row)

    def run_preflight(self):
        self.summary.setText("Ejecutando comprobaciones locales…")
        QtWidgets.QApplication.processEvents()
        self.runner = PreflightRunner(self.main)
        try:
            self.report = self.runner.run()
            self.populate()
        except Exception:
            self.report = {
                "summary": {"passed": False, "blocking_failures": 1, "warnings": 0},
                "checks": [asdict(CheckResult("Preflight", False, traceback.format_exc()))],
            }
            self.populate()
        self.open_button.setEnabled(bool(self.runner and os.path.isdir(self.runner.folder)))
        self.copy_button.setEnabled(self.report is not None)

    def populate(self):
        self.tree.clear()
        for result in self.report.get("checks", []):
            passed = bool(result.get("passed"))
            item = QtWidgets.QTreeWidgetItem([
                str(result.get("name", "")),
                "PASS" if passed else "FAIL",
                str(result.get("detail", "")),
            ])
            color = "#2f7140" if passed else ("#9a6730" if result.get("severity") == "warning" else "#a13f31")
            item.setForeground(1, QtGui.QBrush(QtGui.QColor(color)))
            self.tree.addTopLevelItem(item)
        summary = self.report.get("summary", {})
        passed = bool(summary.get("passed"))
        text = (
            f"{'PRE-FLIGHT APROBADO' if passed else 'PRE-FLIGHT BLOQUEADO'} · "
            f"{summary.get('blocking_failures', 0)} bloqueo(s) · "
            f"{summary.get('warnings', 0)} advertencia(s)"
        )
        if self.runner:
            text += f" · reporte: {self.runner.report_path}"
        self.summary.setText(text)
        self.summary.setProperty("state", "ok" if passed else "error")
        self.summary.style().unpolish(self.summary)
        self.summary.style().polish(self.summary)

    def open_folder(self):
        if self.runner and os.path.isdir(self.runner.folder):
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(self.runner.folder))

    def copy_summary(self):
        if self.report is not None:
            QtWidgets.QApplication.clipboard().setText(
                json.dumps(self.report, ensure_ascii=False, indent=2)
            )


def _install_page(main):
    global _page
    tabs = main.findChild(QtWidgets.QTabWidget, _VERIFICATION_TABS)
    if tabs is None:
        return None
    if _page is None:
        _page = tabs.findChild(QtWidgets.QWidget, _PREFLIGHT_PAGE)
    if _page is None:
        _page = PreflightPage(main, tabs)
        tabs.addTab(_page, "Preflight")
    return _page


def _apply_style(main):
    marker = "/* SolidFreeCAD alpha12 runtime preflight */"
    if marker in main.styleSheet():
        return
    main.setStyleSheet(main.styleSheet() + marker + """
        QWidget#SolidFreeCADAlpha12PreflightPage { background: #f5f7f8; }
        QTreeWidget#SolidFreeCADAlpha12PreflightTree { background: #ffffff; border: 1px solid #b8c4ca; }
        QLabel#SolidFreeCADAlpha12PreflightSummary { padding: 7px; background: #e8f1f6; color: #315a70; }
        QLabel#SolidFreeCADAlpha12PreflightSummary[state="ok"] { background: #dff1e4; color: #245f35; }
        QLabel#SolidFreeCADAlpha12PreflightSummary[state="error"] { background: #f7ded8; color: #8d3528; }
        QPushButton#SolidFreeCADAlpha12Run { font-weight: 700; min-height: 30px; }
        QStatusBar QLabel#SolidFreeCADAlpha12Status { color: #315f74; font-weight: 700; padding: 0 8px; }
    """)


def show_workspace():
    result = show_alpha11_workspace()
    main = Gui.getMainWindow()
    _apply_style(main)
    _install_page(main)
    status = main.findChild(QtWidgets.QLabel, _STATUS)
    if status is None:
        status = QtWidgets.QLabel()
        status.setObjectName(_STATUS)
        main.statusBar().addPermanentWidget(status)
    status.setText("SolidFreeCAD alpha.12 · preflight local disponible · ejecutable aún bloqueado")
    status.show()
    main.setWindowTitle("SolidFreeCAD Desktop alpha.12 · Runtime Preflight Source")
    return result


def hide_workspace():
    hide_alpha11_workspace()
    main = Gui.getMainWindow()
    status = main.findChild(QtWidgets.QLabel, _STATUS)
    if status is not None:
        status.hide()
