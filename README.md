# SolidFreeCAD Desktop

SolidFreeCAD Desktop is a new Qt/C++ graphical interface built on the official FreeCAD 1.1.1 source code.

## Foundation

- Official upstream: `FreeCAD/FreeCAD`
- Pinned source tag: `1.1.1`
- Initial target: Ubuntu Linux x86-64
- GUI technology: Qt Widgets and C++
- CAD kernel and document system: official FreeCAD components

SolidFreeCAD does not replace OpenCASCADE, FCStd, PartDesign, Sketcher, Assembly, TechDraw, FEM, Python, Coin3D or the official command framework. It reorganizes those capabilities through a mechanical-design-oriented interface inspired by the SolidFreeCAD Android concept.

## Repository strategy

This repository is a reproducible GUI overlay. Build scripts obtain the official FreeCAD 1.1.1 source, copy the isolated `src/Gui/SolidFreeCAD` layer into it and apply narrow integration hooks.

This keeps the custom code reviewable while ensuring that every resulting application is built against the official FreeCAD source.

## Implemented in the bootstrap branch

- Idempotent overlay installer for official FreeCAD 1.1.1.
- CMake integration inside the official `FreeCADGui` target.
- Light SolidFreeCAD ribbon shell.
- Native FreeCAD actions, icons, translations, shortcuts and enabled states.
- File commands: New, Open, Save, Undo and Redo.
- View commands: Fit All and Axonometric.
- Part Design entries: Body, Sketch, Pad, Pocket, Fillet and Chamfer.
- Dynamic ribbon refresh when FreeCAD modules register commands.
- Global command search over the registered FreeCAD command catalogue.
- Classic interface recovery mode.
- Command-catalogue verification against the official source.
- Overlay unit tests.
- Ubuntu validation and compilation workflows.

## Prepare a source tree

```bash
./scripts/fetch-upstream.sh build/freecad-source
python3 scripts/verify-command-catalog.py build/freecad-source
python3 scripts/apply-overlay.py build/freecad-source
```

## Classic recovery mode

SolidFreeCAD is enabled by default in builds containing the overlay. To start without the new shell:

```bash
SOLIDFREECAD_CLASSIC_MODE=1 FreeCAD
```

The persistent FreeCAD preference is:

```text
User parameter:BaseApp/Preferences/SolidFreeCAD
InterfaceMode = Classic | SolidFreeCAD
```

## Validation status

The repository contains unit, source-validation and Ubuntu compilation workflows. No successful GitHub Actions execution has been reported yet, so the C++ integration and Ubuntu binary remain unverified until Actions runs and returns build results.

## Next milestone

1. Obtain the first successful `FreeCADGui` Ubuntu build.
2. Launch the application under Xvfb and assert that `SolidFreeCADRibbon` exists.
3. Generate an installable development artifact.
4. Replace the single toolbar with real tabbed ribbon pages.
5. Begin the Feature Manager and Property Manager adaptations.
