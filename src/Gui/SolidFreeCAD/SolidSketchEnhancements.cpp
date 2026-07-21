#include "SolidSketchEnhancements.h"

#include "SolidIconFactory.h"

#include <QAction>
#include <QEvent>
#include <QLabel>
#include <QMenu>
#include <QPointer>
#include <QSize>
#include <QStyle>
#include <QTimer>
#include <QToolBar>
#include <QToolButton>

#include <string>

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

class CompactMenuArrow final : public QLabel
{
public:
    explicit CompactMenuArrow(QToolButton* button)
        : QLabel(button)
        , button_(button)
    {
        setObjectName(QStringLiteral("SolidFreeCADMenuArrow"));
        setText(QStringLiteral("▾"));
        setAlignment(Qt::AlignCenter);
        setAttribute(Qt::WA_TransparentForMouseEvents);
        setFixedSize(9, 9);
        setStyleSheet(QStringLiteral(R"QSS(
            QLabel#SolidFreeCADMenuArrow {
                color: #4b4b4b;
                background: transparent;
                border: 0;
                font-size: 9px;
                font-weight: 600;
                padding: 0;
                margin: 0;
            }
            QLabel#SolidFreeCADMenuArrow:disabled {
                color: #aaaaaa;
            }
        )QSS"));

        button_->installEventFilter(this);
        reposition();
        show();
        raise();
    }

    ~CompactMenuArrow() override
    {
        if (button_) {
            button_->removeEventFilter(this);
        }
    }

protected:
    bool eventFilter(QObject* watched, QEvent* event) override
    {
        if (watched == button_ && event) {
            switch (event->type()) {
                case QEvent::Resize:
                case QEvent::Move:
                case QEvent::Show:
                case QEvent::EnabledChange:
                    reposition();
                    break;
                default:
                    break;
            }
        }
        return QLabel::eventFilter(watched, event);
    }

private:
    void reposition()
    {
        if (!button_) {
            return;
        }

        move(qMax(0, button_->width() - width() - 2),
             qMax(0, button_->height() - height() - 2));
        setEnabled(button_->isEnabled());
        raise();
    }

    QPointer<QToolButton> button_;
};
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

    auto& commandManager = Gui::Application::Instance->commandManager();
    commandChangedConnection_ = commandManager.signalChanged.connect([this]() {
        QTimer::singleShot(0, this, [this]() { refreshRibbon(); });
    });

    refreshRibbon();
    QTimer::singleShot(0, this, [this]() { refreshRibbon(); });
    QTimer::singleShot(250, this, [this]() { refreshRibbon(); });
    QTimer::singleShot(750, this, [this]() { refreshRibbon(); });
    QTimer::singleShot(1500, this, [this]() { refreshRibbon(); });
    return true;
}

void SolidSketchEnhancements::uninstall()
{
    if (!installed_) {
        return;
    }

    commandChangedConnection_.disconnect();
    restoreSketchPalette();
    mainWindow_.clear();
    installed_ = false;
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

    viewParameters->SetUnsigned("FullyConstrainedColor", rgba(0, 0, 0));
    viewParameters->SetUnsigned("FullyConstraintElementColor", rgba(0, 0, 0));
    viewParameters->SetUnsigned(
        "FullyConstraintConstructionElementColor", rgba(72, 72, 72)
    );
    viewParameters->SetUnsigned(
        "FullyConstraintInternalAlignmentColor", rgba(96, 96, 96)
    );

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

    const auto commandStrips =
        ribbon->findChildren<QToolBar*>(QStringLiteral("SolidFreeCADCommandStrip"));
    for (QToolBar* toolbar : commandStrips) {
        configureSmartDimension(toolbar);
        toolbar->setIconSize(QSize(30, 30));

        for (QAction* action : toolbar->actions()) {
            if (!action) {
                continue;
            }

            const QString commandName =
                action->property("SolidFreeCADCommandName").toString();
            if (!hasCustomCommandIcon(commandName)) {
                continue;
            }

            const QString appliedCommand =
                action->property("SolidFreeCADCustomIconCommand").toString();
            if (appliedCommand == commandName) {
                continue;
            }

            action->setProperty("SolidFreeCADCustomIconCommand", commandName);
            action->setProperty("SolidFreeCADCustomIcon", true);
            action->setIcon(customCommandIcon(commandName, QSize(30, 30)));
        }
    }

    configureCompactMenuArrows(ribbon);
}

void SolidSketchEnhancements::configureSmartDimension(QToolBar* toolbar)
{
    if (!toolbar || !Gui::Application::Instance) {
        return;
    }

    for (QAction* action : toolbar->actions()) {
        if (!action
            || action->property("SolidFreeCADCommandName").toString()
                != QStringLiteral("Sketcher_CompDimensionTools")) {
            continue;
        }

        auto* button = qobject_cast<QToolButton*>(toolbar->widgetForAction(action));
        if (!button || button->property("SolidFreeCADSmartDimensionConfigured").toBool()) {
            continue;
        }

        action->setText(tr("Cota inteligente"));
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

        connect(menu, &QMenu::aboutToShow, menu, [menu]() {
            if (!Gui::Application::Instance) {
                return;
            }
            auto& manager = Gui::Application::Instance->commandManager();
            for (QAction* proxy : menu->actions()) {
                const QString commandName =
                    proxy->property("SolidFreeCADCommandName").toString();
                if (commandName.isEmpty()) {
                    continue;
                }
                Gui::Command* command =
                    manager.getCommandByName(commandName.toLatin1().constData());
                proxy->setEnabled(command && command->isActive());
            }
        });

        button->setMenu(menu);
        button->setPopupMode(QToolButton::MenuButtonPopup);
        button->setObjectName(QStringLiteral("qt_toolbutton_menubutton"));
        button->setProperty("SolidFreeCADSmartDimensionConfigured", true);
        button->setToolTip(tr(
            "Acota según la selección. Use la flecha para elegir una cota específica."
        ));
        button->style()->unpolish(button);
        button->style()->polish(button);
    }
}

void SolidSketchEnhancements::configureCompactMenuArrows(QToolBar* ribbon)
{
    if (!ribbon) {
        return;
    }

    if (!ribbon->property("SolidFreeCADNativeMenuIndicatorsHidden").toBool()) {
        ribbon->setStyleSheet(ribbon->styleSheet() + QStringLiteral(R"QSS(
            QToolBar#SolidFreeCADRibbon QToolButton::menu-indicator,
            QToolBar#SolidFreeCADRibbon QToolButton::menu-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border: 0;
                margin: 0;
                padding: 0;
            }
            QToolBar#SolidFreeCADRibbon QToolButton::menu-button,
            QToolBar#SolidFreeCADRibbon QToolButton#qt_toolbutton_menubutton::menu-button {
                background: transparent;
                border: 0;
                border-left: 0;
                width: 11px;
                margin: 0;
                padding: 0;
            }
            QToolBar#SolidFreeCADRibbon QToolButton::menu-button:hover,
            QToolBar#SolidFreeCADRibbon QToolButton#qt_toolbutton_menubutton::menu-button:hover {
                background: #e7f0f7;
                border: 0;
            }
        )QSS"));
        ribbon->setProperty("SolidFreeCADNativeMenuIndicatorsHidden", true);
    }

    const auto buttons = ribbon->findChildren<QToolButton*>();
    for (QToolButton* button : buttons) {
        if (!button) {
            continue;
        }

        const bool hasPopup = button->menu() != nullptr
            || button->popupMode() != QToolButton::DelayedPopup;
        if (!hasPopup
            || button->findChild<QLabel*>(QStringLiteral("SolidFreeCADMenuArrow"),
                                          Qt::FindDirectChildrenOnly)) {
            continue;
        }

        new CompactMenuArrow(button);
    }
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

    QAction* proxy = menu->addAction(QString::fromUtf8(fallbackText));
    proxy->setProperty("SolidFreeCADCommandName", QString::fromLatin1(commandName));
    proxy->setToolTip(QString::fromUtf8(command->getToolTipText()));
    proxy->setEnabled(command->isActive());

    const std::string stableCommandName(commandName);
    connect(proxy, &QAction::triggered, menu, [stableCommandName]() {
        if (Gui::Application::Instance) {
            Gui::Application::Instance->commandManager().runCommandByName(
                stableCommandName.c_str()
            );
        }
    });
    return true;
}

}  // namespace SolidFreeCAD
