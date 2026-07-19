# Architecture

## Core decision

SolidFreeCAD Desktop is a GUI layer over the official FreeCAD 1.1.1 source. It does not implement a parallel CAD kernel.

## Official components retained

- `Base` and `App` libraries.
- `App::Document`, object properties, expressions, transactions and recompute graph.
- FCStd persistence.
- OpenCASCADE geometry through Part and PartDesign.
- Sketcher constraints and solver.
- Assembly, TechDraw, FEM and other official modules.
- Python interpreter and macro infrastructure.
- `Gui::CommandManager` and the registered command catalogue.
- `Gui::View3DInventor`, Coin3D/OpenGL and ViewProviders.
- TaskView, property editors, workbench activation and module loading.

## SolidFreeCAD components

The isolated GUI layer begins under `src/Gui/SolidFreeCAD`:

- `SolidCommandBridge`: resolves and invokes official FreeCAD commands.
- `SolidGuiManager`: installs or removes the new interface shell.
- `SolidRibbon`: grouped mechanical-design commands.
- Later: command search, welcome page, feature manager, property manager and theme manager.

## Integration stages

### Stage A — non-destructive shell

Keep `Gui::MainWindow`, the official MDI area, ComboView, TaskView and 3D viewer. Add a SolidFreeCAD ribbon and retain the classic interface.

### Stage B — adapted panels

Restyle the document tree and property/task presentation while retaining their official models and controllers.

### Stage C — default interface mode

After command coverage and regression tests, make SolidFreeCAD the default shell while keeping Classic mode available.

## Command rule

Production GUI controls must invoke registered FreeCAD commands or official APIs. CAD operations must not be duplicated inside the new GUI.

## Viewer rule

The Android Canvas preview is not used for desktop geometry. `Gui::View3DInventor` remains responsible for rendering, selection, preselection, camera state, clipping and ViewProvider updates.

## Compatibility rule

Documents using official FreeCAD object types must remain openable in unmodified FreeCAD 1.1.1.

## Upstream maintenance

All custom GUI files stay in an isolated directory and integration patches remain narrow. This reduces conflicts when adopting later official FreeCAD releases.
