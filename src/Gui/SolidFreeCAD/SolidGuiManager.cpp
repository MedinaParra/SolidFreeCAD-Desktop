#include "SolidGuiManager.h"

#include "SolidRibbonWidget.h"

#include <QApplication>
#include <QDockWidget>
#include <QEvent>
#include <QMenuBar>
#include <QTimer>
#include <QToolBar>
#include <QWidget>

#include <App/Application.h>
#include <Gui/Application.h>
#include <Gui/Command.h>
#include <Gui/DockWindowManager.h>
#include <Gui/MainWindow.h>

namespace
{
constexpr unsigned long rgba(unsigned char red,
                             unsigned char green,
                             unsigned char blue,
                             unsigned char alpha = 255)
{
    return (static_cast<unsigned long>(red) << 24)
        | (static_cast<unsigned long>(green) << 16)
        | (static_cast<unsigned long>(blue) << 8)
        | static_cast<unsigned long>(alpha);
}
}  // namespace

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
    if (qApp) {
        qApp->installEventFilter(this);
    }

    applyVisualPalette();

    ribbon_ = new QToolBar(tr("SolidFreeCAD Command Manager"), mainWindow_);
    ribbon_->setObjectName(QStringLiteral("SolidFreeCADRibbon"));
    ribbon_->setMovable(false);
    ribbon_->setFloatable(false);
    ribbon_->setAllowedAreas(Qt::TopToolBarArea);
    ribbon_->setContentsMargins(0, 0, 0, 0);
    ribbon_->setMinimumHeight(144);
    ribbon_->setMaximumHeight(144);
    ribbon_->setStyleSheet(QStringLiteral(R"QSS(
        QToolBar#SolidFreeCADRibbon {
            background: #f5f5f5;
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

    if (qApp) {
        qApp->removeEventFilter(this);
    }

    if (ribbon_) {
        if (mainWindow_) {
            mainWindow_->removeToolBar(ribbon_);
        }

        ribbon_->deleteLater();
        ribbon_ = nullptr;
        ribbonShell_ = nullptr;
    }

    restoreModelManager();
    restoreVisualPalette();
    restoreClassicChrome();
    mainWindow_ = nullptr;
}

bool SolidGuiManager::isInstalled() const
{
    return ribbon_ != nullptr;
}

bool SolidGuiManager::eventFilter(QObject* watched, QEvent* event)
{
    if (!mainWindow_ || !ribbon_ || !event) {
        return QObject::eventFilter(watched, event);
    }

    if (event->type() == QEvent::Show || event->type() == QEvent::WindowActivate) {
        const bool relevantWidget = watched == mainWindow_
            || qobject_cast<QMenuBar*>(watched)
            || qobject_cast<QToolBar*>(watched)
            || qobject_cast<QDockWidget*>(watched);

        if (relevantWidget) {
            QTimer::singleShot(0, this, [this]() { enforceSolidChrome(); });
        }
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
    ensureModelManager();
    ribbon_->show();
    mainWindow_->addToolBar(Qt::TopToolBarArea, ribbon_);
}

void SolidGuiManager::ensureModelManager()
{
    if (!mainWindow_) {
        return;
    }

    auto* dockManager = Gui::DockWindowManager::instance();
    if (!dockManager) {
        return;
    }

    QWidget* modelWidget = dockManager->findRegisteredDockWindow("Std_ComboView");
    if (!modelWidget) {
        return;
    }

    QDockWidget* dock = qobject_cast<QDockWidget*>(modelWidget->parentWidget());
    if (!dock || mainWindow_->dockWidgetArea(dock) == Qt::NoDockWidgetArea) {
        const QByteArray dockName = modelWidget->objectName().isEmpty()
            ? QByteArray("Model")
            : modelWidget->objectName().toUtf8();
        dock = dockManager->addDockWindow(dockName.constData(), modelWidget, Qt::LeftDockWidgetArea);
        if (!dock) {
            return;
        }
        modelManagerAddedBySolid_ = true;
    }

    if (!modelManagerDock_) {
        modelManagerOriginalTitle_ = dock->windowTitle();
        modelManagerOriginalStyle_ = modelWidget->styleSheet();
        modelManagerOriginalMinimumWidth_ = modelWidget->minimumWidth();
        modelManagerWasVisible_ = dock->isVisible();
    }

    modelManagerDock_ = dock;
    modelWidget->setMinimumWidth(250);
    modelWidget->setStyleSheet(QStringLiteral(R"QSS(
        QWidget {
            background: #f7f7f7;
            color: #202020;
        }
        QTabWidget::pane {
            background: #ffffff;
            border: 1px solid #b7b7b7;
            top: -1px;
        }
        QTabBar::tab {
            background: #e9e9e9;
            border: 1px solid #b7b7b7;
            padding: 4px 11px;
            min-height: 18px;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            border-bottom-color: #ffffff;
            font-weight: 600;
        }
        QTreeView, QTableView, QListView {
            background: #ffffff;
            alternate-background-color: #f6f7f8;
            border: 0;
            selection-background-color: #d9eaf7;
            selection-color: #101010;
        }
        QTreeView::item {
            min-height: 20px;
            padding: 1px 2px;
        }
        QTreeView::item:hover {
            background: #eef5fa;
        }
        QHeaderView::section {
            background: #ededed;
            border: 0;
            border-right: 1px solid #c7c7c7;
            border-bottom: 1px solid #c7c7c7;
            padding: 3px;
        }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            background: #ffffff;
            border: 1px solid #b6b6b6;
            border-radius: 1px;
            padding: 2px 4px;
        }
    )QSS"));
    dock->setMinimumWidth(260);
    dock->setWindowTitle(tr("Modelo"));
    mainWindow_->addDockWidget(Qt::LeftDockWidgetArea, dock);
    dock->show();
    modelWidget->show();
}

void SolidGuiManager::applyVisualPalette()
{
    if (visualPaletteApplied_) {
        return;
    }

    auto viewParameters = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/View"
    );

    previousGradient_ = viewParameters->GetBool("Gradient", true);
    previousRadialGradient_ = viewParameters->GetBool("RadialGradient", false);
    previousSimpleBackground_ = viewParameters->GetBool("Simple", false);
    previousUseMidColor_ = viewParameters->GetBool("UseBackgroundColorMid", false);
    previousBackgroundColor_ = viewParameters->GetUnsigned("BackgroundColor", rgba(20, 20, 163));
    previousBackgroundColor2_ = viewParameters->GetUnsigned("BackgroundColor2", rgba(101, 101, 101));
    previousBackgroundColor3_ = viewParameters->GetUnsigned("BackgroundColor3", rgba(45, 45, 45));
    previousBackgroundColor4_ = viewParameters->GetUnsigned("BackgroundColor4", rgba(111, 111, 147));
    previousDefaultShapeColor_ = viewParameters->GetUnsigned("DefaultShapeColor", rgba(204, 204, 230));
    previousSelectionColor_ = viewParameters->GetUnsigned("SelectionColor", rgba(41, 255, 41));
    previousHighlightColor_ = viewParameters->GetUnsigned("HighlightColor", rgba(255, 255, 23));

    viewParameters->SetBool("Gradient", true);
    viewParameters->SetBool("RadialGradient", false);
    viewParameters->SetBool("Simple", false);
    viewParameters->SetBool("UseBackgroundColorMid", false);
    viewParameters->SetUnsigned("BackgroundColor", rgba(248, 249, 250));
    viewParameters->SetUnsigned("BackgroundColor2", rgba(214, 220, 226));
    viewParameters->SetUnsigned("BackgroundColor3", rgba(235, 238, 241));
    viewParameters->SetUnsigned("BackgroundColor4", rgba(255, 255, 255));
    viewParameters->SetUnsigned("DefaultShapeColor", rgba(184, 198, 214));
    viewParameters->SetUnsigned("SelectionColor", rgba(54, 156, 217));
    viewParameters->SetUnsigned("HighlightColor", rgba(255, 198, 47));

    visualPaletteApplied_ = true;
}

void SolidGuiManager::restoreVisualPalette()
{
    if (!visualPaletteApplied_) {
        return;
    }

    auto viewParameters = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/View"
    );
    viewParameters->SetBool("Gradient", previousGradient_);
    viewParameters->SetBool("RadialGradient", previousRadialGradient_);
    viewParameters->SetBool("Simple", previousSimpleBackground_);
    viewParameters->SetBool("UseBackgroundColorMid", previousUseMidColor_);
    viewParameters->SetUnsigned("BackgroundColor", previousBackgroundColor_);
    viewParameters->SetUnsigned("BackgroundColor2", previousBackgroundColor2_);
    viewParameters->SetUnsigned("BackgroundColor3", previousBackgroundColor3_);
    viewParameters->SetUnsigned("BackgroundColor4", previousBackgroundColor4_);
    viewParameters->SetUnsigned("DefaultShapeColor", previousDefaultShapeColor_);
    viewParameters->SetUnsigned("SelectionColor", previousSelectionColor_);
    viewParameters->SetUnsigned("HighlightColor", previousHighlightColor_);

    visualPaletteApplied_ = false;
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

void SolidGuiManager::restoreModelManager()
{
    if (!modelManagerDock_) {
        return;
    }

    QWidget* modelWidget = modelManagerDock_->widget();
    if (modelWidget) {
        modelWidget->setMinimumWidth(modelManagerOriginalMinimumWidth_);
        modelWidget->setStyleSheet(modelManagerOriginalStyle_);
    }
    modelManagerDock_->setWindowTitle(modelManagerOriginalTitle_);

    if (modelManagerAddedBySolid_) {
        if (auto* dockManager = Gui::DockWindowManager::instance()) {
            QWidget* restoredWidget = dockManager->removeDockWindow("Model");
            if (restoredWidget) {
                restoredWidget->hide();
            }
        }
    }
    else if (!modelManagerWasVisible_) {
        modelManagerDock_->hide();
    }

    modelManagerDock_.clear();
    modelManagerOriginalTitle_.clear();
    modelManagerOriginalStyle_.clear();
    modelManagerOriginalMinimumWidth_ = 0;
    modelManagerWasVisible_ = false;
    modelManagerAddedBySolid_ = false;
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
