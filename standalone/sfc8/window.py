"""Standalone SolidFreeCAD alpha.9 application window."""
from __future__ import annotations

import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from . import backend
from .manager import ManagerDock
from .widgets import Ribbon

_APP_NAME = "SolidFreeCAD Professional alpha.9"
_window = None


class SolidFreeCADWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.host = Gui.getMainWindow()
        self._host_central = None
        self._signature = None
        self.setObjectName("SolidFreeCADStandaloneWindow")
        self.resize(1500, 900)
        self.setMinimumSize(1100, 700)

        self._take_document_view()
        self._build_menu()
        self.manager = ManagerDock(self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.manager)
        self._build_status()
        self._apply_style()
        backend.set_light_background()

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(400)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh(True)

    def _take_document_view(self):
        self._host_central = self.host.takeCentralWidget()
        if self._host_central is None:
            self._host_central = QtWidgets.QLabel(
                "No se encontró la vista de documento de FreeCAD."
            )
            self._host_central.setAlignment(QtCore.Qt.AlignCenter)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        quick = QtWidgets.QToolBar("Acceso rápido")
        quick.setObjectName("SFC9QuickAccess")
        quick.setMovable(False)
        brand = QtWidgets.QLabel("  SolidFreeCAD  ")
        brand.setObjectName("SFC9Brand")
        quick.addWidget(brand)
        for text, callback in (
            ("Nueva", self.new_part),
            ("Abrir", self.open_document),
            ("Guardar", self.save_document),
        ):
            action = quick.addAction(text)
            action.triggered.connect(callback)
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        quick.addWidget(spacer)
        search = QtWidgets.QLineEdit()
        search.setPlaceholderText("Buscar comandos")
        search.setMinimumWidth(220)
        quick.addWidget(search)
        layout.addWidget(quick)

        self.ribbon = Ribbon(self)
        self.ribbon.setMaximumHeight(150)
        layout.addWidget(self.ribbon)
        layout.addWidget(self._host_central, 1)
        self.setCentralWidget(container)

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("Archivo")
        for text, callback in (
            ("Nueva pieza", self.new_part),
            ("Abrir...", self.open_document),
            ("Guardar", self.save_document),
        ):
            action = file_menu.addAction(text)
            action.triggered.connect(callback)
        view_menu = self.menuBar().addMenu("Ver")
        for text, callback in (
            ("Isométrica", self.axonometric_view),
            ("Frontal", self.front_view),
            ("Superior", self.top_view),
            ("Ajustar", self.fit_view),
        ):
            action = view_menu.addAction(text)
            action.triggered.connect(callback)
        about = self.menuBar().addMenu("Ayuda").addAction("Acerca de")
        about.triggered.connect(
            lambda: QtWidgets.QMessageBox.information(
                self,
                "SolidFreeCAD alpha.9",
                "Ventana propia y administrador contextual único con FreeCAD como motor CAD.",
            )
        )

    def _build_status(self):
        self.state = QtWidgets.QLabel("Listo")
        self.statusBar().addWidget(self.state, 1)
        self.statusBar().addPermanentWidget(
            QtWidgets.QLabel("FreeCAD 1.1.1 · OpenCASCADE · FCStd")
        )

    def refresh(self, force=False):
        doc = backend.active_document()
        signature = None if doc is None else tuple(
            (o.Name, o.Label, o.TypeId, bool(getattr(getattr(o, "ViewObject", None), "Visibility", False)))
            for o in doc.Objects
        )
        if force or signature != self._signature:
            self._signature = signature
            self.manager.rebuild_tree()
            self.manager.refresh_operation()
        label = "Sin documento" if doc is None else (doc.Label or doc.Name)
        self.setWindowTitle(f"{_APP_NAME} — {label}")

    def new_part(self):
        if self.manager.operation is not None:
            self.cancel_manager_operation()
        backend.new_part()
        self.manager.show_model()
        self.state.setText("Pieza nueva")
        self.refresh(True)

    def new_sketch(self):
        if self.manager.operation is not None:
            self.cancel_manager_operation()
        sketch = backend.new_sketch()
        self.manager.begin_sketch(sketch.Name, rollback_on_cancel=True)
        self.ribbon.setCurrentIndex(1)
        self.state.setText("Croquis activo · administrador contextual")
        self.refresh(True)

    def add_rectangle(self):
        if self.manager.operation != "sketch":
            self.new_sketch()
        backend.add_rectangle(self.manager.width.value(), self.manager.height.value())
        self.manager.refresh_operation()
        self.state.setText("Rectángulo agregado al croquis")
        self.refresh(True)

    def add_circle(self):
        if self.manager.operation != "sketch":
            self.new_sketch()
        backend.add_circle(self.manager.radius.value())
        self.manager.refresh_operation()
        self.state.setText("Círculo agregado al croquis")
        self.refresh(True)

    def begin_pad(self):
        sketch = backend.active_sketch()
        if sketch is None:
            QtWidgets.QMessageBox.warning(
                self, "Saliente/Base", "Cree o seleccione un croquis cerrado."
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
        else:
            sketch = backend.active_sketch()
            if sketch is not None:
                self.manager.begin_sketch(sketch.Name, rollback_on_cancel=False)
                self.accept_manager_operation()

    def show_sketch_properties(self):
        sketch = backend.active_sketch()
        if sketch is None:
            QtWidgets.QMessageBox.information(
                self, "Croquis", "Cree o seleccione un croquis."
            )
            return
        self.manager.begin_sketch(sketch.Name, rollback_on_cancel=False)
        self.ribbon.setCurrentIndex(1)

    def on_tree_selection(self, name):
        obj = backend.select_object(name)
        self.manager.show_object(obj)

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
            self, "Abrir", "", "FreeCAD (*.FCStd);;STEP (*.step *.stp);;Todos (*.*)"
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
                self, "Guardar", f"{doc.Label or doc.Name}.FCStd", "FreeCAD (*.FCStd)"
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
            "SolidFreeCAD alpha.9",
            "Se implementará después de estabilizar pieza, croquis y operaciones.",
        )

    def _apply_style(self):
        self.setStyleSheet(r"""
            QMainWindow { background: #eef1f5; }
            QMenuBar { background: #f7f7f8; border-bottom: 1px solid #cdd1d5; }
            QMenuBar::item { padding: 5px 9px; }
            QToolBar#SFC9QuickAccess { background: #f7f7f8; border: 0;
                border-bottom: 1px solid #cdd1d5; spacing: 4px; padding: 3px 6px; }
            QLabel#SFC9Brand { color: #b32635; font-size: 15px;
                font-weight: 700; font-style: italic; }
            QTabWidget#SFC9Ribbon::pane { background: #f7f7f8; border: 0;
                border-top: 1px solid #cdd1d5; }
            QTabWidget#SFC9Ribbon QTabBar::tab { background: #eceff2;
                padding: 5px 12px; border: 1px solid transparent; }
            QTabWidget#SFC9Ribbon QTabBar::tab:selected { background: #f7f7f8;
                border-color: #c5c9cd; }
            QFrame#SFC9RibbonGroup { background: #f7f7f8;
                border-right: 1px solid #d6d9dc; }
            QLabel#SFC9GroupCaption { color: #606a72; font-size: 10px; }
            QDockWidget#SFC9ManagerDock { background: white; border-right: 1px solid #bcc3c9; }
            QTabBar#SFC9ManagerTabs::tab { background: #e9ecef; padding: 6px 7px;
                border-right: 1px solid #c7ccd0; font-size: 10px; }
            QTabBar#SFC9ManagerTabs::tab:selected { background: white; }
            QTreeWidget#SFC9FeatureTree { background: white; border: 1px solid #d4d8dc; }
            QTreeWidget#SFC9FeatureTree::item { height: 21px; }
            QWidget#SFC9PropertyHeader { background: #e4e8eb;
                border-bottom: 1px solid #b8c0c6; }
            QToolButton#SFC9Accept { color: #16833b; background: #e5f5e9;
                border: 1px solid #78b98a; font-size: 16px; min-width: 27px; }
            QToolButton#SFC9Cancel { color: #b22c2c; background: #fae8e8;
                border: 1px solid #ce8888; font-size: 15px; min-width: 27px; }
            QLabel#SFC9PropertyTitle { font-weight: 650; font-size: 12px; }
            QLabel#SFC9PropertyMessage { background: #eef5fb;
                border: 1px solid #b9cede; padding: 7px; }
            QToolButton#SFC9SectionHeader { background: #e8ebee; border: 0;
                border-top: 1px solid #c5cbd0; text-align: left; padding: 5px; font-weight: 600; }
            QLabel#SFC9SelectionBox { background: #fff8d8; border: 1px solid #d6c878;
                padding: 6px; min-height: 25px; }
            QLabel#SFC9Definition { background: #edf6ec; border: 1px solid #a9c9a5;
                padding: 5px; }
            QLabel#SFC9ManagerFooter { color: #747c82; font-size: 9px; }
            QStatusBar { background: #f7f7f8; border-top: 1px solid #cdd1d5; }
        """)

    def closeEvent(self, event):
        if self.manager.operation is not None:
            self.cancel_manager_operation()
        self.timer.stop()
        container = self.takeCentralWidget()
        if container is not None and self._host_central is not None:
            layout = container.layout()
            if layout:
                layout.removeWidget(self._host_central)
            self._host_central.setParent(None)
            self.host.setCentralWidget(self._host_central)
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
