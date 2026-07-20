#include "SolidGuiBootstrap.h"

#include "SolidGuiManager.h"

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

    guiManager->install(mainWindow);
}

void uninstallGui()
{
    guiManager.reset();
}

}  // namespace SolidFreeCAD
