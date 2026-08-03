"""SolidFreeCAD alpha.14 guided physical acceptance recorder.

This source-only layer guides a real Windows modeling session and records local
JSON and PNG evidence. It does not create geometry on behalf of the user and it
does not compile, package or publish an executable.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
import re
import tempfile

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from SolidFreeCAD.InteractionWorkspace import _in_edit_object
from SolidFreeCAD.RuntimeStabilityWorkspaceCompat import (
    hide_workspace as hide_alpha13_workspace,
    show_workspace as show_alpha13_workspace,
)

_ACCEPTANCE_PAGE = "SolidFreeCADAlpha14AcceptancePage"
_ACCEPTANCE_TREE = "SolidFreeCADAlpha14AcceptanceTree"
_ACCEPTANCE_SUMMARY = "SolidFreeCADAlpha14AcceptanceSummary"
_ACCEPTANCE_START = "SolidFreeCADAlpha14Start"
_ACCEPTANCE_CAPTURE = "SolidFreeCADAlpha14Capture"
_STATUS = "SolidFreeCADAlpha14Status"
_VERIFICATION_TABS = "SolidFreeCADAlpha11VerificationTabs"

_page = None


@dataclass(frozen=True)
class AcceptanceDefinition:
    key: str
    title: str
    instruction: str
    detector: str
    manual: bool = False


@dataclass
class AcceptanceRecord:
    key: str
    title: str
    state: str = "pending"
    detail: str = ""
    captured_at: str = ""
    screenshot: str = ""
    snapshot: dict = field(default_factory=dict)


_DEFINITIONS = (
    AcceptanceDefinition("body", "Crear pieza y Body", "Cree una pieza con un Body activo.", "body"),
    AcceptanceDefinition("sketch", "Crear croquis", "Cree un croquis dentro del Body.", "sketch"),
    AcceptanceDefinition("pad", "Crear saliente", "Genere un Saliente/Base desde el croquis.", "pad"),
    AcceptanceDefinition("edit-pad", "Editar saliente", "Entre a editar el Saliente y cambie una dimensión.", "edit-pad"),
    AcceptanceDefinition("pocket", "Crear corte", "Cree un Corte extruido que retire material.", "pocket"),
    AcceptanceDefinition("revolution", "Crear revolución", "Cree o edite una Revolución usando un eje nativo.", "revolution"),
    AcceptanceDefinition("fillet", "Crear redondeo", "Seleccione aristas y cree un Redondeo.", "fillet"),
    AcceptanceDefinition("chamfer", "Crear chaflán", "Seleccione aristas y cree un Chaflán.", "chamfer"),
    AcceptanceDefinition("save", "Guardar FCStd", "Guarde el documento en una ruta local.", "save"),
    AcceptanceDefinition("reopen", "Cerrar y reabrir", "Cierre y reabra el mismo FCStd; después capture este paso.", "reopen"),
    AcceptanceDefinition("undo-redo", "Probar Undo y Redo", "Modifique un parámetro, deshaga, rehaga y confirme visualmente.", "manual", True),
    AcceptanceDefinition("dpi-100", "Escala Windows 100%", "Revise paneles, menús y controles a 100%.", "manual", True),
    AcceptanceDefinition("dpi-125", "Escala Windows 125%", "Revise paneles, menús y controles a 125%.", "manual", True),
    AcceptanceDefinition("dpi-150", "Escala Windows 150%", "Revise paneles, menús y controles a 150%.", "manual", True),
    AcceptanceDefinition("dpi-200", "Escala Windows 200%", "Revise paneles, menús y controles a 200%.", "manual", True),
    AcceptanceDefinition("long-session", "Sesión prolongada", "Trabaje al menos 45 minutos sin paneles duplicados ni atajos capturados.", "manual", True),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _token_match(obj, *tokens: str) -> bool:
    haystack = " ".join((getattr(obj, "TypeId", ""), getattr(obj, "Name", ""), getattr(obj, "Label", ""))).lower()
    return any(token.lower() in haystack for token in tokens)


def _selection_snapshot() -> list[dict]:
    values = []
    for entry in Gui.Selection.getSelectionEx():
        obj = getattr(entry, "Object", None)
        if obj is None:
            continue
        values.append({
            "name": obj.Name,
            "label": getattr(obj, "Label", obj.Name),
            "type_id": getattr(obj, "TypeId", ""),
            "subelements": list(getattr(entry, "SubElementNames", ()) or ()),
        })
    return values


def _document_snapshot() -> dict:
    doc = App.ActiveDocument
    if doc is None:
        return {"active_document": None, "objects": [], "selection": _selection_snapshot()}
    objects = []
    for obj in doc.Objects:
        shape = getattr(obj, "Shape", None)
        shape_valid = None
        volume = None
        try:
            if shape is not None and not shape.isNull():
                shape_valid = bool(shape.isValid())
                volume = float(shape.Volume)
        except Exception:
            pass
        objects.append({
            "name": obj.Name,
            "label": obj.Label or obj.Name,
            "type_id": obj.TypeId,
            "visible": bool(getattr(getattr(obj, "ViewObject", None), "Visibility", True)),
            "shape_valid": shape_valid,
            "volume": volume,
        })
    return {
        "active_document": doc.Name,
        "label": doc.Label,
        "file_name": getattr(doc, "FileName", ""),
        "objects": objects,
        "selection": _selection_snapshot(),
    }


class AcceptanceDetector:
    def __init__(self):
        self.saved_file = ""
        self.saved_document_name = ""
        self.saw_document_absent = False

    def evaluate(self, definition: AcceptanceDefinition) -> tuple[bool, str]:
        if definition.manual:
            return False, "Requiere confirmación manual con evidencia."
        doc = App.ActiveDocument
        objects = list(doc.Objects) if doc is not None else []
        key = definition.detector
        if key == "body":
            found = any("PartDesign::Body" in obj.TypeId for obj in objects)
            return found, "Body detectado" if found else "No se detecta un Body"
        if key == "sketch":
            found = any("Sketcher::SketchObject" in obj.TypeId for obj in objects)
            return found, "Croquis detectado" if found else "No se detecta un croquis"
        if key == "pad":
            found = any(_token_match(obj, "pad", "saliente") for obj in objects)
            return found, "Saliente detectado" if found else "No se detecta un Saliente/Pad"
        if key == "edit-pad":
            obj = _in_edit_object()
            found = obj is not None and _token_match(obj, "pad", "saliente")
            return found, f"Editando {obj.Label or obj.Name}" if found else "El Saliente no está en edición"
        if key == "pocket":
            found = any(_token_match(obj, "pocket", "corte") for obj in objects)
            return found, "Corte detectado" if found else "No se detecta un Pocket/Corte"
        if key == "revolution":
            found = any(_token_match(obj, "revolution", "revolución", "revolucion") for obj in objects)
            return found, "Revolución detectada" if found else "No se detecta una Revolución"
        if key == "fillet":
            found = any(_token_match(obj, "fillet", "redonde") for obj in objects)
            return found, "Redondeo detectado" if found else "No se detecta un Redondeo"
        if key == "chamfer":
            found = any(_token_match(obj, "chamfer", "chaflán", "chaflan") for obj in objects)
            return found, "Chaflán detectado" if found else "No se detecta un Chaflán"
        if key == "save":
            file_name = getattr(doc, "FileName", "") if doc is not None else ""
            found = bool(file_name and os.path.isfile(file_name))
            if found:
                self.saved_file = os.path.abspath(file_name)
                self.saved_document_name = doc.Name
            return found, self.saved_file if found else "El documento todavía no está guardado"
        if key == "reopen":
            if not self.saved_file:
                return False, "Capture primero el paso Guardar FCStd"
            if doc is None:
                self.saw_document_absent = True
                return False, "Documento cerrado; vuelva a abrir el FCStd"
            current = os.path.abspath(getattr(doc, "FileName", "")) if getattr(doc, "FileName", "") else ""
            changed_instance = self.saw_document_absent or doc.Name != self.saved_document_name
            found = current == self.saved_file and changed_instance
            return found, current if found else "Aún no se confirma cierre y reapertura del mismo archivo"
        return False, "Detector no disponible"


class AcceptanceSession:
    def __init__(self, main):
        self.main = main
        self.detector = AcceptanceDetector()
        self.folder = ""
        self.report_path = ""
        self.started_at = ""
        self.finished_at = ""
        self.records = {definition.key: AcceptanceRecord(definition.key, definition.title) for definition in _DEFINITIONS}
        self.runtime = {}

    def start(self, folder: str):
        self.folder = folder
        os.makedirs(self.folder, exist_ok=True)
        self.report_path = os.path.join(self.folder, "solidfreecad-alpha14-acceptance.json")
        self.started_at = _utc_now()
        self.finished_at = ""
        self.detector = AcceptanceDetector()
        self.records = {definition.key: AcceptanceRecord(definition.key, definition.title) for definition in _DEFINITIONS}
        self.runtime = {
            "freecad": list(App.Version()),
            "qt": QtCore.qVersion(),
            "window": [self.main.width(), self.main.height()],
            "device_pixel_ratio": float(getattr(self.main, "devicePixelRatioF", lambda: 1.0)()),
        }
        self.write_report()

    def capture(self, definition: AcceptanceDefinition, manual_state: str | None = None, note: str = ""):
        if not self.folder:
            raise RuntimeError("La sesión de aceptación no está iniciada.")
        detected, detail = self.detector.evaluate(definition)
        if manual_state is not None:
            state = manual_state
            detail = note or ("Confirmado manualmente" if state == "passed" else "Marcado como fallo")
        else:
            state = "passed" if detected else "failed"
        safe_key = re.sub(r"[^a-zA-Z0-9_-]+", "-", definition.key)
        screenshot = os.path.join(self.folder, f"alpha14-{safe_key}.png")
        saved = False
        try:
            saved = bool(self.main.grab().save(screenshot))
        except Exception:
            saved = False
        record = self.records[definition.key]
        record.state = state
        record.detail = detail
        record.captured_at = _utc_now()
        record.screenshot = screenshot if saved else ""
        record.snapshot = _document_snapshot()
        self.write_report()
        return record

    def finish(self):
        self.finished_at = _utc_now()
        self.write_report()
        return self.summary()

    def summary(self):
        values = list(self.records.values())
        passed = sum(record.state == "passed" for record in values)
        failed = sum(record.state == "failed" for record in values)
        pending = sum(record.state == "pending" for record in values)
        return {
            "passed": failed == 0 and pending == 0,
            "steps": len(values),
            "passed_steps": passed,
            "failed_steps": failed,
            "pending_steps": pending,
        }

    def write_report(self):
        if not self.report_path:
            return
        payload = {
            "schema": "solidfreecad-acceptance-1",
            "version": "0.1.0-alpha.14-interactive-acceptance",
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "folder": self.folder,
            "runtime": self.runtime,
            "summary": self.summary(),
            "steps": [asdict(self.records[definition.key]) for definition in _DEFINITIONS],
        }
        with open(self.report_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)


class AcceptancePage(QtWidgets.QWidget):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.session = AcceptanceSession(main)
        self.setObjectName(_ACCEPTANCE_PAGE)
        root = QtWidgets.QVBoxLayout(self)
        self.summary = QtWidgets.QLabel(
            "Inicie una sesión física. Cada paso debe capturarse con el estado real del modelo."
        )
        self.summary.setObjectName(_ACCEPTANCE_SUMMARY)
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setObjectName(_ACCEPTANCE_TREE)
        self.tree.setHeaderLabels(["Paso", "Estado", "Detección / evidencia"])
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        root.addWidget(self.tree, 1)
        for definition in _DEFINITIONS:
            item = QtWidgets.QTreeWidgetItem([definition.title, "Pendiente", definition.instruction])
            item.setData(0, QtCore.Qt.UserRole, definition.key)
            item.setToolTip(0, definition.instruction)
            self.tree.addTopLevelItem(item)
        row = QtWidgets.QGridLayout()
        start = QtWidgets.QPushButton("Iniciar sesión")
        start.setObjectName(_ACCEPTANCE_START)
        start.clicked.connect(self.start_session)
        row.addWidget(start, 0, 0)
        capture = QtWidgets.QPushButton("Capturar paso")
        capture.setObjectName(_ACCEPTANCE_CAPTURE)
        capture.clicked.connect(self.capture_selected)
        row.addWidget(capture, 0, 1)
        manual_pass = QtWidgets.QPushButton("Confirmar manualmente")
        manual_pass.clicked.connect(self.manual_pass)
        row.addWidget(manual_pass, 0, 2)
        fail = QtWidgets.QPushButton("Marcar fallo")
        fail.clicked.connect(self.mark_failed)
        row.addWidget(fail, 1, 0)
        finish = QtWidgets.QPushButton("Finalizar")
        finish.clicked.connect(self.finish_session)
        row.addWidget(finish, 1, 1)
        self.open_button = QtWidgets.QPushButton("Abrir evidencia")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_folder)
        row.addWidget(self.open_button, 1, 2)
        root.addLayout(row)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(800)
        self.timer.timeout.connect(self.preview_selected)
        self.timer.start()

    def selected_definition(self):
        item = self.tree.currentItem()
        if item is None:
            return None, None
        key = item.data(0, QtCore.Qt.UserRole)
        definition = next((entry for entry in _DEFINITIONS if entry.key == key), None)
        return definition, item

    def start_session(self):
        default = os.path.join(
            os.path.expanduser("~"),
            "Documents",
            "SolidFreeCAD-Acceptance-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
        )
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Carpeta de evidencia", os.path.dirname(default))
        if not folder:
            folder = tempfile.mkdtemp(prefix="SolidFreeCAD-alpha14-")
        else:
            folder = os.path.join(folder, os.path.basename(default))
        self.session.start(folder)
        self.open_button.setEnabled(True)
        self.summary.setText(f"Sesión iniciada · evidencia local: {folder}")
        self.refresh_tree()

    def capture_selected(self):
        definition, _item = self.selected_definition()
        if definition is None:
            return
        if definition.manual:
            self.summary.setText("Este paso exige confirmación manual o marcado de fallo.")
            return
        try:
            record = self.session.capture(definition)
            self.summary.setText(f"{definition.title}: {record.detail}")
            self.refresh_tree()
        except Exception as exc:
            self.summary.setText(str(exc))

    def manual_pass(self):
        definition, _item = self.selected_definition()
        if definition is None:
            return
        note, accepted = QtWidgets.QInputDialog.getText(
            self, "Confirmación manual", "Evidencia u observación", text=definition.instruction
        )
        if not accepted:
            return
        try:
            self.session.capture(definition, "passed", note.strip())
            self.refresh_tree()
        except Exception as exc:
            self.summary.setText(str(exc))

    def mark_failed(self):
        definition, _item = self.selected_definition()
        if definition is None:
            return
        note, accepted = QtWidgets.QInputDialog.getText(
            self, "Registrar fallo", "Describa el defecto observado"
        )
        if not accepted:
            return
        try:
            self.session.capture(definition, "failed", note.strip() or "Fallo sin detalle")
            self.refresh_tree()
        except Exception as exc:
            self.summary.setText(str(exc))

    def preview_selected(self):
        definition, item = self.selected_definition()
        if definition is None or item is None or definition.manual:
            return
        detected, detail = self.session.detector.evaluate(definition)
        if self.session.records[definition.key].state == "pending":
            item.setText(2, ("Detectable: " if detected else "Pendiente: ") + detail)

    def refresh_tree(self):
        for index, definition in enumerate(_DEFINITIONS):
            item = self.tree.topLevelItem(index)
            record = self.session.records[definition.key]
            label = {"pending": "Pendiente", "passed": "PASS", "failed": "FAIL"}.get(record.state, record.state)
            item.setText(1, label)
            item.setText(2, record.detail or definition.instruction)
            color = {"passed": "#2f7140", "failed": "#a13f31", "pending": "#6f7c84"}[record.state]
            item.setForeground(1, QtGui.QBrush(QtGui.QColor(color)))
        summary = self.session.summary()
        self.summary.setText(
            f"{summary['passed_steps']}/{summary['steps']} aprobados · "
            f"{summary['failed_steps']} fallos · {summary['pending_steps']} pendientes"
        )

    def finish_session(self):
        if not self.session.folder:
            self.summary.setText("Primero inicie una sesión.")
            return
        summary = self.session.finish()
        self.refresh_tree()
        self.summary.setText(
            ("ACEPTACIÓN COMPLETA" if summary["passed"] else "ACEPTACIÓN INCOMPLETA")
            + f" · reporte: {self.session.report_path}"
        )
        self.summary.setProperty("state", "ok" if summary["passed"] else "warning")
        self.summary.style().unpolish(self.summary)
        self.summary.style().polish(self.summary)

    def open_folder(self):
        if self.session.folder and os.path.isdir(self.session.folder):
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(self.session.folder))


def _install_page(main):
    global _page
    tabs = main.findChild(QtWidgets.QTabWidget, _VERIFICATION_TABS)
    if tabs is None:
        return None
    if _page is None:
        _page = tabs.findChild(QtWidgets.QWidget, _ACCEPTANCE_PAGE)
    if _page is None:
        _page = AcceptancePage(main, tabs)
        tabs.addTab(_page, "Aceptación")
    return _page


def _apply_style(main):
    marker = "/* SolidFreeCAD alpha14 interactive acceptance */"
    if marker in main.styleSheet():
        return
    main.setStyleSheet(main.styleSheet() + marker + """
        QWidget#SolidFreeCADAlpha14AcceptancePage { background: #f5f7f8; }
        QTreeWidget#SolidFreeCADAlpha14AcceptanceTree { background: #ffffff; border: 1px solid #b8c4ca; }
        QLabel#SolidFreeCADAlpha14AcceptanceSummary { padding: 7px; background: #e8f1f6; color: #315a70; }
        QLabel#SolidFreeCADAlpha14AcceptanceSummary[state="ok"] { background: #dff1e4; color: #245f35; }
        QLabel#SolidFreeCADAlpha14AcceptanceSummary[state="warning"] { background: #fff0cb; color: #76561e; }
        QPushButton#SolidFreeCADAlpha14Start,
        QPushButton#SolidFreeCADAlpha14Capture { font-weight: 700; min-height: 30px; }
        QStatusBar QLabel#SolidFreeCADAlpha14Status { color: #315f74; font-weight: 700; padding: 0 8px; }
    """)


def show_workspace():
    result = show_alpha13_workspace()
    main = Gui.getMainWindow()
    _apply_style(main)
    _install_page(main)
    status = main.findChild(QtWidgets.QLabel, _STATUS)
    if status is None:
        status = QtWidgets.QLabel()
        status.setObjectName(_STATUS)
        main.statusBar().addPermanentWidget(status)
    status.setText("SolidFreeCAD alpha.14 · aceptación física pendiente · ejecutable bloqueado")
    status.show()
    main.setWindowTitle("SolidFreeCAD Desktop alpha.14 · Interactive Acceptance")
    return result


def hide_workspace():
    hide_alpha13_workspace()
    main = Gui.getMainWindow()
    status = main.findChild(QtWidgets.QLabel, _STATUS)
    if status is not None:
        status.hide()
