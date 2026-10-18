"""Mouse-driven entities, local-plane snapping and transient Coin previews."""
import math
import FreeCADGui as Gui
from . import backend
from .sketch_geometry import arc_through_points, distance, TOLERANCE


class SketchInteractionController:
    def __init__(self, owner):
        self.owner = owner
        self.view = None
        self.tool = None
        self.first_point = None
        self.middle_point = None
        self.chain_start = None
        self.chain_segments = 0
        self.callbacks = []
        self.preview_root = None
        self.preview_coords = None
        self.preview_lines = None
        self.pick_tolerance = TOLERANCE

    @property
    def active(self):
        return self.tool is not None

    def start(self, tool):
        if tool not in ("line", "polyline", "rectangle", "circle", "arc", "trim"):
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
        messages = {
            "polyline": "Seleccione el inicio y continúe con clics. Vuelva al inicio para cerrar; Enter termina.",
            "arc": "Arco de tres puntos: inicio, punto intermedio y final.",
            "trim": "Seleccione el tramo que desea recortar. Esc termina la herramienta.",
        }
        self.owner.on_sketch_tool_state(tool, messages.get(tool, "Seleccione el primer punto. Esc cancela la herramienta."))

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
        self.view = self.tool = self.first_point = self.middle_point = self.chain_start = None
        self.chain_segments = 0
        if was_active and not silent:
            self.owner.on_sketch_tool_cancelled()

    def _point_from_info(self, info):
        position = info.get("Position")
        if position is None or self.view is None:
            return None
        point = backend.pointer_in_sketch(self.view.getPoint(position[0], position[1]))
        nearby = backend.pointer_in_sketch(self.view.getPoint(position[0] + 7, position[1]))
        self.pick_tolerance = max(TOLERANCE, distance(nearby, point))
        if self.tool == "trim":
            return point
        targets = [(0.0, 0.0)]
        for geometry in backend.active_sketch().Geometry:
            for attr in ("StartPoint", "EndPoint", "Center"):
                candidate = getattr(geometry, attr, None)
                if candidate is not None:
                    targets.append((float(candidate.x), float(candidate.y)))
        closest = min(targets, key=lambda p: distance(p, point))
        if distance(closest, point) < self.pick_tolerance:
            return closest
        if self.tool in ("line", "polyline") and self.first_point is not None:
            if abs(point[0] - self.first_point[0]) < self.pick_tolerance:
                return self.first_point[0], point[1]
            if abs(point[1] - self.first_point[1]) < self.pick_tolerance:
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
        if point is not None:
            self.place_point(point)

    def place_point(self, point):
        if self.tool == "trim":
            try:
                index = backend.nearest_geometry(point, self.pick_tolerance)
                backend.trim_geometry(index, point)
                self.owner.on_sketch_tool_completed("trim")
            except Exception as exc:
                self.owner.on_sketch_tool_state("trim", str(exc))
            return
        if self.first_point is None:
            self.first_point = point
            self.chain_start = point
            self.owner.on_sketch_tool_first_point(self.tool, point)
        elif self.tool == "arc" and self.middle_point is None:
            if distance(self.first_point, point) <= TOLERANCE:
                self.owner.on_sketch_tool_state("arc", "Seleccione un punto intermedio distinto del inicio.")
                return
            self.middle_point = point
            self.owner.on_sketch_tool_state("arc", "Seleccione el punto final del arco.")
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
            radius = distance(point, self.first_point)
            points = [(x + radius * math.cos(i * math.tau / 64), y + radius * math.sin(i * math.tau / 64)) for i in range(65)]
        elif self.tool == "arc" and self.middle_point is not None:
            try:
                points = arc_through_points(self.first_point, self.middle_point, point)
            except ValueError:
                points = [self.first_point, self.middle_point, point]
        else:
            points = [self.first_point, point]
        from FreeCAD import Vector
        placement = backend.active_sketch().getGlobalPlacement()
        world = [placement.multVec(Vector(px, py, 0)) for px, py in points]
        self.preview_coords.point.setValues(0, len(world), [(p.x, p.y, p.z) for p in world])
        self.preview_lines.numVertices.setValue(len(world))
        self.view.redraw()

    def _on_key(self, info):
        if info.get("State") == "DOWN":
            if info.get("Key") == "ESCAPE":
                self.cancel()
            elif info.get("Key") in ("RETURN", "ENTER") and self.tool == "polyline":
                self.cancel(silent=True)
                self.owner.on_sketch_tool_completed("polyline")

    def _commit(self, second):
        tool, first = self.tool, self.first_point
        try:
            if tool == "rectangle":
                backend.add_rectangle_points(first, second)
            elif tool == "circle":
                backend.add_circle_points(first, second)
            elif tool == "arc":
                backend.add_arc_points(first, self.middle_point, second)
            else:
                backend.add_line_points(first, second)
        except Exception as exc:
            self.owner.on_sketch_tool_state(tool, str(exc))
            return
        if tool == "polyline":
            self.chain_segments += 1
            if self.chain_segments >= 3 and distance(second, self.chain_start) <= TOLERANCE:
                self.cancel(silent=True)
            else:
                self.first_point = second
                self.preview_lines.numVertices.setValue(0)
                self.owner.on_sketch_tool_state(tool, "Continúe con otro punto; vuelva al inicio para cerrar o pulse Enter.")
        else:
            self.cancel(silent=True)
        self.owner.on_sketch_tool_completed(tool)
