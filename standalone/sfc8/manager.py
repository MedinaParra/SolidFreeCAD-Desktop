"""SolidFreeCAD alpha.10 single left manager.

Implements a professional parametric-CAD interaction pattern:
- one persistent left panel,
- model tree when idle,
- contextual PropertyManager during commands,
- configurations in the same physical location,
- accept/cancel lifecycle without FreeCAD TaskView.
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
        self.header.setObjectName("SFC10SectionHeader")
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setChecked(True)
        self.header.setArrowType(QtCore.Qt.DownArrow)
        self.header.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.header.toggled.connect(self._toggle)
        root.addWidget(self.header)

        self.body = QtWidgets.QWidget()
        self.body.setObjectName("SFC10SectionBody")
        self.layout = QtWidgets.QVBoxLayout(self.body)
        self.layout.setContentsMargins(8, 6, 8, 8)
        self.layout.setSpacing(5)
        root.addWidget(self.body)

    def _toggle(self, checked: bool):
        self.body.setVisible(checked)
        self.header.setArrowType(
            QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow
        )


class FeatureTree(QtWidgets.QTreeWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setObjectName("SFC10FeatureTree")
        self.setHeaderHidden(True)
        self.setIndentation(13)
        self.setUniformRowHeights(True)
        self.setAnimated(False)
        self.itemSelectionChanged.connect(self._selection_changed)
        self.itemDoubleClicked.connect(self._double_clicked)

    def rebuild(self):
        selected_name = None
        items = self.selectedItems()
        if items:
            selected_name = items[0].data(0, QtCore.Qt.UserRole)

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
        root.setExpanded(True)
        self.addTopLevelItem(root)

        for label in (
            "Historial",
            "Sensores",
            "Anotaciones",
            "Material <sin especificar>",
        ):
            root.addChild(QtWidgets.QTreeWidgetItem([label]))

        origin = QtWidgets.QTreeWidgetItem(["Origen"])
        for plane in ("Alzado", "Planta", "Vista lateral"):
            origin.addChild(QtWidgets.QTreeWidgetItem([plane]))
        root.addChild(origin)

        current_item = None
        for obj in doc.Objects:
            if obj.TypeId == "PartDesign::Body":
                continue
            label = obj.Label or obj.Name
            visible = bool(
                getattr(getattr(obj, "ViewObject", None), "Visibility", True)
            )
            item = QtWidgets.QTreeWidgetItem(
                [label if visible else f"{label} (oculto)"]
            )
            item.setData(0, QtCore.Qt.UserRole, obj.Name)
            root.addChild(item)
            if obj.Name == selected_name:
                current_item = item

        if current_item is not None:
            self.setCurrentItem(current_item)

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
    """Single fixed left manager with model/property/configuration modes."""

    MODEL = 0
    PROPERTY = 1
    CONFIG = 2

    def __init__(self, owner):
        super().__init__("", owner)
        self.owner = owner
        self.setObjectName("SFC10ManagerDock")
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.setTitleBarWidget(QtWidgets.QWidget())
        self.setMinimumWidth(205)
        self.setMaximumWidth(285)

        self.operation = None
        self.operation_object_name = None
        self.rollback_on_cancel = False
        self.selected_name = None

        shell = QtWidgets.QWidget()
        shell.setObjectName("SFC10ManagerShell")
        root = QtWidgets.QVBoxLayout(shell)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._mode_strip())

        self.stack = QtWidgets.QStackedWidget()
        self.stack.setObjectName("SFC10ManagerStack")
        self.stack.addWidget(self._model_page())
        self.stack.addWidget(self._property_page())
        self.stack.addWidget(self._configuration_page())
        root.addWidget(self.stack, 1)
        self.setWidget(shell)
        self.show_model()

    def _mode_strip(self):
        strip = QtWidgets.QWidget()
        strip.setObjectName("SFC10ManagerModeStrip")
        row = QtWidgets.QHBoxLayout(strip)
        row.setContentsMargins(3, 2, 3, 2)
        row.setSpacing(1)

        self.mode_buttons = []
        for index, (glyph, tip) in enumerate(
            (
                ("◆", "Árbol de diseño"),
                ("▤", "PropertyManager"),
                ("⚙", "Configuraciones"),
                ("◎", "Administrador de visualización"),
            )
        ):
            button = QtWidgets.QToolButton()
            button.setObjectName("SFC10ManagerModeButton")
            button.setText(glyph)
            button.setToolTip(tip)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setFixedSize(34, 27)
            button.clicked.connect(
                lambda _checked=False, i=index: self.set_mode_index(i)
            )
            self.mode_buttons.append(button)
            row.addWidget(button)
        row.addStretch(1)
        self.mode_buttons[0].setChecked(True)
        return strip

    def set_mode_index(self, index: int):
        if index == 0:
            self.show_model()
        elif index == 1:
            self.stack.setCurrentIndex(self.PROPERTY)
            self.mode_buttons[1].setChecked(True)
        else:
            self.stack.setCurrentIndex(self.CONFIG)
            self.mode_buttons[2].setChecked(True)

    def _model_page(self):
        page = QtWidgets.QWidget()
        page.setObjectName("SFC10ModelPage")
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        self.filter = QtWidgets.QLineEdit()
        self.filter.setObjectName("SFC10TreeFilter")
        self.filter.setPlaceholderText("Filtrar árbol")
        self.filter.setClearButtonEnabled(True)
        layout.addWidget(self.filter)

        self.tree = FeatureTree(self.owner)
        layout.addWidget(self.tree, 1)

        footer = QtWidgets.QLabel("Modelo")
        footer.setObjectName("SFC10ModelFooter")
        footer.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(footer)
        return page

    def _property_page(self):
        page = QtWidgets.QWidget()
        page.setObjectName("SFC10PropertyPage")
        outer = QtWidgets.QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QtWidgets.QWidget()
        header.setObjectName("SFC10PropertyHeader")
        row = QtWidgets.QHBoxLayout(header)
        row.setContentsMargins(5, 4, 5, 4)
        row.setSpacing(4)

        self.accept = QtWidgets.QToolButton()
        self.accept.setObjectName("SFC10Accept")
        self.accept.setText("✓")
        self.accept.setToolTip("Aceptar")
        self.accept.clicked.connect(self.owner.accept_manager_operation)
        row.addWidget(self.accept)

        self.cancel = QtWidgets.QToolButton()
        self.cancel.setObjectName("SFC10Cancel")
        self.cancel.setText("✕")
        self.cancel.setToolTip("Cancelar")
        self.cancel.clicked.connect(self.owner.cancel_manager_operation)
        row.addWidget(self.cancel)

        self.property_title = QtWidgets.QLabel("PropertyManager")
        self.property_title.setObjectName("SFC10PropertyTitle")
        row.addWidget(self.property_title, 1)

        help_button = QtWidgets.QToolButton()
        help_button.setText("?")
        help_button.setToolTip("Ayuda contextual")
        row.addWidget(help_button)
        outer.addWidget(header)

        scroll = QtWidgets.QScrollArea()
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setWidgetResizable(True)

        body = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(body)
        layout.setContentsMargins(4, 4, 4, 8)
        layout.setSpacing(3)

        self.message = QtWidgets.QLabel("Seleccione una operación.")
        self.message.setObjectName("SFC10PropertyMessage")
        self.message.setWordWrap(True)
        layout.addWidget(self.message)

        self.selection_section = CollapsibleSection("Selecciones")
        self.selection_box = QtWidgets.QLabel("Sin selección")
        self.selection_box.setObjectName("SFC10SelectionBox")
        self.selection_box.setWordWrap(True)
        self.selection_section.layout.addWidget(self.selection_box)
        layout.addWidget(self.selection_section)

        self.sketch_section = CollapsibleSection("Parámetros")
        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        self.width = self._spin(100.0)
        self.height = self._spin(60.0)
        self.radius = self._spin(25.0)
        form.addRow("Ancho", self.width)
        form.addRow("Alto", self.height)
        form.addRow("Radio", self.radius)
        self.sketch_section.layout.addLayout(form)
        tools = QtWidgets.QHBoxLayout()
        rectangle = QtWidgets.QPushButton("Rectángulo")
        rectangle.clicked.connect(self.owner.add_rectangle)
        tools.addWidget(rectangle)
        circle = QtWidgets.QPushButton("Círculo")
        circle.clicked.connect(self.owner.add_circle)
        tools.addWidget(circle)
        self.sketch_section.layout.addLayout(tools)
        layout.addWidget(self.sketch_section)

        self.relations_section = CollapsibleSection("Relaciones existentes")
        self.relations = QtWidgets.QListWidget()
        self.relations.setMaximumHeight(100)
        self.relations_section.layout.addWidget(self.relations)
        self.definition = QtWidgets.QLabel("Estado: subdefinido")
        self.definition.setObjectName("SFC10Definition")
        self.relations_section.layout.addWidget(self.definition)
        layout.addWidget(self.relations_section)

        self.pad_section = CollapsibleSection("Dirección 1")
        pad_form = QtWidgets.QFormLayout()
        pad_form.setContentsMargins(0, 0, 0, 0)
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
        object_form.setContentsMargins(0, 0, 0, 0)
        self.object_name = QtWidgets.QLineEdit()
        self.object_name.editingFinished.connect(self._rename_selected)
        self.object_visible = QtWidgets.QCheckBox("Visible")
        self.object_visible.toggled.connect(self._set_visibility)
        self.object_type = QtWidgets.QLabel("—")
        object_form.addRow("Nombre", self.object_name)
        object_form.addRow("Tipo", self.object_type)
        object_form.addRow("", self.object_visible)
        self.object_section.layout.addLayout(object_form)
        layout.addWidget(self.object_section)

        layout.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)
        return page

    def _configuration_page(self):
        page = QtWidgets.QWidget()
        page.setObjectName("SFC10ConfigurationPage")
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        tree = QtWidgets.QTreeWidget()
        tree.setHeaderLabels(["Configuración", "Estado"])
        tree.addTopLevelItem(
            QtWidgets.QTreeWidgetItem(["Predeterminado", "Activa"])
        )
        layout.addWidget(tree)
        return page

    def _spin(self, value: float):
        control = QtWidgets.QDoubleSpinBox()
        control.setRange(0.01, 1000000.0)
        control.setDecimals(2)
        control.setValue(value)
        control.setSuffix(" mm")
        return control

    def show_model(self):
        self.operation = None
        self.operation_object_name = None
        self.rollback_on_cancel = False
        self.stack.setCurrentIndex(self.MODEL)
        self.mode_buttons[0].setChecked(True)
        self.rebuild_tree()

    def begin_sketch(self, name: str, rollback_on_cancel: bool):
        self.operation = "sketch"
        self.operation_object_name = name
        self.rollback_on_cancel = rollback_on_cancel
        self.property_title.setText("Croquis")
        self.message.setText(
            "Edite el croquis sin abandonar la interfaz SolidFreeCAD."
        )
        self.selection_box.setText("Plano o croquis activo")
        self.sketch_section.show()
        self.relations_section.show()
        self.pad_section.hide()
        self.object_section.hide()
        self.stack.setCurrentIndex(self.PROPERTY)
        self.mode_buttons[1].setChecked(True)
        self.refresh_operation()

    def begin_pad(self, sketch_name: str):
        self.operation = "pad"
        self.operation_object_name = sketch_name
        self.rollback_on_cancel = False
        self.property_title.setText("Saliente/Base")
        self.message.setText(
            "Defina la profundidad y confirme para crear la operación."
        )
        self.selection_box.setText(sketch_name)
        self.sketch_section.hide()
        self.relations_section.hide()
        self.pad_section.show()
        self.object_section.hide()
        self.stack.setCurrentIndex(self.PROPERTY)
        self.mode_buttons[1].setChecked(True)

    def show_object(self, obj):
        if obj is None:
            return
        self.operation = "object"
        self.operation_object_name = obj.Name
        self.rollback_on_cancel = False
        self.selected_name = obj.Name
        self.property_title.setText(obj.Label or obj.Name)
        self.message.setText("Propiedades del elemento seleccionado.")
        self.selection_box.setText(f"{obj.Label} ({obj.TypeId})")
        self.sketch_section.hide()
        self.relations_section.hide()
        self.pad_section.hide()
        self.object_section.show()
        self.object_name.setText(obj.Label or obj.Name)
        self.object_type.setText(obj.TypeId)
        visible = bool(
            getattr(getattr(obj, "ViewObject", None), "Visibility", False)
        )
        self.object_visible.blockSignals(True)
        self.object_visible.setChecked(visible)
        self.object_visible.blockSignals(False)
        self.stack.setCurrentIndex(self.PROPERTY)
        self.mode_buttons[1].setChecked(True)

    def finish_operation(self):
        self.show_model()

    def rebuild_tree(self):
        self.tree.rebuild()

    def refresh_operation(self):
        if self.operation != "sketch":
            return
        obj = backend.object_by_name(self.operation_object_name)
        self.relations.clear()
        if obj is None:
            self.definition.setText("Estado: sin croquis")
            return
        geometry_count = int(getattr(obj, "GeometryCount", 0))
        constraints = list(getattr(obj, "Constraints", []))
        for constraint in constraints:
            self.relations.addItem(str(constraint))
        self.definition.setText(
            f"Geometría: {geometry_count} · Relaciones: {len(constraints)}"
        )

    def _rename_selected(self):
        if not self.selected_name:
            return
        obj = backend.object_by_name(self.selected_name)
        if obj is None:
            return
        value = self.object_name.text().strip()
        if value:
            obj.Label = value
            obj.Document.recompute()
            self.rebuild_tree()

    def _set_visibility(self, checked: bool):
        if not self.selected_name:
            return
        obj = backend.object_by_name(self.selected_name)
        if obj is not None and hasattr(obj, "ViewObject"):
            obj.ViewObject.Visibility = checked
            self.rebuild_tree()
