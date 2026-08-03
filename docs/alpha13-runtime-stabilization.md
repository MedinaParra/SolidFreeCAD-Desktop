# SolidFreeCAD alpha.13 runtime stabilization

## Purpose

Alpha.13 is a source-only stabilization iteration. It does not add another modeling feature and it does not create a portable archive, installer or executable.

Its purpose is to replace optimistic interface maturity with repeatable runtime evidence before any Windows distribution is authorized.

## Runtime baseline

The supported validation baseline is FreeCAD **1.1.3 or newer within the compatible 1.1 line**.

The Windows evidence workflow obtains the official release metadata from `FreeCAD/FreeCAD`, selects the official Windows x86_64 7z asset dynamically, downloads it into the runner temporary directory and records its SHA-256 digest.

The official runtime is used only as a temporary test bench. It is not repackaged, renamed or uploaded by SolidFreeCAD.

## Stability checks

### Runtime fingerprint

The report records:

- FreeCAD version;
- minimum supported version;
- Python version;
- Qt version;
- Windows/platform information;
- executable path;
- official asset name and digest in the Windows evidence run.

### Unique interface contract

The following critical widgets must exist exactly once:

- CommandManager;
- FeatureManager;
- task pane;
- context bar;
- quick-access toolbar;
- confirmation corner;
- native-binding panel;
- Verification page;
- alpha.12 Preflight page.

Duplicate panels are blocking because they indicate repeated initialization or incomplete cleanup.

### Command coverage

Missing file, sketch or Part Design commands are blocking. Missing secondary evaluation or view commands are reported as warnings.

Unavailable commands remain disabled; they are never represented as completed functions.

### Workspace preferences

Persisted layout, density and theme values must remain inside the supported enumerations.

### Layout accessibility

The same runtime session is checked at:

- 1366×768;
- 1920×1080.

Critical visible panels must retain usable geometry. This automated check does not replace physical testing at 100%, 125%, 150% and 200% Windows scaling.

### Transaction round trip

In an isolated document, alpha.13:

1. creates a valid native feature;
2. changes a length and its BRep inside a document transaction;
3. performs Undo and verifies the original parameter and volume;
4. performs Redo and verifies the modified parameter and volume;
5. saves FCStd;
6. closes and reopens the document;
7. verifies the persisted parameter and BRep;
8. closes the temporary document;
9. restores whichever document was active before the test.

Evidence is stored as `alpha13-transaction-roundtrip.FCStd`.

## Windows evidence workflow

The workflow is:

```text
.github/workflows/alpha13-windows-stability-evidence.yml
```

It performs these steps:

1. validates Python syntax;
2. queries the official FreeCAD release metadata;
3. downloads FreeCAD 1.1.3 Windows x86_64 into the runner temp directory;
4. verifies the published digest when available and always records a local SHA-256;
5. discovers the actual FreeCAD executable, Mod directory and Qt platform plugin;
6. overlays the SolidFreeCAD alpha.13 source;
7. runs alpha.12 preflight and alpha.13 stability checks;
8. rejects executable distribution outputs under `dist`;
9. uploads only non-executable evidence.

## Evidence files

The job may retain:

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

It must not retain or publish `.exe`, `.dll`, `.msi`, `.7z` or `.zip` outputs.

## Remaining gate before an executable

Even a fully passing alpha.13 is not enough by itself. A user-facing executable remains blocked until:

- the evidence screenshot is visually reviewed;
- the complete interactive modeling workflow is performed on Windows;
- profile, axis, face and edge bindings are inspected in real native operations;
- accept, cancel, restore, Undo and Redo behave coherently;
- 100%, 125%, 150% and 200% Windows scaling are physically tested;
- a long session reveals no duplicate panels, captured shortcuts or inaccessible controls;
- FCStd and STEP regression evidence remains valid;
- no blocking or high-severity defect remains;
- executable creation is authorized as a separate iteration.
