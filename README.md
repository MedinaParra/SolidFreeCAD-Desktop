# SolidFreeCAD Desktop

SolidFreeCAD Desktop is a Qt/C++ graphical interface built on the official FreeCAD source code.

## Foundation

- Official upstream: `FreeCAD/FreeCAD`
- Current pinned source tag: `1.1.1`
- GUI technology: Qt Widgets and C++
- CAD kernel and document system: official FreeCAD components
- Supported development tracks: Windows x64 and Ubuntu Linux x86-64

SolidFreeCAD does not replace OpenCASCADE, FCStd, PartDesign, Sketcher, Assembly, TechDraw, FEM, Python, Coin3D or the official command framework. It reorganizes those capabilities through a mechanical-design-oriented interface inspired by the existing SolidFreeCAD Android concept.

## Platform strategy

The project keeps both desktop targets active:

- **Windows x64 is the current delivery priority.** Work will focus on reproducible GitHub Actions builds, a portable package and a Windows installer.
- **Ubuntu Linux remains an official future target.** Existing Ubuntu plans are preserved and platform-specific work must not be removed while Windows development advances.
- Shared CAD, GUI and branding code belongs in common directories. Platform-specific scripts, packaging and workflows belong under their own platform directories.

See [`docs/platform-strategy.md`](docs/platform-strategy.md) for the repository rules.

## Repository layout

```text
.github/workflows/        GitHub Actions workflows by platform
docs/                     Architecture and roadmap documentation
platform/windows/         Windows-specific packaging and platform notes
platform/ubuntu/          Ubuntu-specific packaging and platform notes
scripts/windows/          Windows bootstrap, build and packaging scripts
scripts/ubuntu/           Ubuntu bootstrap, build and packaging scripts
src/                      Shared SolidFreeCAD source and GUI overlay
branding/                 Shared icons, splash screens and product assets
```

## Repository strategy

This repository starts as a reproducible GUI overlay. Build scripts obtain the official FreeCAD source, apply the isolated SolidFreeCAD layer and compile the resulting application.

This keeps iterations small and reviewable while ensuring builds use the official FreeCAD engine.

## Current milestone: Windows foundation

The first Windows milestone targets:

- Windows x64 build on GitHub Actions.
- Official FreeCAD engine and 3D viewer.
- SolidFreeCAD ribbon prototype.
- Native New, Open, Save, Undo and Redo commands.
- Native fit-all and isometric view commands.
- FCStd and STEP/STP opening.
- Portable ZIP artifact.
- Installer artifact after the portable build is stable.
- Classic FreeCAD interface retained as compatibility mode.

## Ubuntu continuity

Ubuntu development is not cancelled or replaced. Its source, documentation and future workflows remain under `platform/ubuntu` and `scripts/ubuntu`. Windows-specific changes must not introduce assumptions that prevent a later Linux build.
