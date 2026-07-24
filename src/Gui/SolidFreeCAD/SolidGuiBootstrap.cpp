#include "SolidGuiBootstrap.h"

#include "SolidActiveSketch.h"
#include "SolidDocumentWorkspace.h"
#include "SolidGuiManager.h"
#include "SolidPartDesignMvp.h"
#include "SolidPropertyManager.h"
#include "SolidSketchEnhancements.h"
#include "SolidTaskOverlayGuard.h"
#include "SolidWorkspacePolish.h"

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
std::unique_ptr<SolidPropertyManager> propertyManager;
std::unique_ptr<SolidSketchEnhancements> sketchEnhancements;
std::unique_ptr<SolidWorkspacePolish> workspacePolish;
std::unique_ptr<SolidDocumentWorkspace> documentWorkspace;
std::unique_ptr<SolidPartDesignMvp> partDesignMvp;
std::unique_ptr<SolidActiveSketch> activeSketch;
std::unique_ptr<SolidTaskOverlayGuard> taskOverlayGuard;

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
    if (!propertyManager) {
        propertyManager = std::make_unique<SolidPropertyManager>();
    }
    if (!sketchEnhancements) {
        sketchEnhancements = std::make_unique<SolidSketchEnhancements>();
    }
    if (!workspacePolish) {
        workspacePolish = std::make_unique<SolidWorkspacePolish>();
    }
    if (!documentWorkspace) {
        documentWorkspace = std::make_unique<SolidDocumentWorkspace>();
    }
    if (!partDesignMvp) {
        partDesignMvp = std::make_unique<SolidPartDesignMvp>();
    }
    if (!activeSketch) {
        activeSketch = std::make_unique<SolidActiveSketch>();
    }
    if (!taskOverlayGuard) {
        taskOverlayGuard = std::make_unique<SolidTaskOverlayGuard>();
    }

    guiManager->install(mainWindow);
    propertyManager->install(mainWindow);
    sketchEnhancements->install(mainWindow);
    workspacePolish->install(mainWindow);
    documentWorkspace->install(mainWindow);
    partDesignMvp->install(mainWindow);
    activeSketch->install(mainWindow);
    taskOverlayGuard->install(mainWindow);
}

void uninstallGui()
{
    taskOverlayGuard.reset();
    activeSketch.reset();
    partDesignMvp.reset();
    documentWorkspace.reset();
    workspacePolish.reset();
    sketchEnhancements.reset();
    propertyManager.reset();
    guiManager.reset();
}

}  // namespace SolidFreeCAD
