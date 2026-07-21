# SolidFreeCAD Desktop roadmap

Updated: 2026-07-21

## Overall progress

| Area | Progress | Current state |
| --- | ---: | --- |
| Reproducible FreeCAD 1.1.1 foundation | 90% | Overlay, CI, Ubuntu build, deb packaging, clean install and Classic recovery are operational. |
| SolidFreeCAD mechanical workspace | 65% | Tabbed ribbon, command search, custom icons, model history, Property Manager and contextual workspace states are implemented. |
| Basic Part Design workflow | 48% | Body, Sketch, Pad and Pocket are validated; the next gate is complete guided editing for Revolution, Fillet and Chamfer. |
| File and interchange workflow | 45% | Native New/Open/Save/Save As/Import/Export commands are exposed through the new File workspace; broader STEP regression fixtures remain. |
| FCStd compatibility and persistence | 42% | A Sketch → Pad vertical slice is saved, reopened and volume-checked. Complex workbench-preservation fixtures remain. |
| Macro and Python workflow | 20% | The official FreeCAD Python engine remains available; a controlled macro editor and compatibility suite are not implemented yet. |
| Assembly, TechDraw, Sheet Metal and FEM | 12% | Ribbon entry points exist, but production workflows and regression projects are still pending. |
| Product release and documentation | 28% | Installable Ubuntu development packages exist; updater, signed release, onboarding and user documentation remain. |

**Estimated complete product progress: 44%.**

The percentage represents the full desktop product vision, not only the first usable MVP. The basic mechanical-design MVP is approximately 65% complete.

## Completed milestones

### M0 — Official foundation

- Pin official FreeCAD 1.1.1 source.
- Apply an isolated and idempotent Qt/C++ overlay.
- Build `FreeCADGui`, PartDesign, Sketcher and the FreeCAD executable.
- Preserve a Classic recovery mode.
- Package and install an Ubuntu 22.04 `.deb` in a clean container.

### M1 — Mechanical workspace foundation

- Tabbed mechanical ribbon.
- Global command search.
- SolidFreeCAD vector icon system.
- Model-history panel and Property Manager.
- Sketch, Pad and Pocket selection/edit contracts.
- Automatic GUI screenshots and Xvfb smoke tests.

### M2 — Workspace and document controls

- Tabs displayed above command pages.
- Primary modeling commands highlighted.
- Dynamic workspace badge (`PIEZA`, `CROQUIS`, `ARCHIVO`, and other environments).
- Active-document title and `NUEVO`/`GUARDADO` state.
- Native File workspace with:
  - New
  - Open
  - Save
  - Save As
  - Import
  - Export
  - Project information
  - Print
  - Close document
- Start group for Body and Sketch creation.

## Current milestone — M3 Basic modeling MVP

The current objective is a reliable end-to-end workflow for ordinary mechanical parts.

### Required gates

- [x] Create a Body.
- [x] Create and edit a Sketch.
- [x] Create and edit a Pad.
- [x] Create and edit a Pocket.
- [x] Save and reopen FCStd without losing the validated solid.
- [x] Expose native document and interchange commands.
- [ ] Add guided Revolution parameters and regression geometry.
- [ ] Add Fillet and Chamfer selection/property workflows.
- [ ] Add a controlled STEP export/import round-trip fixture.
- [ ] Add recent-file and recovery-session UX.
- [ ] Replace the remaining floating Task strip with a safe context panel that preserves Sketcher editing.

## Next milestones

### M4 — Robust FCStd and STEP compatibility

- Open representative FCStd files from Part Design, Assembly, TechDraw and FEM.
- Preserve unknown workbench data when saving.
- Detect partial restore and unsupported objects without destructive edits.
- Build STEP/STP import and export regression fixtures with geometry and volume checks.

### M5 — Macro and automation workspace

- Embedded macro editor.
- Run/stop controls and output console.
- Compatibility tests for `FreeCAD`, `Part` and selected Sketcher APIs.
- Local macro library and trusted-script warnings.

### M6 — Advanced workbenches

- Assembly constraints and component insertion.
- TechDraw page and dimension flow.
- Sheet Metal integration.
- FEM study setup and solver workflow.

### M7 — Product release

- Signed packages and release channel.
- First-run onboarding and example projects.
- Crash recovery and session restore.
- Performance testing with large FCStd and STEP files.
- End-user documentation and acceptance tests.
