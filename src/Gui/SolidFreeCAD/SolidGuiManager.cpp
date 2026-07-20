#include "SolidGuiManager.h"

#include <QAction>
#include <QToolBar>

#include <Gui/Application.h>
#include <Gui/Command.h>
#include <Gui/MainWindow.h>

namespace SolidFreeCAD
{

SolidGuiManager::SolidGuiManager(QObject* parent)
    : QObject(parent)
{}

SolidGuiManager::~SolidGuiManager()
{
    uninstall();
}

bool SolidGuiManager::install(Gui::MainWindow* mainWindow)
{
    if (!mainWindow) {
        return false;
    }

    if (ribbon_) {
        return true;
    }

    mainWindow_ = mainWindow;
    ribbon_ = new QToolBar(tr("SolidFreeCAD"), mainWindow_);
    ribbon_->setObjectName(QStringLiteral("SolidFreeCADRibbon"));
    ribbon_->setMovable(false);
    ribbon_->setFloatable(false);
    ribbon_->setToolButtonStyle(Qt::ToolButtonTextUnderIcon);

    addCommand("Std_New");
    addCommand("Std_Open");
    addCommand("Std_Save");
    ribbon_->addSeparator();
    addCommand("Std_Undo");
    addCommand("Std_Redo");
    ribbon_->addSeparator();
    addCommand("Std_ViewFitAll");
    addCommand("Std_ViewAxonometric");

    mainWindow_->addToolBar(Qt::TopToolBarArea, ribbon_);
    ribbon_->show();
    return true;
}

void SolidGuiManager::uninstall()
{
    if (!ribbon_) {
        mainWindow_ = nullptr;
        return;
    }

    if (mainWindow_) {
        mainWindow_->removeToolBar(ribbon_);
    }

    ribbon_->deleteLater();
    ribbon_ = nullptr;
    mainWindow_ = nullptr;
}

bool SolidGuiManager::isInstalled() const
{
    return ribbon_ != nullptr;
}

bool SolidGuiManager::addCommand(const char* commandName)
{
    if (!ribbon_ || !commandName || !*commandName || !Gui::Application::Instance) {
        return false;
    }

    auto& manager = Gui::Application::Instance->commandManager();
    if (Gui::Command* command = manager.getCommandByName(commandName)) {
        command->addTo(ribbon_);
        return true;
    }

    QAction* unavailable = ribbon_->addAction(QString::fromLatin1(commandName));
    unavailable->setEnabled(false);
    unavailable->setToolTip(tr("FreeCAD command is not available in this build"));
    return false;
}

}  // namespace SolidFreeCAD
