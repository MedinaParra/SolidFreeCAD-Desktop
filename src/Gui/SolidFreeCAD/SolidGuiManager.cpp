#include "SolidGuiManager.h"

#include <QAction>
#include <QLabel>
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
    if (!mainWindow || !Gui::Application::Instance) {
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

    auto& manager = Gui::Application::Instance->commandManager();
    commandChangedConnection_ = manager.signalChanged.connect([this]() {
        if (ribbon_) {
            rebuildRibbon();
        }
    });

    rebuildRibbon();
    mainWindow_->addToolBar(Qt::TopToolBarArea, ribbon_);
    ribbon_->show();
    return true;
}

void SolidGuiManager::uninstall()
{
    commandChangedConnection_.disconnect();

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

void SolidGuiManager::rebuildRibbon()
{
    if (!ribbon_) {
        return;
    }

    ribbon_->clear();

    addSection(tr("File"), {
        "Std_New",
        "Std_Open",
        "Std_Save",
        "Std_Undo",
        "Std_Redo",
    });

    addSection(tr("View"), {
        "Std_ViewFitAll",
        "Std_ViewAxonometric",
    });

    addSection(tr("Part Design"), {
        "PartDesign_Body",
        "PartDesign_NewSketch",
        "PartDesign_Pad",
        "PartDesign_Pocket",
        "PartDesign_Fillet",
        "PartDesign_Chamfer",
    });
}

void SolidGuiManager::addSection(
    const QString& title,
    std::initializer_list<const char*> commandNames
)
{
    if (!ribbon_) {
        return;
    }

    if (!ribbon_->actions().isEmpty()) {
        ribbon_->addSeparator();
    }

    auto* label = new QLabel(title, ribbon_);
    label->setObjectName(QStringLiteral("SolidFreeCADRibbonSection"));
    label->setMargin(6);
    ribbon_->addWidget(label);

    for (const char* commandName : commandNames) {
        addCommand(commandName);
    }
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
    unavailable->setToolTip(tr("Command available after loading the related FreeCAD workbench"));
    return false;
}

}  // namespace SolidFreeCAD
