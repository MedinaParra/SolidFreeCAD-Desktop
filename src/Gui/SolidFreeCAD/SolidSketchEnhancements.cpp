#include "SolidSketchEnhancements.h"

#include <QAction>
#include <QApplication>
#include <QEvent>
#include <QMenu>
#include <QSet>
#include <QStyle>
#include <QTimer>
#include <QToolBar>
#include <QToolButton>

#include <App/Application.h>
#include <Gui/Application.h>
#include <Gui/Command.h>
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

SolidSketchEnhancements::SolidSketchEnhancements(QObject* parent)
    : QObject(parent)
{}

SolidSketchEnhancements::~SolidSketchEnhancements()
{
    uninstall();
}

bool SolidSketchEnhancements::install(Gui::MainWindow* mainWindow)
{
    if (installed_ || !mainWindow || !Gui::Application::Instance) {
        return installed_;
    }

    mainWindow_ = mainWindow;
    installed_ = true;
    applySketchPalette();

    if (qApp) {
        qApp->installEventFilter(this);
    }

    auto& commandManager = Gui::Application::Instance->commandManager();
    commandChangedConnection_ = commandManager.signalChanged.connect([this]() {
        QTimer::singleShot(0, this, [this]() { refreshRibbon(); });
    });

    refreshRibbon();
    QTimer::singleShot(0, this, [this]() { refreshRibbon(); });
    QTimer::singleShot(250, this, [this]() { refreshRibbon(); });
    QTimer::singleShot(750, this, [this]() { refreshRibbon(); });
    return true;
}

void SolidSketchEnhancements::uninstall()
{
    if (!installed_) {
        return;
    }

    commandChangedConnection_.disconnect();
    if (qApp) {
        qApp->removeEventFilter(this);
    }

    restoreSketchPalette();
    mainWindow_.clear();
    installed_ = false;
}

bool SolidSketchEnhancements::eventFilter(QObject* watched, QEvent* event)
{
    if (!installed_ || !event) {
        return QObject::eventFilter(watched, event);
    }

    const auto type = event->type();
    if (type == QEvent::Show || type == QEvent::Polish || type == QEvent::ChildAdded) {
        if (watched == mainWindow_ || qobject_cast<QToolBar*>(watched)
            || qobject_cast<QToolButton*>(watched)) {
            QTimer::singleShot(0, this, [this]() { refreshRibbon(); });
        }
    }

    return QObject::eventFilter(watched, event);
}

void SolidSketchEnhancements::applySketchPalette()
{
    if (paletteApplied_) {
        return;
    }

    auto viewParameters = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/View"
    );
    auto sketchParameters = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/Mod/Sketcher/General"
    );

    previousFullyConstrainedColor_ =
        viewParameters->GetUnsigned("FullyConstrainedColor", 0x00FF00FF);
    previousFullyConstraintElementColor_ =
        viewParameters->GetUnsigned("FullyConstraintElementColor", 0x80D0A0FF);
    previousFullyConstraintConstructionElementColor_ =
        viewParameters->GetUnsigned("FullyConstraintConstructionElementColor", 0x8FA9FDFF);
    previousFullyConstraintInternalAlignmentColor_ =
        viewParameters->GetUnsigned("FullyConstraintInternalAlignmentColor", 0xDEDEC8FF);
    previousSketchFaceColor_ = sketchParameters->GetUnsigned("SketchFaceColor", 0x54ABFF40);

    // Fully constrained sketch geometry uses a neutral black, matching a drafting convention.
    viewParameters->SetUnsigned("FullyConstrainedColor", rgba(0, 0, 0));
    viewParameters->SetUnsigned("FullyConstraintElementColor", rgba(0, 0, 0));
    viewParameters->SetUnsigned(
        "FullyConstraintConstructionElementColor", rgba(72, 72, 72)
    );
    viewParameters->SetUnsigned(
        "FullyConstraintInternalAlignmentColor", rgba(96, 96, 96)
    );

    // Closed sketch wires are rendered by FreeCAD's native SoSketchFaces node.
    // The alpha byte keeps this fill visible only as a translucent sketch aid.
    sketchParameters->SetUnsigned("SketchFaceColor", rgba(151, 158, 188, 92));

    paletteApplied_ = true;
}

void SolidSketchEnhancements::restoreSketchPalette()
{
    if (!paletteApplied_) {
        return;
    }

    auto viewParameters = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/View"
    );
    auto sketchParameters = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/Mod/Sketcher/General"
    );

    viewParameters->SetUnsigned("FullyConstrainedColor", previousFullyConstrainedColor_);
    viewParameters->SetUnsigned(
        "FullyConstraintElementColor", previousFullyConstraintElementColor_
    );
    viewParameters->SetUnsigned(
        "FullyConstraintConstructionElementColor",
        previousFullyConstraintConstructionElementColor_
    );
    viewParameters->SetUnsigned(
        "FullyConstraintInternalAlignmentColor",
        previousFullyConstraintInternalAlignmentColor_
    );
    sketchParameters->SetUnsigned("SketchFaceColor", previousSketchFaceColor_);

    paletteApplied_ = false;
}

void SolidSketchEnhancements::refreshRibbon()
{
    if (!mainWindow_) {
        return;
    }

    auto* ribbon = mainWindow_->findChild<QToolBar*>(QStringLiteral("SolidFreeCADRibbon"));
    if (!ribbon) {
        return;
    }

    configureCompactMenuArrows(ribbon);

    const auto commandStrips =
        ribbon->findChildren<QToolBar*>(QStringLiteral("SolidFreeCADCommandStrip"));
    for (QToolBar* toolbar : commandStrips) {
        configureSmartDimension(toolbar);
    }
}

void SolidSketchEnhancements::configureSmartDimension(QToolBar* toolbar)
{
    if (!toolbar || !Gui::Application::Instance) {
        return;
    }

    for (QAction* action : toolbar->actions()) {
        if (!action
            || action->property("SolidFreeCADCommandName").toString()
                != QStringLiteral("Sketcher_Dimension")) {
            continue;
        }

        action->setText(tr("Cota inteligente"));
        auto* button = qobject_cast<QToolButton*>(toolbar->widgetForAction(action));
        if (!button || button->property("SolidFreeCADSmartDimensionConfigured").toBool()) {
            continue;
        }

        auto* menu = new QMenu(button);
        menu->setObjectName(QStringLiteral("SolidFreeCADSmartDimensionMenu"));
        addMenuCommand(menu, "Sketcher_Dimension", "Cota inteligente");
        menu->addSeparator();
        addMenuCommand(menu, "Sketcher_ConstrainDistanceX", "Cota horizontal");
        addMenuCommand(menu, "Sketcher_ConstrainDistanceY", "Cota vertical");
        addMenuCommand(menu, "Sketcher_ConstrainDistance", "Longitud o distancia");
        addMenuCommand(menu, "Sketcher_ConstrainRadius", "Radio");
        addMenuCommand(menu, "Sketcher_ConstrainDiameter", "Diámetro");
        addMenuCommand(menu, "Sketcher_ConstrainAngle", "Ángulo");
        addMenuCommand(menu, "Sketcher_ConstrainLock", "Fijar posición");

        button->setMenu(menu);
        button->setPopupMode(QToolButton::MenuButtonPopup);
        button->setProperty("SolidFreeCADSmartDimensionConfigured", true);
        button->setProperty("SolidFreeCADHasMenu", true);
        button->setToolTip(tr(
            "Acota según la selección. Use la flecha para elegir una cota específica."
        ));
        button->style()->unpolish(button);
        button->style()->polish(button);
    }
}

void SolidSketchEnhancements::configureCompactMenuArrows(QToolBar* ribbon)
{
    if (!ribbon || ribbon->property("SolidFreeCADCompactMenuArrows").toBool()) {
        return;
    }

    ribbon->setStyleSheet(ribbon->styleSheet() + QStringLiteral(R"QSS(
        QToolBar#SolidFreeCADRibbon QToolButton::menu-indicator {
            image: none;
            subcontrol-origin: padding;
            subcontrol-position: bottom right;
            width: 0px;
            height: 0px;
            border-left: 3px solid transparent;
            border-right: 3px solid transparent;
            border-top: 4px solid #4b4b4b;
            margin-right: 3px;
            margin-bottom: 2px;
        }
        QToolBar#SolidFreeCADRibbon QToolButton:disabled::menu-indicator {
            border-top-color: #a8a8a8;
        }
    )QSS"));
    ribbon->setProperty("SolidFreeCADCompactMenuArrows", true);
}

bool SolidSketchEnhancements::addMenuCommand(QMenu* menu,
                                              const char* commandName,
                                              const char* fallbackText)
{
    if (!menu || !commandName || !*commandName || !Gui::Application::Instance) {
        return false;
    }

    auto& commandManager = Gui::Application::Instance->commandManager();
    Gui::Command* command = commandManager.getCommandByName(commandName);
    if (!command) {
        QAction* unavailable = menu->addAction(QString::fromUtf8(fallbackText));
        unavailable->setEnabled(false);
        return false;
    }

    QSet<QAction*> previous;
    for (QAction* action : menu->actions()) {
        previous.insert(action);
    }

    command->addTo(menu);
    for (QAction* action : menu->actions()) {
        if (!previous.contains(action)) {
            action->setText(QString::fromUtf8(fallbackText));
            action->setProperty(
                "SolidFreeCADCommandName", QString::fromLatin1(commandName)
            );
        }
    }
    return true;
}

}  // namespace SolidFreeCAD
