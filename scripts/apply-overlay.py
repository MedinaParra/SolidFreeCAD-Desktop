#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


CMAKE_ANCHOR = "add_library(FreeCADGui SHARED)\n"
CMAKE_INSERT = CMAKE_ANCHOR + "add_subdirectory(SolidFreeCAD)\n"

INCLUDE_ANCHOR = '#include "MainWindow.h"\n'
INCLUDE_LINE = '#include "SolidFreeCAD/SolidGuiBootstrap.h"\n'

INSTALL_ANCHOR = '    statusBar()->showMessage(tr("Ready"), 2001);\n'
INSTALL_LINE = "    SolidFreeCAD::installGui(this);\n\n"

DESTRUCTOR_ANCHOR = "MainWindow::~MainWindow()\n{\n"
DESTRUCTOR_INSERT = DESTRUCTOR_ANCHOR + "    SolidFreeCAD::uninstallGui();\n"

PROPERTY_SELECTION_ANCHOR = (
    "    const auto selection = "
    "Gui::Selection().getCompleteSelection(Gui::ResolveMode::NoResolve);\n"
    "    return selection.size() == 1 ? selection.front().pObject : nullptr;\n"
)
PROPERTY_SELECTION_INSERT = (
    "    const auto selection = "
    "Gui::Selection().getCompleteSelection(Gui::ResolveMode::NoResolve);\n"
    "    if (selection.size() != 1) {\n"
    "        return nullptr;\n"
    "    }\n\n"
    "    const auto& selected = selection.front();\n"
    "    return selected.pResolvedObject ? selected.pResolvedObject : selected.pObject;\n"
)

SKETCH_EDIT_ANCHOR = "    Workbench::enterEditMode();\n\n"
SKETCH_EDIT_INSERT = (
    SKETCH_EDIT_ANCHOR
    + "    // SolidFreeCAD: rebuild and display native faces for closed profiles while editing.\n"
    + "    const auto& solidFreeCADProfileShape = getSketchObject()->InternalShape.getValue();\n"
    + "    setupCoinGeometry(\n"
    + "        solidFreeCADProfileShape,\n"
    + "        pcSketchFaces,\n"
    + "        this->Deviation.getValue(),\n"
    + "        this->AngularDeflection.getValue()\n"
    + "    );\n"
    + "    pcSketchFacesToggle->on = true;\n\n"
)

SKETCH_UNSET_ANCHOR = (
    "    if (ModNum != ViewProviderSketch::Default) {\n"
    "        return PartGui::ViewProvider2DObject::unsetEdit(ModNum);\n"
    "    }\n\n"
)
SKETCH_UNSET_INSERT = (
    SKETCH_UNSET_ANCHOR
    + "    // SolidFreeCAD: leave profile shading with the normal object visibility lifecycle.\n"
    + "    pcSketchFacesToggle->on = Visibility.getValue();\n\n"
)


def insert_once(text: str, anchor: str, insertion: str, description: str) -> str:
    if insertion in text:
        return text
    if anchor not in text:
        raise RuntimeError(f"Could not find {description} anchor")
    return text.replace(anchor, insertion, 1)


def replace_once(text: str, old: str, new: str, description: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Could not find {description} text")
    return text.replace(old, new, 1)


def polish_ribbon(destination_overlay: Path) -> None:
    ribbon_file = destination_overlay / "SolidRibbonWidget.cpp"
    ribbon_text = ribbon_file.read_text(encoding="utf-8")

    ribbon_text = replace_once(
        ribbon_text,
        "#include <QToolBar>\n",
        "#include <QToolBar>\n#include <QTimer>\n",
        "ribbon timer include",
    )
    ribbon_text = replace_once(
        ribbon_text,
        "#include <Gui/Application.h>\n",
        "#include <App/Application.h>\n#include <App/Document.h>\n#include <Gui/Application.h>\n",
        "active document includes",
    )
    ribbon_text = replace_once(
        ribbon_text,
        "    setMinimumHeight(137);\n    setMaximumHeight(137);\n",
        "    setMinimumHeight(151);\n    setMaximumHeight(151);\n",
        "ribbon shell height",
    )
    ribbon_text = replace_once(
        ribbon_text,
        "    pages_->setMinimumHeight(78);\n    pages_->setMaximumHeight(78);\n",
        "    pages_->setMinimumHeight(88);\n    pages_->setMaximumHeight(88);\n",
        "ribbon page height",
    )
    ribbon_text = replace_once(
        ribbon_text,
        "    rootLayout->addWidget(pages_);\n\n    tabs_ = new QTabBar(this);\n",
        "    tabs_ = new QTabBar(this);\n",
        "ribbon tab ordering start",
    )
    ribbon_text = replace_once(
        ribbon_text,
        "    tabs_->setMinimumHeight(25);\n    tabs_->setMaximumHeight(25);\n",
        "    tabs_->setMinimumHeight(27);\n    tabs_->setMaximumHeight(27);\n",
        "ribbon tab height",
    )
    ribbon_text = replace_once(
        ribbon_text,
        "    rootLayout->addWidget(tabs_);\n\n    connect(",
        "    rootLayout->addWidget(tabs_);\n    rootLayout->addWidget(pages_);\n\n    connect(",
        "ribbon tab ordering end",
    )
    ribbon_text = replace_once(
        ribbon_text,
        "    rowLayout->addWidget(brand);\n\n    auto* quickTools",
        "    rowLayout->addWidget(brand);\n\n"
        "    auto* contextBadge = new QLabel(tr(\"PIEZA\"), quickRow);\n"
        "    contextBadge->setObjectName(QStringLiteral(\"SolidFreeCADContextBadge\"));\n"
        "    contextBadge->setToolTip(tr(\"Entorno activo: diseño de piezas\"));\n"
        "    rowLayout->addWidget(contextBadge);\n\n"
        "    auto* quickTools",
        "workspace context badge",
    )
    ribbon_text = replace_once(
        ribbon_text,
        "    rowLayout->addWidget(documentTitle, 1);\n",
        "    rowLayout->addWidget(documentTitle, 1);\n\n"
        "    const auto refreshDocumentTitle = [documentTitle]() {\n"
        "        if (auto* document = App::GetApplication().getActiveDocument()) {\n"
        "            documentTitle->setText(QString::fromUtf8(document->getName()));\n"
        "        }\n"
        "        else {\n"
        "            documentTitle->setText(QObject::tr(\"Sin documento\"));\n"
        "        }\n"
        "    };\n"
        "    auto* documentTimer = new QTimer(documentTitle);\n"
        "    documentTimer->setInterval(400);\n"
        "    connect(documentTimer, &QTimer::timeout, documentTitle, refreshDocumentTitle);\n"
        "    refreshDocumentTitle();\n"
        "    documentTimer->start();\n",
        "active document title timer",
    )
    ribbon_text = replace_once(
        ribbon_text,
        "    addPage(tr(\"Operaciones\"), createRibbonPage({\n        {\"Crear\", {",
        "    addPage(tr(\"Operaciones\"), createRibbonPage({\n"
        "        {\"Inicio\", {\n"
        "            {\"PartDesign_Body\", \"Nuevo cuerpo\"},\n"
        "            {\"PartDesign_NewSketch\", \"Nuevo croquis\"},\n"
        "        }},\n"
        "        {\"Crear\", {",
        "modeling start group",
    )
    ribbon_text = replace_once(
        ribbon_text,
        "    layout->setContentsMargins(4, 2, 4, 1);\n",
        "    layout->setContentsMargins(6, 4, 6, 2);\n",
        "ribbon page margins",
    )
    ribbon_text = replace_once(
        ribbon_text,
        "    toolbar->setIconSize(QSize(27, 27));\n",
        "    toolbar->setIconSize(QSize(30, 30));\n",
        "command strip icon size",
    )
    ribbon_text = replace_once(
        ribbon_text,
        "    toolbar->setMinimumHeight(57);\n    toolbar->setMaximumHeight(57);\n",
        "    toolbar->setMinimumHeight(69);\n    toolbar->setMaximumHeight(69);\n",
        "command strip height",
    )
    ribbon_text = replace_once(
        ribbon_text,
        "    rebuild();\n}\n",
        "    setStyleSheet(styleSheet() + QStringLiteral(R\"QSS(\n"
        "        QLabel#SolidFreeCADContextBadge {\n"
        "            color: #1f5f87;\n"
        "            background: #e5f1f8;\n"
        "            border: 1px solid #b9d7e8;\n"
        "            border-radius: 8px;\n"
        "            font-size: 9px;\n"
        "            font-weight: 700;\n"
        "            padding: 2px 8px;\n"
        "            margin-right: 4px;\n"
        "        }\n"
        "        QToolBar#SolidFreeCADCommandStrip QToolButton[SolidFreeCADPrimaryCommand=\"true\"] {\n"
        "            background: #eef6fb;\n"
        "            border: 1px solid #c0dae9;\n"
        "            border-radius: 3px;\n"
        "            font-weight: 700;\n"
        "            min-width: 66px;\n"
        "        }\n"
        "        QToolBar#SolidFreeCADCommandStrip QToolButton[SolidFreeCADPrimaryCommand=\"true\"]:hover {\n"
        "            background: #dceef8;\n"
        "            border-color: #6ba7ca;\n"
        "        }\n"
        "        QTabBar#SolidFreeCADRibbonTabs::tab:selected {\n"
        "            color: #155f8d;\n"
        "        }\n"
        "    )QSS\"));\n\n"
        "    rebuild();\n}\n",
        "ribbon polish stylesheet",
    )
    ribbon_file.write_text(ribbon_text, encoding="utf-8")


def polish_icons(destination_overlay: Path) -> None:
    icon_file = destination_overlay / "SolidIconFactory.cpp"
    icon_text = icon_file.read_text(encoding="utf-8")

    icon_text = replace_once(
        icon_text,
        '    if (name == "PartDesign_Pad") {\n',
        '    if (name == "Std_New") {\n'
        '        painter.setPen(outline());\n'
        '        painter.setBrush(QColor("#ffffff"));\n'
        '        painter.drawRoundedRect(QRectF(7, 4, 18, 24), 1.5, 1.5);\n'
        '        painter.setPen(outline(blueDark, 1.1));\n'
        '        painter.drawLine(QPointF(11, 10), QPointF(21, 10));\n'
        '        painter.drawLine(QPointF(11, 14), QPointF(21, 14));\n'
        '        painter.setPen(outline(green, 2.0));\n'
        '        painter.drawLine(QPointF(22, 22), QPointF(29, 22));\n'
        '        painter.drawLine(QPointF(25.5, 18.5), QPointF(25.5, 25.5));\n'
        '    }\n'
        '    else if (name == "Std_Open") {\n'
        '        painter.setPen(outline());\n'
        '        painter.setBrush(yellow);\n'
        '        painter.drawPolygon(QPolygonF() << QPointF(4, 10) << QPointF(13, 10)\n'
        '                                       << QPointF(16, 14) << QPointF(28, 14)\n'
        '                                       << QPointF(25, 27) << QPointF(5, 27));\n'
        '        drawArrow(painter, QPointF(17, 7), QPointF(24, 12), blueDark, 1.7);\n'
        '    }\n'
        '    else if (name == "Std_Save") {\n'
        '        painter.setPen(outline());\n'
        '        painter.setBrush(blue);\n'
        '        painter.drawRoundedRect(QRectF(5, 5, 22, 22), 2, 2);\n'
        '        painter.setBrush(QColor("#f8fbfd"));\n'
        '        painter.drawRect(QRectF(9, 7, 13, 7));\n'
        '        painter.drawRect(QRectF(9, 18, 14, 7));\n'
        '        painter.setBrush(orange);\n'
        '        painter.drawRect(QRectF(18, 8, 3, 5));\n'
        '    }\n'
        '    else if (name == "Std_Undo" || name == "Std_Redo") {\n'
        '        painter.save();\n'
        '        if (name == "Std_Redo") {\n'
        '            painter.translate(32, 0);\n'
        '            painter.scale(-1, 1);\n'
        '        }\n'
        '        painter.setPen(outline(blueDark, 2.2));\n'
        '        painter.setBrush(Qt::NoBrush);\n'
        '        painter.drawArc(QRectF(7, 8, 20, 17), 25 * 16, 230 * 16);\n'
        '        painter.setPen(Qt::NoPen);\n'
        '        painter.setBrush(blueDark);\n'
        '        painter.drawPolygon(QPolygonF() << QPointF(7, 9) << QPointF(12, 6) << QPointF(12, 13));\n'
        '        painter.restore();\n'
        '    }\n'
        '    else if (name == "Std_DlgPreferences") {\n'
        '        painter.setPen(outline(ink, 2.2));\n'
        '        painter.drawLine(QPointF(7, 25), QPointF(24, 8));\n'
        '        painter.setBrush(orange);\n'
        '        painter.drawEllipse(QRectF(20, 4, 7, 7));\n'
        '        painter.setBrush(blueLight);\n'
        '        painter.drawEllipse(QRectF(4, 22, 7, 7));\n'
        '    }\n'
        '    else if (name == "Std_ViewFitAll") {\n'
        '        drawArrow(painter, QPointF(4, 4), QPointF(12, 12), blueDark, 1.7);\n'
        '        drawArrow(painter, QPointF(28, 4), QPointF(20, 12), blueDark, 1.7);\n'
        '        drawArrow(painter, QPointF(4, 28), QPointF(12, 20), blueDark, 1.7);\n'
        '        drawArrow(painter, QPointF(28, 28), QPointF(20, 20), blueDark, 1.7);\n'
        '        painter.setPen(outline(orange, 1.6));\n'
        '        painter.setBrush(QColor(242, 139, 44, 55));\n'
        '        painter.drawRoundedRect(QRectF(11, 11, 10, 10), 2, 2);\n'
        '    }\n'
        '    else if (name == "Std_ViewIsometric") {\n'
        '        drawIsoBlock(painter, QRectF(5, 6, 22, 21));\n'
        '    }\n'
        '    else if (name == "PartDesign_Body") {\n'
        '        drawIsoBlock(painter, QRectF(5, 8, 21, 19));\n'
        '        painter.setPen(outline(green, 2.0));\n'
        '        painter.drawLine(QPointF(23, 7), QPointF(29, 7));\n'
        '        painter.drawLine(QPointF(26, 4), QPointF(26, 10));\n'
        '    }\n'
        '    else if (name == "PartDesign_NewSketch") {\n'
        '        drawSketchFrame(painter);\n'
        '        painter.setPen(outline(green, 2.0));\n'
        '        painter.drawLine(QPointF(22, 24), QPointF(29, 24));\n'
        '        painter.drawLine(QPointF(25.5, 20.5), QPointF(25.5, 27.5));\n'
        '    }\n'
        '    else if (name == "PartDesign_Pad") {\n',
        "expanded SolidFreeCAD icon catalogue",
    )
    icon_text = replace_once(
        icon_text,
        "    return {\n        \"PartDesign_Pad\",",
        "    return {\n"
        "        \"Std_New\", \"Std_Open\", \"Std_Save\", \"Std_Undo\", \"Std_Redo\",\n"
        "        \"Std_DlgPreferences\", \"Std_ViewFitAll\", \"Std_ViewIsometric\",\n"
        "        \"PartDesign_Body\", \"PartDesign_NewSketch\", \"PartDesign_Pad\",",
        "custom icon command list",
    )
    icon_file.write_text(icon_text, encoding="utf-8")


def polish_command_presentation(destination_overlay: Path) -> None:
    enhancements_file = destination_overlay / "SolidSketchEnhancements.cpp"
    enhancements_text = enhancements_file.read_text(encoding="utf-8")
    old_block = '''            if (!hasCustomCommandIcon(commandName)) {
                continue;
            }

            const QString appliedCommand =
                action->property("SolidFreeCADCustomIconCommand").toString();
            if (appliedCommand == commandName) {
                continue;
            }

            action->setProperty("SolidFreeCADCustomIconCommand", commandName);
            action->setProperty("SolidFreeCADCustomIcon", true);
            action->setIcon(customCommandIcon(commandName, QSize(30, 30)));
'''
    new_block = '''            const bool primaryCommand =
                commandName == QStringLiteral("PartDesign_Body")
                || commandName == QStringLiteral("PartDesign_NewSketch")
                || commandName == QStringLiteral("PartDesign_Pad")
                || commandName == QStringLiteral("PartDesign_Pocket")
                || commandName == QStringLiteral("PartDesign_Hole")
                || commandName == QStringLiteral("Sketcher_CompDimensionTools");

            if (auto* button = qobject_cast<QToolButton*>(toolbar->widgetForAction(action))) {
                button->setProperty("SolidFreeCADPrimaryCommand", primaryCommand);
                button->setIconSize(primaryCommand ? QSize(38, 38) : QSize(30, 30));
                if (primaryCommand) {
                    button->setMinimumWidth(68);
                    button->setMinimumHeight(66);
                    button->setMaximumHeight(66);
                }
                button->style()->unpolish(button);
                button->style()->polish(button);
            }

            if (!hasCustomCommandIcon(commandName)) {
                continue;
            }

            const QString appliedCommand =
                action->property("SolidFreeCADCustomIconCommand").toString();
            if (appliedCommand == commandName) {
                continue;
            }

            action->setProperty("SolidFreeCADCustomIconCommand", commandName);
            action->setProperty("SolidFreeCADCustomIcon", true);
            action->setIcon(customCommandIcon(
                commandName,
                primaryCommand ? QSize(38, 38) : QSize(30, 30)
            ));
'''
    enhancements_text = replace_once(
        enhancements_text,
        old_block,
        new_block,
        "primary command presentation",
    )
    enhancements_text = replace_once(
        enhancements_text,
        "    configureCompactMenuArrows(ribbon);\n",
        "    const auto quickAccessToolbars =\n"
        "        ribbon->findChildren<QToolBar*>(QStringLiteral(\"SolidFreeCADQuickAccess\"));\n"
        "    for (QToolBar* toolbar : quickAccessToolbars) {\n"
        "        for (QAction* action : toolbar->actions()) {\n"
        "            if (!action) {\n"
        "                continue;\n"
        "            }\n"
        "            const QString commandName =\n"
        "                action->property(\"SolidFreeCADCommandName\").toString();\n"
        "            if (!hasCustomCommandIcon(commandName)) {\n"
        "                continue;\n"
        "            }\n"
        "            action->setProperty(\"SolidFreeCADCustomIconCommand\", commandName);\n"
        "            action->setProperty(\"SolidFreeCADCustomIcon\", true);\n"
        "            action->setIcon(customCommandIcon(commandName, QSize(21, 21)));\n"
        "        }\n"
        "    }\n\n"
        "    configureCompactMenuArrows(ribbon);\n",
        "quick access custom icons",
    )
    enhancements_file.write_text(enhancements_text, encoding="utf-8")


def polish_workspace(destination_overlay: Path, repo_root: Path) -> None:
    manager_file = destination_overlay / "SolidGuiManager.cpp"
    manager_text = manager_file.read_text(encoding="utf-8")
    manager_text = replace_once(
        manager_text,
        "    ribbon_->setMinimumHeight(144);\n    ribbon_->setMaximumHeight(144);\n",
        "    ribbon_->setMinimumHeight(158);\n    ribbon_->setMaximumHeight(158);\n",
        "command manager height",
    )
    manager_text = replace_once(
        manager_text,
        "    hideBottomUtilityDocks();\n    ensureModelManager();\n    ribbon_->show();\n",
        "    hideBottomUtilityDocks();\n    ensureModelManager();\n\n"
        "    const auto floatingPanels =\n"
        "        mainWindow_->findChildren<QDockWidget*>(QString(), Qt::FindDirectChildrenOnly);\n"
        "    for (QDockWidget* dock : floatingPanels) {\n"
        "        if (!dock || !dock->isVisible()) {\n"
        "            continue;\n"
        "        }\n"
        "        const QString identity =\n"
        "            (dock->objectName() + QLatin1Char(' ') + dock->windowTitle()).toLower();\n"
        "        const bool taskPanel = identity.contains(QStringLiteral(\"task\"))\n"
        "            || identity.contains(QStringLiteral(\"tarea\"));\n"
        "        const bool detached = dock->isFloating()\n"
        "            || mainWindow_->dockWidgetArea(dock) == Qt::NoDockWidgetArea;\n"
        "        if (taskPanel && detached) {\n"
        "            dock->hide();\n"
        "        }\n"
        "    }\n\n"
        "    ribbon_->show();\n",
        "floating task panel normalization",
    )
    manager_text = manager_text.replace("modelWidget->setMinimumWidth(250);", "modelWidget->setMinimumWidth(300);")
    manager_text = manager_text.replace("dock->setMinimumWidth(260);", "dock->setMinimumWidth(310);")
    manager_text = manager_text.replace('dock->setWindowTitle(tr("Modelo"));', 'dock->setWindowTitle(tr("Historial del modelo"));')
    manager_file.write_text(manager_text, encoding="utf-8")

    property_manager_file = destination_overlay / "SolidPropertyManager.cpp"
    property_text = property_manager_file.read_text(encoding="utf-8")
    property_text = property_text.replace('new QDockWidget(tr("Property Manager"), mainWindow_)', 'new QDockWidget(tr("Propiedades"), mainWindow_)')
    property_text = property_text.replace(
        "dock_->setAllowedAreas(Qt::LeftDockWidgetArea | Qt::RightDockWidgetArea);",
        "dock_->setAllowedAreas(Qt::LeftDockWidgetArea);",
    )
    property_text = property_text.replace(
        "dock_->setFeatures(QDockWidget::DockWidgetMovable | QDockWidget::DockWidgetFloatable);",
        "dock_->setFeatures(QDockWidget::DockWidgetMovable);",
    )
    property_text = property_text.replace("dock_->setMinimumWidth(286);", "dock_->setMinimumWidth(310);")
    property_text = property_text.replace("modelDock_->setMinimumWidth(286);", "modelDock_->setMinimumWidth(310);")
    property_text = replace_once(
        property_text,
        "            tabs->setTabText(0, tr(\"Modelo\"));\n"
        "            tabs->setTabText(1, tr(\"Tareas\"));\n"
        "            break;\n",
        "            tabs->setTabText(0, tr(\"Modelo\"));\n"
        "            tabs->setTabText(1, tr(\"Tareas\"));\n"
        "            tabs->setCurrentIndex(0);\n"
        "            break;\n",
        "model tab activation",
    )
    property_manager_file.write_text(property_text, encoding="utf-8")

    gui_smoke_file = repo_root / "tests" / "gui_smoke.py"
    gui_smoke_text = gui_smoke_file.read_text(encoding="utf-8")
    gui_smoke_text = insert_once(
        gui_smoke_text,
        "    stage(\"capture-modeling-start\")\n",
        "    FreeCADGui.Selection.clearSelection()\n"
        "    FreeCADGui.Selection.addSelection(active_document.Name, pad.Name)\n"
        "    process_for(0.25)\n"
        "    stage(\"capture-modeling-start\")\n",
        "modeling screenshot feature selection",
    )
    gui_smoke_file.write_text(gui_smoke_text, encoding="utf-8")


def apply(repo_root: Path, freecad_root: Path) -> None:
    source_overlay = repo_root / "src" / "Gui" / "SolidFreeCAD"
    destination_overlay = freecad_root / "src" / "Gui" / "SolidFreeCAD"
    cmake_file = freecad_root / "src" / "Gui" / "CMakeLists.txt"
    main_window_file = freecad_root / "src" / "Gui" / "MainWindow.cpp"
    sketch_view_file = (
        freecad_root / "src" / "Mod" / "Sketcher" / "Gui" / "ViewProviderSketch.cpp"
    )

    for required in (source_overlay, cmake_file, main_window_file, sketch_view_file):
        if not required.exists():
            raise FileNotFoundError(required)

    if destination_overlay.exists():
        shutil.rmtree(destination_overlay)
    shutil.copytree(source_overlay, destination_overlay)

    property_manager_file = destination_overlay / "SolidPropertyManager.cpp"
    property_manager_text = property_manager_file.read_text(encoding="utf-8")
    property_manager_text = insert_once(
        property_manager_text,
        PROPERTY_SELECTION_ANCHOR,
        PROPERTY_SELECTION_INSERT,
        "Property Manager resolved selection",
    )
    property_manager_file.write_text(property_manager_text, encoding="utf-8")

    polish_ribbon(destination_overlay)
    polish_icons(destination_overlay)
    polish_command_presentation(destination_overlay)
    polish_workspace(destination_overlay, repo_root)

    cmake_text = cmake_file.read_text(encoding="utf-8")
    cmake_text = insert_once(
        cmake_text,
        CMAKE_ANCHOR,
        CMAKE_INSERT,
        "FreeCADGui target",
    )
    cmake_file.write_text(cmake_text, encoding="utf-8")

    main_text = main_window_file.read_text(encoding="utf-8")
    if INCLUDE_LINE not in main_text:
        main_text = insert_once(
            main_text,
            INCLUDE_ANCHOR,
            INCLUDE_ANCHOR + INCLUDE_LINE,
            "MainWindow include",
        )
    if "SolidFreeCAD::installGui(this);" not in main_text:
        main_text = insert_once(
            main_text,
            INSTALL_ANCHOR,
            INSTALL_LINE + INSTALL_ANCHOR,
            "MainWindow constructor",
        )
    if "SolidFreeCAD::uninstallGui();" not in main_text:
        main_text = insert_once(
            main_text,
            DESTRUCTOR_ANCHOR,
            DESTRUCTOR_INSERT,
            "MainWindow destructor",
        )
    main_window_file.write_text(main_text, encoding="utf-8")

    sketch_text = sketch_view_file.read_text(encoding="utf-8")
    sketch_text = insert_once(
        sketch_text,
        SKETCH_EDIT_ANCHOR,
        SKETCH_EDIT_INSERT,
        "Sketcher edit-mode profile shading",
    )
    sketch_text = insert_once(
        sketch_text,
        SKETCH_UNSET_ANCHOR,
        SKETCH_UNSET_INSERT,
        "Sketcher unset-edit profile shading",
    )
    sketch_view_file.write_text(sketch_text, encoding="utf-8")

    marker = freecad_root / "SOLIDFREECAD_OVERLAY_APPLIED"
    marker.write_text("SolidFreeCAD GUI overlay applied\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply the SolidFreeCAD GUI overlay to official FreeCAD 1.1.1 source"
    )
    parser.add_argument("freecad_source", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    apply(repo_root, args.freecad_source.resolve())
    print(f"SolidFreeCAD overlay applied to {args.freecad_source.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
