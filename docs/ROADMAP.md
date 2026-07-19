# Roadmap

## Milestone 0 — Official baseline

- Obtain `FreeCAD/FreeCAD` tag `1.1.1`.
- Validate that the checkout is exactly the requested tag.
- Build the official source without SolidFreeCAD changes.
- Record compiler, Qt, Python, OpenCASCADE and Coin3D versions.
- Run FCStd, STEP and BREP smoke tests.

## Milestone 1 — Solid GUI shell

- Add `src/Gui/SolidFreeCAD` to `FreeCADGui`.
- Install `SolidGuiManager` after main-window initialization.
- Add a first mechanical ribbon.
- Invoke official commands by registered name.
- Preserve classic menus, docks and toolbars.

## Milestone 2 — Mechanical modeling ribbon

- Add Part Design and Sketcher groups.
- Support Body, Sketch, Pad, Pocket, Fillet and Chamfer.
- Synchronize enabled and disabled command states.
- Add command search and contextual groups.

## Milestone 3 — Feature and property managers

- Restyle the official tree and property panels.
- Integrate TaskView with a consistent accept/cancel layout.
- Add filtering, active-feature state and error indicators.

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

- AppImage x86-64.
- Debian package.
- ARM64 build where dependency support permits.
- GitHub Actions build matrix and artifacts.

## Immediate backlog

1. Bootstrap official source acquisition.
2. Apply the isolated GUI overlay automatically.
3. Validate the required 1.1.1 GUI APIs.
4. Compile the first ribbon shell.
5. Produce an Ubuntu artifact.
