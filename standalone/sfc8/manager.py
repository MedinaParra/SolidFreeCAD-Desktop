"""Single left-side manager owned by SolidFreeCAD alpha.9.

The manager reproduces the interaction mechanics of a professional parametric CAD:
one persistent dock alternates between design tree, contextual PropertyManager and
configurations. No secondary property dock or native FreeCAD task panel is used.
"""
from __future__ import annotations

import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from . import backend


class CollapsibleSection(QtWidgets.QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = QtWidgets.QToolButton()
        self.header.setObjectName("SFC9SectionHeader")
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setChecked(True)
        self.header.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.header.setArrowType(QtCore.Qt.DownArrow)
        self.header.toggled.connect(self._toggle)
        root.addWidget(self.header)

        self.body = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout(self.body)
        self.layout.setContentsMargins(7, 7, 7, 8)
        self.layout.setSpacing(6)
        root.addWidget(self.body)

    def _toggle(self, checked: bool):
        self.body.setVisible(checked)
        self.header.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)


class FeatureTree(QtWidgets.QTreeWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setObjectName("SFC9FeatureTree")
        self.setHeaderHidden(True)
        self.setIndentation(14)
        self.setUniformRowHeights(True)
        self.itemSelectionChanged.connect(self._selection_changed)
        self.itemDoubleClicked.connect(self._double_clicked)

    def rebuild(self):
        current = None
        items = self.selectedItems()
        if items:
            current = items[0].data(0, QtCore.Qt.UserRole)

        self.clear()
        doc = backend.active_document()
        if doc is None:
            root = QtWidgets.QTreeWidgetItem(["Sin documento"])
            root.addChild(QtWidgets.QTreeWidgetItem(["Nueva pieza para comenzar"]))
            self.addTopLevelItem(root)
            root.setExpanded(True)
            return

        root = QtWidgets.QTreeWidgetItem([doc.Label or doc.Name])
        root.setData(0, QtCore.Qt.UserRole, "__document__")
        self.addTopLevelItem(root)
        for label in ("Historial", "Sensores", "Anotaciones", "Material <sin especificar>"):
            root.addChild(QtWidgets.QTreeWidgetItem([label]))

        origin = QtWidgets.QTreeWidgetItem(["Origen"])
        origin.setExpanded(False)
        for plane in ("Alzado", "Planta", "Vista lateral"):
            origin.addChild(QtWidgets.QTreeWidgetItem([plane]))
        root.addChild(origin)

        selected_item = None
        for obj in doc.Objects:
            if obj.TypeId == "PartDesign::Body":
                continue
            label = obj.Label or obj.Name
            item = QtWidgets.QTreeWidgetItem([label])
            item.setData(0, QtCore.Qt.UserRole, obj.Name)
            if getattr(getattr(obj, "ViewObject", None), "Visibility", True) is False:
                item.setText(0, f"{label} (oculto)")
            root.addChild(item)
            if obj.Name == current:
                selected_item = item

        root.setExpanded(True)
        if selected_item is not None:
            self.setCurrentItem(selected_item)

    def _selection_changed(self):
        items = self.selectedItems()
        if not items:
            return
        name = items[0].data(0, QtCore.Qt.UserRole)
        if name and name != "__document__":
            self.owner.on_tree_selection(name)

    def _double_clicked(self, item, _column):
        name = item.data(0, QtCore.Qt.UserRole)
        if name and name != "__document__":
            self.owner.on_tree_double_click(name)


class ManagerDock(QtWidgets.QDockWidget):
    """Single persistent manager replacing all previous alpha.8 panels."""

    def __init__(self, owner):
        super().__init__("Administrador", owner)
        self.owner = owner
        self.setObjectName("SFC9ManagerDock")
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.setMinimumWidth(250)
        self.setMaximumWidth(340)

        self.operation = None
        self.operation_object_name = None
        self.rollback_on_cancel = False
        self.selected_name = None

        page = QtWidgets.QWidget()
        root = QtWidgets.QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.tabs = QtWidgets.QTabBar()
        self.tabs.setObjectName("SFC9ManagerTabs")
        self.tabs.setShape(QtWidgets.QTabBar.RoundedNorth)
        self.tabs.setExpanding(True)
        self.tabs.addTab("Modelo")
        self.tabs.addTab("Propiedades")
        self.tabs.addTab("Configuraciones")
        self.tabs.currentChanged.connect(self._tab_changed)
        root.addWidget(self.tabs)

        self.stack = QtWidgets.QStackedWidget()
        self.stack.addWidget(self._model_page())
        self.stack.addWidget(self._property_page())
        self.stack.addWidget(self._configuration_page())
        root.addWidget(self.stack, 1)
        self.setWidget(page)

        self.show_model()

    def _tab_changed(self, index: int):
        self.stack.setCurrentIndex(index)

    def _model_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        self.filter = QtWidgets.QLineEdit()
        self.filter.setPlaceholderText("Filtrar historial")
        self.filter.setClearButtonEnabled(True)
        layout.addWidget(self.filter)
        self.tree = FeatureTree(self.owner)
        layout.addWidget(self.tree, 1)
        footer = QtWidgets.QLabel("Historial paramétrico · FCStd")
        footer.setObjectName("SFC9ManagerFooter")
        layout.addWidget(footer)
        return page

    def _property_page(self):
        page = QtWidgets.QWidget()
        root = QtWidgets.QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QtWidgets.QWidget()
        header.setObjectName("SFC9PropertyHeader")
        row = QtWidgets.QHBoxLayout(header)
        row.setContentsMargins(7, 5, 7, 5)
        row.setSpacing(5)
        self.accept = QtWidgets.QToolButton()
        self.accept.setObjectName("SFC9Accept")
        self.accept.setText("✓")
        self.accept.setToolTip("Aceptar operación")
        self.accept.clicked.connect(self.owner.accept_manager_operation)
        row.addWidget(self.accept)
        self.cancel = QtWidgets.QToolButton()
        self.cancel.setObjectName("SFC9Cancel")
        self.cancel.setText("✕")
        self.cancel.setToolTip("Cancelar operación")
        self.cancel.clicked.connect(self.owner.cancel_manager_operation)
        row.addWidget(self.cancel)
        self.property_title = QtWidgets.QLabel("Propiedades")
        self.property_title.setObjectName("SFC9PropertyTitle")
        row.addWidget(self.property_title, 1)
        root.addWidget(header)

        scroll = QtWidgets.QScrollArea()
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        body = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(body)
        layout.setContentsMargins(5, 5, 5, 8)
        layout.setSpacing(5)

        self.message = QtWidgets.QLabel("Seleccione una operación o un elemento del árbol.")
        self.message.setObjectName("SFC9PropertyMessage")
        self.message.setWordWrap(True)
        layout.addWidget(self.message)

        self.selection_section = CollapsibleSection("Selecciones")
        self.selection_box = QtWidgets.QLabel("Sin selección")
        self.selection_box.setObjectName("SFC9SelectionBox")
        self.selection_box.setWordWrap(True)
        self.selection_section.layout.addWidget(self.selection_box)
        layout.addWidget(self.selection_section)

        self.sketch_section = CollapsibleSection("Parámetros de croquis")
        sketch_form = QtWidgets.QFormLayout()
        self.width = self._spin(100.0)
        self.height = self._spin(60.0)
        self.radius = self._spin(25.0)
        sketch_form.addRow("Ancho", self.width)
        sketch_form.addRow("Alto", self.height)
        sketch_form.addRow("Radio", self.radius)
        self.sketch_section.layout.addLayout(sketch_form)
        sketch_buttons = QtWidgets.QHBoxLayout()
        rectangle = QtWidgets.QPushButton("Rectángulo")
        rectangle.clicked.connect(self.owner.add_rectangle)
        sketch_buttons.addWidget(rectangle)
        circle = QtWidgets.QPushButton("Círculo")
        circle.clicked.connect(self.owner.add_circle)
        sketch_buttons.addWidget(circle)
        self.sketch_section.layout.addLayout(sketch_buttons)
        layout.addWidget(self.sketch_section)

        self.relations_section = CollapsibleSection("Relaciones existentes")
        self.relations = QtWidgets.QListWidget()
        self.relations.setMaximumHeight(115)
        self.relations_section.layout.addWidget(self.relations)
        self.definition = QtWidgets.QLabel("Estado: subdefinido")
        self.definition.setObjectName("SFC9Definition")
        self.relations_section.layout.addWidget(self.definition)
        layout.addWidget(self.relations_section)

        self.pad_section = CollapsibleSection("Dirección 1")
        pad_form = QtWidgets.QFormLayout()
        self.pad_length = self._spin(20.0)
        self.reverse = QtWidgets.QCheckBox("Invertir dirección")
        self.preview = QtWidgets.QCheckBox("Vista preliminar")
        self.preview.setChecked(True)
        pad_form.addRow("Profundidad", self.pad_length)
        pad_form.addRow("", self.reverse)
        pad_form.addRow("", self.preview)
        self.pad_section.layout.addLayout(pad_form)
        layout.addWidget(self.pad_section)

        self.object_section = CollapsibleSection("Propiedades del elemento")
        object_form = QtWidgets.QFormLayout()
        self.object_label = QtWidgets.QLineEdit()
        self.object_label.editingFinished.connect(self._rename_selected)
        self.object_type = QtWidgets.QLabel("—")
        self.object_visible = QtWidgets.QCheckBox("Visible")
        self.object_visible.toggled.connect(self._visibility_changed)
        object_form.addRow("Nombre", self.object_label)
        object_form.addRow("Tipo", self.object_type)
        object_form.addRow("Visualización", self.object_visible)
        self.object_section.layout.addLayout(object_form)
        layout.addWidget(self.object_section)

        layout.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)
        return page

    def _configuration_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(5, 5, 5, 5)
        tree = QtWidgets.QTreeWidget()
        tree.setHeaderLabels(["Configuración", "Estado"])
        active = QtWidgets.QTreeWidgetItem(["Predeterminado", "Activa"])
        tree.addTopLevelItem(active)
        layout.addWidget(tree, 1)
        note = QtWidgets.QLabel(
            "Las configuraciones dimensionales se implementarán sobre las propiedades paramétricas del documento."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        return page

    def _spin(self, value: float):
        control = QtWidgets.QDoubleSpinBox()
        control.setRange(0.1, 100000.0)
        control.setDecimals(2)
        control.setValue(value)
        control.setSuffix(" mm")
        control.setKeyboardTracking(False)
        return control

    def _set_sections(self, *, selection=False, sketch=False, relations=False, pad=False, obj=False):
        self.selection_section.setVisible(selection)
        self.sketch_section.setVisible(sketch)
        self.relations_section.setVisible(relations)
        self.pad_section.setVisible(pad)
        self.object_section.setVisible(obj)

    def rebuild_tree(self):
        self.tree.rebuild()

    def show_model(self):
        self.operation = None
        self.operation_object_name = None
        self.rollback_on_cancel = False
        self.tabs.setCurrentIndex(0)
        self.accept.setEnabled(False)
        self.cancel.setEnabled(False)
        self.rebuild_tree()

    def begin_sketch(self, sketch_name: str, rollback_on_cancel=True):
        self.operation = "sketch"
        self.operation_object_name = sketch_name
        self.rollback_on_cancel = bool(rollback_on_cancel)
        self.property_title.setText("Croquis")
        self.message.setText(
            "Cree geometría, aplique relaciones y acepte el croquis sin abandonar SolidFreeCAD."
        )
        self.selection_box.setText("Plano XY · " + sketch_name)
        self._set_sections(selection=True, sketch=True, relations=True)
        self._refresh_relations()
        self.accept.setEnabled(True)
        self.cancel.setEnabled(True)
        self.tabs.setCurrentIndex(1)

    def begin_pad(self, sketch_name: str):
        self.operation = "pad"
        self.operation_object_name = sketch_name
        self.rollback_on_cancel = False
        self.property_title.setText("Saliente/Base extruido")
        self.message.setText(
            "Defina la profundidad y confirme. La operación no se crea hasta pulsar aceptar."
        )
        self.selection_box.setText("Perfil: " + sketch_name)
        self._set_sections(selection=True, pad=True)
        self.accept.setEnabled(True)
        self.cancel.setEnabled(True)
        self.tabs.setCurrentIndex(1)

    def show_object(self, obj):
        if obj is None or self.operation is not None:
            return
        self.selected_name = obj.Name
        self.property_title.setText(obj.Label or obj.Name)
        self.message.setText("Propiedades del elemento seleccionado en el historial.")
        self.selection_box.setText(f"{obj.Label or obj.Name} ({obj.Name})")
        self.object_label.blockSignals(True)
        self.object_label.setText(obj.Label or obj.Name)
        self.object_label.blockSignals(False)
        self.object_type.setText(obj.TypeId)
        visible = bool(getattr(getattr(obj, "ViewObject", None), "Visibility", False))
        self.object_visible.blockSignals(True)
        self.object_visible.setChecked(visible)
        self.object_visible.blockSignals(False)
        self._set_sections(selection=True, obj=True)
        self.accept.setEnabled(False)
        self.cancel.setEnabled(False)
        self.tabs.setCurrentIndex(1)

    def finish_operation(self):
        self.operation = None
        self.operation_object_name = None
        self.rollback_on_cancel = False
        self.show_model()

    def _refresh_relations(self):
        self.relations.clear()
        sketch = backend.object_by_name(self.operation_object_name)
        if sketch is None:
            self.definition.setText("Estado: sin croquis")
            return
        count = len(getattr(sketch, "Constraints", []))
        geometry = int(getattr(sketch, "GeometryCount", 0))
        for index, constraint in enumerate(getattr(sketch, "Constraints", []), 1):
            self.relations.addItem(f"{index}. {constraint.Type}")
        self.definition.setText(
            f"Geometría: {geometry} · Relaciones: {count} · Estado: subdefinido"
        )

    def refresh_operation(self):
        if self.operation == "sketch":
            self._refresh_relations()

    def _rename_selected(self):
        if self.selected_name:
            backend.set_object_label(self.selected_name, self.object_label.text().strip())
            self.rebuild_tree()

    def _visibility_changed(self, checked: bool):
        if self.selected_name:
            backend.set_object_visibility(self.selected_name, checked)
            self.rebuild_tree()
