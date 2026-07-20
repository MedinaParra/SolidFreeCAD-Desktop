#pragma once

#include <initializer_list>

#include <QObject>
#include <QString>

#include <boost/signals2/connection.hpp>

class QToolBar;

namespace Gui
{
class MainWindow;
}

namespace SolidFreeCAD
{

class SolidGuiManager final : public QObject
{
public:
    explicit SolidGuiManager(QObject* parent = nullptr);
    ~SolidGuiManager() override;

    bool install(Gui::MainWindow* mainWindow);
    void uninstall();
    bool isInstalled() const;

private:
    void rebuildRibbon();
    void addSection(const QString& title, std::initializer_list<const char*> commandNames);
    bool addCommand(const char* commandName);

    Gui::MainWindow* mainWindow_ = nullptr;
    QToolBar* ribbon_ = nullptr;
    boost::signals2::scoped_connection commandChangedConnection_;
};

}  // namespace SolidFreeCAD
