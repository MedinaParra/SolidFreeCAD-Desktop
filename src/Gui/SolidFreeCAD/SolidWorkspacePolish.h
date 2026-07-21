#pragma once

#include <QPointer>

#include <QObject>

class QLabel;
class QToolBar;
class QWidget;

namespace Gui
{
class MainWindow;
}

namespace SolidFreeCAD
{

class SolidWorkspacePolish final : public QObject
{
public:
    explicit SolidWorkspacePolish(QObject* parent = nullptr);
    ~SolidWorkspacePolish() override;

    bool install(Gui::MainWindow* mainWindow);
    void uninstall();
    bool isInstalled() const;

private:
    void apply();
    void polishRibbon(QToolBar* ribbon);
    void polishSidePanels();
    void ensureContextBadge(QWidget* shell);
    void updateDocumentTitle(QWidget* shell);
    void stylePrimaryCommands(QToolBar* ribbon);

    Gui::MainWindow* mainWindow_ = nullptr;
    QPointer<QLabel> contextBadge_;
    QPointer<QLabel> documentTitle_;
    bool installed_ = false;
};

}  // namespace SolidFreeCAD
