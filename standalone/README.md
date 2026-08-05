# SolidFreeCAD alpha.8 — standalone application shell

## Decision

Alpha.8 is **not a FreeCAD workbench** and does not attempt to repaint, tabify or
hide parts of the standard FreeCAD window.

The physical Windows test showed that native GUI commands such as
`Sketcher_NewSketch` activate another workbench and rebuild FreeCAD's TaskView.
That behavior removes the SolidFreeCAD ribbon and restores the native Sketcher
interface. A workbench overlay therefore cannot guarantee a stable application
shell.

Alpha.8 changes the boundary:

```text
SolidFreeCAD QMainWindow
├── own menu, quick access and command ribbon
├── own FeatureManager
├── own PropertyManager / task state
├── FreeCAD document viewport embedded in the center
└── SolidFreeCAD command controllers
    ├── FreeCAD App documents and FCStd
    ├── Sketcher document objects
    ├── Part / OpenCASCADE geometry
    └── FreeCAD Gui view and selection services
```

## Rules

1. SolidFreeCAD owns the top-level `QMainWindow`.
2. FreeCAD's standard main window remains hidden while SolidFreeCAD is active.
3. The native document viewport is embedded in the SolidFreeCAD central area.
4. Modelling commands must not call `Gui.runCommand()` when that command can
   activate a workbench or open a native TaskView.
5. Sketch creation and early sketch geometry are performed directly through
   `Sketcher::SketchObject`.
6. Solid creation is initially performed through controlled Part/OpenCASCADE
   operations and stored as native document features.
7. FCStd remains the project file format.
8. Alpha.6 remains the validated engine/runtime reference, not the GUI base.

## Current prototype

`SolidFreeCADStandalone.py` creates a separate application window and implements:

- clean application menu and quick-access area;
- fixed tabbed ribbon owned by SolidFreeCAD;
- custom design tree and property panel;
- embedded FreeCAD document viewport;
- new PartDesign Body without changing workbench;
- new `Sketcher::SketchObject` without activating Sketcher;
- rectangle and circle creation through the Sketcher API;
- a controlled extruded solid from a closed sketch;
- open/save FCStd and import STEP;
- isometric, front, top and fit views;
- restoration of the FreeCAD host window when the prototype closes.

## Scope boundary

The first prototype proves the architecture and the stable sketch transition.
It is not yet a production replacement for the complete Sketcher solver UI.

The next gates are:

1. validate that the standalone window remains visible through the full sequence
   `new part -> new sketch -> rectangle -> solid`;
2. implement mouse-driven line, rectangle, circle and trim tools using callbacks
   on the embedded 3D view;
3. implement SolidFreeCAD-owned constraints and dimensions panels;
4. replace the temporary direct extrusion with a fully parametric feature proxy;
5. add undo transactions and document observers;
6. create a dedicated Windows launcher and installer;
7. test 100%, 125% and 150% DPI on a physical engineering workstation.

## Intellectual property

SolidFreeCAD uses its own code, terminology, layout details and visual assets.
The goal is a familiar professional mechanical-CAD workflow, not a copy of
SolidWorks branding, source code or proprietary artwork.
