"""Qt widgets owned by the SolidFreeCAD alpha.8 application."""
from __future__ import annotations

import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from . import backend


class CommandButton(QtWidgets.QToolButton):
    def __init__(self, text, callback, large=False, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextUnderIcon
            if large
            else QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.setMinimumHeight(54 if large else 30)
        self.setAutoRaise(True)
        self.clicked.connect(callback)


class Ribbon(QtWidgets.QTabWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setObjectName("SFC8Ribbon")
        self.setDocumentMode(True)
        self.addTab(self._operations(), "Operaciones")
        self.addTab(self._sketch(), "Croquis")
        self.addTab(self._evaluate(), "Evaluar")
        self.addTab(self._assembly(), "Ensamblaje")

    def _page(self, groups):
        page = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(page)
        row.setContentsMargins(5, 4, 5, 4)
        row.setSpacing(4)
        for title, commands in groups:
            frame = QtWidgets.QFrame()
            frame.setObjectName("SFC8RibbonGroup")
            layout = QtWidgets.QVBoxLayout(frame)
            layout.setContentsMargins(5, 3, 5, 2)
            buttons = QtWidgets.QHBoxLayout()
            for label, callback, large in commands:
                buttons.addWidget(CommandButton(label, callback, large, frame))
            layout.addLayout(buttons, 1)
            caption = QtWidgets.QLabel(title)
            caption.setObjectName("SFC8GroupCaption")
            caption.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(caption)
            row.addWidget(frame)
        row.addStretch(1)
        return page

    def _operations(self):
        return self._page((
            ("Pieza", (
                ("Nueva pieza", self.owner.new_part, True),
                ("Abrir", self.owner.open_document, False),
                ("Guardar", self.owner.save_document, False),
            )),
            ("Operaciones", (
                ("Nuevo croquis", self.owner.new_sketch, True),
                ("Saliente/Base", self.owner.pad_selected_sketch, True),
                ("Ajustar vista", self.owner.fit_view, False),
            )),
        ))

    def _sketch(self):
        return self._page((
            ("Crear", (
                ("Nuevo croquis", self.owner.new_sketch, True),
                ("Rectángulo", self.owner.add_rectangle, True),
                ("Círculo", self.owner.add_circle, False),
            )),
            ("Estado", (
                ("Editar medidas", self.owner.show_sketch_properties, True),
                ("Cerrar croquis", self.owner.finish_sketch, True),
            )),
        ))

    def _evaluate(self):
        return self._page((
            ("Vista", (
                ("Isométrica", self.owner.axonometric_view, True),
                ("Frontal", self.owner.front_view, False),
                ("Superior", self.owner.top_view, False),
                ("Ajustar", self.owner.fit_view, False),
            )),
        ))

    def _assembly(self):
        return self._page((
            ("Ensamblaje", (
                ("Nuevo ensamblaje", self.owner.not_implemented, True),
                ("Insertar componente", self.owner.not_implemented, True),
            )),
        ))


class FeatureTree(QtWidgets.QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("SFC8FeatureTree")
        self.setHeaderHidden(True)
        self.setIndentation(15)
        self.itemSelectionChanged.connect(self._select_document_object)

    def rebuild(self):
        self.clear()
        doc = backend.active_document()
        if doc is None:
            root = QtWidgets.QTreeWidgetItem(["Sin documento"])
            root.addChild(QtWidgets.QTreeWidgetItem(["Use Nueva pieza"]))
            self.addTopLevelItem(root)
            root.setExpanded(True)
            return
        root = QtWidgets.QTreeWidgetItem([doc.Label or doc.Name])
        self.addTopLevelItem(root)
        for label in ("Historial", "Sensores", "Anotaciones", "Material <sin especificar>"):
            root.addChild(QtWidgets.QTreeWidgetItem([label]))
        origin = QtWidgets.QTreeWidgetItem(["Origen"])
        for plane in ("Alzado", "Planta", "Vista lateral"):
            origin.addChild(QtWidgets.QTreeWidgetItem([plane]))
        root.addChild(origin)
        for obj in doc.Objects:
            item = QtWidgets.QTreeWidgetItem([obj.Label or obj.Name])
            item.setData(0, QtCore.Qt.UserRole, obj.Name)
            root.addChild(item)
        root.setExpanded(True)

    def _select_document_object(self):
        items = self.selectedItems()
        doc = backend.active_document()
        if not items or doc is None:
            return
        name = items[0].data(0, QtCore.Qt.UserRole)
        obj = doc.getObject(name) if name else None
        if obj is not None:
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(obj)


class PropertyPanel(QtWidgets.QDockWidget):
    def __init__(self, owner):
        super().__init__("Propiedades", owner)
        self.setObjectName("SFC8PropertyPanel")
        self.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.setMinimumWidth(285)
        self.setMaximumWidth(380)

        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        self.title = QtWidgets.QLabel("Preparar modelo")
        self.title.setObjectName("SFC8PropertyTitle")
        layout.addWidget(self.title)
        self.message = QtWidgets.QLabel(
            "La interfaz alpha.8 controla las operaciones sin cambiar de workbench."
        )
        self.message.setObjectName("SFC8Message")
        self.message.setWordWrap(True)
        layout.addWidget(self.message)

        form = QtWidgets.QFormLayout()
        self.width = self._spin(100.0)
        self.height = self._spin(60.0)
        self.radius = self._spin(25.0)
        self.pad_length = self._spin(20.0)
        form.addRow("Ancho", self.width)
        form.addRow("Alto", self.height)
        form.addRow("Radio", self.radius)
        form.addRow("Longitud", self.pad_length)
        layout.addLayout(form)

        self.primary = QtWidgets.QPushButton("Crear rectángulo")
        self.primary.clicked.connect(owner.add_rectangle)
        layout.addWidget(self.primary)
        self.secondary = QtWidgets.QPushButton("Crear saliente")
        self.secondary.clicked.connect(owner.pad_selected_sketch)
        layout.addWidget(self.secondary)
        layout.addStretch(1)
        self.setWidget(page)

    def _spin(self, value):
        control = QtWidgets.QDoubleSpinBox()
        control.setRange(0.1, 100000.0)
        control.setValue(value)
        control.setSuffix(" mm")
        return control

    def mode(self, title, message, primary_text=None):
        self.title.setText(title)
        self.message.setText(message)
        if primary_text:
            self.primary.setText(primary_text)
