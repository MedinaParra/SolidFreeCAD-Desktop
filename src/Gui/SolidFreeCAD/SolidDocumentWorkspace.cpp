#include "SolidDocumentWorkspace.h"

#include <QAction>
#include <QBoxLayout>
#include <QFrame>
#include <QHBoxLayout>
#include <QLabel>
#include <QScrollArea>
#include <QSize>
#include <QStackedWidget>
#include <QTabBar>
#include <QTimer>
#include <QToolBar>
#include <QVBoxLayout>
#include <QWidget>

#include <App/Application.h>
#include <App/Document.h>
#include <Gui/Application.h>
#include <Gui/Command.h>
#include <Gui/MainWindow.h>

namespace SolidFreeCAD
{

SolidDocumentWorkspace::SolidDocumentWorkspace(QObject* parent)
    : QObject(parent)
{}

SolidDocumentWorkspace::~SolidDocumentWorkspace()
{
    uninstall();
}

bool SolidDocumentWorkspace::install(Gui::MainWindow* mainWindow)
{
    if (installed_ || !mainWindow || !Gui::Application::Instance) {
        return installed_;
    }

    mainWindow_ = mainWindow;
    installed_ = true;

    auto& commandManager = Gui::Application::Instance->commandManager();
    commandChangedConnection_ = commandManager.signalChanged.connect([this]() {
        QTimer::singleShot(0, this, [this]() { apply(); });
    });

    for (const int delay : {0, 300, 800, 1500, 2400}) {
        QTimer::singleShot(delay, this, [this]() { apply(); });
    }

    statusTimer_ = new QTimer(this);
    statusTimer_->setInterval(500);
    connect(statusTimer_, &QTimer::timeout, this, [this]() {
        updateDocumentState();
        updateContextBadge();
    });
    statusTimer_->start();
    return true;
}

void SolidDocumentWorkspace::uninstall()
{
    if (!installed_) {
        return;
    }

    commandChangedConnection_.disconnect();
    if (statusTimer_) {
        statusTimer_->stop();
        statusTimer_->deleteLater();
    }

    statusTimer_.clear();
    documentState_.clear();
    documentTitle_.clear();
    contextBadge_.clear();
    ribbonTabs_.clear();
    mainWindow_ = nullptr;
    installed_ = false;
}

bool SolidDocumentWorkspace::isInstalled() const
{
    return installed_;
}

void SolidDocumentWorkspace::apply()
{
    if (!installed_ || !mainWindow_) {
        return;
    }

    auto* ribbon = mainWindow_->findChild<QToolBar*>(QStringLiteral("SolidFreeCADRibbon"));
    if (!ribbon) {
        return;
    }

    ensureFilePage(ribbon);
    ensureStartGroup(ribbon);

    QWidget* shell = ribbon->findChild<QWidget*>(QStringLiteral("SolidFreeCADRibbonShell"));
    if (shell) {
        ensureDocumentState(shell);
    }

    ribbonTabs_ = ribbon->findChild<QTabBar*>(QStringLiteral("SolidFreeCADRibbonTabs"));
    contextBadge_ = ribbon->findChild<QLabel*>(QStringLiteral("SolidFreeCADContextBadge"));
    if (ribbonTabs_ && !ribbonTabs_->property("SolidFreeCADContextConnected").toBool()) {
        connect(ribbonTabs_, &QTabBar::currentChanged, this, [this](int) {
            updateContextBadge();
        });
        ribbonTabs_->setProperty("SolidFreeCADContextConnected", true);
    }

    updateDocumentState();
    updateContextBadge();
}

void SolidDocumentWorkspace::ensureFilePage(QToolBar* ribbon)
{
    auto* pages = ribbon->findChild<QStackedWidget*>(QStringLiteral("SolidFreeCADRibbonPages"));
    auto* tabs = ribbon->findChild<QTabBar*>(QStringLiteral("SolidFreeCADRibbonTabs"));
    if (!pages || !tabs) {
        return;
    }

    for (int index = 0; index < tabs->count(); ++index) {
        if (tabs->tabText(index) == tr("Archivo")) {
            return;
        }
    }

    const QString previousTab = tabs->currentIndex() >= 0
        ? tabs->tabText(tabs->currentIndex())
        : QString();

    pages->insertWidget(0, createFilePage(pages));
    tabs->insertTab(0, tr("Archivo"));

    if (!previousTab.isEmpty()) {
        for (int index = 0; index < tabs->count(); ++index) {
            if (tabs->tabText(index) == previousTab) {
                tabs->setCurrentIndex(index);
                break;
            }
        }
    }
}

void SolidDocumentWorkspace::ensureStartGroup(QToolBar* ribbon)
{
    auto* pages = ribbon->findChild<QStackedWidget*>(QStringLiteral("SolidFreeCADRibbonPages"));
    auto* tabs = ribbon->findChild<QTabBar*>(QStringLiteral("SolidFreeCADRibbonTabs"));
    if (!pages || !tabs) {
        return;
    }

    int operationsIndex = -1;
    for (int index = 0; index < tabs->count(); ++index) {
        if (tabs->tabText(index) == tr("Operaciones")) {
            operationsIndex = index;
            break;
        }
    }
    if (operationsIndex < 0 || operationsIndex >= pages->count()) {
        return;
    }

    auto* scroll = qobject_cast<QScrollArea*>(pages->widget(operationsIndex));
    QWidget* viewport = scroll ? scroll->widget() : nullptr;
    auto* layout = viewport ? qobject_cast<QHBoxLayout*>(viewport->layout()) : nullptr;
    if (!layout) {
        return;
    }

    const auto groups = viewport->findChildren<QWidget*>(QString(), Qt::FindDirectChildrenOnly);
    for (QWidget* group : groups) {
        if (group && group->property("SolidFreeCADGroupId").toString()
                == QStringLiteral("ModelStart")) {
            return;
        }
    }

    QWidget* group = createCommandGroup(
        pages,
        "Inicio",
        {
            {"PartDesign_Body", "Nuevo cuerpo"},
            {"PartDesign_NewSketch", "Nuevo croquis"},
        },
        "ModelStart"
    );
    layout->insertWidget(0, group);
}

void SolidDocumentWorkspace::ensureDocumentState(QWidget* shell)
{
    if (!shell) {
        return;
    }

    if (!documentTitle_) {
        documentTitle_ = shell->findChild<QLabel*>(QStringLiteral("SolidFreeCADDocumentTitle"));
    }
    if (!documentTitle_ || documentState_) {
        return;
    }

    auto* row = documentTitle_->parentWidget();
    auto* layout = row ? qobject_cast<QBoxLayout*>(row->layout()) : nullptr;
    if (!layout) {
        return;
    }

    documentState_ = new QLabel(tr("SIN DOCUMENTO"), row);
    documentState_->setObjectName(QStringLiteral("SolidFreeCADDocumentState"));
    documentState_->setAlignment(Qt::AlignCenter);
    documentState_->setMinimumWidth(72);

    const int titleIndex = layout->indexOf(documentTitle_);
    layout->insertWidget(titleIndex >= 0 ? titleIndex + 1 : 1, documentState_);
}

void SolidDocumentWorkspace::updateDocumentState()
{
    if (!documentState_ || !documentTitle_) {
        return;
    }

    App::Document* document = App::GetApplication().getActiveDocument();
    if (!document) {
        documentTitle_->setText(tr("Sin documento"));
        documentTitle_->setToolTip(QString());
        documentState_->setText(tr("SIN DOCUMENTO"));
        documentState_->setToolTip(QString());
        documentState_->setStyleSheet(QStringLiteral(
            "QLabel#SolidFreeCADDocumentState { color:#666; background:#eeeeee; "
            "border:1px solid #cccccc; border-radius:8px; font-size:9px; "
            "font-weight:700; padding:2px 7px; }"
        ));
        return;
    }

    const QString label = QString::fromStdString(document->Label.getStrValue());
    const QString filename = QString::fromStdString(document->FileName.getStrValue());
    documentTitle_->setText(label.isEmpty() ? QString::fromUtf8(document->getName()) : label);
    documentTitle_->setToolTip(filename.isEmpty() ? tr("Documento nuevo") : filename);

    if (document->isSaved()) {
        documentState_->setText(tr("GUARDADO"));
        documentState_->setToolTip(filename);
        documentState_->setStyleSheet(QStringLiteral(
            "QLabel#SolidFreeCADDocumentState { color:#24764b; background:#e8f5ee; "
            "border:1px solid #a9d8bf; border-radius:8px; font-size:9px; "
            "font-weight:700; padding:2px 7px; }"
        ));
    }
    else {
        documentState_->setText(tr("NUEVO"));
        documentState_->setToolTip(tr("El documento todavía no tiene una ubicación FCStd"));
        documentState_->setStyleSheet(QStringLiteral(
            "QLabel#SolidFreeCADDocumentState { color:#9a5519; background:#fff2e3; "
            "border:1px solid #efc28c; border-radius:8px; font-size:9px; "
            "font-weight:700; padding:2px 7px; }"
        ));
    }
}

void SolidDocumentWorkspace::updateContextBadge()
{
    if (!ribbonTabs_) {
        return;
    }
    if (!contextBadge_ && mainWindow_) {
        contextBadge_ = mainWindow_->findChild<QLabel*>(QStringLiteral("SolidFreeCADContextBadge"));
    }
    if (!contextBadge_) {
        return;
    }

    const QString tab = ribbonTabs_->currentIndex() >= 0
        ? ribbonTabs_->tabText(ribbonTabs_->currentIndex())
        : QString();

    QString context = tab.toUpper();
    if (tab == tr("Operaciones")) {
        context = tr("PIEZA");
    }
    else if (tab == tr("Piezas soldadas")) {
        context = tr("SOLDADURA");
    }
    else if (tab == tr("Chapa metálica")) {
        context = tr("CHAPA");
    }

    contextBadge_->setText(context.isEmpty() ? tr("PIEZA") : context);
    contextBadge_->setToolTip(tr("Entorno activo: %1").arg(tab));
}

QWidget* SolidDocumentWorkspace::createFilePage(QStackedWidget* pages)
{
    auto* scroll = new QScrollArea(pages);
    scroll->setObjectName(QStringLiteral("SolidFreeCADRibbonPage"));
    scroll->setWidgetResizable(true);
    scroll->setHorizontalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    scroll->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    scroll->setFrameShape(QFrame::NoFrame);
    scroll->setProperty("SolidFreeCADPageId", QStringLiteral("File"));

    auto* viewport = new QWidget(scroll);
    viewport->setObjectName(QStringLiteral("SolidFreeCADRibbonPageViewport"));
    auto* layout = new QHBoxLayout(viewport);
    layout->setContentsMargins(6, 4, 6, 2);
    layout->setSpacing(0);

    layout->addWidget(createCommandGroup(
        pages,
        "Documento",
        {
            {"Std_New", "Nuevo"},
            {"Std_Open", "Abrir"},
            {"Std_Save", "Guardar"},
            {"Std_SaveAs", "Guardar como"},
        },
        "FileDocument"
    ));
    layout->addWidget(createCommandGroup(
        pages,
        "Intercambio",
        {
            {"Std_Import", "Importar"},
            {"Std_Export", "Exportar"},
        },
        "FileExchange"
    ));
    layout->addWidget(createCommandGroup(
        pages,
        "Proyecto",
        {
            {"Std_ProjectInfo", "Información"},
            {"Std_Print", "Imprimir"},
            {"Std_CloseActiveWindow", "Cerrar"},
        },
        "FileProject"
    ));
    layout->addStretch(1);

    scroll->setWidget(viewport);
    return scroll;
}

QWidget* SolidDocumentWorkspace::createCommandGroup(
    QStackedWidget* pages,
    const char* title,
    std::initializer_list<CommandSpec> commands,
    const char* groupId
)
{
    auto* container = new QWidget(pages);
    container->setObjectName(QStringLiteral("SolidFreeCADCommandGroup"));
    container->setProperty("SolidFreeCADGroupId", QString::fromLatin1(groupId));

    auto* layout = new QVBoxLayout(container);
    layout->setContentsMargins(2, 0, 2, 0);
    layout->setSpacing(0);

    auto* toolbar = new QToolBar(container);
    toolbar->setObjectName(QStringLiteral("SolidFreeCADCommandStrip"));
    toolbar->setMovable(false);
    toolbar->setFloatable(false);
    toolbar->setIconSize(QSize(30, 30));
    toolbar->setToolButtonStyle(Qt::ToolButtonTextUnderIcon);
    toolbar->setMinimumHeight(69);
    toolbar->setMaximumHeight(69);

    for (const CommandSpec& command : commands) {
        addCommand(toolbar, command);
    }
    layout->addWidget(toolbar);

    auto* label = new QLabel(QString::fromUtf8(title), container);
    label->setObjectName(QStringLiteral("SolidFreeCADGroupTitle"));
    label->setAlignment(Qt::AlignHCenter | Qt::AlignVCenter);
    layout->addWidget(label);
    return container;
}

bool SolidDocumentWorkspace::addCommand(QToolBar* toolbar, const CommandSpec& command)
{
    if (!toolbar || !command.first || !*command.first || !Gui::Application::Instance) {
        return false;
    }

    auto& manager = Gui::Application::Instance->commandManager();
    if (Gui::Command* nativeCommand = manager.getCommandByName(command.first)) {
        const int previousCount = toolbar->actions().size();
        nativeCommand->addTo(toolbar);
        if (toolbar->actions().size() > previousCount) {
            QAction* action = toolbar->actions().last();
            action->setProperty("SolidFreeCADCommandName", QString::fromLatin1(command.first));
            action->setProperty("SolidFreeCADDocumentCommand", true);
            action->setText(QString::fromUtf8(command.second));
        }
        return true;
    }

    QAction* unavailable = toolbar->addAction(QString::fromUtf8(command.second));
    unavailable->setProperty("SolidFreeCADCommandName", QString::fromLatin1(command.first));
    unavailable->setProperty("SolidFreeCADDocumentCommand", true);
    unavailable->setEnabled(false);
    unavailable->setToolTip(tr("Disponible cuando FreeCAD registre el módulo correspondiente"));
    return false;
}

}  // namespace SolidFreeCAD
