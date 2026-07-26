"""Classic Windows workspace for SolidFreeCAD.

This module builds a compact, tabbed CAD command manager and a contextual
PropertyManager-style dock while keeping FreeCAD's native document model,
commands and file formats intact.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Sequence

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from SolidFreeCAD.ClassicIcons import ensure_icon_pack

_MODULE_DIR = os.path.dirname(__file__)
_ICON_ROOT = os.path.join(_MODULE_DIR, "Resources", "icons", "classic")
_COMMAND_MANAGER_NAME = "SolidFreeCADClassicCommandManager"
_PROPERTY_MANAGER_NAME = "SolidFreeCADClassicPropertyManager"
_workspace = None
_property_manager = None


def _icon(relative_path: str) -> QtGui.QIcon:
    path = os.path.join(_ICON_ROOT, *relative_path.split("/"))
    if os.path.exists(path):
        return QtGui.QIcon(path)
    fallback = os.path.join(_MODULE_DIR, "Resources", "icons", "SolidFreeCAD.svg")
    return QtGui.QIcon(fallback)


def _first_available(candidates: Sequence[str]) -> str | None:
    registered = set(Gui.listCommands())
    for candidate in candidates:
        if candidate in registered:
            return candidate
    return None


def _run_candidates(candidates: Sequence[str]) -> bool:
    command = _first_available(candidates)
    if not command:
        App.Console.PrintWarning(
            "SolidFreeCAD: ninguna variante del comando está disponible: "
            + ", ".join(candidates)
            + "\n"
        )
        return False
    Gui.runCommand(command, 0)
    return True


@dataclass(frozen=True)
class CommandSpec:
    title: str
    icon: str
    candidates: tuple[str, ...]
    tooltip: str
    large: bool = False
    requires_document: bool = False
    next_mode: str = ""


class _SelectionObserver:
    def __init__(self, owner):
        self.owner = owner

    def addSelection(self, *_args):
        self.owner.refresh_selection()

    def removeSelection(self, *_args):
        self.owner.refresh_selection()

    def clearSelection(self, *_args):
        self.owner.refresh_selection()


class ClassicPropertyManager(QtWidgets.QDockWidget):
    """Contextual left-side task panel inspired by classic mechanical CAD."""

    MODE_MESSAGES = {
        "idle": "Cree una pieza nueva o seleccione una operación del CommandManager.",
        "part": "Pieza activa. Seleccione un plano o una cara para comenzar un croquis.",
        "sketch": "Seleccione el plano sobre el que desea crear un croquis para la entidad.",
        "feature": "Seleccione un croquis o las aristas necesarias y configure la operación.",
        "surface": "Seleccione caras, perfiles o trayectorias compatibles con la superficie.",
        "evaluate": "Seleccione la geometría que desea medir o verificar.",
        "shaft": "Seleccione un eje SolidFreeCAD para editar sus parámetros principales.",
    }

    def __init__(self, parent=None):
        super().__init__("Administrador", parent)
        self.setObjectName(_PROPERTY_MANAGER_NAME)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.setMinimumWidth(250)
        self._mode = "idle"

        container = QtWidgets.QWidget(self)
        root = QtWidgets.QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QtWidgets.QWidget()
        header.setObjectName("SFCPropertyHeader")
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(7, 5, 7, 5)
        header_layout.setSpacing(5)

        self.accept_button = QtWidgets.QToolButton()
        self.accept_button.setObjectName("SFCAccept")
        self.accept_button.setIcon(_icon("propertymanager/aceptar.svg"))
        self.accept_button.setToolTip("Aceptar operación")
        self.accept_button.clicked.connect(self.accept_current)
        header_layout.addWidget(self.accept_button)

        self.cancel_button = QtWidgets.QToolButton()
        self.cancel_button.setObjectName("SFCCancel")
        self.cancel_button.setIcon(_icon("propertymanager/cancelar.svg"))
        self.cancel_button.setToolTip("Cancelar operación")
        self.cancel_button.clicked.connect(self.cancel_current)
        header_layout.addWidget(self.cancel_button)

        self.title_label = QtWidgets.QLabel("SolidFreeCAD")
        self.title_label.setStyleSheet("font-weight: 600; padding-left: 4px;")
        header_layout.addWidget(self.title_label, 1)

        help_button = QtWidgets.QToolButton()
        help_button.setIcon(_icon("propertymanager/ayuda.svg"))
        help_button.setToolTip("Ayuda del flujo actual")
        help_button.clicked.connect(self.show_help)
        header_layout.addWidget(help_button)
        root.addWidget(header)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        body = QtWidgets.QWidget()
        body_layout = QtWidgets.QVBoxLayout(body)
        body_layout.setContentsMargins(8, 8, 8, 8)
        body_layout.setSpacing(8)

        self.section_title = QtWidgets.QLabel("Preparar modelo")
        self.section_title.setObjectName("SFCPropertyTitle")
        self.section_title.setStyleSheet("font-weight: 600;")
        body_layout.addWidget(self.section_title)

        message_caption = QtWidgets.QLabel("Mensaje")
        message_caption.setStyleSheet("font-weight: 600; color: #4c5962;")
        body_layout.addWidget(message_caption)

        self.message = QtWidgets.QLabel(self.MODE_MESSAGES["idle"])
        self.message.setObjectName("SFCFlowMessage")
        self.message.setWordWrap(True)
        self.message.setStyleSheet(
            "QLabel { background: #fff59a; border: 1px solid #d0bd45; "
            "padding: 7px; color: #202020; }"
        )
        body_layout.addWidget(self.message)

        self.selection_group = QtWidgets.QGroupBox("Selección")
        selection_layout = QtWidgets.QVBoxLayout(self.selection_group)
        self.selection_label = QtWidgets.QLabel("Sin selección")
        self.selection_label.setWordWrap(True)
        selection_layout.addWidget(self.selection_label)
        body_layout.addWidget(self.selection_group)

        self.workflow_group = QtWidgets.QGroupBox("Flujo de pieza")
        workflow_layout = QtWidgets.QVBoxLayout(self.workflow_group)
        self.new_part_button = QtWidgets.QPushButton("1. Nueva pieza")
        self.new_part_button.setIcon(_icon("archivo/nuevo.svg"))
        self.new_part_button.clicked.connect(lambda: self.trigger(("SFC_CreatePart",), "part"))
        workflow_layout.addWidget(self.new_part_button)

        self.new_sketch_button = QtWidgets.QPushButton("2. Crear croquis")
        self.new_sketch_button.setIcon(_icon("croquis/nuevo_croquis.svg"))
        self.new_sketch_button.clicked.connect(lambda: self.trigger(("SFC_NewSketch", "Sketcher_NewSketch"), "sketch"))
        workflow_layout.addWidget(self.new_sketch_button)

        self.pad_button = QtWidgets.QPushButton("3. Saliente/Base")
        self.pad_button.setIcon(_icon("operaciones/saliente_base.svg"))
        self.pad_button.clicked.connect(lambda: self.trigger(("SFC_Pad", "PartDesign_Pad"), "feature"))
        workflow_layout.addWidget(self.pad_button)
        body_layout.addWidget(self.workflow_group)

        self.properties_group = QtWidgets.QGroupBox("Propiedades de la selección")
        properties_layout = QtWidgets.QFormLayout(self.properties_group)
        self.object_name = QtWidgets.QLabel("—")
        self.object_type = QtWidgets.QLabel("—")
        self.object_visibility = QtWidgets.QCheckBox("Visible")
        self.object_visibility.toggled.connect(self.set_selected_visibility)
        properties_layout.addRow("Nombre", self.object_name)
        properties_layout.addRow("Tipo", self.object_type)
        properties_layout.addRow("Visualización", self.object_visibility)
        body_layout.addWidget(self.properties_group)

        body_layout.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)
        self.setWidget(container)

        self._observer = _SelectionObserver(self)
        Gui.Selection.addObserver(self._observer)
        self.set_mode("idle")
        self.refresh_selection()

    def set_mode(self, mode: str, title: str | None = None):
        self._mode = mode if mode in self.MODE_MESSAGES else "idle"
        titles = {
            "idle": "Preparar modelo",
            "part": "Pieza",
            "sketch": "Editar croquis",
            "feature": "Operación 3D",
            "surface": "Superficie",
            "evaluate": "Evaluar",
            "shaft": "Eje paramétrico",
        }
        self.section_title.setText(title or titles[self._mode])
        self.message.setText(self.MODE_MESSAGES[self._mode])

    def trigger(self, candidates: Sequence[str], mode: str):
        if _run_candidates(candidates):
            self.set_mode(mode)

    def accept_current(self):
        try:
            if Gui.activeDocument():
                Gui.activeDocument().resetEdit()
            Gui.Control.closeDialog()
        except Exception as exc:
            App.Console.PrintMessage(f"SolidFreeCAD: cierre de operación: {exc}\n")
        self.set_mode("part" if App.ActiveDocument else "idle")
        self.refresh_selection()

    def cancel_current(self):
        try:
            Gui.Control.closeDialog()
            if Gui.activeDocument():
                Gui.activeDocument().resetEdit()
        except Exception as exc:
            App.Console.PrintMessage(f"SolidFreeCAD: cancelación de operación: {exc}\n")
        self.set_mode("part" if App.ActiveDocument else "idle")

    def show_help(self):
        QtWidgets.QMessageBox.information(
            self,
            "Flujo SolidFreeCAD",
            "1. Cree una pieza.\n2. Seleccione un plano o cara.\n"
            "3. Cree y restrinja el croquis.\n4. Acepte el croquis.\n"
            "5. Aplique una operación 3D.\n\n"
            "Los comandos siguen usando el motor y el formato FCStd de FreeCAD.",
        )

    def refresh_selection(self):
        selected = Gui.Selection.getSelection()
        if not selected:
            self.selection_label.setText("Sin selección")
            self.object_name.setText("—")
            self.object_type.setText("—")
            self.object_visibility.blockSignals(True)
            self.object_visibility.setChecked(False)
            self.object_visibility.blockSignals(False)
            return
        obj = selected[0]
        self.selection_label.setText(f"{obj.Label} ({obj.Name})")
        self.object_name.setText(obj.Label)
        self.object_type.setText(getattr(obj, "TypeId", type(obj).__name__))
        visible = bool(getattr(getattr(obj, "ViewObject", None), "Visibility", False))
        self.object_visibility.blockSignals(True)
        self.object_visibility.setChecked(visible)
        self.object_visibility.blockSignals(False)

    def set_selected_visibility(self, checked: bool):
        selected = Gui.Selection.getSelection()
        if selected and hasattr(selected[0], "ViewObject"):
            selected[0].ViewObject.Visibility = checked

    def closeEvent(self, event):
        event.ignore()
        self.hide()


class CommandManager(QtWidgets.QDockWidget):
    """Tabbed command strip with compact classic CAD styling."""

    def __init__(self, parent=None):
        super().__init__("CommandManager", parent)
        self.setObjectName(_COMMAND_MANAGER_NAME)
        self.setAllowedAreas(QtCore.Qt.TopDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        self.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.setTitleBarWidget(QtWidgets.QWidget())
        self.setMinimumHeight(118)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setObjectName("SolidFreeCADCommandTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(False)
        self.setWidget(self.tabs)

        for title, groups in self._tab_definitions():
            self.tabs.addTab(self._make_tab(groups), title)

    def _tab_definitions(self):
        return (
            ("Operaciones", (
                ("Pieza", (
                    CommandSpec("Nueva pieza", "archivo/nuevo.svg", ("SFC_CreatePart",), "Crear documento y Body", True),
                    CommandSpec("Croquis", "croquis/nuevo_croquis.svg", ("SFC_NewSketch", "Sketcher_NewSketch"), "Crear croquis", True, True, "sketch"),
                )),
                ("Operaciones", (
                    CommandSpec("Saliente/Base", "operaciones/saliente_base.svg", ("SFC_Pad", "PartDesign_Pad"), "Agregar material", True, True, "feature"),
                    CommandSpec("Corte-Extruir", "operaciones/corte_extruir.svg", ("SFC_Pocket", "PartDesign_Pocket"), "Quitar material", True, True, "feature"),
                    CommandSpec("Revolución", "operaciones/revolucion.svg", ("SFC_Revolution", "PartDesign_Revolution"), "Revolucionar perfil", False, True, "feature"),
                    CommandSpec("Redondeo", "operaciones/redondeo.svg", ("SFC_Fillet", "PartDesign_Fillet"), "Redondear aristas", False, True, "feature"),
                    CommandSpec("Chaflán", "operaciones/chaflan.svg", ("SFC_Chamfer", "PartDesign_Chamfer"), "Chaflanar aristas", False, True, "feature"),
                    CommandSpec("Agujero", "operaciones/agujero.svg", ("PartDesign_Hole",), "Crear agujero", False, True, "feature"),
                )),
                ("Patrones", (
                    CommandSpec("Patrón lineal", "operaciones/patron_lineal.svg", ("PartDesign_LinearPattern",), "Patrón lineal", False, True, "feature"),
                    CommandSpec("Patrón circular", "operaciones/patron_circular.svg", ("PartDesign_PolarPattern",), "Patrón circular", False, True, "feature"),
                    CommandSpec("Simetría", "operaciones/simetria.svg", ("PartDesign_Mirrored",), "Operación simétrica", False, True, "feature"),
                )),
            )),
            ("Croquis", (
                ("Croquis", (
                    CommandSpec("Nuevo croquis", "croquis/nuevo_croquis.svg", ("SFC_NewSketch", "Sketcher_NewSketch"), "Crear croquis", True, True, "sketch"),
                    CommandSpec("Línea", "croquis/linea.svg", ("Sketcher_CreatePolyline", "Sketcher_CreateLine"), "Dibujar línea", False, True, "sketch"),
                    CommandSpec("Rectángulo", "croquis/rectangulo.svg", ("Sketcher_CreateRectangle",), "Dibujar rectángulo", False, True, "sketch"),
                    CommandSpec("Círculo", "croquis/circulo.svg", ("Sketcher_CreateCircle",), "Dibujar círculo", False, True, "sketch"),
                    CommandSpec("Arco", "croquis/arco.svg", ("Sketcher_CreateArc", "Sketcher_CreateArcOfCircle"), "Dibujar arco", False, True, "sketch"),
                    CommandSpec("Spline", "croquis/spline.svg", ("Sketcher_CreateBSpline",), "Dibujar spline", False, True, "sketch"),
                    CommandSpec("Recortar", "croquis/recortar.svg", ("Sketcher_Trimming", "Sketcher_Trim"), "Recortar entidades", False, True, "sketch"),
                )),
                ("Cotas y relaciones", (
                    CommandSpec("Cota inteligente", "cotas_relaciones/cota_inteligente.svg", ("Sketcher_ConstrainDistance",), "Agregar cota", True, True, "sketch"),
                    CommandSpec("Horizontal", "cotas_relaciones/horizontal.svg", ("Sketcher_ConstrainHorizontal",), "Relación horizontal", False, True, "sketch"),
                    CommandSpec("Vertical", "cotas_relaciones/vertical.svg", ("Sketcher_ConstrainVertical",), "Relación vertical", False, True, "sketch"),
                    CommandSpec("Coincidente", "cotas_relaciones/coincidente.svg", ("Sketcher_ConstrainCoincident",), "Relación coincidente", False, True, "sketch"),
                    CommandSpec("Paralelo", "cotas_relaciones/paralelo.svg", ("Sketcher_ConstrainParallel",), "Relación paralela", False, True, "sketch"),
                    CommandSpec("Perpendicular", "cotas_relaciones/perpendicular.svg", ("Sketcher_ConstrainPerpendicular",), "Relación perpendicular", False, True, "sketch"),
                    CommandSpec("Igual", "cotas_relaciones/igual.svg", ("Sketcher_ConstrainEqual",), "Relación igual", False, True, "sketch"),
                )),
            )),
            ("Superficies", (
                ("Crear", (
                    CommandSpec("Superficie extruida", "superficies/superficie_extruida.svg", ("Surface_ExtendFace", "Part_Extrude"), "Crear superficie extruida", True, True, "surface"),
                    CommandSpec("Superficie reglada", "superficies/superficie_revolucion.svg", ("Part_RuledSurface",), "Crear superficie reglada", False, True, "surface"),
                    CommandSpec("Loft", "operaciones/loft.svg", ("PartDesign_AdditiveLoft", "Part_Loft"), "Crear loft", False, True, "surface"),
                    CommandSpec("Barrido", "operaciones/barrido.svg", ("PartDesign_AdditivePipe", "Part_Sweep"), "Crear barrido", False, True, "surface"),
                )),
                ("Modificar", (
                    CommandSpec("Recortar", "superficies/recortar_superficie.svg", ("Surface_Cut", "Part_Cut"), "Recortar superficie", False, True, "surface"),
                    CommandSpec("Coser", "superficies/coser_superficies.svg", ("Part_JoinConnect", "Part_BooleanFragments"), "Unir superficies", False, True, "surface"),
                    CommandSpec("Equidistanciar", "superficies/equidistanciar_superficie.svg", ("Part_Offset",), "Equidistanciar superficie", False, True, "surface"),
                )),
            )),
            ("Evaluar", (
                ("Inspección", (
                    CommandSpec("Medir", "evaluacion/medir.svg", ("Std_Measure", "Part_Measure_Menu"), "Medir geometría", True, True, "evaluate"),
                    CommandSpec("Verificar geometría", "evaluacion/verificar_geometria.svg", ("Part_CheckGeometry",), "Verificar BRep", True, True, "evaluate"),
                    CommandSpec("Interferencia", "evaluacion/interferencia.svg", ("Part_BooleanFragments",), "Comprobar interferencia", False, True, "evaluate"),
                )),
                ("Vistas", (
                    CommandSpec("Isométrica", "vistas/isometrica.svg", ("SFC_FitAxonometric", "ViewAxonometric"), "Vista isométrica", False, True),
                    CommandSpec("Frontal", "vistas/frontal.svg", ("Std_ViewFront",), "Vista frontal", False, True),
                    CommandSpec("Superior", "vistas/superior.svg", ("Std_ViewTop",), "Vista superior", False, True),
                    CommandSpec("Derecha", "vistas/derecha.svg", ("Std_ViewRight",), "Vista derecha", False, True),
                    CommandSpec("Ajustar", "vistas/ajustar.svg", ("ViewFit",), "Ajustar a pantalla", False, True),
                )),
            )),
            ("Eje", (
                ("Eje paramétrico", (
                    CommandSpec("Crear eje", "eje_parametrico/crear_eje.svg", ("SFC_CreateShaft",), "Crear eje paramétrico", True, False, "shaft"),
                    CommandSpec("Editar eje", "eje_parametrico/editar_eje.svg", ("SFC_ShowShaftPanel",), "Editar eje", True, False, "shaft"),
                    CommandSpec("Agregar chavetero", "eje_parametrico/agregar_chavetero.svg", ("SFC_ShowShaftPanel",), "Editar chavetero", False, False, "shaft"),
                    CommandSpec("Configurar eje", "eje_parametrico/configurar_eje.svg", ("SFC_ShowShaftPanel",), "Configurar eje", False, False, "shaft"),
                )),
            )),
        )

    def _make_tab(self, groups: Iterable[tuple[str, Sequence[CommandSpec]]]):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(page)
        layout.setContentsMargins(5, 4, 5, 4)
        layout.setSpacing(3)
        for group_title, specs in groups:
            frame = QtWidgets.QFrame()
            frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            frame_layout = QtWidgets.QVBoxLayout(frame)
            frame_layout.setContentsMargins(4, 3, 4, 2)
            frame_layout.setSpacing(1)
            buttons_layout = QtWidgets.QHBoxLayout()
            buttons_layout.setSpacing(2)
            for spec in specs:
                buttons_layout.addWidget(self._button(spec))
            frame_layout.addLayout(buttons_layout, 1)
            caption = QtWidgets.QLabel(group_title)
            caption.setAlignment(QtCore.Qt.AlignCenter)
            caption.setStyleSheet("color: #53616a; font-size: 10px;")
            frame_layout.addWidget(caption)
            layout.addWidget(frame)
        layout.addStretch(1)
        return page

    def _button(self, spec: CommandSpec):
        button = QtWidgets.QToolButton()
        button.setText(spec.title)
        button.setIcon(_icon(spec.icon))
        button.setIconSize(QtCore.QSize(32 if spec.large else 22, 32 if spec.large else 22))
        button.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon if spec.large else QtCore.Qt.ToolButtonTextBesideIcon)
        button.setAutoRaise(True)
        button.setToolTip(spec.tooltip)
        button.setMinimumHeight(62 if spec.large else 30)
        if not spec.large:
            button.setMaximumWidth(145)
        available = bool(_first_available(spec.candidates))
        button.setEnabled(available and (not spec.requires_document or App.ActiveDocument is not None))
        button.clicked.connect(lambda _checked=False, s=spec: self.execute(s))
        return button

    def execute(self, spec: CommandSpec):
        if _run_candidates(spec.candidates) and spec.next_mode:
            manager = show_property_manager()
            manager.set_mode(spec.next_mode, spec.title)


class ClassicWorkspace:
    def __init__(self):
        ensure_icon_pack()
        self.main_window = Gui.getMainWindow()
        self.command_manager = None
        self.property_manager = None

    def show(self):
        self._apply_style()
        self.command_manager = self.main_window.findChild(QtWidgets.QDockWidget, _COMMAND_MANAGER_NAME)
        if self.command_manager is None:
            self.command_manager = CommandManager(self.main_window)
            self.main_window.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.command_manager)
        self.command_manager.show()

        self.property_manager = show_property_manager()
        self._tabify_with_combo_view(self.property_manager)
        self._hide_legacy_sfc_toolbars()
        return self

    def hide(self):
        if self.command_manager:
            self.command_manager.hide()
        if self.property_manager:
            self.property_manager.hide()

    def _tabify_with_combo_view(self, panel):
        combo = None
        for dock in self.main_window.findChildren(QtWidgets.QDockWidget):
            name = dock.objectName().lower()
            title = dock.windowTitle().lower()
            if name in ("combo view", "comboview") or "combo" in name or "vista combinada" in title:
                combo = dock
                break
        if combo is not None:
            combo.show()
            self.main_window.addDockWidget(QtCore.Qt.LeftDockWidgetArea, combo)
            self.main_window.addDockWidget(QtCore.Qt.LeftDockWidgetArea, panel)
            self.main_window.tabifyDockWidget(combo, panel)
            combo.raise_()
        else:
            self.main_window.addDockWidget(QtCore.Qt.LeftDockWidgetArea, panel)

    def _hide_legacy_sfc_toolbars(self):
        for toolbar in self.main_window.findChildren(QtWidgets.QToolBar):
            if toolbar.windowTitle() in {"Archivo", "Modelado mecánico", "Vista"}:
                toolbar.hide()

    def _apply_style(self):
        self.main_window.setStyleSheet(
            self.main_window.styleSheet()
            + """
            QDockWidget#SolidFreeCADClassicCommandManager { background: #e8ebed; }
            QTabWidget#SolidFreeCADCommandTabs::pane { border: 1px solid #9fa9b0; background: #edf0f2; }
            QTabWidget#SolidFreeCADCommandTabs QTabBar::tab { background: #d7dcdf; border: 1px solid #aeb6bc; padding: 4px 12px; }
            QTabWidget#SolidFreeCADCommandTabs QTabBar::tab:selected { background: #f4f5f6; border-bottom-color: #f4f5f6; }
            QDockWidget#SolidFreeCADClassicPropertyManager { background: #f1f2f3; }
            QWidget#SFCPropertyHeader { background: #d7dcdf; border-bottom: 1px solid #aeb6bc; }
            QToolButton#SFCAccept, QToolButton#SFCCancel { border: 0; padding: 2px; }
            QToolButton { padding: 2px 4px; }
            QToolButton:hover { background: #d6ebf7; border: 1px solid #7fb6d7; }
            QGroupBox { font-weight: 600; margin-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 7px; padding: 0 3px; }
            """
        )


def show_property_manager():
    global _property_manager
    main = Gui.getMainWindow()
    if _property_manager is None:
        _property_manager = main.findChild(QtWidgets.QDockWidget, _PROPERTY_MANAGER_NAME)
    if _property_manager is None:
        _property_manager = ClassicPropertyManager(main)
        main.addDockWidget(QtCore.Qt.LeftDockWidgetArea, _property_manager)
    _property_manager.show()
    return _property_manager


def show_workspace():
    global _workspace
    if _workspace is None:
        _workspace = ClassicWorkspace()
    return _workspace.show()


def hide_workspace():
    if _workspace is not None:
        _workspace.hide()
