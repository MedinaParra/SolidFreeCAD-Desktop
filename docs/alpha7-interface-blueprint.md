# SolidFreeCAD alpha.7 — interface-first prototype

## Purpose

Alpha.7 is an interface and workflow iteration only. It must move SolidFreeCAD closer to the clarity and speed expected from a professional mechanical CAD application while preserving its own identity and the native FreeCAD engine.

The branch must **not** create, upload or advertise a Windows executable, portable package or installer. Existing alpha.6 packaging workflows remain untouched and are not extended to alpha.7.

## Product principles

1. Preserve FCStd documents, OpenCASCADE BRep geometry and native FreeCAD commands.
2. Use familiar mechanical-CAD interaction patterns without copying proprietary code, icons, trademarks or exact artwork.
3. Keep unavailable functions visibly disabled rather than simulating successful operations.
4. Prefer contextual controls and progressive disclosure over permanent tool clutter.
5. Preserve the classic FreeCAD interface as a recovery and compatibility path.

## Alpha.7 interface hierarchy

### CommandManager

The alpha.6 tabbed manager remains the primary command surface for Operations, Sketch, Surfaces, Evaluate, Shaft, Sheet Metal and Assembly.

### Document context bar

A new compact strip exposes:

- active-document selector;
- document/object breadcrumb;
- BRep or document state;
- command search with `Ctrl+K`;
- explicit recompute action.

### Left design manager

The existing Model, Properties and Configurations tabs remain. Alpha.7 adds safer model-tree context actions for edit, visibility and zoom.

### Right task pane

The new task pane contains:

- **Tasks:** selected-object state, quick actions and common numeric parameters;
- **Library:** native design commands grouped by purpose;
- **Appearances:** visibility, shape color and transparency;
- **Resources:** open documents and compatibility information.

### Viewport support

The alpha.6 Heads-Up view toolbar remains separate from feature creation. Alpha.7 does not attempt to replace the Coin3D viewer or navigation engine.

## Functional boundary

Alpha.7 may:

- invoke registered native FreeCAD commands;
- recompute documents;
- switch active documents;
- edit exposed numeric properties within transactions;
- edit object visibility, color and transparency;
- activate edit mode on native objects;
- search a curated command catalog.

Alpha.7 may not:

- claim unsupported sheet-metal or assembly functions;
- create fake geometry results;
- replace the FCStd document model;
- publish executable artifacts;
- remove the classic interface fallback.

## Visual acceptance gate before packaging

A future executable may be created only after physical Windows review confirms:

- stable layout at 100%, 125%, 150% and 200% scaling;
- usable 1366×768, 1920×1080 and ultrawide layouts;
- readable original icons in light and dark Windows environments;
- no overlap between CommandManager, context strip, managers and viewport;
- correct behavior with multiple FCStd documents;
- command search and shortcuts do not interfere with sketch editing;
- right task pane remains optional and dockable;
- property changes recompute and undo correctly;
- no regression in alpha.6 BRep, FCStd and STEP behavior.

## Release gate

Only after the interface screenshot and physical interaction are accepted should a new packaging workflow be created for:

1. portable Windows x64 package;
2. installable Windows x64 setup;
3. checksums and version metadata.

Until then, alpha.7 remains a source-only draft branch.
