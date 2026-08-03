"""SolidFreeCAD alpha.13 runtime stability gate.

This source-only layer runs on top of alpha.12. It validates the supported
runtime baseline, critical widget uniqueness, workspace layout accessibility,
transactions, Undo/Redo, FCStd persistence and active-document restoration.
It does not compile, package or publish an executable.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
import platform
import re
import sys
import tempfile
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from SolidFreeCAD.RuntimePreflightWorkspaceCompat import (
    hide_workspace as hide_alpha12_workspace,
    show_workspace as show_alpha12_workspace,
)
from SolidFreeCAD.WorkspaceRC import _COMMAND_REQUIREMENTS
from SolidFreeCAD.ClassicWorkspace import _first_available

_STABILITY_PAGE = "SolidFreeCADAlpha13StabilityPage"
_STABILITY_TREE = "SolidFreeCADAlpha13StabilityTree"
_STABILITY_SUMMARY = "SolidFreeCADAlpha13StabilitySummary"
_STABILITY_RUN = "SolidFreeCADAlpha13Run"
_STATUS = "SolidFreeCADAlpha13Status"
_VERIFICATION_TABS = "SolidFreeCADAlpha11VerificationTabs"

_page = None


@dataclass
class StabilityResult:
    name: str
    passed: bool
    detail: str
    severity: str = "error"


def _version_tuple(values) -> tuple[int, int, int]:
    numbers: list[int] = []
    for value in values:
        match = re.search(r"\d+", str(value))
        if match:
            numbers.append(int(match.group(0)))
        if len(numbers) == 3:
            break
    return tuple((numbers + [0, 0, 0])[:3])


class RuntimeStabilityRunner:
    MINIMUM_RUNTIME = (1, 1, 3)
    CRITICAL_WIDGETS = (
        (QtWidgets.QDockWidget, "SolidFreeCADClassicCommandManager"),
        (QtWidgets.QDockWidget, "SolidFreeCADFeatureManager"),
        (QtWidgets.QDockWidget, "SolidFreeCADAlpha7TaskPane"),
        (QtWidgets.QToolBar, "SolidFreeCADAlpha7ContextBar"),
        (QtWidgets.QToolBar, "SolidFreeCADAlpha11QuickAccess"),
        (QtWidgets.QFrame, "SolidFreeCADAlpha8ConfirmationCorner"),
        (QtWidgets.QGroupBox, "SolidFreeCADAlpha10BindingPanel"),
        (QtWidgets.QWidget, "SolidFreeCADAlpha11VerificationPage"),
        (QtWidgets.QWidget, "SolidFreeCADAlpha12PreflightPage"),
    )

    def __init__(self, main, folder: str | None = None):
        self.main = main
        self.folder = folder or tempfile.mkdtemp(prefix="SolidFreeCAD-alpha13-")
        os.makedirs(self.folder, exist_ok=True)
        self.report_path = os.path.join(self.folder, "solidfreecad-alpha13-stability.json")
        self.results: list[StabilityResult] = []
        self.runtime: dict[str, object] = {}

    def add(self, name, passed, detail, severity="error"):
        self.results.append(StabilityResult(str(name), bool(passed), str(detail), str(severity)))

    def run(self):
        self.check_runtime_baseline()
        self.check_widget_uniqueness()
        self.check_command_coverage()
        self.check_workspace_preferences()
        self.check_layouts()
        self.check_transaction_roundtrip()
        report = self.build_report()
        with open(self.report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        return report

    def check_runtime_baseline(self):
        freecad_values = list(App.Version())
        version = _version_tuple(freecad_values)
        self.runtime = {
            "freecad": freecad_values,
            "freecad_version": ".".join(str(value) for value in version),
            "minimum_supported": ".".join(str(value) for value in self.MINIMUM_RUNTIME),
            "python": sys.version,
            "qt": QtCore.qVersion(),
            "platform": platform.platform(),
            "executable": App.ConfigGet("ExeName") if hasattr(App, "ConfigGet") else "",
        }
        self.add(
            "Runtime · FreeCAD compatible",
            version >= self.MINIMUM_RUNTIME,
            f"detectado {version}; mínimo {self.MINIMUM_RUNTIME}",
        )
        self.add(
            "Runtime · Python 3",
            sys.version_info.major == 3,
            sys.version.splitlines()[0],
        )
        self.add("Runtime · Qt disponible", bool(QtCore.qVersion()), QtCore.qVersion())

    def check_widget_uniqueness(self):
        for widget_type, object_name in self.CRITICAL_WIDGETS:
            matches = self.main.findChildren(widget_type, object_name)
            self.add(
                f"UI única · {object_name}",
                len(matches) == 1,
                f"instancias={len(matches)}",
            )

    def check_command_coverage(self):
        missing_critical: list[str] = []
        available = 0
        for requirement in _COMMAND_REQUIREMENTS:
            command = _first_available(requirement.candidates)
            if command:
                available += 1
            elif requirement.group in {"Archivo", "Croquis", "Operaciones"}:
                missing_critical.append(f"{requirement.group}/{requirement.label}")
        self.add(
            "Comandos · Cobertura crítica",
            not missing_critical,
            "completa" if not missing_critical else ", ".join(missing_critical),
        )
        self.add(
            "Comandos · Cobertura total",
            available == len(_COMMAND_REQUIREMENTS),
            f"{available}/{len(_COMMAND_REQUIREMENTS)}",
            "warning",
        )

    def check_workspace_preferences(self):
        params = App.ParamGet("User parameter:BaseApp/Preferences/SolidFreeCAD/WorkspaceRC")
        profile = params.GetString("Profile", "Estándar")
        density = params.GetString("Density", "Normal")
        theme = params.GetString("Theme", "Sistema")
        self.add(
            "Preferencias · Perfil",
            profile in {"Portátil", "Estándar", "Pantalla amplia"},
            profile,
        )
        self.add(
            "Preferencias · Densidad",
            density in {"Compacta", "Normal", "Cómoda"},
            density,
        )
        self.add(
            "Preferencias · Tema",
            theme in {"Sistema", "Claro", "Oscuro"},
            theme,
        )

    def check_layouts(self):
        original_size = self.main.size()
        try:
            for width, height in ((1366, 768), (1920, 1080)):
                self.main.resize(width, height)
                QtWidgets.QApplication.processEvents()
                inaccessible: list[str] = []
                for widget_type, object_name in self.CRITICAL_WIDGETS[:5]:
                    widget = self.main.findChild(widget_type, object_name)
                    if widget is None:
                        inaccessible.append(object_name + ":missing")
                        continue
                    if widget.isVisible() and (widget.width() < 80 or widget.height() < 22):
                        inaccessible.append(f"{object_name}:{widget.width()}x{widget.height()}")
                self.add(
                    f"Layout · {width}×{height}",
                    not inaccessible,
                    "accesible" if not inaccessible else " | ".join(inaccessible),
                )
        finally:
            self.main.resize(original_size)
            QtWidgets.QApplication.processEvents()

    def check_transaction_roundtrip(self):
        previous_name = App.ActiveDocument.Name if App.ActiveDocument else ""
        document_name = "SFCAlpha13Transactions"
        path = os.path.join(self.folder, "alpha13-transaction-roundtrip.FCStd")
        try:
            import Part

            if document_name in App.listDocuments():
                App.closeDocument(document_name)
            doc = App.newDocument(document_name)
            feature = doc.addObject("PartDesign::Feature", "TransactionPart")
            feature.Label = "Pieza transaccional"
            feature.addProperty("App::PropertyLength", "TestLength", "Stability")
            feature.TestLength = 10.0
            feature.Shape = Part.makeBox(10.0, 20.0, 5.0)
            doc.recompute()
            base_volume = float(feature.Shape.Volume)

            doc.openTransaction("Alpha13 transaction")
            feature.TestLength = 25.0
            feature.Shape = Part.makeBox(25.0, 20.0, 5.0)
            doc.recompute()
            changed_volume = float(feature.Shape.Volume)
            doc.commitTransaction()

            doc.undo()
            doc.recompute()
            undo_ok = abs(float(feature.TestLength) - 10.0) < 1e-9 and abs(float(feature.Shape.Volume) - base_volume) < 1e-6
            self.add("Transacción · Undo", undo_ok, f"length={float(feature.TestLength):.3f}; volume={float(feature.Shape.Volume):.3f}")

            doc.redo()
            doc.recompute()
            redo_ok = abs(float(feature.TestLength) - 25.0) < 1e-9 and abs(float(feature.Shape.Volume) - changed_volume) < 1e-6
            self.add("Transacción · Redo", redo_ok, f"length={float(feature.TestLength):.3f}; volume={float(feature.Shape.Volume):.3f}")

            doc.saveAs(path)
            self.add("Persistencia · Guardar FCStd", os.path.isfile(path) and os.path.getsize(path) > 0, path)
            App.closeDocument(document_name)

            reopened = App.openDocument(path)
            restored = reopened.getObject("TransactionPart")
            persistence_ok = bool(
                restored
                and abs(float(restored.TestLength) - 25.0) < 1e-9
                and not restored.Shape.isNull()
                and restored.Shape.isValid()
                and abs(float(restored.Shape.Volume) - changed_volume) < 1e-6
            )
            self.add(
                "Persistencia · Reabrir FCStd",
                persistence_ok,
                f"objeto={'sí' if restored else 'no'}; volumen={float(restored.Shape.Volume) if restored else 0.0:.3f}",
            )
            App.closeDocument(reopened.Name)
        except Exception:
            self.add("Transacción · Round trip", False, traceback.format_exc())
        finally:
            if document_name in App.listDocuments():
                try:
                    App.closeDocument(document_name)
                except Exception:
                    pass
            if previous_name and previous_name in App.listDocuments():
                try:
                    App.setActiveDocument(previous_name)
                except Exception:
                    pass
            current = App.ActiveDocument.Name if App.ActiveDocument else ""
            self.add(
                "Sesión · Restaurar documento activo",
                current == previous_name,
                f"antes={previous_name or 'ninguno'}; después={current or 'ninguno'}",
            )

    def build_report(self):
        blocking = [item for item in self.results if not item.passed and item.severity == "error"]
        warnings = [item for item in self.results if not item.passed and item.severity == "warning"]
        return {
            "schema": "solidfreecad-stability-1",
            "version": "0.1.0-alpha.13-runtime-stabilization",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "working_directory": self.folder,
            "runtime": self.runtime,
            "summary": {
                "passed": not blocking,
                "checks": len(self.results),
                "blocking_failures": len(blocking),
                "warnings": len(warnings),
            },
            "checks": [asdict(item) for item in self.results],
        }


class StabilityPage(QtWidgets.QWidget):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.runner: RuntimeStabilityRunner | None = None
        self.report: dict | None = None
        self.setObjectName(_STABILITY_PAGE)
        root = QtWidgets.QVBoxLayout(self)
        self.summary = QtWidgets.QLabel(
            "Comprueba runtime, widgets únicos, layouts, Undo/Redo y persistencia FCStd."
        )
        self.summary.setObjectName(_STABILITY_SUMMARY)
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setObjectName(_STABILITY_TREE)
        self.tree.setHeaderLabels(["Comprobación", "Resultado", "Detalle"])
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        root.addWidget(self.tree, 1)
        row = QtWidgets.QHBoxLayout()
        run_button = QtWidgets.QPushButton("Ejecutar estabilidad")
        run_button.setObjectName(_STABILITY_RUN)
        run_button.clicked.connect(self.run_stability)
        row.addWidget(run_button)
        self.open_button = QtWidgets.QPushButton("Abrir carpeta")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_folder)
        row.addWidget(self.open_button)
        self.copy_button = QtWidgets.QPushButton("Copiar informe")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy_report)
        row.addWidget(self.copy_button)
        root.addLayout(row)

    def run_stability(self):
        self.summary.setText("Ejecutando pruebas de estabilidad…")
        QtWidgets.QApplication.processEvents()
        self.runner = RuntimeStabilityRunner(self.main)
        self.report = self.runner.run()
        self.populate()
        self.open_button.setEnabled(True)
        self.copy_button.setEnabled(True)

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
        self.summary.setText(
            f"{'ESTABILIDAD APROBADA' if passed else 'ESTABILIDAD BLOQUEADA'} · "
            f"{summary.get('blocking_failures', 0)} bloqueo(s) · {summary.get('warnings', 0)} advertencia(s)"
        )
        self.summary.setProperty("state", "ok" if passed else "error")
        self.summary.style().unpolish(self.summary)
        self.summary.style().polish(self.summary)

    def open_folder(self):
        if self.runner and os.path.isdir(self.runner.folder):
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(self.runner.folder))

    def copy_report(self):
        if self.report is not None:
            QtWidgets.QApplication.clipboard().setText(json.dumps(self.report, ensure_ascii=False, indent=2))


def _install_page(main):
    global _page
    tabs = main.findChild(QtWidgets.QTabWidget, _VERIFICATION_TABS)
    if tabs is None:
        return None
    if _page is None:
        _page = tabs.findChild(QtWidgets.QWidget, _STABILITY_PAGE)
    if _page is None:
        _page = StabilityPage(main, tabs)
        tabs.addTab(_page, "Estabilidad")
    return _page


def _apply_style(main):
    marker = "/* SolidFreeCAD alpha13 runtime stability */"
    if marker in main.styleSheet():
        return
    main.setStyleSheet(main.styleSheet() + marker + """
        QWidget#SolidFreeCADAlpha13StabilityPage { background: #f5f7f8; }
        QTreeWidget#SolidFreeCADAlpha13StabilityTree { background: #ffffff; border: 1px solid #b8c4ca; }
        QLabel#SolidFreeCADAlpha13StabilitySummary { padding: 7px; background: #e8f1f6; color: #315a70; }
        QLabel#SolidFreeCADAlpha13StabilitySummary[state="ok"] { background: #dff1e4; color: #245f35; }
        QLabel#SolidFreeCADAlpha13StabilitySummary[state="error"] { background: #f7ded8; color: #8d3528; }
        QPushButton#SolidFreeCADAlpha13Run { font-weight: 700; min-height: 30px; }
        QStatusBar QLabel#SolidFreeCADAlpha13Status { color: #315f74; font-weight: 700; padding: 0 8px; }
    """)


def show_workspace():
    result = show_alpha12_workspace()
    main = Gui.getMainWindow()
    _apply_style(main)
    _install_page(main)
    status = main.findChild(QtWidgets.QLabel, _STATUS)
    if status is None:
        status = QtWidgets.QLabel()
        status.setObjectName(_STATUS)
        main.statusBar().addPermanentWidget(status)
    version = _version_tuple(App.Version())
    status.setText(
        f"SolidFreeCAD alpha.13 · FreeCAD {'.'.join(map(str, version))} · estabilidad pendiente · sin ejecutable"
    )
    status.show()
    main.setWindowTitle("SolidFreeCAD Desktop alpha.13 · Runtime Stabilization")
    return result


def hide_workspace():
    hide_alpha12_workspace()
    main = Gui.getMainWindow()
    status = main.findChild(QtWidgets.QLabel, _STATUS)
    if status is not None:
        status.hide()
