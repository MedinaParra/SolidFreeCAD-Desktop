# SolidFreeCAD alpha.8 interaction maturity

## Goal

Alpha.8 moves the project from a static CAD shell toward an interface that feels natural to an experienced mechanical designer. The goal is familiar speed, hierarchy and feedback while preserving an original identity and using only native FreeCAD/OpenCASCADE operations.

It does not copy proprietary source code, trademarks, icons, artwork or protected screen assets.

## Added interaction layers

1. **Edit-state awareness**
   - Detects active sketch and feature editing.
   - Changes the active CommandManager context.
   - Reports sketch degrees of freedom when the runtime exposes them.

2. **Confirmation corner**
   - Floating accept and close controls inside the graphics area.
   - Visible only during a native edit session.
   - Delegates completion to FreeCAD rather than creating parallel geometry.

3. **Contextual operation page**
   - Inserted as the first tab in the right task pane.
   - Displays current selection and edit state.
   - Edits common native length, angle, float, integer, boolean and enumeration properties.
   - Uses document transactions, recompute and abort on failure.

4. **Hierarchical design history**
   - Replaces the earlier flat object list.
   - Groups bodies, parts, sketches, features, references and loose objects.
   - Synchronizes tree selection with the 3D model.
   - Preserves expanded nodes and identifies hidden or invalid objects.

5. **Shortcut palette**
   - Opens with `S` when text editing is not active.
   - Shows sketch commands while sketching and feature commands otherwise.
   - Enables only commands present in the current FreeCAD runtime.

6. **Display and orientation controls**
   - Shaded with edges, shaded and wireframe modes.
   - Isometric, front, top, right and fit actions.

7. **Adaptive layout**
   - Keeps both side panels on large displays.
   - Reduces dock widths on standard laptops.
   - Hides the secondary task pane on narrow windows when no edit is active.

## Source-only rule

This branch must not:

- add a GitHub Actions packaging workflow;
- publish a portable archive;
- generate a Setup executable;
- modify the validated alpha.6 packaging scripts;
- claim visual acceptance without a real Windows screenshot and physical use.

## Remaining gaps before an executable

### Sketch workflow

- Verify native line, rectangle, circle and constraint command identifiers on the pinned Windows runtime.
- Keep the operation page synchronized while adding and deleting sketch geometry.
- Confirm that `Esc`, `S`, `F` and `Ctrl+S` do not interfere with native edit tools.
- Add a reliable normal-to-selected-face action.
- Test fully defined, underdefined and overconstrained states.

### Feature PropertyManagers

- Build dedicated layouts for Pad, Pocket, Revolution, Fillet, Chamfer and Hole.
- Support selection collectors for profiles, directions, axes, edges and faces.
- Distinguish accept from cancel through the native task-dialog transaction.
- Provide stable preview updates without creating duplicate recomputes.

### Design tree

- Represent nested App::Part and PartDesign::Body structures recursively.
- Show rollback/tip state, suppressed features, errors and external references.
- Add safe rename, reorder and parent-navigation behavior.
- Avoid conflicts with the classic FreeCAD tree when compatibility mode is restored.

### Graphics area

- Add view-orientation overlay and selection breadcrumbs without obscuring geometry.
- Add section-view controls only when backed by a native command.
- Test selection filters for vertices, edges, faces, bodies and components.

### Windows physical acceptance

The first executable remains blocked until all of these pass:

- Windows 10 and Windows 11;
- 1366×768, 1920×1080 and a high-DPI display;
- 100%, 125%, 150% and 200% scaling;
- mouse and touchpad navigation;
- single and multiple monitors;
- light and dark Windows themes;
- long sketch and feature editing sessions;
- multi-document switching;
- FCStd save, close and reopen;
- STEP import/export;
- no BRep regression;
- no inaccessible accept/cancel controls;
- no shortcut capture inside text and numeric fields.

## Release decision

An executable may be created only after:

1. the interface screenshot is visually reviewed;
2. the complete `Part → Sketch → Pad → Edit → Pocket → Fillet → Save → Reopen` flow is performed physically;
3. no blocking interface defect remains;
4. native files and geometry remain valid;
5. portable and installer packaging are explicitly authorized as a separate iteration.
