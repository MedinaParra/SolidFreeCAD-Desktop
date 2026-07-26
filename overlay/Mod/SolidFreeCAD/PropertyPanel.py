"""Simplified SolidFreeCAD property panel for parametric shafts."""

from __future__ import annotations

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from SolidFreeCAD.ShaftFeature import create_shaft, is_shaft


_PANEL_OBJECT_NAME = "SolidFreeCADShaftPropertyPanel"
_panel = None


class _SelectionObserver:
    def __init__(self, panel):
        self.panel = panel

    def addSelection(self, *_args):
        self.panel.refresh_from_selection()

    def removeSelection(self, *_args):
        self.panel.refresh_from_selection()

    def clearSelection(self, *_args):
        self.panel.refresh_from_selection()


class ShaftPropertyPanel(QtWidgets.QDockWidget):
    """Dockable editor that exposes only the main shaft parameters."""

    _length_properties = (
        ("MainLength", "Largo principal"),
        ("MainDiameter", "Diámetro principal"),
        ("ShoulderLength", "Largo del resalte"),
        ("ShoulderDiameter", "Diámetro del resalte"),
        ("KeywayWidth", "Ancho chavetero"),
        ("KeywayDepth", "Profundidad chavetero"),
        ("KeywayLength", "Largo chavetero"),
        ("KeywayOffset", "Posición chavetero"),
    )

    def __init__(self, parent=None):
        super().__init__("Propiedades del eje", parent)
        self.setObjectName(_PANEL_OBJECT_NAME)
        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self._object = None
        self._loading = False
        self._editors = {}

        content = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QtWidgets.QLabel("SolidFreeCAD · Eje paramétrico")
        title.setStyleSheet("font-size: 15px; font-weight: 600;")
        layout.addWidget(title)

        self._selection_label = QtWidgets.QLabel("No hay un eje seleccionado")
        self._selection_label.setWordWrap(True)
        layout.addWidget(self._selection_label)

        form = QtWidgets.QFormLayout()
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)

        for property_name, label in self._length_properties:
            editor = QtWidgets.QDoubleSpinBox()
            editor.setDecimals(2)
            editor.setRange(0.0, 1_000_000.0)
            editor.setSingleStep(1.0)
            editor.setSuffix(" mm")
            editor.editingFinished.connect(self.apply_changes)
            self._editors[property_name] = editor
            form.addRow(label, editor)

        self._keyway_checkbox = QtWidgets.QCheckBox("Incluir chavetero")
        self._keyway_checkbox.toggled.connect(self._on_keyway_toggled)
        form.addRow("Chavetero", self._keyway_checkbox)
        layout.addLayout(form)

        buttons = QtWidgets.QHBoxLayout()
        self._create_button = QtWidgets.QPushButton("Crear eje")
        self._create_button.clicked.connect(self.create_new_shaft)
        buttons.addWidget(self._create_button)

        self._apply_button = QtWidgets.QPushButton("Aplicar")
        self._apply_button.clicked.connect(self.apply_changes)
        buttons.addWidget(self._apply_button)
        layout.addLayout(buttons)

        secondary = QtWidgets.QHBoxLayout()
        self._fit_button = QtWidgets.QPushButton("Ajustar vista")
        self._fit_button.clicked.connect(self.fit_view)
        secondary.addWidget(self._fit_button)

        self._standard_button = QtWidgets.QPushButton("Editor completo")
        self._standard_button.setToolTip(
            "Mantiene seleccionado el eje para editar propiedades avanzadas "
            "en el panel estándar de FreeCAD."
        )
        self._standard_button.clicked.connect(self.select_current_object)
        secondary.addWidget(self._standard_button)
        layout.addLayout(secondary)

        note = QtWidgets.QLabel(
            "Las cotas se actualizan en el modelo al presionar Aplicar o al "
            "salir de un campo."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: palette(mid);")
        layout.addWidget(note)
        layout.addStretch(1)

        self.setWidget(content)
        self._selection_observer = _SelectionObserver(self)
        Gui.Selection.addObserver(self._selection_observer)
        self.refresh_from_selection()

    def _find_selected_shaft(self):
        for obj in Gui.Selection.getSelection():
            if is_shaft(obj):
                return obj

        doc = App.ActiveDocument
        if doc:
            shafts = [obj for obj in doc.Objects if is_shaft(obj)]
            if len(shafts) == 1:
                return shafts[0]
        return None

    def refresh_from_selection(self):
        self._object = self._find_selected_shaft()
        self._loading = True
        try:
            enabled = self._object is not None
            self._selection_label.setText(
                self._object.Label if enabled else "No hay un eje seleccionado"
            )
            self._apply_button.setEnabled(enabled)
            self._fit_button.setEnabled(enabled)
            self._standard_button.setEnabled(enabled)
            self._keyway_checkbox.setEnabled(enabled)

            for property_name, editor in self._editors.items():
                editor.setEnabled(enabled)
                if enabled:
                    editor.setValue(float(getattr(self._object, property_name)))

            if enabled:
                self._keyway_checkbox.setChecked(bool(self._object.AddKeyway))
            self._set_keyway_editors_enabled(
                enabled and self._keyway_checkbox.isChecked()
            )
        finally:
            self._loading = False

    def _set_keyway_editors_enabled(self, enabled):
        for property_name in (
            "KeywayWidth",
            "KeywayDepth",
            "KeywayLength",
            "KeywayOffset",
        ):
            self._editors[property_name].setEnabled(enabled)

    def _on_keyway_toggled(self, checked):
        self._set_keyway_editors_enabled(bool(self._object) and checked)
        if not self._loading:
            self.apply_changes()

    def apply_changes(self):
        if self._loading or not self._object:
            return

        for property_name, editor in self._editors.items():
            setattr(self._object, property_name, editor.value())
        self._object.AddKeyway = self._keyway_checkbox.isChecked()
        self._object.Document.recompute()
        self._selection_label.setText(f"{self._object.Label} · actualizado")

    def create_new_shaft(self):
        obj = create_shaft()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(obj)
        self.refresh_from_selection()
        self.fit_view()

    def select_current_object(self):
        if not self._object:
            return
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(self._object)

    def fit_view(self):
        if not App.ActiveDocument or not Gui.activeDocument():
            return
        view = Gui.activeDocument().activeView()
        view.viewAxonometric()
        view.fitAll()

    def closeEvent(self, event):
        event.ignore()
        self.hide()


def show_panel():
    """Show and return the singleton shaft property panel."""

    global _panel
    main_window = Gui.getMainWindow()
    if _panel is None:
        _panel = main_window.findChild(QtWidgets.QDockWidget, _PANEL_OBJECT_NAME)
    if _panel is None:
        _panel = ShaftPropertyPanel(main_window)
        main_window.addDockWidget(QtCore.Qt.RightDockWidgetArea, _panel)
    _panel.refresh_from_selection()
    _panel.show()
    _panel.raise_()
    return _panel


def hide_panel():
    if _panel is not None:
        _panel.hide()
