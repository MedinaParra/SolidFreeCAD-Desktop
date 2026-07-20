#pragma once

namespace Gui
{
class MainWindow;
}

namespace SolidFreeCAD
{

bool isGuiEnabled();
void installGui(Gui::MainWindow* mainWindow);
void uninstallGui();

}  // namespace SolidFreeCAD
