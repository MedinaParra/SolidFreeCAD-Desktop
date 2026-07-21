# SolidFreeCAD Desktop roadmap

Updated: 2026-07-21

## Product scope

SolidFreeCAD Desktop is a local-first mechanical CAD application built on official FreeCAD 1.1.1 components. The intended product covers part design, sketches, assemblies, drawings, sheet metal, welded structures, FCStd/STEP interoperability and local macro automation.

The following areas are intentionally outside the current product scope:

- FEM, stress, thermal, fluid and motion simulation.
- Mesh generation, solver setup and simulation post-processing.
- Cloud-only 3DEXPERIENCE services.
- Licensed SOLIDWORKS-specific formats or behavior that cannot be reproduced safely with FreeCAD APIs.

The existing Simulation/FEM ribbon placeholder is scheduled for removal. Inspection in SolidFreeCAD means geometry, dimensions, mass properties, clearances, interferences and model-health checks, not engineering simulation.

## Visual design contract

- All primary SolidFreeCAD commands must use colorful, attractive and consistent vector icons.
- Monochrome placeholder icons are not accepted for enabled production commands.
- Disabled commands may use desaturated versions of the same icon.
- Icons must remain legible at 16, 24, 32 and 48 px and on light or dark backgrounds.
- Related commands must share a recognizable visual family while remaining distinguishable.
- The active command icon must communicate the expected click sequence or selection type whenever practical.
- Sketch status colors, inference guides, constraints and warning states must remain visually distinct.
- The interface may be inspired by professional mechanical CAD workflows, but must use original SolidFreeCAD artwork and naming.

## Overall progress

| Area | Progress | Current state |
| --- | ---: | --- |
| Reproducible FreeCAD 1.1.1 foundation | 90% | Overlay, CI, Ubuntu build, deb packaging, clean install and Classic recovery are operational. |
| SolidFreeCAD mechanical workspace | 55% | Tabbed ribbon, command search, initial colorful icons, model history, Property Manager and contextual workspace states are implemented. Welcome, context-command and heads-up interaction layers remain. |
| Basic Part Design workflow | 46% | Body, Sketch, Pad and Pocket are validated; the reviewed manuals add stricter requirements for sketch guidance, constraints, dimensions, status and repair. |
| File and interchange workflow | 45% | Native New/Open/Save/Save As/Import/Export commands are exposed; recent documents, templates and STEP round-trip fixtures remain. |
| FCStd compatibility and persistence | 42% | A Sketch -> Pad vertical slice is saved, reopened and volume-checked. Complex-workbench preservation fixtures remain. |
| Welded structures workflow | 15% | A ribbon placeholder exists, but structural-member, trim, cut-list and weld metadata logic are not yet implemented. |
| Assembly, TechDraw and Sheet Metal | 12% | Ribbon entry points exist, but production workflows, drawing-template editing and regression projects are still pending. |
| Macro and Python workflow | 20% | The official FreeCAD Python engine remains available; a controlled macro editor and compatibility suite are not implemented yet. |
| Product release and documentation | 28% | Installable Ubuntu development packages exist; updater, signed release, onboarding and user documentation remain. |

**Estimated complete product progress: 42%.**

The percentage remains unchanged after reviewing the SOLIDWORKS 2025 tutorial and the Easyworks good-practices manual because they validate the architecture but expand the acceptance criteria. The basic mechanical-design MVP is approximately 58% complete under the stricter sketch-quality definition.

## Feasibility validation from the reviewed manuals

The reviewed workflows are technically feasible with official FreeCAD 1.1.1 components plus the SolidFreeCAD Qt/C++ interaction layer.

### Already available in the underlying engine

- Sketches attached to reference planes or planar faces.
- Lines, circles, arcs, ellipses, splines, slots, polygons, rectangles, points and construction geometry.
- Geometric constraints, dimensional constraints and a parametric sketch solver.
- Trim, extend, external geometry, offset, symmetry and sketch transformations.
- Part Design features that consume sketches, including Pad and Pocket.
- TechDraw pages and SVG templates with editable text fields.
- FCStd persistence of sketches, constraints, features, document properties and TechDraw objects.

### SolidFreeCAD interaction work still required

- Guided plane/face selection before entering Sketcher.
- Cursor feedback and Property Manager warnings when the required support is missing.
- A clear active-sketch state, Confirmation Corner and automatic normal-to-sketch view.
- SolidFreeCAD-specific inference graphics, command-state feedback and sketch status presentation.
- Smart-dimension placement and a compact value editor with units and expressions.
- A friendly drawing-border/title-block editor over TechDraw SVG templates.
- Modifier-key workflows, configurable shortcuts and contextual drag-copy behavior.

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

## Current milestone - M3 Basic modeling and sketch-quality MVP

The current objective is a reliable end-to-end workflow for ordinary mechanical parts, with sketch behavior suitable for daily professional use.

### Existing vertical-slice gates

- [x] Create a Body.
- [x] Create and edit a Sketch.
- [x] Create and edit a Pad.
- [x] Create and edit a Pocket.
- [x] Save and reopen FCStd without losing the validated solid.
- [x] Expose native document and interchange commands.

### Sketch creation and active-mode gates

- [ ] Require or guide selection of Front/Top/Right plane, a datum plane or a planar face before sketch creation.
- [ ] Show a cursor-state icon and Property Manager message when no valid sketch support is selected.
- [ ] Automatically orient the camera normal to the sketch plane, with an option to disable this behavior.
- [ ] Align the visible coordinate indicator with the active sketch plane.
- [ ] Show an unambiguous `EDITANDO CROQUIS` state in the header/status area.
- [ ] Add a Confirmation Corner with Accept, Cancel and Exit Sketch controls.
- [ ] Ensure Esc exits the active drawing command without unexpectedly closing the sketch.

### Sketch geometry gates

- [ ] Validate line and connected polyline workflows using click-click and click-drag interaction.
- [ ] Support double-click to stop chained lines and Esc to cancel the current entity command.
- [ ] Validate midpoint line, center circle, three-point/perimeter circle and center/tangent/three-point arc variants.
- [ ] Validate ellipse, partial ellipse, spline, straight slot, centerpoint slot and polygon workflows.
- [ ] Validate corner, center and three-point rectangle variants.
- [ ] Validate point and construction-geometry creation.
- [ ] Complete colorful icons that visually distinguish geometry variants and expected point sequence.

### Relations, inference and sketch-state gates

- [ ] Show automatic horizontal, vertical, coincident, tangent and other inferred relations during creation.
- [ ] Draw inference guides separately from actual constraints so the user can distinguish suggestions from committed relations.
- [ ] Add manual relation controls for coincident, point-on-object, parallel, perpendicular, collinear, horizontal, vertical, equal, midpoint, tangent, concentric and symmetry constraints where supported.
- [ ] Show under-constrained, fully constrained and over-constrained/conflicting states in the Property Manager and model tree.
- [ ] Use configurable status colors and never rely on color alone; include text/icons for accessibility.
- [ ] Provide a relation inspector for dangling, redundant and conflicting constraints.
- [ ] Add repair actions that select the offending constraints before deletion or suppression.

### Smart dimension gates

- [ ] Infer radius/diameter, horizontal, vertical, aligned, distance and angular dimension types from the selected entities.
- [ ] Show a live dimension preview whose orientation follows the pointer.
- [ ] Allow placement rules comparable to centered placement and manually positioned text without copying proprietary UI.
- [ ] Open a compact dimension editor immediately after placement.
- [ ] Support explicit units, arithmetic expressions and simple equations in the value field.
- [ ] Provide Apply, Cancel, Recompute, sign reversal and configurable wheel-increment controls.
- [ ] Distinguish driving and reference dimensions.

### Sketch editing gates

- [ ] Add sketch fillet and sketch chamfer workflows.
- [ ] Validate trim modes, extend-to-nearest, external/converted geometry and offset geometry.
- [ ] Add mirror, move, rotate and scale selection workflows.
- [ ] Add guided linear and circular sketch patterns with instance count, spacing/angle and equal-spacing options.
- [ ] Add guided Revolution parameters and regression geometry.
- [ ] Add Part Design Fillet and Chamfer edge-selection/property workflows.
- [ ] Add a controlled STEP export/import round-trip fixture.
- [ ] Replace the remaining floating Task strip with a safe context panel that preserves Sketcher editing.
- [ ] Complete color-vector icons for every enabled command in Archivo, Operaciones and Croquis.

### Embedded good-practice validator

- [ ] Encourage simple sketches instead of one oversized sketch containing unrelated features.
- [ ] Encourage use of the origin or stable reference geometry.
- [ ] Guide the sequence: approximate contour -> geometric relations -> dimensions.
- [ ] Warn when geometry is drawn at an extreme scale relative to the intended dimensions.
- [ ] Suggest adding smaller controlling dimensions before large overall dimensions when this reduces solver instability.
- [ ] Warn before creating downstream features from an over-constrained or invalid sketch.
- [ ] Offer a non-blocking warning when a production feature depends on an under-constrained sketch.

## M4 - Professional interaction layer

This milestone incorporates useful interaction concepts identified in the reviewed manuals without copying their artwork.

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
- [ ] Optional Alt+arrow view rotation with a predictable angular increment.

### Model history and dependency navigation

- [ ] Rollback/timeline bar that temporarily suppresses later features without deleting them.
- [ ] Roll to previous, roll forward and roll to end actions.
- [ ] Parent/child dynamic-reference visualization in the model tree.
- [ ] Filter tree by feature type, name, sketch, folder, tag and custom property.
- [ ] User tags, collapse-all and synchronized tree/viewport selection.
- [ ] Split model tree and optional simultaneous Property Manager view.
- [ ] Configuration manager for controlled variants of a part or assembly.
- [ ] Display manager for visibility, appearance, feature-color classes and display-state control.
- [ ] Lightweight sensors for dimensions, measurements, mass properties and geometry-health limits; no FEM data.

### Productivity and modifier-key behavior

- [ ] Preserve standard configurable shortcuts for New, Open, Save, Undo, Redo, Fit and Cancel.
- [ ] Add a shortcut reference panel and user-editable key map with conflict detection.
- [ ] Support safe Ctrl-drag duplication for selected reference planes, features or components when dependency rules allow it.
- [ ] Support drag insertion of a chosen component configuration into an assembly.
- [ ] Add assembly drag modifiers for copy, rotate and context movement.
- [ ] Add annotation modifiers for breaking alignment, moving an annotation independently and creating extra leaders.
- [ ] Add drawing-view modifiers for breaking alignment and selecting overlapping collinear edges.
- [ ] Add reference relinking when opening an assembly or drawing with missing linked files.
- [ ] Add geometric interference detection for assemblies without invoking FEM.

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

### Assemblies

- [ ] Assembly constraints, component insertion and grounded/fixed states.
- [ ] Insert a selected part configuration/variant into an assembly.
- [ ] Drag-copy components with optional automatic joint creation where supported.
- [ ] Replace or relink referenced components without rebuilding the complete assembly.
- [ ] Interference detection and clearance inspection.

### Drawings and custom sheet formats

- [ ] TechDraw page, standard views, section views, dimensions, notes, balloons and BOM flow.
- [ ] View Palette style insertion of drawing views.
- [ ] New empty drawing workflow with ISO/ANSI sheet-size selection.
- [ ] Friendly editor for SVG-based TechDraw templates rather than requiring manual SVG source editing.
- [ ] Automatic border wizard with removable legacy border geometry.
- [ ] Configurable rows, columns, zone width and reference center based on sheet or margins.
- [ ] Configurable margins, line style, line weight, single/double border and independent-edge offsets.
- [ ] Masks for selected row/column labels and separators.
- [ ] Editable title-block sketch/grid using snapping, constraints and dimensions.
- [ ] Company logo insertion with preserved aspect ratio and embedded/linked asset options.
- [ ] Editable title-block fields for title, drawing number, revision, material, scale, author, date, client and custom properties.
- [ ] Property-linked fields that update from the source part/assembly where technically supported.
- [ ] Save custom formats as reusable local templates with preview thumbnails.
- [ ] Export drawing pages to PDF, SVG and DXF with visual regression tests.

### Sheet metal

- [ ] Sheet Metal base, wall, bend, relief, unfold and refold workflows.

### Acceptance project

- [ ] Create several parts with Line, Circle, Slot, Smart Dimension, Pad, Pocket and Linear Pattern.
- [ ] Assemble the parts and validate component references and interference inspection.
- [ ] Create a drawing using a custom A3 title block and company logo.
- [ ] Reopen the FCStd project and verify that geometry, constraints, linked properties, drawing format and annotations persist.

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
