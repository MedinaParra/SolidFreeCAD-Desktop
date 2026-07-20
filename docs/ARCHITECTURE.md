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
- Native `Gui::Action` and `QAction` objects.
- `Gui::View3DInventor`, Coin3D/OpenGL and ViewProviders.
- TaskView, property editors, workbench activation and module loading.

## Implemented SolidFreeCAD components

The isolated GUI layer lives under `src/Gui/SolidFreeCAD`:

- `SolidCommandBridge`: resolves and invokes official FreeCAD commands.
- `SolidCommandSearch`: searchable catalogue of all registered commands.
- `SolidGuiBootstrap`: interface-mode selection and recovery path.
- `SolidGuiManager`: installs, refreshes and removes the interface shell.
- Light ribbon prototype containing native FreeCAD actions.

The current ribbon refreshes when `Gui::CommandManager::signalChanged` reports that a workbench or module has registered more commands. This allows Part Design entries to become native actions after their module is loaded.

## Integration strategy

### Stage A — non-destructive shell

Keep `Gui::MainWindow`, the official MDI area, ComboView, TaskView and 3D viewer. Insert the SolidFreeCAD shell near the end of `MainWindow` initialization and remove it before main-window teardown.

The classic interface remains available through:

- `SOLIDFREECAD_CLASSIC_MODE=1`.
- FreeCAD preference `BaseApp/Preferences/SolidFreeCAD/InterfaceMode=Classic`.

### Stage B — tabbed ribbon

Replace the single toolbar prototype with a dedicated tabbed ribbon while continuing to host the official FreeCAD actions. No modeling command is reimplemented.

### Stage C — adapted panels

Restyle or wrap the document tree, PropertyView and TaskView while retaining their official models and controllers.

### Stage D — default SolidFreeCAD experience

After command coverage, file-cycle regression tests and Ubuntu packaging are stable, make SolidFreeCAD the default shell while keeping Classic mode available.

## Command rule

Production GUI controls must invoke registered FreeCAD commands or official APIs. CAD operations must not be duplicated inside the new GUI.

The preferred integration is `Gui::Command::addTo(QWidget*)`, which preserves the official icon, translation, shortcut, activation logic and enabled state.

## Viewer rule

The Android Canvas preview is not used for desktop geometry. `Gui::View3DInventor` remains responsible for rendering, selection, preselection, camera state, clipping and ViewProvider updates.

## Compatibility rule

Documents using official FreeCAD object types must remain openable in unmodified FreeCAD 1.1.1. Custom SolidFreeCAD document objects are prohibited until an explicit compatibility and migration design exists.

## Validation layers

1. Python unit tests for overlay application and idempotence.
2. Source checks against the official 1.1.1 APIs and command catalogue.
3. CMake compilation of `FreeCADGui` and the FreeCAD executable.
4. Xvfb GUI smoke test checking the ribbon, search box and native actions.
5. Automated screenshot capture for visual inspection.

## Upstream maintenance

All custom GUI files stay in an isolated directory and integration patches remain narrow. This reduces conflicts when adopting later official FreeCAD releases.
