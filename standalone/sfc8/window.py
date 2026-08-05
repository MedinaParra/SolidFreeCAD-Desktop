"""Standalone SolidFreeCAD application window."""
from __future__ import annotations

import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from . import backend
from .widgets import FeatureTree, PropertyPanel, Ribbon

_APP_NAME = "SolidFreeCAD Professional alpha.8"
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
        self._build_left_manager()
        self.properties = PropertyPanel(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.properties)
        self._build_status()
        self._apply_style()
        backend.set_light_background()

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(500)
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
        quick.setObjectName("SFC8QuickAccess")
        quick.setMovable(False)
        brand = QtWidgets.QLabel("  SolidFreeCAD  ")
        brand.setObjectName("SFC8Brand")
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
        self.ribbon.setMaximumHeight(145)
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
                self, "SolidFreeCAD alpha.8", "Interfaz propia con FreeCAD como motor CAD."
            )
        )

    def _build_left_manager(self):
        dock = QtWidgets.QDockWidget("Administrador de diseño", self)
        dock.setObjectName("SFC8FeatureManager")
        dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        dock.setMinimumWidth(225)
        dock.setMaximumWidth(320)
        tabs = QtWidgets.QTabWidget()
        tabs.setDocumentMode(True)
        model = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(model)
        layout.setContentsMargins(4, 4, 4, 4)
        self.tree = FeatureTree()
        layout.addWidget(self.tree)
        tabs.addTab(model, "Modelo")
        config = QtWidgets.QWidget()
        config_layout = QtWidgets.QVBoxLayout(config)
        config_layout.addWidget(QtWidgets.QLabel("Configuración predeterminada"))
        config_layout.addStretch(1)
        tabs.addTab(config, "Configuraciones")
        dock.setWidget(tabs)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)

    def _build_status(self):
        self.state = QtWidgets.QLabel("Listo")
        self.statusBar().addWidget(self.state, 1)
        self.statusBar().addPermanentWidget(
            QtWidgets.QLabel("FreeCAD 1.1.1 · OpenCASCADE · FCStd")
        )

    def refresh(self, force=False):
        doc = backend.active_document()
        signature = None if doc is None else tuple(
            (o.Name, o.Label, o.TypeId) for o in doc.Objects
        )
        if force or signature != self._signature:
            self._signature = signature
            self.tree.rebuild()
        label = "Sin documento" if doc is None else (doc.Label or doc.Name)
        self.setWindowTitle(f"{_APP_NAME} — {label}")

    def new_part(self):
        backend.new_part()
        self.properties.mode("Nueva pieza", "Seleccione Nuevo croquis para comenzar.")
        self.refresh(True)

    def new_sketch(self):
        backend.new_sketch()
        self.ribbon.setCurrentIndex(1)
        self.properties.mode(
            "Croquis",
            "Creado mediante Sketcher::SketchObject sin activar el workbench Sketcher.",
            "Crear rectángulo",
        )
        self.state.setText("Croquis activo · interfaz SolidFreeCAD estable")
        self.refresh(True)

    def add_rectangle(self):
        backend.add_rectangle(
            self.properties.width.value(), self.properties.height.value()
        )
        self.state.setText("Rectángulo creado")
        self.refresh(True)

    def add_circle(self):
        backend.add_circle(self.properties.radius.value())
        self.state.setText("Círculo creado")
        self.refresh(True)

    def pad_selected_sketch(self):
        try:
            backend.pad_sketch(self.properties.pad_length.value())
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Saliente/Base", str(exc))
            return
        self.ribbon.setCurrentIndex(0)
        self.properties.mode(
            "Saliente/Base", "Sólido creado sin cambiar la interfaz."
        )
        self.state.setText("Saliente/Base creado")
        self.refresh(True)

    def finish_sketch(self):
        self.ribbon.setCurrentIndex(0)
        self.properties.mode("Pieza", "Croquis finalizado. Puede crear un saliente/base.")

    def show_sketch_properties(self):
        self.properties.raise_()
        self.properties.mode("Medidas", "Edite las medidas y cree geometría.")

    def open_document(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Abrir", "", "FreeCAD (*.FCStd);;STEP (*.step *.stp);;Todos (*.*)"
        )
        if path:
            backend.open_document(path)
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
            self, "SolidFreeCAD alpha.8",
            "Se implementará después de estabilizar pieza, croquis y operaciones."
        )

    def _apply_style(self):
        self.setStyleSheet(r"""
            QMainWindow { background: #eef1f5; }
            QMenuBar { background: #f7f7f8; border-bottom: 1px solid #cdd1d5; }
            QMenuBar::item { padding: 5px 9px; }
            QToolBar#SFC8QuickAccess { background: #f7f7f8; border: 0;
                border-bottom: 1px solid #cdd1d5; spacing: 4px; padding: 3px 6px; }
            QLabel#SFC8Brand { color: #b32635; font-size: 15px;
                font-weight: 700; font-style: italic; }
            QTabWidget#SFC8Ribbon::pane { background: #f7f7f8; border: 0;
                border-top: 1px solid #cdd1d5; }
            QTabWidget#SFC8Ribbon QTabBar::tab { background: #eceff2;
                padding: 5px 12px; border: 1px solid transparent; }
            QTabWidget#SFC8Ribbon QTabBar::tab:selected { background: #f7f7f8;
                border-color: #c5c9cd; }
            QFrame#SFC8RibbonGroup { background: #f7f7f8;
                border-right: 1px solid #d6d9dc; }
            QLabel#SFC8GroupCaption { color: #606a72; font-size: 10px; }
            QDockWidget { background: white; }
            QTreeWidget#SFC8FeatureTree { background: white; border: 0; }
            QTreeWidget#SFC8FeatureTree::item { height: 21px; }
            QLabel#SFC8PropertyTitle { font-weight: 650; font-size: 13px; }
            QLabel#SFC8Message { background: #eef5fb;
                border: 1px solid #b9cede; padding: 7px; }
            QToolButton { padding: 3px 6px; }
            QToolButton:hover { background: #e6f0f8;
                border: 1px solid #8eb9d6; }
            QStatusBar { background: #f7f7f8;
                border-top: 1px solid #cdd1d5; }
        """)

    def closeEvent(self, event):
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
