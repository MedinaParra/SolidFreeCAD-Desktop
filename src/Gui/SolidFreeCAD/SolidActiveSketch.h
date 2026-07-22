#pragma once

#include <QObject>
#include <QPointer>

class QFrame;
class QLabel;
class QTabWidget;
class QTimer;
class QWidget;

namespace App
{
class DocumentObject;
}

namespace Gui
{
class MainWindow;
}

namespace SolidFreeCAD
{

class SolidActiveSketch final : public QObject
{
public:
    explicit SolidActiveSketch(QObject* parent = nullptr);
    ~SolidActiveSketch() override;

    bool install(Gui::MainWindow* mainWindow);
    void uninstall();
    bool isInstalled() const;

private:
    void refresh();
    bool activeSketch(App::DocumentObject** object = nullptr) const;
    void applyPreferences();
    void restorePreferences();
    void ensureConfirmationCorner();
    void ensureGuidancePanel();
    void configureNewSketchCommand();
    void updateConfirmationCorner(bool editing, App::DocumentObject* sketch);
    void updateGuidance(bool editing, App::DocumentObject* sketch);
    void updateTaskPanel(bool editing);
    void selectSketchRibbon();
    void repositionConfirmationCorner();

    Gui::MainWindow* mainWindow_ = nullptr;
    QPointer<QTimer> refreshTimer_;
    QPointer<QFrame> confirmationCorner_;
    QPointer<QFrame> guidanceFrame_;
    QPointer<QLabel> guidanceTitle_;
    QPointer<QLabel> guidanceText_;
    QPointer<QTabWidget> modelTaskTabs_;
    bool installed_ = false;
    bool previousEditing_ = false;
    bool preferencesApplied_ = false;
    bool previousLeaveSketchWithEscape_ = true;
    bool previousForceOrtho_ = false;
    bool previousRestoreCamera_ = true;
};

}  // namespace SolidFreeCAD
