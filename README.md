# SolidFreeCAD Desktop

SolidFreeCAD Desktop is a mechanical-design interface built on the official FreeCAD engine. It preserves native FCStd documents, OpenCASCADE geometry, Part Design, Sketcher, TechDraw, FEM, Python and the classic FreeCAD interface while presenting a more integrated task-oriented workflow.

## Current development track

**Windows x64 is the current product priority.** Ubuntu remains a future target and shared CAD/UI code stays platform-neutral.

Current source candidate: **0.1.0-alpha.14-interactive-acceptance**

Alpha.14 remains deliberately **source only**. It does not build or publish a SolidFreeCAD portable archive, installer or executable. It adds the final guided physical-acceptance layer required before packaging can be considered.

## Alpha.14 interactive acceptance

Alpha.14 adds an **Aceptación** tab inside the Verification panel. A tester starts a local evidence session and performs the real modeling and usability sequence step by step.

The recorder covers:

- Part and Body creation;
- Sketch creation;
- Pad / Saliente;
- Pad edit mode and parameter change;
- Pocket / Corte;
- Revolution with a native axis;
- Fillet / Redondeo;
- Chamfer / Chaflán;
- FCStd save;
- closing and reopening the same FCStd;
- Undo and Redo confirmation;
- Windows scaling at 100%, 125%, 150% and 200%;
- an extended session of at least 45 minutes.

Native objects and edit states are detected conservatively. DPI, long-session and Undo/Redo observations require explicit human confirmation. Any step can be marked as failed with a defect description.

Each captured step stores a local screenshot and a document snapshot containing object type IDs, labels, visibility, BRep validity, volume, FCStd path and current 3D selection.

The session is approved only when every step is passed, none is failed and none remains pending.

## Alpha.14 local evidence

A completed physical session writes:

```text
solidfreecad-alpha14-acceptance.json
alpha14-body.png
alpha14-sketch.png
alpha14-pad.png
alpha14-edit-pad.png
alpha14-pocket.png
alpha14-revolution.png
alpha14-fillet.png
alpha14-chamfer.png
alpha14-save.png
alpha14-reopen.png
alpha14-undo-redo.png
alpha14-dpi-100.png
alpha14-dpi-125.png
alpha14-dpi-150.png
alpha14-dpi-200.png
alpha14-long-session.png
```

Nothing is uploaded automatically.

## Preserved alpha.13 runtime stabilization

Alpha.13 remains the automated Windows gate beneath alpha.14:

- official FreeCAD 1.1.3 validation baseline;
- runtime fingerprint and official asset digest;
- exact-one-instance checks for critical SolidFreeCAD panels and toolbars;
- critical command coverage;
- persistent workspace preference validation;
- automated 1366×768 and 1920×1080 layout checks;
- isolated document transactions;
- native Undo and Redo verification;
- FCStd save, close, reopen and persistence verification;
- restoration of the previously active document.

The Windows evidence workflow is:

```text
.github/workflows/alpha13-windows-stability-evidence.yml
```

It uses the official FreeCAD runtime only as a temporary test bench, rejects executable distribution outputs and retains only non-executable JSON, PNG, FCStd, STEP and log evidence.

## Preserved interface and modeling foundation

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
- recovery chain from alpha.14 through every earlier source layer.

Unavailable or incompatible operations remain disabled or are reported as runtime gaps rather than represented as completed functionality.

## Original identity and compatibility

The project adopts established interaction patterns common to professional mechanical CAD so experienced users can work quickly. It does not bundle or copy proprietary SolidWorks source code, icons, logos, trademarks or exact artwork. All SolidFreeCAD visual resources are original.

## Validation entry points

Alpha.14 source-only validation:

```text
.github/workflows/alpha14-source-validation.yml
```

Alpha.14 graphical contract:

```text
tests/solidfreecad_alpha14_gui_smoke.py
```

Alpha.14 physical-acceptance specification:

```text
docs/alpha14-interactive-acceptance.md
```

Alpha.13 automated Windows stability entry point:

```text
tests/solidfreecad_alpha13_windows_stability.py
```

## Executable release gate

A user-facing Windows executable remains blocked until:

1. alpha.12 preflight and alpha.13 stability pass on the official supported runtime;
2. alpha.14 physical acceptance has every step passed and no unresolved defect;
3. the generated interface screenshots are visually reviewed;
4. profile, axis, face and edge bindings write the exact native references expected by the runtime;
5. end conditions update native preview and geometry without duplicate recomputes;
6. accept, cancel, restore-session, Undo and Redo remain coherent;
7. layout works physically at 1366×768, 1920×1080 and high DPI;
8. Windows scaling works at 100%, 125%, 150% and 200%;
9. FCStd, STEP and BRep regression evidence passes;
10. an extended physical Windows session reveals no blocking or high-severity defect;
11. executable creation is explicitly authorized as a separate step.

## Repository layout

```text
.github/workflows/        Source checks, evidence-only runtime validation and previous build tracks
docs/                     Architecture, interface gates and integration contracts
overlay/Mod/SolidFreeCAD/ Shared SolidFreeCAD workbench and GUI overlay
platform/windows/         Windows packaging notes
platform/ubuntu/          Preserved Ubuntu target
scripts/windows/          Existing Windows build and packaging scripts
tests/                    Headless and graphical validation
```

## Foundation

- Official upstream: `FreeCAD/FreeCAD`
- Supported validation baseline: `1.1.3`
- GUI: Qt/Python overlay plus native FreeCAD commands
- CAD kernel: official FreeCAD/OpenCASCADE runtime
- Primary platform: Windows x64
- Future platform: Ubuntu Linux x86-64

## License

See the repository license and third-party notices. SolidFreeCAD must remain compatible with the licenses of FreeCAD, Qt, OpenCASCADE, Python and the packaged dependencies.
