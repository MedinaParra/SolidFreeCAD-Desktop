# SolidFreeCAD alpha.14 interactive acceptance

## Purpose

Alpha.14 is the final source-only acceptance layer before a Windows executable can be considered. It does not add another modeling command and it does not package or publish a binary.

Its purpose is to guide a real Windows session, capture what actually happened and prevent a visually attractive but operationally incomplete interface from being released.

## Acceptance page

Alpha.14 adds an **Aceptación** tab inside the Verification panel.

The user starts a local evidence session, performs each modeling or usability step and deliberately captures the result. Automated detectors help with native model states, while DPI, long-session and Undo/Redo observations require explicit human confirmation.

## Required sequence

The guided sequence contains:

1. create Part and Body;
2. create a Sketch;
3. create Pad / Saliente;
4. enter Pad edit mode and change a dimension;
5. create Pocket / Corte;
6. create Revolution with a native axis;
7. create Fillet / Redondeo;
8. create Chamfer / Chaflán;
9. save FCStd;
10. close and reopen the same FCStd;
11. verify Undo and Redo;
12. inspect Windows scaling at 100%;
13. inspect Windows scaling at 125%;
14. inspect Windows scaling at 150%;
15. inspect Windows scaling at 200%;
16. complete a session of at least 45 minutes without duplicate panels, inaccessible controls or captured shortcuts.

## Automated detection

The recorder can detect:

- active PartDesign Body;
- Sketcher object;
- Pad/Saliente object;
- Pad edit mode;
- Pocket/Corte object;
- Revolution object;
- Fillet/Redondeo object;
- Chamfer/Chaflán object;
- saved FCStd path;
- closure and reopening of the same saved file.

Detection is conservative. If a native object cannot be identified reliably, the step does not pass automatically.

## Manual evidence

The following steps require human confirmation:

- Undo and Redo behavior;
- Windows scale 100%, 125%, 150% and 200%;
- extended-session stability.

Manual confirmation asks for an observation and captures the interface at that moment. A tester can also mark any step as failed and record the defect.

## Evidence structure

The session writes:

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

Each recorded step includes:

- state: pending, passed or failed;
- timestamp;
- tester observation or detector result;
- screenshot path;
- active document name and FCStd path;
- native object names, labels and type IDs;
- BRep validity and volume when available;
- current 3D selection and subelements.

Nothing is uploaded automatically.

## Reopen verification

When the Save step passes, the recorder stores the absolute FCStd path and document instance name. The Reopen step passes only when the same file path is active after the previous document was absent or a new document instance was created.

This reduces false positives caused by capturing Save twice without actually closing the model.

## Acceptance result

The session is approved only when:

- every required step is passed;
- no step is failed;
- no step remains pending.

A completed JSON report is evidence for release review, not automatic authorization to build the executable.

## Remaining release decision

After alpha.13 automated stability and alpha.14 physical acceptance both pass, the release review must still confirm:

- interface screenshot quality;
- original visual identity and no proprietary assets;
- correct native profile, axis, face and edge bindings;
- no FCStd, STEP or BRep regression;
- no blocking or high-severity issue;
- explicit authorization to begin a separate packaging iteration.
