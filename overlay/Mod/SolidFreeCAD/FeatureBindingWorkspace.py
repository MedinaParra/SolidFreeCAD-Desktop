"""SolidFreeCAD alpha.10 native feature binding workspace.

This source-only layer builds on alpha.9 and closes a major interaction gap:
geometric collectors can write to compatible native FreeCAD Link/LinkSub
properties, enum end conditions come from the runtime itself, and preview
recomputes are debounced. It does not create parallel geometry or packaging.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from SolidFreeCAD.ClassicWorkspace import _icon
from SolidFreeCAD.FeatureManagerWorkspace import (
    _active_feature,
    _feature_kind,
    hide_workspace as hide_alpha9_workspace,
    show_workspace as show_alpha9_workspace,
)

_OPERATION_PAGE = "SolidFreeCADAlpha8OperationPage"
_BINDING_PANEL = "SolidFreeCADAlpha10BindingPanel"
_END_CONDITION = "SolidFreeCADAlpha10EndCondition"
_BINDING_LIST = "SolidFreeCADAlpha10BindingList"
_READINESS = "SolidFreeCADAlpha10Readiness"
_STATUS = "SolidFreeCADAlpha10Status"

_controller = None


@dataclass(frozen=True)
class SelectionRef:
    object_name: str
    object_label: str
    subelements: tuple[str, ...]

    @property
    def display(self) -> str:
        if self.subelements:
            return f"{self.object_label} · {', '.join(self.subelements)}"
        return self.object_label


def _selection_refs() -> list[SelectionRef]:
    values: list[SelectionRef] = []
    for entry in Gui.Selection.getSelectionEx():
        obj = getattr(entry, "Object", None)
        if obj is None:
            continue
        values.append(
            SelectionRef(
                object_name=obj.Name,
                object_label=getattr(obj, "Label", obj.Name),
                subelements=tuple(getattr(entry, "SubElementNames", ()) or ()),
            )
        )
    return values


def _property_type(obj, name: str) -> str:
    try:
        return obj.getTypeIdOfProperty(name)
    except Exception:
        return ""


def _property_exists(obj, name: str) -> bool:
    return obj is not None and name in getattr(obj, "PropertiesList", [])


def _enum_values(obj, name: str) -> list[str]:
    try:
        values = obj.getEnumerationsOfProperty(name)
        return [str(value) for value in values]
    except Exception:
        return []


def _document_object(ref: SelectionRef):
    doc = App.ActiveDocument
    return doc.getObject(ref.object_name) if doc is not None else None


def _copy_property(value):
    """Return a conservative restorable snapshot for common native properties."""
    if hasattr(value, "Value"):
        return float(value.Value)
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, tuple):
        return tuple(value)
    if isinstance(value, list):
        return list(value)
    return value


class PreviewScheduler(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(120)
        self.timer.timeout.connect(self.recompute)

    def request(self):
        self.timer.start()

    @staticmethod
    def recompute():
        doc = App.ActiveDocument
        if doc is None:
            return
        try:
            doc.recompute()
        except Exception as exc:
            App.Console.PrintError(f"SolidFreeCAD alpha.10 preview: {exc}\n")


class FeatureSession:
    """Track a small, explicit property snapshot without replacing native tasks."""

    TRACKED = (
        "Type", "Length", "Length2", "Reversed", "Midplane", "Offset",
        "TaperAngle", "Angle", "Radius", "Size", "Size2", "Diameter",
        "Depth", "Profile", "Base", "ReferenceAxis", "Axis", "UpToFace",
    )

    def __init__(self):
        self.object_name = ""
        self.values: dict[str, object] = {}

    def capture(self, obj):
        name = getattr(obj, "Name", "") if obj is not None else ""
        if name == self.object_name:
            return
        self.object_name = name
        self.values = {}
        if obj is None:
            return
        for prop in self.TRACKED:
            if not _property_exists(obj, prop):
                continue
            try:
                self.values[prop] = _copy_property(getattr(obj, prop))
            except Exception:
                pass

    def restore(self, obj) -> tuple[int, list[str]]:
        if obj is None or getattr(obj, "Name", "") != self.object_name:
            return 0, ["La operación activa cambió; no se restauró la sesión anterior."]
        restored = 0
        errors: list[str] = []
        doc = App.ActiveDocument
        if doc is None:
            return 0, ["No existe un documento activo."]
        try:
            doc.openTransaction("Restaurar definición alpha.10")
            for prop, value in self.values.items():
                try:
                    setattr(obj, prop, value)
                    restored += 1
                except Exception as exc:
                    errors.append(f"{prop}: {exc}")
            doc.recompute()
            doc.commitTransaction()
        except Exception as exc:
            try:
                doc.abortTransaction()
            except Exception:
                pass
            errors.append(str(exc))
        return restored, errors


class NativeBindingAdapter:
    """Bind current selection only to compatible properties exposed by FreeCAD."""

    ROLE_PROPERTIES = {
        "profile": ("Profile", "Base"),
        "axis": ("ReferenceAxis", "Axis", "AxisLink"),
        "limit": ("UpToFace", "Face", "Support"),
        "edges": ("Base", "Edges"),
        "points": ("Profile", "Base"),
    }

    @staticmethod
    def candidate_property(obj, role: str) -> str | None:
        for name in NativeBindingAdapter.ROLE_PROPERTIES.get(role, ()):
            if not _property_exists(obj, name):
                continue
            type_id = _property_type(obj, name)
            if any(token in type_id for token in ("PropertyLink", "PropertyLinkSub")):
                return name
        return None

    @staticmethod
    def bind(obj, role: str, refs: Iterable[SelectionRef]) -> tuple[bool, str]:
        refs = list(refs)
        if obj is None:
            return False, "No hay una operación activa."
        prop = NativeBindingAdapter.candidate_property(obj, role)
        if prop is None:
            return False, f"La operación no expone un vínculo nativo compatible para {role}."
        if not refs:
            return False, "Seleccione geometría antes de capturarla."

        type_id = _property_type(obj, prop)
        resolved = [(ref, _document_object(ref)) for ref in refs]
        resolved = [(ref, source) for ref, source in resolved if source is not None]
        if not resolved:
            return False, "La selección ya no pertenece al documento activo."

        try:
            if "PropertyLinkSubList" in type_id:
                value = [
                    (source, list(ref.subelements))
                    for ref, source in resolved
                    if ref.subelements
                ]
                if not value:
                    return False, f"{prop} requiere caras, aristas o vértices."
            elif "PropertyLinkSub" in type_id:
                ref, source = resolved[0]
                value = (source, list(ref.subelements))
            elif "PropertyLinkList" in type_id:
                value = [source for _ref, source in resolved]
            elif "PropertyLink" in type_id:
                value = resolved[0][1]
            else:
                return False, f"Tipo de vínculo no soportado de forma segura: {type_id}."

            doc = App.ActiveDocument
            doc.openTransaction(f"Vincular {prop}")
            setattr(obj, prop, value)
            doc.recompute()
            doc.commitTransaction()
            return True, f"{prop} vinculado con {len(resolved)} selección(es)."
        except Exception as exc:
            try:
                App.ActiveDocument.abortTransaction()
            except Exception:
                pass
            return False, f"FreeCAD rechazó el vínculo {prop}: {exc}"


class EndConditionEditor(QtWidgets.QGroupBox):
    def __init__(self, scheduler: PreviewScheduler, parent=None):
        super().__init__("Condición final nativa", parent)
        self.setObjectName(_END_CONDITION)
        self.scheduler = scheduler
        self._object = None
        self._updating = False
        layout = QtWidgets.QVBoxLayout(self)
        self.info = QtWidgets.QLabel(
            "Las opciones se leen desde la propiedad enumerada del objeto nativo."
        )
        self.info.setWordWrap(True)
        layout.addWidget(self.info)
        self.combo = QtWidgets.QComboBox()
        self.combo.currentIndexChanged.connect(self.apply)
        layout.addWidget(self.combo)
        self.hide()

    def set_object(self, obj):
        self._object = obj
        self._updating = True
        self.combo.clear()
        if obj is None or not _property_exists(obj, "Type"):
            self.hide()
            self._updating = False
            return
        values = _enum_values(obj, "Type")
        if not values:
            self.hide()
            self._updating = False
            return
        self.combo.addItems(values)
        try:
            current = str(getattr(obj, "Type"))
            index = self.combo.findText(current)
            if index < 0:
                raw = int(getattr(obj, "Type"))
                index = raw if 0 <= raw < len(values) else 0
            self.combo.setCurrentIndex(index)
        except Exception:
            self.combo.setCurrentIndex(0)
        self.show()
        self._updating = False

    def apply(self, index):
        if self._updating or self._object is None or index < 0:
            return
        text = self.combo.itemText(index)
        doc = App.ActiveDocument
        if doc is None:
            return
        try:
            doc.openTransaction("Cambiar condición final")
            try:
                setattr(self._object, "Type", text)
            except Exception:
                setattr(self._object, "Type", index)
            doc.commitTransaction()
            self.scheduler.request()
        except Exception as exc:
            try:
                doc.abortTransaction()
            except Exception:
                pass
            App.Console.PrintError(f"SolidFreeCAD alpha.10 end condition: {exc}\n")


class BindingPanel(QtWidgets.QGroupBox):
    ROLE_LABELS = {
        "profile": "Perfil",
        "axis": "Eje",
        "limit": "Cara límite",
        "edges": "Aristas",
        "points": "Puntos",
    }

    def __init__(self, parent=None):
        super().__init__("Entradas de la operación", parent)
        self.setObjectName(_BINDING_PANEL)
        self._object = None
        self.scheduler = PreviewScheduler(self)
        self.session = FeatureSession()
        root = QtWidgets.QVBoxLayout(self)

        self.readiness = QtWidgets.QLabel("Seleccione una operación nativa.")
        self.readiness.setObjectName(_READINESS)
        self.readiness.setWordWrap(True)
        root.addWidget(self.readiness)

        self.end_condition = EndConditionEditor(self.scheduler, self)
        root.addWidget(self.end_condition)

        self.list = QtWidgets.QListWidget()
        self.list.setObjectName(_BINDING_LIST)
        self.list.setMaximumHeight(100)
        root.addWidget(self.list)

        grid = QtWidgets.QGridLayout()
        self.buttons: dict[str, QtWidgets.QPushButton] = {}
        for index, role in enumerate(("profile", "axis", "limit", "edges", "points")):
            button = QtWidgets.QPushButton(f"Capturar {self.ROLE_LABELS[role]}")
            button.setIcon(_icon("propertymanager/aceptar.svg"))
            button.clicked.connect(lambda _checked=False, value=role: self.bind(value))
            grid.addWidget(button, index // 2, index % 2)
            self.buttons[role] = button
        root.addLayout(grid)

        row = QtWidgets.QHBoxLayout()
        refresh = QtWidgets.QPushButton("Actualizar selección")
        refresh.clicked.connect(self.refresh_selection)
        row.addWidget(refresh)
        restore = QtWidgets.QPushButton("Restaurar sesión")
        restore.setIcon(_icon("propertymanager/cancelar.svg"))
        restore.clicked.connect(self.restore_session)
        row.addWidget(restore)
        root.addLayout(row)

        self.message = QtWidgets.QLabel()
        self.message.setObjectName("SFCAlpha10Message")
        self.message.setWordWrap(True)
        root.addWidget(self.message)

    def set_object(self, obj):
        self._object = obj
        self.session.capture(obj)
        self.end_condition.set_object(obj)
        kind = _feature_kind(obj)
        roles = {
            "pad": {"profile", "limit"},
            "pocket": {"profile", "limit"},
            "revolution": {"profile", "axis"},
            "fillet": {"edges"},
            "chamfer": {"edges"},
            "hole": {"profile", "points", "limit"},
        }.get(kind, set())
        for role, button in self.buttons.items():
            prop = NativeBindingAdapter.candidate_property(obj, role) if role in roles else None
            button.setVisible(role in roles)
            button.setEnabled(prop is not None)
            button.setToolTip(
                f"Escribirá la selección en {prop}." if prop else "La operación no expone un vínculo compatible."
            )
        self.refresh_selection()
        self.update_readiness(kind)

    def refresh_selection(self):
        refs = _selection_refs()
        self.list.clear()
        for ref in refs[:20]:
            self.list.addItem(ref.display)
        if not refs:
            item = QtWidgets.QListWidgetItem("Sin selección geométrica")
            item.setForeground(QtGui.QBrush(QtGui.QColor("#73818a")))
            self.list.addItem(item)

    def bind(self, role: str):
        ok, message = NativeBindingAdapter.bind(self._object, role, _selection_refs())
        self.message.setText(("✓ " if ok else "⚠ ") + message)
        self.message.setProperty("result", "ok" if ok else "warning")
        self.message.style().unpolish(self.message)
        self.message.style().polish(self.message)
        self.update_readiness(_feature_kind(self._object))

    def restore_session(self):
        count, errors = self.session.restore(self._object)
        text = f"Se restauraron {count} propiedades de la sesión."
        if errors:
            text += " " + " | ".join(errors[:3])
        self.message.setText(text)
        self.end_condition.set_object(self._object)
        self.update_readiness(_feature_kind(self._object))

    def update_readiness(self, kind: str):
        obj = self._object
        if obj is None:
            self.readiness.setText("Sin operación activa.")
            self.readiness.setProperty("state", "idle")
            return
        required_roles = {
            "pad": ("profile",),
            "pocket": ("profile",),
            "revolution": ("profile", "axis"),
            "fillet": ("edges",),
            "chamfer": ("edges",),
            "hole": ("profile",),
        }.get(kind, ())
        missing = []
        for role in required_roles:
            prop = NativeBindingAdapter.candidate_property(obj, role)
            if prop is None:
                missing.append(self.ROLE_LABELS[role])
                continue
            try:
                value = getattr(obj, prop)
                if value in (None, "", [], ()):
                    missing.append(self.ROLE_LABELS[role])
            except Exception:
                missing.append(self.ROLE_LABELS[role])
        if missing:
            self.readiness.setText("Faltan entradas: " + ", ".join(missing))
            self.readiness.setProperty("state", "warning")
        else:
            self.readiness.setText("Entradas nativas disponibles para previsualizar y aceptar.")
            self.readiness.setProperty("state", "ok")
        self.readiness.style().unpolish(self.readiness)
        self.readiness.style().polish(self.readiness)


class Alpha10Controller(QtCore.QObject):
    def __init__(self, main, panel):
        super().__init__(main)
        self.main = main
        self.panel = panel
        self.signature = None
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(280)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh(force=True)

    def refresh(self, force=False):
        obj = _active_feature()
        selection = tuple((ref.object_name, ref.subelements) for ref in _selection_refs())
        signature = (getattr(obj, "Name", ""), _feature_kind(obj), selection)
        if not force and signature == self.signature:
            return
        self.signature = signature
        self.panel.set_object(obj)
        status = self.main.findChild(QtWidgets.QLabel, _STATUS)
        if status is None:
            status = QtWidgets.QLabel()
            status.setObjectName(_STATUS)
            self.main.statusBar().addPermanentWidget(status)
        status.setText(
            f"SolidFreeCAD alpha.10 · {_feature_kind(obj)} · vínculos nativos · source-only"
            if obj is not None
            else "SolidFreeCAD alpha.10 · esperando operación · sin ejecutable"
        )
        status.show()


def _install_panel(main):
    page = main.findChild(QtWidgets.QWidget, _OPERATION_PAGE)
    if page is None or page.layout() is None:
        return None
    existing = page.findChild(QtWidgets.QGroupBox, _BINDING_PANEL)
    if existing is not None:
        return existing
    panel = BindingPanel(page)
    page.layout().insertWidget(6, panel)
    return panel


def _apply_style(main):
    marker = "/* SolidFreeCAD alpha10 native bindings */"
    if marker in main.styleSheet():
        return
    main.setStyleSheet(main.styleSheet() + marker + """
        QGroupBox#SolidFreeCADAlpha10BindingPanel {
            font-weight: 600; border: 1px solid #9eafb9; margin-top: 8px; background: #f7f9fa;
        }
        QLabel#SolidFreeCADAlpha10Readiness { padding: 6px; border-radius: 2px; }
        QLabel#SolidFreeCADAlpha10Readiness[state="idle"] { background: #e7ebee; color: #5f6b72; }
        QLabel#SolidFreeCADAlpha10Readiness[state="ok"] { background: #dff1e4; color: #245f35; }
        QLabel#SolidFreeCADAlpha10Readiness[state="warning"] { background: #fff0cb; color: #76561e; }
        QListWidget#SolidFreeCADAlpha10BindingList { background: #ffffff; border: 1px solid #bdc7cd; }
        QLabel#SFCAlpha10Message[result="ok"] { background: #dff1e4; color: #245f35; padding: 5px; }
        QLabel#SFCAlpha10Message[result="warning"] { background: #fae1da; color: #843a2c; padding: 5px; }
        QStatusBar QLabel#SolidFreeCADAlpha10Status { color: #2d6078; font-weight: 700; padding: 0 8px; }
    """)


def show_workspace():
    global _controller
    result = show_alpha9_workspace()
    main = Gui.getMainWindow()
    _apply_style(main)
    panel = _install_panel(main)
    if panel is not None:
        if _controller is None:
            _controller = Alpha10Controller(main, panel)
        else:
            _controller.timer.start()
            _controller.refresh(force=True)
    main.setWindowTitle("SolidFreeCAD Desktop alpha.10 · Native Bindings Prototype")
    return result


def hide_workspace():
    hide_alpha9_workspace()
    main = Gui.getMainWindow()
    if _controller is not None:
        _controller.timer.stop()
    status = main.findChild(QtWidgets.QLabel, _STATUS)
    if status is not None:
        status.hide()
