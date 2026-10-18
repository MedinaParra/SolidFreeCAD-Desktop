# SolidFreeCAD Desktop

SolidFreeCAD Desktop is a mechanical-design interface built on the official FreeCAD engine. It preserves native FCStd documents, OpenCASCADE geometry, Part Design, Sketcher, TechDraw, FEM, Python and the classic FreeCAD interface while presenting a more integrated task-oriented workflow.

## Current development track

Windows x64 is the delivery priority. The current standalone candidate is
**0.1.0-alpha.12**, based on the latest alpha.11 branch of 14 October 2026.
Ubuntu and the previous overlay remain preserved.

The application owns its Qt window, menus, CommandManager, FeatureManager and
PropertyManager. The embedded FreeCAD view handles rendering and selection.
Geometry uses native Sketcher and Part Design objects without dispatching native
workbench commands.

Implemented: sketches on reference planes and planar faces; interactive line,
rectangle and circle; driving dimensions; native Pad, Pocket, Revolution, Fillet
and Chamfer; live feature previews with accept/cancel transactions; Undo/Redo;
FCStd history and STEP exchange; search, filtering, measurement and validation.

See [the current application guide](standalone/README.md) for installation,
modelling steps, validation and the remaining advanced-CAD scope. This candidate
completes basic part modelling; it does not claim parity with the full SolidWorks
product.

The interface follows common professional mechanical-CAD interaction patterns
using original SolidFreeCAD code and vector icons.

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

## Previous Windows alpha.6 validation flow

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
- GUI: independent Qt/Python window embedding the FreeCAD viewport; earlier overlay preserved
- CAD kernel: official FreeCAD/OpenCASCADE runtime
- Primary platform: Windows x64
- Future platform: Ubuntu Linux x86-64

## License

See the repository license and third-party notices. SolidFreeCAD must remain compatible with the licenses of FreeCAD, Qt, OpenCASCADE, Python and the packaged dependencies.
