# Changelog

## 0.1.0-alpha.14-interactive-acceptance

- Added a guided physical-acceptance page inside the Verification panel.
- Added conservative detection for Body, Sketch, Pad, Pad edit mode, Pocket, Revolution, Fillet and Chamfer.
- Added saved-FCStd path capture and close/reopen verification.
- Added explicit manual evidence for Undo/Redo, Windows scaling and long-session stability.
- Added per-step interface screenshots and native document snapshots.
- Added object type, visibility, BRep validity, volume and 3D selection evidence.
- Added passed, failed and pending state management for every acceptance step.
- Added a structured local acceptance JSON report.
- Added alpha.14 fallback to alpha.13.
- Added a graphical contract and source-only validation workflow.
- Did not build, package, upload or publish a SolidFreeCAD executable.

## 0.1.0-alpha.13-runtime-stabilization

- Raised the supported Windows validation baseline to official FreeCAD 1.1.3.
- Replaced the expiring internal runtime-artifact dependency with dynamic official release discovery.
- Added official asset name and SHA-256 runtime provenance.
- Added exact-one-instance checks for critical SolidFreeCAD widgets.
- Added blocking critical-command coverage and warning-level secondary coverage.
- Added persisted layout, density and theme validation.
- Added automated 1366×768 and 1920×1080 accessibility checks.
- Added isolated native transaction, Undo and Redo verification.
- Added FCStd transaction persistence and active-document restoration checks.
- Added the alpha.13 Stability page and structured JSON report.
- Added a Windows evidence workflow that rejects executable distribution outputs.
- Added alpha.13 fallback to alpha.12.
- Did not build, package or publish a SolidFreeCAD executable.

## 0.1.0-alpha.12-runtime-preflight-source

- Added a local Preflight page inside the Verification panel.
- Added interface widget and window-scale evidence checks.
- Added essential runtime command coverage checks.
- Added local interface screenshot capture.
- Added isolated native BRep creation and validation.
- Added FCStd save, close, reopen and volume comparison.
- Added STEP export, import and shape validation.
- Added structured local JSON report and temporary evidence folder.
- Added a Windows CI preflight that reuses an existing runtime without compiling or packaging.
- Added a binary-output rejection gate and non-executable evidence artifact.
- Added alpha.12 fallback to alpha.11.
- Did not compile, package, upload or publish any Windows executable.

## 0.1.0-alpha.11-workspace-rc

- Added original quick-access toolbar for essential document and view actions.
- Added persistent laptop, standard and wide workspace profiles.
- Added persistent UI density and system/light/dark modes.
- Added automatic narrow-window adaptation and workspace reset.
- Added document diagnostics for unsaved files, invalid BRep and underdefined sketches.
- Added runtime command-coverage auditing.
- Added safe visible-label rename through a document transaction.
- Added a manual physical-release checklist and source-RC gate.
- Added alpha.11 fallback to alpha.10.
- Did not compile, package or publish any Windows executable.

## 0.1.0-alpha.10-native-bindings

- Added safe native Link, LinkList, LinkSub and LinkSubList detection.
- Added role-specific capture for profiles, axes, limiting faces, edges and points.
- Added runtime-derived end-condition enumerations.
- Added debounced preview recomputation.
- Added conservative feature-session snapshots and explicit restore.
- Added operation readiness feedback for missing inputs.
- Added alpha.10 fallback to alpha.9.
- Added manual GUI contract and source-only validation.
- Did not compile, package or publish any Windows executable.

## 0.1.0-alpha.9-feature-managers

- Added dedicated profiles for Pad, Pocket, Revolution, Fillet, Chamfer, Hole and Sketch.
- Added native-property-only controls and operation-specific instructions.
- Added a geometric selection collector with refresh and clear actions.
- Added sketch geometry, dimension and relation commands to the contextual panel.
- Added two-column FeatureManager design/state presentation.
- Added Body tip, hidden, sketch-definition and invalid-BRep states.
- Added optional native selection gates for faces, edges, vertices and bodies.
- Added an original compact orientation overlay.
- Added an alpha.9 compatibility fallback to alpha.8.
- Added a manual alpha.9 GUI contract test and source-only syntax validation.
- Did not compile, package or publish any Windows executable.

## 0.1.0-alpha.8-interaction

- Added native edit-session detection for sketches and features.
- Added a floating confirmation corner in the graphics area.
- Added a contextual Operation tab with native property editors.
- Added sketch degree-of-freedom feedback when available.
- Replaced the flat design list with a hierarchical native-object tree.
- Added synchronized FeatureManager and 3D selection.
- Added hidden-object and invalid-BRep visual feedback.
- Added context-aware CommandManager tab switching.
- Added the `S` shortcut palette for sketch and feature commands.
- Added shaded-with-edges, shaded and wireframe controls.
- Added standard orientation controls and adaptive dock sizing.
- Added a safe alpha.7 recovery loader.
- Added a manual alpha.8 GUI contract test and source-only validation workflow.
- Did not compile, package or publish any Windows executable.

## 0.1.0-alpha.7-interface

- Added a source-only professional mechanical-CAD interface layer.
- Added active-document context strip, breadcrumb and model/BRep state.
- Added curated command search with `Ctrl+K`.
- Added a dockable right task pane with Tasks, Library, Appearances and Resources.
- Added common native numeric-property editing inside FreeCAD transactions.
- Added selection edit, visibility, zoom and recompute actions.
- Added shape color and transparency controls.
- Added safe FeatureManager tree context actions.
- Added a manual GUI contract test and a physical Windows acceptance gate.
- Did not add or publish portable, installer or executable artifacts.

## 0.1.0-alpha.6

- Added integrated FeatureManager, PropertyManager and configurations tabs.
- Added compact Heads-Up view toolbar.
- Extended CommandManager with sheet-metal and assembly foundations.
- Added parametric demonstration plate with through-hole and pocket.
- Added end-to-end BRep, parameter edit, FCStd save/reopen and STEP export test.
- Added automated Windows interface screenshot artifact.
- Added application-mother metadata schema and example.
- Preserved the native FreeCAD engine, FCStd format and classic compatibility path.
- Continued using original SolidFreeCAD icon resources only.
