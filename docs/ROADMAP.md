# SolidFreeCAD Desktop — Workflow Roadmap

Updated: 2026-07-20

## Product target

SolidFreeCAD Desktop will provide a mechanical CAD workflow built on official FreeCAD 1.1.1 components, with an independent Qt/C++ user experience organized around the same mental model used by mainstream parametric CAD systems:

1. Create or open a document.
2. Select a plane or planar face.
3. Create and fully constrain a sketch.
4. Create parametric features from the sketch.
5. Edit features from a chronological model tree.
6. Assemble components with joints or constraints.
7. Generate associated technical drawings.
8. Propagate model changes to assemblies and drawings.

The target is workflow equivalence and professional usability. Proprietary logos, icons, file formats, artwork and implementation details are outside the scope.

## Current baseline

Status: **compiled foundation, GUI validation in progress**

Completed:

- Official `FreeCAD/FreeCAD` source pinned to tag `1.1.1`.
- Reproducible source overlay and narrow integration hooks.
- Ubuntu 22.04 CMake configuration.
- Successful compilation of `FreeCADGui`.
- Successful compilation of `PartDesignGui` and `SketcherGui`.
- Successful compilation and linkage of the FreeCAD executable.
- Ubuntu 22.04 compatibility patch for system OCCT 7.5.
- Persistent compiler cache.
- Classic recovery mode.
- Global command search.
- Tabbed mechanical Command Manager prototype.
- Initial Part Design, Sketcher, Assembly, TechDraw and FEM command catalogue.

Current blocker:

- The latest automated GUI smoke test fails after compilation. The binary and mechanical modules build correctly; the next iteration must diagnose the runtime validation failure and publish a clean screenshot.

## Delivery assumptions

The schedule below assumes:

- AI-assisted implementation continues at the current iteration rate.
- The user provides rapid visual and workflow feedback.
- GitHub Actions remains available for Ubuntu builds.
- The first supported platform remains Ubuntu x86-64.
- We reuse FreeCAD's official geometry, document, viewer and workbench engines instead of rewriting them.
- Scope changes are added only after the current milestone is accepted.

The dates are target ranges, not guarantees. CAD interaction work becomes slower as more edit states, selections and edge cases are added.

---

## Phase 0 — Stable GUI shell and development build

Target window: **2026-07-20 to 2026-07-27**

Goals:

- Fix the Xvfb GUI smoke-test failure.
- Produce a clean 1720×900 screenshot.
- Hide legacy menus, toolbars and report docks in SolidFreeCAD mode.
- Keep Classic mode fully recoverable.
- Load Part Design and Sketcher commands with native icons.
- Generate the first runnable Ubuntu development archive.

Acceptance criteria:

- Application starts under Xvfb and on a normal Ubuntu desktop.
- SolidFreeCAD shell is visible and Classic chrome is hidden.
- Part Design workbench loads.
- Classic recovery mode starts without the custom shell.
- Build artifact opens on a second Ubuntu installation.

Expected result: **visual alpha**.

## Phase 1 — Context-sensitive Command Manager

Target window: **2026-07-27 to 2026-08-09**

Goals:

- Replace static command pages with document-aware pages.
- Detect Part, Assembly, Drawing, Sketch edit and FEM contexts.
- Add large primary commands and compact secondary commands.
- Add tooltips, disabled-state explanations and command search integration.
- Persist user ribbon customization.
- Add the keyboard shortcut palette and initial contextual mini-toolbar.

Acceptance criteria:

- Opening a Part, Assembly or Drawing changes available tabs automatically.
- Entering Sketch edit mode switches to sketch-specific tools.
- Leaving edit mode restores feature tools.
- Ribbon state survives restart.

Expected result: **professional navigation shell**.

## Phase 2 — FeatureManager-style model panel

Target window: **2026-08-03 to 2026-08-23**

Goals:

- Restyle and reorganize the official model tree.
- Show document, Body, Origin, planes, sketches and features consistently.
- Add active-feature highlighting.
- Add suppressed, hidden, warning and failed-feature states.
- Add tree filtering and command search.
- Add contextual actions for rename, edit, suppress, delete and visibility.

Acceptance criteria:

- Selecting a tree item selects the same object in the viewer.
- Selecting geometry highlights the corresponding tree object where possible.
- Double-click edits supported sketches and features.
- Failed recomputes are visible without opening the report console.

Expected result: **usable chronological model history**.

## Phase 3 — PropertyManager and feature transactions

Target window: **2026-08-17 to 2026-09-13**

Goals:

- Convert FreeCAD TaskView into a consistent operation editor.
- Standardize Accept, Cancel, Preview and Help controls.
- Provide selectors for profiles, faces, axes and reference geometry.
- Provide live numeric fields with units.
- Add reversible preview transactions.
- Add common controls for direction, symmetric extent, reversed direction and merge result.

First supported operations:

- Body.
- New Sketch.
- Pad.
- Pocket.
- Revolution.
- Groove.
- Fillet.
- Chamfer.
- Thickness/Shell.
- Linear and polar patterns.

Acceptance criteria:

- Starting an operation opens the Property panel.
- Parameter changes update the preview.
- Cancel leaves no document residue.
- Accept creates one valid parametric feature.
- Editing an existing feature reopens the same parameters.

Expected result: **first complete modeling workflow**.

## Phase 4 — Sketch workflow parity

Target window: **2026-08-24 to 2026-09-20**

Goals:

- Plane or planar-face selection workflow.
- Sketch creation and orientation.
- Rectangle, line, circle, arc, slot and construction geometry.
- Smart dimension workflow.
- Coincident, horizontal, vertical, parallel, perpendicular, tangent, equal and symmetry constraints.
- Clear under-constrained, fully constrained and over-constrained states.
- Context-sensitive cursor and inference feedback.
- Escape, Accept and Cancel behavior consistent across tools.

Acceptance criteria:

- A new user can create a dimensioned rectangle without using Classic mode.
- The solver state is always visible.
- Conflicting constraints are identifiable and removable.
- A fully constrained sketch can drive Pad and Pocket.

Expected result: **sketch-to-solid alpha**.

## Phase 5 — Manual lesson acceptance test: box and lid

Target window: **2026-09-07 to 2026-09-27**

The introductory manual's box lesson becomes the first product acceptance test.

Required workflow:

1. Create a new part.
2. Set units.
3. Select a base plane.
4. Sketch and dimension a rectangle.
5. Pad the sketch.
6. Shell the solid.
7. Save the box.
8. Create and save a lid using the same workflow.
9. Reopen both documents and preserve parametric history.

Acceptance criteria:

- The complete exercise is performed without Classic mode.
- Every operation is editable from the model tree.
- Changing dimensions recomputes the final geometry.
- Save, close and reopen preserves the model.

Expected result: **SolidFreeCAD Modeling MVP**.

## Phase 6 — Assembly workflow

Target window: **2026-09-21 to 2026-10-25**

Goals:

- New Assembly document.
- Insert existing components.
- Fix and unfix a component.
- Move and rotate components.
- Coincident, concentric, distance, angle and fixed joints.
- Component tree and joint folder.
- Hide, isolate and show components.
- Basic interference or collision check.
- Exploded view foundation.

Acceptance criteria:

- Insert the box and lid.
- Reposition the lid interactively.
- Constrain the two parts predictably.
- Save and reopen the assembly.
- Changes to a referenced part update the assembly.

Expected result: **SolidFreeCAD Assembly MVP**.

## Phase 7 — Drawing workflow

Target window: **2026-10-12 to 2026-11-15**

Goals:

- New Drawing wizard.
- ISO A4/A3 templates.
- Base, projected and isometric views.
- Section and detail views.
- Dimensions and annotations.
- Basic title-block editing.
- PDF and DXF export.
- Assembly BOM and balloons foundation.

Acceptance criteria:

- Generate three standard views and one isometric view of the box.
- Add dimensions.
- Export a readable PDF.
- Modify the box and update drawing views.

Expected result: **end-to-end manual lesson completed**.

## Phase 8 — Configurations and design variants

Target window: **2026-11-02 to 2026-12-13**

Goals:

- Configuration table tied to named parameters.
- Feature suppression by configuration.
- Part and assembly variants.
- Display states.
- Basic design-table import/export using CSV.

Acceptance criteria:

- One document produces at least three dimensional variants.
- Switching configuration recomputes predictably.
- Assembly references a selected component configuration.

Expected result: **engineering beta**.

## Phase 9 — Workshop beta

Target window: **2026-12-01 to 2027-01-31**

Goals:

- STEP, IGES, BREP, STL and FCStd regression suite.
- Autosave and crash recovery.
- Recent files and welcome screen.
- Selection filters and Select Other.
- Custom shortcuts and mouse gestures.
- Measurement and inspection tools.
- Basic FEM study launcher.
- Installer or AppImage.
- User-visible error reporting.

Acceptance criteria:

- Daily modeling use without Classic mode for the supported workflow.
- No data loss across the regression suite.
- Installation on a clean Ubuntu workstation.
- At least ten real mechanical parts validated.

Expected result: **public beta suitable for controlled workshop use**.

## Phase 10 — Version 1.0

Target window: **2027-02-01 to 2027-04-30**

Goals:

- Stabilize part, assembly and drawing workflows.
- Resolve high-priority crashes and data-loss defects.
- Complete packaging, upgrade and uninstall behavior.
- Performance profiling on medium assemblies.
- Documentation and integrated tutorials.
- Accessibility and high-DPI review.
- Licensing and attribution review.

Acceptance criteria:

- Repeatable release build.
- Supported workflow documented and tested.
- No known critical data-loss issue.
- Part → Assembly → Drawing tutorial passes automatically and manually.

Expected result: **SolidFreeCAD Desktop 1.0**.

---

## Delivery forecast at the current velocity

### Earliest useful builds

- Clean GUI alpha: **within 1 week**.
- Sketch → Pad → Pocket modeling demo: **3 to 5 weeks**.
- Box and lid Modeling MVP: **7 to 10 weeks**.
- Box/lid Assembly and associated Drawing: **12 to 17 weeks**.
- Controlled workshop beta: **5 to 7 months**.
- Stable 1.0 release: **7 to 10 months**.

### Confidence

- GUI alpha: high confidence.
- Modeling MVP: medium-high confidence.
- Assembly and Drawing MVP: medium confidence.
- Workshop beta: medium confidence.
- 1.0 date: low-to-medium confidence until real users complete the acceptance workflow.

## Critical path

The project should not broaden into every FreeCAD workbench yet. The shortest path to a useful product is:

1. Stable runtime and screenshot.
2. Context-aware ribbon.
3. Model tree.
4. Property panel and transactions.
5. Sketch workflow.
6. Core Part Design operations.
7. Box/lid acceptance test.
8. Assembly.
9. Drawing.
10. Packaging and real-user validation.

## Scope controls

Deferred until after the Modeling MVP:

- Full sheet-metal parity.
- Advanced weldments.
- Advanced surfacing.
- Feature recognition from imported STEP.
- Motion simulation.
- Advanced nonlinear FEM.
- Native proprietary CAD file writing.
- Windows and macOS packaging.

## Definition of project success

SolidFreeCAD Desktop is successful when a new mechanical designer can complete the full Part → Assembly → Drawing lesson using only the SolidFreeCAD interface, understand the model history, edit parameters safely, and reopen the resulting FCStd documents without data loss.
