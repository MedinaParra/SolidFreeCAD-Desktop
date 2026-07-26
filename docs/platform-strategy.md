# Platform strategy

## Objective

SolidFreeCAD Desktop will support Windows x64 and Ubuntu Linux x86-64 from one shared codebase. Windows is the immediate release priority, but Ubuntu remains a first-class planned target.

## Non-destructive platform rule

Windows work must not delete, overwrite or permanently disable Ubuntu-specific source, scripts, documentation or build decisions. The same rule applies in reverse when Ubuntu development resumes.

## Directory ownership

- `src/`, `branding/` and shared tests contain platform-neutral product code.
- `platform/windows/` contains Windows packaging, manifests, resources and platform notes.
- `platform/ubuntu/` contains Ubuntu packaging, desktop integration and platform notes.
- `scripts/windows/` and `scripts/ubuntu/` contain platform-specific automation.
- `.github/workflows/` uses one named workflow per platform unless a shared matrix is demonstrably simpler.

## Shared-core requirements

Shared SolidFreeCAD code must avoid direct Win32 or Linux API calls unless hidden behind a narrow platform abstraction. Qt and FreeCAD APIs are preferred wherever possible.

The following capabilities should remain shared:

- application shell and ribbon
- document tree and property panels
- commands and task panels
- FCStd, STEP and STP workflows
- sketch and PartDesign command integration
- branding assets where the operating system does not require a special format
- automated functional tests

## Windows delivery sequence

1. Reproducible dependency and upstream-source bootstrap.
2. Compile an unmodified FreeCAD baseline on Windows x64.
3. Apply the SolidFreeCAD overlay without breaking classic mode.
4. Produce a portable ZIP artifact.
5. Add smoke tests for startup, FCStd opening and STEP import.
6. Produce an installer.
7. Add release automation and optional code signing.

## Ubuntu continuity sequence

Ubuntu work remains documented and isolated while Windows is prioritised. When resumed, it should:

1. compile the same shared overlay against the pinned upstream source;
2. retain classic FreeCAD compatibility mode;
3. produce a portable archive or AppImage/deb packaging path;
4. run the same shared functional tests where supported.

## Pull-request rule

Every platform-specific pull request must state:

- which platform it changes;
- whether shared code changes are included;
- how the other platform was protected from regression;
- what was actually built or tested.
