"""SolidFreeCAD mechanical-design workbench registration."""

import FreeCADGui as Gui


class SolidFreeCADWorkbench(Gui.Workbench):
    MenuText = "SolidFreeCAD"
    ToolTip = "Diseño mecánico paramétrico basado en FreeCAD"

    def Initialize(self):
        from SolidFreeCAD import Commands  # noqa: F401

        file_commands = [
            "Std_New",
            "Std_Open",
            "Std_Save",
            "Std_Undo",
            "Std_Redo",
        ]
        mechanical_commands = [
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
        view_commands = [
            "SFC_FitAxonometric",
            "ViewFit",
            "ViewAxonometric",
            "Std_ViewFront",
            "Std_ViewTop",
            "Std_ViewRight",
        ]

        self.appendToolbar("Archivo", file_commands)
        self.appendToolbar("Modelado mecánico", mechanical_commands)
        self.appendToolbar("Vista", view_commands)

        self.appendMenu("Archivo", file_commands)
        self.appendMenu("SolidFreeCAD", mechanical_commands)
        self.appendMenu("Vista", view_commands)

    def Activated(self):
        main_window = Gui.getMainWindow()
        main_window.setWindowTitle("SolidFreeCAD Desktop")

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(SolidFreeCADWorkbench())
