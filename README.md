# SolidFreeCAD Desktop

SolidFreeCAD Desktop is a mechanical-design interface built on the official FreeCAD engine. It preserves native FCStd documents, OpenCASCADE geometry, Part Design, Sketcher, TechDraw, FEM, Python and the classic FreeCAD interface while presenting a more integrated task-oriented workflow.

## Current development track

**Windows x64 is the current product priority.** Ubuntu remains a future target and shared CAD/UI code stays platform-neutral.

Current source candidate: **0.1.0-alpha.13-runtime-stabilization**

Alpha.13 remains deliberately **source only**. It does not build or publish a SolidFreeCAD portable archive, installer or executable. Its purpose is to stabilize the runtime contract before any distribution build is authorized.

## Alpha.13 runtime stabilization

Alpha.13 builds on the alpha.12 local preflight and adds:

- supported runtime baseline of official FreeCAD 1.1.3 or newer compatible 1.1.x maintenance release;
- runtime fingerprint with FreeCAD, Python, Qt, platform, executable and official asset digest;
- exact-one-instance checks for critical SolidFreeCAD panels and toolbars;
- blocking command coverage for files, sketches and Part Design operations;
- persistent workspace preference validation;
- automated 1366×768 and 1920×1080 layout accessibility checks;
- isolated document transaction test;
- Undo and Redo verification using native parameters and BRep volume;
- FCStd save, close, reopen and persistence verification;
- restoration of the previously active document after testing;
- a dedicated **Estabilidad** page inside the Verification panel;
- recovery chain from alpha.13 through every earlier source layer.

Alpha.13 adds no new modeling feature. It exists to expose duplicated UI, incompatible runtimes, broken transactions and persistence failures before an executable is considered.

## Official Windows runtime evidence

The workflow:

```text
.github/workflows/alpha13-windows-stability-evidence.yml
```

queries the official `FreeCAD/FreeCAD` release metadata, downloads the official FreeCAD 1.1.3 Windows x86_64 archive into the runner temporary directory, records its SHA-256 digest and discovers the real executable, Mod directory and Qt platform plugin.

It then overlays the SolidFreeCAD source and runs:

1. alpha.12 interface, command, BRep, FCStd and STEP preflight;
2. alpha.13 runtime, UI uniqueness, layout, transaction, Undo/Redo and persistence checks.

The official runtime is used only as a temporary test bench. It is not repackaged, renamed or uploaded.

The job rejects `.exe`, `.dll`, `.msi`, `.7z` and `.zip` files under the evidence output directory.

## Non-executable evidence

The Windows evidence job may retain only:

```text
solidfreecad-alpha12-preflight.json
solidfreecad-alpha13-stability.json
solidfreecad-alpha13-combined.json
solidfreecad-alpha13-interface.png
alpha12-preflight.FCStd
alpha12-preflight.step
alpha13-transaction-roundtrip.FCStd
alpha13-marker.txt
alpha13-stdout.txt
alpha13-stderr.txt
```

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
- native FCStd, Part Design, Sketcher and OpenCASCADE geometry.

Unavailable or incompatible operations remain disabled or are reported as runtime gaps rather than represented as completed functionality.

## Original identity and compatibility

The project adopts established interaction patterns common to professional mechanical CAD so experienced users can work quickly. It does not bundle or copy proprietary SolidWorks source code, icons, logos, trademarks or exact artwork. All SolidFreeCAD visual resources are original.

## Validation entry points

Source-only validation:

```text
.github/workflows/alpha13-source-validation.yml
```

Manual graphical contract:

```text
tests/solidfreecad_alpha13_gui_smoke.py
```

Automated Windows stability entry point:

```text
tests/solidfreecad_alpha13_windows_stability.py
```

Stabilization specification:

```text
docs/alpha13-runtime-stabilization.md
```

## Executable release gate

A user-facing Windows executable remains blocked until:

1. alpha.12 preflight and alpha.13 stability pass on the official supported runtime;
2. the generated interface screenshot is visually reviewed;
3. `Part → Sketch → Pad → Edit → Pocket → Revolution → Fillet → Chamfer → Save → Reopen` works interactively;
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
