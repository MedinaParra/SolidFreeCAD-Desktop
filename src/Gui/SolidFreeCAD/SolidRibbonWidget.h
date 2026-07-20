#pragma once

#include <QWidget>

class QStackedWidget;
class QTabBar;
class QToolBar;
class QVBoxLayout;

namespace SolidFreeCAD
{

class SolidRibbonWidget final : public QWidget
{
public:
    explicit SolidRibbonWidget(QWidget* parent = nullptr);

    void rebuild();

private:
    struct CommandItem
    {
        const char* commandName;
        const char* fallbackText;
    };

    struct CommandGroup
    {
        const char* title;
        std::initializer_list<CommandItem> commands;
    };

    QWidget* createRibbonPage(std::initializer_list<CommandGroup> groups);
    QWidget* createCommandGroup(const CommandGroup& group);
    bool addCommand(QToolBar* toolbar, const CommandItem& item, bool compact = false);
    void buildQuickAccessBar(QVBoxLayout* rootLayout);
    void addRibbonPages();

    QStackedWidget* pages_ = nullptr;
    QTabBar* tabs_ = nullptr;
};

}  // namespace SolidFreeCAD
