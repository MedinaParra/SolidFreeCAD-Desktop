#include "SolidPropertyManager.h"

#include "SolidCommandBridge.h"

#include <cmath>
#include <exception>
#include <string>

#include <QAbstractItemView>
#include <QApplication>
#include <QCheckBox>
#include <QDockWidget>
#include <QDoubleSpinBox>
#include <QFormLayout>
#include <QFrame>
#include <QGroupBox>
#include <QHeaderView>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QSignalBlocker>
#include <QTabWidget>
#include <QTimer>
#include <QTreeView>
#include <QVBoxLayout>
#include <QWidget>

#include <App/Document.h>
#include <App/DocumentObject.h>
#include <App/PropertyStandard.h>
#include <App/PropertyUnits.h>
#include <Base/Exception.h>
#include <Gui/DockWindowManager.h>
#include <Gui/MainWindow.h>
#include <Gui/Selection/Selection.h>

namespace
{

template<typename PropertyType>
PropertyType* propertyAs(App::DocumentObject* object, const char* name)
{
    if (!object || !name) {
        return nullptr;
    }
    return dynamic_cast<PropertyType*>(object->getPropertyByName(name));
}

QString propertyString(App::DocumentObject* object, const char* name)
{
    if (auto* property = propertyAs<App::PropertyString>(object, name)) {
        return QString::fromUtf8(property->getValue());
    }
    return {};
}

}  // namespace

namespace SolidFreeCAD
{

SolidPropertyManager::SolidPropertyManager(QObject* parent)
    : QObject(parent)
    , Gui::SelectionObserver(true, Gui::ResolveMode::NoResolve)
{}

SolidPropertyManager::~SolidPropertyManager()
{
    uninstall();
}

bool SolidPropertyManager::install(Gui::MainWindow* mainWindow)
{
    if (!mainWindow) {
        return false;
    }

    mainWindow_ = mainWindow;
    if (!dock_) {
        buildPanel();
    }

    enhanceModelTree();
    refreshSelection();

    QTimer::singleShot(0, this, [this]() { enhanceModelTree(); });
    QTimer::singleShot(250, this, [this]() { enhanceModelTree(); });
    QTimer::singleShot(750, this, [this]() { enhanceModelTree(); });
    return dock_ != nullptr;
}

void SolidPropertyManager::uninstall()
{
    if (dock_) {
        if (mainWindow_) {
            mainWindow_->removeDockWidget(dock_);
        }
        dock_->deleteLater();
    }

    dock_.clear();
    modelDock_.clear();
    panel_.clear();
    objectLabel_.clear();
    typeLabel_.clear();
    summaryLabel_.clear();
    statusLabel_.clear();
    lengthCaption_.clear();
    labelEditor_.clear();
    lengthEditor_.clear();
    reversedEditor_.clear();
    midplaneEditor_.clear();
    editSketchButton_.clear();
    applyButton_.clear();
    reloadButton_.clear();
    splitApplied_ = false;
    mainWindow_ = nullptr;
}

bool SolidPropertyManager::isInstalled() const
{
    return dock_ != nullptr;
}

void SolidPropertyManager::onSelectionChanged(const Gui::SelectionChanges& message)
{
    if (message.Type == Gui::SelectionChanges::AddSelection
        || message.Type == Gui::SelectionChanges::RmvSelection
        || message.Type == Gui::SelectionChanges::SetSelection
        || message.Type == Gui::SelectionChanges::ClrSelection) {
        QTimer::singleShot(0, this, [this]() { refreshSelection(); });
    }
}

void SolidPropertyManager::buildPanel()
{
    if (!mainWindow_) {
        return;
    }

    dock_ = new QDockWidget(tr("Property Manager"), mainWindow_);
    dock_->setObjectName(QStringLiteral("SolidFreeCADPropertyManager"));
    dock_->setAllowedAreas(Qt::LeftDockWidgetArea | Qt::RightDockWidgetArea);
    dock_->setFeatures(QDockWidget::DockWidgetMovable | QDockWidget::DockWidgetFloatable);
    dock_->setMinimumWidth(286);
    dock_->setMinimumHeight(230);

    panel_ = new QWidget(dock_);
    panel_->setObjectName(QStringLiteral("SolidFreeCADPropertyManagerWidget"));
    panel_->setProperty("SolidFeatureKind", QStringLiteral("None"));

    auto* outer = new QVBoxLayout(panel_);
    outer->setContentsMargins(8, 8, 8, 8);
    outer->setSpacing(7);

    objectLabel_ = new QLabel(tr("Ningún elemento seleccionado"), panel_);
    objectLabel_->setObjectName(QStringLiteral("SolidFreeCADPropertyObject"));
    objectLabel_->setWordWrap(true);
    objectLabel_->setTextInteractionFlags(Qt::TextSelectableByMouse);
    outer->addWidget(objectLabel_);

    typeLabel_ = new QLabel(tr("Seleccione un Croquis, Pad o Pocket"), panel_);
    typeLabel_->setObjectName(QStringLiteral("SolidFreeCADPropertyType"));
    outer->addWidget(typeLabel_);

    summaryLabel_ = new QLabel(
        tr("El editor usa las propiedades oficiales del documento FCStd y una transacción reversible."),
        panel_);
    summaryLabel_->setObjectName(QStringLiteral("SolidFreeCADPropertySummary"));
    summaryLabel_->setWordWrap(true);
    outer->addWidget(summaryLabel_);

    auto* separator = new QFrame(panel_);
    separator->setFrameShape(QFrame::HLine);
    separator->setFrameShadow(QFrame::Sunken);
    outer->addWidget(separator);

    auto* group = new QGroupBox(tr("Parámetros"), panel_);
    group->setObjectName(QStringLiteral("SolidFreeCADPropertyFields"));
    auto* form = new QFormLayout(group);
    form->setContentsMargins(8, 9, 8, 8);
    form->setHorizontalSpacing(8);
    form->setVerticalSpacing(7);
    form->setFieldGrowthPolicy(QFormLayout::AllNonFixedFieldsGrow);

    labelEditor_ = new QLineEdit(group);
    labelEditor_->setObjectName(QStringLiteral("SolidFreeCADLabelEditor"));
    labelEditor_->setClearButtonEnabled(true);
    form->addRow(tr("Nombre"), labelEditor_);

    lengthCaption_ = new QLabel(tr("Longitud"), group);
    lengthEditor_ = new QDoubleSpinBox(group);
    lengthEditor_->setObjectName(QStringLiteral("SolidFreeCADLengthEditor"));
    lengthEditor_->setDecimals(3);
    lengthEditor_->setRange(0.001, 1000000.0);
    lengthEditor_->setSingleStep(1.0);
    lengthEditor_->setSuffix(tr(" mm"));
    lengthEditor_->setKeyboardTracking(false);
    form->addRow(lengthCaption_, lengthEditor_);

    reversedEditor_ = new QCheckBox(tr("Dirección invertida"), group);
    reversedEditor_->setObjectName(QStringLiteral("SolidFreeCADReversedEditor"));
    form->addRow(QString(), reversedEditor_);

    midplaneEditor_ = new QCheckBox(tr("Plano medio"), group);
    midplaneEditor_->setObjectName(QStringLiteral("SolidFreeCADMidplaneEditor"));
    form->addRow(QString(), midplaneEditor_);

    outer->addWidget(group);

    editSketchButton_ = new QPushButton(tr("Editar croquis"), panel_);
    editSketchButton_->setObjectName(QStringLiteral("SolidFreeCADEditSketch"));
    connect(editSketchButton_, &QPushButton::clicked, this, [this]() { editSketch(); });
    outer->addWidget(editSketchButton_);

    auto* buttons = new QHBoxLayout();
    reloadButton_ = new QPushButton(tr("Recargar"), panel_);
    reloadButton_->setObjectName(QStringLiteral("SolidFreeCADReloadProperties"));
    applyButton_ = new QPushButton(tr("Aplicar"), panel_);
    applyButton_->setObjectName(QStringLiteral("SolidFreeCADApplyProperties"));
    applyButton_->setDefault(true);
    connect(reloadButton_, &QPushButton::clicked, this, [this]() { refreshSelection(); });
    connect(applyButton_, &QPushButton::clicked, this, [this]() { applyChanges(); });
    buttons->addWidget(reloadButton_);
    buttons->addStretch(1);
    buttons->addWidget(applyButton_);
    outer->addLayout(buttons);

    statusLabel_ = new QLabel(tr("Listo"), panel_);
    statusLabel_->setObjectName(QStringLiteral("SolidFreeCADPropertyStatus"));
    statusLabel_->setWordWrap(true);
    outer->addWidget(statusLabel_);
    outer->addStretch(1);

    panel_->setStyleSheet(QStringLiteral(R"QSS(
        QWidget#SolidFreeCADPropertyManagerWidget {
            background: #f5f6f7;
            color: #202326;
        }
        QLabel#SolidFreeCADPropertyObject {
            font-size: 14px;
            font-weight: 700;
            color: #18222b;
        }
        QLabel#SolidFreeCADPropertyType {
            color: #39759b;
            font-weight: 600;
        }
        QLabel#SolidFreeCADPropertySummary {
            color: #5d666d;
        }
        QLabel#SolidFreeCADPropertyStatus[error="true"] {
            color: #b3261e;
            font-weight: 600;
        }
        QLabel#SolidFreeCADPropertyStatus[error="false"] {
            color: #2e6d43;
        }
        QGroupBox {
            background: #ffffff;
            border: 1px solid #c8cdd1;
            border-radius: 2px;
            margin-top: 8px;
            font-weight: 600;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 7px;
            padding: 0 3px;
        }
        QLineEdit, QDoubleSpinBox {
            min-height: 24px;
            background: #ffffff;
            border: 1px solid #aeb6bc;
            padding: 2px 4px;
        }
        QPushButton {
            min-height: 25px;
            padding: 3px 10px;
        }
        QPushButton#SolidFreeCADApplyProperties {
            font-weight: 700;
        }
    )QSS"));

    dock_->setWidget(panel_);
    mainWindow_->addDockWidget(Qt::LeftDockWidgetArea, dock_);
    dock_->show();
}

void SolidPropertyManager::enhanceModelTree()
{
    if (!mainWindow_) {
        return;
    }

    auto* dockManager = Gui::DockWindowManager::instance();
    if (!dockManager) {
        return;
    }

    QWidget* modelWidget = dockManager->findRegisteredDockWindow("Std_ComboView");
    if (!modelWidget) {
        return;
    }

    QDockWidget* modelDock = qobject_cast<QDockWidget*>(modelWidget->parentWidget());
    if (!modelDock) {
        return;
    }

    modelDock_ = modelDock;
    modelDock_->setProperty("SolidFreeCADEnhancedModelManager", true);
    modelDock_->setMinimumWidth(286);

    const auto trees = modelWidget->findChildren<QTreeView*>();
    for (QTreeView* tree : trees) {
        if (!tree) {
            continue;
        }
        tree->setProperty("SolidFreeCADModelTree", true);
        tree->setAlternatingRowColors(true);
        tree->setUniformRowHeights(true);
        tree->setAllColumnsShowFocus(true);
        tree->setAnimated(false);
        tree->setIndentation(18);
        tree->setExpandsOnDoubleClick(true);
        tree->setHorizontalScrollMode(QAbstractItemView::ScrollPerPixel);
        tree->setVerticalScrollMode(QAbstractItemView::ScrollPerPixel);
        tree->setStyleSheet(QStringLiteral(R"QSS(
            QTreeView {
                background: #ffffff;
                alternate-background-color: #f7f8f9;
                border: 0;
                outline: 0;
                selection-background-color: #d7eaf7;
                selection-color: #101820;
            }
            QTreeView::item {
                min-height: 22px;
                padding: 1px 3px;
                border-bottom: 1px solid transparent;
            }
            QTreeView::item:hover {
                background: #edf5fa;
            }
            QTreeView::item:selected {
                border-left: 3px solid #2d84b8;
            }
        )QSS"));
        if (tree->header()) {
            tree->header()->setStretchLastSection(true);
        }
    }

    const auto tabWidgets = modelWidget->findChildren<QTabWidget*>();
    for (QTabWidget* tabs : tabWidgets) {
        if (!tabs || tabs->count() < 2) {
            continue;
        }
        tabs->setDocumentMode(true);
        tabs->setTabText(0, tr("Modelo"));
        tabs->setTabText(1, tr("Tareas"));
        break;
    }

    if (dock_ && !splitApplied_
        && mainWindow_->dockWidgetArea(modelDock_) != Qt::NoDockWidgetArea) {
        mainWindow_->addDockWidget(Qt::LeftDockWidgetArea, dock_);
        mainWindow_->splitDockWidget(modelDock_, dock_, Qt::Vertical);
        splitApplied_ = true;
        dock_->show();
    }
}

App::DocumentObject* SolidPropertyManager::selectedObject() const
{
    auto selection = Gui::Selection().getSelectionEx(
        nullptr,
        App::DocumentObject::getClassTypeId(),
        Gui::ResolveMode::NoResolve);
    if (selection.size() != 1) {
        return nullptr;
    }
    return selection.front().getObject();
}

QString SolidPropertyManager::featureKind(App::DocumentObject* object) const
{
    if (!object) {
        return QStringLiteral("None");
    }

    const std::string typeName = object->getTypeId().getName();
    if (typeName == "Sketcher::SketchObject") {
        return QStringLiteral("Sketch");
    }
    if (typeName == "PartDesign::Pad") {
        return QStringLiteral("Pad");
    }
    if (typeName == "PartDesign::Pocket") {
        return QStringLiteral("Pocket");
    }
    return QStringLiteral("Unsupported");
}

void SolidPropertyManager::refreshSelection()
{
    if (!panel_ || !labelEditor_ || !lengthEditor_) {
        return;
    }

    App::DocumentObject* object = selectedObject();
    const QString kind = featureKind(object);
    panel_->setProperty("SolidFeatureKind", kind);
    panel_->setProperty(
        "SolidObjectName",
        object ? QString::fromUtf8(object->getNameInDocument()) : QString());

    QSignalBlocker labelBlocker(labelEditor_);
    QSignalBlocker lengthBlocker(lengthEditor_);
    QSignalBlocker reversedBlocker(reversedEditor_);
    QSignalBlocker midplaneBlocker(midplaneEditor_);

    if (!object) {
        objectLabel_->setText(tr("Ningún elemento seleccionado"));
        typeLabel_->setText(tr("Seleccione un Croquis, Pad o Pocket"));
        summaryLabel_->setText(
            tr("La selección múltiple queda en modo de inspección para evitar cambios ambiguos."));
        labelEditor_->clear();
        lengthEditor_->setValue(1.0);
        reversedEditor_->setChecked(false);
        midplaneEditor_->setChecked(false);
        setFeatureControls(QStringLiteral("None"));
        setStatus(tr("Listo"));
        return;
    }

    const QString label = propertyString(object, "Label");
    objectLabel_->setText(label.isEmpty() ? QString::fromUtf8(object->getNameInDocument()) : label);
    typeLabel_->setText(QString::fromUtf8(object->getTypeId().getName()));
    labelEditor_->setText(label);

    if (auto* length = propertyAs<App::PropertyQuantity>(object, "Length")) {
        lengthEditor_->setValue(length->getValue());
        lengthEditor_->setEnabled(true);
    }
    else {
        lengthEditor_->setValue(1.0);
        lengthEditor_->setEnabled(false);
    }

    if (auto* reversed = propertyAs<App::PropertyBool>(object, "Reversed")) {
        reversedEditor_->setChecked(reversed->getValue());
        reversedEditor_->setEnabled(true);
    }
    else {
        reversedEditor_->setChecked(false);
        reversedEditor_->setEnabled(false);
    }

    if (auto* midplane = propertyAs<App::PropertyBool>(object, "Midplane")) {
        midplaneEditor_->setChecked(midplane->getValue());
        midplaneEditor_->setEnabled(true);
    }
    else {
        midplaneEditor_->setChecked(false);
        midplaneEditor_->setEnabled(false);
    }

    if (kind == QStringLiteral("Sketch")) {
        summaryLabel_->setText(
            tr("Edite el nombre aquí o abra el editor oficial de Sketcher para geometría y restricciones."));
    }
    else if (kind == QStringLiteral("Pad")) {
        summaryLabel_->setText(
            tr("Extrusión paramétrica. Los cambios se guardan como una única operación deshacible."));
    }
    else if (kind == QStringLiteral("Pocket")) {
        summaryLabel_->setText(
            tr("Corte paramétrico. Longitud, inversión y plano medio usan propiedades FCStd oficiales."));
    }
    else {
        summaryLabel_->setText(
            tr("Este tipo todavía usa el editor de propiedades oficial de FreeCAD."));
    }

    setFeatureControls(kind);
    setStatus(tr("Listo"));
}

void SolidPropertyManager::setFeatureControls(const QString& kind)
{
    const bool sketch = kind == QStringLiteral("Sketch");
    const bool lengthFeature = kind == QStringLiteral("Pad") || kind == QStringLiteral("Pocket");
    const bool supported = sketch || lengthFeature;

    lengthCaption_->setVisible(lengthFeature);
    lengthEditor_->setVisible(lengthFeature);
    reversedEditor_->setVisible(lengthFeature);
    midplaneEditor_->setVisible(lengthFeature);
    editSketchButton_->setVisible(sketch);
    editSketchButton_->setEnabled(sketch && SolidCommandBridge::isAvailable("Sketcher_EditSketch"));
    labelEditor_->setEnabled(supported);
    applyButton_->setEnabled(supported);
    reloadButton_->setEnabled(kind != QStringLiteral("None"));
}

void SolidPropertyManager::applyChanges()
{
    App::DocumentObject* object = selectedObject();
    const QString kind = featureKind(object);
    if (!object || (kind != QStringLiteral("Sketch") && kind != QStringLiteral("Pad")
                    && kind != QStringLiteral("Pocket"))) {
        setStatus(tr("Seleccione un Croquis, Pad o Pocket antes de aplicar."), true);
        return;
    }

    App::Document* document = object->getDocument();
    if (!document) {
        setStatus(tr("El objeto seleccionado no pertenece a un documento activo."), true);
        return;
    }

    bool transactionOpen = false;
    bool changed = false;
    try {
        document->openTransaction("SolidFreeCAD Property Manager");
        transactionOpen = true;

        if (auto* label = propertyAs<App::PropertyString>(object, "Label")) {
            const QByteArray desired = labelEditor_->text().trimmed().toUtf8();
            if (desired != QByteArray(label->getValue())) {
                label->setValue(desired.constData());
                changed = true;
            }
        }

        if (kind == QStringLiteral("Pad") || kind == QStringLiteral("Pocket")) {
            if (auto* length = propertyAs<App::PropertyQuantity>(object, "Length")) {
                if (std::abs(length->getValue() - lengthEditor_->value()) > 1e-9) {
                    length->setValue(lengthEditor_->value());
                    changed = true;
                }
            }
            if (auto* reversed = propertyAs<App::PropertyBool>(object, "Reversed")) {
                if (reversed->getValue() != reversedEditor_->isChecked()) {
                    reversed->setValue(reversedEditor_->isChecked());
                    changed = true;
                }
            }
            if (auto* midplane = propertyAs<App::PropertyBool>(object, "Midplane")) {
                if (midplane->getValue() != midplaneEditor_->isChecked()) {
                    midplane->setValue(midplaneEditor_->isChecked());
                    changed = true;
                }
            }
        }

        if (changed) {
            document->recompute();
            document->commitTransaction();
            transactionOpen = false;
            refreshSelection();
            setStatus(tr("Cambios aplicados. Use Deshacer para revertir la operación."));
        }
        else {
            document->abortTransaction();
            transactionOpen = false;
            setStatus(tr("No había cambios pendientes."));
        }
    }
    catch (const Base::Exception& exception) {
        if (transactionOpen) {
            document->abortTransaction();
        }
        setStatus(tr("No se pudieron aplicar los cambios: %1")
                      .arg(QString::fromUtf8(exception.what())),
                  true);
    }
    catch (const std::exception& exception) {
        if (transactionOpen) {
            document->abortTransaction();
        }
        setStatus(tr("No se pudieron aplicar los cambios: %1")
                      .arg(QString::fromUtf8(exception.what())),
                  true);
    }
    catch (...) {
        if (transactionOpen) {
            document->abortTransaction();
        }
        setStatus(tr("No se pudieron aplicar los cambios."), true);
    }
}

void SolidPropertyManager::editSketch()
{
    if (featureKind(selectedObject()) != QStringLiteral("Sketch")) {
        setStatus(tr("Seleccione un croquis antes de abrir el editor."), true);
        return;
    }

    if (!SolidCommandBridge::invoke("Sketcher_EditSketch")) {
        setStatus(tr("El comando de edición de Sketcher todavía no está disponible."), true);
        return;
    }
    setStatus(tr("Editor de croquis abierto."));
}

void SolidPropertyManager::setStatus(const QString& message, bool error)
{
    if (!statusLabel_) {
        return;
    }
    statusLabel_->setProperty("error", error);
    statusLabel_->setText(message);
    statusLabel_->style()->unpolish(statusLabel_);
    statusLabel_->style()->polish(statusLabel_);
}

}  // namespace SolidFreeCAD
