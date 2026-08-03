# SolidFreeCAD Desktop

SolidFreeCAD Desktop is a mechanical-design interface built on the official FreeCAD engine. It preserves native FCStd documents, OpenCASCADE geometry, Part Design, Sketcher, TechDraw, FEM, Python and the classic FreeCAD interface while presenting a more integrated task-oriented workflow.

## Current development track

**Windows x64 is the current product priority.** Ubuntu remains an official future target and shared CAD/UI code stays platform-neutral.

Current source prototype: **0.1.0-alpha.10-native-bindings**

Alpha.10 remains intentionally **source only**. It does not publish a portable archive, Setup.exe or any executable. Packaging resumes only after the complete modeling workflow passes physical Windows review.

## Alpha.10 native-binding prototype

Alpha.10 builds on the dedicated alpha.9 PropertyManagers and connects compatible geometric selections to real native feature properties:

- selection capture through `Gui.Selection.getSelectionEx()`;
- safe detection of native Link, LinkList, LinkSub and LinkSubList properties;
- role-specific capture for profiles, axes, limiting faces, edges and points;
- refusal to write when the active object exposes no compatible native property;
- end-condition choices read from the object's own native enumeration;
- document transactions for binding and condition changes;
- debounced recomputation for preview stability;
- conservative feature-session snapshots with explicit restore action;
- readiness feedback showing missing profile, axis or edge inputs;
- safe fallback from alpha.10 to alpha.9 and all earlier source shells.

All changes continue to edit native FreeCAD objects. SolidFreeCAD does not create a parallel geometry or document model.

## Preserved interface foundation

- dedicated panels for Pad, Pocket, Revolution, Fillet, Chamfer, Hole and Sketch;
- edit-session awareness and floating confirmation corner;
- hierarchical FeatureManager and synchronized 3D selection;
- model and BRep state feedback;
- contextual CommandManager switching and `S` shortcut palette;
- original orientation and display controls;
- adaptive desktop/laptop layout;
- native FCStd, Part Design, Sketcher and OpenCASCADE geometry.

Unavailable or incompatible operations remain disabled or report the native limitation rather than pretending to work.

## Original identity and compatibility

The project adopts established interaction patterns common to professional mechanical CAD so experienced users can work quickly. It does not bundle or copy proprietary SolidWorks source code, icons, logos, trademarks or exact artwork. All SolidFreeCAD visual resources are original.

## Source-only validation

The workflow `.github/workflows/alpha10-source-validation.yml` performs only:

- Python syntax compilation;
- compatibility-chain checks;
- native-binding contract marker checks;
- verification that alpha.10 contains no installer or portable packaging commands.

It does not compile FreeCAD, upload an artifact or generate an executable.

Manual graphical contract:

```text
tests/solidfreecad_alpha10_gui_smoke.py
```

Maturity criteria and runtime gaps:

```text
docs/alpha10-native-binding-maturity.md
```

## Executable release gate

A Windows executable remains blocked until physical tests confirm:

1. `Part → Sketch → Pad → Edit → Pocket → Revolution → Fillet → Chamfer → Save → Reopen` works end to end.
2. Profile, axis, face and edge collectors write the exact native references expected by FreeCAD 1.1.1.
3. End conditions update native preview and geometry without duplicate recomputes.
4. Accept, cancel, restore-session, Undo and Redo remain coherent.
5. Tree, selection, Body tip and sketch status remain synchronized.
6. Layout works at 1366×768, 1920×1080 and high DPI.
7. Windows scaling works at 100%, 125%, 150% and 200%.
8. FCStd, STEP and BRep behavior show no regression.
9. A real interface screenshot and an extended Windows modeling session are reviewed.

Only after those gates pass will portable and installable builds be created in a separate iteration.

## Repository layout

```text
.github/workflows/        Source validation and previous validated build tracks
docs/                     Architecture, interface gates and integration contracts
overlay/Mod/SolidFreeCAD/ Shared SolidFreeCAD workbench and GUI overlay
platform/windows/         Windows packaging notes
platform/ubuntu/          Preserved Ubuntu target
scripts/windows/          Existing Windows build and packaging scripts
tests/                    Headless and graphical validation
```

## Foundation

- Official upstream: `FreeCAD/FreeCAD`
- Pinned source tag: `1.1.1`
- GUI: Qt/Python overlay plus native FreeCAD commands
- CAD kernel: official FreeCAD/OpenCASCADE runtime
- Primary platform: Windows x64
- Future platform: Ubuntu Linux x86-64

## License

See the repository license and third-party notices. SolidFreeCAD must remain compatible with the licenses of FreeCAD, Qt, OpenCASCADE, Python and the packaged dependencies.
