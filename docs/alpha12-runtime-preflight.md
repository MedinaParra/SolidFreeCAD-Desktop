# SolidFreeCAD alpha.12 local runtime preflight

## Purpose

Alpha.12 is the last source-only iteration before considering a disposable Windows validation build. It adds a local preflight that runs inside an existing FreeCAD installation and records evidence without creating or publishing a SolidFreeCAD executable.

## Preflight checks

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

### Evidence

The preflight stores locally:

- `solidfreecad-alpha12-preflight.json`;
- `solidfreecad-alpha12-interface.png`;
- the temporary FCStd fixture;
- the temporary STEP fixture.

Nothing is uploaded automatically.

## Interpretation

`passed: true` means the automated checks found no blocking failure in that particular runtime session. It does not prove:

- high-DPI usability at every Windows scale;
- correct interactive selection for every feature;
- native task-dialog cancel behavior;
- long-session stability;
- equivalence to another commercial CAD interface.

## Gate before any executable

The next step may be a disposable internal Windows validation runtime only when explicitly authorized. Before a user-facing portable or installer:

- alpha.12 must pass in the intended FreeCAD 1.1.1 Windows runtime;
- the generated screenshot must be visually reviewed;
- the complete interactive modeling flow must be performed manually;
- LinkSub bindings must be inspected in saved FCStd documents;
- all target resolutions and Windows scaling values must be tested;
- no blocking diagnostic may remain;
- FCStd, STEP and BRep regression evidence must pass;
- executable creation must be requested separately.
