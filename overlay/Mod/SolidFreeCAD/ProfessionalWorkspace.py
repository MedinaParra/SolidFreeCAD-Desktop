"""SolidFreeCAD alpha.7 professional mechanical-CAD interface prototype.

This layer refines the alpha.6 workspace without replacing FreeCAD's native
commands, BRep engine, FCStd documents or classic compatibility mode.  It adds
an original professional CAD shell: document context bar, command search,
selection-aware task pane, design library, appearance controls and clearer
model-state feedback.

No packaging or executable-generation logic belongs in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from SolidFreeCAD.ClassicWorkspace import _first_available, _icon, _run_candidates
from SolidFreeCAD.MechanicalWorkspace import (
    hide_workspace as hide_alpha6_workspace,
    show_workspace as show_alpha6_workspace,
)

_CONTEXT_BAR = "SolidFreeCADAlpha7ContextBar"
_TASK_PANE = "SolidFreeCADAlpha7TaskPane"
_COMMAND_SEARCH = "SolidFreeCADAlpha7CommandSearch"
_DOCUMENT_SELECTOR = "SolidFreeCADAlpha7DocumentSelector"
_BREADCRUMB = "SolidFreeCADAlpha7Breadcrumb"
_MODEL_STATE = "SolidFreeCADAlpha7ModelState"
_TASK_TABS = "SolidFreeCADAlpha7TaskTabs"
_PARAMETER_FORM = "SolidFreeCADAlpha7ParameterForm"
_STATUS = "SolidFreeCADAlpha7Status"

_context_controller = None
_task_pane = None
_tree_controller = None
_shortcuts = []


@dataclass(frozen=True)
class SearchCommand:
    label: str
    candidates: tuple[str, ...]
    keywords: tuple[str, ...] = ()


_SEARCH_COMMANDS = (
    SearchCommand("Nueva pieza", ("SFC_CreatePart", "Std_New"), ("nuevo", "parte", "pieza")),
    SearchCommand("Abrir archivo", ("SFC_Open", "Std_Open"), ("abrir", "fcstd", "step")),
    SearchCommand("Guardar", ("SFC_Save", "Std_Save"), ("guardar", "save")),
    SearchCommand("Nuevo croquis", ("SFC_NewSketch", "Sketcher_NewSketch"), ("croquis", "sketch")),
    SearchCommand("Saliente / Base", ("SFC_Pad", "PartDesign_Pad"), ("extruir", "pad", "saliente")),
    SearchCommand("Corte extruido", ("SFC_Pocket", "PartDesign_Pocket"), ("corte", "pocket")),
    SearchCommand("Revolución", ("SFC_Revolution", "PartDesign_Revolution"), ("revolucion", "giro")),
    SearchCommand("Redondeo", ("SFC_Fillet", "PartDesign_Fillet"), ("fillet", "radio")),
    SearchCommand("Chaflán", ("SFC_Chamfer", "PartDesign_Chamfer"), ("chaflan", "chamfer")),
    SearchCommand("Ajustar vista", ("ViewFit", "Std_ViewFitAll"), ("fit", "encuadrar")),
    SearchCommand("Vista isométrica", ("SFC_FitAxonometric", "ViewAxonometric"), ("isometrica", "iso")),
    SearchCommand("Vista frontal", ("Std_ViewFront",), ("frontal", "front")),
    SearchCommand("Vista superior", ("Std_ViewTop",), ("superior", "top")),
    SearchCommand("Medir", ("Std_Measure", "Part_Measure_Menu"), ("medida", "distancia")),
    SearchCommand("Recalcular modelo", ("Std_Refresh",), ("recalcular", "rebuild", "actualizar")),
)


def _active_document():
    return App.ActiveDocument


def _selected_object():
    selected = Gui.Selection.getSelection()
    return selected[0] if selected else None


def _shape_state(obj) -> str:
    shape = getattr(obj, "Shape", None)
    if shape is None or getattr(shape, "isNull", lambda: True)():
        return "Sin BRep"
    try:
        return "BRep válido" if shape.isValid() else "BRep con errores"
    except Exception:
        return "BRep disponible"


def _run_search_command(entry: SearchCommand) -> bool:
    return _run_candidates(entry.candidates)


class CommandSearch(QtWidgets.QLineEdit):
    """Compact command search that delegates only to registered FreeCAD commands."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(_COMMAND_SEARCH)
        self.setPlaceholderText("Buscar comando  Ctrl+K")
        self.setClearButtonEnabled(True)
        self.setMinimumWidth(230)
        self.setMaximumWidth(360)
        labels = [entry.label for entry in _SEARCH_COMMANDS]
        completer = QtWidgets.QCompleter(labels, self)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer.setFilterMode(QtCore.Qt.MatchContains)
        self.setCompleter(completer)
        self.returnPressed.connect(self.execute_query)

    def execute_query(self):
        query = self.text().strip().lower()
        if not query:
            return
        ranked = []
        for entry in _SEARCH_COMMANDS:
            haystack = " ".join((entry.label, *entry.keywords)).lower()
            if query == entry.label.lower():
                ranked.insert(0, entry)
            elif query in haystack:
                ranked.append(entry)
        if ranked and _run_search_command(ranked[0]):
            self.clear()
            return
        App.Console.PrintWarning(f"SolidFreeCAD: no se encontró un comando disponible para '{query}'.\n")
        self.selectAll()


class _SelectionObserver:
    def __init__(self, callback):
        self.callback = callback

    def addSelection(self, *_args):
        self.callback()

    def removeSelection(self, *_args):
        self.callback()

    def clearSelection(self, *_args):
        self.callback()


class ContextController(QtCore.QObject):
    """Keeps the top context strip synchronized with documents and selections."""

    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.toolbar = self._build_toolbar()
        self._observer = _SelectionObserver(self.refresh)
        Gui.Selection.addObserver(self._observer)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(650)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()
        self.refresh()

    def _build_toolbar(self):
        toolbar = self.main.findChild(QtWidgets.QToolBar, _CONTEXT_BAR)
        if toolbar is not None:
            toolbar.show()
            return toolbar
        toolbar = QtWidgets.QToolBar("Contexto de diseño", self.main)
        toolbar.setObjectName(_CONTEXT_BAR)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QtCore.QSize(18, 18))

        caption = QtWidgets.QLabel("Documento")
        caption.setObjectName("SFCAlpha7ContextCaption")
        toolbar.addWidget(caption)

        self.documents = QtWidgets.QComboBox()
        self.documents.setObjectName(_DOCUMENT_SELECTOR)
        self.documents.setMinimumWidth(145)
        self.documents.currentIndexChanged.connect(self.activate_document)
        toolbar.addWidget(self.documents)
        toolbar.addSeparator()

        self.breadcrumb = QtWidgets.QLabel("Inicio")
        self.breadcrumb.setObjectName(_BREADCRUMB)
        self.breadcrumb.setMinimumWidth(240)
        toolbar.addWidget(self.breadcrumb)

        self.state = QtWidgets.QLabel("Sin documento")
        self.state.setObjectName(_MODEL_STATE)
        toolbar.addWidget(self.state)
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        self.search = CommandSearch(toolbar)
        toolbar.addWidget(self.search)
        rebuild = toolbar.addAction(_icon("evaluacion/comprobar.svg"), "Recalcular")
        rebuild.setToolTip("Recalcular el documento activo")
        rebuild.triggered.connect(self.recompute)

        self.main.addToolBar(QtCore.Qt.TopToolBarArea, toolbar)
        return toolbar

    def refresh(self):
        names = list(App.listDocuments().keys())
        current_name = App.ActiveDocument.Name if App.ActiveDocument else ""
        previous = self.documents.blockSignals(True)
        self.documents.clear()
        self.documents.addItem("—")
        for name in names:
            doc = App.getDocument(name)
            self.documents.addItem(doc.Label or name, name)
        index = self.documents.findData(current_name)
        self.documents.setCurrentIndex(index if index >= 0 else 0)
        self.documents.blockSignals(previous)

        doc = App.ActiveDocument
        obj = _selected_object()
        if doc is None:
            self.breadcrumb.setText("Inicio  ›  Sin documento")
            self.state.setText("Sin documento")
            self.state.setProperty("state", "idle")
        elif obj is None:
            self.breadcrumb.setText(f"{doc.Label or doc.Name}  ›  Modelo")
            self.state.setText("Modelo actualizado" if not doc.RecomputesFrozen else "Recomputación pausada")
            self.state.setProperty("state", "ok")
        else:
            self.breadcrumb.setText(f"{doc.Label or doc.Name}  ›  {obj.Label or obj.Name}")
            state = _shape_state(obj)
            self.state.setText(state)
            self.state.setProperty("state", "warning" if "errores" in state else "ok")
        self.state.style().unpolish(self.state)
        self.state.style().polish(self.state)

    def activate_document(self, index):
        name = self.documents.itemData(index)
        if not name:
            return
        try:
            Gui.activeDocument().activeView()
            App.setActiveDocument(name)
            Gui.activeDocument().activeView().fitAll()
        except Exception as exc:
            App.Console.PrintWarning(f"SolidFreeCAD: no se pudo activar {name}: {exc}\n")

    def recompute(self):
        doc = App.ActiveDocument
        if doc is None:
            return
        try:
            doc.recompute()
            self.refresh()
        except Exception as exc:
            App.Console.PrintError(f"SolidFreeCAD: error al recalcular: {exc}\n")


class ParameterEditor(QtWidgets.QWidget):
    """Edits common numeric properties of the current native FreeCAD object."""

    SUPPORTED = (
        "App::PropertyLength",
        "App::PropertyDistance",
        "App::PropertyAngle",
        "App::PropertyFloat",
        "App::PropertyInteger",
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(_PARAMETER_FORM)
        self._object = None
        self._updating = False
        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)

    def clear(self):
        while self.layout.rowCount():
            self.layout.removeRow(0)

    def set_object(self, obj):
        self._object = obj
        self._updating = True
        self.clear()
        if obj is None:
            self.layout.addRow(QtWidgets.QLabel("Seleccione una operación o pieza."))
            self._updating = False
            return
        added = 0
        for name in getattr(obj, "PropertiesList", []):
            try:
                type_id = obj.getTypeIdOfProperty(name)
            except Exception:
                continue
            if type_id not in self.SUPPORTED or name in {"Placement", "Label"}:
                continue
            try:
                raw = getattr(obj, name)
                value = float(getattr(raw, "Value", raw))
            except Exception:
                continue
            editor = QtWidgets.QDoubleSpinBox()
            editor.setDecimals(3)
            editor.setRange(-1.0e9, 1.0e9)
            editor.setSingleStep(1.0)
            editor.setValue(value)
            editor.setProperty("propertyName", name)
            editor.valueChanged.connect(lambda new_value, prop=name: self.apply_value(prop, new_value))
            self.layout.addRow(name, editor)
            added += 1
            if added >= 12:
                break
        if not added:
            self.layout.addRow(QtWidgets.QLabel("La selección no expone parámetros numéricos editables."))
        self._updating = False

    def apply_value(self, property_name: str, value: float):
        if self._updating or self._object is None or App.ActiveDocument is None:
            return
        try:
            App.ActiveDocument.openTransaction(f"Editar {property_name}")
            setattr(self._object, property_name, value)
            App.ActiveDocument.recompute()
            App.ActiveDocument.commitTransaction()
        except Exception as exc:
            try:
                App.ActiveDocument.abortTransaction()
            except Exception:
                pass
            App.Console.PrintError(f"SolidFreeCAD: no se pudo editar {property_name}: {exc}\n")


class TaskPane(QtWidgets.QDockWidget):
    """Right-side task pane with native-object actions and original UI resources."""

    def __init__(self, main):
        super().__init__("Panel de tareas", main)
        self.setObjectName(_TASK_PANE)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.setMinimumWidth(285)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setObjectName(_TASK_TABS)
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._tasks_page(), "Tareas")
        self.tabs.addTab(self._library_page(), "Biblioteca")
        self.tabs.addTab(self._appearance_page(), "Apariencias")
        self.tabs.addTab(self._resources_page(), "Recursos")
        self.setWidget(self.tabs)
        self._observer = _SelectionObserver(self.refresh_selection)
        Gui.Selection.addObserver(self._observer)
        self.refresh_selection()

    def _tasks_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        title = QtWidgets.QLabel("Selección activa")
        title.setObjectName("SFCAlpha7SectionTitle")
        layout.addWidget(title)
        self.selection_name = QtWidgets.QLabel("Sin selección")
        self.selection_name.setObjectName("SFCAlpha7SelectionName")
        self.selection_name.setWordWrap(True)
        layout.addWidget(self.selection_name)
        self.shape_state = QtWidgets.QLabel("Seleccione un objeto para revisar su estado.")
        self.shape_state.setObjectName("SFCAlpha7ShapeState")
        layout.addWidget(self.shape_state)

        quick = QtWidgets.QGroupBox("Acciones rápidas")
        quick_layout = QtWidgets.QGridLayout(quick)
        actions = (
            ("Editar", "propertymanager/aceptar.svg", self.edit_selected),
            ("Mostrar/Ocultar", "vistas/mostrar_ocultar.svg", self.toggle_visibility),
            ("Zoom", "vistas/ajustar.svg", self.fit_selection),
            ("Recalcular", "evaluacion/comprobar.svg", self.recompute),
        )
        for index, (label, icon, callback) in enumerate(actions):
            button = QtWidgets.QPushButton(label)
            button.setIcon(_icon(icon))
            button.clicked.connect(callback)
            quick_layout.addWidget(button, index // 2, index % 2)
        layout.addWidget(quick)

        parameters = QtWidgets.QGroupBox("Parámetros")
        parameters_layout = QtWidgets.QVBoxLayout(parameters)
        self.parameter_editor = ParameterEditor()
        parameters_layout.addWidget(self.parameter_editor)
        layout.addWidget(parameters, 1)
        return page

    def _library_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        note = QtWidgets.QLabel("Accesos de diseño mecánico que usan comandos nativos disponibles.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.library = QtWidgets.QTreeWidget()
        self.library.setObjectName("SolidFreeCADAlpha7DesignLibrary")
        self.library.setHeaderHidden(True)
        entries = (
            ("Plantillas", (
                ("Nueva pieza", "archivo/nuevo.svg", ("SFC_CreatePart", "Std_New")),
                ("Nuevo ensamblaje", "archivo/nuevo.svg", ("Assembly_CreateAssembly", "Assembly_NewAssembly")),
                ("Abrir componente", "archivo/abrir.svg", ("SFC_Open", "Std_Open")),
            )),
            ("Operaciones frecuentes", (
                ("Nuevo croquis", "croquis/nuevo_croquis.svg", ("SFC_NewSketch", "Sketcher_NewSketch")),
                ("Saliente / Base", "operaciones/saliente_base.svg", ("SFC_Pad", "PartDesign_Pad")),
                ("Corte extruido", "operaciones/corte_extruido.svg", ("SFC_Pocket", "PartDesign_Pocket")),
                ("Revolución", "operaciones/revolucion.svg", ("SFC_Revolution", "PartDesign_Revolution")),
                ("Redondeo", "operaciones/redondeo.svg", ("SFC_Fillet", "PartDesign_Fillet")),
            )),
            ("Evaluación", (
                ("Medir", "evaluacion/medir.svg", ("Std_Measure", "Part_Measure_Menu")),
                ("Ajustar vista", "vistas/ajustar.svg", ("ViewFit", "Std_ViewFitAll")),
            )),
        )
        for group_label, children in entries:
            group = QtWidgets.QTreeWidgetItem([group_label])
            self.library.addTopLevelItem(group)
            for label, icon, commands in children:
                item = QtWidgets.QTreeWidgetItem([label])
                item.setIcon(0, _icon(icon))
                item.setData(0, QtCore.Qt.UserRole, commands)
                item.setDisabled(_first_available(commands) is None)
                group.addChild(item)
            group.setExpanded(True)
        self.library.itemDoubleClicked.connect(self.run_library_item)
        layout.addWidget(self.library, 1)
        return page

    def _appearance_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        info = QtWidgets.QLabel("Los cambios se aplican al objeto seleccionado y se guardan en el documento.")
        info.setWordWrap(True)
        layout.addWidget(info)
        self.visibility = QtWidgets.QCheckBox("Visible")
        self.visibility.toggled.connect(self.set_visibility)
        layout.addWidget(self.visibility)
        color = QtWidgets.QPushButton("Color de pieza…")
        color.setIcon(_icon("evaluacion/comprobar.svg"))
        color.clicked.connect(self.choose_color)
        layout.addWidget(color)
        layout.addWidget(QtWidgets.QLabel("Transparencia"))
        self.transparency = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.transparency.setRange(0, 100)
        self.transparency.valueChanged.connect(self.set_transparency)
        layout.addWidget(self.transparency)
        layout.addStretch(1)
        return page

    def _resources_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(QtWidgets.QLabel("Documentos abiertos"))
        self.documents = QtWidgets.QListWidget()
        self.documents.setObjectName("SolidFreeCADAlpha7OpenDocuments")
        self.documents.itemDoubleClicked.connect(self.activate_resource_document)
        layout.addWidget(self.documents, 1)
        refresh = QtWidgets.QPushButton("Actualizar lista")
        refresh.clicked.connect(self.refresh_documents)
        layout.addWidget(refresh)
        compatibility = QtWidgets.QLabel(
            "Formato nativo FCStd · Motor OpenCASCADE · Interfaz clásica disponible como respaldo."
        )
        compatibility.setObjectName("SFCAlpha7CompatibilityNote")
        compatibility.setWordWrap(True)
        layout.addWidget(compatibility)
        return page

    def refresh_selection(self):
        obj = _selected_object()
        blocked = self.visibility.blockSignals(True)
        blocked_transparency = self.transparency.blockSignals(True)
        if obj is None:
            self.selection_name.setText("Sin selección")
            self.shape_state.setText("Seleccione un objeto para revisar su estado.")
            self.visibility.setChecked(False)
            self.transparency.setValue(0)
        else:
            self.selection_name.setText(f"{obj.Label or obj.Name}\n{obj.TypeId}")
            self.shape_state.setText(_shape_state(obj))
            view = getattr(obj, "ViewObject", None)
            self.visibility.setChecked(bool(view and view.Visibility))
            self.transparency.setValue(int(getattr(view, "Transparency", 0)) if view else 0)
        self.visibility.blockSignals(blocked)
        self.transparency.blockSignals(blocked_transparency)
        self.parameter_editor.set_object(obj)
        self.refresh_documents()

    def run_library_item(self, item, _column):
        commands = item.data(0, QtCore.Qt.UserRole)
        if commands:
            _run_candidates(tuple(commands))

    def edit_selected(self):
        obj = _selected_object()
        if obj is None or Gui.activeDocument() is None:
            return
        try:
            Gui.activeDocument().setEdit(obj.Name)
        except Exception as exc:
            App.Console.PrintWarning(f"SolidFreeCAD: el objeto no admite edición directa: {exc}\n")

    def toggle_visibility(self):
        obj = _selected_object()
        if obj is not None and hasattr(obj, "ViewObject"):
            obj.ViewObject.Visibility = not obj.ViewObject.Visibility
            self.refresh_selection()

    def fit_selection(self):
        if Gui.activeDocument() is None:
            return
        try:
            Gui.activeDocument().activeView().fitSelection()
        except Exception:
            Gui.activeDocument().activeView().fitAll()

    def recompute(self):
        if App.ActiveDocument is not None:
            App.ActiveDocument.recompute()
            self.refresh_selection()

    def set_visibility(self, visible):
        obj = _selected_object()
        if obj is not None and hasattr(obj, "ViewObject"):
            obj.ViewObject.Visibility = bool(visible)

    def choose_color(self):
        obj = _selected_object()
        if obj is None or not hasattr(obj, "ViewObject"):
            return
        current = getattr(obj.ViewObject, "ShapeColor", (0.72, 0.72, 0.78))
        initial = QtGui.QColor.fromRgbF(*current[:3])
        color = QtWidgets.QColorDialog.getColor(initial, self, "Color de pieza")
        if color.isValid():
            red, green, blue, _alpha = color.getRgbF()
            obj.ViewObject.ShapeColor = (red, green, blue)

    def set_transparency(self, value):
        obj = _selected_object()
        if obj is not None and hasattr(obj, "ViewObject"):
            obj.ViewObject.Transparency = int(value)

    def refresh_documents(self):
        if not hasattr(self, "documents"):
            return
        current = self.documents.currentItem().data(QtCore.Qt.UserRole) if self.documents.currentItem() else None
        self.documents.clear()
        for name, doc in App.listDocuments().items():
            item = QtWidgets.QListWidgetItem(doc.Label or name)
            item.setData(QtCore.Qt.UserRole, name)
            self.documents.addItem(item)
            if name == current:
                self.documents.setCurrentItem(item)

    def activate_resource_document(self, item):
        name = item.data(QtCore.Qt.UserRole)
        if name:
            App.setActiveDocument(name)
            self.refresh_selection()

    def closeEvent(self, event):
        event.ignore()
        self.hide()


class FeatureTreeController(QtCore.QObject):
    """Adds safe context actions to the alpha.6 model history tree."""

    def __init__(self, tree):
        super().__init__(tree)
        self.tree = tree
        tree.setAlternatingRowColors(True)
        tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(self.open_menu)

    def open_menu(self, position):
        item = self.tree.itemAt(position)
        name = item.data(0, QtCore.Qt.UserRole) if item else None
        obj = App.ActiveDocument.getObject(name) if name and App.ActiveDocument else None
        if obj is None:
            return
        menu = QtWidgets.QMenu(self.tree)
        edit = menu.addAction("Editar operación")
        visibility = menu.addAction("Mostrar / Ocultar")
        zoom = menu.addAction("Zoom a selección")
        chosen = menu.exec_(self.tree.viewport().mapToGlobal(position))
        if chosen == edit:
            try:
                Gui.activeDocument().setEdit(obj.Name)
            except Exception:
                pass
        elif chosen == visibility and hasattr(obj, "ViewObject"):
            obj.ViewObject.Visibility = not obj.ViewObject.Visibility
        elif chosen == zoom and Gui.activeDocument() is not None:
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(obj)
            try:
                Gui.activeDocument().activeView().fitSelection()
            except Exception:
                Gui.activeDocument().activeView().fitAll()


def _install_shortcuts(main, search):
    global _shortcuts
    if _shortcuts:
        return
    focus_search = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+K"), main)
    focus_search.activated.connect(lambda: (search.setFocus(), search.selectAll()))
    escape = QtWidgets.QShortcut(QtGui.QKeySequence("Esc"), main)
    escape.activated.connect(lambda: Gui.Control.closeDialog())
    _shortcuts = [focus_search, escape]


def _enhance_feature_manager(main):
    global _tree_controller
    manager = main.findChild(QtWidgets.QDockWidget, "SolidFreeCADFeatureManager")
    tree = main.findChild(QtWidgets.QTreeWidget, "SolidFreeCADFeatureTree")
    if manager is not None:
        manager.setWindowTitle("Diseño")
        manager.setMinimumWidth(300)
    if tree is not None and _tree_controller is None:
        _tree_controller = FeatureTreeController(tree)


def _show_task_pane(main):
    global _task_pane
    if _task_pane is None:
        _task_pane = main.findChild(QtWidgets.QDockWidget, _TASK_PANE)
    if _task_pane is None:
        _task_pane = TaskPane(main)
        main.addDockWidget(QtCore.Qt.RightDockWidgetArea, _task_pane)
    _task_pane.show()
    return _task_pane


def _apply_alpha7_style(main):
    marker = "/* SolidFreeCAD alpha7 professional interface */"
    if marker in main.styleSheet():
        return
    main.setStyleSheet(main.styleSheet() + marker + """
        QToolBar#SolidFreeCADAlpha7ContextBar {
            background: #edf1f4; border-top: 1px solid #ffffff;
            border-bottom: 1px solid #aab5bd; spacing: 5px; padding: 3px 5px;
        }
        QLabel#SFCAlpha7ContextCaption { color: #4d5c66; font-weight: 600; }
        QComboBox#SolidFreeCADAlpha7DocumentSelector,
        QLineEdit#SolidFreeCADAlpha7CommandSearch {
            background: #ffffff; border: 1px solid #9eabb4; border-radius: 2px; padding: 3px 6px;
        }
        QLabel#SolidFreeCADAlpha7Breadcrumb { color: #24333d; font-weight: 600; padding: 2px 7px; }
        QLabel#SolidFreeCADAlpha7ModelState { border-radius: 8px; padding: 2px 8px; }
        QLabel#SolidFreeCADAlpha7ModelState[state="idle"] { background: #dfe5e9; color: #59666e; }
        QLabel#SolidFreeCADAlpha7ModelState[state="ok"] { background: #dff0e3; color: #285c36; }
        QLabel#SolidFreeCADAlpha7ModelState[state="warning"] { background: #f8e1d8; color: #8a392b; }
        QDockWidget#SolidFreeCADAlpha7TaskPane { background: #f5f7f8; }
        QTabWidget#SolidFreeCADAlpha7TaskTabs::pane { border: 1px solid #aeb8bf; background: #f7f8f9; }
        QTabWidget#SolidFreeCADAlpha7TaskTabs QTabBar::tab { padding: 6px 8px; min-width: 58px; }
        QTabWidget#SolidFreeCADAlpha7TaskTabs QTabBar::tab:selected {
            background: #ffffff; color: #165f91; border-bottom: 2px solid #2d83b8;
        }
        QLabel#SFCAlpha7SectionTitle { color: #1f4f70; font-size: 13px; font-weight: 700; }
        QLabel#SFCAlpha7SelectionName { background: #ffffff; border: 1px solid #c2cbd1; padding: 7px; }
        QLabel#SFCAlpha7ShapeState { background: #e8f2f8; color: #285a78; padding: 5px; }
        QLabel#SFCAlpha7CompatibilityNote { color: #5f6e77; background: #edf1f3; padding: 7px; }
        QTreeWidget#SolidFreeCADAlpha7DesignLibrary { background: #ffffff; border: 1px solid #c2cbd1; }
        QTreeWidget#SolidFreeCADFeatureTree { alternate-background-color: #f4f7f9; }
        QStatusBar QLabel#SolidFreeCADAlpha7Status { color: #40515b; font-weight: 600; padding: 0 8px; }
    """)


def show_workspace():
    """Show alpha.7 UI on top of the validated alpha.6 mechanical workspace."""
    global _context_controller
    result = show_alpha6_workspace()
    main = Gui.getMainWindow()
    _apply_alpha7_style(main)
    _enhance_feature_manager(main)
    task = _show_task_pane(main)
    if _context_controller is None:
        _context_controller = ContextController(main)
    else:
        _context_controller.toolbar.show()
        _context_controller.refresh()
    _install_shortcuts(main, _context_controller.search)
    task.refresh_selection()

    status = main.findChild(QtWidgets.QLabel, _STATUS)
    if status is None:
        status = QtWidgets.QLabel("SolidFreeCAD alpha.7 · Prototipo de interfaz · Sin paquete publicado")
        status.setObjectName(_STATUS)
        main.statusBar().addPermanentWidget(status)
    status.show()
    return result


def hide_workspace():
    hide_alpha6_workspace()
    main = Gui.getMainWindow()
    for name, kind in ((_CONTEXT_BAR, QtWidgets.QToolBar), (_TASK_PANE, QtWidgets.QDockWidget)):
        widget = main.findChild(kind, name)
        if widget is not None:
            widget.hide()
    status = main.findChild(QtWidgets.QLabel, _STATUS)
    if status is not None:
        status.hide()
