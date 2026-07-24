#include "SolidTaskOverlayGuard.h"

#include <QDockWidget>
#include <QLabel>
#include <QList>
#include <QTimer>
#include <QWidget>

#include <App/DocumentObject.h>
#include <Base/Type.h>
#include <Gui/Application.h>
#include <Gui/DockWindowManager.h>
#include <Gui/Document.h>
#include <Gui/MainWindow.h>
#include <Gui/OverlayManager.h>
#include <Gui/ViewProviderDocumentObject.h>

namespace
{

bool containsTaskView(QDockWidget* dock)
{
    if (!dock) {
        return false;
    }
    for (QWidget* child : dock->findChildren<QWidget*>()) {
        const QString className = QString::fromLatin1(child->metaObject()->className());
        if (className.contains(QStringLiteral("TaskView"), Qt::CaseInsensitive)) {
            return true;
        }
    }
    return false;
}

bool looksLikeTaskDock(QDockWidget* dock)
{
    if (!dock) {
        return false;
    }
    const QString identity =
        (dock->objectName() + QLatin1Char(' ') + dock->windowTitle()).toLower();
    return containsTaskView(dock)
        || identity.contains(QStringLiteral("tasks"))
        || identity.contains(QStringLiteral("task view"))
        || identity.contains(QStringLiteral("tareas"));
}

QDockWidget* parentDock(QWidget* widget)
{
    QWidget* current = widget;
    while (current) {
        if (auto* dock = qobject_cast<QDockWidget*>(current)) {
            return dock;
        }
        current = current->parentWidget();
    }
    return nullptr;
}

}  // namespace

namespace SolidFreeCAD
{

SolidTaskOverlayGuard::SolidTaskOverlayGuard(QObject* parent)
    : QObject(parent)
{}

SolidTaskOverlayGuard::~SolidTaskOverlayGuard()
{
    uninstall();
}

bool SolidTaskOverlayGuard::install(Gui::MainWindow* mainWindow)
{
    if (installed_ || !mainWindow || !Gui::Application::Instance) {
        return installed_;
    }

    mainWindow_ = mainWindow;
    installed_ = true;
    startupBadgeLock_ = true;
    refresh();
    refreshTimer_ = new QTimer(this);
    refreshTimer_->setInterval(45);
    connect(refreshTimer_, &QTimer::timeout, this, [this]() { refresh(); });
    refreshTimer_->start();
    QTimer::singleShot(5000, this, [this]() {
        startupBadgeLock_ = false;
        refresh();
    });
    for (const int delay : {0, 60, 180, 420, 900, 1800, 3200}) {
        QTimer::singleShot(delay, this, [this]() { refresh(); });
    }
    return true;
}

void SolidTaskOverlayGuard::uninstall()
{
    if (!installed_) {
        return;
    }
    if (refreshTimer_) {
        refreshTimer_->stop();
        refreshTimer_->deleteLater();
    }
    refreshTimer_.clear();
    startupBadgeLock_ = false;
    mainWindow_ = nullptr;
    installed_ = false;
}

bool SolidTaskOverlayGuard::isInstalled() const
{
    return installed_;
}

bool SolidTaskOverlayGuard::activeSketch() const
{
    if (!Gui::Application::Instance) {
        return false;
    }
    Gui::Document* document = Gui::Application::Instance->editDocument();
    auto* provider = document
        ? dynamic_cast<Gui::ViewProviderDocumentObject*>(document->getInEdit())
        : nullptr;
    App::DocumentObject* object = provider ? provider->getObject() : nullptr;
    return object && object->getTypeId().isDerivedFrom(
        Base::Type::fromName("Sketcher::SketchObject")
    );
}

void SolidTaskOverlayGuard::refresh()
{
    if (!installed_ || !mainWindow_) {
        return;
    }
    const bool editing = activeSketch();
    synchronizeContextBadges(editing);
    normalizeTaskDocks(editing);
}

void SolidTaskOverlayGuard::synchronizeContextBadges(bool editing)
{
    if (!mainWindow_) {
        return;
    }
    const auto badges = mainWindow_->findChildren<QLabel*>(
        QStringLiteral("SolidFreeCADContextBadge")
    );
    if (badges.isEmpty()) {
        return;
    }

    QString text;
    QString tooltip;
    for (QLabel* badge : badges) {
        if (badge && badge->isVisible() && !badge->text().isEmpty()) {
            text = badge->text();
            tooltip = badge->toolTip();
            break;
        }
    }
    if (editing) {
        text = tr("EDITANDO CROQUIS");
        tooltip = tr("Croquis activo: vista normal y controles de confirmación");
    }
    else if (startupBadgeLock_) {
        text = tr("PIEZA");
        tooltip = tr("Entorno de modelado de pieza activo");
    }
    else if (text.isEmpty() || text == tr("EDITANDO CROQUIS")) {
        text = tr("PIEZA");
        tooltip = tr("Entorno de modelado de pieza activo");
    }

    for (QLabel* badge : badges) {
        if (!badge) {
            continue;
        }
        badge->setText(text);
        badge->setToolTip(tooltip);
        badge->setProperty("SolidFreeCADSketchEditing", editing);
    }
}

void SolidTaskOverlayGuard::normalizeTaskDocks(bool editing)
{
    if (!mainWindow_) {
        return;
    }

    QList<QDockWidget*> candidates;
    QDockWidget* activeTaskDock = nullptr;
    for (QDockWidget* dock : mainWindow_->findChildren<QDockWidget*>()) {
        if (!looksLikeTaskDock(dock)) {
            continue;
        }
        candidates.append(dock);
        if (!activeTaskDock && containsTaskView(dock)) {
            activeTaskDock = dock;
        }
    }

    if (!activeTaskDock) {
        if (auto* manager = Gui::DockWindowManager::instance()) {
            QWidget* taskView = manager->getDockWindow("Tasks");
            activeTaskDock = parentDock(taskView);
            if (activeTaskDock && !candidates.contains(activeTaskDock)) {
                candidates.append(activeTaskDock);
            }
        }
    }

    Gui::OverlayManager* overlay = Gui::OverlayManager::instance();
    for (QDockWidget* dock : candidates) {
        if (!dock) {
            continue;
        }
        if (overlay) {
            overlay->unsetupDockWidget(dock);
        }
        mainWindow_->removeDockWidget(dock);
        dock->hide();
        dock->setProperty("SolidFreeCADTaskOverlayDisabled", true);
        dock->setProperty("SolidFreeCADTaskDockActive", false);
    }

    if (!editing || !activeTaskDock) {
        return;
    }

    activeTaskDock->setAllowedAreas(Qt::LeftDockWidgetArea | Qt::RightDockWidgetArea);
    activeTaskDock->setFeatures(
        QDockWidget::DockWidgetMovable | QDockWidget::DockWidgetFloatable
    );
    activeTaskDock->setMinimumWidth(290);
    activeTaskDock->setMaximumWidth(440);
    activeTaskDock->setFloating(false);
    activeTaskDock->setProperty("SolidFreeCADTaskDockActive", true);
    mainWindow_->addDockWidget(Qt::LeftDockWidgetArea, activeTaskDock);
    activeTaskDock->show();
    activeTaskDock->raise();

    QList<QDockWidget*> docks;
    QList<int> sizes;
    docks.append(activeTaskDock);
    sizes.append(340);
    mainWindow_->resizeDocks(docks, sizes, Qt::Horizontal);
}

}  // namespace SolidFreeCAD
