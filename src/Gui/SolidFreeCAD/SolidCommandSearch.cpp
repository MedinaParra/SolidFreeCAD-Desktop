#include "SolidCommandSearch.h"

#include "SolidCommandBridge.h"

#include <QApplication>
#include <QCompleter>
#include <QStringList>
#include <QStringListModel>

#include <Gui/Application.h>
#include <Gui/Command.h>

namespace SolidFreeCAD
{

SolidCommandSearch::SolidCommandSearch(QWidget* parent)
    : QLineEdit(parent)
    , model_(new QStringListModel(this))
{
    setObjectName(QStringLiteral("SolidFreeCADCommandSearch"));
    setPlaceholderText(tr("Search FreeCAD commands…"));
    setClearButtonEnabled(true);
    setMinimumWidth(240);

    auto* commandCompleter = new QCompleter(model_, this);
    commandCompleter->setCaseSensitivity(Qt::CaseInsensitive);
    commandCompleter->setFilterMode(Qt::MatchContains);
    commandCompleter->setCompletionMode(QCompleter::PopupCompletion);
    setCompleter(commandCompleter);

    connect(this, &QLineEdit::returnPressed, this, [this]() { executeCurrentCommand(); });

    if (Gui::Application::Instance) {
        auto& manager = Gui::Application::Instance->commandManager();
        commandChangedConnection_ = manager.signalChanged.connect([this]() { refreshCatalog(); });
    }

    refreshCatalog();
}

SolidCommandSearch::~SolidCommandSearch()
{
    commandChangedConnection_.disconnect();
}

void SolidCommandSearch::refreshCatalog()
{
    QStringList commandNames;

    if (Gui::Application::Instance) {
        const auto commands = Gui::Application::Instance->commandManager().getAllCommands();
        commandNames.reserve(static_cast<qsizetype>(commands.size()));
        for (const Gui::Command* command : commands) {
            if (command && command->getName()) {
                commandNames.append(QString::fromLatin1(command->getName()));
            }
        }
    }

    commandNames.removeDuplicates();
    commandNames.sort(Qt::CaseInsensitive);
    model_->setStringList(commandNames);
}

void SolidCommandSearch::executeCurrentCommand()
{
    const QByteArray commandName = text().trimmed().toLatin1();
    if (commandName.isEmpty()) {
        return;
    }

    if (SolidCommandBridge::invoke(commandName.constData())) {
        clear();
        return;
    }

    QApplication::beep();
    selectAll();
    setToolTip(tr("Command is not available in the active FreeCAD context"));
}

}  // namespace SolidFreeCAD
