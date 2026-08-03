# SolidFreeCAD alpha.10 native-binding maturity

## Objective

Alpha.10 moves the contextual interface from descriptive collectors toward native FreeCAD feature inputs. It remains source-only and never creates a second CAD model beside FCStd/OpenCASCADE.

## Implemented

- Reads the selected object and subelements through `Gui.Selection.getSelectionEx()`.
- Detects compatible `PropertyLink`, `PropertyLinkList`, `PropertyLinkSub` and `PropertyLinkSubList` properties.
- Provides role-specific capture for profile, axis, limiting face, edges and points.
- Refuses to write when the active feature does not expose a compatible native property.
- Reads end-condition enumerations from the active object's own `Type` property rather than hardcoding runtime indices.
- Uses document transactions for bindings and end-condition changes.
- Debounces preview recomputes to reduce repeated updates.
- Captures a conservative per-feature property snapshot and provides an explicit restore-session action.
- Reports whether the feature appears ready or still lacks required inputs.
- Preserves alpha.9, alpha.8 and earlier recovery paths.

## Safety boundaries

The binding adapter must not:

- invent properties that the native object does not expose;
- coerce unsupported property types;
- create duplicate geometry;
- claim that a binding succeeded after FreeCAD rejected it;
- replace native accept/cancel semantics;
- compile or package an executable.

## Runtime validation still required

FreeCAD 1.1.1 on Windows must confirm the exact value shapes accepted by:

- Pad/Pocket `Profile`;
- Revolution `ReferenceAxis` or runtime-equivalent axis property;
- Fillet/Chamfer `Base` edge lists;
- Hole profile and point inputs;
- `UpToFace` or runtime-equivalent limiting-face properties;
- enum assignment by label versus index.

## Physical workflow gate

The executable remains blocked until a real Windows run proves:

1. A closed sketch can be captured as Pad profile.
2. Pad end conditions change and preview correctly.
3. A second sketch can be captured as Pocket profile.
4. Revolution accepts a profile and selected axis.
5. Fillet and Chamfer accept one and multiple edges.
6. Limiting-face selection works where supported.
7. Restore-session returns the feature to the captured state.
8. Undo and Redo remain coherent after bindings.
9. FCStd save, close and reopen preserves all references.
10. STEP export/import and BRep validity show no regression.

## Next iteration

Alpha.11 should focus on workspace polish and operational reliability:

- persistent desktop/laptop layout presets;
- native error and warning diagnostics;
- command-availability auditing;
- shortcut conflict protection;
- recursive design-tree navigation and safe rename;
- theme/density adaptation;
- a source release-candidate checklist without packaging.
