"""SolidFreeCAD mechanical-design workbench registration."""

import FreeCADGui as Gui


def _available(command_names):
    registered = set(Gui.listCommands())
    return [command for command in command_names if command in registered]


class SolidFreeCADWorkbench(Gui.Workbench):
    MenuText = "SolidFreeCAD"
    ToolTip = "Diseño mecánico paramétrico basado en FreeCAD"

    def Initialize(self):
        from SolidFreeCAD import Commands  # noqa: F401

        # Importing these GUI modules registers their native command sets.
        # The imports remain optional so a reduced FreeCAD build can still
        # start the SolidFreeCAD workbench with the commands it provides.
        try:
            import PartDesignGui  # noqa: F401
        except ImportError:
            pass

        try:
            import SketcherGui  # noqa: F401
        except ImportError:
            pass

        file_commands = _available(
            [
                "Std_New",
                "Std_Open",
                "Std_Save",
                "Std_Undo",
                "Std_Redo",
            ]
        )
        mechanical_commands = _available(
            [
                "SFC_CreatePart",
                "SFC_CreateShaft",
                "PartDesign_Body",
                "Sketcher_NewSketch",
                "PartDesign_Pad",
                "PartDesign_Pocket",
                "PartDesign_Revolution",
                "PartDesign_Fillet",
                "PartDesign_Chamfer",
            ]
        )
        view_commands = _available(
            [
                "SFC_FitAxonometric",
                "ViewFit",
                "ViewAxonometric",
                "Std_ViewFront",
                "Std_ViewTop",
                "Std_ViewRight",
            ]
        )

        if file_commands:
            self.appendToolbar("Archivo", file_commands)
            self.appendMenu("Archivo", file_commands)

        if mechanical_commands:
            self.appendToolbar("Modelado mecánico", mechanical_commands)
            self.appendMenu("SolidFreeCAD", mechanical_commands)

        if view_commands:
            self.appendToolbar("Vista", view_commands)
            self.appendMenu("Vista", view_commands)

    def Activated(self):
        main_window = Gui.getMainWindow()
        main_window.setWindowTitle("SolidFreeCAD Desktop")

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(SolidFreeCADWorkbench())
