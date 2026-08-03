# SolidFreeCAD alpha.9 feature-manager maturity

## Objective

Alpha.9 reduces the gap between a generic FreeCAD task panel and a guided professional mechanical-CAD workflow. It remains an original SolidFreeCAD interface and uses only native FreeCAD properties, commands and document transactions.

## Implemented

### Dedicated feature profiles

The contextual operation pane recognizes and presents focused definitions for:

- Pad / Saliente;
- Pocket / Corte;
- Revolution / Revolución;
- Fillet / Redondeo;
- Chamfer / Chaflán;
- Hole / Taladro;
- Sketch / Croquis.

Each profile exposes only properties that actually exist on the selected native object. Missing properties do not create fake controls.

### Selection collector

- Shows selected objects, faces, edges and vertices.
- Provides clear operation-specific selection guidance.
- Allows refreshing or clearing the current selection.
- Does not manufacture unsupported FreeCAD references.

### Sketch definition panel

- Shows fully defined or remaining degrees of freedom when available.
- Exposes native line, rectangle, circle, dimension, horizontal and vertical commands.
- Disables commands not registered by the pinned runtime.

### Design-tree state

The FeatureManager now displays two columns:

- Design object;
- State.

It marks:

- the active Body tip;
- hidden objects;
- fully defined or underdefined sketches;
- invalid BRep objects;
- bodies and general operations.

### Selection and view tools

- Optional native selection gates for faces, edges, vertices and bodies.
- Original compact orientation overlay for top, front, right, isometric and fit.
- Safe fallback to automatic selection when a gate is unavailable.

## Source-only boundary

Alpha.9 does not:

- compile FreeCAD;
- generate an executable;
- create a portable archive;
- create an installer;
- upload GitHub Actions artifacts;
- modify previous validated packaging scripts.

The alpha.9 workflow compiles Python syntax and verifies this boundary only.

## Remaining interface gaps

### Native preview and transaction semantics

- Verify that each feature editor updates the native preview exactly once.
- Distinguish native accept and cancel semantics for every task dialog.
- Confirm that cancelling restores pre-edit geometry and selections.
- Prevent recursive updates when FreeCAD changes a property programmatically.

### Selection collectors

- Bind profile selection lists to native LinkSub / LinkSubList properties.
- Support profile, axis, direction, face, edge and body collectors separately.
- Highlight which collector is currently active.
- Preserve selection when switching between parameter fields.

### End conditions

- Translate and validate Pad/Pocket end conditions from the pinned runtime.
- Support dimension, through-all, up-to-face, two-length and symmetric modes.
- Show only controls relevant to the chosen condition.

### Sketch experience

- Confirm native command identifiers on Windows FreeCAD 1.1.1.
- Show overconstrained and conflicting constraints distinctly.
- Add relation inference feedback without replacing Sketcher.
- Keep the `S` palette and keyboard shortcuts from stealing text input.

### Tree experience

- Add recursive nested Part and Body hierarchy.
- Represent rollback, suppression and external references when supported.
- Add safe rename and parent navigation.
- Verify that tree refresh never interrupts inline editing.

### Physical Windows review

Before an executable, the following must be performed on a real Windows workstation:

1. Create Part and Body.
2. Create and fully define a sketch.
3. Create and edit Pad.
4. Create and edit Pocket.
5. Create Revolution using a selected axis.
6. Create Fillet and Chamfer from selected edges.
7. Save FCStd, close and reopen.
8. Export and reimport STEP.
9. Undo and redo parameter changes.
10. Repeat at 100%, 125%, 150% and 200% Windows scaling.

## Packaging gate

Portable and installer builds remain prohibited until:

- all feature profiles work on native operations;
- selection collectors write correct references;
- accept/cancel behavior is confirmed;
- the complete physical workflow succeeds repeatedly;
- a real Windows screenshot is reviewed;
- no blocking or high-severity UI defects remain.
