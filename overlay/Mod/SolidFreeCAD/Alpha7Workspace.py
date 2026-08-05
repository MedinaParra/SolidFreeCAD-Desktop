"""SolidFreeCAD alpha.7 professional Windows workspace.

Alpha.7 replaces the visibly layered alpha.6 desktop with one coherent shell:
quick access, command ribbon, compact design tree and a light modelling area.
FreeCAD commands, FCStd documents and OpenCASCADE geometry remain native.
"""
from __future__ import annotations

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from SolidFreeCAD.ClassicWorkspace import CommandSpec, _icon, _run_candidates
from SolidFreeCAD.MechanicalWorkspace import show_workspace as show_alpha6_workspace

_QUICK = "SolidFreeCADAlpha7QuickAccess"
_MANAGER = "SolidFreeCADAlpha7Manager"
_STATUS = "SolidFreeCADAlpha7Status"
_workspace = None


def _find_combo(main):
    for dock in main.findChildren(QtWidgets.QDockWidget):
        name = (dock.objectName() or "").lower()
        title = (dock.windowTitle() or "").lower()
        if "combo" in name or "vista combinada" in title:
            return dock
    return None


def _light_view():
    view = App.ParamGet("User parameter:BaseApp/Preferences/View")
    view.SetBool("Simple", False)
    view.SetBool("UseBackgroundColorMid", False)
    view.SetUnsigned("BackgroundColor", 0xEEF2F7FF)
    view.SetUnsigned("BackgroundColor2", 0xFFFFFFFF)
    view.SetUnsigned("BackgroundColor3", 0xFFFFFFFF)
    try:
        if Gui.activeDocument():
            Gui.activeDocument().activeView().redraw()
    except Exception:
        pass


class QuickAccess(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super().__init__("Acceso rápido", parent)
        self.setObjectName(_QUICK)
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QtCore.QSize(18, 18))

        brand = QtWidgets.QLabel("  SFC  ")
        brand.setObjectName("SFCAlpha7Brand")
        self.addWidget(brand)
        self.addSeparator()

        for title, icon, commands in (
            ("Nueva pieza", "archivo/nuevo.svg", ("SFC_CreatePart",)),
            ("Abrir", "archivo/abrir.svg", ("SFC_Open", "Std_Open")),
            ("Guardar", "archivo/guardar.svg", ("SFC_Save", "Std_Save")),
            ("Deshacer", "vistas/ajustar.svg", ("Std_Undo",)),
            ("Rehacer", "vistas/isometrica.svg", ("Std_Redo",)),
        ):
            action = self.addAction(_icon(icon), title)
            action.setToolTip(title)
            action.triggered.connect(
                lambda _checked=False, candidates=commands: _run_candidates(candidates)
            )

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.addWidget(spacer)
        self.search = QtWidgets.QLineEdit()
        self.search.setObjectName("SFCAlpha7Search")
        self.search.setPlaceholderText("Buscar comandos")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(220)
        self.search.returnPressed.connect(self._search)
        self.addWidget(self.search)

    def _search(self):
        text = self.search.text().strip().lower()
        commands = (
            ("pieza", ("SFC_CreatePart",)),
            ("croquis", ("SFC_NewSketch", "Sketcher_NewSketch")),
            ("saliente", ("SFC_Pad", "PartDesign_Pad")),
            ("corte", ("SFC_Pocket", "PartDesign_Pocket")),
            ("revolución", ("SFC_Revolution", "PartDesign_Revolution")),
            ("redondeo", ("SFC_Fillet", "PartDesign_Fillet")),
            ("chaflán", ("SFC_Chamfer", "PartDesign_Chamfer")),
            ("medir", ("Std_Measure", "Part_Measure_Menu")),
        )
        for label, candidates in commands:
            if text and text in label:
                _run_candidates(candidates)
                self.search.clear()
                return


class DesignManager(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Administrador de diseño", parent)
        self.setObjectName(_MANAGER)
        self.setMinimumWidth(205)
        self.setMaximumWidth(285)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self._signature = None

        body = QtWidgets.QWidget()
        root = QtWidgets.QVBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setObjectName("SFCAlpha7ManagerTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._tree_page(), "Modelo")
        self.tabs.addTab(self._properties_page(), "Propiedades")
        self.tabs.addTab(self._config_page(), "Configuraciones")
        root.addWidget(self.tabs)
        self.setWidget(body)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh(True)

    def _tree_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(3, 3, 3, 3)
        self.filter = QtWidgets.QLineEdit()
        self.filter.setPlaceholderText("Filtrar árbol")
        self.filter.setClearButtonEnabled(True)
        layout.addWidget(self.filter)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setObjectName("SFCAlpha7Tree")
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        layout.addWidget(self.tree, 1)
        footer = QtWidgets.QLabel("Historial paramétrico FCStd")
        footer.setObjectName("SFCAlpha7Footer")
        layout.addWidget(footer)
        return page

    def _properties_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(7, 7, 7, 7)
        controls = QtWidgets.QHBoxLayout()
        ok = QtWidgets.QToolButton()
        ok.setIcon(_icon("propertymanager/aceptar.svg"))
        ok.clicked.connect(self._accept)
        controls.addWidget(ok)
        cancel = QtWidgets.QToolButton()
        cancel.setIcon(_icon("propertymanager/cancelar.svg"))
        cancel.clicked.connect(self._cancel)
        controls.addWidget(cancel)
        controls.addStretch(1)
        layout.addLayout(controls)
        title = QtWidgets.QLabel("Propiedades de la operación")
        title.setObjectName("SFCAlpha7PropertyTitle")
        layout.addWidget(title)
        note = QtWidgets.QLabel("Seleccione una entidad u operación para editar sus parámetros.")
        note.setWordWrap(True)
        note.setObjectName("SFCAlpha7PropertyNote")
        layout.addWidget(note)
        layout.addStretch(1)
        return page

    def _config_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        tree = QtWidgets.QTreeWidget()
        tree.setHeaderLabels(["Configuración", "Estado"])
        tree.addTopLevelItem(QtWidgets.QTreeWidgetItem(["Predeterminado", "Activa"]))
        layout.addWidget(tree)
        return page

    def refresh(self, force=False):
        doc = App.ActiveDocument
        signature = None if doc is None else tuple((o.Name, o.Label, o.TypeId) for o in doc.Objects)
        if not force and signature == self._signature:
            return
        self._signature = signature
        self.tree.clear()
        if doc is None:
            root = QtWidgets.QTreeWidgetItem(["Nueva pieza"])
            root.addChild(QtWidgets.QTreeWidgetItem(["Use Archivo > Nueva pieza"]))
            self.tree.addTopLevelItem(root)
            root.setExpanded(True)
            return
        root = QtWidgets.QTreeWidgetItem([doc.Label or doc.Name])
        self.tree.addTopLevelItem(root)
        for label in ("Historial", "Sensores", "Anotaciones", "Material <sin especificar>"):
            root.addChild(QtWidgets.QTreeWidgetItem([label]))
        origin = QtWidgets.QTreeWidgetItem(["Origen"])
        for plane in ("Alzado", "Planta", "Vista lateral"):
            origin.addChild(QtWidgets.QTreeWidgetItem([plane]))
        root.addChild(origin)
        for obj in doc.Objects:
            root.addChild(QtWidgets.QTreeWidgetItem([obj.Label or obj.Name]))
        root.setExpanded(True)

    def _accept(self):
        try:
            Gui.Control.closeDialog()
            if Gui.activeDocument():
                Gui.activeDocument().resetEdit()
        except Exception:
            pass
        self.tabs.setCurrentIndex(0)

    def _cancel(self):
        self._accept()

    def closeEvent(self, event):
        event.ignore()
        self.hide()


class Alpha7Workspace:
    def __init__(self):
        self.main = Gui.getMainWindow()
        self.quick = None
        self.manager = None
        self.ribbon = None
        self._native = {}
        self.title_timer = QtCore.QTimer(self.main)
        self.title_timer.setInterval(1000)
        self.title_timer.timeout.connect(self._title)

    def show(self):
        show_alpha6_workspace()
        self._hide_native_toolbars()
        self._hide_alpha6_panels()
        self._quick_access()
        self._design_manager()
        self._prepare_ribbon()
        self._place_combo()
        self._style()
        self._status()
        _light_view()
        self._title()
        self.title_timer.start()
        return self

    def hide(self):
        self.title_timer.stop()
        for widget in (self.quick, self.manager, self.ribbon):
            if widget is not None:
                widget.hide()
        for toolbar in self.main.findChildren(QtWidgets.QToolBar):
            key = toolbar.objectName() or toolbar.windowTitle()
            if self._native.get(key, False):
                toolbar.show()

    def _hide_native_toolbars(self):
        for toolbar in self.main.findChildren(QtWidgets.QToolBar):
            key = toolbar.objectName() or toolbar.windowTitle()
            if key not in self._native:
                self._native[key] = toolbar.isVisible()
            toolbar.hide()

    def _hide_alpha6_panels(self):
        for name in ("SolidFreeCADFeatureManager", "SolidFreeCADClassicPropertyManager", "SolidFreeCADHeadsUpToolbar"):
            widget = self.main.findChild(QtWidgets.QWidget, name)
            if widget is not None:
                widget.hide()

    def _quick_access(self):
        self.quick = self.main.findChild(QtWidgets.QToolBar, _QUICK)
        if self.quick is None:
            self.quick = QuickAccess(self.main)
            self.main.addToolBar(QtCore.Qt.TopToolBarArea, self.quick)
        self.quick.show()

    def _design_manager(self):
        self.manager = self.main.findChild(QtWidgets.QDockWidget, _MANAGER)
        if self.manager is None:
            self.manager = DesignManager(self.main)
            self.main.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.manager)
        self.manager.show()
        self.manager.raise_()

    def _prepare_ribbon(self):
        self.ribbon = self.main.findChild(QtWidgets.QDockWidget, "SolidFreeCADClassicCommandManager")
        if self.ribbon is None:
            return
        self.ribbon.setMinimumHeight(116)
        self.ribbon.setMaximumHeight(145)
        self.ribbon.show()
        tabs = self.main.findChild(QtWidgets.QTabWidget, "SolidFreeCADCommandTabs")
        if tabs is not None:
            labels = [tabs.tabText(i) for i in range(tabs.count())]
            if "Piezas soldadas" not in labels:
                groups = (("Estructura", (
                    CommandSpec("Miembro estructural", "operaciones/saliente_base.svg", ("Arch_Profile",), "Insertar perfil", True, True),
                    CommandSpec("Recortar/Extender", "croquis/recortar.svg", ("PartDesign_Boolean",), "Ajustar miembros", True, True),
                    CommandSpec("Cordón", "operaciones/redondeo.svg", ("PartDesign_AdditivePipe",), "Representar soldadura", False, True),
                )),)
                tabs.insertTab(min(4, tabs.count()), self.ribbon._make_tab(groups), "Piezas soldadas")

    def _place_combo(self):
        combo = _find_combo(self.main)
        if combo is not None:
            self.main.addDockWidget(QtCore.Qt.LeftDockWidgetArea, combo)
            self.main.tabifyDockWidget(self.manager, combo)
            combo.hide()
            self.manager.raise_()

    def _title(self):
        doc = "Sin documento" if App.ActiveDocument is None else (App.ActiveDocument.Label or App.ActiveDocument.Name)
        self.main.setWindowTitle(f"SolidFreeCAD Professional alpha.7 — {doc}")

    def _status(self):
        label = self.main.findChild(QtWidgets.QLabel, _STATUS)
        if label is None:
            label = QtWidgets.QLabel("SolidFreeCAD alpha.7 · FreeCAD 1.1.1 · OpenCASCADE · FCStd")
            label.setObjectName(_STATUS)
            self.main.statusBar().addPermanentWidget(label)

    def _style(self):
        marker = "/* SolidFreeCAD alpha7 professional */"
        if marker in self.main.styleSheet():
            return
        self.main.setStyleSheet(self.main.styleSheet() + marker + r"""
            QMainWindow { background: #f4f5f7; }
            QMenuBar { background: #f7f7f8; border-bottom: 1px solid #d2d6da; padding: 1px; font-size: 12px; }
            QMenuBar::item { padding: 4px 8px; }
            QToolBar#SolidFreeCADAlpha7QuickAccess { background: #f7f7f8; border: 0; border-bottom: 1px solid #d2d6da; spacing: 2px; padding: 2px 5px; }
            QLabel#SFCAlpha7Brand { color: #b21f2d; font-size: 14px; font-weight: 700; font-style: italic; padding: 2px 9px; }
            QLineEdit#SFCAlpha7Search { background: white; border: 1px solid #bfc5ca; padding: 3px 7px; }
            QDockWidget#SolidFreeCADClassicCommandManager { background: #f7f7f8; border-bottom: 1px solid #c7cbd0; }
            QTabWidget#SolidFreeCADCommandTabs::pane { background: #f7f7f8; border: 0; border-top: 1px solid #cfd3d7; }
            QTabWidget#SolidFreeCADCommandTabs QTabBar::tab { background: #eceef0; border: 1px solid transparent; padding: 4px 10px; font-size: 10px; }
            QTabWidget#SolidFreeCADCommandTabs QTabBar::tab:selected { background: #f7f7f8; border-color: #c7cbd0; }
            QDockWidget#SolidFreeCADAlpha7Manager { background: white; border-right: 1px solid #bfc4c8; }
            QTabWidget#SFCAlpha7ManagerTabs::pane { border: 0; background: white; }
            QTabWidget#SFCAlpha7ManagerTabs QTabBar::tab { background: #eceef0; border: 0; border-right: 1px solid #c9cdd1; padding: 5px 7px; font-size: 10px; }
            QTabWidget#SFCAlpha7ManagerTabs QTabBar::tab:selected { background: white; }
            QTreeWidget#SFCAlpha7Tree { background: white; border: 1px solid #d5d8db; font-size: 11px; }
            QTreeWidget#SFCAlpha7Tree::item { height: 19px; }
            QLabel#SFCAlpha7PropertyTitle { font-weight: 600; font-size: 12px; }
            QLabel#SFCAlpha7PropertyNote { background: #f4f7fa; border: 1px solid #cdd6dd; padding: 6px; }
            QLabel#SFCAlpha7Footer { color: #737a80; font-size: 9px; }
            QToolButton { padding: 2px 4px; }
            QToolButton:hover { background: #e6f0f8; border: 1px solid #8eb9d6; }
            QStatusBar { background: #f7f7f8; border-top: 1px solid #d2d6da; font-size: 10px; }
        """)


def show_workspace():
    global _workspace
    if _workspace is None:
        _workspace = Alpha7Workspace()
    return _workspace.show()


def hide_workspace():
    if _workspace is not None:
        _workspace.hide()
