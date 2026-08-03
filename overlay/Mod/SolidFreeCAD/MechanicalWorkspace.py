"""SolidFreeCAD alpha.6 integrated mechanical-CAD workspace.

Extends the validated alpha.5 CommandManager with an integrated FeatureManager,
contextual properties, configurations and a compact Heads-Up view toolbar.
The implementation keeps FreeCAD's native commands, BRep engine and FCStd files.
"""
from __future__ import annotations

from typing import Sequence

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from SolidFreeCAD.ClassicWorkspace import (
    CommandSpec,
    _first_available,
    _icon,
    _run_candidates,
    hide_workspace as hide_classic_workspace,
    show_workspace as show_classic_workspace,
)

_FEATURE_MANAGER = "SolidFreeCADFeatureManager"
_MANAGER_TABS = "SolidFreeCADManagerTabs"
_FEATURE_TREE = "SolidFreeCADFeatureTree"
_HEADS_UP = "SolidFreeCADHeadsUpToolbar"
_feature_manager = None


class _SelectionObserver:
    def __init__(self, owner):
        self.owner = owner

    def addSelection(self, *_args):
        self.owner.refresh_selection()

    def removeSelection(self, *_args):
        self.owner.refresh_selection()

    def clearSelection(self, *_args):
        self.owner.refresh_selection()


class FeatureManager(QtWidgets.QDockWidget):
    MESSAGES = {
        "idle": "Cree una pieza o abra un archivo para comenzar.",
        "part": "Seleccione un plano o una cara plana y cree un croquis.",
        "sketch": "Dibuje el perfil, aplique relaciones y deje el croquis totalmente definido.",
        "feature": "Configure la operación y revise la previsualización antes de aceptar.",
        "surface": "Seleccione perfiles, caras o trayectorias compatibles.",
        "evaluate": "Seleccione la geometría que desea medir o comprobar.",
        "shaft": "Edite diámetros, longitudes y chavetero del eje paramétrico.",
        "assembly": "Inserte componentes y defina sus relaciones mecánicas.",
    }

    def __init__(self, parent=None):
        super().__init__("SolidFreeCAD", parent)
        self.setObjectName(_FEATURE_MANAGER)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.setMinimumWidth(285)
        self._mode = "idle"
        self._signature = None
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setObjectName(_MANAGER_TABS)
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._model_page(), "Modelo")
        self.tabs.addTab(self._property_page(), "Propiedades")
        self.tabs.addTab(self._configuration_page(), "Configuraciones")
        self.setWidget(self.tabs)
        self._observer = _SelectionObserver(self)
        Gui.Selection.addObserver(self._observer)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(700)
        self._timer.timeout.connect(self.refresh_tree)
        self._timer.start()
        self.refresh_tree(force=True)
        self.refresh_selection()

    def _model_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(5, 5, 5, 5)
        title = QtWidgets.QLabel("Historial de diseño")
        title.setObjectName("SFCManagerTitle")
        layout.addWidget(title)
        self.filter = QtWidgets.QLineEdit()
        self.filter.setPlaceholderText("Filtrar operaciones y croquis")
        self.filter.textChanged.connect(self._filter_tree)
        layout.addWidget(self.filter)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setObjectName(_FEATURE_TREE)
        self.tree.setHeaderHidden(True)
        self.tree.itemSelectionChanged.connect(self._select_tree_object)
        layout.addWidget(self.tree, 1)
        footer = QtWidgets.QLabel("Motor nativo FreeCAD · Historial FCStd")
        footer.setObjectName("SFCManagerFooter")
        layout.addWidget(footer)
        return page

    def _property_page(self):
        page = QtWidgets.QWidget()
        root = QtWidgets.QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        header = QtWidgets.QWidget()
        header.setObjectName("SFCAlpha6PropertyHeader")
        row = QtWidgets.QHBoxLayout(header)
        row.setContentsMargins(7, 5, 7, 5)
        self.accept = QtWidgets.QToolButton()
        self.accept.setObjectName("SFCAlpha6Accept")
        self.accept.setIcon(_icon("propertymanager/aceptar.svg"))
        self.accept.clicked.connect(self.accept_current)
        row.addWidget(self.accept)
        self.cancel = QtWidgets.QToolButton()
        self.cancel.setObjectName("SFCAlpha6Cancel")
        self.cancel.setIcon(_icon("propertymanager/cancelar.svg"))
        self.cancel.clicked.connect(self.cancel_current)
        row.addWidget(self.cancel)
        self.title = QtWidgets.QLabel("Preparar modelo")
        self.title.setObjectName("SFCManagerTitle")
        row.addWidget(self.title, 1)
        root.addWidget(header)

        body = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(body)
        self.message = QtWidgets.QLabel(self.MESSAGES["idle"])
        self.message.setObjectName("SFCAlpha6Message")
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        self.definition = QtWidgets.QLabel("Estado: sin documento")
        self.definition.setObjectName("SFCDefinitionStatus")
        layout.addWidget(self.definition)
        group = QtWidgets.QGroupBox("Selección")
        group_layout = QtWidgets.QVBoxLayout(group)
        self.selection = QtWidgets.QLabel("Sin selección")
        self.selection.setWordWrap(True)
        group_layout.addWidget(self.selection)
        layout.addWidget(group)
        flow = QtWidgets.QGroupBox("Flujo recomendado")
        flow_layout = QtWidgets.QVBoxLayout(flow)
        for label, icon, commands, mode in (
            ("1. Nueva pieza", "archivo/nuevo.svg", ("SFC_CreatePart",), "part"),
            ("2. Nuevo croquis", "croquis/nuevo_croquis.svg", ("SFC_NewSketch", "Sketcher_NewSketch"), "sketch"),
            ("3. Saliente/Base", "operaciones/saliente_base.svg", ("SFC_Pad", "PartDesign_Pad"), "feature"),
            ("Pieza demostrativa alpha.6", "operaciones/agujero.svg", ("SFC_CreateDemoPart",), "part"),
        ):
            button = QtWidgets.QPushButton(label)
            button.setIcon(_icon(icon))
            button.clicked.connect(lambda _checked=False, c=commands, m=mode: self.trigger(c, m))
            flow_layout.addWidget(button)
        layout.addWidget(flow)
        layout.addStretch(1)
        root.addWidget(body, 1)
        return page

    def _configuration_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        note = QtWidgets.QLabel(
            "Base preparada para variantes dimensionales futuras sin cambiar el formato FCStd."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        tree = QtWidgets.QTreeWidget()
        tree.setHeaderLabels(["Configuración", "Estado"])
        tree.addTopLevelItem(QtWidgets.QTreeWidgetItem(["Predeterminado", "Activa"]))
        layout.addWidget(tree, 1)
        return page

    def set_mode(self, mode: str, title: str | None = None):
        self._mode = mode if mode in self.MESSAGES else "idle"
        names = {"idle": "Preparar modelo", "part": "Pieza", "sketch": "Croquis",
                 "feature": "Operación 3D", "surface": "Superficie", "evaluate": "Evaluar",
                 "shaft": "Eje paramétrico", "assembly": "Ensamblaje"}
        self.title.setText(title or names[self._mode])
        self.message.setText(self.MESSAGES[self._mode])
        self.definition.setText(
            "Croquis: revise cotas y relaciones" if self._mode == "sketch"
            else ("Modelo: listo para recomputar" if App.ActiveDocument else "Estado: sin documento")
        )
        self.tabs.setCurrentIndex(1 if self._mode != "idle" else 0)

    def trigger(self, commands: Sequence[str], mode: str):
        if _run_candidates(commands):
            self.set_mode(mode)
            self.refresh_tree(force=True)

    def accept_current(self):
        try:
            Gui.Control.closeDialog()
            if Gui.activeDocument():
                Gui.activeDocument().resetEdit()
        except Exception as exc:
            App.Console.PrintMessage(f"SolidFreeCAD alpha.6 accept: {exc}\n")
        self.set_mode("part" if App.ActiveDocument else "idle")
        self.refresh_tree(force=True)

    def cancel_current(self):
        try:
            Gui.Control.closeDialog()
            if Gui.activeDocument():
                Gui.activeDocument().resetEdit()
        except Exception as exc:
            App.Console.PrintMessage(f"SolidFreeCAD alpha.6 cancel: {exc}\n")
        self.set_mode("part" if App.ActiveDocument else "idle")

    def refresh_tree(self, force=False):
        doc = App.ActiveDocument
        signature = None if doc is None else tuple((o.Name, o.Label, o.TypeId) for o in doc.Objects)
        if not force and signature == self._signature:
            return
        self._signature = signature
        self.tree.clear()
        if doc is None:
            self.tree.addTopLevelItem(QtWidgets.QTreeWidgetItem(["Sin documento activo"]))
            return
        root = QtWidgets.QTreeWidgetItem([doc.Label or doc.Name])
        self.tree.addTopLevelItem(root)
        origin = QtWidgets.QTreeWidgetItem(["Origen"])
        root.addChild(origin)
        for plane in ("Plano XY", "Plano XZ", "Plano YZ"):
            origin.addChild(QtWidgets.QTreeWidgetItem([plane]))
        for obj in doc.Objects:
            item = QtWidgets.QTreeWidgetItem([obj.Label or obj.Name])
            item.setData(0, QtCore.Qt.UserRole, obj.Name)
            root.addChild(item)
        root.setExpanded(True)
        self._filter_tree(self.filter.text())

    def _filter_tree(self, text):
        needle = text.strip().lower()
        root = self.tree.invisibleRootItem()
        def visit(item):
            child_match = any(visit(item.child(i)) for i in range(item.childCount()))
            visible = not needle or needle in item.text(0).lower() or child_match
            item.setHidden(not visible)
            return visible
        for index in range(root.childCount()):
            visit(root.child(index))

    def _select_tree_object(self):
        items = self.tree.selectedItems()
        if not items or App.ActiveDocument is None:
            return
        name = items[0].data(0, QtCore.Qt.UserRole)
        obj = App.ActiveDocument.getObject(name) if name else None
        if obj is not None:
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(obj)

    def refresh_selection(self):
        selected = Gui.Selection.getSelection()
        self.selection.setText(
            f"{selected[0].Label} ({selected[0].TypeId})" if selected else "Sin selección"
        )

    def closeEvent(self, event):
        event.ignore()
        self.hide()


def _extra_groups(kind):
    if kind == "sheet":
        return (("Chapa", (
            CommandSpec("Pieza de chapa", "operaciones/saliente_base.svg", ("PartDesign_Body",), "Crear pieza de chapa", True),
            CommandSpec("Pliegue", "operaciones/revolucion.svg", ("SheetMetal_AddWall",), "Pliegue experimental", True, True, "feature"),
            CommandSpec("Desplegar", "vistas/superior.svg", ("SheetMetal_Unfold",), "Requiere banco SheetMetal", False, True, "feature"),
        )),)
    return (("Ensamblaje", (
        CommandSpec("Nuevo ensamblaje", "archivo/nuevo.svg", ("Assembly_CreateAssembly", "Assembly_NewAssembly"), "Crear ensamblaje", True, False, "assembly"),
        CommandSpec("Insertar componente", "archivo/abrir.svg", ("Assembly_InsertComponent",), "Insertar componente", True, True, "assembly"),
        CommandSpec("Relación", "cotas_relaciones/coincidente.svg", ("Assembly_CreateJoint",), "Crear relación", False, True, "assembly"),
    )),)


def _extend_command_manager(main):
    manager = main.findChild(QtWidgets.QDockWidget, "SolidFreeCADClassicCommandManager")
    tabs = main.findChild(QtWidgets.QTabWidget, "SolidFreeCADCommandTabs")
    if manager is None or tabs is None:
        return
    labels = [tabs.tabText(i) for i in range(tabs.count())]
    if "Chapa metálica" not in labels:
        tabs.addTab(manager._make_tab(_extra_groups("sheet")), "Chapa metálica")
    if "Ensamblaje" not in labels:
        tabs.addTab(manager._make_tab(_extra_groups("assembly")), "Ensamblaje")


def _show_heads_up(main):
    toolbar = main.findChild(QtWidgets.QToolBar, _HEADS_UP)
    if toolbar is None:
        toolbar = QtWidgets.QToolBar("Vista rápida", main)
        toolbar.setObjectName(_HEADS_UP)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QtCore.QSize(20, 20))
        for title, icon, commands in (
            ("Isométrica", "vistas/isometrica.svg", ("SFC_FitAxonometric", "ViewAxonometric")),
            ("Frontal", "vistas/frontal.svg", ("Std_ViewFront",)),
            ("Superior", "vistas/superior.svg", ("Std_ViewTop",)),
            ("Derecha", "vistas/derecha.svg", ("Std_ViewRight",)),
            ("Ajustar", "vistas/ajustar.svg", ("ViewFit",)),
            ("Medir", "evaluacion/medir.svg", ("Std_Measure", "Part_Measure_Menu")),
        ):
            action = toolbar.addAction(_icon(icon), title)
            action.setEnabled(_first_available(commands) is not None)
            action.triggered.connect(lambda _checked=False, c=commands: _run_candidates(c))
        main.addToolBar(QtCore.Qt.TopToolBarArea, toolbar)
    toolbar.show()
    return toolbar


def _apply_style(main):
    marker = "/* SolidFreeCAD alpha6 visual system */"
    if marker in main.styleSheet():
        return
    main.setStyleSheet(main.styleSheet() + marker + """
        QDockWidget#SolidFreeCADFeatureManager { background: #f5f6f7; }
        QTabWidget#SolidFreeCADManagerTabs::pane { border: 1px solid #aeb7bd; }
        QTabWidget#SolidFreeCADManagerTabs QTabBar::tab { padding: 5px 9px; }
        QWidget#SFCAlpha6PropertyHeader { background: #e3e8ec; border-bottom: 1px solid #aeb7bd; }
        QLabel#SFCManagerTitle { font-weight: 600; }
        QLabel#SFCAlpha6Message { background: #fff4a8; border: 1px solid #cfb93f; color: #202020; padding: 7px; }
        QLabel#SFCDefinitionStatus { background: #e8f2fa; border: 1px solid #9fc2dc; color: #174d70; padding: 5px; }
        QLabel#SFCManagerFooter { color: #667681; padding: 3px; }
        QTreeWidget#SolidFreeCADFeatureTree { border: 1px solid #c2c9ce; background: #ffffff; }
        QToolButton#SFCAlpha6Accept { background: #e3f4e7; border: 1px solid #76b984; }
        QToolButton#SFCAlpha6Cancel { background: #f8e5e5; border: 1px solid #c98080; }
        QToolBar#SolidFreeCADHeadsUpToolbar { background: #f8f9fa; border: 1px solid #b9c2c8; spacing: 2px; }
    """)


def show_feature_manager():
    global _feature_manager
    main = Gui.getMainWindow()
    if _feature_manager is None:
        _feature_manager = main.findChild(QtWidgets.QDockWidget, _FEATURE_MANAGER)
    if _feature_manager is None:
        _feature_manager = FeatureManager(main)
        main.addDockWidget(QtCore.Qt.LeftDockWidgetArea, _feature_manager)
    _feature_manager.show()
    return _feature_manager


def show_workspace():
    classic = show_classic_workspace()
    main = Gui.getMainWindow()
    _apply_style(main)
    _extend_command_manager(main)
    manager = show_feature_manager()
    combo = main.findChild(QtWidgets.QDockWidget, "Combo View")
    if combo is not None:
        main.tabifyDockWidget(combo, manager)
    manager.raise_()
    legacy = main.findChild(QtWidgets.QDockWidget, "SolidFreeCADClassicPropertyManager")
    if legacy is not None:
        legacy.hide()
    _show_heads_up(main)
    status = main.findChild(QtWidgets.QLabel, "SolidFreeCADAlpha6Status")
    if status is None:
        status = QtWidgets.QLabel("SolidFreeCAD alpha.6 · FreeCAD 1.1.1 · FCStd")
        status.setObjectName("SolidFreeCADAlpha6Status")
        main.statusBar().addPermanentWidget(status)
    return classic


def hide_workspace():
    hide_classic_workspace()
    main = Gui.getMainWindow()
    for name, kind in ((_FEATURE_MANAGER, QtWidgets.QDockWidget), (_HEADS_UP, QtWidgets.QToolBar)):
        widget = main.findChild(kind, name)
        if widget is not None:
            widget.hide()
