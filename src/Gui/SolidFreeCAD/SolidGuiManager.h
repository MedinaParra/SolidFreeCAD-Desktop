#pragma once

#include <QList>
#include <QPointer>
#include <QString>

#include <QObject>

#include <boost/signals2/connection.hpp>

class QDockWidget;
class QEvent;
class QMenuBar;
class QToolBar;

namespace Gui
{
class MainWindow;
}

namespace SolidFreeCAD
{

class SolidRibbonWidget;

class SolidGuiManager final : public QObject
{
public:
    explicit SolidGuiManager(QObject* parent = nullptr);
    ~SolidGuiManager() override;

    bool install(Gui::MainWindow* mainWindow);
    void uninstall();
    bool isInstalled() const;

protected:
    bool eventFilter(QObject* watched, QEvent* event) override;

private:
    void enforceSolidChrome();
    void ensureModelManager();
    void hideClassicChrome();
    void hideBottomUtilityDocks();
    void restoreModelManager();
    void restoreClassicChrome();
    void rebuildRibbon();

    Gui::MainWindow* mainWindow_ = nullptr;
    QToolBar* ribbon_ = nullptr;
    SolidRibbonWidget* ribbonShell_ = nullptr;
    QPointer<QMenuBar> hiddenMenuBar_;
    QList<QPointer<QToolBar>> hiddenToolbars_;
    QList<QPointer<QDockWidget>> hiddenDocks_;
    QPointer<QDockWidget> modelManagerDock_;
    QString modelManagerOriginalTitle_;
    int modelManagerOriginalMinimumWidth_ = 0;
    bool modelManagerWasVisible_ = false;
    bool modelManagerAddedBySolid_ = false;
    boost::signals2::scoped_connection commandChangedConnection_;
};

}  // namespace SolidFreeCAD
