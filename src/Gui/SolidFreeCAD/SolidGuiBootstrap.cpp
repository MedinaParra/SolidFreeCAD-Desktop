#include "SolidGuiBootstrap.h"

#include "SolidGuiManager.h"
#include "SolidSketchEnhancements.h"

#include <memory>
#include <string>

#include <QtGlobal>

#include <App/Application.h>
#include <Base/Parameter.h>

namespace SolidFreeCAD
{
namespace
{
std::unique_ptr<SolidGuiManager> guiManager;
std::unique_ptr<SolidSketchEnhancements> sketchEnhancements;

bool classicModeRequestedByEnvironment()
{
    bool parsed = false;
    const int value = qEnvironmentVariableIntValue("SOLIDFREECAD_CLASSIC_MODE", &parsed);
    return parsed && value != 0;
}
}

bool isGuiEnabled()
{
    if (classicModeRequestedByEnvironment()) {
        return false;
    }

    const auto group = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/SolidFreeCAD"
    );
    const std::string mode = group->GetASCII("InterfaceMode", "SolidFreeCAD");
    return mode != "Classic";
}

void installGui(Gui::MainWindow* mainWindow)
{
    if (!isGuiEnabled()) {
        return;
    }

    if (!guiManager) {
        guiManager = std::make_unique<SolidGuiManager>();
    }
    if (!sketchEnhancements) {
        sketchEnhancements = std::make_unique<SolidSketchEnhancements>();
    }

    guiManager->install(mainWindow);
    sketchEnhancements->install(mainWindow);
}

void uninstallGui()
{
    sketchEnhancements.reset();
    guiManager.reset();
}

}  // namespace SolidFreeCAD
