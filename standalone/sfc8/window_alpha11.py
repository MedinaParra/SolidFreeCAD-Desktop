"""SolidFreeCAD alpha.11 window extension with interactive sketch placement."""
from __future__ import annotations

import math

from PySide import QtWidgets

from . import backend
from .sketch_interaction import SketchInteractionController
from .window import SolidFreeCADWindow as Alpha10Window

_APP_NAME = "SolidFreeCAD Professional alpha.11"
_window = None


class SolidFreeCADWindow(Alpha10Window):
    """Alpha.10 morphology plus mouse-driven sketch tools."""

    def __init__(self):
        self.sketch_interaction = None
        super().__init__()
        self.sketch_interaction = SketchInteractionController(self)
        self.refresh(True)

    def refresh(self, force=False):
        super().refresh(force)
        doc = backend.active_document()
        label = "Sin documento" if doc is None else (doc.Label or doc.Name)
        self.setWindowTitle(f"{_APP_NAME} — {label}")

    def show_about(self):
        QtWidgets.QMessageBox.information(
            self,
            "SolidFreeCAD alpha.11",
            "CAD paramétrico sobre FreeCAD 1.1.1 con croquis interactivo propio.",
        )

    def _ensure_sketch_operation(self):
        if self.manager.operation != "sketch":
            self.new_sketch()
        sketch = backend.active_sketch()
        if sketch is None:
            raise ValueError("No se pudo activar un croquis.")
        backend.prepare_sketch_view()
        return sketch

    def start_rectangle_tool(self):
        try:
            self._ensure_sketch_operation()
            self.sketch_interaction.start("rectangle")
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Rectángulo", str(exc))

    def start_circle_tool(self):
        try:
            self._ensure_sketch_operation()
            self.sketch_interaction.start("circle")
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Círculo", str(exc))

    def accept_manager_operation(self):
        if self.sketch_interaction is not None:
            self.sketch_interaction.cancel(silent=True)
        super().accept_manager_operation()

    def cancel_manager_operation(self):
        if self.sketch_interaction is not None:
            self.sketch_interaction.cancel(silent=True)
        super().cancel_manager_operation()

    def on_sketch_tool_state(self, tool, message):
        name = "Rectángulo" if tool == "rectangle" else "Círculo"
        self.state.setText(f"{name}: {message}")
        if self.manager.operation == "sketch":
            self.manager.message.setText(message)

    def on_sketch_tool_first_point(self, tool, point):
        name = "rectángulo" if tool == "rectangle" else "círculo"
        self.state.setText(
            f"Primer punto del {name}: X={point[0]:.2f}  Y={point[1]:.2f} mm · seleccione el segundo punto"
        )
        self.manager.message.setText(
            "Primer punto fijado. Mueva el cursor y seleccione el segundo punto; Esc cancela la herramienta."
        )

    def on_sketch_pointer(self, tool, first, point):
        if first is None:
            self.state.setText(
                f"X={point[0]:.2f}  Y={point[1]:.2f} mm · seleccione el primer punto"
            )
            return

        dx = point[0] - first[0]
        dy = point[1] - first[1]
        if tool == "rectangle":
            width = abs(dx)
            height = abs(dy)
            if width >= 0.01:
                self.manager.width.setValue(width)
            if height >= 0.01:
                self.manager.height.setValue(height)
            self.state.setText(
                f"Rectángulo {width:.2f} × {height:.2f} mm · X={point[0]:.2f} Y={point[1]:.2f}"
            )
        else:
            radius = math.hypot(dx, dy)
            if radius >= 0.01:
                self.manager.radius.setValue(radius)
            self.state.setText(
                f"Círculo R={radius:.2f} mm · X={point[0]:.2f} Y={point[1]:.2f}"
            )

    def on_sketch_tool_completed(self, tool):
        self.manager.refresh_operation()
        name = "Rectángulo" if tool == "rectangle" else "Círculo"
        self.state.setText(f"{name} agregado al croquis")
        self.manager.message.setText(
            f"{name} creado. Puede iniciar otra entidad o aceptar el croquis."
        )
        self.refresh(True)

    def on_sketch_tool_cancelled(self):
        self.state.setText("Herramienta de croquis cancelada")
        if self.manager.operation == "sketch":
            self.manager.message.setText(
                "Herramienta cancelada. El croquis sigue activo."
            )

    def closeEvent(self, event):
        if self.sketch_interaction is not None:
            self.sketch_interaction.cancel(silent=True)
        super().closeEvent(event)


def show_standalone():
    global _window
    if _window is None:
        _window = SolidFreeCADWindow()
    _window.showMaximized()
    _window.raise_()
    _window.activateWindow()
    _window.host.hide()
    return _window
