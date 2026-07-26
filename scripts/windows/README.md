# Windows scripts

This directory contains Windows-only automation for SolidFreeCAD Desktop.

## Current script

`Bootstrap-FreeCAD.ps1` performs a shallow checkout of the pinned official FreeCAD tag, including shallow submodules. It does not patch or modify the upstream source.

Example:

```powershell
./scripts/windows/Bootstrap-FreeCAD.ps1 \
  -Tag "1.1.1" \
  -Destination ".work/FreeCAD"
```

## Planned scripts

- dependency bootstrap and cache preparation;
- unmodified baseline compilation;
- SolidFreeCAD overlay application;
- portable runtime collection;
- installer packaging;
- smoke-test execution.

Windows scripts must not contain shared GUI or CAD behavior that belongs under `src/`.
