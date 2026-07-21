#include "SolidWorkspacePolish.h"

#include "SolidIconFactory.h"

#include <QAction>
#include <QBoxLayout>
#include <QDockWidget>
#include <QLabel>
#include <QSize>
#include <QStackedWidget>
#include <QTabBar>
#include <QTabWidget>
#include <QTimer>
#include <QToolBar>
#include <QToolButton>
#include <QVBoxLayout>
#include <QWidget>

#include <App/Application.h>
#include <App/Document.h>
#include <Gui/MainWindow.h>

namespace
{

bool isPrimaryCommand(const QString& commandName)
{
    return commandName == QStringLiteral("PartDesign_Pad")
        || commandName == QStringLiteral("PartDesign_Pocket")
        || commandName == QStringLiteral("PartDesign_Hole")
        || commandName == QStringLiteral("PartDesign_Revolution")
        || commandName == QStringLiteral("Sketcher_CompDimensionTools")
        || commandName == QStringLiteral("Sketcher_CompCreateRectangles");
}

}  // namespace

namespace SolidFreeCAD
{

SolidWorkspacePolish::SolidWorkspacePolish(QObject* parent)
    : QObject(parent)
{}

SolidWorkspacePolish::~SolidWorkspacePolish()
{
    uninstall();
}

bool SolidWorkspacePolish::install(Gui::MainWindow* mainWindow)
{
    if (installed_ || !mainWindow) {
        return installed_;
    }

    mainWindow_ = mainWindow;
    installed_ = true;

    for (const int delay : {0, 350, 900, 1700, 2600}) {
        QTimer::singleShot(delay, this, [this]() { apply(); });
    }
    return true;
}

void SolidWorkspacePolish::uninstall()
{
    installed_ = false;
    contextBadge_.clear();
    documentTitle_.clear();
    mainWindow_ = nullptr;
}

bool SolidWorkspacePolish::isInstalled() const
{
    return installed_;
}

void SolidWorkspacePolish::apply()
{
    if (!installed_ || !mainWindow_) {
        return;
    }

    auto* ribbon = mainWindow_->findChild<QToolBar*>(QStringLiteral("SolidFreeCADRibbon"));
    if (ribbon) {
        polishRibbon(ribbon);
    }
    polishSidePanels();
}

void SolidWorkspacePolish::polishRibbon(QToolBar* ribbon)
{
    if (!ribbon) {
        return;
    }

    ribbon->setMinimumHeight(158);
    ribbon->setMaximumHeight(158);

    QWidget* shell = ribbon->findChild<QWidget*>(QStringLiteral("SolidFreeCADRibbonShell"));
    auto* tabs = ribbon->findChild<QTabBar*>(QStringLiteral("SolidFreeCADRibbonTabs"));
    auto* pages = ribbon->findChild<QStackedWidget*>(QStringLiteral("SolidFreeCADRibbonPages"));
    if (!shell || !tabs || !pages) {
        return;
    }

    shell->setMinimumHeight(151);
    shell->setMaximumHeight(151);
    tabs->setMinimumHeight(27);
    tabs->setMaximumHeight(27);
    pages->setMinimumHeight(88);
    pages->setMaximumHeight(88);

    if (auto* layout = qobject_cast<QVBoxLayout*>(shell->layout())) {
        layout->removeWidget(tabs);
        layout->removeWidget(pages);
        layout->insertWidget(1, tabs);
        layout->insertWidget(2, pages);
    }

    if (!shell->property("SolidFreeCADWorkspacePolished").toBool()) {
        shell->setStyleSheet(shell->styleSheet() + QStringLiteral(R"QSS(
            QLabel#SolidFreeCADContextBadge {
                color: #1f5f87;
                background: #e5f1f8;
                border: 1px solid #b9d7e8;
                border-radius: 8px;
                font-size: 9px;
                font-weight: 700;
                padding: 2px 8px;
                margin-right: 4px;
            }
            QToolBar#SolidFreeCADCommandStrip QToolButton[SolidFreeCADPrimaryCommand="true"] {
                background: #eef6fb;
                border: 1px solid #c0dae9;
                border-radius: 3px;
                font-weight: 700;
                min-width: 66px;
            }
            QToolBar#SolidFreeCADCommandStrip QToolButton[SolidFreeCADPrimaryCommand="true"]:hover {
                background: #dceef8;
                border-color: #6ba7ca;
            }
            QTabBar#SolidFreeCADRibbonTabs::tab:selected {
                color: #155f8d;
            }
        )QSS"));
        shell->setProperty("SolidFreeCADWorkspacePolished", true);
    }

    ensureContextBadge(shell);
    updateDocumentTitle(shell);
    stylePrimaryCommands(ribbon);
}

void SolidWorkspacePolish::ensureContextBadge(QWidget* shell)
{
    if (!shell || contextBadge_) {
        return;
    }

    auto* brand = shell->findChild<QLabel*>(QStringLiteral("SolidFreeCADBrand"));
    if (!brand || !brand->parentWidget()) {
        return;
    }

    auto* rowLayout = qobject_cast<QBoxLayout*>(brand->parentWidget()->layout());
    if (!rowLayout) {
        return;
    }

    contextBadge_ = new QLabel(tr("PIEZA"), brand->parentWidget());
    contextBadge_->setObjectName(QStringLiteral("SolidFreeCADContextBadge"));
    contextBadge_->setToolTip(tr("Entorno activo: diseño de piezas"));
    const int brandIndex = rowLayout->indexOf(brand);
    rowLayout->insertWidget(brandIndex >= 0 ? brandIndex + 1 : 1, contextBadge_);
}

void SolidWorkspacePolish::updateDocumentTitle(QWidget* shell)
{
    if (!shell) {
        return;
    }

    if (!documentTitle_) {
        documentTitle_ = shell->findChild<QLabel*>(QStringLiteral("SolidFreeCADDocumentTitle"));
    }
    if (!documentTitle_) {
        return;
    }

    if (auto* document = App::GetApplication().getActiveDocument()) {
        documentTitle_->setText(QString::fromUtf8(document->getName()));
        documentTitle_->setToolTip(tr("Documento activo"));
    }
    else {
        documentTitle_->setText(tr("Sin documento"));
        documentTitle_->setToolTip(QString());
    }
}

void SolidWorkspacePolish::stylePrimaryCommands(QToolBar* ribbon)
{
    const auto strips =
        ribbon->findChildren<QToolBar*>(QStringLiteral("SolidFreeCADCommandStrip"));
    for (QToolBar* strip : strips) {
        if (!strip) {
            continue;
        }
        strip->setMinimumHeight(69);
        strip->setMaximumHeight(69);

        for (QAction* action : strip->actions()) {
            if (!action) {
                continue;
            }
            const QString commandName =
                action->property("SolidFreeCADCommandName").toString();
            const bool primary = isPrimaryCommand(commandName);
            auto* button = qobject_cast<QToolButton*>(strip->widgetForAction(action));
            if (!button) {
                continue;
            }

            button->setProperty("SolidFreeCADPrimaryCommand", primary);
            button->setIconSize(primary ? QSize(38, 38) : QSize(30, 30));
            if (primary) {
                button->setMinimumWidth(68);
                button->setMinimumHeight(66);
                button->setMaximumHeight(66);
                if (hasCustomCommandIcon(commandName)) {
                    action->setIcon(customCommandIcon(commandName, QSize(38, 38)));
                    action->setProperty("SolidFreeCADCustomIcon", true);
                }
            }
            button->style()->unpolish(button);
            button->style()->polish(button);
        }
    }
}

void SolidWorkspacePolish::polishSidePanels()
{
    if (!mainWindow_) {
        return;
    }

    auto* propertyDock =
        mainWindow_->findChild<QDockWidget*>(QStringLiteral("SolidFreeCADPropertyManager"));
    if (propertyDock) {
        propertyDock->setWindowTitle(tr("Propiedades"));
        propertyDock->setAllowedAreas(Qt::LeftDockWidgetArea);
        propertyDock->setFeatures(QDockWidget::DockWidgetMovable);
        propertyDock->setMinimumWidth(310);
    }

    QDockWidget* modelDock = nullptr;
    const auto docks = mainWindow_->findChildren<QDockWidget*>(QString(), Qt::FindDirectChildrenOnly);
    for (QDockWidget* dock : docks) {
        if (!dock || dock == propertyDock
            || mainWindow_->dockWidgetArea(dock) != Qt::LeftDockWidgetArea) {
            continue;
        }
        const QString identity =
            (dock->objectName() + QLatin1Char(' ') + dock->windowTitle()).toLower();
        if (dock->objectName() == QStringLiteral("Model")
            || identity.contains(QStringLiteral("modelo"))
            || identity.contains(QStringLiteral("model"))) {
            modelDock = dock;
            break;
        }
    }

    if (!modelDock) {
        return;
    }

    modelDock->setWindowTitle(tr("Historial del modelo"));
    modelDock->setMinimumWidth(310);
    if (modelDock->widget()) {
        modelDock->widget()->setMinimumWidth(300);
    }

    const auto tabWidgets = modelDock->findChildren<QTabWidget*>();
    for (QTabWidget* tabs : tabWidgets) {
        if (!tabs || tabs->count() < 2) {
            continue;
        }
        tabs->setTabText(0, tr("Modelo"));
        tabs->setTabText(1, tr("Tareas"));
        tabs->setCurrentIndex(0);
        break;
    }
}

}  // namespace SolidFreeCAD
