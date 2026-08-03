# SolidFreeCAD Desktop

SolidFreeCAD Desktop is a mechanical-design interface built on the official FreeCAD engine. It preserves native FCStd documents, OpenCASCADE geometry, Part Design, Sketcher, TechDraw, FEM, Python and the classic FreeCAD interface while presenting a more integrated task-oriented workflow.

## Current release track

**Windows x64 is the current delivery priority.** Ubuntu remains an official future target and shared CAD/UI code stays platform-neutral.

Current development version: **0.1.0-alpha.6**

## Alpha.6 interface

The alpha.6 workspace introduces a familiar mechanical-CAD structure using original SolidFreeCAD code and artwork:

- tabbed CommandManager for Operations, Sketch, Surfaces, Evaluate, Shaft, Sheet Metal and Assembly;
- integrated FeatureManager design tree;
- contextual PropertyManager with accept/cancel controls and guided messages;
- configurations foundation;
- compact Heads-Up view toolbar;
- native FreeCAD commands and FCStd documents underneath the new interface;
- classic FreeCAD UI retained as a compatibility fallback.

The project may adopt established interaction patterns common to professional mechanical CAD, but it does not bundle proprietary SolidWorks code, icons, trademarks or artwork.

## Functional and validated

- Windows Qt runtime repair and `qwindows.dll` packaging;
- isolated portable configuration;
- branded launcher, portable package and Inno Setup installer;
- native document and Part Design Body creation;
- native FreeCAD command delegation for sketches and features;
- editable parametric shaft with optional keyway;
- parametric alpha.6 demonstration plate with through-hole and pocket;
- BRep validation;
- FCStd save, close and reopen validation;
- STEP export validation;
- automated GUI structure test and Windows interface screenshot;
- original SVG icon pack.

## Experimental

- sheet-metal commands depend on an installed compatible SheetMetal workbench;
- assembly commands depend on the assembly commands available in the pinned FreeCAD runtime;
- some advanced surface and evaluation commands vary by FreeCAD build;
- the interface still requires physical review on Windows for spacing, DPI scaling and long editing sessions.

Unavailable commands are disabled rather than represented as working features.

## Repository layout

```text
.github/workflows/        Windows CI and release validation
docs/                     Architecture, visual system and integration contracts
overlay/Mod/SolidFreeCAD/ Shared SolidFreeCAD workbench and GUI overlay
platform/windows/         Windows packaging notes
platform/ubuntu/          Preserved Ubuntu target
scripts/windows/          Windows build and packaging scripts
tests/                    Headless and graphical validation
```

## Windows alpha.6 validation flow

The workflow `.github/workflows/windows-alpha6-solidworks-workflow.yml`:

1. reuses the validated alpha.5 Windows runtime;
2. installs the alpha.6 overlay;
3. validates Python, SVG and JSON contracts;
4. creates and edits a parametric part;
5. validates its BRep;
6. saves and reopens FCStd;
7. exports STEP;
8. validates the GUI structure;
9. captures a Windows screenshot;
10. generates portable and Setup.exe artifacts with SHA-256 files.

## Application-mother integration

The project contract under `docs/solidfreecad-project.schema.json` prepares future links with:

- Android photogrammetry and reconstructed geometry;
- work orders and asset identity;
- geometry confidence and validation status;
- FCStd/STEP exchange;
- source images and operator corrections.

No cloud dependency is required by this contract.

## Foundation

- Official upstream: `FreeCAD/FreeCAD`
- Pinned source tag: `1.1.1`
- GUI: Qt/Python overlay plus native FreeCAD commands
- CAD kernel: official FreeCAD/OpenCASCADE runtime
- Primary platform: Windows x64
- Future platform: Ubuntu Linux x86-64

## License

See the repository license and third-party notices. SolidFreeCAD must remain compatible with the licenses of FreeCAD, Qt, OpenCASCADE, Python and the packaged dependencies.
