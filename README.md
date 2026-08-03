# SolidFreeCAD Desktop

SolidFreeCAD Desktop is a mechanical-design interface built on the official FreeCAD engine. It preserves native FCStd documents, OpenCASCADE geometry, Part Design, Sketcher, TechDraw, FEM, Python and the classic FreeCAD interface while presenting a more integrated task-oriented workflow.

## Current development track

**Windows x64 is the current product priority.** Ubuntu remains an official future target and shared CAD/UI code stays platform-neutral.

Current source prototype: **0.1.0-alpha.8-interaction**

Alpha.8 remains intentionally **source only**. It does not publish a portable archive, Setup.exe or any executable. Packaging resumes only after the complete mechanical workflow passes physical Windows review.

## Alpha.8 interaction prototype

Alpha.8 builds on the alpha.7 professional shell and adds the interaction layer needed for a mature desktop CAD workflow:

- automatic detection of sketch and feature edit sessions;
- floating confirmation corner inside the graphics area;
- contextual **Operation** tab with accept, close, selection and native parameters;
- sketch degree-of-freedom feedback when exposed by the FreeCAD runtime;
- hierarchical design history grouped by parts, bodies, features and references;
- synchronized tree and 3D selection;
- visual indication of hidden and invalid objects;
- contextual CommandManager tab switching;
- `S` shortcut palette for sketch and feature commands;
- display modes for shaded with edges, shaded and wireframe;
- orientation menu for isometric and standard views;
- adaptive side-panel sizing for desktop and laptop windows;
- safe fallback to alpha.7 if the interaction layer cannot initialize.

All modeling actions delegate to registered native FreeCAD commands or edit native FreeCAD properties. SolidFreeCAD does not create a parallel CAD document model.

## Preserved alpha.7 and alpha.6 foundation

- document selector, breadcrumb, command search and model-state feedback;
- right-side Tasks, Library, Appearances and Resources pane;
- CommandManager for Operations, Sketch, Surfaces, Evaluate, Shaft, Sheet Metal and Assembly;
- FeatureManager and PropertyManager foundations;
- configurations foundation and Heads-Up view toolbar;
- native FCStd, Part Design, Sketcher and OpenCASCADE geometry;
- parametric shaft and demonstration component;
- classic FreeCAD compatibility fallback;
- previous BRep, FCStd and STEP validation work.

Unavailable commands remain disabled rather than represented as completed features.

## Original identity and compatibility

The project adopts established interaction patterns common to professional mechanical CAD so experienced users can work quickly. It does not bundle or copy proprietary SolidWorks source code, icons, logos, trademarks or exact artwork. All SolidFreeCAD visual resources are original and the native FreeCAD engine remains visible in the product architecture.

## Source-only validation

The workflow `.github/workflows/alpha8-source-validation.yml` performs only:

- Python syntax compilation;
- compatibility-loader checks;
- verification that alpha.8 contains no installer or portable packaging commands.

It does not compile FreeCAD, upload an artifact or generate an executable.

The manual graphical contract test is:

```text
tests/solidfreecad_alpha8_gui_smoke.py
```

The maturity criteria and release gate are documented in:

```text
docs/alpha8-interaction-maturity.md
```

## Executable release gate

A Windows executable remains blocked until physical tests confirm:

1. `Part → Sketch → Pad → Edit → Pocket → Fillet → Save → Reopen` works end to end.
2. Sketch shortcuts and confirmation controls do not conflict with native tools.
3. Feature parameters update preview and geometry safely.
4. Tree hierarchy, selections and multi-document behavior remain synchronized.
5. Layout works at 1366×768, 1920×1080 and high DPI.
6. Windows scaling works at 100%, 125%, 150% and 200%.
7. FCStd, STEP and BRep behavior show no regression.
8. A real interface screenshot and an extended Windows session are reviewed.

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
