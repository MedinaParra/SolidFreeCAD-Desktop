#include "SolidGuiManager.h"

#include "SolidRibbonWidget.h"

#include <QDockWidget>
#include <QEvent>
#include <QMenuBar>
#include <QTimer>
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
    mainWindow_->installEventFilter(this);

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
        enforceSolidChrome();
    });

    mainWindow_->addToolBar(Qt::TopToolBarArea, ribbon_);
    ribbon_->show();
    enforceSolidChrome();

    // FreeCAD restores menus, workbench toolbars and dock state during startup.
    // Reapply the SolidFreeCAD shell after those deferred restoration passes.
    QTimer::singleShot(0, this, [this]() { enforceSolidChrome(); });
    QTimer::singleShot(250, this, [this]() { enforceSolidChrome(); });
    QTimer::singleShot(750, this, [this]() { enforceSolidChrome(); });
    return true;
}

void SolidGuiManager::uninstall()
{
    commandChangedConnection_.disconnect();

    if (mainWindow_) {
        mainWindow_->removeEventFilter(this);
    }

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

bool SolidGuiManager::eventFilter(QObject* watched, QEvent* event)
{
    if (watched == mainWindow_ && event
        && (event->type() == QEvent::Show || event->type() == QEvent::WindowActivate)) {
        QTimer::singleShot(0, this, [this]() { enforceSolidChrome(); });
    }

    return QObject::eventFilter(watched, event);
}

void SolidGuiManager::enforceSolidChrome()
{
    if (!mainWindow_ || !ribbon_) {
        return;
    }

    hideClassicChrome();
    hideBottomUtilityDocks();
    ribbon_->show();
    mainWindow_->addToolBar(Qt::TopToolBarArea, ribbon_);
}

void SolidGuiManager::hideClassicChrome()
{
    if (!mainWindow_) {
        return;
    }

    QMenuBar* menu = mainWindow_->menuBar();
    if (menu) {
        if (!hiddenMenuBar_) {
            hiddenMenuBar_ = menu;
        }
        menu->hide();
    }

    const auto toolbars = mainWindow_->findChildren<QToolBar*>(QString(), Qt::FindDirectChildrenOnly);
    for (QToolBar* toolbar : toolbars) {
        if (!toolbar || toolbar == ribbon_ || toolbar->isHidden()) {
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

void SolidGuiManager::hideBottomUtilityDocks()
{
    if (!mainWindow_) {
        return;
    }

    const auto docks = mainWindow_->findChildren<QDockWidget*>(QString(), Qt::FindDirectChildrenOnly);
    for (QDockWidget* dock : docks) {
        if (!dock || dock->isHidden()
            || mainWindow_->dockWidgetArea(dock) != Qt::BottomDockWidgetArea) {
            continue;
        }

        bool alreadyTracked = false;
        for (const QPointer<QDockWidget>& tracked : hiddenDocks_) {
            if (tracked == dock) {
                alreadyTracked = true;
                break;
            }
        }

        if (!alreadyTracked) {
            hiddenDocks_.append(dock);
        }
        dock->hide();
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

    for (const QPointer<QDockWidget>& dock : hiddenDocks_) {
        if (dock) {
            dock->show();
        }
    }
    hiddenDocks_.clear();
}

void SolidGuiManager::rebuildRibbon()
{
    if (ribbonShell_) {
        ribbonShell_->rebuild();
    }
}

}  // namespace SolidFreeCAD
