# SolidFreeCAD shared overlay

This directory contains application features that are shared by every desktop
platform. It is not a Windows fork of the FreeCAD engine.

## Current module

`Mod/SolidFreeCAD` is installed into the `Mod` directory of an official
FreeCAD runtime. The first preview provides:

- a dedicated SolidFreeCAD workbench;
- native document, Part Design, Sketcher and view commands;
- a parametric stepped shaft;
- editable main and shoulder dimensions;
- an optional editable keyway;
- a headless geometry smoke test.

## Platform rule

Windows packaging copies this overlay into the validated Windows runtime.
Future Ubuntu packaging must install the same files rather than creating a
second implementation. Platform-specific launchers, installers and build
scripts remain outside this directory.
