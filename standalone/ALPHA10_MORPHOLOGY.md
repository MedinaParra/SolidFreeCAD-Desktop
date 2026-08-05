# SolidFreeCAD alpha.10 — integrated mechanical-CAD morphology

Alpha.10 removes the visible default menu/chrome and restructures the standalone window around a fixed professional CAD layout.

## Window contract

- operating-system title bar only;
- custom SolidFreeCAD header replacing `QMenuBar`;
- integrated text menus, centered document name and command search;
- CommandManager fixed across the full top width;
- FeatureManager/PropertyManager fixed at the left;
- no secondary right-side property panel;
- clean central FreeCAD document viewport;
- compact vertical view toolbar at the right;
- compact status and unit bar at the bottom.

## Manager contract

The same left location contains:

1. design tree;
2. contextual PropertyManager;
3. configurations;
4. display manager foundation.

Starting Sketch or Pad switches the left manager to the contextual property definition. Accept or cancel returns to the design tree.

## Native FreeCAD chrome

SolidFreeCAD hides the host menu bar, status bar, toolbars and docks before extracting the document viewport. Standalone files remain prohibited from invoking `Gui.runCommand()`.

## Intellectual property

The implementation follows general professional mechanical-CAD layout and interaction patterns with original SolidFreeCAD code and identity. It does not include SolidWorks code, logos, icons or proprietary artwork.
