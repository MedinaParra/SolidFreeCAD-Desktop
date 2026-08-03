"""SolidFreeCAD alpha.9 feature-definition and design-state workspace.

Alpha.9 builds on the alpha.8 interaction shell. It adds feature-specific
PropertyManager guidance, selection collectors, design-tree state columns,
selection modes and an original orientation overlay. Geometry remains native
FreeCAD/OpenCASCADE and this module contains no packaging logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from SolidFreeCAD.ClassicWorkspace import _first_available, _icon, _run_candidates
from SolidFreeCAD.InteractionWorkspace import (
    PropertyFieldFactory,
    _in_edit_object,
    _safe_recompute,
    _selected_object,
    _sketch_dof,
)
from SolidFreeCAD.InteractionWorkspaceCompat import (
    hide_workspace as hide_alpha8_workspace,
    show_workspace as show_alpha8_workspace,
)

_DEFINITION_CARD = "SolidFreeCADAlpha9DefinitionCard"
_DEFINITION_FORM = "SolidFreeCADAlpha9DefinitionForm"
_SELECTION_COLLECTOR = "SolidFreeCADAlpha9SelectionCollector"
_SELECTION_MODE = "SolidFreeCADAlpha9SelectionMode"
_ORIENTATION_WIDGET = "SolidFreeCADAlpha9OrientationWidget"
_STATUS = "SolidFreeCADAlpha9Status"
_TREE = "SolidFreeCADFeatureTree"
_CONTEXT_BAR = "SolidFreeCADAlpha7ContextBar"
_OPERATION_PAGE = "SolidFreeCADAlpha8OperationPage"

_controller = None
_orientation = None
_tree_enhancer = None
_selection_mode = None


@dataclass(frozen=True)
class FeatureProfile:
    kind: str
    title: str
    instruction: str
    properties: tuple[str, ...]
    selection_hint: str


_FEATURE_PROFILES = {
    "pad": FeatureProfile(
        "pad",
        "Saliente / Base",
        "Defina la condición final, profundidad y dirección del saliente.",
        ("Type", "Length", "Length2", "Reversed", "Midplane", "Offset", "TaperAngle"),
        "Seleccione un croquis cerrado o una cara plana.",
    ),
    "pocket": FeatureProfile(
        "pocket",
        "Corte extruido",
        "Defina la profundidad y el sentido de eliminación de material.",
        ("Type", "Length", "Length2", "Reversed", "Midplane", "Offset", "TaperAngle"),
        "Seleccione un croquis cerrado que interseque el sólido.",
    ),
    "revolution": FeatureProfile(
        "revolution",
        "Revolución",
        "Seleccione un perfil y un eje; después defina el ángulo de revolución.",
        ("Angle", "Reversed", "Midplane", "ReferenceAxis", "Axis", "Base"),
        "Seleccione un croquis y un eje, arista lineal o línea de construcción.",
    ),
    "fillet": FeatureProfile(
        "fillet",
        "Redondeo",
        "Seleccione las aristas y defina el radio de redondeo.",
        ("Radius", "UseAllEdges", "Base"),
        "Seleccione una o más aristas compatibles.",
    ),
    "chamfer": FeatureProfile(
        "chamfer",
        "Chaflán",
        "Seleccione las aristas y defina el tamaño del chaflán.",
        ("Size", "Size2", "Angle", "UseAllEdges", "Base"),
        "Seleccione una o más aristas compatibles.",
    ),
    "hole": FeatureProfile(
        "hole",
        "Asistente para taladro",
        "Defina diámetro, profundidad y terminación del taladro.",
        ("Diameter", "Depth", "HoleCutType", "HoleCutDiameter", "HoleCutDepth", "Threaded"),
        "Seleccione puntos de croquis o una cara plana.",
    ),
    "sketch": FeatureProfile(
        "sketch",
        "Croquis",
        "Cree geometría, agregue relaciones y deje el croquis totalmente definido.",
        (),
        "Use entidades, cotas y relaciones para controlar el perfil.",
    ),
    "generic": FeatureProfile(
        "generic",
        "Definición de operación",
        "Revise las selecciones y los parámetros nativos de la operación.",
        (),
        "Seleccione la geometría requerida por la operación.",
    ),
}


def _feature_kind(obj) -> str:
    if obj is None:
        return "generic"
    type_id = getattr(obj, "TypeId", "").lower()
    name = f"{getattr(obj, 'Name', '')} {getattr(obj, 'Label', '')}".lower()
    haystack = type_id + " " + name
    if "sketcher::sketchobject" in type_id:
        return "sketch"
    if "pocket" in haystack or "corte" in haystack:
        return "pocket"
    if "revolution" in haystack or "revolución" in haystack or "revolucion" in haystack:
        return "revolution"
    if "fillet" in haystack or "redonde" in haystack:
        return "fillet"
    if "chamfer" in haystack or "chaflán" in haystack or "chaflan" in haystack:
        return "chamfer"
    if "hole" in haystack or "taladro" in haystack or "agujero" in haystack:
        return "hole"
    if "pad" in haystack or "saliente" in haystack:
        return "pad"
    return "generic"


def _active_feature():
    return _in_edit_object() or _selected_object()


def _selection_description() -> list[str]:
    descriptions = []
    for entry in Gui.Selection.getSelectionEx():
        label = getattr(entry.Object, "Label", entry.ObjectName)
        subelements = list(getattr(entry, "SubElementNames", []) or [])
        if subelements:
            descriptions.extend(f"{label} · {name}" for name in subelements)
        else:
            descriptions.append(label)
    return descriptions


class SelectionCollector(QtWidgets.QGroupBox):
    """Display and manage the geometric input currently selected by the user."""

    def __init__(self, parent=None):
        super().__init__("Selecciones", parent)
        self.setObjectName(_SELECTION_COLLECTOR)
        layout = QtWidgets.QVBoxLayout(self)
        self.hint = QtWidgets.QLabel("Seleccione geometría en el modelo.")
        self.hint.setWordWrap(True)
        self.hint.setObjectName("SFCAlpha9SelectionHint")
        layout.addWidget(self.hint)
        self.items = QtWidgets.QListWidget()
        self.items.setMaximumHeight(112)
        layout.addWidget(self.items)
        row = QtWidgets.QHBoxLayout()
        capture = QtWidgets.QPushButton("Usar selección actual")
        capture.setIcon(_icon("propertymanager/aceptar.svg"))
        capture.clicked.connect(self.refresh)
        row.addWidget(capture)
        clear = QtWidgets.QPushButton("Limpiar")
        clear.setIcon(_icon("propertymanager/cancelar.svg"))
        clear.clicked.connect(self.clear_selection)
        row.addWidget(clear)
        layout.addLayout(row)
        self.refresh()

    def set_hint(self, text):
        self.hint.setText(text)

    def refresh(self):
        self.items.clear()
        values = _selection_description()
        for value in values[:24]:
            self.items.addItem(value)
        if not values:
            placeholder = QtWidgets.QListWidgetItem("Sin selección geométrica")
            placeholder.setForeground(QtGui.QBrush(QtGui.QColor("#7a878f")))
            self.items.addItem(placeholder)

    def clear_selection(self):
        Gui.Selection.clearSelection()
        self.refresh()


class DedicatedDefinitionCard(QtWidgets.QGroupBox):
    """Feature-specific controls that expose only real native properties."""

    def __init__(self, parent=None):
        super().__init__("Definición de operación", parent)
        self.setObjectName(_DEFINITION_CARD)
        self._object = None
        self._updating = False
        root = QtWidgets.QVBoxLayout(self)
        self.title = QtWidgets.QLabel("Definición de operación")
        self.title.setObjectName("SFCAlpha9FeatureTitle")
        root.addWidget(self.title)
        self.instruction = QtWidgets.QLabel("Seleccione una operación.")
        self.instruction.setWordWrap(True)
        self.instruction.setObjectName("SFCAlpha9FeatureInstruction")
        root.addWidget(self.instruction)
        self.condition = QtWidgets.QComboBox()
        self.condition.setObjectName("SFCAlpha9EndCondition")
        self.condition.hide()
        root.addWidget(self.condition)
        self.form_host = QtWidgets.QWidget()
        self.form = QtWidgets.QFormLayout(self.form_host)
        self.form.setObjectName(_DEFINITION_FORM)
        self.form.setContentsMargins(0, 0, 0, 0)
        self.form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        root.addWidget(self.form_host)
        self.sketch_summary = QtWidgets.QLabel()
        self.sketch_summary.setObjectName("SFCAlpha9SketchSummary")
        self.sketch_summary.setWordWrap(True)
        self.sketch_summary.hide()
        root.addWidget(self.sketch_summary)

        sketch_actions = QtWidgets.QGridLayout()
        self.sketch_buttons = []
        for index, (label, icon, commands) in enumerate((
            ("Línea", "croquis/linea.svg", ("Sketcher_CreatePolyline", "Sketcher_CreateLine")),
            ("Rectángulo", "croquis/rectangulo.svg", ("Sketcher_CreateRectangle",)),
            ("Círculo", "croquis/circulo.svg", ("Sketcher_CreateCircle",)),
            ("Cota inteligente", "cotas_relaciones/cota_inteligente.svg", ("Sketcher_ConstrainDistance",)),
            ("Horizontal", "cotas_relaciones/horizontal.svg", ("Sketcher_ConstrainHorizontal",)),
            ("Vertical", "cotas_relaciones/vertical.svg", ("Sketcher_ConstrainVertical",)),
        )):
            button = QtWidgets.QPushButton(label)
            button.setIcon(_icon(icon))
            button.setEnabled(_first_available(commands) is not None)
            button.clicked.connect(lambda _checked=False, c=commands: _run_candidates(c))
            sketch_actions.addWidget(button, index // 2, index % 2)
            self.sketch_buttons.append(button)
        self.sketch_host = QtWidgets.QWidget()
        self.sketch_host.setLayout(sketch_actions)
        self.sketch_host.hide()
        root.addWidget(self.sketch_host)

    def clear_form(self):
        while self.form.rowCount():
            self.form.removeRow(0)

    def set_object(self, obj):
        self._object = obj
        profile = _FEATURE_PROFILES[_feature_kind(obj)]
        self.title.setText(profile.title)
        self.instruction.setText(profile.instruction)
        self.clear_form()
        self.condition.hide()
        self.sketch_summary.hide()
        self.sketch_host.setVisible(profile.kind == "sketch")
        if obj is None:
            self.form.addRow(QtWidgets.QLabel("Sin operación seleccionada."))
            return
        if profile.kind == "sketch":
            dof = _sketch_dof(obj)
            if dof == 0:
                text = "✓ Croquis totalmente definido"
            elif dof is not None:
                text = f"○ Croquis subdefinido · {dof} grados de libertad"
            else:
                text = "Estado de restricciones no disponible en este momento."
            self.sketch_summary.setText(text)
            self.sketch_summary.show()
            return
        added = 0
        for name in profile.properties:
            if name not in getattr(obj, "PropertiesList", []):
                continue
            try:
                type_id = obj.getTypeIdOfProperty(name)
                widget = PropertyFieldFactory.editor(self, obj, name, type_id)
            except Exception:
                widget = None
            if widget is None:
                continue
            self.form.addRow(PropertyFieldFactory.label(name), widget)
            added += 1
        if not added:
            self.form.addRow(QtWidgets.QLabel("La operación no expone aún parámetros dedicados compatibles."))

    def apply_property(self, name, value):
        if self._updating or self._object is None or App.ActiveDocument is None:
            return
        try:
            App.ActiveDocument.openTransaction(f"Definir {name}")
            setattr(self._object, name, value)
            App.ActiveDocument.recompute()
            App.ActiveDocument.commitTransaction()
        except Exception as exc:
            try:
                App.ActiveDocument.abortTransaction()
            except Exception:
                pass
            App.Console.PrintError(f"SolidFreeCAD alpha.9: no se pudo definir {name}: {exc}\n")


class FeatureDefinitionController(QtCore.QObject):
    """Insert dedicated feature controls into the alpha.8 operation page."""

    def __init__(self, page):
        super().__init__(page)
        self.page = page
        self.card = DedicatedDefinitionCard(page)
        self.collector = SelectionCollector(page)
        layout = page.layout()
        # Header, message, constraint and alpha.8 selection list remain above.
        layout.insertWidget(4, self.collector)
        layout.insertWidget(5, self.card)
        self._signature = None
        self.observer = _SelectionObserver(self.refresh)
        Gui.Selection.addObserver(self.observer)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh(force=True)

    def refresh(self, force=False):
        obj = _active_feature()
        kind = _feature_kind(obj)
        selection = tuple(_selection_description())
        signature = (
            getattr(obj, "Name", ""),
            kind,
            selection,
            _sketch_dof(obj) if kind == "sketch" else None,
        )
        if not force and signature == self._signature:
            return
        self._signature = signature
        profile = _FEATURE_PROFILES[kind]
        self.collector.set_hint(profile.selection_hint)
        self.collector.refresh()
        self.card.set_object(obj)


class _SelectionObserver:
    def __init__(self, callback):
        self.callback = callback

    def addSelection(self, *_args):
        self.callback()

    def removeSelection(self, *_args):
        self.callback()

    def clearSelection(self, *_args):
        self.callback()


class TreeStateEnhancer(QtCore.QObject):
    """Add operation state, tip and sketch-definition information to the tree."""

    def __init__(self, tree):
        super().__init__(tree)
        self.tree = tree
        tree.setColumnCount(2)
        tree.setHeaderHidden(False)
        tree.setHeaderLabels(["Diseño", "Estado"])
        tree.header().setStretchLastSection(False)
        tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(700)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self):
        doc = App.ActiveDocument
        if doc is None:
            return
        tips = {
            getattr(body.Tip, "Name", "")
            for body in doc.Objects
            if "PartDesign::Body" in body.TypeId and getattr(body, "Tip", None) is not None
        }
        iterator = QtWidgets.QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            name = item.data(0, QtCore.Qt.UserRole)
            obj = doc.getObject(name) if name else None
            if obj is not None:
                status = self.object_status(obj, name in tips)
                item.setText(1, status)
                font = item.font(0)
                font.setBold(name in tips)
                item.setFont(0, font)
                if name in tips:
                    item.setForeground(0, QtGui.QBrush(QtGui.QColor("#176b9b")))
            iterator += 1

    @staticmethod
    def object_status(obj, is_tip):
        view = getattr(obj, "ViewObject", None)
        if view is not None and not view.Visibility:
            return "Oculto"
        if "Sketcher::SketchObject" in obj.TypeId:
            dof = _sketch_dof(obj)
            if dof == 0:
                return "Definido"
            if dof is not None:
                return f"{dof} GDL"
            return "Croquis"
        shape = getattr(obj, "Shape", None)
        try:
            if shape is not None and not shape.isNull() and not shape.isValid():
                return "Error"
        except Exception:
            pass
        if is_tip:
            return "Activo"
        if "Body" in obj.TypeId:
            return "Pieza"
        return ""


class SelectionModeController:
    """Optional native selection gates exposed in the context toolbar."""

    MODES = (
        ("Selección automática", ""),
        ("Caras", "SELECT Part::Feature SUBELEMENT Face"),
        ("Aristas", "SELECT Part::Feature SUBELEMENT Edge"),
        ("Vértices", "SELECT Part::Feature SUBELEMENT Vertex"),
        ("Cuerpos", "SELECT PartDesign::Body"),
    )

    def __init__(self, main):
        toolbar = main.findChild(QtWidgets.QToolBar, _CONTEXT_BAR)
        self.combo = None
        if toolbar is None:
            return
        existing = toolbar.findChild(QtWidgets.QComboBox, _SELECTION_MODE)
        if existing is not None:
            self.combo = existing
            return
        toolbar.addSeparator()
        toolbar.addWidget(QtWidgets.QLabel("Filtro"))
        self.combo = QtWidgets.QComboBox()
        self.combo.setObjectName(_SELECTION_MODE)
        for label, gate in self.MODES:
            self.combo.addItem(label, gate)
        self.combo.currentIndexChanged.connect(self.apply)
        toolbar.addWidget(self.combo)

    def apply(self, index):
        gate = self.combo.itemData(index) if self.combo is not None else ""
        try:
            Gui.Selection.removeSelectionGate()
        except Exception:
            pass
        if not gate:
            return
        try:
            Gui.Selection.addSelectionGate(gate)
        except Exception as exc:
            App.Console.PrintWarning(
                f"SolidFreeCAD alpha.9: el filtro no está disponible en este runtime: {exc}\n"
            )
            blocked = self.combo.blockSignals(True)
            self.combo.setCurrentIndex(0)
            self.combo.blockSignals(blocked)


class OrientationOverlay(QtWidgets.QFrame):
    """Original compact orientation control for the graphics area."""

    def __init__(self, main):
        parent = main.centralWidget() or main
        super().__init__(parent)
        self.main = main
        self.setObjectName(_ORIENTATION_WIDGET)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        grid = QtWidgets.QGridLayout(self)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(2)
        entries = (
            ("SUP", ("Std_ViewTop",), 0, 1),
            ("FRE", ("Std_ViewFront",), 1, 0),
            ("ISO", ("SFC_FitAxonometric", "ViewAxonometric"), 1, 1),
            ("DER", ("Std_ViewRight",), 1, 2),
            ("AJU", ("ViewFit", "Std_ViewFitAll"), 2, 1),
        )
        for text, commands, row, column in entries:
            button = QtWidgets.QToolButton()
            button.setText(text)
            button.setToolTip({"SUP": "Superior", "FRE": "Frontal", "ISO": "Isométrica", "DER": "Derecha", "AJU": "Ajustar"}[text])
            button.setEnabled(_first_available(commands) is not None)
            button.clicked.connect(lambda _checked=False, c=commands: _run_candidates(c))
            grid.addWidget(button, row, column)
        self.adjustSize()
        parent.installEventFilter(self)
        self.show()
        self.reposition()

    def eventFilter(self, watched, event):
        if event.type() in (QtCore.QEvent.Resize, QtCore.QEvent.Show):
            QtCore.QTimer.singleShot(0, self.reposition)
        return False

    def reposition(self):
        parent = self.parentWidget()
        if parent is None:
            return
        self.adjustSize()
        self.move(max(8, parent.width() - self.width() - 22), max(90, parent.height() - self.height() - 28))
        self.raise_()


class Alpha9Controller(QtCore.QObject):
    def __init__(self, main, definition_controller):
        super().__init__(main)
        self.main = main
        self.definition_controller = definition_controller
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(350)
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start()
        self.refresh_status()

    def refresh_status(self):
        label = self.main.findChild(QtWidgets.QLabel, _STATUS)
        if label is None:
            label = QtWidgets.QLabel()
            label.setObjectName(_STATUS)
            self.main.statusBar().addPermanentWidget(label)
        obj = _active_feature()
        profile = _FEATURE_PROFILES[_feature_kind(obj)]
        if profile.kind == "sketch":
            dof = _sketch_dof(obj)
            detail = "Totalmente definido" if dof == 0 else (f"{dof} GDL" if dof is not None else "En edición")
            label.setText(f"Croquis · {detail} · SolidFreeCAD alpha.9 source-only")
        elif obj is not None:
            label.setText(f"{profile.title} · Propiedades nativas · SolidFreeCAD alpha.9 source-only")
        else:
            label.setText("SolidFreeCAD alpha.9 · PropertyManagers dedicados · Sin ejecutable")
        label.show()


def _install_definition_controller(main):
    page = main.findChild(QtWidgets.QWidget, _OPERATION_PAGE)
    if page is None:
        return None
    existing = page.findChild(QtWidgets.QGroupBox, _DEFINITION_CARD)
    if existing is not None:
        return getattr(page, "_alpha9_definition_controller", None)
    controller = FeatureDefinitionController(page)
    page._alpha9_definition_controller = controller
    return controller


def _install_tree_enhancer(main):
    global _tree_enhancer
    tree = main.findChild(QtWidgets.QTreeWidget, _TREE)
    if tree is not None and _tree_enhancer is None:
        _tree_enhancer = TreeStateEnhancer(tree)
    return _tree_enhancer


def _apply_style(main):
    marker = "/* SolidFreeCAD alpha9 feature managers */"
    if marker in main.styleSheet():
        return
    main.setStyleSheet(main.styleSheet() + marker + """
        QGroupBox#SolidFreeCADAlpha9DefinitionCard {
            font-weight: 600; border: 1px solid #aebbc3; margin-top: 8px;
            background: #f7f9fa;
        }
        QLabel#SFCAlpha9FeatureTitle { color: #174f73; font-size: 13px; font-weight: 700; }
        QLabel#SFCAlpha9FeatureInstruction { background: #e9f2f8; color: #285a78; padding: 6px; }
        QLabel#SFCAlpha9SelectionHint { color: #596973; padding: 3px; }
        QLabel#SFCAlpha9SketchSummary { background: #fff1c9; color: #76551a; padding: 6px; }
        QComboBox#SolidFreeCADAlpha9SelectionMode {
            min-width: 145px; background: #ffffff; border: 1px solid #9eabb4; padding: 3px 6px;
        }
        QFrame#SolidFreeCADAlpha9OrientationWidget {
            background: rgba(245, 248, 250, 220); border: 1px solid #91a0a9; border-radius: 5px;
        }
        QFrame#SolidFreeCADAlpha9OrientationWidget QToolButton {
            min-width: 34px; min-height: 28px; background: #ffffff; border: 1px solid #bac5cb;
            font-size: 9px; font-weight: 700;
        }
        QFrame#SolidFreeCADAlpha9OrientationWidget QToolButton:hover {
            background: #e4f1f8; border: 1px solid #2d83b8;
        }
        QTreeWidget#SolidFreeCADFeatureTree::item:selected { background: #cfe8f6; color: #173c52; }
        QStatusBar QLabel#SolidFreeCADAlpha9Status { color: #315668; font-weight: 700; padding: 0 8px; }
    """)


def show_workspace():
    """Show alpha.9 on top of the source-only alpha.8 interaction shell."""
    global _controller, _orientation, _selection_mode
    result = show_alpha8_workspace()
    main = Gui.getMainWindow()
    _apply_style(main)
    definition_controller = _install_definition_controller(main)
    _install_tree_enhancer(main)
    if _selection_mode is None:
        _selection_mode = SelectionModeController(main)
    if _orientation is None:
        _orientation = main.findChild(QtWidgets.QFrame, _ORIENTATION_WIDGET)
    if _orientation is None:
        _orientation = OrientationOverlay(main)
    else:
        _orientation.show()
        _orientation.reposition()
    if definition_controller is not None and _controller is None:
        _controller = Alpha9Controller(main, definition_controller)
    elif _controller is not None:
        _controller.timer.start()
        _controller.refresh_status()
    main.setWindowTitle("SolidFreeCAD Desktop alpha.9 · Feature Manager Prototype")
    return result


def hide_workspace():
    hide_alpha8_workspace()
    main = Gui.getMainWindow()
    if _controller is not None:
        _controller.timer.stop()
    for name, kind in ((_ORIENTATION_WIDGET, QtWidgets.QFrame), (_STATUS, QtWidgets.QLabel)):
        widget = main.findChild(kind, name)
        if widget is not None:
            widget.hide()
    try:
        Gui.Selection.removeSelectionGate()
    except Exception:
        pass
