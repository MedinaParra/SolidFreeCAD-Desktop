# SolidFreeCAD alpha.11 source release-candidate gate

## Purpose

Alpha.11 is the final planned source-only interface layer before a Windows runtime validation branch. It does not authorize an executable. Its purpose is to make the workspace coherent, observable and recoverable enough to justify a physical Windows test.

## Implemented

### Daily-use shell

- Original quick-access toolbar for New, Open, Save, Undo, Redo and Fit.
- Persistent workspace profiles for laptop, standard and wide displays.
- Persistent compact, normal and comfortable control density.
- System, light and dark visual modes using original SolidFreeCAD styling.
- Automatic switch to laptop layout on narrow windows.
- Workspace reset action.

### Verification tab

- Document diagnostics for unsaved files, object states, invalid BRep and underdefined sketches.
- Command coverage audit against the actual registered FreeCAD runtime.
- Functions absent from the runtime are shown as unavailable rather than complete.
- Safe visible-label rename through a document transaction.
- Manual physical-release checklist.

### Reliability

- Alpha.11 falls back to alpha.10, then to every earlier compatibility layer.
- Preferences are stored under SolidFreeCAD's own FreeCAD parameter group.
- Repeated refresh uses document signatures instead of rebuilding continuously.
- No package or executable workflow is introduced.

## Source RC is not runtime acceptance

A successful Python syntax check cannot prove:

- Qt layout behavior on Windows;
- correct native LinkSub value shapes;
- native task-dialog accept/cancel behavior;
- OpenGL selection and navigation;
- high-DPI icon and font legibility;
- long-session stability;
- FCStd/STEP/BRep regression safety.

## Required Windows validation branch

The next branch may build a disposable internal portable runtime solely for validation only after explicit authorization. It must not create a public release. The test must record:

1. A real 1920×1080 interface screenshot.
2. A real 1366×768 interface screenshot.
3. Scaling at 100%, 125%, 150% and 200%.
4. Complete Part → Sketch → Pad → Pocket → Revolution → Fillet → Chamfer flow.
5. Edit, accept, cancel, restore, Undo and Redo behavior.
6. Profile, axis, face and edge binding results.
7. Save, close and reopen of FCStd.
8. STEP round trip and BRep validity.
9. Command coverage report from the packaged runtime.
10. At least one extended interactive session on a physical Windows workstation.

## Conditions for creating the actual executable

Portable and installer builds intended for use remain blocked until:

- all essential commands required by the workflow are available;
- no binding writes incorrect native references;
- no blocking or high-severity diagnostic remains;
- accept/cancel semantics are confirmed physically;
- UI remains usable at all target resolutions and scales;
- FCStd and STEP regression checks pass;
- the user reviews the real interface and confirms it feels sufficiently mature;
- executable creation is requested as a separate, explicit step.
