"""Standalone SolidFreeCAD alpha.10 application window.

The native FreeCAD chrome remains hidden. SolidFreeCAD owns the header,
command manager, left FeatureManager/PropertyManager, viewport placement and
status bar.
"""
from __future__ import annotations

import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from . import backend
from .manager import ManagerDock
from .widgets import Ribbon

_APP_NAME = "SolidFreeCAD Professional alpha.10"
_window = None


class HeaderBar(QtWidgets.QWidget):
    """Custom integrated header; replaces the default Qt/FreeCAD menu bar."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setObjectName("SFC10HeaderBar")
        self.setFixedHeight(31)

        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(5, 0, 5, 0)
        row.setSpacing(1)

        brand = QtWidgets.QLabel("SolidFreeCAD")
        brand.setObjectName("SFC10Brand")
        brand.setMinimumWidth(112)
        row.addWidget(brand)

        for text, callback in (
            ("Archivo", owner.show_file_menu),
            ("Edición", owner.not_implemented),
            ("Ver", owner.show_view_menu),
            ("Insertar", owner.not_implemented),
            ("Herramientas", owner.not_implemented),
            ("Simulación", owner.not_implemented),
            ("Ventana", owner.not_implemented),
        ):
            button = QtWidgets.QToolButton()
            button.setObjectName("SFC10HeaderMenu")
            button.setText(text)
            button.setAutoRaise(True)
            button.clicked.connect(callback)
            row.addWidget(button)

        row.addStretch(1)
        self.document_title = QtWidgets.QLabel("Sin documento")
        self.document_title.setObjectName("SFC10DocumentTitle")
        self.document_title.setAlignment(QtCore.Qt.AlignCenter)
        self.document_title.setMinimumWidth(220)
        row.addWidget(self.document_title, 1)
        row.addStretch(1)

        self.search = QtWidgets.QLineEdit()
        self.search.setObjectName("SFC10CommandSearch")
        self.search.setPlaceholderText("Buscar comandos")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(205)
        row.addWidget(self.search)

        help_button = QtWidgets.QToolButton()
        help_button.setObjectName("SFC10HeaderIcon")
        help_button.setText("?")
        help_button.clicked.connect(owner.show_about)
        row.addWidget(help_button)


class SolidFreeCADWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.host = Gui.getMainWindow()
        self._host_central = None
        self._signature = None
        self.setObjectName("SolidFreeCADStandaloneWindow")
        self.resize(1500, 900)
        self.setMinimumSize(1100, 700)

        self.menuBar().hide()
        self.setMenuWidget(HeaderBar(self))
        self.header = self.menuWidget()

        self._take_document_view()
        self._build_command_manager()
        self.manager = ManagerDock(self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.manager)
        self._build_view_toolbar()
        self._build_status()
        self._apply_style()
        backend.set_light_background()

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(400)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh(True)

    def _take_document_view(self):
        self._hide_host_chrome()
        self._host_central = self.host.takeCentralWidget()
        if self._host_central is None:
            self._host_central = QtWidgets.QLabel(
                "No se encontró la vista de documento de FreeCAD."
            )
            self._host_central.setAlignment(QtCore.Qt.AlignCenter)
        self._host_central.setObjectName("SFC10Viewport")
        self.setCentralWidget(self._host_central)

    def _hide_host_chrome(self):
        self.host.menuBar().hide()
        self.host.statusBar().hide()
        for toolbar in self.host.findChildren(QtWidgets.QToolBar):
            toolbar.hide()
        for dock in self.host.findChildren(QtWidgets.QDockWidget):
            dock.hide()

    def _build_command_manager(self):
        self.command_toolbar = QtWidgets.QToolBar("CommandManager", self)
        self.command_toolbar.setObjectName("SFC10CommandManagerBar")
        self.command_toolbar.setMovable(False)
        self.command_toolbar.setFloatable(False)
        self.command_toolbar.setAllowedAreas(QtCore.Qt.TopToolBarArea)
        self.command_toolbar.setFixedHeight(112)

        self.ribbon = Ribbon(self)
        self.ribbon.setObjectName("SFC10Ribbon")
        self.ribbon.setMinimumHeight(108)
        self.ribbon.setMaximumHeight(108)
        self.command_toolbar.addWidget(self.ribbon)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.command_toolbar)

    def _build_view_toolbar(self):
        self.view_toolbar = QtWidgets.QToolBar("Vista rápida", self)
        self.view_toolbar.setObjectName("SFC10ViewToolbar")
        self.view_toolbar.setOrientation(QtCore.Qt.Vertical)
        self.view_toolbar.setMovable(False)
        self.view_toolbar.setFloatable(False)
        for text, callback in (
            ("ISO", self.axonometric_view),
            ("F", self.front_view),
            ("S", self.top_view),
            ("A", self.fit_view),
        ):
            action = self.view_toolbar.addAction(text)
            action.triggered.connect(callback)
        self.addToolBar(QtCore.Qt.RightToolBarArea, self.view_toolbar)

    def _build_status(self):
        self.statusBar().setFixedHeight(22)
        self.state = QtWidgets.QLabel("Editando pieza")
        self.statusBar().addWidget(self.state, 1)
        self.units = QtWidgets.QLabel("MMGS")
        self.statusBar().addPermanentWidget(self.units)

    def _popup(self, entries, x=95):
        menu = QtWidgets.QMenu(self)
        for text, callback in entries:
            action = menu.addAction(text)
            action.triggered.connect(callback)
        position = self.header.mapToGlobal(QtCore.QPoint(x, self.header.height()))
        menu.exec_(position)

    def show_file_menu(self):
        self._popup(
            (
                ("Nueva pieza", self.new_part),
                ("Abrir...", self.open_document),
                ("Guardar", self.save_document),
            )
        )

    def show_view_menu(self):
        self._popup(
            (
                ("Isométrica", self.axonometric_view),
                ("Frontal", self.front_view),
                ("Superior", self.top_view),
                ("Ajustar", self.fit_view),
            ),
            x=190,
        )

    def show_about(self):
        QtWidgets.QMessageBox.information(
            self,
            "SolidFreeCAD alpha.10",
            "Interfaz propia de CAD paramétrico con FreeCAD como motor.",
        )

    def refresh(self, force=False):
        doc = backend.active_document()
        signature = None if doc is None else tuple(
            (
                o.Name,
                o.Label,
                o.TypeId,
                bool(getattr(getattr(o, "ViewObject", None), "Visibility", False)),
            )
            for o in doc.Objects
        )
        if force or signature != self._signature:
            self._signature = signature
            self.manager.rebuild_tree()
            self.manager.refresh_operation()

        label = "Sin documento" if doc is None else (doc.Label or doc.Name)
        self.setWindowTitle(f"{_APP_NAME} — {label}")
        self.header.document_title.setText(label)

    def new_part(self):
        if self.manager.operation is not None:
            self.cancel_manager_operation()
        backend.new_part()
        self.manager.show_model()
        self.state.setText("Editando pieza")
        self.refresh(True)

    def new_sketch(self):
        if self.manager.operation is not None:
            self.cancel_manager_operation()
        sketch = backend.new_sketch()
        self.manager.begin_sketch(sketch.Name, rollback_on_cancel=True)
        self.ribbon.setCurrentIndex(1)
        self.state.setText("Editando croquis")
        self.refresh(True)

    def add_rectangle(self):
        if self.manager.operation != "sketch":
            self.new_sketch()
        backend.add_rectangle(self.manager.width.value(), self.manager.height.value())
        self.manager.refresh_operation()
        self.state.setText("Rectángulo agregado")
        self.refresh(True)

    def add_circle(self):
        if self.manager.operation != "sketch":
            self.new_sketch()
        backend.add_circle(self.manager.radius.value())
        self.manager.refresh_operation()
        self.state.setText("Círculo agregado")
        self.refresh(True)

    def begin_pad(self):
        sketch = backend.active_sketch()
        if sketch is None:
            QtWidgets.QMessageBox.warning(
                self,
                "Saliente/Base",
                "Cree o seleccione un croquis cerrado.",
            )
            return
        self.manager.begin_pad(sketch.Name)
        self.ribbon.setCurrentIndex(0)
        self.state.setText("Definiendo Saliente/Base")

    def accept_manager_operation(self):
        operation = self.manager.operation
        if operation == "sketch":
            self.manager.finish_operation()
            self.ribbon.setCurrentIndex(0)
            self.state.setText("Croquis aceptado")
        elif operation == "pad":
            try:
                backend.pad_sketch(self.manager.pad_length.value())
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self, "Saliente/Base", str(exc))
                return
            self.manager.finish_operation()
            self.ribbon.setCurrentIndex(0)
            self.state.setText("Saliente/Base creado")
        else:
            self.manager.show_model()
        self.refresh(True)

    def cancel_manager_operation(self):
        operation = self.manager.operation
        name = self.manager.operation_object_name
        rollback = self.manager.rollback_on_cancel
        if operation == "sketch" and rollback and name:
            backend.remove_object(name)
        self.manager.finish_operation()
        self.ribbon.setCurrentIndex(0)
        self.state.setText("Operación cancelada")
        self.refresh(True)

    def finish_sketch(self):
        if self.manager.operation == "sketch":
            self.accept_manager_operation()

    def show_sketch_properties(self):
        sketch = backend.active_sketch()
        if sketch is None:
            QtWidgets.QMessageBox.information(
                self,
                "Croquis",
                "Cree o seleccione un croquis.",
            )
            return
        self.manager.begin_sketch(sketch.Name, rollback_on_cancel=False)
        self.ribbon.setCurrentIndex(1)

    def on_tree_selection(self, name):
        obj = backend.select_object(name)
        if obj is not None:
            self.manager.selected_name = obj.Name

    def on_tree_double_click(self, name):
        obj = backend.object_by_name(name)
        if obj is None:
            return
        if obj.TypeId == "Sketcher::SketchObject":
            self.manager.begin_sketch(obj.Name, rollback_on_cancel=False)
            self.ribbon.setCurrentIndex(1)
        else:
            self.manager.show_object(obj)

    def open_document(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Abrir",
            "",
            "FreeCAD (*.FCStd);;STEP (*.step *.stp);;Todos (*.*)",
        )
        if path:
            backend.open_document(path)
            self.manager.show_model()
            self.refresh(True)

    def save_document(self):
        doc = backend.active_document()
        if doc is None:
            return
        path = None
        if not doc.FileName:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Guardar",
                f"{doc.Label or doc.Name}.FCStd",
                "FreeCAD (*.FCStd)",
            )
            if not path:
                return
            if not path.lower().endswith(".fcstd"):
                path += ".FCStd"
        backend.save_document(path)
        self.state.setText("Documento guardado")

    def axonometric_view(self):
        backend.axonometric_view()

    def front_view(self):
        backend.front_view()

    def top_view(self):
        backend.top_view()

    def fit_view(self):
        backend.fit_view()

    def not_implemented(self):
        QtWidgets.QMessageBox.information(
            self,
            "SolidFreeCAD alpha.10",
            "Función pendiente de implementación.",
        )

    def _apply_style(self):
        self.setStyleSheet(r"""
            QMainWindow { background: #f4f5f7; }
            QWidget#SFC10HeaderBar { background: #f7f7f8; border-bottom: 1px solid #bfc4c8; }
            QLabel#SFC10Brand { color: #b32635; font-size: 14px; font-weight: 700; font-style: italic; padding-left: 5px; }
            QToolButton#SFC10HeaderMenu { border: 0; padding: 4px 6px; font-size: 10px; }
            QToolButton#SFC10HeaderMenu:hover { background: #e7edf3; }
            QLabel#SFC10DocumentTitle { color: #24282c; font-size: 10px; }
            QLineEdit#SFC10CommandSearch { background: white; border: 1px solid #bfc5ca; padding: 2px 7px; min-height: 18px; }
            QToolBar#SFC10CommandManagerBar { background: #f8f8f9; border: 0; border-bottom: 1px solid #bfc4c8; padding: 0; spacing: 0; }
            QTabWidget#SFC10Ribbon::pane { background: #f8f8f9; border: 0; border-top: 1px solid #cfd3d7; }
            QTabWidget#SFC10Ribbon QTabBar::tab { background: #eceeef; border: 1px solid transparent; padding: 3px 9px; font-size: 9px; }
            QTabWidget#SFC10Ribbon QTabBar::tab:selected { background: #f8f8f9; border-color: #bdc3c8; }
            QFrame#SFC9RibbonGroup { background: #f8f8f9; border-right: 1px solid #d1d5d8; }
            QLabel#SFC9GroupCaption { color: #586168; font-size: 9px; }
            QDockWidget#SFC10ManagerDock { background: white; border-right: 1px solid #aeb6bc; }
            QWidget#SFC10ManagerShell { background: white; }
            QWidget#SFC10ManagerModeStrip { background: #f2f3f4; border-bottom: 1px solid #aeb6bc; }
            QToolButton#SFC10ManagerModeButton { border: 0; background: transparent; font-size: 13px; }
            QToolButton#SFC10ManagerModeButton:checked { background: white; border: 1px solid #aeb6bc; border-bottom-color: white; }
            QLineEdit#SFC10TreeFilter { border: 1px solid #bfc5ca; padding: 2px; }
            QTreeWidget#SFC10FeatureTree { background: white; border: 0; font-size: 10px; }
            QTreeWidget#SFC10FeatureTree::item { height: 19px; }
            QLabel#SFC10ModelFooter { background: #f4f5f6; border-top: 1px solid #c5cacf; color: #30363b; font-size: 9px; padding: 3px; }
            QWidget#SFC10PropertyHeader { background: #eef0f2; border-bottom: 1px solid #b7bec4; }
            QToolButton#SFC10Accept { color: #157b36; background: #e7f4e9; border: 1px solid #6eaa7d; font-size: 15px; min-width: 26px; min-height: 24px; }
            QToolButton#SFC10Cancel { color: #ae2929; background: #f7e5e5; border: 1px solid #c87979; font-size: 14px; min-width: 26px; min-height: 24px; }
            QLabel#SFC10PropertyTitle { font-weight: 600; font-size: 11px; }
            QLabel#SFC10PropertyMessage { background: #f7f8f9; border: 1px solid #c8cdd1; padding: 5px; font-size: 10px; }
            QToolButton#SFC10SectionHeader { background: #e8ebed; border: 0; border-top: 1px solid #bdc4c9; text-align: left; padding: 4px; font-weight: 600; font-size: 10px; }
            QLabel#SFC10SelectionBox { background: white; border: 1px solid #bfc5ca; padding: 5px; min-height: 24px; }
            QLabel#SFC10Definition { background: #eff6ee; border: 1px solid #a8c5a3; padding: 4px; }
            QToolBar#SFC10ViewToolbar { background: #f5f6f7; border-left: 1px solid #c3c8cc; spacing: 1px; }
            QStatusBar { background: #f7f7f8; border-top: 1px solid #bfc4c8; font-size: 9px; }
        """)

    def closeEvent(self, event):
        if self.manager.operation is not None:
            self.cancel_manager_operation()
        self.timer.stop()
        central = self.takeCentralWidget()
        if central is not None:
            central.setParent(None)
            self.host.setCentralWidget(central)
        self.host.show()
        event.accept()


def show_standalone():
    global _window
    if _window is None:
        _window = SolidFreeCADWindow()
    _window.showMaximized()
    _window.raise_()
    _window.activateWindow()
    _window.host.hide()
    return _window
