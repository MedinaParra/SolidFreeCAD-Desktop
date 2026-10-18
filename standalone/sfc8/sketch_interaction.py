"""Mouse-driven entities, local-plane snapping and transient Coin previews."""
import math
import FreeCADGui as Gui
from . import backend


class SketchInteractionController:
    def __init__(self, owner):
        self.owner = owner
        self.view = None
        self.tool = None
        self.first_point = None
        self.callbacks = []
        self.preview_root = None
        self.preview_coords = None
        self.preview_lines = None

    @property
    def active(self):
        return self.tool is not None

    def start(self, tool):
        if tool not in ("line", "rectangle", "circle"):
            raise ValueError("Herramienta de croquis desconocida.")
        if backend.active_sketch() is None or Gui.activeDocument() is None:
            raise ValueError("Abra un croquis antes de dibujar.")
        self.cancel(silent=True)
        self.view = Gui.activeDocument().activeView()
        self.tool = tool
        try:
            for event, callback in [("SoMouseButtonEvent", self._on_mouse), ("SoLocation2Event", self._on_move), ("SoKeyboardEvent", self._on_key)]:
                self.callbacks.append((event, self.view.addEventCallback(event, callback)))
            self._make_preview()
        except Exception:
            self.cancel(silent=True)
            raise
        self.owner.on_sketch_tool_state(tool, "Seleccione el primer punto. Esc cancela la herramienta.")

    def _make_preview(self):
        from pivy import coin
        self.preview_root = coin.SoSeparator()
        picking = coin.SoPickStyle()
        picking.style = coin.SoPickStyle.UNPICKABLE
        self.preview_root.addChild(picking)
        color = coin.SoBaseColor()
        color.rgb = (0.95, 0.53, 0.12)
        self.preview_root.addChild(color)
        style = coin.SoDrawStyle()
        style.lineWidth = 2.0
        self.preview_root.addChild(style)
        self.preview_coords = coin.SoCoordinate3()
        self.preview_lines = coin.SoLineSet()
        self.preview_lines.numVertices.setValue(0)
        self.preview_root.addChild(self.preview_coords)
        self.preview_root.addChild(self.preview_lines)
        self.view.getSceneGraph().addChild(self.preview_root)

    def cancel(self, silent=False):
        was_active = self.active
        if self.view is not None:
            for event, callback in self.callbacks:
                try:
                    self.view.removeEventCallback(event, callback)
                except RuntimeError:
                    pass
            if self.preview_root is not None:
                try:
                    self.view.getSceneGraph().removeChild(self.preview_root)
                except RuntimeError:
                    pass
        self.callbacks = []
        self.preview_root = self.preview_coords = self.preview_lines = None
        self.view = self.tool = self.first_point = None
        if was_active and not silent:
            self.owner.on_sketch_tool_cancelled()

    def _point_from_info(self, info):
        position = info.get("Position")
        if position is None or self.view is None:
            return None
        point = backend.pointer_in_sketch(self.view.getPoint(position[0], position[1]))
        nearby = backend.pointer_in_sketch(self.view.getPoint(position[0] + 7, position[1]))
        tolerance = max(1e-6, math.hypot(nearby[0] - point[0], nearby[1] - point[1]))
        sketch = backend.active_sketch()
        targets = [(0.0, 0.0)]
        for geometry in sketch.Geometry:
            for attr in ("StartPoint", "EndPoint", "Center"):
                target = getattr(geometry, attr, None)
                if target is not None:
                    targets.append((float(target.x), float(target.y)))
        closest = min(targets, key=lambda p: math.hypot(p[0] - point[0], p[1] - point[1]))
        if math.hypot(closest[0] - point[0], closest[1] - point[1]) < tolerance:
            return closest
        if self.tool == "line" and self.first_point is not None:
            if abs(point[0] - self.first_point[0]) < tolerance:
                return self.first_point[0], point[1]
            if abs(point[1] - self.first_point[1]) < tolerance:
                return point[0], self.first_point[1]
        return point

    def _on_mouse(self, info):
        if info.get("State") != "DOWN":
            return
        if info.get("Button") == "BUTTON2":
            self.cancel()
            return
        if info.get("Button") != "BUTTON1":
            return
        point = self._point_from_info(info)
        if point is None:
            return
        if self.first_point is None:
            self.first_point = point
            self.owner.on_sketch_tool_first_point(self.tool, point)
        else:
            self._commit(point)

    def _on_move(self, info):
        if not self.active:
            return
        point = self._point_from_info(info)
        if point is not None:
            self._update_preview(point)
            self.owner.on_sketch_pointer(self.tool, self.first_point, point)

    def _update_preview(self, point):
        if self.first_point is None or self.preview_root is None:
            return
        x, y = self.first_point
        if self.tool == "rectangle":
            points = [(x, y), (point[0], y), point, (x, point[1]), (x, y)]
        elif self.tool == "circle":
            radius = math.hypot(point[0] - x, point[1] - y)
            points = [(x + radius * math.cos(i * math.tau / 64), y + radius * math.sin(i * math.tau / 64)) for i in range(65)]
        else:
            points = [self.first_point, point]
        from FreeCAD import Vector
        placement = backend.active_sketch().getGlobalPlacement()
        world = [placement.multVec(Vector(px, py, 0)) for px, py in points]
        self.preview_coords.point.setValues(0, len(world), [(p.x, p.y, p.z) for p in world])
        self.preview_lines.numVertices.setValue(len(world))
        self.view.redraw()

    def _on_key(self, info):
        if info.get("State") == "DOWN" and info.get("Key") == "ESCAPE":
            self.cancel()

    def _commit(self, second):
        tool, first = self.tool, self.first_point
        try:
            if tool == "rectangle":
                backend.add_rectangle_points(first, second)
            elif tool == "circle":
                backend.add_circle_points(first, second)
            else:
                backend.add_line_points(first, second)
        except Exception as exc:
            self.owner.on_sketch_tool_state(tool, str(exc))
            return
        self.cancel(silent=True)
        self.owner.on_sketch_tool_completed(tool)
