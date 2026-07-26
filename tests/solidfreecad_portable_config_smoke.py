"""Validate SolidFreeCAD portable user configuration through FreeCADCmd."""

import FreeCAD as App


general = App.ParamGet("User parameter:BaseApp/Preferences/General")
autoload = general.GetString("AutoloadModule", "")
last_module = general.GetString("LastModule", "")

if autoload != "SolidFreeCADWorkbench":
    raise RuntimeError(f"Unexpected AutoloadModule: {autoload!r}")

if last_module != "SolidFreeCADWorkbench":
    raise RuntimeError(f"Unexpected LastModule: {last_module!r}")

print("SolidFreeCAD portable configuration smoke test passed.")
