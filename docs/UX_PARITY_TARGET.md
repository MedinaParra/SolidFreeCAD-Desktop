# SolidFreeCAD UX Parity Target

## Purpose

SolidFreeCAD must feel immediately familiar to users of mainstream mechanical parametric CAD while remaining an independent FreeCAD-based application.

The target is interaction parity, not visual or binary cloning. The application must reproduce the same mental model, task sequence, information hierarchy and response timing without copying proprietary logos, names, icons, artwork, source code or file formats.

## Permanent design rule

When choosing between:

1. rewriting a FreeCAD subsystem, or
2. adapting the official subsystem so that it behaves and appears consistently inside SolidFreeCAD,

prefer adaptation unless the official subsystem prevents the required workflow.

## Core workflow target

The first complete workflow is:

```text
New Part
→ Select plane
→ Create sketch
→ Add geometry
→ Add dimensions and relations
→ Confirm sketch
→ Create feature
→ Preview parameters
→ Accept feature
→ Edit feature from tree
→ Save and reopen
→ Insert into assembly
→ Add constraints
→ Create associated drawing
```

The introductory box-and-lid exercise is the first acceptance test for this workflow.

## What must feel familiar

### Application structure

- Compact quick-access row at the top.
- Context-sensitive tabbed command manager.
- Persistent model manager on the left.
- Property/task manager occupying the same left-side region.
- Large central graphics area.
- Minimal technical consoles during normal modeling.
- Search commands from the top-right area.

### Command behavior

- Commands are grouped by user task, not by internal FreeCAD module.
- Tabs change with document type and editing mode.
- Unavailable commands remain visually understandable and explain why they are disabled.
- Frequently used commands appear as large controls with text.
- Secondary commands use compact controls or overflow menus.

### Model tree

- Chronological feature history.
- Origin and principal planes grouped together.
- Active body and active feature clearly indicated.
- Double-click edits the selected feature.
- Right-click exposes context-relevant actions.
- Suppressed, hidden, failed and externally referenced objects have distinct states.
- Selection remains synchronized with the 3D view.

### Property manager

Every primary modeling operation must present a consistent panel with:

- operation title;
- accept and cancel controls;
- reference selections;
- grouped parameters;
- live preview;
- reversible transaction;
- concise validation errors;
- access to advanced parameters without overwhelming the initial view.

The official FreeCAD TaskView and task panels should be adapted before considering complete replacements.

### Sketch workflow

- Plane or planar face selection before sketch creation.
- Immediate normal-to-sketch view.
- Clear sketch-editing state.
- Dynamic geometric inference.
- Automatic constraints where appropriate.
- Single dimension workflow for common cases.
- Visible under-defined, fully-defined and conflicting states.
- Prominent exit-sketch action.
- Direct transition from a valid sketch to a feature command.

### Feature workflow

For Pad, Pocket, Revolution, Fillet, Chamfer and Thickness:

- one command opens one focused property panel;
- a preview appears before committing;
- manipulator handles may adjust primary values;
- accept creates one feature-tree item;
- cancel leaves no partial objects;
- double-click restores the same editor;
- dependencies and errors remain visible in the tree.

### Assembly workflow

- New assembly document.
- Insert existing components.
- First component can be fixed automatically.
- Move and rotate components directly.
- Create coincident, concentric, distance and angle constraints.
- Show constraint state and unresolved degrees of freedom.
- Edit a component without losing assembly context.

### Drawing workflow

- New drawing from a model or assembly.
- Template selection.
- Base view and projected views.
- Isometric, section and detail views.
- Dimensions and annotations.
- Model changes propagate to the drawing.
- PDF and DXF export remain straightforward.

## What must not be copied

- Proprietary logos or product names.
- Proprietary icon artwork.
- Proprietary source code.
- Proprietary file-format implementations obtained through reverse engineering that violates licenses or agreements.
- Exact pixel-for-pixel replication when an independent visual solution communicates the same workflow.

SolidFreeCAD should use its own name, iconography, color system and visual details.

## Development acceleration policy

### Reuse first

- Reuse the official FreeCAD document model.
- Reuse TreeView through styling, proxy models and context actions.
- Reuse TaskView through wrappers and consistent presentation.
- Reuse Sketcher solving and constraints.
- Reuse Part Design operations.
- Reuse Assembly and TechDraw.

### Prototype before compiling

New workflows should be prototyped through Python commands and macros when possible. Move logic to C++ only when it must integrate with startup, widget lifecycle, performance-critical behavior or official command registration.

### Vertical slices

Each milestone must deliver a complete user action rather than a broad collection of disconnected controls.

Preferred sequence:

1. clean shell;
2. new part;
3. plane selection;
4. rectangle sketch;
5. dimensioned sketch;
6. pad preview and commit;
7. edit pad;
8. pocket;
9. shell;
10. save and reopen;
11. box-and-lid assembly;
12. associated drawing.

## Definition of done for interaction parity

A workflow is considered complete only when:

- it can be executed without opening the Classic interface;
- the relevant command appears in the expected contextual tab;
- the left manager clearly shows the current document state;
- accept, cancel and undo behave correctly;
- failed inputs produce understandable feedback;
- the resulting FCStd file opens again without data loss;
- an automated smoke test covers the main path;
- a screenshot demonstrates the intended visual hierarchy.

## Current priority

Until the box-and-lid lesson is complete, the project will not prioritize advanced sheet metal, weldments, surfaces, FEM, animation, large-assembly optimization or proprietary format compatibility.

The immediate priority remains:

```text
Clean GUI
→ Feature tree
→ Property manager
→ Sketch
→ Pad
→ Pocket
→ Thickness
→ Box and lid
```
