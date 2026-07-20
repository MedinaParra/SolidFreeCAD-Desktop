#pragma once

#include <QObject>
#include <QPointer>

#include <boost/signals2/connection.hpp>

class QEvent;
class QMenu;
class QToolBar;

namespace Gui
{
class MainWindow;
}

namespace SolidFreeCAD
{

class SolidSketchEnhancements final : public QObject
{
public:
    explicit SolidSketchEnhancements(QObject* parent = nullptr);
    ~SolidSketchEnhancements() override;

    bool install(Gui::MainWindow* mainWindow);
    void uninstall();

protected:
    bool eventFilter(QObject* watched, QEvent* event) override;

private:
    void applySketchPalette();
    void restoreSketchPalette();
    void refreshRibbon();
    void configureSmartDimension(QToolBar* toolbar);
    void configureCompactMenuArrows(QToolBar* ribbon);
    bool addMenuCommand(QMenu* menu, const char* commandName, const char* fallbackText);

    QPointer<Gui::MainWindow> mainWindow_;
    bool installed_ = false;
    bool paletteApplied_ = false;

    unsigned long previousFullyConstrainedColor_ = 0;
    unsigned long previousFullyConstraintElementColor_ = 0;
    unsigned long previousFullyConstraintConstructionElementColor_ = 0;
    unsigned long previousFullyConstraintInternalAlignmentColor_ = 0;
    unsigned long previousSketchFaceColor_ = 0;

    boost::signals2::scoped_connection commandChangedConnection_;
};

}  // namespace SolidFreeCAD
