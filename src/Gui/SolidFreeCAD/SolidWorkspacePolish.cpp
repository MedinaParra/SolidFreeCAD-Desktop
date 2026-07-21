#include "SolidWorkspacePolish.h"

#include "SolidIconFactory.h"

#include <QAction>
#include <QBoxLayout>
#include <QColor>
#include <QDockWidget>
#include <QIcon>
#include <QLabel>
#include <QPainter>
#include <QPen>
#include <QPixmap>
#include <QPolygonF>
#include <QSize>
#include <QStackedWidget>
#include <QStyle>
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

const QColor ink(QStringLiteral("#26343e"));
const QColor blue(QStringLiteral("#2f8fc7"));
const QColor blueDark(QStringLiteral("#1f648e"));
const QColor orange(QStringLiteral("#f28b2c"));
const QColor green(QStringLiteral("#35a66f"));
const QColor yellow(QStringLiteral("#f1c84b"));

QPen outline(const QColor& color = ink, qreal width = 1.5)
{
    return QPen(color, width, Qt::SolidLine, Qt::RoundCap, Qt::RoundJoin);
}

bool isPrimaryCommand(const QString& commandName)
{
    return commandName == QStringLiteral("PartDesign_Pad")
        || commandName == QStringLiteral("PartDesign_Pocket")
        || commandName == QStringLiteral("PartDesign_Hole")
        || commandName == QStringLiteral("PartDesign_Revolution")
        || commandName == QStringLiteral("Sketcher_CompDimensionTools")
        || commandName == QStringLiteral("Sketcher_CompCreateRectangles");
}

QIcon quickAccessIcon(const QString& commandName)
{
    const QStringList supported = {
        QStringLiteral("Std_New"),
        QStringLiteral("Std_Open"),
        QStringLiteral("Std_Save"),
        QStringLiteral("Std_Undo"),
        QStringLiteral("Std_Redo"),
        QStringLiteral("Std_DlgPreferences"),
    };
    if (!supported.contains(commandName)) {
        return {};
    }

    QPixmap pixmap(28, 28);
    pixmap.fill(Qt::transparent);
    QPainter painter(&pixmap);
    painter.setRenderHint(QPainter::Antialiasing, true);

    if (commandName == QStringLiteral("Std_New")) {
        painter.setPen(outline());
        painter.setBrush(Qt::white);
        painter.drawRoundedRect(QRectF(5, 3, 16, 21), 1.5, 1.5);
        painter.setPen(outline(blueDark, 1.0));
        painter.drawLine(QPointF(8, 9), QPointF(17, 9));
        painter.drawLine(QPointF(8, 13), QPointF(17, 13));
        painter.setPen(outline(green, 2.0));
        painter.drawLine(QPointF(19, 21), QPointF(26, 21));
        painter.drawLine(QPointF(22.5, 17.5), QPointF(22.5, 24.5));
    }
    else if (commandName == QStringLiteral("Std_Open")) {
        painter.setPen(outline());
        painter.setBrush(yellow);
        painter.drawPolygon(QPolygonF()
                            << QPointF(3, 9) << QPointF(11, 9)
                            << QPointF(14, 13) << QPointF(25, 13)
                            << QPointF(23, 24) << QPointF(4, 24));
        painter.setPen(outline(blueDark, 1.8));
        painter.drawLine(QPointF(16, 6), QPointF(23, 11));
        painter.drawLine(QPointF(23, 11), QPointF(19, 11));
        painter.drawLine(QPointF(23, 11), QPointF(22, 7));
    }
    else if (commandName == QStringLiteral("Std_Save")) {
        painter.setPen(outline());
        painter.setBrush(blue);
        painter.drawRoundedRect(QRectF(4, 4, 20, 20), 2, 2);
        painter.setBrush(Qt::white);
        painter.drawRect(QRectF(8, 6, 12, 6));
        painter.drawRect(QRectF(8, 16, 13, 6));
        painter.setBrush(orange);
        painter.drawRect(QRectF(17, 7, 2.5, 4));
    }
    else if (commandName == QStringLiteral("Std_Undo")
             || commandName == QStringLiteral("Std_Redo")) {
        painter.save();
        if (commandName == QStringLiteral("Std_Redo")) {
            painter.translate(28, 0);
            painter.scale(-1, 1);
        }
        painter.setPen(outline(blueDark, 2.2));
        painter.setBrush(Qt::NoBrush);
        painter.drawArc(QRectF(6, 6, 18, 16), 20 * 16, 235 * 16);
        painter.setPen(Qt::NoPen);
        painter.setBrush(blueDark);
        painter.drawPolygon(QPolygonF()
                            << QPointF(5, 8) << QPointF(11, 5) << QPointF(10, 12));
        painter.restore();
    }
    else if (commandName == QStringLiteral("Std_DlgPreferences")) {
        painter.setPen(outline(blueDark, 1.8));
        painter.drawLine(QPointF(5, 8), QPointF(23, 8));
        painter.drawLine(QPointF(5, 14), QPointF(23, 14));
        painter.drawLine(QPointF(5, 20), QPointF(23, 20));
        painter.setPen(outline(orange, 1.5));
        painter.setBrush(Qt::white);
        painter.drawEllipse(QPointF(10, 8), 2.5, 2.5);
        painter.drawEllipse(QPointF(18, 14), 2.5, 2.5);
        painter.drawEllipse(QPointF(13, 20), 2.5, 2.5);
    }

    painter.end();
    return QIcon(pixmap);
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

    const auto quickToolbars =
        ribbon->findChildren<QToolBar*>(QStringLiteral("SolidFreeCADQuickAccess"));
    for (QToolBar* toolbar : quickToolbars) {
        for (QAction* action : toolbar->actions()) {
            if (!action) {
                continue;
            }
            const QString commandName =
                action->property("SolidFreeCADCommandName").toString();
            const QIcon icon = quickAccessIcon(commandName);
            if (icon.isNull()) {
                continue;
            }
            action->setIcon(icon);
            action->setProperty("SolidFreeCADWorkspaceIcon", true);
        }
    }
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
        if (!dock || dock == propertyDock) {
            continue;
        }

        const QString identity =
            (dock->objectName() + QLatin1Char(' ') + dock->windowTitle()).toLower();
        const bool detachedTaskPanel =
            (dock->isFloating() || mainWindow_->dockWidgetArea(dock) == Qt::NoDockWidgetArea)
            && (identity.trimmed() == QStringLiteral("tasks")
                || identity.trimmed() == QStringLiteral("tareas")
                || identity.contains(QStringLiteral(" task")));
        if (detachedTaskPanel) {
            dock->hide();
            continue;
        }

        if (mainWindow_->dockWidgetArea(dock) != Qt::LeftDockWidgetArea) {
            continue;
        }
        if (dock->objectName() == QStringLiteral("Model")
            || identity.contains(QStringLiteral("modelo"))
            || identity.contains(QStringLiteral("model"))) {
            modelDock = dock;
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
