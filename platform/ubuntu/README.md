# SolidFreeCAD for Ubuntu

Ubuntu Linux x86-64 remains an official SolidFreeCAD Desktop target. Windows is currently prioritised, but Ubuntu work is preserved for future development.

## Preserved direction

The Ubuntu version will use:

- the same pinned official FreeCAD source as the Windows line unless a documented compatibility reason requires otherwise;
- the same shared SolidFreeCAD GUI overlay;
- Qt Widgets and C++;
- the official FreeCAD engine, OpenCASCADE, document system, workbenches and Python integration;
- classic FreeCAD mode as a compatibility fallback.

## Future deliverables

Potential Ubuntu deliverables include:

- a portable application archive;
- AppImage packaging;
- optional `.deb` packaging;
- GitHub Actions build artifacts;
- startup, FCStd, STEP and macro smoke tests shared with Windows where possible.

## Protection rule

Windows changes must not remove this target, introduce avoidable Win32-only code into shared modules or move shared behavior into Windows-only directories.
