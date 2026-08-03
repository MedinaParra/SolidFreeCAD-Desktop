# SolidFreeCAD Desktop

SolidFreeCAD Desktop is a mechanical-design interface built on the official FreeCAD engine. It preserves native FCStd documents, OpenCASCADE geometry, Part Design, Sketcher, TechDraw, FEM, Python and the classic FreeCAD interface while presenting a more integrated task-oriented workflow.

## Current development track

**Windows x64 is the current product priority.** Ubuntu remains an official future target and shared CAD/UI code stays platform-neutral.

Current source prototype: **0.1.0-alpha.7-interface**

Alpha.7 is intentionally **source only**. This branch does not add, trigger or publish a portable build, Setup.exe or other executable. Packaging will resume only after the interface reaches its physical Windows acceptance gate.

## Alpha.7 interface prototype

Alpha.7 builds on the validated alpha.6 mechanical workspace and adds:

- document context bar with active-document selector;
- document/object breadcrumb and model-state feedback;
- curated command search with `Ctrl+K`;
- explicit recompute control;
- right-side task pane with Tasks, Library, Appearances and Resources;
- selection-aware native-property editor for common numeric parameters;
- quick edit, visibility, zoom and recompute actions;
- design library that delegates to registered FreeCAD commands;
- native shape color and transparency controls;
- safer context actions in the FeatureManager tree;
- original SolidFreeCAD styling and resources only.

The project adopts interaction patterns common to professional mechanical CAD, but it does not bundle proprietary SolidWorks code, icons, trademarks or exact artwork.

## Preserved alpha.6 foundation

- tabbed CommandManager for Operations, Sketch, Surfaces, Evaluate, Shaft, Sheet Metal and Assembly;
- integrated FeatureManager design tree;
- contextual PropertyManager with accept/cancel controls and guided messages;
- configurations foundation;
- compact Heads-Up view toolbar;
- native FreeCAD commands and FCStd documents;
- classic FreeCAD UI retained as a compatibility fallback;
- parametric shaft and demonstration part;
- BRep, FCStd and STEP validation from the previous Windows track.

Unavailable commands remain disabled rather than represented as completed features.

## Source-only validation

The manual test `tests/solidfreecad_alpha7_gui_smoke.py` checks the alpha.7 widget contract inside a validated FreeCAD runtime. It is deliberately not connected to a packaging workflow.

The design and future release gate are documented in:

```text
docs/alpha7-interface-blueprint.md
```

A future executable is allowed only after physical Windows review confirms DPI scaling, layout stability, shortcut safety, multi-document behavior, property editing and no regression in native geometry or files.

## Repository layout

```text
.github/workflows/        Existing validated alpha.6 build workflows
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
