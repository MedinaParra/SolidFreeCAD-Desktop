# SolidFreeCAD alpha.7 professional GUI

Alpha.7 replaces the stacked alpha.5/alpha.6 panels with one coherent Windows desktop while preserving the native FreeCAD 1.1.1 engine, OpenCASCADE BRep geometry and FCStd documents.

## Visual target

The interface follows familiar professional mechanical-CAD conventions without copying proprietary branding or artwork:

- clean quick-access strip with file actions and command search;
- full-width tabbed command ribbon;
- grouped large and compact feature buttons;
- narrow left design tree with Model, Properties and Configurations;
- neutral light modelling viewport;
- single SolidFreeCAD application menu;
- hidden native FreeCAD toolbars while SolidFreeCAD is active.

## Ribbon tabs

- Operations
- Sketch
- Surfaces
- Sheet metal
- Weldments
- Evaluate
- Shaft
- Assembly

Commands continue to delegate to registered FreeCAD commands. Missing optional workbenches leave their buttons disabled rather than breaking the workspace.

## Native task compatibility

FreeCAD's Combo View is moved to the left and tabified with the SolidFreeCAD design manager. It remains available for native task dialogs such as Sketcher, but is hidden on normal startup so the application opens with a clean mechanical-CAD layout.

## Legal and design boundary

Alpha.7 uses original SolidFreeCAD Python/Qt code and the existing original SVG icon pack. It does not ship SolidWorks trademarks, logos, screenshots, source code or proprietary icon resources.
