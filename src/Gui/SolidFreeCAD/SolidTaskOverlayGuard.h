#pragma once

#include <QObject>
#include <QPointer>

class QTimer;

namespace Gui
{
class MainWindow;
}

namespace SolidFreeCAD
{

class SolidTaskOverlayGuard final : public QObject
{
public:
    explicit SolidTaskOverlayGuard(QObject* parent = nullptr);
    ~SolidTaskOverlayGuard() override;

    bool install(Gui::MainWindow* mainWindow);
    void uninstall();
    bool isInstalled() const;

private:
    void refresh();
    bool activeSketch() const;
    void synchronizeContextBadges(bool editing);
    void normalizeTaskDocks(bool editing);

    Gui::MainWindow* mainWindow_ = nullptr;
    QPointer<QTimer> refreshTimer_;
    bool installed_ = false;
    bool startupBadgeLock_ = false;
};

}  // namespace SolidFreeCAD
