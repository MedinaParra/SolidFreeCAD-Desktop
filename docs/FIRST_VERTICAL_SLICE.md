# First Vertical Slice — Part → Sketch → Pad

## Goal

Deliver the first complete SolidFreeCAD modeling interaction without requiring the Classic interface.

## User story

A user can create a new part, select a principal plane, create a dimensioned rectangle, exit the sketch, create a pad with live preview, accept it, edit the pad from the model tree, save the document, close it and reopen it without data loss.

## Required GUI states

1. Empty application with contextual Start commands.
2. New Part document with model manager visible.
3. Origin group expanded with XY, XZ and YZ planes.
4. Plane selected and New Sketch available.
5. Sketch editing mode with sketch-specific command tab.
6. Rectangle geometry and dimension tools available.
7. Sketch status visible: under-defined, fully-defined or conflicting.
8. Exit Sketch action returns to Part Design context.
9. Pad command opens the property manager.
10. Live preview responds to length and direction changes.
11. Accept creates one Pad feature.
12. Double-clicking Pad reopens the same parameters.

## Reuse plan

- Official FreeCAD document and Body objects.
- Official TreeView with styling and context adapters.
- Official Sketcher edit mode and solver.
- Official Pad task panel wrapped in SolidFreeCAD property-manager presentation.
- Official transactions, undo and redo.
- Official FCStd persistence.

## Acceptance criteria

- No Classic menu or toolbar is required.
- All primary actions are reachable from the SolidFreeCAD shell.
- Cancel leaves no residual sketch or feature objects.
- Undo and redo work after sketch and pad creation.
- Saving and reopening preserves the Body, Sketch and Pad.
- The workflow has an automated script test.
- CI records screenshots for empty document, sketch edit and pad preview states.

## Deferred

- Advanced sketch entities.
- Expressions and spreadsheets.
- Multiple bodies.
- Additive loft and sweep.
- Topological naming recovery.
- Configurations.
- Assembly and TechDraw.
