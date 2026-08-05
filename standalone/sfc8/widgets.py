"""Ribbon widgets owned by the SolidFreeCAD alpha.9 standalone application."""
from __future__ import annotations

from PySide import QtCore, QtWidgets


class CommandButton(QtWidgets.QToolButton):
    def __init__(self, text, callback, large=False, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextUnderIcon
            if large
            else QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.setMinimumHeight(58 if large else 30)
        self.setAutoRaise(True)
        self.clicked.connect(callback)


class Ribbon(QtWidgets.QTabWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setObjectName("SFC9Ribbon")
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
            frame.setObjectName("SFC9RibbonGroup")
            layout = QtWidgets.QVBoxLayout(frame)
            layout.setContentsMargins(5, 3, 5, 2)
            buttons = QtWidgets.QHBoxLayout()
            buttons.setSpacing(2)
            for label, callback, large in commands:
                buttons.addWidget(CommandButton(label, callback, large, frame))
            layout.addLayout(buttons, 1)
            caption = QtWidgets.QLabel(title)
            caption.setObjectName("SFC9GroupCaption")
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
                ("Saliente/Base", self.owner.begin_pad, True),
                ("Ajustar vista", self.owner.fit_view, False),
            )),
        ))

    def _sketch(self):
        return self._page((
            ("Entidades", (
                ("Rectángulo", self.owner.add_rectangle, True),
                ("Círculo", self.owner.add_circle, True),
            )),
            ("Croquis", (
                ("Editar parámetros", self.owner.show_sketch_properties, True),
                ("Aceptar croquis", self.owner.finish_sketch, True),
                ("Cancelar", self.owner.cancel_manager_operation, False),
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
