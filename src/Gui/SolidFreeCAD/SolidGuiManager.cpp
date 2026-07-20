#include "SolidGuiManager.h"

#include "SolidCommandSearch.h"

#include <QAction>
#include <QLabel>
#include <QSize>
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
    ribbon_->setIconSize(QSize(30, 30));
    ribbon_->setMinimumHeight(82);
    ribbon_->setStyleSheet(QStringLiteral(R"QSS(
        QToolBar#SolidFreeCADRibbon {
            background: #f5f7fa;
            border: 0;
            border-bottom: 1px solid #c8d0da;
            spacing: 3px;
            padding: 4px 8px;
        }
        QToolBar#SolidFreeCADRibbon QToolButton {
            background: transparent;
            border: 1px solid transparent;
            border-radius: 4px;
            min-width: 54px;
            padding: 4px 6px;
        }
        QToolBar#SolidFreeCADRibbon QToolButton:hover {
            background: #e7f1fb;
            border-color: #8bb8e8;
        }
        QToolBar#SolidFreeCADRibbon QToolButton:pressed,
        QToolBar#SolidFreeCADRibbon QToolButton:checked {
            background: #d5e9fb;
            border-color: #4f96d9;
        }
        QToolBar#SolidFreeCADRibbon QToolButton:disabled {
            color: #8d98a5;
        }
        QLabel#SolidFreeCADRibbonSection {
            color: #33475b;
            font-weight: 600;
            padding: 0 4px;
        }
        QLineEdit#SolidFreeCADCommandSearch {
            background: white;
            border: 1px solid #aeb9c5;
            border-radius: 5px;
            padding: 6px 9px;
            margin: 7px 4px;
        }
        QLineEdit#SolidFreeCADCommandSearch:focus {
            border-color: #2878bd;
        }
    )QSS"));

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
    ribbon_->addWidget(new SolidCommandSearch(ribbon_));

    addSection(tr("File"), {
        "Std_New",
        "Std_Open",
        "Std_Save",
        "Std_Undo",
        "Std_Redo",
    });

    addSection(tr("View"), {
        "Std_ViewFitAll",
        "Std_ViewIsometric",
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
