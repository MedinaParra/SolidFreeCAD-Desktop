# SolidFreeCAD alpha.11 — interactive sketch foundation

Alpha.11 keeps the validated alpha.10 standalone morphology and adds the first mouse-driven sketch interaction layer without activating FreeCAD workbenches or TaskView.

## Implemented

- `SketchInteractionController` owns temporary callbacks on the embedded FreeCAD 3D view.
- Rectangle: first click fixes one corner; second click fixes the opposite corner.
- Circle: first click fixes the center; second click fixes the radius.
- Mouse motion reports live X/Y dimensions in the SolidFreeCAD status bar and synchronizes the numeric PropertyManager fields.
- `Esc` cancels the active entity tool without cancelling the complete sketch.
- Accepting/cancelling the sketch and closing SolidFreeCAD always remove active view callbacks.
- The legacy numeric rectangle/circle commands remain available as a fallback under `Por medidas`.
- Geometry is written directly to `Sketcher::SketchObject` through `Part` and `Sketcher` APIs.
- Rectangle geometry receives coincident, horizontal and vertical constraints.

## Current sketch-plane contract

This first interaction milestone creates sketches on the global XY plane. SolidFreeCAD forces a top/normal view before mouse placement and maps the view point to sketch X/Y coordinates. Arbitrary face-supported sketch planes are intentionally deferred to the next milestone.

## Architecture

Alpha.11 is layered over alpha.10 rather than rewriting the validated window:

- `window.py`: validated alpha.10 morphology;
- `window_alpha11.py`: alpha.11 behavioral extension;
- `sketch_interaction.py`: transient mouse/keyboard controller;
- `backend.py`: point-based Sketcher geometry creation;
- `widgets.py`: interactive and numeric sketch commands.

## Validation gate

The Windows alpha.11 workflow must:

1. compile every Python file under `standalone/`;
2. verify registration and removal of mouse/move/keyboard callbacks;
3. verify the point-based rectangle/circle backend;
4. verify the alpha.11 standalone route;
5. reject the native FreeCAD command dispatcher anywhere in standalone Python.

## Next gate

- live transient preview geometry before the second click;
- snapping to origin, endpoints, midpoint and horizontal/vertical inference;
- face/plane selection for arbitrary supported sketches;
- real dimensional constraints driven from the PropertyManager;
- parametric native Pad/Pocket features instead of the current controlled BRep extrusion.
