"""FeatureManager and contextual PropertyManager in one persistent left dock."""
from .qt import QtCore, QtWidgets
from .icons import icon
from . import backend


class CollapsibleSection(QtWidgets.QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.header = QtWidgets.QToolButton()
        self.header.setObjectName("SectionHeader")
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setChecked(True)
        self.header.setArrowType(QtCore.Qt.DownArrow)
        self.header.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.header.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        root.addWidget(self.header)
        self.body = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout(self.body)
        self.layout.setContentsMargins(9, 8, 9, 10)
        self.layout.setSpacing(6)
        root.addWidget(self.body)
        self.header.toggled.connect(self._toggle)

    def _toggle(self, expanded):
        self.body.setVisible(expanded)
        self.header.setArrowType(QtCore.Qt.DownArrow if expanded else QtCore.Qt.RightArrow)


class FeatureTree(QtWidgets.QTreeWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setObjectName("FeatureTree")
        self.setHeaderHidden(True)
        self.setIndentation(17)
        self.setUniformRowHeights(True)
        self.items_by_name = {}
        self.itemSelectionChanged.connect(self._selected)
        self.itemDoubleClicked.connect(self._double_clicked)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

    def _item(self, obj, parent):
        item = QtWidgets.QTreeWidgetItem([obj.Label or obj.Name])
        item.setData(0, QtCore.Qt.UserRole, obj.Name)
        kind = next((k for k, spec in backend.FEATURES.items() if spec[0] == obj.TypeId), "body")
        if obj.TypeId == "Sketcher::SketchObject":
            kind = "sketch"
        item.setIcon(0, icon(kind))
        item.setToolTip(0, f"{obj.Label}\n{obj.TypeId}")
        if hasattr(obj, "Visibility") and not obj.Visibility:
            item.setForeground(0, self.palette().placeholderText())
        parent.addChild(item)
        self.items_by_name[obj.Name] = item
        return item

    def rebuild(self):
        expanded = {name for name, item in self.items_by_name.items() if item.isExpanded()}
        self.blockSignals(True)
        try:
            self.clear()
            self.items_by_name = {}
            doc = backend.active_document()
            if doc is None:
                self.addTopLevelItem(QtWidgets.QTreeWidgetItem(["Nueva pieza para comenzar"]))
                return
            root = QtWidgets.QTreeWidgetItem([doc.Label or doc.Name])
            root.setIcon(0, icon("new"))
            self.addTopLevelItem(root)
            root.setExpanded(True)
            shown = set()
            for body in [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]:
                body_item = self._item(body, root)
                body_item.setExpanded(True)
                shown.add(body.Name)
                origin = QtWidgets.QTreeWidgetItem(["Origen"])
                body_item.addChild(origin)
                for label, plane in [("Planta (XY)", "XY"), ("Alzado (XZ)", "XZ"), ("Lateral (YZ)", "YZ")]:
                    item = QtWidgets.QTreeWidgetItem([label])
                    item.setData(0, QtCore.Qt.UserRole, "__plane_" + plane)
                    item.setIcon(0, icon("plane"))
                    origin.addChild(item)
                # Consume sketches under their profile feature instead of duplicating them.
                consumed = {}
                for obj in body.Group:
                    profile = getattr(obj, "Profile", None)
                    if isinstance(profile, tuple):
                        profile = profile[0]
                    if profile is not None:
                        consumed.setdefault(profile.Name, obj.Name)
                for obj in body.Group:
                    if obj.Name in consumed:
                        continue
                    feature_item = self._item(obj, body_item)
                    shown.add(obj.Name)
                    for profile_name, feature_name in consumed.items():
                        if feature_name == obj.Name:
                            profile = doc.getObject(profile_name)
                            if profile is not None and profile.Name not in shown:
                                self._item(profile, feature_item)
                                shown.add(profile.Name)
            for obj in doc.Objects:
                if obj.Name in shown or backend.body_of(obj) is not None:
                    continue
                if hasattr(obj, "Shape") and not obj.TypeId.startswith(("App::", "PartDesign::")):
                    self._item(obj, root)
            for name in expanded:
                if name in self.items_by_name:
                    self.items_by_name[name].setExpanded(True)
            self.sync_selection()
        finally:
            self.blockSignals(False)

    def sync_selection(self):
        obj = backend.selected_object()
        if obj is None:
            return
        item = self.items_by_name.get(obj.Name)
        if item is not None:
            previous = self.blockSignals(True)
            self.setCurrentItem(item)
            self.blockSignals(previous)

    def filter_items(self, text):
        text = text.casefold().strip()
        def visit(item):
            children = [visit(item.child(i)) for i in range(item.childCount())]
            matches = text in item.text(0).casefold() or any(children)
            item.setHidden(not matches)
            if text and any(children):
                item.setExpanded(True)
            return matches
        for i in range(self.topLevelItemCount()):
            visit(self.topLevelItem(i))

    def _selected(self):
        item = self.currentItem()
        name = item.data(0, QtCore.Qt.UserRole) if item else None
        if name and not name.startswith("__"):
            self.owner.on_tree_selection(name)

    def _double_clicked(self, item, column):
        name = item.data(0, QtCore.Qt.UserRole)
        if name and name.startswith("__plane_"):
            self.owner.new_sketch(plane=name[8:])
        elif name:
            self.owner.edit_object(name)

    def _context_menu(self, point):
        item = self.itemAt(point)
        if item is None:
            return
        self.setCurrentItem(item)
        name = item.data(0, QtCore.Qt.UserRole)
        if not name or name.startswith("__"):
            return
        menu = QtWidgets.QMenu(self)
        for key in ("edit", "visibility", "rename", "delete"):
            menu.addAction(self.owner.actions[key])
        menu.exec_(self.viewport().mapToGlobal(point))


class ManagerDock(QtWidgets.QDockWidget):
    def __init__(self, owner):
        super().__init__("Diseño", owner)
        self.owner = owner
        self.operation = None
        self.operation_object_name = None
        self._loading = False
        self.setObjectName("ManagerDock")
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.setTitleBarWidget(QtWidgets.QWidget())
        self.setMinimumWidth(248)
        self.setMaximumWidth(380)
        shell = QtWidgets.QWidget()
        root = QtWidgets.QVBoxLayout(shell)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.modes = QtWidgets.QTabBar()
        self.modes.addTab(icon("body"), "Modelo")
        self.modes.addTab(icon("edit"), "Propiedades")
        self.modes.setExpanding(True)
        root.addWidget(self.modes)
        self.stack = QtWidgets.QStackedWidget()
        self.stack.addWidget(self._model_page())
        self.stack.addWidget(self._property_page())
        root.addWidget(self.stack)
        self.setWidget(shell)
        self.modes.currentChanged.connect(self._change_mode)
        self.show_model()

    def _change_mode(self, index):
        self.stack.setCurrentIndex(index)
        if index == 1 and self.operation is None:
            self.show_object(backend.selected_object())

    def _model_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(5, 6, 5, 0)
        self.filter = QtWidgets.QLineEdit()
        self.filter.setPlaceholderText("Filtrar árbol de operaciones")
        self.filter.setClearButtonEnabled(True)
        layout.addWidget(self.filter)
        self.tree = FeatureTree(self.owner)
        self.filter.textChanged.connect(self.tree.filter_items)
        layout.addWidget(self.tree)
        return page

    def _property_page(self):
        page = QtWidgets.QWidget()
        outer = QtWidgets.QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        header = QtWidgets.QWidget()
        header.setObjectName("PropertyHeader")
        row = QtWidgets.QHBoxLayout(header)
        row.setContentsMargins(6, 6, 6, 6)
        self.accept = QtWidgets.QToolButton()
        self.accept.setIcon(icon("check"))
        self.accept.setToolTip("Aceptar operación")
        self.accept.clicked.connect(lambda: self.owner._run(self.owner.accept_manager_operation))
        row.addWidget(self.accept)
        self.cancel = QtWidgets.QToolButton()
        self.cancel.setIcon(icon("cancel"))
        self.cancel.setToolTip("Cancelar operación · Esc")
        self.cancel.clicked.connect(self.owner.cancel_manager_operation)
        row.addWidget(self.cancel)
        self.property_title = QtWidgets.QLabel("Propiedades")
        row.addWidget(self.property_title, 1)
        outer.addWidget(header)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        body = QtWidgets.QWidget()
        self.content = QtWidgets.QVBoxLayout(body)
        self.content.setContentsMargins(4, 6, 4, 8)
        self.content.setSpacing(4)
        self.message = QtWidgets.QLabel("Seleccione un elemento del modelo.")
        self.message.setObjectName("PropertyMessage")
        self.message.setWordWrap(True)
        self.content.addWidget(self.message)
        self.selection = CollapsibleSection("Selección")
        self.selection_box = QtWidgets.QLabel()
        self.selection_box.setWordWrap(True)
        self.selection.layout.addWidget(self.selection_box)
        self.content.addWidget(self.selection)

        self.feature_section = CollapsibleSection("Definición de la operación")
        form = QtWidgets.QFormLayout()
        self.value = self._spin(20)
        self.value_label = QtWidgets.QLabel("Profundidad")
        form.addRow(self.value_label, self.value)
        self.reverse = QtWidgets.QCheckBox("Invertir dirección")
        self.symmetric = QtWidgets.QCheckBox("Simétrico al plano")
        self.through = QtWidgets.QCheckBox("Por todo")
        self.preview = QtWidgets.QCheckBox("Vista preliminar")
        self.preview.setChecked(True)
        self.axis = QtWidgets.QComboBox()
        self.axis.addItem("Eje vertical del croquis", "V_Axis")
        self.axis.addItem("Eje horizontal del croquis", "H_Axis")
        form.addRow(self.axis)
        for control in (self.reverse, self.symmetric, self.through, self.preview):
            form.addRow(control)
            control.toggled.connect(self._parameters_changed)
        self.value.valueChanged.connect(self._parameters_changed)
        self.axis.currentIndexChanged.connect(self._parameters_changed)
        self.feature_section.layout.addLayout(form)
        self.content.addWidget(self.feature_section)

        self.sketch_section = CollapsibleSection("Entidades por medidas")
        form = QtWidgets.QFormLayout()
        self.width, self.height, self.radius = self._spin(100), self._spin(60), self._spin(10)
        for label, control in (("Ancho", self.width), ("Alto", self.height), ("Radio", self.radius)):
            form.addRow(label, control)
        self.sketch_section.layout.addLayout(form)
        row = QtWidgets.QHBoxLayout()
        for text, callback in (("Rectángulo", self.owner.add_rectangle), ("Círculo", self.owner.add_circle)):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(callback)
            row.addWidget(button)
        self.sketch_section.layout.addLayout(row)
        self.content.addWidget(self.sketch_section)
        self.dimension_section = CollapsibleSection("Cotas y relaciones")
        self.geometry = QtWidgets.QComboBox()
        self.dimension_section.layout.addWidget(self.geometry)
        self.constraint = QtWidgets.QComboBox()
        for label, kind in [("Longitud", "Distance"), ("Radio", "Radius"), ("Horizontal", "Horizontal"), ("Vertical", "Vertical")]:
            self.constraint.addItem(label, kind)
        self.dimension_section.layout.addWidget(self.constraint)
        self.dimension_value = self._spin(25)
        self.dimension_section.layout.addWidget(self.dimension_value)
        apply = QtWidgets.QPushButton("Aplicar cota / relación")
        apply.clicked.connect(self.owner.apply_dimension)
        self.dimension_section.layout.addWidget(apply)
        self.definition = QtWidgets.QLabel()
        self.definition.setWordWrap(True)
        self.dimension_section.layout.addWidget(self.definition)
        self.content.addWidget(self.dimension_section)
        self.object_section = CollapsibleSection("Elemento")
        self.object_details = QtWidgets.QLabel()
        self.object_details.setWordWrap(True)
        self.object_section.layout.addWidget(self.object_details)
        self.content.addWidget(self.object_section)
        self.content.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll)
        return page

    def _spin(self, value):
        control = QtWidgets.QDoubleSpinBox()
        control.setRange(0.001, 1000000)
        control.setDecimals(3)
        control.setSuffix(" mm")
        control.setValue(value)
        return control

    def _sections(self, feature=False, sketch=False, obj=False):
        self.feature_section.setVisible(feature)
        self.sketch_section.setVisible(sketch)
        self.dimension_section.setVisible(sketch)
        self.object_section.setVisible(obj)
        self.accept.setVisible(feature or sketch)
        self.cancel.setVisible(feature or sketch)
        self.modes.setCurrentIndex(1)
        self.stack.setCurrentIndex(1)

    def show_model(self):
        self.operation = None
        self.operation_object_name = None
        self.modes.setCurrentIndex(0)
        self.stack.setCurrentIndex(0)
        self.rebuild_tree()

    def begin_sketch(self, sketch):
        self.operation = "sketch"
        self.operation_object_name = sketch.Name
        self.property_title.setText("Croquis")
        self.selection_box.setText(sketch.Label)
        self.message.setText("Dibuje con el ratón o introduzca medidas. Confirme para conservar el croquis.")
        self._sections(sketch=True)
        self.accept.setEnabled(True)
        self.refresh_sketch()

    def begin_feature(self, session):
        self._loading = True
        try:
            kind, obj = session.kind, session.feature
            self.operation, self.operation_object_name = kind, obj.Name
            self.property_title.setText(backend.FEATURES[kind][2])
            self.selection_box.setText(obj.Label)
            labels = {"revolution": ("Ángulo", "Angle", 360), "fillet": ("Radio", "Radius", 2), "chamfer": ("Distancia", "Size", 2)}
            label, prop, default = labels.get(kind, ("Profundidad", "Length", 20))
            self.value_label.setText(label)
            self.value.setSuffix(" °" if kind == "revolution" else " mm")
            self.value.setMaximum(360 if kind == "revolution" else 1000000)
            self.value.setValue(float(getattr(obj, prop, default)))
            self.reverse.setChecked(bool(getattr(obj, "Reversed", False)))
            symmetric = str(getattr(obj, "SideType", "")) == "Symmetric" or bool(getattr(obj, "Midplane", False))
            self.symmetric.setChecked(symmetric)
            self.through.setChecked(str(getattr(obj, "Type", "")) == "ThroughAll")
            axis = getattr(obj, "ReferenceAxis", None)
            self.axis.setCurrentIndex(1 if axis and axis[1] and axis[1][0] == "H_Axis" else 0)
            for control in (self.reverse, self.symmetric):
                control.setVisible(kind in ("pad", "pocket", "revolution"))
            self.through.setVisible(kind == "pocket")
            self.axis.setVisible(kind == "revolution")
            self.preview.setChecked(True)
            self._sections(feature=True)
        finally:
            self._loading = False

    def feature_values(self):
        return dict(value=self.value.value(), reverse=self.reverse.isChecked(), symmetric=self.symmetric.isChecked(), through=self.through.isChecked(), axis=self.axis.currentData(), preview=self.preview.isChecked())

    def _parameters_changed(self, *args):
        self.value.setEnabled(not (self.operation == "pocket" and self.through.isChecked()))
        if not self._loading and self.operation in backend.FEATURES:
            self.owner.schedule_preview()

    def refresh_sketch(self):
        if self.operation != "sketch":
            return
        sketch = backend.object_by_name(self.operation_object_name)
        if sketch is None:
            return
        previous = self.geometry.currentData()
        self.geometry.clear()
        for i, geometry in enumerate(sketch.Geometry):
            label = "Círculo" if hasattr(geometry, "Radius") else "Línea"
            self.geometry.addItem(f"{i + 1} · {label}", i)
        index = self.geometry.findData(previous)
        self.geometry.setCurrentIndex(index if index >= 0 else max(0, self.geometry.count() - 1))
        state = "Definido" if getattr(sketch, "FullyConstrained", False) else "Subdefinido"
        self.definition.setText(f"{state} · {sketch.GeometryCount} entidades\n{sketch.ConstraintCount} restricciones")

    def show_object(self, obj):
        if self.operation is not None:
            return
        self.property_title.setText("Propiedades del elemento")
        self.selection_box.setText(obj.Label if obj is not None else "Sin selección")
        self.object_details.setText(f"Nombre: {obj.Label}\nTipo: {obj.TypeId}\n\nDoble clic para editar la operación." if obj is not None else "Seleccione un elemento del árbol o del visor.")
        self.message.setText("Los parámetros se editan en su operación de origen.")
        self._sections(obj=True)

    def rebuild_tree(self):
        self.tree.rebuild()
        self.tree.filter_items(self.filter.text())
