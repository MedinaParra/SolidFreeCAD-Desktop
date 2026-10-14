"""Interactive sketch tools for SolidFreeCAD alpha.11.

The controller owns temporary 3D-view callbacks while a sketch entity is being
placed. It does not activate a native FreeCAD workbench; geometry is committed
through the SolidFreeCAD backend instead of the native command dispatcher.
"""
from __future__ import annotations

import math

import FreeCADGui as Gui

from . import backend


class SketchInteractionController:
    """Two-click rectangle/circle placement in the active sketch plane."""

    def __init__(self, owner):
        self.owner = owner
        self.view = None
        self.tool = None
        self.first_point = None
        self._mouse_callback = None
        self._move_callback = None
        self._key_callback = None

    @property
    def active(self):
        return self.tool is not None

    def start(self, tool: str):
        if tool not in ("rectangle", "circle"):
            raise ValueError(f"Unsupported sketch tool: {tool}")
        if backend.active_sketch() is None:
            raise ValueError("No hay un croquis activo.")
        if Gui.activeDocument() is None:
            raise ValueError("No hay una vista 3D activa.")

        self.cancel(silent=True)
        backend.prepare_sketch_view()
        self.view = Gui.activeDocument().activeView()
        self.tool = tool
        self.first_point = None
        self._mouse_callback = self.view.addEventCallback(
            "SoMouseButtonEvent", self._on_mouse
        )
        self._move_callback = self.view.addEventCallback(
            "SoLocation2Event", self._on_move
        )
        self._key_callback = self.view.addEventCallback(
            "SoKeyboardEvent", self._on_key
        )
        self.owner.on_sketch_tool_state(
            tool,
            "Seleccione el primer punto en el plano del croquis.",
        )

    def cancel(self, silent=False):
        was_active = self.active
        view = self.view
        callbacks = (
            ("SoMouseButtonEvent", self._mouse_callback),
            ("SoLocation2Event", self._move_callback),
            ("SoKeyboardEvent", self._key_callback),
        )
        if view is not None:
            for event_name, callback in callbacks:
                if callback is None:
                    continue
                try:
                    view.removeEventCallback(event_name, callback)
                except Exception:
                    pass

        self.view = None
        self.tool = None
        self.first_point = None
        self._mouse_callback = None
        self._move_callback = None
        self._key_callback = None
        if was_active and not silent:
            self.owner.on_sketch_tool_cancelled()

    def _point_from_info(self, info):
        position = info.get("Position")
        if position is None or self.view is None:
            return None
        point = self.view.getPoint(position[0], position[1])
        # Alpha.11 currently creates sketches on the global XY plane. The
        # viewport is forced normal to that plane, so x/y are the sketch
        # coordinates and z is intentionally discarded.
        return float(point.x), float(point.y)

    def _on_mouse(self, info):
        if info.get("State") != "DOWN":
            return
        button = info.get("Button")
        if button == "BUTTON2":
            self.cancel()
            return
        if button != "BUTTON1":
            return

        point = self._point_from_info(info)
        if point is None:
            return
        if self.first_point is None:
            self.first_point = point
            self.owner.on_sketch_tool_first_point(self.tool, point)
            return
        self._commit(point)

    def _on_move(self, info):
        if not self.active:
            return
        point = self._point_from_info(info)
        if point is not None:
            self.owner.on_sketch_pointer(self.tool, self.first_point, point)

    def _on_key(self, info):
        if info.get("State") == "DOWN" and info.get("Key") == "ESCAPE":
            self.cancel()

    def _commit(self, second_point):
        tool = self.tool
        first_point = self.first_point
        if first_point is None or tool is None:
            return

        dx = second_point[0] - first_point[0]
        dy = second_point[1] - first_point[1]
        if tool == "rectangle":
            if abs(dx) < 1e-6 or abs(dy) < 1e-6:
                self.owner.on_sketch_tool_state(
                    tool, "El rectángulo necesita ancho y alto distintos de cero."
                )
                return
            backend.add_rectangle_points(first_point, second_point)
        else:
            radius = math.hypot(dx, dy)
            if radius < 1e-6:
                self.owner.on_sketch_tool_state(
                    tool, "El círculo necesita un radio distinto de cero."
                )
                return
            backend.add_circle_points(first_point, second_point)

        self.cancel(silent=True)
        self.owner.on_sketch_tool_completed(tool)
