#include "SolidGuiManager.h"

#include "SolidRibbonWidget.h"

#include <QMenuBar>
#include <QToolBar>

#include <Gui/Application.h>
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
    hideClassicChrome();

    ribbon_ = new QToolBar(tr("SolidFreeCAD Command Manager"), mainWindow_);
    ribbon_->setObjectName(QStringLiteral("SolidFreeCADRibbon"));
    ribbon_->setMovable(false);
    ribbon_->setFloatable(false);
    ribbon_->setAllowedAreas(Qt::TopToolBarArea);
    ribbon_->setContentsMargins(0, 0, 0, 0);
    ribbon_->setMinimumHeight(137);
    ribbon_->setMaximumHeight(137);
    ribbon_->setStyleSheet(QStringLiteral(R"QSS(
        QToolBar#SolidFreeCADRibbon {
            background: #f2f3f5;
            border: 0;
            margin: 0;
            padding: 0;
            spacing: 0;
        }
        QToolBar#SolidFreeCADRibbon::handle {
            width: 0;
            height: 0;
        }
    )QSS"));

    ribbonShell_ = new SolidRibbonWidget(ribbon_);
    ribbon_->addWidget(ribbonShell_);

    auto& manager = Gui::Application::Instance->commandManager();
    commandChangedConnection_ = manager.signalChanged.connect([this]() {
        rebuildRibbon();
        hideClassicChrome();
    });

    mainWindow_->addToolBar(Qt::TopToolBarArea, ribbon_);
    ribbon_->show();
    return true;
}

void SolidGuiManager::uninstall()
{
    commandChangedConnection_.disconnect();

    if (ribbon_) {
        if (mainWindow_) {
            mainWindow_->removeToolBar(ribbon_);
        }

        ribbon_->deleteLater();
        ribbon_ = nullptr;
        ribbonShell_ = nullptr;
    }

    restoreClassicChrome();
    mainWindow_ = nullptr;
}

bool SolidGuiManager::isInstalled() const
{
    return ribbon_ != nullptr;
}

void SolidGuiManager::hideClassicChrome()
{
    if (!mainWindow_) {
        return;
    }

    QMenuBar* menu = mainWindow_->menuBar();
    if (menu && menu->isVisible()) {
        hiddenMenuBar_ = menu;
        menu->hide();
    }

    const auto toolbars = mainWindow_->findChildren<QToolBar*>(QString(), Qt::FindDirectChildrenOnly);
    for (QToolBar* toolbar : toolbars) {
        if (!toolbar || toolbar == ribbon_ || !toolbar->isVisible()) {
            continue;
        }

        bool alreadyTracked = false;
        for (const QPointer<QToolBar>& tracked : hiddenToolbars_) {
            if (tracked == toolbar) {
                alreadyTracked = true;
                break;
            }
        }

        if (!alreadyTracked) {
            hiddenToolbars_.append(toolbar);
        }
        toolbar->hide();
    }
}

void SolidGuiManager::restoreClassicChrome()
{
    if (hiddenMenuBar_) {
        hiddenMenuBar_->show();
        hiddenMenuBar_.clear();
    }

    for (const QPointer<QToolBar>& toolbar : hiddenToolbars_) {
        if (toolbar) {
            toolbar->show();
        }
    }
    hiddenToolbars_.clear();
}

void SolidGuiManager::rebuildRibbon()
{
    if (ribbonShell_) {
        ribbonShell_->rebuild();
    }
}

}  // namespace SolidFreeCAD
