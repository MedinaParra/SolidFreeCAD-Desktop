# SolidFreeCAD Desktop

SolidFreeCAD Desktop is a new Qt/C++ graphical interface built on the official FreeCAD 1.1.1 source code.

## Foundation

- Official upstream: `FreeCAD/FreeCAD`
- Pinned source tag: `1.1.1`
- Initial target: Ubuntu Linux x86-64
- GUI technology: Qt Widgets and C++
- CAD kernel and document system: official FreeCAD components

SolidFreeCAD does not replace OpenCASCADE, FCStd, PartDesign, Sketcher, Assembly, TechDraw, FEM, Python, Coin3D or the official command framework. It reorganizes those capabilities through a new mechanical-design-oriented interface inspired by the existing SolidFreeCAD Android concept.

## Repository strategy

This repository starts as a reproducible GUI overlay. Build scripts obtain the official FreeCAD 1.1.1 source, apply the isolated `src/Gui/SolidFreeCAD` layer and compile the resulting application.

This keeps the first iterations small and reviewable while ensuring every build uses the official FreeCAD source.

## Status

The project is in bootstrap development. The first milestone is a runnable Ubuntu build with:

- Official FreeCAD 1.1.1 engine and 3D viewer.
- SolidFreeCAD ribbon prototype.
- Native New, Open, Save, Undo and Redo commands.
- Native fit-all and isometric view commands.
- Classic FreeCAD interface retained as compatibility mode.
