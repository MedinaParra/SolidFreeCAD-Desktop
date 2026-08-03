"""SolidFreeCAD alpha.8 interaction and editing workspace.

The alpha.8 layer builds on the alpha.7 source-only interface and focuses on
interaction maturity: edit-state awareness, a confirmation corner, contextual
operation controls, hierarchical design history, display controls and a
keyboard shortcut palette. All geometry and documents remain native FreeCAD.

This file intentionally contains no build, packaging or executable logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from SolidFreeCAD.ClassicWorkspace import _first_available, _icon, _run_candidates
from SolidFreeCAD.ProfessionalWorkspaceCompat import (
    hide_workspace as hide_alpha7_workspace,
    show_workspace as show_alpha7_workspace,
)

_CONFIRMATION_CORNER = "SolidFreeCADAlpha8ConfirmationCorner"
_OPERATION_PAGE = "SolidFreeCADAlpha8OperationPage"
_OPERATION_TABS = "SolidFreeCADAlpha7TaskTabs"
_FEATURE_TREE = "SolidFreeCADFeatureTree"
_COMMAND_TABS = "SolidFreeCADCommandTabs"
_CONTEXT_BAR = "SolidFreeCADAlpha7ContextBar"
_STATUS = "SolidFreeCADAlpha8Status"
_MODE_BADGE = "SolidFreeCADAlpha8ModeBadge"
_DISPLAY_COMBO = "SolidFreeCADAlpha8DisplayStyle"
_SHORTCUT_PALETTE = "SolidFreeCADAlpha8ShortcutPalette"

_controller = None
_hierarchy = None
_operation_page = None
_confirmation_corner = None
_shortcuts: list[QtWidgets.QShortcut] = []


@dataclass(frozen=True)
class EditState:
    mode: str
    title: str
    object_name: str = ""
    object_type: str = ""
    message: str = ""
    degrees_of_freedom: int | None = None


def _selected_object():
    selected = Gui.Selection.getSelection()
    return selected[0] if selected else None


def _in_edit_object():
    gui_document = Gui.activeDocument()
    if gui_document is None:
        return None
    try:
        value = gui_document.getInEdit()
    except Exception:
        return None
    if isinstance(value, tuple):
        value = value[0] if value else None
    if value is None:
        return None
    if hasattr(value, "Object"):
        value = value.Object
    if isinstance(value, str) and App.ActiveDocument is not None:
        value = App.ActiveDocument.getObject(value)
    return value if hasattr(value, "TypeId") else None


def _sketch_dof(obj) -> int | None:
    if obj is None or "Sketcher::SketchObject" not in getattr(obj, "TypeId", ""):
        return None
    for accessor in ("getSolverDoFs", "getDOF"):
        method = getattr(obj, accessor, None)
        if callable(method):
            try:
                return int(method())
            except Exception:
                pass
    return None


def _state_from_context() -> EditState:
    editing = _in_edit_object()
    selected = _selected_object()
    obj = editing or selected
    if App.ActiveDocument is None:
        return EditState("idle", "Inicio", message="Cree una pieza o abra un documento.")
    if editing is not None:
        type_id = getattr(editing, "TypeId", "")
        label = editing.Label or editing.Name
        if "Sketcher::SketchObject" in type_id:
            dof = _sketch_dof(editing)
            constraint = (
                "Croquis totalmente definido"
                if dof == 0
                else (f"{dof} grados de libertad" if dof is not None else "Revise cotas y relaciones")
            )
            return EditState(
                "sketch",
                "EDITANDO CROQUIS",
                editing.Name,
                type_id,
                f"{label} · {constraint}",
                dof,
            )
        return EditState(
            "feature",
            "EDITANDO OPERACIÓN",
            editing.Name,
            type_id,
            f"Configure {label} y confirme cuando la previsualización sea correcta.",
        )
    if obj is None:
        return EditState("part", "MODELO", message="Seleccione una operación, cara o croquis.")
    type_id = getattr(obj, "TypeId", "")
    label = obj.Label or obj.Name
    if "Sketcher::SketchObject" in type_id:
        return EditState("sketch-selected", "CROQUIS", obj.Name, type_id, f"{label} listo para editar.")
    if "PartDesign::Feature" in type_id or "Part::Feature" in type_id:
        return EditState("feature-selected", "OPERACIÓN", obj.Name, type_id, f"{label} seleccionado.")
    if "Body" in type_id:
        return EditState("body", "PIEZA", obj.Name, type_id, f"{label} activo.")
    if "Assembly" in type_id:
        return EditState("assembly", "ENSAMBLAJE", obj.Name, type_id, f"{label} seleccionado.")
    return EditState("selection", "SELECCIÓN", obj.Name, type_id, f"{label} seleccionado.")


def _native_object(name: str):
    return App.ActiveDocument.getObject(name) if name and App.ActiveDocument else None


def _safe_recompute():
    if App.ActiveDocument is None:
        return
    try:
        App.ActiveDocument.recompute()
    except Exception as exc:
        App.Console.PrintError(f"SolidFreeCAD alpha.8: error al recalcular: {exc}\n")


def _finish_edit(accept: bool):
    """Close the native edit session without fabricating geometry operations."""
    gui_document = Gui.activeDocument()
    if gui_document is None:
        return
    try:
        # Native FreeCAD task dialogs own their transaction. Closing the dialog
        # and resetting edit delegates final geometry handling to FreeCAD.
        Gui.Control.closeDialog()
    except Exception:
        pass
    try:
        gui_document.resetEdit()
    except Exception as exc:
        App.Console.PrintWarning(f"SolidFreeCAD alpha.8: no se pudo cerrar edición: {exc}\n")
    if accept:
        _safe_recompute()


class ConfirmationCorner(QtWidgets.QFrame):
    """Viewport confirmation controls shown only during a native edit session."""

    def __init__(self, main):
        parent = main.centralWidget() or main
        super().__init__(parent)
        self.main = main
        self.setObjectName(_CONFIRMATION_CORNER)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)
        self.badge = QtWidgets.QLabel("EDITANDO")
        self.badge.setObjectName(_MODE_BADGE)
        layout.addWidget(self.badge)
        self.accept = QtWidgets.QToolButton()
        self.accept.setObjectName("SFCAlpha8Accept")
        self.accept.setIcon(_icon("propertymanager/aceptar.svg"))
        self.accept.setToolTip("Aceptar y salir de la edición")
        self.accept.clicked.connect(lambda: _finish_edit(True))
        layout.addWidget(self.accept)
        self.cancel = QtWidgets.QToolButton()
        self.cancel.setObjectName("SFCAlpha8Cancel")
        self.cancel.setIcon(_icon("propertymanager/cancelar.svg"))
        self.cancel.setToolTip("Cerrar la edición")
        self.cancel.clicked.connect(lambda: _finish_edit(False))
        layout.addWidget(self.cancel)
        self.adjustSize()
        parent.installEventFilter(self)
        self.hide()

    def eventFilter(self, watched, event):
        if event.type() in (QtCore.QEvent.Resize, QtCore.QEvent.Show):
            QtCore.QTimer.singleShot(0, self.reposition)
        return False

    def reposition(self):
        parent = self.parentWidget()
        if parent is None:
            return
        self.adjustSize()
        self.move(max(8, parent.width() - self.width() - 22), 18)
        self.raise_()

    def update_state(self, state: EditState):
        active = state.mode in {"sketch", "feature"}
        self.badge.setText(state.title)
        self.setVisible(active)
        if active:
            self.reposition()


class PropertyFieldFactory:
    """Build native property editors for common feature parameters."""

    NUMERIC_TYPES = {
        "App::PropertyLength",
        "App::PropertyDistance",
        "App::PropertyAngle",
        "App::PropertyFloat",
        "App::PropertyInteger",
    }

    FRIENDLY_NAMES = {
        "Length": "Profundidad",
        "Length2": "Segunda profundidad",
        "Angle": "Ángulo",
        "Radius": "Radio",
        "Size": "Tamaño",
        "Reversed": "Invertir dirección",
        "Midplane": "Plano medio",
        "ThroughAll": "A través de todo",
        "Diameter": "Diámetro",
        "Height": "Altura",
        "Width": "Ancho",
        "Thickness": "Espesor",
    }

    @classmethod
    def label(cls, name):
        return cls.FRIENDLY_NAMES.get(name, name)

    @classmethod
    def editor(cls, owner, obj, name, type_id):
        if type_id in cls.NUMERIC_TYPES:
            widget = QtWidgets.QDoubleSpinBox()
            widget.setDecimals(3)
            widget.setRange(-1.0e9, 1.0e9)
            widget.setSingleStep(1.0)
            try:
                value = getattr(obj, name)
                widget.setValue(float(getattr(value, "Value", value)))
            except Exception:
                widget.setValue(0.0)
            widget.editingFinished.connect(
                lambda w=widget, n=name: owner.apply_property(n, w.value())
            )
            return widget
        if type_id == "App::PropertyBool":
            widget = QtWidgets.QCheckBox()
            try:
                widget.setChecked(bool(getattr(obj, name)))
            except Exception:
                pass
            widget.toggled.connect(lambda value, n=name: owner.apply_property(n, bool(value)))
            return widget
        if type_id == "App::PropertyEnumeration":
            widget = QtWidgets.QComboBox()
            try:
                choices = list(obj.getEnumerationsOfProperty(name))
                widget.addItems(choices)
                widget.setCurrentText(str(getattr(obj, name)))
                widget.currentTextChanged.connect(lambda value, n=name: owner.apply_property(n, value))
                return widget
            except Exception:
                return None
        return None


class ContextualOperationPage(QtWidgets.QWidget):
    """Selection/edit-aware PropertyManager page integrated into alpha.7."""

    PRIORITY_PROPERTIES = (
        "Length", "Length2", "Type", "Reversed", "Midplane", "Angle",
        "Radius", "Size", "Diameter", "Height", "Width", "Thickness",
        "ThroughAll", "Occurrences", "Pitch",
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(_OPERATION_PAGE)
        self._object = None
        self._updating = False
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(7)

        header = QtWidgets.QWidget()
        header.setObjectName("SFCAlpha8OperationHeader")
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(5, 4, 5, 4)
        self.accept = QtWidgets.QToolButton()
        self.accept.setIcon(_icon("propertymanager/aceptar.svg"))
        self.accept.setToolTip("Aceptar")
        self.accept.clicked.connect(lambda: _finish_edit(True))
        header_layout.addWidget(self.accept)
        self.cancel = QtWidgets.QToolButton()
        self.cancel.setIcon(_icon("propertymanager/cancelar.svg"))
        self.cancel.setToolTip("Cerrar edición")
        self.cancel.clicked.connect(lambda: _finish_edit(False))
        header_layout.addWidget(self.cancel)
        self.title = QtWidgets.QLabel("Preparar modelo")
        self.title.setObjectName("SFCAlpha8OperationTitle")
        header_layout.addWidget(self.title, 1)
        root.addWidget(header)

        self.message = QtWidgets.QLabel("Seleccione una operación para ver sus parámetros.")
        self.message.setObjectName("SFCAlpha8OperationMessage")
        self.message.setWordWrap(True)
        root.addWidget(self.message)

        self.constraint = QtWidgets.QLabel("Estado del modelo")
        self.constraint.setObjectName("SFCAlpha8ConstraintState")
        self.constraint.setWordWrap(True)
        root.addWidget(self.constraint)

        selection_group = QtWidgets.QGroupBox("Selecciones de la operación")
        selection_layout = QtWidgets.QVBoxLayout(selection_group)
        self.selection_list = QtWidgets.QListWidget()
        self.selection_list.setMaximumHeight(92)
        selection_layout.addWidget(self.selection_list)
        root.addWidget(selection_group)

        parameters_group = QtWidgets.QGroupBox("Definición")
        self.parameters_layout = QtWidgets.QFormLayout(parameters_group)
        self.parameters_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        root.addWidget(parameters_group, 1)

        actions = QtWidgets.QGridLayout()
        for index, (label, icon, callback) in enumerate((
            ("Editar", "croquis/nuevo_croquis.svg", self.edit_current),
            ("Normal a", "vistas/frontal.svg", self.normal_to_selection),
            ("Ajustar", "vistas/ajustar.svg", self.fit_all),
            ("Recalcular", "evaluacion/comprobar.svg", _safe_recompute),
        )):
            button = QtWidgets.QPushButton(label)
            button.setIcon(_icon(icon))
            button.clicked.connect(callback)
            actions.addWidget(button, index // 2, index % 2)
        root.addLayout(actions)

    def clear_form(self):
        while self.parameters_layout.rowCount():
            self.parameters_layout.removeRow(0)

    def set_state(self, state: EditState):
        self.title.setText(state.title.title())
        self.message.setText(state.message or "Seleccione una operación.")
        if state.mode == "sketch":
            if state.degrees_of_freedom == 0:
                self.constraint.setText("✓ Croquis totalmente definido")
                self.constraint.setProperty("state", "ok")
            elif state.degrees_of_freedom is not None:
                self.constraint.setText(f"○ Croquis subdefinido · {state.degrees_of_freedom} grados de libertad")
                self.constraint.setProperty("state", "warning")
            else:
                self.constraint.setText("Croquis en edición · revise cotas y relaciones")
                self.constraint.setProperty("state", "editing")
        else:
            self.constraint.setText("Modelo listo" if App.ActiveDocument else "Sin documento")
            self.constraint.setProperty("state", "ok" if App.ActiveDocument else "idle")
        self.constraint.style().unpolish(self.constraint)
        self.constraint.style().polish(self.constraint)
        obj = _native_object(state.object_name) or _selected_object()
        if obj is not self._object:
            self.set_object(obj)
        self.refresh_selection_list()

    def set_object(self, obj):
        self._object = obj
        self._updating = True
        self.clear_form()
        if obj is None:
            self.parameters_layout.addRow(QtWidgets.QLabel("Sin parámetros editables."))
            self._updating = False
            return
        names = list(getattr(obj, "PropertiesList", []))
        ordered = [name for name in self.PRIORITY_PROPERTIES if name in names]
        ordered.extend(name for name in names if name not in ordered)
        added = 0
        for name in ordered:
            if name in {"Label", "Placement", "Shape", "ExpressionEngine", "Proxy"}:
                continue
            try:
                type_id = obj.getTypeIdOfProperty(name)
                widget = PropertyFieldFactory.editor(self, obj, name, type_id)
            except Exception:
                widget = None
            if widget is None:
                continue
            self.parameters_layout.addRow(PropertyFieldFactory.label(name), widget)
            added += 1
            if added >= 14:
                break
        if not added:
            self.parameters_layout.addRow(QtWidgets.QLabel("Esta selección no expone parámetros compatibles."))
        self._updating = False

    def apply_property(self, name, value):
        if self._updating or self._object is None or App.ActiveDocument is None:
            return
        try:
            App.ActiveDocument.openTransaction(f"Editar {name}")
            setattr(self._object, name, value)
            App.ActiveDocument.recompute()
            App.ActiveDocument.commitTransaction()
        except Exception as exc:
            try:
                App.ActiveDocument.abortTransaction()
            except Exception:
                pass
            App.Console.PrintError(f"SolidFreeCAD alpha.8: no se pudo cambiar {name}: {exc}\n")

    def refresh_selection_list(self):
        self.selection_list.clear()
        extended = Gui.Selection.getSelectionEx()
        for entry in extended:
            label = getattr(entry.Object, "Label", entry.ObjectName)
            names = list(getattr(entry, "SubElementNames", []) or [])
            if names:
                for name in names[:12]:
                    self.selection_list.addItem(f"{label} · {name}")
            else:
                self.selection_list.addItem(label)
        if self.selection_list.count() == 0:
            self.selection_list.addItem("Sin selección geométrica")

    def edit_current(self):
        obj = self._object or _selected_object()
        if obj is None or Gui.activeDocument() is None:
            return
        try:
            Gui.activeDocument().setEdit(obj.Name)
        except Exception as exc:
            App.Console.PrintWarning(f"SolidFreeCAD alpha.8: no admite edición: {exc}\n")

    def normal_to_selection(self):
        # Prefer registered native commands; no private camera manipulation.
        if not _run_candidates(("Std_ViewSelection", "ViewSelection")):
            _run_candidates(("Std_ViewFront",))

    def fit_all(self):
        if Gui.activeDocument() is not None:
            Gui.activeDocument().activeView().fitAll()


class FeatureHierarchyController(QtCore.QObject):
    """Replace the flat alpha.6 history with a native-object hierarchy."""

    def __init__(self, manager, tree):
        super().__init__(tree)
        self.manager = manager
        self.tree = tree
        self._signature = None
        self._updating_selection = False
        timer = getattr(manager, "_timer", None)
        if timer is not None:
            timer.stop()
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree.itemDoubleClicked.connect(self.edit_item)
        self.tree.itemSelectionChanged.connect(self.select_items)
        self._observer = _HierarchySelectionObserver(self)
        Gui.Selection.addObserver(self._observer)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(600)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh(force=True)

    def signature(self):
        doc = App.ActiveDocument
        if doc is None:
            return None
        return (
            doc.Name,
            tuple(
                (
                    obj.Name,
                    obj.Label,
                    obj.TypeId,
                    bool(getattr(getattr(obj, "ViewObject", None), "Visibility", True)),
                    tuple(child.Name for child in getattr(obj, "Group", []) or []),
                )
                for obj in doc.Objects
            ),
        )

    def refresh(self, force=False):
        signature = self.signature()
        if not force and signature == self._signature:
            return
        self._signature = signature
        expanded = self.expanded_names()
        selected_names = {obj.Name for obj in Gui.Selection.getSelection()}
        self.tree.blockSignals(True)
        self.tree.clear()
        doc = App.ActiveDocument
        if doc is None:
            self.tree.addTopLevelItem(QtWidgets.QTreeWidgetItem(["Sin documento activo"]))
            self.tree.blockSignals(False)
            return
        root = self.make_item(doc.Label or doc.Name, "", "document")
        self.tree.addTopLevelItem(root)
        root.setExpanded(True)

        bodies = [obj for obj in doc.Objects if "PartDesign::Body" in obj.TypeId]
        parts = [obj for obj in doc.Objects if obj.TypeId in {"App::Part", "App::DocumentObjectGroup"}]
        grouped = set()
        for container in (*parts, *bodies):
            item = self.object_item(container)
            root.addChild(item)
            grouped.add(container.Name)
            for child in getattr(container, "Group", []) or []:
                item.addChild(self.object_item(child))
                grouped.add(child.Name)
            item.setExpanded(container.Name in expanded or "Body" in container.TypeId)

        references = []
        loose = []
        for obj in doc.Objects:
            if obj.Name in grouped:
                continue
            if any(token in obj.TypeId for token in ("Plane", "Axis", "Origin", "CoordinateSystem")):
                references.append(obj)
            else:
                loose.append(obj)
        if references:
            group = self.make_item("Origen y referencias", "", "group")
            root.addChild(group)
            for obj in references:
                group.addChild(self.object_item(obj))
            group.setExpanded("__references__" in expanded)
            group.setData(0, QtCore.Qt.UserRole + 2, "__references__")
        if loose:
            group = self.make_item("Operaciones y objetos", "", "group")
            root.addChild(group)
            for obj in loose:
                group.addChild(self.object_item(obj))
            group.setExpanded(True)

        self.restore_selection(root, selected_names)
        self.tree.blockSignals(False)

    def expanded_names(self):
        names = set()
        iterator = QtWidgets.QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if item.isExpanded():
                name = item.data(0, QtCore.Qt.UserRole) or item.data(0, QtCore.Qt.UserRole + 2)
                if name:
                    names.add(str(name))
            iterator += 1
        return names

    def make_item(self, text, name, category):
        item = QtWidgets.QTreeWidgetItem([text])
        item.setData(0, QtCore.Qt.UserRole, name)
        item.setData(0, QtCore.Qt.UserRole + 1, category)
        return item

    def object_item(self, obj):
        visible = bool(getattr(getattr(obj, "ViewObject", None), "Visibility", True))
        suffix = "" if visible else "  (oculto)"
        item = self.make_item((obj.Label or obj.Name) + suffix, obj.Name, self.category(obj))
        item.setToolTip(0, f"{obj.TypeId}\nNombre interno: {obj.Name}")
        icon_path = self.icon_for(obj)
        if icon_path:
            item.setIcon(0, _icon(icon_path))
        if not visible:
            item.setForeground(0, QtGui.QBrush(QtGui.QColor("#8a949b")))
        shape = getattr(obj, "Shape", None)
        try:
            if shape is not None and not shape.isNull() and not shape.isValid():
                item.setText(0, "⚠ " + item.text(0))
                item.setForeground(0, QtGui.QBrush(QtGui.QColor("#a23a2a")))
        except Exception:
            pass
        return item

    @staticmethod
    def category(obj):
        type_id = obj.TypeId
        if "Sketcher::SketchObject" in type_id:
            return "sketch"
        if "Body" in type_id:
            return "body"
        if "PartDesign" in type_id or "Part::Feature" in type_id:
            return "feature"
        if "Assembly" in type_id:
            return "assembly"
        return "object"

    @staticmethod
    def icon_for(obj):
        type_id = obj.TypeId
        if "Sketcher::SketchObject" in type_id:
            return "croquis/nuevo_croquis.svg"
        label = (obj.Label or obj.Name).lower()
        if "pocket" in type_id.lower() or "corte" in label:
            return "operaciones/corte_extruido.svg"
        if "revolution" in type_id.lower() or "revol" in label:
            return "operaciones/revolucion.svg"
        if "fillet" in type_id.lower() or "redonde" in label:
            return "operaciones/redondeo.svg"
        if "chamfer" in type_id.lower() or "chaf" in label:
            return "operaciones/chaflan.svg"
        if "Body" in type_id:
            return "archivo/nuevo.svg"
        if "PartDesign" in type_id or "Part::Feature" in type_id:
            return "operaciones/saliente_base.svg"
        return "evaluacion/comprobar.svg"

    def restore_selection(self, root, names):
        iterator = QtWidgets.QTreeWidgetItemIterator(root)
        while iterator.value():
            item = iterator.value()
            if item.data(0, QtCore.Qt.UserRole) in names:
                item.setSelected(True)
            iterator += 1

    def edit_item(self, item, _column):
        name = item.data(0, QtCore.Qt.UserRole)
        obj = _native_object(name)
        if obj is None or Gui.activeDocument() is None:
            return
        try:
            Gui.activeDocument().setEdit(obj.Name)
        except Exception:
            pass

    def select_items(self):
        if self._updating_selection or App.ActiveDocument is None:
            return
        self._updating_selection = True
        try:
            Gui.Selection.clearSelection()
            for item in self.tree.selectedItems():
                name = item.data(0, QtCore.Qt.UserRole)
                obj = App.ActiveDocument.getObject(name) if name else None
                if obj is not None:
                    Gui.Selection.addSelection(obj)
        finally:
            self._updating_selection = False

    def sync_from_model(self):
        if self._updating_selection:
            return
        names = {obj.Name for obj in Gui.Selection.getSelection()}
        self._updating_selection = True
        try:
            self.tree.blockSignals(True)
            iterator = QtWidgets.QTreeWidgetItemIterator(self.tree)
            while iterator.value():
                item = iterator.value()
                item.setSelected(item.data(0, QtCore.Qt.UserRole) in names)
                iterator += 1
            self.tree.blockSignals(False)
        finally:
            self._updating_selection = False


class _HierarchySelectionObserver:
    def __init__(self, owner):
        self.owner = owner

    def addSelection(self, *_args):
        self.owner.sync_from_model()

    def removeSelection(self, *_args):
        self.owner.sync_from_model()

    def clearSelection(self, *_args):
        self.owner.sync_from_model()


class ShortcutPalette(QtWidgets.QFrame):
    """Context-aware popup command palette opened with the S key."""

    def __init__(self, main):
        super().__init__(None, QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint)
        self.main = main
        self.setObjectName(_SHORTCUT_PALETTE)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(5)

    def show_for_state(self, state: EditState):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if state.mode in {"sketch", "sketch-selected"}:
            commands = (
                ("Línea", "croquis/linea.svg", ("Sketcher_CreatePolyline", "Sketcher_CreateLine")),
                ("Rectángulo", "croquis/rectangulo.svg", ("Sketcher_CreateRectangle",)),
                ("Círculo", "croquis/circulo.svg", ("Sketcher_CreateCircle",)),
                ("Cota", "cotas_relaciones/cota.svg", ("Sketcher_ConstrainDistance",)),
                ("Horizontal", "cotas_relaciones/horizontal.svg", ("Sketcher_ConstrainHorizontal",)),
                ("Vertical", "cotas_relaciones/vertical.svg", ("Sketcher_ConstrainVertical",)),
            )
        else:
            commands = (
                ("Croquis", "croquis/nuevo_croquis.svg", ("SFC_NewSketch", "Sketcher_NewSketch")),
                ("Saliente", "operaciones/saliente_base.svg", ("SFC_Pad", "PartDesign_Pad")),
                ("Corte", "operaciones/corte_extruido.svg", ("SFC_Pocket", "PartDesign_Pocket")),
                ("Revolución", "operaciones/revolucion.svg", ("SFC_Revolution", "PartDesign_Revolution")),
                ("Redondeo", "operaciones/redondeo.svg", ("SFC_Fillet", "PartDesign_Fillet")),
                ("Medir", "evaluacion/medir.svg", ("Std_Measure", "Part_Measure_Menu")),
            )
        for index, (label, icon, candidates) in enumerate(commands):
            button = QtWidgets.QToolButton()
            button.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
            button.setIcon(_icon(icon))
            button.setIconSize(QtCore.QSize(24, 24))
            button.setText(label)
            button.setEnabled(_first_available(candidates) is not None)
            button.clicked.connect(lambda _checked=False, c=candidates: (self.hide(), _run_candidates(c)))
            self.layout.addWidget(button, index // 3, index % 3)
        self.adjustSize()
        point = QtGui.QCursor.pos()
        self.move(point.x() - self.width() // 2, point.y() - self.height() // 2)
        self.show()
        self.raise_()


class InteractionController(QtCore.QObject):
    """Synchronize edit mode, contextual tabs and adaptive shell state."""

    def __init__(self, main, operation_page, corner, palette):
        super().__init__(main)
        self.main = main
        self.operation_page = operation_page
        self.corner = corner
        self.palette = palette
        self._state = None
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        main.installEventFilter(self)
        self.refresh(force=True)

    def refresh(self, force=False):
        state = _state_from_context()
        signature = (state.mode, state.object_name, state.message, state.degrees_of_freedom)
        if not force and signature == self._state:
            return
        previous_mode = self._state[0] if self._state else None
        self._state = signature
        self.operation_page.set_state(state)
        self.corner.update_state(state)
        self.update_command_tab(state, previous_mode)
        self.update_status(state)

    def update_command_tab(self, state, previous_mode):
        if state.mode == previous_mode:
            return
        tabs = self.main.findChild(QtWidgets.QTabWidget, _COMMAND_TABS)
        if tabs is None:
            return
        target = {
            "sketch": "Croquis",
            "sketch-selected": "Croquis",
            "assembly": "Ensamblaje",
            "feature": "Operaciones",
            "feature-selected": "Operaciones",
            "body": "Operaciones",
        }.get(state.mode)
        if not target:
            return
        for index in range(tabs.count()):
            if tabs.tabText(index) == target:
                tabs.setCurrentIndex(index)
                break

    def update_status(self, state):
        label = self.main.findChild(QtWidgets.QLabel, _STATUS)
        if label is None:
            label = QtWidgets.QLabel()
            label.setObjectName(_STATUS)
            self.main.statusBar().addPermanentWidget(label)
        if state.mode == "sketch" and state.degrees_of_freedom == 0:
            label.setText("Croquis totalmente definido · Motor FreeCAD · FCStd")
            label.setProperty("state", "ok")
        elif state.mode == "sketch":
            label.setText(f"{state.message} · Edición activa")
            label.setProperty("state", "editing")
        else:
            label.setText("SolidFreeCAD alpha.8 · Flujo interactivo source-only · Sin ejecutable")
            label.setProperty("state", "idle")
        label.style().unpolish(label)
        label.style().polish(label)
        label.show()

    def eventFilter(self, watched, event):
        if event.type() == QtCore.QEvent.Resize:
            QtCore.QTimer.singleShot(0, self.apply_adaptive_layout)
        return False

    def apply_adaptive_layout(self):
        width = self.main.width()
        task = self.main.findChild(QtWidgets.QDockWidget, "SolidFreeCADAlpha7TaskPane")
        manager = self.main.findChild(QtWidgets.QDockWidget, "SolidFreeCADFeatureManager")
        if width >= 1450:
            if task is not None:
                task.show()
            try:
                self.main.resizeDocks([manager, task], [310, 310], QtCore.Qt.Horizontal)
            except Exception:
                pass
        elif width >= 1120:
            if task is not None:
                task.show()
            try:
                self.main.resizeDocks([manager, task], [275, 285], QtCore.Qt.Horizontal)
            except Exception:
                pass
        elif task is not None and task.isVisible() and _in_edit_object() is None:
            task.hide()

    def show_shortcut_palette(self):
        focus = QtWidgets.QApplication.focusWidget()
        if isinstance(focus, (QtWidgets.QLineEdit, QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit, QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
            return
        self.palette.show_for_state(_state_from_context())


class DisplayStyleController:
    STYLES = ("Sombreado con aristas", "Sombreado", "Alámbrico")

    def __init__(self, main):
        self.main = main
        toolbar = main.findChild(QtWidgets.QToolBar, _CONTEXT_BAR)
        if toolbar is None:
            return
        existing = toolbar.findChild(QtWidgets.QComboBox, _DISPLAY_COMBO)
        if existing is not None:
            self.combo = existing
            return
        toolbar.addSeparator()
        toolbar.addWidget(QtWidgets.QLabel("Visualización"))
        self.combo = QtWidgets.QComboBox()
        self.combo.setObjectName(_DISPLAY_COMBO)
        self.combo.addItems(self.STYLES)
        self.combo.setCurrentIndex(0)
        self.combo.currentTextChanged.connect(self.apply)
        toolbar.addWidget(self.combo)
        orientation = QtWidgets.QToolButton()
        orientation.setText("Orientación")
        orientation.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        menu = QtWidgets.QMenu(orientation)
        for label, candidates in (
            ("Isométrica", ("SFC_FitAxonometric", "ViewAxonometric")),
            ("Frontal", ("Std_ViewFront",)),
            ("Superior", ("Std_ViewTop",)),
            ("Derecha", ("Std_ViewRight",)),
            ("Ajustar", ("ViewFit", "Std_ViewFitAll")),
        ):
            action = menu.addAction(label)
            action.setEnabled(_first_available(candidates) is not None)
            action.triggered.connect(lambda _checked=False, c=candidates: _run_candidates(c))
        orientation.setMenu(menu)
        toolbar.addWidget(orientation)

    def apply(self, text):
        gui_doc = Gui.activeDocument()
        if gui_doc is None:
            return
        style = {
            "Sombreado con aristas": "Flat Lines",
            "Sombreado": "Shaded",
            "Alámbrico": "Wireframe",
        }.get(text, "Flat Lines")
        try:
            gui_doc.activeView().setDrawStyle(style)
        except Exception as exc:
            App.Console.PrintWarning(f"SolidFreeCAD alpha.8: estilo no disponible: {exc}\n")


def _install_operation_page(main):
    global _operation_page
    tabs = main.findChild(QtWidgets.QTabWidget, _OPERATION_TABS)
    if tabs is None:
        return None
    existing = main.findChild(QtWidgets.QWidget, _OPERATION_PAGE)
    if existing is not None:
        _operation_page = existing
        return existing
    _operation_page = ContextualOperationPage(tabs)
    tabs.insertTab(0, _operation_page, "Operación")
    tabs.setCurrentWidget(_operation_page)
    return _operation_page


def _install_hierarchy(main):
    global _hierarchy
    manager = main.findChild(QtWidgets.QDockWidget, "SolidFreeCADFeatureManager")
    tree = main.findChild(QtWidgets.QTreeWidget, _FEATURE_TREE)
    if manager is None or tree is None:
        return None
    if _hierarchy is None:
        _hierarchy = FeatureHierarchyController(manager, tree)
    else:
        _hierarchy.refresh(force=True)
    return _hierarchy


def _install_shortcuts(main, controller):
    global _shortcuts
    if _shortcuts:
        return
    palette = QtWidgets.QShortcut(QtGui.QKeySequence("S"), main)
    palette.setContext(QtCore.Qt.ApplicationShortcut)
    palette.activated.connect(controller.show_shortcut_palette)
    fit = QtWidgets.QShortcut(QtGui.QKeySequence("F"), main)
    fit.setContext(QtCore.Qt.ApplicationShortcut)
    fit.activated.connect(lambda: Gui.activeDocument() and Gui.activeDocument().activeView().fitAll())
    save = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), main)
    save.setContext(QtCore.Qt.ApplicationShortcut)
    save.activated.connect(lambda: _run_candidates(("SFC_Save", "Std_Save")))
    _shortcuts = [palette, fit, save]


def _apply_alpha8_style(main):
    marker = "/* SolidFreeCAD alpha8 interaction workflow */"
    if marker in main.styleSheet():
        return
    main.setStyleSheet(main.styleSheet() + marker + """
        QFrame#SolidFreeCADAlpha8ConfirmationCorner {
            background: rgba(245, 248, 250, 235); border: 1px solid #8d9aa3;
            border-radius: 4px;
        }
        QLabel#SolidFreeCADAlpha8ModeBadge {
            color: #174f73; font-weight: 700; padding: 2px 7px;
        }
        QToolButton#SFCAlpha8Accept { background: #dff2e3; border: 1px solid #6fad7b; padding: 3px; }
        QToolButton#SFCAlpha8Cancel { background: #f6dfdf; border: 1px solid #bf7777; padding: 3px; }
        QWidget#SFCAlpha8OperationHeader { background: #e4e9ed; border: 1px solid #b4bec5; }
        QLabel#SFCAlpha8OperationTitle { color: #243844; font-weight: 700; }
        QLabel#SFCAlpha8OperationMessage { background: #fff4a8; border: 1px solid #ccb942; padding: 7px; }
        QLabel#SFCAlpha8ConstraintState { border-radius: 3px; padding: 6px; }
        QLabel#SFCAlpha8ConstraintState[state="ok"] { background: #e1f1e5; color: #2b6239; }
        QLabel#SFCAlpha8ConstraintState[state="warning"] { background: #fff0cf; color: #805c18; }
        QLabel#SFCAlpha8ConstraintState[state="editing"] { background: #e1eff8; color: #205c7e; }
        QFrame#SolidFreeCADAlpha8ShortcutPalette {
            background: #f6f8f9; border: 1px solid #7f8f99; border-radius: 5px;
        }
        QFrame#SolidFreeCADAlpha8ShortcutPalette QToolButton {
            min-width: 72px; min-height: 58px; background: #ffffff;
            border: 1px solid #c1cbd1; padding: 4px;
        }
        QFrame#SolidFreeCADAlpha8ShortcutPalette QToolButton:hover {
            border: 1px solid #2d83b8; background: #eaf4fa;
        }
        QComboBox#SolidFreeCADAlpha8DisplayStyle {
            min-width: 145px; background: #ffffff; border: 1px solid #9eabb4; padding: 3px 6px;
        }
        QStatusBar QLabel#SolidFreeCADAlpha8Status[state="ok"] { color: #2b6239; font-weight: 700; }
        QStatusBar QLabel#SolidFreeCADAlpha8Status[state="editing"] { color: #1d648c; font-weight: 700; }
        QStatusBar QLabel#SolidFreeCADAlpha8Status[state="idle"] { color: #53636d; font-weight: 600; }
    """)


def show_workspace():
    """Show the alpha.8 source-only interaction prototype."""
    global _controller, _confirmation_corner
    result = show_alpha7_workspace()
    main = Gui.getMainWindow()
    _apply_alpha8_style(main)
    operation_page = _install_operation_page(main)
    _install_hierarchy(main)
    DisplayStyleController(main)
    if _confirmation_corner is None:
        _confirmation_corner = main.findChild(QtWidgets.QFrame, _CONFIRMATION_CORNER)
    if _confirmation_corner is None:
        _confirmation_corner = ConfirmationCorner(main)
    palette = ShortcutPalette(main)
    if operation_page is not None and _controller is None:
        _controller = InteractionController(main, operation_page, _confirmation_corner, palette)
        _install_shortcuts(main, _controller)
    elif _controller is not None:
        _controller.timer.start()
        _controller.refresh(force=True)
    main.setWindowTitle("SolidFreeCAD Desktop alpha.8 · Interaction Prototype")
    return result


def hide_workspace():
    hide_alpha7_workspace()
    main = Gui.getMainWindow()
    if _controller is not None:
        _controller.timer.stop()
    for name, kind in (
        (_CONFIRMATION_CORNER, QtWidgets.QFrame),
        (_STATUS, QtWidgets.QLabel),
    ):
        widget = main.findChild(kind, name)
        if widget is not None:
            widget.hide()
