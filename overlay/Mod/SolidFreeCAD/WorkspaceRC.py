"""SolidFreeCAD alpha.11 source release-candidate workspace.

Alpha.11 focuses on day-long usability and release readiness: persistent layout
profiles, quick access, command coverage, document diagnostics, safe rename,
visual density and theme adaptation. It remains source-only and builds on the
native-binding alpha.10 workspace.
"""
from __future__ import annotations

from dataclasses import dataclass

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from SolidFreeCAD.ClassicWorkspace import _first_available, _icon, _run_candidates
from SolidFreeCAD.FeatureBindingWorkspaceCompat import (
    hide_workspace as hide_alpha10_workspace,
    show_workspace as show_alpha10_workspace,
)
from SolidFreeCAD.InteractionWorkspace import _sketch_dof

_QUICK_ACCESS = "SolidFreeCADAlpha11QuickAccess"
_LAYOUT_COMBO = "SolidFreeCADAlpha11LayoutProfile"
_DENSITY_COMBO = "SolidFreeCADAlpha11Density"
_THEME_COMBO = "SolidFreeCADAlpha11Theme"
_VERIFICATION_PAGE = "SolidFreeCADAlpha11VerificationPage"
_VERIFICATION_TABS = "SolidFreeCADAlpha11VerificationTabs"
_DIAGNOSTICS = "SolidFreeCADAlpha11Diagnostics"
_COVERAGE = "SolidFreeCADAlpha11Coverage"
_RELEASE_LIST = "SolidFreeCADAlpha11ReleaseChecklist"
_STATUS = "SolidFreeCADAlpha11Status"
_TASK_TABS = "SolidFreeCADAlpha7TaskTabs"
_FEATURE_MANAGER = "SolidFreeCADFeatureManager"
_TASK_PANE = "SolidFreeCADAlpha7TaskPane"

_controller = None
_layout_controller = None
_verification = None
_shortcuts = []


@dataclass(frozen=True)
class CommandRequirement:
    group: str
    label: str
    candidates: tuple[str, ...]


_COMMAND_REQUIREMENTS = (
    CommandRequirement("Archivo", "Nuevo", ("SFC_CreatePart", "Std_New")),
    CommandRequirement("Archivo", "Abrir", ("SFC_Open", "Std_Open")),
    CommandRequirement("Archivo", "Guardar", ("SFC_Save", "Std_Save")),
    CommandRequirement("Historial", "Deshacer", ("Std_Undo",)),
    CommandRequirement("Historial", "Rehacer", ("Std_Redo",)),
    CommandRequirement("Croquis", "Nuevo croquis", ("SFC_NewSketch", "Sketcher_NewSketch")),
    CommandRequirement("Croquis", "Línea", ("Sketcher_CreatePolyline", "Sketcher_CreateLine")),
    CommandRequirement("Croquis", "Rectángulo", ("Sketcher_CreateRectangle",)),
    CommandRequirement("Croquis", "Círculo", ("Sketcher_CreateCircle",)),
    CommandRequirement("Croquis", "Cota", ("Sketcher_ConstrainDistance",)),
    CommandRequirement("Operaciones", "Saliente", ("SFC_Pad", "PartDesign_Pad")),
    CommandRequirement("Operaciones", "Corte", ("SFC_Pocket", "PartDesign_Pocket")),
    CommandRequirement("Operaciones", "Revolución", ("SFC_Revolution", "PartDesign_Revolution")),
    CommandRequirement("Operaciones", "Redondeo", ("SFC_Fillet", "PartDesign_Fillet")),
    CommandRequirement("Operaciones", "Chaflán", ("SFC_Chamfer", "PartDesign_Chamfer")),
    CommandRequirement("Vista", "Isométrica", ("SFC_FitAxonometric", "ViewAxonometric")),
    CommandRequirement("Vista", "Ajustar", ("ViewFit", "Std_ViewFitAll")),
    CommandRequirement("Evaluar", "Medir", ("Std_Measure", "Part_Measure_Menu")),
)

_RELEASE_CHECKS = (
    "Pieza, Body y croquis se crean sin cambiar de banco manualmente",
    "Croquis informa definido, subdefinido o conflicto",
    "Saliente y Corte conservan perfil y condición final",
    "Revolución conserva perfil y eje",
    "Redondeo y Chaflán conservan aristas",
    "Aceptar, cancelar, restaurar, Undo y Redo son coherentes",
    "Árbol, selección 3D y Body Tip permanecen sincronizados",
    "FCStd guarda, cierra y reabre sin pérdida",
    "STEP exporta e importa sin regresión BRep",
    "1366×768 y 1920×1080 mantienen controles accesibles",
    "Escalado 100%, 125%, 150% y 200% revisado físicamente",
    "Sesión prolongada sin paneles duplicados ni atajos capturados",
)


def _preferences():
    return App.ParamGet("User parameter:BaseApp/Preferences/SolidFreeCAD/WorkspaceRC")


def _selected_object():
    selected = Gui.Selection.getSelection()
    return selected[0] if selected else None


def _object_issues(obj) -> list[str]:
    issues: list[str] = []
    state = [str(value) for value in getattr(obj, "State", []) or []]
    for value in state:
        if any(token in value.lower() for token in ("error", "invalid", "touch")):
            issues.append(value)
    shape = getattr(obj, "Shape", None)
    try:
        if shape is not None and not shape.isNull() and not shape.isValid():
            issues.append("BRep inválido")
    except Exception:
        pass
    if "Sketcher::SketchObject" in getattr(obj, "TypeId", ""):
        dof = _sketch_dof(obj)
        if dof is not None and dof > 0:
            issues.append(f"Croquis con {dof} GDL")
    return list(dict.fromkeys(issues))


class QuickAccessController:
    def __init__(self, main, reset_callback):
        self.main = main
        toolbar = main.findChild(QtWidgets.QToolBar, _QUICK_ACCESS)
        if toolbar is None:
            toolbar = QtWidgets.QToolBar("Acceso rápido", main)
            toolbar.setObjectName(_QUICK_ACCESS)
            toolbar.setMovable(False)
            toolbar.setFloatable(False)
            commands = (
                ("Nuevo", "archivo/nuevo.svg", ("SFC_CreatePart", "Std_New")),
                ("Abrir", "archivo/abrir.svg", ("SFC_Open", "Std_Open")),
                ("Guardar", "archivo/guardar.svg", ("SFC_Save", "Std_Save")),
                ("Deshacer", "propertymanager/cancelar.svg", ("Std_Undo",)),
                ("Rehacer", "propertymanager/aceptar.svg", ("Std_Redo",)),
                ("Ajustar", "vistas/ajustar.svg", ("ViewFit", "Std_ViewFitAll")),
            )
            for label, icon, candidates in commands:
                action = toolbar.addAction(_icon(icon), label)
                action.setToolTip(label)
                action.setEnabled(_first_available(candidates) is not None)
                action.triggered.connect(lambda _checked=False, values=candidates: _run_candidates(values))
            toolbar.addSeparator()
            reset = toolbar.addAction("Restaurar espacio")
            reset.triggered.connect(reset_callback)
            main.addToolBar(QtCore.Qt.TopToolBarArea, toolbar)
        toolbar.show()
        self.toolbar = toolbar


class LayoutController(QtCore.QObject):
    PROFILES = ("Portátil", "Estándar", "Pantalla amplia")
    DENSITIES = ("Compacta", "Normal", "Cómoda")
    THEMES = ("Sistema", "Claro", "Oscuro")

    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.params = _preferences()
        self._updating = False
        self.toolbar = self._build_controls()
        self.restore()
        main.installEventFilter(self)

    def _build_controls(self):
        toolbar = self.main.findChild(QtWidgets.QToolBar, _QUICK_ACCESS)
        if toolbar is None:
            raise RuntimeError("Quick access toolbar must exist before layout controls")
        toolbar.addSeparator()
        toolbar.addWidget(QtWidgets.QLabel("Espacio"))
        self.profile = QtWidgets.QComboBox()
        self.profile.setObjectName(_LAYOUT_COMBO)
        self.profile.addItems(self.PROFILES)
        self.profile.currentTextChanged.connect(self.apply_profile)
        toolbar.addWidget(self.profile)

        toolbar.addWidget(QtWidgets.QLabel("Densidad"))
        self.density = QtWidgets.QComboBox()
        self.density.setObjectName(_DENSITY_COMBO)
        self.density.addItems(self.DENSITIES)
        self.density.currentTextChanged.connect(self.apply_density)
        toolbar.addWidget(self.density)

        toolbar.addWidget(QtWidgets.QLabel("Tema"))
        self.theme = QtWidgets.QComboBox()
        self.theme.setObjectName(_THEME_COMBO)
        self.theme.addItems(self.THEMES)
        self.theme.currentTextChanged.connect(self.apply_theme)
        toolbar.addWidget(self.theme)
        return toolbar

    def restore(self):
        self._updating = True
        profile = self.params.GetString("Profile", "Estándar")
        density = self.params.GetString("Density", "Normal")
        theme = self.params.GetString("Theme", "Sistema")
        self.profile.setCurrentText(profile if profile in self.PROFILES else "Estándar")
        self.density.setCurrentText(density if density in self.DENSITIES else "Normal")
        self.theme.setCurrentText(theme if theme in self.THEMES else "Sistema")
        self._updating = False
        self.apply_profile(self.profile.currentText())
        self.apply_density(self.density.currentText())
        self.apply_theme(self.theme.currentText())

    def reset(self):
        self._updating = True
        self.profile.setCurrentText("Estándar")
        self.density.setCurrentText("Normal")
        self.theme.setCurrentText("Sistema")
        self._updating = False
        self.apply_profile("Estándar")
        self.apply_density("Normal")
        self.apply_theme("Sistema")

    def apply_profile(self, profile):
        if not profile:
            return
        self.params.SetString("Profile", profile)
        manager = self.main.findChild(QtWidgets.QDockWidget, _FEATURE_MANAGER)
        task = self.main.findChild(QtWidgets.QDockWidget, _TASK_PANE)
        widths = {
            "Portátil": (255, 275),
            "Estándar": (300, 305),
            "Pantalla amplia": (335, 340),
        }.get(profile, (300, 305))
        for dock in (manager, task):
            if dock is not None:
                dock.show()
        try:
            self.main.resizeDocks(
                [dock for dock in (manager, task) if dock is not None],
                list(widths[: len([dock for dock in (manager, task) if dock is not None])]),
                QtCore.Qt.Horizontal,
            )
        except Exception:
            pass

    def apply_density(self, density):
        if not density:
            return
        self.params.SetString("Density", density)
        icon_size, property_value = {
            "Compacta": (18, "compact"),
            "Normal": (22, "normal"),
            "Cómoda": (28, "comfortable"),
        }.get(density, (22, "normal"))
        self.main.setProperty("sfcDensity", property_value)
        for toolbar in self.main.findChildren(QtWidgets.QToolBar):
            toolbar.setIconSize(QtCore.QSize(icon_size, icon_size))
        self._repolish(self.main)

    def apply_theme(self, theme):
        if not theme:
            return
        self.params.SetString("Theme", theme)
        value = {"Sistema": "system", "Claro": "light", "Oscuro": "dark"}.get(theme, "system")
        self.main.setProperty("sfcTheme", value)
        self._repolish(self.main)

    @staticmethod
    def _repolish(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def eventFilter(self, watched, event):
        if watched is self.main and event.type() == QtCore.QEvent.Resize:
            QtCore.QTimer.singleShot(0, self.adapt_to_width)
        return False

    def adapt_to_width(self):
        if self.main.width() < 1150 and self.profile.currentText() != "Portátil":
            self.profile.setCurrentText("Portátil")


class VerificationPage(QtWidgets.QWidget):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.setObjectName(_VERIFICATION_PAGE)
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setObjectName(_VERIFICATION_TABS)
        self.tabs.addTab(self._diagnostic_page(), "Diagnóstico")
        self.tabs.addTab(self._coverage_page(), "Comandos")
        self.tabs.addTab(self._release_page(), "Gate")
        root.addWidget(self.tabs)
        self.refresh_all()

    def _diagnostic_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        self.summary = QtWidgets.QLabel()
        self.summary.setObjectName("SFCAlpha11DiagnosticSummary")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.diagnostics = QtWidgets.QTreeWidget()
        self.diagnostics.setObjectName(_DIAGNOSTICS)
        self.diagnostics.setHeaderLabels(["Elemento", "Estado"])
        self.diagnostics.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.diagnostics, 1)
        row = QtWidgets.QHBoxLayout()
        refresh = QtWidgets.QPushButton("Actualizar")
        refresh.clicked.connect(self.refresh_diagnostics)
        row.addWidget(refresh)
        rename = QtWidgets.QPushButton("Renombrar selección")
        rename.clicked.connect(self.rename_selected)
        row.addWidget(rename)
        layout.addLayout(row)
        return page

    def _coverage_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        info = QtWidgets.QLabel(
            "Audita comandos registrados por el runtime. Una ausencia no se presenta como función terminada."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        self.coverage = QtWidgets.QTreeWidget()
        self.coverage.setObjectName(_COVERAGE)
        self.coverage.setHeaderLabels(["Comando", "Estado"])
        self.coverage.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.coverage, 1)
        refresh = QtWidgets.QPushButton("Revisar comandos")
        refresh.clicked.connect(self.refresh_coverage)
        layout.addWidget(refresh)
        return page

    def _release_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        note = QtWidgets.QLabel(
            "Lista de aceptación física. No se marca automáticamente porque requiere Windows real y archivos CAD."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.release = QtWidgets.QListWidget()
        self.release.setObjectName(_RELEASE_LIST)
        for text in _RELEASE_CHECKS:
            item = QtWidgets.QListWidgetItem(text)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.release.addItem(item)
        layout.addWidget(self.release, 1)
        clear = QtWidgets.QPushButton("Limpiar marcas")
        clear.clicked.connect(self.clear_release_checks)
        layout.addWidget(clear)
        return page

    def refresh_all(self):
        self.refresh_diagnostics()
        self.refresh_coverage()

    def refresh_diagnostics(self):
        self.diagnostics.clear()
        doc = App.ActiveDocument
        if doc is None:
            self.summary.setText("Sin documento activo.")
            return
        issues_total = 0
        root = QtWidgets.QTreeWidgetItem([doc.Label or doc.Name, "Documento"])
        self.diagnostics.addTopLevelItem(root)
        if not getattr(doc, "FileName", ""):
            root.addChild(QtWidgets.QTreeWidgetItem(["Archivo", "Sin guardar"]))
            issues_total += 1
        for obj in doc.Objects:
            issues = _object_issues(obj)
            if not issues:
                continue
            item = QtWidgets.QTreeWidgetItem([obj.Label or obj.Name, " | ".join(issues)])
            item.setData(0, QtCore.Qt.UserRole, obj.Name)
            item.setForeground(1, QtGui.QBrush(QtGui.QColor("#a34532")))
            root.addChild(item)
            issues_total += len(issues)
        if not root.childCount():
            root.addChild(QtWidgets.QTreeWidgetItem(["Modelo", "Sin advertencias detectadas"]))
        root.setExpanded(True)
        self.summary.setText(
            f"{issues_total} advertencia(s) detectada(s). Revise antes de guardar o exportar."
            if issues_total
            else "No se detectaron advertencias básicas en el documento activo."
        )
        self.summary.setProperty("state", "warning" if issues_total else "ok")
        self.summary.style().unpolish(self.summary)
        self.summary.style().polish(self.summary)

    def refresh_coverage(self):
        self.coverage.clear()
        groups: dict[str, QtWidgets.QTreeWidgetItem] = {}
        available = 0
        for requirement in _COMMAND_REQUIREMENTS:
            group = groups.get(requirement.group)
            if group is None:
                group = QtWidgets.QTreeWidgetItem([requirement.group, ""])
                groups[requirement.group] = group
                self.coverage.addTopLevelItem(group)
            command = _first_available(requirement.candidates)
            status = command or "No disponible"
            item = QtWidgets.QTreeWidgetItem([requirement.label, status])
            if command:
                item.setForeground(1, QtGui.QBrush(QtGui.QColor("#2d6f3d")))
                available += 1
            else:
                item.setForeground(1, QtGui.QBrush(QtGui.QColor("#9a4635")))
            group.addChild(item)
            group.setExpanded(True)
        self.coverage.setToolTip(f"{available}/{len(_COMMAND_REQUIREMENTS)} capacidades esenciales disponibles")

    def rename_selected(self):
        obj = _selected_object()
        doc = App.ActiveDocument
        if obj is None or doc is None:
            return
        value, accepted = QtWidgets.QInputDialog.getText(
            self, "Renombrar elemento", "Nombre visible", text=obj.Label or obj.Name
        )
        value = value.strip()
        if not accepted or not value or value == obj.Label:
            return
        try:
            doc.openTransaction("Renombrar elemento")
            obj.Label = value
            doc.recompute()
            doc.commitTransaction()
            self.refresh_diagnostics()
        except Exception as exc:
            try:
                doc.abortTransaction()
            except Exception:
                pass
            App.Console.PrintError(f"SolidFreeCAD alpha.11 rename: {exc}\n")

    def clear_release_checks(self):
        for index in range(self.release.count()):
            self.release.item(index).setCheckState(QtCore.Qt.Unchecked)


class Alpha11Controller(QtCore.QObject):
    def __init__(self, main, verification):
        super().__init__(main)
        self.main = main
        self.verification = verification
        self.signature = None
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(850)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh(force=True)

    def refresh(self, force=False):
        doc = App.ActiveDocument
        signature = None if doc is None else (
            doc.Name,
            len(doc.Objects),
            tuple((obj.Name, tuple(str(value) for value in getattr(obj, "State", []) or [])) for obj in doc.Objects),
        )
        if not force and signature == self.signature:
            return
        self.signature = signature
        self.verification.refresh_diagnostics()
        status = self.main.findChild(QtWidgets.QLabel, _STATUS)
        if status is None:
            status = QtWidgets.QLabel()
            status.setObjectName(_STATUS)
            self.main.statusBar().addPermanentWidget(status)
        issues = 0
        if doc is not None:
            issues = sum(len(_object_issues(obj)) for obj in doc.Objects)
        status.setText(
            f"SolidFreeCAD alpha.11 RC source · {issues} advertencia(s) · ejecutable bloqueado"
        )
        status.setProperty("state", "warning" if issues else "ok")
        status.style().unpolish(status)
        status.style().polish(status)
        status.show()


def _install_verification_page(main):
    tabs = main.findChild(QtWidgets.QTabWidget, _TASK_TABS)
    if tabs is None:
        return None
    existing = tabs.findChild(QtWidgets.QWidget, _VERIFICATION_PAGE)
    if existing is not None:
        return existing
    page = VerificationPage(main, tabs)
    tabs.addTab(page, "Verificación")
    return page


def _install_shortcuts(main, verification):
    global _shortcuts
    if _shortcuts:
        return
    diagnostics = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Shift+D"), main)
    diagnostics.activated.connect(lambda: verification.tabs.setCurrentIndex(0))
    save = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), main)
    save.setContext(QtCore.Qt.ApplicationShortcut)
    save.activated.connect(lambda: _run_candidates(("SFC_Save", "Std_Save")))
    _shortcuts = [diagnostics, save]


def _apply_style(main):
    marker = "/* SolidFreeCAD alpha11 workspace RC */"
    if marker in main.styleSheet():
        return
    main.setStyleSheet(main.styleSheet() + marker + """
        QToolBar#SolidFreeCADAlpha11QuickAccess {
            background: #e9eef1; border-bottom: 1px solid #9eabb4; spacing: 3px; padding: 2px 4px;
        }
        QComboBox#SolidFreeCADAlpha11LayoutProfile,
        QComboBox#SolidFreeCADAlpha11Density,
        QComboBox#SolidFreeCADAlpha11Theme {
            min-width: 92px; background: #ffffff; border: 1px solid #9eabb4; padding: 2px 5px;
        }
        QWidget#SolidFreeCADAlpha11VerificationPage { background: #f5f7f8; }
        QTabWidget#SolidFreeCADAlpha11VerificationTabs::pane { border: 1px solid #b2bdc4; }
        QTreeWidget#SolidFreeCADAlpha11Diagnostics,
        QTreeWidget#SolidFreeCADAlpha11Coverage,
        QListWidget#SolidFreeCADAlpha11ReleaseChecklist { background: #ffffff; border: 1px solid #bec8ce; }
        QLabel#SFCAlpha11DiagnosticSummary[state="ok"] { background: #dff1e4; color: #245f35; padding: 6px; }
        QLabel#SFCAlpha11DiagnosticSummary[state="warning"] { background: #fff0cb; color: #76561e; padding: 6px; }
        QMainWindow[sfcDensity="compact"] QPushButton { min-height: 22px; padding: 2px 5px; }
        QMainWindow[sfcDensity="normal"] QPushButton { min-height: 26px; padding: 3px 7px; }
        QMainWindow[sfcDensity="comfortable"] QPushButton { min-height: 32px; padding: 5px 9px; }
        QMainWindow[sfcTheme="dark"] QDockWidget,
        QMainWindow[sfcTheme="dark"] QTabWidget,
        QMainWindow[sfcTheme="dark"] QWidget#SolidFreeCADAlpha11VerificationPage {
            background: #30363b; color: #e5e9ec;
        }
        QMainWindow[sfcTheme="dark"] QTreeWidget,
        QMainWindow[sfcTheme="dark"] QListWidget,
        QMainWindow[sfcTheme="dark"] QLineEdit,
        QMainWindow[sfcTheme="dark"] QComboBox,
        QMainWindow[sfcTheme="dark"] QSpinBox,
        QMainWindow[sfcTheme="dark"] QDoubleSpinBox {
            background: #24292d; color: #edf0f2; border: 1px solid #65727a;
        }
        QStatusBar QLabel#SolidFreeCADAlpha11Status[state="ok"] { color: #2d6f3d; font-weight: 700; }
        QStatusBar QLabel#SolidFreeCADAlpha11Status[state="warning"] { color: #91502c; font-weight: 700; }
    """)


def show_workspace():
    global _controller, _layout_controller, _verification
    result = show_alpha10_workspace()
    main = Gui.getMainWindow()
    _apply_style(main)

    quick = main.findChild(QtWidgets.QToolBar, _QUICK_ACCESS)
    if quick is None:
        placeholder = lambda: _layout_controller.reset() if _layout_controller is not None else None
        QuickAccessController(main, placeholder)
    else:
        quick.show()

    if _layout_controller is None:
        _layout_controller = LayoutController(main)
    else:
        _layout_controller.toolbar.show()
        _layout_controller.restore()

    _verification = _install_verification_page(main)
    if _verification is not None:
        _verification.refresh_all()
        _install_shortcuts(main, _verification)
        if _controller is None:
            _controller = Alpha11Controller(main, _verification)
        else:
            _controller.timer.start()
            _controller.refresh(force=True)

    main.setWindowTitle("SolidFreeCAD Desktop alpha.11 · Source Release Candidate")
    return result


def hide_workspace():
    hide_alpha10_workspace()
    main = Gui.getMainWindow()
    if _controller is not None:
        _controller.timer.stop()
    for name, kind in ((_QUICK_ACCESS, QtWidgets.QToolBar), (_STATUS, QtWidgets.QLabel)):
        widget = main.findChild(kind, name)
        if widget is not None:
            widget.hide()
