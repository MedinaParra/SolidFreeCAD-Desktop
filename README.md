# SolidFreeCAD Desktop

SolidFreeCAD Desktop is a mechanical-design interface built on the official FreeCAD engine. It preserves native FCStd documents, OpenCASCADE geometry, Part Design, Sketcher, TechDraw, FEM, Python and the classic FreeCAD interface while presenting a more integrated task-oriented workflow.

## Current development track

**Windows x64 is the current product priority.** Ubuntu remains an official future target and shared CAD/UI code stays platform-neutral.

Current source prototype: **0.1.0-alpha.9-feature-managers**

Alpha.9 remains intentionally **source only**. It does not publish a portable archive, Setup.exe or any executable. Packaging resumes only after the complete modeling workflow passes physical Windows review.

## Alpha.9 feature-manager prototype

Alpha.9 builds on the alpha.8 interaction shell and replaces generic editing with more focused mechanical-design guidance:

- dedicated definition profiles for Pad, Pocket, Revolution, Fillet, Chamfer, Hole and Sketch;
- property controls created only when the native FreeCAD object exposes the corresponding property;
- operation-specific selection instructions and a geometric selection collector;
- sketch geometry and relation commands inside the contextual panel;
- sketch fully-defined or remaining-degree-of-freedom feedback;
- two-column FeatureManager showing design object and state;
- active Body tip, hidden-object, underdefined-sketch and invalid-BRep states;
- optional native selection gates for faces, edges, vertices and bodies;
- original orientation overlay for top, front, right, isometric and fit;
- safe fallback from alpha.9 to alpha.8 and then to earlier validated shells.

All modeling actions continue to delegate to registered native FreeCAD commands or edit native FreeCAD properties inside document transactions.

## Preserved alpha.8 foundation

- edit-session awareness for sketches and features;
- floating confirmation corner;
- contextual Operation tab;
- hierarchical design history and synchronized 3D selection;
- `S` shortcut palette;
- display-style and standard-view controls;
- adaptive desktop/laptop layout;
- native FCStd, Part Design, Sketcher and OpenCASCADE geometry.

Unavailable commands remain disabled rather than represented as completed features.

## Original identity and compatibility

The project adopts established interaction patterns common to professional mechanical CAD so experienced users can work quickly. It does not bundle or copy proprietary SolidWorks source code, icons, logos, trademarks or exact artwork. All SolidFreeCAD visual resources are original.

## Source-only validation

The workflow `.github/workflows/alpha9-source-validation.yml` performs only:

- Python syntax compilation;
- compatibility-chain checks;
- verification that alpha.9 contains no installer or portable packaging commands.

It does not compile FreeCAD, upload an artifact or generate an executable.

Manual graphical contract:

```text
tests/solidfreecad_alpha9_gui_smoke.py
```

Maturity criteria and remaining gaps:

```text
docs/alpha9-feature-manager-maturity.md
```

## Executable release gate

A Windows executable remains blocked until physical tests confirm:

1. `Part → Sketch → Pad → Edit → Pocket → Revolution → Fillet → Chamfer → Save → Reopen` works end to end.
2. Dedicated panels update native preview and geometry without duplicate recomputes.
3. Selection collectors write correct profile, axis, face and edge references.
4. Accept and cancel restore the correct native transaction state.
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
