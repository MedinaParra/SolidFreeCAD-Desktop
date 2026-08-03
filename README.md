# SolidFreeCAD Desktop

SolidFreeCAD Desktop is a mechanical-design interface built on the official FreeCAD engine. It preserves native FCStd documents, OpenCASCADE geometry, Part Design, Sketcher, TechDraw, FEM, Python and the classic FreeCAD interface while presenting a more integrated task-oriented workflow.

## Current development track

**Windows x64 is the current product priority.** Ubuntu remains an official future target and shared CAD/UI code stays platform-neutral.

Current source candidate: **0.1.0-alpha.11-workspace-rc**

Alpha.11 is deliberately **source only**. It does not publish a portable archive, Setup.exe or executable. It is the final planned interface layer before a separately authorized Windows runtime-validation build.

## Alpha.11 workspace release candidate

Alpha.11 builds on the alpha.10 native feature bindings and focuses on sustained daily use:

- original quick-access toolbar for New, Open, Save, Undo, Redo and Fit;
- persistent laptop, standard and wide workspace profiles;
- persistent compact, normal and comfortable control density;
- system, light and dark visual modes;
- automatic laptop-layout selection for narrow windows;
- workspace reset action;
- Verification tab with document diagnostics;
- warnings for unsaved documents, invalid BRep and underdefined sketches;
- command-coverage audit against the actual runtime;
- safe visible-label rename inside a document transaction;
- manual physical-release checklist;
- safe fallback from alpha.11 to alpha.10 and every earlier source shell.

Alpha.11 does not claim that the runtime has passed. It makes the remaining failures visible and creates a controlled gate for physical Windows validation.

## Preserved mechanical workflow

- dedicated PropertyManagers for Pad, Pocket, Revolution, Fillet, Chamfer, Hole and Sketch;
- native selection bindings for compatible profile, axis, face, edge and point properties;
- end-condition options read from native FreeCAD enumerations;
- edit-session awareness and floating confirmation corner;
- hierarchical FeatureManager and synchronized 3D selection;
- model, sketch and BRep state feedback;
- contextual CommandManager switching and `S` shortcut palette;
- original orientation and display controls;
- native FCStd, Part Design, Sketcher and OpenCASCADE geometry.

Unavailable or incompatible operations remain disabled or are reported as runtime gaps rather than represented as completed functionality.

## Original identity and compatibility

The project adopts established interaction patterns common to professional mechanical CAD so experienced users can work quickly. It does not bundle or copy proprietary SolidWorks source code, icons, logos, trademarks or exact artwork. All SolidFreeCAD visual resources are original.

## Source-RC validation

The workflow `.github/workflows/alpha11-source-validation.yml` performs only:

- Python syntax compilation;
- compatibility-chain checks;
- release-candidate widget and transaction markers;
- verification that alpha.11 contains no executable, installer or artifact generation.

It does not compile FreeCAD or publish a binary.

Manual graphical contract:

```text
tests/solidfreecad_alpha11_gui_smoke.py
```

Runtime gate:

```text
docs/alpha11-source-rc-gate.md
```

## Executable release gate

A user-facing Windows executable remains blocked until physical tests confirm:

1. `Part → Sketch → Pad → Edit → Pocket → Revolution → Fillet → Chamfer → Save → Reopen` works end to end.
2. Profile, axis, face and edge bindings write the exact references required by FreeCAD 1.1.1.
3. End conditions update native preview and geometry without duplicate recomputes.
4. Accept, cancel, restore-session, Undo and Redo remain coherent.
5. Tree, selection, Body tip and sketch status remain synchronized.
6. Layout works at 1366×768, 1920×1080 and high DPI.
7. Windows scaling works at 100%, 125%, 150% and 200%.
8. FCStd, STEP and BRep behavior show no regression.
9. A real interface screenshot and an extended physical Windows session are reviewed.
10. No blocking or high-severity diagnostic remains.

Only after those gates pass and executable creation is explicitly authorized will portable and installable builds be produced.

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
