#include "SolidActiveSketch.h"

#include <algorithm>

#include <QAction>
#include <QDockWidget>
#include <QFrame>
#include <QHBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QSize>
#include <QStyle>
#include <QTabBar>
#include <QTabWidget>
#include <QTimer>
#include <QToolBar>
#include <QVBoxLayout>
#include <QWidget>

#include <App/Application.h>
#include <App/DocumentObject.h>
#include <Base/Type.h>
#include <Gui/Application.h>
#include <Gui/Command.h>
#include <Gui/Control.h>
#include <Gui/Document.h>
#include <Gui/MainWindow.h>
#include <Gui/Selection/Selection.h>
#include <Gui/ViewProvider.h>

namespace SolidFreeCAD
{

SolidActiveSketch::SolidActiveSketch(QObject* parent)
    : QObject(parent)
{}

SolidActiveSketch::~SolidActiveSketch()
{
    uninstall();
}

bool SolidActiveSketch::install(Gui::MainWindow* mainWindow)
{
    if (installed_ || !mainWindow || !Gui::Application::Instance) {
        return installed_;
    }

    mainWindow_ = mainWindow;
    installed_ = true;
    applyPreferences();

    refreshTimer_ = new QTimer(this);
    refreshTimer_->setInterval(160);
    connect(refreshTimer_, &QTimer::timeout, this, [this]() { refresh(); });
    refreshTimer_->start();

    for (const int delay : {0, 250, 700, 1400, 2400}) {
        QTimer::singleShot(delay, this, [this]() { refresh(); });
    }
    return true;
}

void SolidActiveSketch::uninstall()
{
    if (!installed_) {
        return;
    }

    if (refreshTimer_) {
        refreshTimer_->stop();
        refreshTimer_->deleteLater();
    }
    if (modelTaskTabs_ && modelTaskTabs_->tabBar()) {
        modelTaskTabs_->tabBar()->show();
        modelTaskTabs_->setCurrentIndex(0);
    }
    if (confirmationCorner_) {
        confirmationCorner_->deleteLater();
    }
    if (guidanceFrame_) {
        guidanceFrame_->deleteLater();
    }

    restorePreferences();
    refreshTimer_.clear();
    confirmationCorner_.clear();
    guidanceFrame_.clear();
    guidanceTitle_.clear();
    guidanceText_.clear();
    modelTaskTabs_.clear();
    mainWindow_ = nullptr;
    previousEditing_ = false;
    installed_ = false;
}

bool SolidActiveSketch::isInstalled() const
{
    return installed_;
}

void SolidActiveSketch::applyPreferences()
{
    if (preferencesApplied_) {
        return;
    }

    auto sketch = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/Mod/Sketcher"
    );
    auto general = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/Mod/Sketcher/General"
    );

    previousLeaveSketchWithEscape_ = sketch->GetBool("LeaveSketchWithEscape", true);
    previousForceOrtho_ = general->GetBool("ForceOrtho", false);
    previousRestoreCamera_ = general->GetBool("RestoreCamera", true);

    // Escape cancels the active drawing tool instead of unexpectedly closing the sketch.
    sketch->SetBool("LeaveSketchWithEscape", false);
    // ViewProviderSketch already aligns the camera with the real sketch placement.
    general->SetBool("ForceOrtho", true);
    general->SetBool("RestoreCamera", true);
    preferencesApplied_ = true;
}

void SolidActiveSketch::restorePreferences()
{
    if (!preferencesApplied_) {
        return;
    }

    auto sketch = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/Mod/Sketcher"
    );
    auto general = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/Mod/Sketcher/General"
    );
    sketch->SetBool("LeaveSketchWithEscape", previousLeaveSketchWithEscape_);
    general->SetBool("ForceOrtho", previousForceOrtho_);
    general->SetBool("RestoreCamera", previousRestoreCamera_);
    preferencesApplied_ = false;
}

bool SolidActiveSketch::activeSketch(App::DocumentObject** object) const
{
    if (object) {
        *object = nullptr;
    }
    if (!Gui::Application::Instance) {
        return false;
    }

    Gui::Document* document = Gui::Application::Instance->editDocument();
    if (!document) {
        document = Gui::Application::Instance->activeDocument();
    }
    Gui::ViewProvider* viewProvider = document ? document->getInEdit() : nullptr;
    App::DocumentObject* candidate = viewProvider ? viewProvider->getObject() : nullptr;
    if (!candidate) {
        return false;
    }

    const bool sketch = candidate->getTypeId().isDerivedFrom(
        Base::Type::fromName("Sketcher::SketchObject")
    );
    if (sketch && object) {
        *object = candidate;
    }
    return sketch;
}

void SolidActiveSketch::refresh()
{
    if (!installed_ || !mainWindow_) {
        return;
    }

    ensureConfirmationCorner();
    ensureGuidancePanel();
    configureNewSketchCommand();

    App::DocumentObject* sketch = nullptr;
    const bool editing = activeSketch(&sketch);
    mainWindow_->setProperty("SolidFreeCADSketchEditing", editing);

    if (editing && !previousEditing_) {
        selectSketchRibbon();
    }
    updateTaskPanel(editing);
    updateConfirmationCorner(editing, sketch);
    updateGuidance(editing, sketch);
    repositionConfirmationCorner();
    previousEditing_ = editing;
}

void SolidActiveSketch::ensureConfirmationCorner()
{
    if (confirmationCorner_ || !mainWindow_) {
        return;
    }

    confirmationCorner_ = new QFrame(mainWindow_);
    confirmationCorner_->setObjectName(QStringLiteral("SolidFreeCADConfirmationCorner"));
    confirmationCorner_->setAttribute(Qt::WA_StyledBackground, true);
    confirmationCorner_->setStyleSheet(QStringLiteral(R"QSS(
        QFrame#SolidFreeCADConfirmationCorner {
            background: rgba(250, 252, 253, 246);
            border: 1px solid #9db8c9;
            border-radius: 7px;
        }
        QLabel#SolidFreeCADSketchEditingTitle {
            color: #155f8d;
            font-size: 10px;
            font-weight: 800;
            padding: 0 5px;
        }
        QPushButton {
            min-height: 25px;
            padding: 2px 9px;
            border: 1px solid #aebbc3;
            border-radius: 3px;
            background: #ffffff;
        }
        QPushButton:hover { background: #e8f3f9; border-color: #6c9fbd; }
        QPushButton#SolidFreeCADSketchAccept {
            background: #e8f5ee;
            border-color: #8fc7a8;
            color: #246b43;
            font-weight: 700;
        }
        QPushButton#SolidFreeCADSketchCancel {
            background: #fff0ee;
            border-color: #d7aaa4;
            color: #9b352d;
        }
    )QSS"));

    auto* layout = new QHBoxLayout(confirmationCorner_);
    layout->setContentsMargins(7, 6, 7, 6);
    layout->setSpacing(5);

    auto* title = new QLabel(tr("EDITANDO CROQUIS"), confirmationCorner_);
    title->setObjectName(QStringLiteral("SolidFreeCADSketchEditingTitle"));
    layout->addWidget(title);

    auto* accept = new QPushButton(tr("Aceptar"), confirmationCorner_);
    accept->setObjectName(QStringLiteral("SolidFreeCADSketchAccept"));
    accept->setToolTip(tr("Aceptar los cambios del diálogo activo"));
    connect(accept, &QPushButton::clicked, confirmationCorner_, []() {
        Gui::Control().accept();
    });
    layout->addWidget(accept);

    auto* cancel = new QPushButton(tr("Cancelar"), confirmationCorner_);
    cancel->setObjectName(QStringLiteral("SolidFreeCADSketchCancel"));
    cancel->setToolTip(tr("Cancelar los cambios del diálogo activo"));
    connect(cancel, &QPushButton::clicked, confirmationCorner_, []() {
        Gui::Control().reject();
    });
    layout->addWidget(cancel);

    auto* exit = new QPushButton(tr("Salir del croquis"), confirmationCorner_);
    exit->setObjectName(QStringLiteral("SolidFreeCADSketchExit"));
    exit->setToolTip(tr("Finalizar la edición del croquis"));
    connect(exit, &QPushButton::clicked, confirmationCorner_, []() {
        if (!Gui::Application::Instance) {
            return;
        }
        auto& manager = Gui::Application::Instance->commandManager();
        Gui::Command* command = manager.getCommandByName("Sketcher_LeaveSketch");
        if (command && command->isActive()) {
            manager.runCommandByName("Sketcher_LeaveSketch");
        }
        else {
            Gui::Control().accept();
        }
    });
    layout->addWidget(exit);

    confirmationCorner_->adjustSize();
    confirmationCorner_->hide();
}

void SolidActiveSketch::ensureGuidancePanel()
{
    if (guidanceFrame_ || !mainWindow_) {
        return;
    }

    QWidget* propertyPanel = mainWindow_->findChild<QWidget*>(
        QStringLiteral("SolidFreeCADPropertyManagerWidget")
    );
    auto* layout = propertyPanel ? qobject_cast<QVBoxLayout*>(propertyPanel->layout()) : nullptr;
    if (!layout) {
        return;
    }

    guidanceFrame_ = new QFrame(propertyPanel);
    guidanceFrame_->setObjectName(QStringLiteral("SolidFreeCADSketchGuidance"));
    guidanceFrame_->setProperty("ready", false);
    guidanceFrame_->setStyleSheet(QStringLiteral(R"QSS(
        QFrame#SolidFreeCADSketchGuidance {
            background: #ffffff;
            border: 1px solid #c6d2d9;
            border-left: 4px solid #e29a3b;
            border-radius: 3px;
        }
        QFrame#SolidFreeCADSketchGuidance[ready="true"] {
            border-left-color: #3b9b69;
            background: #f4fbf7;
        }
        QFrame#SolidFreeCADSketchGuidance[editing="true"] {
            border-left-color: #2f8fc7;
            background: #f1f8fc;
        }
        QLabel#SolidFreeCADSketchGuidanceTitle {
            color: #20313c;
            font-weight: 700;
        }
        QLabel#SolidFreeCADSketchGuidanceText { color: #53626b; }
    )QSS"));

    auto* guidanceLayout = new QVBoxLayout(guidanceFrame_);
    guidanceLayout->setContentsMargins(8, 6, 8, 7);
    guidanceLayout->setSpacing(2);
    guidanceTitle_ = new QLabel(tr("Preparar nuevo croquis"), guidanceFrame_);
    guidanceTitle_->setObjectName(QStringLiteral("SolidFreeCADSketchGuidanceTitle"));
    guidanceText_ = new QLabel(
        tr("Seleccione un plano de origen o una cara plana y pulse Nuevo croquis."),
        guidanceFrame_
    );
    guidanceText_->setObjectName(QStringLiteral("SolidFreeCADSketchGuidanceText"));
    guidanceText_->setWordWrap(true);
    guidanceLayout->addWidget(guidanceTitle_);
    guidanceLayout->addWidget(guidanceText_);

    layout->insertWidget(std::min(3, layout->count()), guidanceFrame_);
}

void SolidActiveSketch::configureNewSketchCommand()
{
    if (!mainWindow_) {
        return;
    }
    auto* ribbon = mainWindow_->findChild<QToolBar*>(QStringLiteral("SolidFreeCADRibbon"));
    if (!ribbon) {
        return;
    }

    const auto toolbars = ribbon->findChildren<QToolBar*>();
    for (QToolBar* toolbar : toolbars) {
        for (QAction* action : toolbar->actions()) {
            if (!action || action->property("SolidFreeCADCommandName").toString()
                    != QStringLiteral("PartDesign_NewSketch")) {
                continue;
            }
            action->setToolTip(tr(
                "Seleccione primero un plano de origen o una cara plana. Sin selección, "
                "FreeCAD abrirá el selector de soporte."
            ));
            if (action->property("SolidFreeCADSketchGuidanceConnected").toBool()) {
                continue;
            }
            connect(action, &QAction::triggered, this, [this]() {
                QTimer::singleShot(0, this, [this]() { refresh(); });
                QTimer::singleShot(250, this, [this]() { refresh(); });
                QTimer::singleShot(700, this, [this]() { refresh(); });
            });
            action->setProperty("SolidFreeCADSketchGuidanceConnected", true);
        }
    }
}

void SolidActiveSketch::updateConfirmationCorner(bool editing, App::DocumentObject* sketch)
{
    if (!confirmationCorner_) {
        return;
    }
    confirmationCorner_->setProperty(
        "SolidFreeCADSketchName",
        sketch ? QString::fromUtf8(sketch->getNameInDocument()) : QString()
    );
    confirmationCorner_->setVisible(editing);
    if (editing) {
        confirmationCorner_->adjustSize();
        confirmationCorner_->raise();
    }
}

void SolidActiveSketch::updateGuidance(bool editing, App::DocumentObject* sketch)
{
    if (!guidanceFrame_ || !guidanceTitle_ || !guidanceText_) {
        return;
    }

    const auto selection = Gui::Selection().getCompleteSelection(Gui::ResolveMode::NoResolve);
    const bool ready = !editing && !selection.empty();
    guidanceFrame_->setProperty("ready", ready);
    guidanceFrame_->setProperty("editing", editing);

    if (editing) {
        guidanceTitle_->setText(tr("Croquis activo: %1").arg(
            sketch ? QString::fromUtf8(sketch->getNameInDocument()) : tr("Croquis")
        ));
        guidanceText_->setText(tr(
            "La vista está alineada con el plano del croquis. Esc cancela la herramienta "
            "de dibujo actual; use el panel superior para aceptar, cancelar o salir."
        ));
    }
    else if (ready) {
        guidanceTitle_->setText(tr("Soporte seleccionado"));
        guidanceText_->setText(tr(
            "Pulse Nuevo croquis. FreeCAD comprobará que la selección sea un plano de origen "
            "o una cara plana válida."
        ));
    }
    else {
        guidanceTitle_->setText(tr("Preparar nuevo croquis"));
        guidanceText_->setText(tr(
            "Seleccione Frontal, Superior, Derecho, un plano de referencia o una cara plana; "
            "después pulse Nuevo croquis."
        ));
    }

    guidanceFrame_->style()->unpolish(guidanceFrame_);
    guidanceFrame_->style()->polish(guidanceFrame_);
}

void SolidActiveSketch::updateTaskPanel(bool editing)
{
    if (!mainWindow_) {
        return;
    }

    if (!modelTaskTabs_) {
        const auto docks = mainWindow_->findChildren<QDockWidget*>();
        for (QDockWidget* dock : docks) {
            if (!dock || mainWindow_->dockWidgetArea(dock) != Qt::LeftDockWidgetArea) {
                continue;
            }
            const QString identity =
                (dock->objectName() + QLatin1Char(' ') + dock->windowTitle()).toLower();
            if (!identity.contains(QStringLiteral("model"))
                && !identity.contains(QStringLiteral("modelo"))
                && !identity.contains(QStringLiteral("historial"))) {
                continue;
            }
            const auto tabs = dock->findChildren<QTabWidget*>();
            for (QTabWidget* candidate : tabs) {
                if (candidate && candidate->count() >= 2) {
                    modelTaskTabs_ = candidate;
                    break;
                }
            }
            if (modelTaskTabs_) {
                break;
            }
        }
    }

    if (!modelTaskTabs_) {
        return;
    }
    modelTaskTabs_->setTabText(0, tr("Modelo"));
    modelTaskTabs_->setTabText(1, tr("Tareas"));
    modelTaskTabs_->setCurrentIndex(editing ? 1 : 0);
    modelTaskTabs_->setProperty("SolidFreeCADTaskStripReplaced", true);
    if (modelTaskTabs_->tabBar()) {
        modelTaskTabs_->tabBar()->hide();
    }
}

void SolidActiveSketch::selectSketchRibbon()
{
    if (!mainWindow_) {
        return;
    }
    auto* tabs = mainWindow_->findChild<QTabBar*>(QStringLiteral("SolidFreeCADRibbonTabs"));
    if (!tabs) {
        return;
    }
    for (int index = 0; index < tabs->count(); ++index) {
        if (tabs->tabText(index) == tr("Croquis")) {
            tabs->setCurrentIndex(index);
            return;
        }
    }
}

void SolidActiveSketch::repositionConfirmationCorner()
{
    if (!confirmationCorner_ || !confirmationCorner_->isVisible() || !mainWindow_) {
        return;
    }

    auto* ribbon = mainWindow_->findChild<QToolBar*>(QStringLiteral("SolidFreeCADRibbon"));
    const int top = ribbon ? ribbon->geometry().bottom() + 12 : 175;
    confirmationCorner_->adjustSize();
    const int left = std::max(12, mainWindow_->width() - confirmationCorner_->width() - 24);
    confirmationCorner_->move(left, top);
    confirmationCorner_->raise();
}

}  // namespace SolidFreeCAD
