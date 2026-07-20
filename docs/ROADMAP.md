# Roadmap

## Milestone 0 — Official baseline

Status: **partially complete**

Completed:

- Pin `FreeCAD/FreeCAD` tag `1.1.1`.
- Reproducible official-source acquisition.
- Exact-tag validation.
- Official API and command-catalogue checks.

Pending:

- First successful Ubuntu compilation.
- Record compiler, Qt, Python, OpenCASCADE and Coin3D versions from CI.
- FCStd, STEP and BREP smoke files.

## Milestone 1 — Solid GUI shell

Status: **implemented, awaiting compilation**

Completed:

- Add isolated `src/Gui/SolidFreeCAD` sources to `FreeCADGui`.
- Install and remove the shell through narrow `MainWindow` hooks.
- Add a light mechanical ribbon prototype.
- Reuse native FreeCAD actions.
- Preserve classic menus, docks, toolbars and viewer.
- Add Classic recovery mode.
- Add global command search.
- Add dynamic refresh when modules register commands.

Validation gate:

- Compile `FreeCADGui` and FreeCAD on Ubuntu 22.04.
- Launch under Xvfb.
- Confirm the ribbon and native actions.
- Capture the first screenshot.

## Milestone 2 — Mechanical modeling ribbon

Status: **started**

Implemented catalogue entries:

- Body.
- New Sketch.
- Pad.
- Pocket.
- Fillet.
- Chamfer.

Next:

- Replace the single toolbar with tabbed ribbon pages.
- Add Sketcher geometry and constraint groups.
- Add contextual activation based on workbench and edit mode.
- Validate a complete Body → Sketch → Pad → Pocket workflow.

## Milestone 3 — Feature and property managers

- Restyle the official tree and property panels.
- Integrate TaskView with a consistent accept/cancel layout.
- Add filtering, active-feature state and error indicators.
- Preserve selection and edit-mode synchronization.

## Milestone 4 — File workflows

- Welcome page and recent files.
- STEP, IGES, BREP and STL import.
- FCStd open-edit-save-reopen regression tests.
- Recovery and autosave integration.

## Milestone 5 — Assembly and drawings

- Assembly commands and component-tree behavior.
- TechDraw pages, views, sections and dimensions.
- PDF and DXF export.

## Milestone 6 — Ubuntu release

- Installable development artifact.
- AppImage x86-64.
- Debian package.
- ARM64 build where dependency support permits.
- Build matrix and release artifacts.

## Immediate backlog

1. Enable or trigger GitHub Actions for the new repository.
2. Correct the first CMake or C++ errors reported by Ubuntu CI.
3. Validate the Xvfb GUI smoke test and screenshot.
4. Package the first runnable development build.
5. Begin the tabbed ribbon architecture.
