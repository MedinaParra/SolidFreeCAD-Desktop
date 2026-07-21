# SolidFreeCAD Desktop roadmap

Updated: 2026-07-21

## Product scope

SolidFreeCAD Desktop is a local-first mechanical CAD application built on official FreeCAD 1.1.1 components. The intended product covers part design, sketches, assemblies, drawings, sheet metal, welded structures, FCStd/STEP interoperability and local macro automation.

The following areas are intentionally outside the current product scope:

- FEM, stress, thermal, fluid and motion simulation.
- Mesh generation, solver setup and simulation post-processing.
- Cloud-only 3DEXPERIENCE services.
- Licensed SOLIDWORKS-specific formats or behavior that cannot be reproduced safely with FreeCAD APIs.

The existing Simulation/FEM ribbon placeholder is scheduled for removal. Inspection in SolidFreeCAD means geometry, dimensions, mass properties, clearances and model-health checks, not engineering simulation.

## Visual design contract

- All primary SolidFreeCAD commands must use colorful, attractive and consistent vector icons.
- Monochrome placeholder icons are not accepted for enabled production commands.
- Disabled commands may use desaturated versions of the same icon.
- Icons must remain legible at 16, 24, 32 and 48 px and on light or dark backgrounds.
- Related commands must share a recognizable visual family while remaining distinguishable.
- The interface may be inspired by professional mechanical CAD workflows, but must use original SolidFreeCAD artwork and naming.

## Overall progress

| Area | Progress | Current state |
| --- | ---: | --- |
| Reproducible FreeCAD 1.1.1 foundation | 90% | Overlay, CI, Ubuntu build, deb packaging, clean install and Classic recovery are operational. |
| SolidFreeCAD mechanical workspace | 55% | Tabbed ribbon, command search, initial colorful icons, model history, Property Manager and contextual workspace states are implemented. Welcome, context-command and heads-up interaction layers remain. |
| Basic Part Design workflow | 48% | Body, Sketch, Pad and Pocket are validated; guided Revolution, Fillet, Chamfer, patterns and richer sketch tools remain. |
| File and interchange workflow | 45% | Native New/Open/Save/Save As/Import/Export commands are exposed; recent documents, templates and STEP round-trip fixtures remain. |
| FCStd compatibility and persistence | 42% | A Sketch -> Pad vertical slice is saved, reopened and volume-checked. Complex-workbench preservation fixtures remain. |
| Welded structures workflow | 15% | A ribbon placeholder exists, but structural-member, trim, cut-list and weld metadata logic are not yet implemented. |
| Assembly, TechDraw and Sheet Metal | 12% | Ribbon entry points exist, but production workflows and regression projects are still pending. |
| Macro and Python workflow | 20% | The official FreeCAD Python engine remains available; a controlled macro editor and compatibility suite are not implemented yet. |
| Product release and documentation | 28% | Installable Ubuntu development packages exist; updater, signed release, onboarding and user documentation remain. |

**Estimated complete product progress: 42%.**

The refined percentage is lower than the previous estimate because the user-interface and welded-structure acceptance criteria are now defined in greater detail. The basic mechanical-design MVP is approximately 60% complete.

## Completed milestones

### M0 - Official foundation

- Pin official FreeCAD 1.1.1 source.
- Apply an isolated and idempotent Qt/C++ overlay.
- Build `FreeCADGui`, PartDesign, Sketcher and the FreeCAD executable.
- Preserve a Classic recovery mode.
- Package and install an Ubuntu 22.04 `.deb` in a clean container.

### M1 - Mechanical workspace foundation

- Tabbed mechanical ribbon.
- Global command search.
- Initial SolidFreeCAD color-vector icon system.
- Model-history panel and Property Manager.
- Sketch, Pad and Pocket selection/edit contracts.
- Automatic GUI screenshots and Xvfb smoke tests.

### M2 - Workspace and document controls

- Tabs displayed above command pages.
- Primary modeling commands highlighted.
- Dynamic workspace badge (`PIEZA`, `CROQUIS`, `ARCHIVO`, `SOLDADURA` and other environments).
- Active-document title and `NUEVO`/`GUARDADO` state.
- Native File workspace with New, Open, Save, Save As, Import, Export, project information, Print and Close.
- Start group for Body and Sketch creation.

## Current milestone - M3 Basic modeling MVP

The current objective is a reliable end-to-end workflow for ordinary mechanical parts.

### Required gates

- [x] Create a Body.
- [x] Create and edit a Sketch.
- [x] Create and edit a Pad.
- [x] Create and edit a Pocket.
- [x] Save and reopen FCStd without losing the validated solid.
- [x] Expose native document and interchange commands.
- [ ] Add guided Revolution parameters and regression geometry.
- [ ] Add Fillet and Chamfer edge-selection/property workflows.
- [ ] Validate Line, Circle, Centerpoint Slot and Smart Dimension style workflows.
- [ ] Add guided Linear Pattern and Mirror workflows.
- [ ] Add a controlled STEP export/import round-trip fixture.
- [ ] Replace the remaining floating Task strip with a safe context panel that preserves Sketcher editing.
- [ ] Complete color-vector icons for every enabled command in Archivo, Operaciones and Croquis.

## M4 - Professional interaction layer

This milestone incorporates the useful interaction concepts identified in the reviewed SOLIDWORKS 2025 tutorial without copying its artwork.

### Welcome and document creation

- [ ] Local Welcome center with Home, Recent, Learn and Recovery sections.
- [ ] Recent documents and folders with thumbnails, full path and last-saved information.
- [ ] New-document chooser for Part, Assembly and Drawing.
- [ ] Simple and advanced template modes.
- [ ] Local user template library and custom template locations.
- [ ] Y-up/Z-up orientation choice where technically compatible with FreeCAD.
- [ ] Document units, decimal precision, angular precision and drafting-standard presets.
- [ ] Document properties, custom properties, material selection and searchable local material library.

### Context-sensitive commands

- [ ] Context toolbar for selected bodies, faces, edges, vertices, sketches and features.
- [ ] Consolidated fly-out command groups that remember the last-used variant.
- [ ] Cursor feedback icons that indicate the expected selection type.
- [ ] Confirmation Corner with Accept, Cancel and Exit Sketch controls.
- [ ] Move Accept/Cancel controls near the pointer through an optional shortcut.
- [ ] Command-specific help and validation messages in the Property Manager.

### Heads-up view and graphics controls

- [ ] Floating heads-up view toolbar over the 3D viewport.
- [ ] Fit, zoom area, previous view and section-view commands.
- [ ] Front, Back, Left, Right, Top, Bottom, Isometric, Dimetric and Trimetric views.
- [ ] View selector/cube with live orientation feedback.
- [ ] Single, horizontal split, vertical split and four-view layouts.
- [ ] Wireframe, hidden-line, shaded and shaded-with-edges display styles.
- [ ] Hide/show reference items, named views, appearance and background controls.
- [ ] Configurable three-button mouse navigation and documented shortcuts.

### Model history and dependency navigation

- [ ] Rollback/timeline bar that temporarily suppresses later features without deleting them.
- [ ] Roll to previous, roll forward and roll to end actions.
- [ ] Parent/child dynamic-reference visualization in the model tree.
- [ ] Filter tree by feature type, name, sketch, folder, tag and custom property.
- [ ] User tags, collapse-all and synchronized tree/viewport selection.
- [ ] Split model tree and optional simultaneous Property Manager view.
- [ ] Configuration manager for controlled variants of a part or assembly.
- [ ] Display manager for visibility, appearance and display-state control.
- [ ] Lightweight sensors for dimensions, measurements, mass properties and geometry-health limits; no FEM data.

### Local task pane and learning

- [ ] Safe dockable Task Pane with local Design Library, File Explorer, View Palette, Appearances and Custom Properties.
- [ ] Context-sensitive local HTML help.
- [ ] Integrated tutorials and example projects.
- [ ] Recovery notices and diagnostics after an abnormal shutdown.
- [ ] Bilingual feature labels and optional translated names in the model tree.

## M5 - Robust FCStd and STEP compatibility

- Open representative FCStd files from Part Design, Assembly, TechDraw, Sheet Metal and welded-structure projects.
- Preserve unknown workbench data when saving.
- Detect partial restore and unsupported objects without destructive edits.
- Build STEP/STP import and export regression fixtures with geometry and volume checks.
- Add a compatibility report before saving over files created by a newer or unsupported feature set.
- Add local Pack-and-Go packaging for a document and its linked files.
- Add recent-file, autosave and session-recovery UX.

## M6 - Welded structures workspace

Yes, SolidFreeCAD can implement a guided welded-structure workflow similar in logic to professional Weldments tools while using FreeCAD/OpenCASCADE geometry and original SolidFreeCAD UI.

### Proposed user flow

1. Create a `Welded Structure` document or container.
2. Create or select a 2D/3D skeleton sketch containing the member centerlines.
3. Choose a profile standard, family, size and material from a local profile library.
4. Apply structural members to selected sketch segments with live preview.
5. Edit member alignment, rotation, insertion point, offset, group and corner treatment in the Property Manager.
6. Trim or extend intersections using miter, butt, overlap and cope/notch treatments.
7. Add gussets, end caps, base plates, stiffeners, holes, pockets and edge preparation.
8. Add symbolic or geometric weld beads with type, size, length, pitch and intermittent-weld metadata.
9. Generate and maintain an automatic cut list.
10. Produce drawings, balloons, bill of materials and CSV/DXF/STEP outputs.

### Required implementation gates

- [ ] `SolidWeldment` container and `StructuralMember` feature model.
- [ ] Local profile library for common metric and imperial structural sections plus user-defined profiles.
- [ ] Profile preview with colorful icons and section thumbnails.
- [ ] Sweep/member generation along straight and supported curved paths.
- [ ] Stable profile orientation and insertion-point rules.
- [ ] Member grouping and batch editing.
- [ ] Trim/extend engine with miter, butt, overlap and cope operations.
- [ ] Gusset, end-cap, base-plate and stiffener tools.
- [ ] Weld metadata and optional visual bead geometry; no weld-strength calculation.
- [ ] Automatic cut-list fields: item, profile, material, quantity, length, end angles, mass and custom properties.
- [ ] Validation for gaps, overlaps, duplicate members, zero-length members, missing profiles and untrimmed intersections.
- [ ] Property Manager preview with Accept/Cancel and selection filters.
- [ ] FCStd persistence and STEP export tests for complete welded frames.
- [ ] TechDraw cut-list and fabrication-drawing integration.
- [ ] Regression project: a small welded frame with at least two profile families, miters, base plates, gussets and an exported cut list.

### Technical direction

- Use Sketcher for the structural skeleton.
- Use existing FreeCAD Arch/BIM profile and frame capabilities where reliable.
- Use native Part/OpenCASCADE sweep, boolean and trimming operations for deterministic geometry.
- Store profile, member, cut-list and weld information as explicit document properties so it survives FCStd save/reopen.
- Keep every member editable and traceable to its source sketch segments rather than converting the frame into an opaque final solid.

## M7 - Assemblies, drawings and sheet metal

- Assembly constraints, component insertion and grounded/fixed states.
- Associative dimensions between parts, assemblies and drawings where FreeCAD APIs support them.
- TechDraw page, standard views, section views, dimensions, notes, balloons and BOM flow.
- View Palette style insertion of drawing views.
- Sheet Metal base, wall, bend, relief, unfold and refold workflows.
- Acceptance project based on a linkage: create several parts with Line, Circle, Slot, Smart Dimension, Pad, Pocket and Linear Pattern; assemble them and create a drawing.

## M8 - Macro and automation workspace

- Embedded macro editor.
- Run/stop controls and output console.
- Compatibility tests for `FreeCAD`, `Part` and selected Sketcher APIs.
- Local macro library and trusted-script warnings.
- Recordable command history suitable for converting repeated operations into a macro draft.

## M9 - Product release

- Signed packages and release channel.
- First-run onboarding and example projects.
- Crash recovery and session restore.
- Performance testing with large FCStd and STEP files.
- End-user documentation and acceptance tests.
- Visual regression tests that reject missing, monochrome or inconsistent production icons.