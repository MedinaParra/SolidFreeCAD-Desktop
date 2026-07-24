#pragma once

#include <initializer_list>
#include <utility>

#include <QPointer>

#include <QObject>

#include <boost/signals2/connection.hpp>

class QLabel;
class QStackedWidget;
class QTabBar;
class QTimer;
class QToolBar;
class QWidget;

namespace Gui
{
class MainWindow;
}

namespace SolidFreeCAD
{

class SolidDocumentWorkspace final : public QObject
{
public:
    explicit SolidDocumentWorkspace(QObject* parent = nullptr);
    ~SolidDocumentWorkspace() override;

    bool install(Gui::MainWindow* mainWindow);
    void uninstall();
    bool isInstalled() const;

private:
    using CommandSpec = std::pair<const char*, const char*>;

    void apply();
    void ensureFilePage(QToolBar* ribbon);
    void ensureStartGroup(QToolBar* ribbon);
    void ensureDocumentState(QWidget* shell);
    void updateDocumentState();
    void updateContextBadge();

    QWidget* createFilePage(QStackedWidget* pages);
    QWidget* createCommandGroup(QStackedWidget* pages,
                                const char* title,
                                std::initializer_list<CommandSpec> commands,
                                const char* groupId);
    bool addCommand(QToolBar* toolbar, const CommandSpec& command);

    Gui::MainWindow* mainWindow_ = nullptr;
    QPointer<QLabel> documentState_;
    QPointer<QLabel> documentTitle_;
    QPointer<QLabel> contextBadge_;
    QPointer<QTabBar> ribbonTabs_;
    QPointer<QTimer> statusTimer_;
    boost::signals2::connection commandChangedConnection_;
    bool installed_ = false;
};

}  // namespace SolidFreeCAD
