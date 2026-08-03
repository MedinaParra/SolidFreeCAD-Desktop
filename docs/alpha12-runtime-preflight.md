# SolidFreeCAD alpha.12 runtime preflight

## Purpose

Alpha.12 is the last source-only iteration before considering a user-facing Windows build. It adds a local preflight and an evidence-only Windows CI path without compiling or publishing a SolidFreeCAD executable.

## Local preflight checks

### Interface contract

- CommandManager exists.
- FeatureManager exists.
- Task pane and context bar exist.
- Quick-access toolbar exists.
- Confirmation corner exists.
- Native-binding panel exists.
- Verification page exists.
- Current window dimensions and device pixel ratio are recorded.

### Command coverage

The preflight checks the actual runtime registration of essential commands for:

- files and history;
- sketch creation and entities;
- Pad, Pocket, Revolution, Fillet and Chamfer;
- standard views and measurement.

Missing commands are reported explicitly.

### Active-document diagnostics

- unsaved or problematic objects remain visible through alpha.11 diagnostics;
- invalid BRep and underdefined sketches are listed;
- no current document is modified by the geometry round trip.

### Isolated geometry round trip

In a temporary folder and temporary documents, the preflight:

1. creates a native BRep with an outer solid, through hole and pocket;
2. validates the BRep and volume;
3. saves FCStd;
4. exports STEP;
5. closes and reopens FCStd;
6. compares reopened volume;
7. imports STEP into a separate document;
8. validates imported shapes;
9. closes all temporary documents.

### Local evidence

The local preflight stores:

- `solidfreecad-alpha12-preflight.json`;
- `solidfreecad-alpha12-interface.png`;
- the temporary FCStd fixture;
- the temporary STEP fixture.

The local button uploads nothing.

## Windows CI evidence path

`.github/workflows/alpha12-windows-preflight-no-package.yml` downloads the previously validated alpha.5 portable runtime into the Windows runner as a temporary test bench. It does not rebuild or redistribute that runtime.

The workflow:

1. syntax-checks the alpha.12 source;
2. expands the existing runtime under the runner temporary directory;
3. overlays the alpha.12 workbench source;
4. launches FreeCAD with `tests/solidfreecad_alpha12_windows_preflight.py`;
5. executes the same interface, command and geometry checks;
6. rejects `.exe`, `.dll`, `.msi` and `.7z` files from the output directory;
7. may upload only PNG, JSON, FCStd, STEP, marker and text logs as review evidence.

The artifact does not include the downloaded FreeCAD runtime or a SolidFreeCAD distribution.

## Interpretation

`passed: true` means the automated checks found no blocking failure in that particular runtime session. It does not prove:

- high-DPI usability at every Windows scale;
- correct interactive selection for every feature;
- native task-dialog cancel behavior;
- long-session stability;
- exact equivalence to another commercial CAD product.

## Gate before any executable

Before a user-facing portable or installer:

- the Windows alpha.12 preflight must pass;
- the generated screenshot must be visually reviewed;
- the complete interactive modeling flow must be performed manually;
- LinkSub bindings must be inspected in saved FCStd documents;
- all target resolutions and Windows scaling values must be tested;
- no blocking diagnostic may remain;
- FCStd, STEP and BRep regression evidence must pass;
- executable creation must be requested separately.
