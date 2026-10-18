"""SolidFreeCAD's independent mechanical-CAD window and command lifecycle."""
from __future__ import annotations

import math
import unicodedata

import FreeCAD as App
import FreeCADGui as Gui
from .qt import QtCore, QtGui, QtWidgets, Action, Shortcut
from .icons import icon
from . import backend
from .widgets import Ribbon, CommandButton
from .manager import ManagerDock
from .sketch_interaction import SketchInteractionController

VERSION = "0.1.0-alpha.13"
_window = None


def _plain(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold()) if not unicodedata.combining(c))


class SolidFreeCADWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("SolidFreeCADStandaloneWindow")
        self.host = Gui.getMainWindow()
        self.session = None
        self._closed = False
        self._signature = None
        self.sketch_interaction = SketchInteractionController(self)
        self.settings = QtCore.QSettings("SolidFreeCAD", "Desktop")
        self.resize(1440, 900)
        self.setMinimumSize(1000, 650)
        self._build_actions()
        self.setMenuWidget(self._header())
        self._host_state = [(widget, widget.isVisible()) for widget in [self.host.menuBar(), self.host.statusBar()] + self.host.findChildren(QtWidgets.QToolBar) + self.host.findChildren(QtWidgets.QDockWidget)]
        for widget, visible in self._host_state:
            widget.hide()
        self._host_central = self.host.takeCentralWidget()
        if self._host_central is None:
            raise RuntimeError("FreeCAD no expuso un visor de documentos para integrar.")
        self.setCentralWidget(self._host_central)
        self.command_toolbar = QtWidgets.QToolBar("CommandManager", self)
        self.command_toolbar.setObjectName("CommandManager")
        self.command_toolbar.setMovable(False)
        self.command_toolbar.setFloatable(False)
        self.ribbon = Ribbon(self)
        self.ribbon.setFixedHeight(114)
        self.command_toolbar.addWidget(self.ribbon)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.command_toolbar)
        self.manager = ManagerDock(self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.manager)
        self.resizeDocks([self.manager], [270], QtCore.Qt.Horizontal)
        self.view_toolbar = QtWidgets.QToolBar("Vista", self)
        self.view_toolbar.setObjectName("ViewToolbar")
        self.view_toolbar.setMovable(False)
        self.view_toolbar.setIconSize(QtCore.QSize(22, 22))
        for key in ("iso", "front", "top", "right", "fit", "shaded", "wireframe"):
            self.view_toolbar.addAction(self.actions[key])
        self.addToolBar(QtCore.Qt.RightToolBarArea, self.view_toolbar)
        self.state = QtWidgets.QLabel("Listo · cree una pieza o abra un archivo")
        self.statusBar().addWidget(self.state, 1)
        self.statusBar().addPermanentWidget(QtWidgets.QLabel("MMGS  ·  FreeCAD 1.1.1"))
        self.preview_timer = QtCore.QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(180)
        self.preview_timer.timeout.connect(self.preview_feature)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(350)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self._apply_style()
        preferences = App.ParamGet("User parameter:BaseApp/Preferences/View")
        self._missing_view_preferences = {
            name for name in ("BackgroundColor", "BackgroundColor2", "SelectionColor", "Simple", "UseBackgroundColorMid")
            if name not in {entry[1] for entry in preferences.GetContents()}
        }
        self._view_preferences = {
            name: preferences.GetUnsigned(name) for name in (
                "BackgroundColor", "BackgroundColor2", "SelectionColor"
            )
        }
        self._view_flags = {
            name: preferences.GetBool(name) for name in ("Simple", "UseBackgroundColorMid")
        }
        backend.set_light_background()
        geometry = self.settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        self.refresh(True)

    def _build_actions(self):
        commands = [
            ("new", "Nueva pieza", self.new_part, "new", "Ctrl+N", "Crear un documento y un cuerpo Part Design"),
            ("open", "Abrir", self.open_document, "open", "Ctrl+O", "Abrir FCStd o importar STEP"),
            ("save", "Guardar", self.save_document, "save", "Ctrl+S", "Guardar el documento nativo FCStd"),
            ("save_as", "Guardar como", self.save_as, "save", "Ctrl+Shift+S", "Guardar una copia FCStd con otro nombre"),
            ("export", "Exportar STEP", self.export_step, "export", "", "Exportar los sólidos del documento a STEP"),
            ("undo", "Deshacer", self.undo, "undo", "Ctrl+Z", "Deshacer la última operación confirmada"),
            ("redo", "Rehacer", self.redo, "redo", "Ctrl+Y", "Rehacer una operación deshecha"),
            ("sketch", "Nuevo croquis", self.new_sketch, "sketch", "", "Dibujar en XY, XZ, YZ o sobre una cara plana seleccionada"),
            ("pad", "Saliente/Base", lambda: self.begin_feature("pad"), "pad", "", "Extrusión paramétrica desde un croquis cerrado"),
            ("pocket", "Corte extruido", lambda: self.begin_feature("pocket"), "pocket", "", "Cortar con profundidad definida o por todo"),
            ("revolution", "Revolución", lambda: self.begin_feature("revolution"), "revolution", "", "Girar un perfil alrededor de su eje horizontal o vertical"),
            ("fillet", "Redondeo", lambda: self.begin_feature("fillet"), "fillet", "", "Seleccione aristas con Ctrl + clic para aplicar un radio"),
            ("chamfer", "Chaflán", lambda: self.begin_feature("chamfer"), "chamfer", "", "Seleccione aristas y defina la distancia del chaflán"),
            ("linear_pattern", "Patrón lineal", lambda: self.begin_feature("linear_pattern"), "linear_pattern", "", "Repetir un Saliente, Corte o Revolución con separación constante"),
            ("polar_pattern", "Patrón circular", lambda: self.begin_feature("polar_pattern"), "polar_pattern", "", "Repetir una operación alrededor de un eje del cuerpo"),
            ("edit", "Editar operación", self.edit_selected, "edit", "", "Editar los parámetros nativos del elemento seleccionado"),
            ("rename", "Cambiar nombre", self.rename_selected, "edit", "F2", "Cambiar el nombre del elemento seleccionado"),
            ("delete", "Eliminar", self.delete_selected, "cancel", "Delete", "Eliminar un elemento sin dependencias posteriores"),
            ("visibility", "Mostrar/ocultar", self.toggle_visibility, "eye", "Space", "Mostrar u ocultar el elemento seleccionado"),
            ("line", "Línea", lambda: self.start_tool("line"), "line", "", "Dos clics · ajuste a extremos, origen, horizontal y vertical"),
            ("polyline", "Polilínea", lambda: self.start_tool("polyline"), "polyline", "", "Clics sucesivos · vuelva al inicio para cerrar · Enter termina"),
            ("arc", "Arco de 3 puntos", lambda: self.start_tool("arc"), "arc", "", "Seleccione inicio, punto intermedio y final del arco"),
            ("slot", "Ranura recta", self.add_slot, "slot", "", "Crear una ranura con longitud total y ancho editables en Propiedades"),
            ("trim", "Recortar", lambda: self.start_tool("trim"), "trim", "", "Seleccione un tramo del croquis para recortar entre intersecciones"),
            ("rectangle", "Rectángulo", lambda: self.start_tool("rectangle"), "rectangle", "", "Dos esquinas opuestas con vista preliminar"),
            ("circle", "Círculo", lambda: self.start_tool("circle"), "circle", "", "Centro y punto de radio con vista preliminar"),
            ("rectangle_numeric", "Rectángulo", self.add_rectangle, "rectangle", "", "Crear un rectángulo con cotas de ancho y alto"),
            ("circle_numeric", "Círculo", self.add_circle, "circle", "", "Crear un círculo acotado por radio"),
            ("dimension", "Cota inteligente", self.show_dimensions, "dimension", "", "Añadir o editar una longitud, radio o relación geométrica"),
            ("accept", "Aceptar", self.accept_manager_operation, "check", "", "Confirmar la operación y conservar los cambios"),
            ("cancel", "Cancelar", self.cancel_manager_operation, "cancel", "", "Revertir la operación actual"),
            ("measure", "Medir", self.measure, "measure", "", "Consultar longitud, área, volumen o distancia entre dos vértices"),
            ("validate", "Comprobar sólido", self.validate_solid, "check", "", "Comprobar la validez BRep del elemento seleccionado"),
            ("iso", "Isométrica", backend.axonometric_view, "iso", "Ctrl+7", "Orientación isométrica"),
            ("front", "Frontal", backend.front_view, "front", "Ctrl+1", "Vista frontal"),
            ("top", "Superior", backend.top_view, "plane", "Ctrl+5", "Vista superior"),
            ("right", "Derecha", lambda: backend._view().viewRight(), "front", "Ctrl+3", "Vista lateral derecha"),
            ("fit", "Ajustar vista", backend.fit_view, "fit", "F", "Ajustar la geometría visible al visor"),
            ("shaded", "Sombreado con aristas", lambda: self.draw_style("Flat Lines"), "body", "", "Sombreado sólido con aristas visibles"),
            ("wireframe", "Alámbrico", lambda: self.draw_style("Wireframe"), "body", "", "Mostrar solo las aristas del modelo"),
        ]
        self.actions = {}
        for key, text, callback, symbol, shortcut, tip in commands:
            action = Action(icon(symbol), text, self)
            action.setObjectName("command_" + key)
            action.setToolTip(tip + (" · " + shortcut if shortcut else ""))
            if shortcut:
                action.setShortcut(QtGui.QKeySequence(shortcut))
            action.triggered.connect(lambda checked=False, fn=callback: self._run(fn))
            self.addAction(action)
            self.actions[key] = action
        self.escape = Shortcut(QtGui.QKeySequence("Esc"), self)
        self.escape.activated.connect(self.escape_operation)
        self.search_shortcut = Shortcut(QtGui.QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(lambda: self.search.setFocus())

    def _header(self):
        header = QtWidgets.QWidget()
        header.setObjectName("AppHeader")
        row = QtWidgets.QHBoxLayout(header)
        row.setContentsMargins(10, 3, 8, 3)
        row.setSpacing(4)
        brand = QtWidgets.QLabel("SolidFreeCAD")
        brand.setObjectName("Brand")
        row.addWidget(brand)
        for text, keys in [("Archivo", ("new", "open", "save", "save_as", "export")), ("Edición", ("undo", "redo", "edit", "rename", "delete")), ("Ver", ("iso", "front", "top", "right", "fit", "shaded", "wireframe")), ("Insertar", ("sketch", "pad", "pocket", "revolution", "fillet", "chamfer", "linear_pattern", "polar_pattern"))]:
            button = QtWidgets.QToolButton()
            button.setText(text)
            button.setAutoRaise(True)
            menu = QtWidgets.QMenu(button)
            for key in keys:
                menu.addAction(self.actions[key])
            button.setMenu(menu)
            button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
            row.addWidget(button)
        for key in ("new", "open", "save", "undo", "redo"):
            button = CommandButton(self.actions[key], parent=header)
            button.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
            button.setMinimumWidth(26)
            button.setFixedHeight(28)
            row.addWidget(button)
        row.addStretch(1)
        self.document_title = QtWidgets.QLabel("Sin documento")
        self.document_title.setObjectName("DocumentTitle")
        row.addWidget(self.document_title)
        row.addStretch(1)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Buscar comandos  ·  Ctrl+F")
        self.search.setClearButtonEnabled(True)
        self.search.setMaximumWidth(245)
        labels = list(dict.fromkeys(action.text() for action in self.actions.values()))
        completer = QtWidgets.QCompleter(labels, self.search)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer.setFilterMode(QtCore.Qt.MatchContains)
        self.search.setCompleter(completer)
        self.search.returnPressed.connect(self.run_search)
        row.addWidget(self.search)
        return header

    def _run(self, callback):
        try:
            callback()
        except Exception as exc:
            self.state.setText(str(exc))
            QtWidgets.QMessageBox.warning(self, "SolidFreeCAD", str(exc))
        self.refresh(True)

    def run_search(self):
        query = _plain(self.search.text().strip())
        if not query:
            return
        matches = [a for a in self.actions.values() if a.isEnabled() and query in _plain(a.text())]
        exact = [a for a in matches if _plain(a.text()) == query]
        if exact or len(matches) == 1:
            (exact or matches)[0].trigger()
            self.search.clear()
        else:
            self.state.setText("Elija un comando de la lista." if matches else "No hay comandos disponibles con ese nombre.")

    def refresh(self, force=False):
        if self._closed:
            return
        doc = backend.active_document()
        if self.session is not None and (doc is None or self.session.document_name != doc.Name):
            self.cancel_manager_operation()
        signature = None if doc is None else (doc.Name, tuple((o.Name, o.Label, bool(getattr(o, "Visibility", False))) for o in doc.Objects))
        if force or signature != self._signature:
            self._signature = signature
            self.manager.rebuild_tree()
        self.manager.tree.sync_selection()
        label = doc.Label if doc is not None else "Sin documento"
        self.document_title.setText(label)
        self.setWindowTitle(f"{label} — SolidFreeCAD {VERSION}")
        active = self.session is not None
        sketch = isinstance(self.session, backend.SketchSession)
        for bar in self.centralWidget().findChildren(QtWidgets.QTabBar):
            bar.setEnabled(not active)
        selected = backend.selected_object() is not None
        for key in ("save", "save_as", "export", "undo", "redo"):
            self.actions[key].setEnabled(doc is not None and not active)
        if doc is not None and not active:
            self.actions["undo"].setEnabled(doc.UndoCount > 0)
            self.actions["redo"].setEnabled(doc.RedoCount > 0)
        for key in ("pad", "pocket", "revolution", "fillet", "chamfer", "sketch", "linear_pattern", "polar_pattern"):
            self.actions[key].setEnabled(not active)
        for key in ("line", "polyline", "arc", "slot", "trim", "rectangle", "circle", "rectangle_numeric", "circle_numeric", "dimension"):
            self.actions[key].setEnabled(sketch)
        for key in ("edit", "rename", "delete", "visibility"):
            self.actions[key].setEnabled(selected and not active)
        for key in ("accept", "cancel"):
            self.actions[key].setEnabled(active)
        for key in ("measure", "validate", "iso", "front", "top", "right", "fit", "shaded", "wireframe"):
            self.actions[key].setEnabled(doc is not None)
        self.actions["new"].setEnabled(not active)
        self.actions["open"].setEnabled(not active)

    def new_part(self):
        if self.session is not None:
            raise ValueError("Acepte o cancele la operación actual.")
        backend.new_part()
        self.manager.show_model()
        self.state.setText("Pieza nueva · cree un croquis para comenzar")

    def new_sketch(self, plane=None):
        if self.session is not None:
            raise ValueError("Acepte o cancele la operación actual.")
        face = backend.selected_planar_face() if plane is None else None
        if plane is None and face is None:
            label, ok = QtWidgets.QInputDialog.getItem(self, "Nuevo croquis", "Plano de referencia", ["Planta (XY)", "Alzado (XZ)", "Lateral (YZ)"], 0, False)
            if not ok:
                return
            plane = {"Planta (XY)": "XY", "Alzado (XZ)": "XZ", "Lateral (YZ)": "YZ"}[label]
        self.session = backend.SketchSession(plane=plane or "XY", face=face)
        self.manager.begin_sketch(self.session.sketch)
        self.ribbon.setCurrentIndex(1)
        self.state.setText("Editando croquis · seleccione una entidad del CommandManager")

    def start_tool(self, tool):
        self.sketch_interaction.start(tool)

    def start_rectangle_tool(self):
        self.start_tool("rectangle")

    def start_circle_tool(self):
        self.start_tool("circle")

    def add_rectangle(self):
        self.sketch_interaction.cancel(silent=True)
        backend.add_rectangle(self.manager.width.value(), self.manager.height.value())
        self.manager.refresh_sketch()
        self.state.setText("Rectángulo creado con cotas editables")

    def add_circle(self):
        self.sketch_interaction.cancel(silent=True)
        backend.add_circle(self.manager.radius.value())
        self.manager.refresh_sketch()
        self.state.setText("Círculo creado con radio editable")

    def add_slot(self):
        self.sketch_interaction.cancel(silent=True)
        backend.add_slot(self.manager.slot_length.value(), self.manager.slot_width.value())
        self.manager.refresh_sketch()
        self.state.setText("Ranura creada · radio y tramo recto editables en Cotas y relaciones")

    def show_dimensions(self):
        self.manager.modes.setCurrentIndex(1)
        self.manager.dimension_section.header.setChecked(True)
        self.manager.geometry.setFocus()
        self.state.setText("Seleccione la entidad y aplique una cota o relación")

    def apply_dimension(self):
        def apply():
            if not isinstance(self.session, backend.SketchSession) or self.manager.geometry.currentData() is None:
                raise ValueError("Seleccione una entidad del croquis.")
            self.sketch_interaction.cancel(silent=True)
            kind = self.manager.constraint.currentData()
            if kind in ("Tangent", "Concentric", "Parallel", "Perpendicular", "Equal"):
                backend.constrain_pair(self.session.sketch, self.manager.geometry.currentData(), self.manager.geometry2.currentData(), kind)
            else:
                backend.constrain_geometry(self.session.sketch, self.manager.geometry.currentData(), kind, self.manager.dimension_value.value())
            self.manager.refresh_sketch()
            self.state.setText("Cota / relación aplicada")
        self._run(apply)

    def begin_feature(self, kind, feature=None):
        if self.session is not None:
            raise ValueError("Acepte o cancele la operación actual.")
        edges = backend.selected_edges() if feature is None and kind in ("fillet", "chamfer") else None
        source = backend.selected_pattern_source() if feature is None and kind in backend.PATTERNS else None
        profile = backend.active_sketch() if feature is None and edges is None and source is None else None
        self.session = backend.FeatureSession(kind, profile=profile, edge_selection=edges, feature=feature, pattern_source=source)
        self.manager.begin_feature(self.session)
        self.ribbon.setCurrentIndex(0)
        backend.axonometric_view()
        self.preview_feature()

    def schedule_preview(self):
        self.manager.accept.setEnabled(False)
        self.preview_timer.start()

    def preview_feature(self):
        if not isinstance(self.session, backend.FeatureSession):
            return
        valid = self.session.update(**self.manager.feature_values())
        self.manager.accept.setEnabled(valid)
        if valid:
            self.manager.message.setText("Vista preliminar válida. Confirme para conservar la operación.")
            self.state.setText("Definiendo " + backend.FEATURES[self.session.kind][2])
        else:
            self.manager.message.setText(self.session.error)
            self.state.setText("Revise los parámetros de la operación")
        self.refresh()

    def accept_manager_operation(self):
        if self.session is None:
            return
        self.sketch_interaction.cancel(silent=True)
        self.preview_timer.stop()
        if isinstance(self.session, backend.FeatureSession):
            self.preview_feature()
        obj = self.session.accept()
        self.session = None
        self.manager.show_model()
        self.ribbon.setCurrentIndex(0)
        backend.select_object(obj.Name)
        self.state.setText(obj.Label + " confirmado")
        self.refresh(True)

    def cancel_manager_operation(self):
        self.preview_timer.stop()
        self.sketch_interaction.cancel(silent=True)
        if self.session is not None:
            self.session.cancel()
            self.session = None
        self.manager.show_model()
        self.ribbon.setCurrentIndex(0)
        self.state.setText("Operación cancelada · cambios revertidos")
        self.refresh(True)

    def escape_operation(self):
        if self.sketch_interaction.active:
            self.sketch_interaction.cancel()
        elif self.session is not None:
            self.cancel_manager_operation()

    def on_sketch_tool_state(self, tool, message):
        self.manager.message.setText(message)
        self.state.setText(message)

    def on_sketch_tool_first_point(self, tool, point):
        self.state.setText(f"X={point[0]:.3f}  Y={point[1]:.3f} mm · seleccione el segundo punto")

    def on_sketch_pointer(self, tool, first, point):
        if first is not None:
            dx, dy = point[0] - first[0], point[1] - first[1]
            if tool == "rectangle":
                detail = f"Ancho {abs(dx):.3f} · Alto {abs(dy):.3f} mm"
            elif tool == "circle":
                detail = f"Radio {math.hypot(dx, dy):.3f} mm"
            elif tool == "arc":
                detail = "Arco · seleccione el punto final" if self.sketch_interaction.middle_point is not None else "Arco · seleccione el punto intermedio"
            else:
                detail = f"Longitud {math.hypot(dx, dy):.3f} mm"
            self.state.setText(detail + " · clic para confirmar · Esc para cancelar")
        else:
            self.state.setText(f"X={point[0]:.3f} · Y={point[1]:.3f} mm")

    def on_sketch_tool_completed(self, tool):
        self.manager.refresh_sketch()
        if self.sketch_interaction.active and tool == "polyline":
            self.manager.message.setText("Continúe con otro punto; vuelva al inicio para cerrar o pulse Enter.")
        elif tool == "trim":
            self.manager.message.setText("Tramo recortado. Seleccione otro tramo o pulse Esc.")
        else:
            self.manager.message.setText("Entidad creada. Continúe dibujando o acepte el croquis.")
        self.refresh(True)

    def on_sketch_tool_cancelled(self):
        self.manager.message.setText("Herramienta cancelada. El croquis sigue activo.")
        self.state.setText("Seleccione otra entidad o acepte el croquis")

    def on_tree_selection(self, name):
        if self.session is None:
            backend.select_object(name)
            if self.manager.stack.currentIndex() == 1:
                self.manager.show_object(backend.object_by_name(name))

    def edit_selected(self):
        obj = backend.selected_object()
        if obj is not None:
            self.edit_object(obj.Name)

    def edit_object(self, name):
        obj = backend.object_by_name(name)
        if obj is None or self.session is not None:
            return
        if obj.TypeId == "Sketcher::SketchObject":
            self.session = backend.SketchSession(sketch=obj)
            self.manager.begin_sketch(obj)
            self.ribbon.setCurrentIndex(1)
        else:
            kind = next((k for k, spec in backend.FEATURES.items() if spec[0] == obj.TypeId), None)
            if kind:
                self.begin_feature(kind, feature=obj)
            else:
                self.manager.show_object(obj)
        self.refresh()

    def rename_selected(self):
        obj = backend.selected_object()
        if obj is not None:
            label, ok = QtWidgets.QInputDialog.getText(self, "Cambiar nombre", "Nombre", text=obj.Label)
            if ok and label.strip():
                backend.set_object_label(obj.Name, label.strip())

    def delete_selected(self):
        obj = backend.selected_object()
        if obj is not None:
            backend.remove_object(obj.Name)

    def toggle_visibility(self):
        obj = backend.selected_object()
        if obj is not None:
            backend.set_object_visibility(obj.Name, not obj.Visibility)

    def undo(self):
        if self.session is None and backend.active_document() is not None:
            Gui.Selection.clearSelection()
            backend.active_document().undo()
            backend.active_document().recompute()

    def redo(self):
        if self.session is None and backend.active_document() is not None:
            backend.active_document().redo()
            backend.active_document().recompute()

    def open_document(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Abrir documento", "", "CAD (*.FCStd *.fcstd *.step *.stp);;Todos los archivos (*)")
        if path:
            backend.open_document(path)
            self.manager.show_model()

    def _save(self, copy=False):
        doc = backend.active_document()
        if doc is None:
            return
        path = None
        if copy or not doc.FileName:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar documento", doc.FileName or doc.Label + ".FCStd", "FreeCAD (*.FCStd)")
            if not path:
                return
            if not path.lower().endswith(".fcstd"):
                path += ".FCStd"
        backend.save_document(path)
        self.state.setText("Documento guardado")

    def save_document(self):
        self._save()

    def save_as(self):
        self._save(copy=True)

    def export_step(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Exportar sólidos", "Pieza.step", "STEP (*.step *.stp)")
        if path:
            if not path.lower().endswith((".step", ".stp")):
                path += ".step"
            backend.export_step(path)
            self.state.setText("Sólidos exportados a STEP")

    def draw_style(self, style):
        for obj in backend.active_document().Objects:
            if hasattr(obj.ViewObject, "DisplayMode") and style in obj.ViewObject.listDisplayModes():
                obj.ViewObject.DisplayMode = style

    def measure(self):
        selected = Gui.Selection.getSelectionEx()
        if not selected:
            raise ValueError("Seleccione una arista, cara, sólido o dos vértices.")
        vertices = [sub for entry in selected for sub in entry.SubObjects if sub.ShapeType == "Vertex"]
        if len(vertices) == 2:
            result = f"Distancia: {(vertices[1].Point - vertices[0].Point).Length:.4f} mm"
        else:
            shapes = [sub for entry in selected for sub in entry.SubObjects] or [selected[0].Object.Shape]
            shape = shapes[0]
            result = f"Longitud: {shape.Length:.4f} mm\nÁrea: {shape.Area:.4f} mm²\nVolumen: {shape.Volume:.4f} mm³"
        QtWidgets.QMessageBox.information(self, "Medir", result)

    def validate_solid(self):
        obj = backend.selected_object()
        if obj is None or not hasattr(obj, "Shape"):
            raise ValueError("Seleccione un sólido del árbol o del visor.")
        shape = obj.Shape
        valid = not shape.isNull() and shape.isValid()
        QtWidgets.QMessageBox.information(self, "Comprobar geometría", f"{obj.Label}\nBRep: {'válido' if valid else 'inválido'}\nSólidos: {len(shape.Solids)}\nVolumen: {shape.Volume:.4f} mm³")

    def _apply_style(self):
        self.setStyleSheet('''
            QMainWindow { background: #edf0f4; }
            QWidget { font-family: "Segoe UI", "DejaVu Sans", sans-serif; font-size: 11px; color: #28343e; }
            QWidget#AppHeader { background: #f9fafc; border-bottom: 1px solid #b5bec7; }
            QLabel#Brand { color: #b12b3c; font-size: 17px; font-weight: 700; font-style: italic; padding-right: 15px; }
            QLabel#DocumentTitle { color: #546475; }
            QToolButton { border: 1px solid transparent; border-radius: 3px; padding: 3px; }
            QToolButton:hover { background: #e5f0f9; border-color: #9bbbd3; }
            QToolButton:pressed { background: #c8deef; }
            QToolButton:disabled { color: #929ca6; }
            QToolBar#CommandManager { background: #f8f9fb; border: 0; border-bottom: 1px solid #b8c2cb; spacing: 0; }
            QTabWidget#SFC12Ribbon::pane { background: #f8f9fb; border: 0; }
            QTabWidget#SFC12Ribbon QScrollArea, QTabWidget#SFC12Ribbon QScrollArea > QWidget > QWidget { background: #f8f9fb; }
            QTabBar::tab { background: #e9edf1; padding: 5px 14px; border: 1px solid #c4ccd4; }
            QTabBar::tab:selected { background: #fff; border-top: 2px solid #4383b3; }
            QFrame#RibbonGroup { border-right: 1px solid #cdd4db; }
            QLabel#GroupCaption { color: #667481; font-size: 10px; padding: 2px; }
            QToolBar#ViewToolbar { background: #f8f9fb; border-left: 1px solid #b8c2cb; spacing: 4px; }
            QDockWidget#ManagerDock { background: white; border-right: 1px solid #aebbc5; }
            QTreeWidget#FeatureTree { background: white; border: 0; }
            QTreeWidget#FeatureTree::item { height: 25px; }
            QTreeWidget#FeatureTree::item:selected { background: #d8eafa; color: #183e5b; }
            QLineEdit, QDoubleSpinBox, QComboBox { background: white; border: 1px solid #bac5ce; border-radius: 2px; padding: 4px; min-height: 19px; }
            QLineEdit:focus, QDoubleSpinBox:focus { border-color: #4286b8; }
            QWidget#PropertyHeader { background: #edf2f6; border-bottom: 1px solid #bcc7d0; }
            QLabel#PropertyMessage { background: #f0f6fb; border: 1px solid #c3d7e6; padding: 7px; color: #35556e; }
            QToolButton#SectionHeader { background: #e9eef3; text-align: left; padding: 5px; font-weight: 600; border-radius: 0; border-top: 1px solid #c6d0d8; }
            QPushButton { background: #f0f4f7; border: 1px solid #bbc8d2; border-radius: 3px; padding: 6px; }
            QPushButton:hover { background: #e0eef9; }
            QScrollArea { background: white; }
            QStatusBar { background: #f8fafc; border-top: 1px solid #bac5ce; }
        ''')

    def closeEvent(self, event):
        if self.session is not None:
            self.cancel_manager_operation()
        self._closed = True
        self.timer.stop()
        self.preview_timer.stop()
        self.settings.setValue("geometry", self.saveGeometry())
        central = self.takeCentralWidget()
        if central is not None:
            self.host.setCentralWidget(central)
        for widget, visible in self._host_state:
            widget.setVisible(visible)
        preferences = App.ParamGet("User parameter:BaseApp/Preferences/View")
        for name, value in self._view_preferences.items():
            if name in self._missing_view_preferences:
                preferences.RemUnsigned(name)
            else:
                preferences.SetUnsigned(name, value)
        for name, value in self._view_flags.items():
            if name in self._missing_view_preferences:
                preferences.RemBool(name)
            else:
                preferences.SetBool(name, value)
        # The host retains all open documents, including unsaved work.
        self.host.show()
        event.accept()


def show_standalone():
    global _window
    if _window is None or _window._closed:
        _window = SolidFreeCADWindow()
    _window.showMaximized()
    _window.raise_()
    _window.activateWindow()
    _window.host.hide()
    return _window
