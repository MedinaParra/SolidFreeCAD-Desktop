# SolidFreeCAD Workshop Readiness

## Purpose

SolidFreeCAD is intended to become a daily mechanical-design tool for a demanding workshop environment. Visual familiarity is necessary, but a release is not workshop-ready unless it protects work, behaves predictably and handles real production files.

## Non-negotiable principles

1. No silent data loss.
2. Every primary operation is undoable as one transaction.
3. A failed operation leaves the document in the previous valid state.
4. FCStd remains the authoritative editable document format.
5. STEP import and export must be repeatable and diagnosable.
6. Millimetres are the default workshop unit, with the active unit system always visible.
7. The application must start and model offline.
8. Classic recovery mode remains available until SolidFreeCAD reaches feature parity for the validated workflow.
9. Errors are shown in user language while detailed diagnostics remain available for support.
10. Automated tests must reproduce every critical workflow before release.

## Workshop release levels

### Development build

- Starts on the reference Ubuntu workstation.
- Can create and reopen the Part -> Sketch -> Pad vertical slice.
- Produces a real screenshot and FCStd artifact in CI.
- May expose incomplete commands and diagnostic warnings.

### Alpha workshop build

- Clean SolidFreeCAD shell.
- New Part, plane selection, rectangle sketch, dimensions, Pad and Pocket.
- Save, close and reopen without data loss.
- Undo and redo across sketch and feature creation.
- Import and inspect a representative STEP file.
- AppImage or equivalent installable artifact.

### Controlled beta

- Box-and-lid lesson completed without Classic mode.
- Fillet, Chamfer and Thickness validated.
- Property manager with preview, accept and cancel.
- Recovery of autosaved work after forced termination.
- Ten representative workshop FCStd files opened, edited, saved and reopened.
- Ten representative STEP files imported without crashes.
- Session diagnostics can be exported as one support bundle.

### Daily-use release

- Four continuous weeks of controlled workshop use without critical data loss.
- At least 100 save/reopen regression cycles in CI.
- Crash-recovery test passes repeatedly.
- Large-model interaction remains usable on the reference workstation.
- Assembly and drawing workflows used in at least three real jobs.
- Versioned backups and safe-save replacement are enabled.
- Release notes identify known limitations and migration risks.

## Reliability gates

### Safe save

Saving must follow a recoverable sequence:

1. write a temporary document;
2. flush and close it;
3. validate that it can be reopened;
4. preserve the previous valid file as a backup;
5. atomically replace the destination where the platform permits;
6. report a clear error without deleting either valid copy if replacement fails.

### Autosave and recovery

- Configurable interval with a conservative workshop default.
- Recovery files stored separately from the original.
- Recovery dialog shows document, timestamp and source path.
- Recovered work is never written over the original without explicit confirmation.
- Recovery files are cleaned only after a confirmed successful save.

### Transaction integrity

The following must each be one undoable transaction:

- create Body;
- create Sketch;
- accept Sketch edits;
- create Pad;
- create Pocket;
- edit feature parameters;
- insert assembly component;
- create assembly constraint.

Cancel must restore the exact pre-command document state.

### File regression

Every release candidate must test:

- create -> save -> close -> reopen;
- edit -> save -> reopen;
- undo -> save -> reopen;
- imported STEP -> save as FCStd -> reopen;
- missing external reference;
- read-only destination;
- interrupted save simulation;
- non-ASCII file and directory names;
- long but supported file paths;
- documents created by the previous SolidFreeCAD release.

## Performance targets

Initial targets for the reference Ubuntu x86-64 workstation:

- cold startup to usable shell: under 15 seconds;
- warm startup: under 8 seconds;
- new document: under 2 seconds;
- parameter preview response for a simple part: under 250 ms where practical;
- save a simple FCStd document: under 2 seconds;
- open a representative workshop part: under 10 seconds;
- no UI freeze longer than 2 seconds without progress feedback;
- operations longer than 5 seconds expose cancellation or clear progress.

These are product targets, not current claims.

## Usability targets

- Primary commands remain visible with text labels.
- Disabled commands explain the missing prerequisite.
- Selection filters are quickly reachable.
- Active Body, active Sketch and active feature are visually unambiguous.
- Units and document modification state are always visible.
- Accept and cancel remain in a consistent location.
- Error messages identify the affected feature and a corrective action.
- Technical report docks remain hidden during normal modeling.
- Command search works without knowing FreeCAD module names.

## Reference workshop dataset

The project will maintain a private or redistributable validation set containing:

- simple machined shaft;
- bearing housing;
- pulley hub;
- rectangular plate with hole pattern;
- welded bracket represented as a part;
- imported supplier STEP component;
- medium-size assembly;
- associated manufacturing drawing.

No confidential customer geometry should be committed to the public repository.

## Current validated vertical slice

The first automated production trace is:

```text
Body
-> fully dimensioned rectangular Sketch on XY plane
-> Pad
-> validate solid and volume
-> save FCStd
-> close
-> reopen
-> validate Body, Sketch, Pad and volume
```

This is the minimum persistence foundation. It does not yet prove the complete GUI interaction, preview or editing workflow.

## Current priority

Until the controlled beta gate is reached, development priority remains:

```text
Clean shell
-> reliable persistence
-> model tree
-> property manager
-> sketch workflow
-> Pad
-> Pocket
-> Fillet / Chamfer / Thickness
-> box and lid
-> AppImage
```
