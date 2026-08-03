# SolidFreeCAD Desktop

SolidFreeCAD Desktop is a mechanical-design interface built on the official FreeCAD engine. It preserves native FCStd documents, OpenCASCADE geometry, Part Design, Sketcher, TechDraw, FEM, Python and the classic FreeCAD interface while presenting a more integrated task-oriented workflow.

## Current development track

**Windows x64 is the current product priority.** Ubuntu remains an official future target and shared CAD/UI code stays platform-neutral.

Current source candidate: **0.1.0-alpha.12-runtime-preflight-source**

Alpha.12 remains deliberately **source only**. It does not build or publish a SolidFreeCAD portable archive, Setup.exe or executable. It adds the runtime evidence needed before a separately authorized distribution build.

## Alpha.12 local runtime preflight

Alpha.12 adds a **Preflight** page inside the alpha.11 Verification panel. When run inside an existing FreeCAD installation it:

- verifies the CommandManager, FeatureManager, task pane, context bar and quick access;
- verifies the confirmation corner and native-binding panel;
- records current window dimensions and device pixel ratio;
- audits essential commands registered by the actual runtime;
- reviews the active document for basic warnings;
- captures a real local interface screenshot;
- creates an isolated native BRep in a temporary document;
- saves, closes and reopens FCStd and compares volume;
- exports STEP, imports it into another document and validates the imported shapes;
- writes a structured local JSON report;
- leaves all evidence in a temporary folder for review;
- creates no executable.

The local button uploads nothing. A passing preflight proves only that the automated checks passed in that particular runtime session; it does not replace interactive Windows use or high-DPI testing.

## Windows evidence workflow

`.github/workflows/alpha12-windows-preflight-no-package.yml` reuses the previously validated alpha.5 portable runtime only as a temporary test bench. It overlays the current alpha.12 source and runs the GUI and geometry preflight without compiling or packaging SolidFreeCAD.

The job explicitly rejects `.exe`, `.dll`, `.msi` and `.7z` files under its output directory. It may retain only the following review evidence:

```text
solidfreecad-alpha12-preflight.json
solidfreecad-alpha12-interface.png
alpha12-preflight.FCStd
alpha12-preflight.step
alpha12-marker.txt
alpha12-stdout.txt
alpha12-stderr.txt
```

The downloaded base runtime is temporary and is not included in the evidence artifact.

## Preserved source release candidate

- quick-access toolbar and persistent workspace profiles;
- compact, normal and comfortable density;
- system, light and dark visual modes;
- document diagnostics and command-coverage audit;
- dedicated PropertyManagers for Pad, Pocket, Revolution, Fillet, Chamfer, Hole and Sketch;
- native selection bindings for compatible profile, axis, face, edge and point properties;
- runtime-derived end conditions and debounced recomputation;
- edit-session awareness and floating confirmation corner;
- hierarchical FeatureManager and synchronized 3D selection;
- native FCStd, Part Design, Sketcher and OpenCASCADE geometry;
- recovery chain from alpha.12 through every earlier source layer.

Unavailable or incompatible operations remain disabled or are reported as runtime gaps rather than represented as completed functionality.

## Original identity and compatibility

The project adopts established interaction patterns common to professional mechanical CAD so experienced users can work quickly. It does not bundle or copy proprietary SolidWorks source code, icons, logos, trademarks or exact artwork. All SolidFreeCAD visual resources are original.

## Source-only validation

The workflow `.github/workflows/alpha12-source-validation.yml` performs only:

- Python syntax compilation;
- compatibility-chain checks;
- local-preflight contract checks;
- verification that the source workflow contains no packaging or artifact upload.

The separate Windows preflight workflow uploads only the non-executable evidence listed above.

Manual graphical contract:

```text
tests/solidfreecad_alpha12_gui_smoke.py
```

Automated Windows preflight entry point:

```text
tests/solidfreecad_alpha12_windows_preflight.py
```

Preflight specification:

```text
docs/alpha12-runtime-preflight.md
```

## Executable release gate

A user-facing Windows executable remains blocked until:

1. Alpha.12 passes inside the intended FreeCAD 1.1.1 Windows runtime.
2. The generated interface screenshot is visually reviewed.
3. `Part → Sketch → Pad → Edit → Pocket → Revolution → Fillet → Chamfer → Save → Reopen` works interactively.
4. Profile, axis, face and edge bindings write the exact native references expected by the runtime.
5. End conditions update native preview and geometry without duplicate recomputes.
6. Accept, cancel, restore-session, Undo and Redo remain coherent.
7. Layout works at 1366×768, 1920×1080 and high DPI.
8. Windows scaling works at 100%, 125%, 150% and 200%.
9. FCStd, STEP and BRep regression evidence passes.
10. An extended physical Windows session reveals no blocking or high-severity defect.
11. Executable creation is explicitly authorized as a separate step.

## Repository layout

```text
.github/workflows/        Source checks, evidence-only preflight and previous build tracks
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
