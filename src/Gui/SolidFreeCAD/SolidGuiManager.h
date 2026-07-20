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
    void applyVisualPalette();
    void restoreVisualPalette();
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
    QString modelManagerOriginalStyle_;
    int modelManagerOriginalMinimumWidth_ = 0;
    bool modelManagerWasVisible_ = false;
    bool modelManagerAddedBySolid_ = false;

    bool visualPaletteApplied_ = false;
    bool previousGradient_ = true;
    bool previousRadialGradient_ = false;
    bool previousSimpleBackground_ = false;
    bool previousUseMidColor_ = false;
    unsigned long previousBackgroundColor_ = 0;
    unsigned long previousBackgroundColor2_ = 0;
    unsigned long previousBackgroundColor3_ = 0;
    unsigned long previousBackgroundColor4_ = 0;
    unsigned long previousDefaultShapeColor_ = 0;
    unsigned long previousSelectionColor_ = 0;
    unsigned long previousHighlightColor_ = 0;

    boost::signals2::scoped_connection commandChangedConnection_;
};

}  // namespace SolidFreeCAD
