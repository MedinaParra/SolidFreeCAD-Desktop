#include "SolidRibbonWidget.h"

#include "SolidCommandSearch.h"

#include <QAction>
#include <QFrame>
#include <QHBoxLayout>
#include <QLabel>
#include <QScrollArea>
#include <QSize>
#include <QSizePolicy>
#include <QStackedWidget>
#include <QTabBar>
#include <QToolBar>
#include <QVBoxLayout>

#include <Gui/Application.h>
#include <Gui/Command.h>

namespace SolidFreeCAD
{

SolidRibbonWidget::SolidRibbonWidget(QWidget* parent)
    : QWidget(parent)
{
    setObjectName(QStringLiteral("SolidFreeCADRibbonShell"));
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    setMinimumHeight(144);
    setMaximumHeight(144);

    auto* rootLayout = new QVBoxLayout(this);
    rootLayout->setContentsMargins(0, 0, 0, 0);
    rootLayout->setSpacing(0);

    buildQuickAccessBar(rootLayout);

    pages_ = new QStackedWidget(this);
    pages_->setObjectName(QStringLiteral("SolidFreeCADRibbonPages"));
    pages_->setMinimumHeight(85);
    pages_->setMaximumHeight(85);
    rootLayout->addWidget(pages_);

    tabs_ = new QTabBar(this);
    tabs_->setObjectName(QStringLiteral("SolidFreeCADRibbonTabs"));
    tabs_->setDocumentMode(true);
    tabs_->setDrawBase(false);
    tabs_->setExpanding(false);
    tabs_->setUsesScrollButtons(true);
    tabs_->setMinimumHeight(25);
    tabs_->setMaximumHeight(25);
    rootLayout->addWidget(tabs_);

    connect(tabs_, &QTabBar::currentChanged, pages_, &QStackedWidget::setCurrentIndex);

    setStyleSheet(QStringLiteral(R"QSS(
        QWidget#SolidFreeCADRibbonShell {
            background: #f4f4f4;
            border: 0;
            border-bottom: 1px solid #a9a9a9;
        }
        QWidget#SolidFreeCADQuickRow {
            background: #fafafa;
            border-bottom: 1px solid #c9c9c9;
        }
        QLabel#SolidFreeCADBrand {
            color: #1f648f;
            font-size: 14px;
            font-weight: 700;
            padding: 0 10px 0 12px;
        }
        QLabel#SolidFreeCADDocumentTitle {
            color: #202020;
            font-size: 11px;
            padding: 0 8px;
        }
        QLabel#SolidFreeCADStatusLight {
            color: #2d9442;
            font-size: 15px;
            padding: 0 5px;
        }
        QToolBar#SolidFreeCADQuickAccess {
            background: transparent;
            border: 0;
            spacing: 1px;
            padding: 1px;
        }
        QToolBar#SolidFreeCADQuickAccess QToolButton {
            background: transparent;
            border: 1px solid transparent;
            border-radius: 1px;
            padding: 2px;
        }
        QToolBar#SolidFreeCADQuickAccess QToolButton:hover {
            background: #e5f0f8;
            border-color: #78a9ca;
        }
        QToolBar#SolidFreeCADQuickAccess QToolButton:pressed,
        QToolBar#SolidFreeCADQuickAccess QToolButton:checked {
            background: #d7e9f5;
            border-color: #4d91bd;
        }
        QLineEdit#SolidFreeCADCommandSearch {
            background: #ffffff;
            color: #202020;
            border: 1px solid #b4b4b4;
            border-radius: 1px;
            min-height: 21px;
            padding: 2px 8px;
            margin: 3px 8px;
        }
        QLineEdit#SolidFreeCADCommandSearch:focus {
            border-color: #4b91bd;
        }
        QStackedWidget#SolidFreeCADRibbonPages,
        QScrollArea#SolidFreeCADRibbonPage,
        QWidget#SolidFreeCADRibbonPageViewport {
            background: #f5f5f5;
            border: 0;
        }
        QWidget#SolidFreeCADCommandGroup {
            background: transparent;
            border-right: 1px solid #bdbdbd;
        }
        QToolBar#SolidFreeCADCommandStrip {
            background: transparent;
            border: 0;
            spacing: 1px;
            padding: 1px 3px;
        }
        QToolBar#SolidFreeCADCommandStrip QToolButton {
            background: transparent;
            color: #202020;
            border: 1px solid transparent;
            border-radius: 1px;
            min-width: 62px;
            padding: 3px 4px 1px 4px;
            font-size: 9px;
        }
        QToolBar#SolidFreeCADCommandStrip QToolButton:hover {
            background: #ffffff;
            border-color: #8aaec5;
        }
        QToolBar#SolidFreeCADCommandStrip QToolButton:pressed,
        QToolBar#SolidFreeCADCommandStrip QToolButton:checked {
            background: #dcecf7;
            border-color: #4c91bd;
        }
        QToolBar#SolidFreeCADCommandStrip QToolButton:disabled {
            color: #9b9b9b;
        }
        QLabel#SolidFreeCADGroupTitle {
            color: #4d4d4d;
            font-size: 8px;
            padding: 0 5px 1px 5px;
        }
        QTabBar#SolidFreeCADRibbonTabs {
            background: #e8e8e8;
            border-top: 1px solid #bdbdbd;
        }
        QTabBar#SolidFreeCADRibbonTabs::tab {
            background: #e8e8e8;
            color: #202020;
            border: 1px solid transparent;
            border-right-color: #bdbdbd;
            min-height: 22px;
            padding: 1px 10px;
            font-size: 10px;
        }
        QTabBar#SolidFreeCADRibbonTabs::tab:selected {
            background: #ffffff;
            border-color: #a9a9a9;
            border-top: 2px solid #4b91bd;
            border-bottom-color: #ffffff;
            font-weight: 600;
        }
        QTabBar#SolidFreeCADRibbonTabs::tab:hover:!selected {
            background: #f7f7f7;
        }
    )QSS"));

    rebuild();
}

void SolidRibbonWidget::buildQuickAccessBar(QVBoxLayout* rootLayout)
{
    auto* quickRow = new QWidget(this);
    quickRow->setObjectName(QStringLiteral("SolidFreeCADQuickRow"));
    quickRow->setMinimumHeight(34);
    quickRow->setMaximumHeight(34);

    auto* rowLayout = new QHBoxLayout(quickRow);
    rowLayout->setContentsMargins(0, 0, 0, 0);
    rowLayout->setSpacing(2);

    auto* brand = new QLabel(tr("SolidFreeCAD"), quickRow);
    brand->setObjectName(QStringLiteral("SolidFreeCADBrand"));
    rowLayout->addWidget(brand);

    auto* quickTools = new QToolBar(quickRow);
    quickTools->setObjectName(QStringLiteral("SolidFreeCADQuickAccess"));
    quickTools->setMovable(false);
    quickTools->setFloatable(false);
    quickTools->setIconSize(QSize(19, 19));
    quickTools->setToolButtonStyle(Qt::ToolButtonIconOnly);

    addCommand(quickTools, {"Std_New", "Nuevo"}, true);
    addCommand(quickTools, {"Std_Open", "Abrir"}, true);
    addCommand(quickTools, {"Std_Save", "Guardar"}, true);
    addCommand(quickTools, {"Std_Print", "Imprimir"}, true);
    quickTools->addSeparator();
    addCommand(quickTools, {"Std_Undo", "Deshacer"}, true);
    addCommand(quickTools, {"Std_Redo", "Rehacer"}, true);
    rowLayout->addWidget(quickTools);

    rowLayout->addStretch(1);

    auto* documentTitle = new QLabel(tr("Sin título"), quickRow);
    documentTitle->setObjectName(QStringLiteral("SolidFreeCADDocumentTitle"));
    documentTitle->setAlignment(Qt::AlignCenter);
    rowLayout->addWidget(documentTitle, 1);

    rowLayout->addStretch(1);

    auto* statusLight = new QLabel(QStringLiteral("●"), quickRow);
    statusLight->setObjectName(QStringLiteral("SolidFreeCADStatusLight"));
    statusLight->setToolTip(tr("SolidFreeCAD interface active"));
    rowLayout->addWidget(statusLight);

    auto* search = new SolidCommandSearch(quickRow);
    search->setMinimumWidth(250);
    search->setMaximumWidth(330);
    search->setPlaceholderText(tr("Buscar comandos"));
    rowLayout->addWidget(search);

    auto* settings = new QToolBar(quickRow);
    settings->setObjectName(QStringLiteral("SolidFreeCADQuickAccess"));
    settings->setIconSize(QSize(18, 18));
    settings->setToolButtonStyle(Qt::ToolButtonIconOnly);
    addCommand(settings, {"Std_DlgPreferences", "Preferencias"}, true);
    rowLayout->addWidget(settings);

    rootLayout->addWidget(quickRow);
}

void SolidRibbonWidget::rebuild()
{
    if (!pages_ || !tabs_) {
        return;
    }

    while (pages_->count() > 0) {
        QWidget* page = pages_->widget(0);
        pages_->removeWidget(page);
        page->deleteLater();
    }
    while (tabs_->count() > 0) {
        tabs_->removeTab(tabs_->count() - 1);
    }

    addRibbonPages();
    tabs_->setCurrentIndex(0);
}

void SolidRibbonWidget::addRibbonPages()
{
    const auto addPage = [this](const QString& title, QWidget* page) {
        pages_->addWidget(page);
        tabs_->addTab(title);
    };

    addPage(tr("Operaciones"), createRibbonPage({
        {"Crear", {
            {"PartDesign_Pad", "Extruir"},
            {"PartDesign_Revolution", "Revolución"},
            {"PartDesign_AdditivePipe", "Barrido"},
            {"PartDesign_AdditiveLoft", "Recubrir"},
        }},
        {"Cortar", {
            {"PartDesign_Pocket", "Corte"},
            {"PartDesign_Groove", "Corte revolución"},
            {"PartDesign_Hole", "Taladro"},
            {"PartDesign_SubtractivePipe", "Corte barrido"},
        }},
        {"Acabado", {
            {"PartDesign_Fillet", "Redondeo"},
            {"PartDesign_Chamfer", "Chaflán"},
            {"PartDesign_Draft", "Ángulo salida"},
            {"PartDesign_Thickness", "Vaciado"},
        }},
        {"Patrones", {
            {"PartDesign_LinearPattern", "Matriz lineal"},
            {"PartDesign_PolarPattern", "Matriz polar"},
            {"PartDesign_Mirrored", "Simetría"},
        }},
        {"Referencia", {
            {"PartDesign_Plane", "Plano"},
            {"PartDesign_Line", "Eje"},
            {"PartDesign_Point", "Punto"},
        }},
        {"Vista", {
            {"Std_ViewFitAll", "Ajustar"},
            {"Std_ViewIsometric", "Isométrica"},
        }},
    }));

    addPage(tr("Croquis"), createRibbonPage({
        {"Croquis", {
            {"Sketcher_LeaveSketch", "Salir del croquis"},
            {"Sketcher_Dimension", "Cota inteligente"},
        }},
        {"Geometría", {
            {"Sketcher_CompLine", "Línea"},
            {"Sketcher_CompCreateRectangles", "Rectángulo"},
            {"Sketcher_CompCreateArc", "Arcos y círculos"},
            {"Sketcher_CompCreateConic", "Cónicas"},
            {"Sketcher_CompSlot", "Ranura"},
            {"Sketcher_CompCreateBSpline", "Spline"},
        }},
        {"Editar entidades", {
            {"Sketcher_CompCurveEdition", "Recortar entidades"},
            {"Sketcher_CompExternal", "Convertir entidades"},
            {"Sketcher_Offset", "Equidistanciar entidades"},
        }},
        {"Transformar", {
            {"Sketcher_Symmetry", "Crear simetría"},
            {"Sketcher_Translate", "Matriz lineal de croquis"},
            {"Sketcher_Rotate", "Mover entidades"},
        }},
        {"Relaciones", {
            {"Sketcher_SelectConstraints", "Visualizar/Eliminar relaciones"},
            {"Sketcher_ValidateSketch", "Reparar croquis"},
            {"Sketcher_SelectElementsAssociatedWithConstraints", "Relaciones asociadas"},
        }},
        {"Asistencia", {
            {"Sketcher_ConstrainCoincidentUnified", "Capturas rápidas"},
            {"Sketcher_CompHorVer", "Croquis rápido"},
            {"Sketcher_ToggleConstruction", "Instant 2D"},
            {"Sketcher_ViewSection", "Contornos sombreados"},
        }},
    }));

    addPage(tr("Chapa metálica"), createRibbonPage({
        {"Base", {
            {"SheetMetal_AddBase", "Brida base"},
            {"SheetMetal_AddWall", "Pestaña"},
            {"SheetMetal_AddBend", "Pliegue"},
        }},
        {"Operaciones", {
            {"SheetMetal_AddJunction", "Unión"},
            {"SheetMetal_AddRelief", "Alivio"},
            {"SheetMetal_AddForming", "Conformado"},
        }},
        {"Desplegado", {
            {"SheetMetal_Unfold", "Desplegar"},
            {"SheetMetal_Refold", "Replegar"},
        }},
    }));

    addPage(tr("Piezas soldadas"), createRibbonPage({
        {"Estructura", {
            {"Arch_Profile", "Perfil"},
            {"Arch_Frame", "Miembro estructural"},
            {"PartDesign_AdditiveLoft", "Transición"},
        }},
        {"Uniones", {
            {"PartDesign_Boolean", "Combinar"},
            {"PartDesign_Chamfer", "Preparar borde"},
            {"PartDesign_Pocket", "Recorte"},
        }},
        {"Inspección", {
            {"Std_MeasureDistance", "Medir"},
            {"Std_ViewFitAll", "Ajustar vista"},
        }},
    }));

    addPage(tr("Ensamblaje"), createRibbonPage({
        {"Componentes", {
            {"Assembly_CreateAssembly", "Nuevo ensamblaje"},
            {"Assembly_InsertComponent", "Insertar componente"},
            {"Assembly_CreateJoint", "Crear unión"},
        }},
        {"Posición", {
            {"Assembly_CreateFixedJoint", "Fijar"},
            {"Assembly_Solve", "Resolver"},
            {"Assembly_ToggleGrounded", "Anclar"},
        }},
        {"Vista", {
            {"Std_ViewIsometric", "Isométrica"},
            {"Std_ViewFitAll", "Ajustar"},
        }},
    }));

    addPage(tr("Inspección"), createRibbonPage({
        {"Medición", {
            {"Std_MeasureDistance", "Distancia"},
            {"Std_MeasureAngle", "Ángulo"},
            {"Std_MeasureArea", "Área"},
        }},
        {"Análisis", {
            {"Part_CheckGeometry", "Comprobar geometría"},
            {"Part_Measure_Linear", "Medición lineal"},
            {"Std_DlgMacroExecute", "Herramientas"},
        }},
        {"Sección", {
            {"Std_ViewSectionCut", "Corte de sección"},
            {"Std_ViewClipPlane", "Plano de corte"},
        }},
    }));

    addPage(tr("Simulación"), createRibbonPage({
        {"Estudio", {
            {"FEM_Analysis", "Nuevo estudio"},
            {"FEM_MaterialSolid", "Material"},
            {"FEM_ConstraintFixed", "Fijación"},
        }},
        {"Cargas", {
            {"FEM_ConstraintForce", "Fuerza"},
            {"FEM_ConstraintPressure", "Presión"},
            {"FEM_ConstraintGravity", "Gravedad"},
        }},
        {"Malla", {
            {"FEM_MeshGmshFromShape", "Generar malla"},
            {"FEM_SolverCalculix", "Solver"},
            {"FEM_SolverRun", "Ejecutar"},
        }},
        {"Resultados", {
            {"FEM_ResultShow", "Resultados"},
            {"FEM_PostPipelineFromResult", "Postproceso"},
        }},
    }));

    addPage(tr("Plano"), createRibbonPage({
        {"Página", {
            {"TechDraw_PageDefault", "Nueva página"},
            {"TechDraw_View", "Vista"},
            {"TechDraw_SectionView", "Sección"},
        }},
        {"Anotación", {
            {"TechDraw_Dimension", "Cota"},
            {"TechDraw_HorizontalDimension", "Cota horizontal"},
            {"TechDraw_VerticalDimension", "Cota vertical"},
            {"TechDraw_LeaderLine", "Directriz"},
        }},
        {"Exportar", {
            {"TechDraw_ExportPageDXF", "Exportar DXF"},
            {"Std_Print", "Imprimir"},
        }},
    }));
}

QWidget* SolidRibbonWidget::createRibbonPage(std::initializer_list<CommandGroup> groups)
{
    auto* scroll = new QScrollArea(pages_);
    scroll->setObjectName(QStringLiteral("SolidFreeCADRibbonPage"));
    scroll->setWidgetResizable(true);
    scroll->setHorizontalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    scroll->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    scroll->setFrameShape(QFrame::NoFrame);

    auto* viewport = new QWidget(scroll);
    viewport->setObjectName(QStringLiteral("SolidFreeCADRibbonPageViewport"));
    auto* layout = new QHBoxLayout(viewport);
    layout->setContentsMargins(3, 2, 3, 1);
    layout->setSpacing(0);

    for (const CommandGroup& group : groups) {
        layout->addWidget(createCommandGroup(group));
    }
    layout->addStretch(1);

    scroll->setWidget(viewport);
    return scroll;
}

QWidget* SolidRibbonWidget::createCommandGroup(const CommandGroup& group)
{
    auto* container = new QWidget(pages_);
    container->setObjectName(QStringLiteral("SolidFreeCADCommandGroup"));
    auto* layout = new QVBoxLayout(container);
    layout->setContentsMargins(2, 0, 2, 0);
    layout->setSpacing(0);

    auto* toolbar = new QToolBar(container);
    toolbar->setObjectName(QStringLiteral("SolidFreeCADCommandStrip"));
    toolbar->setMovable(false);
    toolbar->setFloatable(false);
    toolbar->setIconSize(QSize(28, 28));
    toolbar->setToolButtonStyle(Qt::ToolButtonTextUnderIcon);
    toolbar->setMinimumHeight(64);
    toolbar->setMaximumHeight(64);

    for (const CommandItem& item : group.commands) {
        addCommand(toolbar, item);
    }

    layout->addWidget(toolbar);

    auto* label = new QLabel(QString::fromUtf8(group.title), container);
    label->setObjectName(QStringLiteral("SolidFreeCADGroupTitle"));
    label->setAlignment(Qt::AlignHCenter | Qt::AlignVCenter);
    layout->addWidget(label);

    return container;
}

bool SolidRibbonWidget::addCommand(QToolBar* toolbar, const CommandItem& item, bool compact)
{
    if (!toolbar || !item.commandName || !*item.commandName || !Gui::Application::Instance) {
        return false;
    }

    auto& manager = Gui::Application::Instance->commandManager();
    if (Gui::Command* command = manager.getCommandByName(item.commandName)) {
        const int previousCount = toolbar->actions().size();
        command->addTo(toolbar);
        if (toolbar->actions().size() > previousCount) {
            QAction* action = toolbar->actions().last();
            action->setProperty("SolidFreeCADCommandName", QString::fromLatin1(item.commandName));
            if (!compact && item.fallbackText && *item.fallbackText) {
                action->setText(QString::fromUtf8(item.fallbackText));
            }
            if (compact && action->toolTip().isEmpty()) {
                action->setToolTip(QString::fromUtf8(item.fallbackText));
            }
        }
        return true;
    }

    QAction* unavailable = toolbar->addAction(QString::fromUtf8(item.fallbackText));
    unavailable->setProperty("SolidFreeCADCommandName", QString::fromLatin1(item.commandName));
    unavailable->setEnabled(false);
    unavailable->setToolTip(tr("Disponible al cargar el módulo correspondiente de FreeCAD"));
    return false;
}

}  // namespace SolidFreeCAD
