#pragma once

#include <QObject>

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
    bool addCommand(const char* commandName);

    Gui::MainWindow* mainWindow_ = nullptr;
    QToolBar* ribbon_ = nullptr;
};

}  // namespace SolidFreeCAD
