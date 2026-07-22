#include "SolidPartDesignMvp.h"

#include <cmath>
#include <exception>

#include <QCheckBox>
#include <QDoubleSpinBox>
#include <QFormLayout>
#include <QGroupBox>
#include <QLabel>
#include <QPushButton>
#include <QSignalBlocker>
#include <QStackedWidget>
#include <QTabBar>
#include <QTimer>
#include <QToolBar>
#include <QVBoxLayout>
#include <QWidget>

#include <App/Document.h>
#include <App/DocumentObject.h>
#include <App/PropertyLinks.h>
#include <App/PropertyStandard.h>
#include <App/PropertyUnits.h>
#include <Base/Exception.h>
#include <Base/Type.h>
#include <Gui/MainWindow.h>
#include <Gui/Selection/Selection.h>

namespace
{

template<typename PropertyType>
PropertyType* propertyAs(App::DocumentObject* object, const char* name)
{
    return object && name
        ? dynamic_cast<PropertyType*>(object->getPropertyByName(name))
        : nullptr;
}

bool isFreeCADType(App::DocumentObject* object, const char* typeName)
{
    return object
        && object->getTypeId().isDerivedFrom(Base::Type::fromName(typeName));
}

QString displayLabel(App::DocumentObject* object)
{
    if (auto* label = propertyAs<App::PropertyString>(object, "Label")) {
        return QString::fromUtf8(label->getValue());
    }
    return object ? QString::fromUtf8(object->getNameInDocument()) : QString();
}

}  // namespace

namespace SolidFreeCAD
{

SolidPartDesignMvp::SolidPartDesignMvp(QObject* parent)
    : QObject(parent)
    , Gui::SelectionObserver(true, Gui::ResolveMode::NoResolve)
{}

SolidPartDesignMvp::~SolidPartDesignMvp()
{
    uninstall();
}

bool SolidPartDesignMvp::install(Gui::MainWindow* mainWindow)
{
    if (installed_ || !mainWindow) {
        return installed_;
    }

    mainWindow_ = mainWindow;
    installed_ = true;
    buildFeatureEditor();
    applyRibbonScope();
    refreshSelection();

    for (const int delay : {0, 250, 700, 1400, 2400}) {
        QTimer::singleShot(delay, this, [this]() {
            buildFeatureEditor();
            applyRibbonScope();
            refreshSelection();
        });
    }
    return true;
}

void SolidPartDesignMvp::uninstall()
{
    if (!installed_) {
        return;
    }
    if (featureGroup_) {
        featureGroup_->deleteLater();
    }
    featureGroup_.clear();
    propertyPanel_.clear();
    valueCaption_.clear();
    valueEditor_.clear();
    reversedEditor_.clear();
    midplaneEditor_.clear();
    useAllEdgesEditor_.clear();
    referenceLabel_.clear();
    applyButton_.clear();
    statusLabel_.clear();
    mainWindow_ = nullptr;
    installed_ = false;
}

bool SolidPartDesignMvp::isInstalled() const
{
    return installed_;
}

void SolidPartDesignMvp::onSelectionChanged(const Gui::SelectionChanges& message)
{
    if (message.Type == Gui::SelectionChanges::AddSelection
        || message.Type == Gui::SelectionChanges::RmvSelection
        || message.Type == Gui::SelectionChanges::SetSelection
        || message.Type == Gui::SelectionChanges::ClrSelection) {
        QTimer::singleShot(15, this, [this]() { refreshSelection(); });
    }
}

void SolidPartDesignMvp::buildFeatureEditor()
{
    if (!mainWindow_ || featureGroup_) {
        return;
    }

    propertyPanel_ = mainWindow_->findChild<QWidget*>(
        QStringLiteral("SolidFreeCADPropertyManagerWidget")
    );
    auto* outer = propertyPanel_
        ? qobject_cast<QVBoxLayout*>(propertyPanel_->layout())
        : nullptr;
    if (!outer) {
        return;
    }

    statusLabel_ = propertyPanel_->findChild<QLabel*>(
        QStringLiteral("SolidFreeCADPropertyStatus")
    );

    featureGroup_ = new QGroupBox(tr("Operación avanzada"), propertyPanel_);
    featureGroup_->setObjectName(QStringLiteral("SolidFreeCADM3FeatureGroup"));
    auto* form = new QFormLayout(featureGroup_);
    form->setContentsMargins(8, 9, 8, 8);
    form->setFieldGrowthPolicy(QFormLayout::AllNonFixedFieldsGrow);

    valueCaption_ = new QLabel(tr("Valor"), featureGroup_);
    valueEditor_ = new QDoubleSpinBox(featureGroup_);
    valueEditor_->setObjectName(QStringLiteral("SolidFreeCADAdvancedValueEditor"));
    valueEditor_->setDecimals(3);
    valueEditor_->setKeyboardTracking(false);
    form->addRow(valueCaption_, valueEditor_);

    reversedEditor_ = new QCheckBox(tr("Dirección invertida"), featureGroup_);
    reversedEditor_->setObjectName(QStringLiteral("SolidFreeCADAdvancedReversed"));
    form->addRow(QString(), reversedEditor_);

    midplaneEditor_ = new QCheckBox(tr("Plano medio"), featureGroup_);
    midplaneEditor_->setObjectName(QStringLiteral("SolidFreeCADAdvancedMidplane"));
    form->addRow(QString(), midplaneEditor_);

    useAllEdgesEditor_ = new QCheckBox(tr("Aplicar a todas las aristas"), featureGroup_);
    useAllEdgesEditor_->setObjectName(QStringLiteral("SolidFreeCADUseAllEdges"));
    form->addRow(QString(), useAllEdgesEditor_);

    referenceLabel_ = new QLabel(featureGroup_);
    referenceLabel_->setObjectName(QStringLiteral("SolidFreeCADReferenceSummary"));
    referenceLabel_->setWordWrap(true);
    form->addRow(tr("Referencias"), referenceLabel_);

    applyButton_ = new QPushButton(tr("Aplicar operación"), featureGroup_);
    applyButton_->setObjectName(QStringLiteral("SolidFreeCADApplyAdvancedFeature"));
    applyButton_->setDefault(false);
    connect(applyButton_, &QPushButton::clicked, this, [this]() { applyChanges(); });
    form->addRow(QString(), applyButton_);

    featureGroup_->setStyleSheet(QStringLiteral(R"QSS(
        QGroupBox#SolidFreeCADM3FeatureGroup {
            background: #ffffff;
            border: 1px solid #8eb7d2;
            margin-top: 8px;
            font-weight: 700;
        }
        QDoubleSpinBox { min-height: 24px; background: #ffffff; border: 1px solid #8fa9ba; }
        QLabel#SolidFreeCADReferenceSummary { color: #52636f; }
        QPushButton#SolidFreeCADApplyAdvancedFeature {
            min-height: 27px;
            font-weight: 700;
            background: #e8f3fa;
            border: 1px solid #6e9fbe;
        }
    )QSS"));

    const int insertionIndex = std::max(0, outer->count() - 3);
    outer->insertWidget(insertionIndex, featureGroup_);
    featureGroup_->hide();
}

void SolidPartDesignMvp::applyRibbonScope()
{
    if (!mainWindow_) {
        return;
    }
    auto* ribbon = mainWindow_->findChild<QToolBar*>(QStringLiteral("SolidFreeCADRibbon"));
    auto* tabs = ribbon
        ? ribbon->findChild<QTabBar*>(QStringLiteral("SolidFreeCADRibbonTabs"))
        : nullptr;
    auto* pages = ribbon
        ? ribbon->findChild<QStackedWidget*>(QStringLiteral("SolidFreeCADRibbonPages"))
        : nullptr;
    if (!ribbon || !tabs || !pages) {
        return;
    }

    for (int index = tabs->count() - 1; index >= 0; --index) {
        const QString title = tabs->tabText(index);
        if (title == tr("Simulación") || title == tr("Simulation")) {
            QWidget* page = index < pages->count() ? pages->widget(index) : nullptr;
            tabs->removeTab(index);
            if (page) {
                pages->removeWidget(page);
                page->deleteLater();
            }
        }
    }
    ribbon->setProperty("SolidFreeCADSimulationRemoved", true);
}

App::DocumentObject* SolidPartDesignMvp::selectedObject() const
{
    const auto selection = Gui::Selection().getCompleteSelection(Gui::ResolveMode::NoResolve);
    if (selection.size() != 1) {
        return nullptr;
    }
    const auto& selected = selection.front();
    return selected.pResolvedObject ? selected.pResolvedObject : selected.pObject;
}

QString SolidPartDesignMvp::featureKind(App::DocumentObject* object) const
{
    if (!object) {
        return QStringLiteral("None");
    }
    const QString name = QString::fromUtf8(object->getNameInDocument());
    if (isFreeCADType(object, "PartDesign::Revolution")
        || (name.startsWith(QStringLiteral("Revolution"))
            && object->getPropertyByName("Angle")
            && object->getPropertyByName("ReferenceAxis"))) {
        return QStringLiteral("Revolution");
    }
    if (isFreeCADType(object, "PartDesign::Fillet")
        || (name.startsWith(QStringLiteral("Fillet"))
            && object->getPropertyByName("Radius")
            && object->getPropertyByName("UseAllEdges"))) {
        return QStringLiteral("Fillet");
    }
    if (isFreeCADType(object, "PartDesign::Chamfer")
        || (name.startsWith(QStringLiteral("Chamfer"))
            && object->getPropertyByName("Size")
            && object->getPropertyByName("UseAllEdges"))) {
        return QStringLiteral("Chamfer");
    }
    return QStringLiteral("Unsupported");
}

int SolidPartDesignMvp::referenceCount(App::DocumentObject* object) const
{
    if (auto* base = propertyAs<App::PropertyLinkSub>(object, "Base")) {
        return static_cast<int>(base->getSubValues().size());
    }
    return 0;
}

void SolidPartDesignMvp::refreshSelection()
{
    if (!featureGroup_ || !propertyPanel_) {
        return;
    }

    App::DocumentObject* object = selectedObject();
    const QString kind = featureKind(object);
    propertyPanel_->setProperty("SolidAdvancedFeatureKind", kind);

    const bool advanced = kind == QStringLiteral("Revolution")
        || kind == QStringLiteral("Fillet")
        || kind == QStringLiteral("Chamfer");
    featureGroup_->setVisible(advanced);
    if (!advanced) {
        return;
    }

    auto* objectLabel = propertyPanel_->findChild<QLabel*>(
        QStringLiteral("SolidFreeCADPropertyObject")
    );
    auto* typeLabel = propertyPanel_->findChild<QLabel*>(
        QStringLiteral("SolidFreeCADPropertyType")
    );
    auto* summaryLabel = propertyPanel_->findChild<QLabel*>(
        QStringLiteral("SolidFreeCADPropertySummary")
    );
    if (objectLabel) {
        objectLabel->setText(displayLabel(object));
    }
    if (typeLabel) {
        typeLabel->setText(QString::fromUtf8(object->getTypeId().getName()));
    }

    const QSignalBlocker blockValue(valueEditor_);
    const QSignalBlocker blockReversed(reversedEditor_);
    const QSignalBlocker blockMidplane(midplaneEditor_);
    const QSignalBlocker blockUseAll(useAllEdgesEditor_);

    if (kind == QStringLiteral("Revolution")) {
        featureGroup_->setTitle(tr("Revolución guiada"));
        valueCaption_->setText(tr("Ángulo"));
        valueEditor_->setRange(0.001, 360.0);
        valueEditor_->setSuffix(tr(" °"));
        if (auto* angle = propertyAs<App::PropertyQuantity>(object, "Angle")) {
            valueEditor_->setValue(angle->getValue());
        }
        if (auto* reversed = propertyAs<App::PropertyBool>(object, "Reversed")) {
            reversedEditor_->setChecked(reversed->getValue());
        }
        if (auto* midplane = propertyAs<App::PropertyBool>(object, "Midplane")) {
            midplaneEditor_->setChecked(midplane->getValue());
        }
        reversedEditor_->show();
        midplaneEditor_->show();
        useAllEdgesEditor_->hide();
        referenceLabel_->setText(tr("El perfil y el eje permanecen enlazados mediante propiedades nativas."));
        if (summaryLabel) {
            summaryLabel->setText(tr("Edite ángulo, dirección y plano medio dentro de una transacción deshacible."));
        }
    }
    else {
        const bool fillet = kind == QStringLiteral("Fillet");
        featureGroup_->setTitle(fillet ? tr("Redondeo guiado") : tr("Chaflán guiado"));
        valueCaption_->setText(fillet ? tr("Radio") : tr("Distancia"));
        valueEditor_->setRange(0.001, 1000000.0);
        valueEditor_->setSuffix(tr(" mm"));
        const char* valueProperty = fillet ? "Radius" : "Size";
        if (auto* value = propertyAs<App::PropertyQuantity>(object, valueProperty)) {
            valueEditor_->setValue(value->getValue());
        }
        if (auto* useAll = propertyAs<App::PropertyBool>(object, "UseAllEdges")) {
            useAllEdgesEditor_->setChecked(useAll->getValue());
        }
        reversedEditor_->hide();
        midplaneEditor_->hide();
        useAllEdgesEditor_->show();
        const int count = referenceCount(object);
        referenceLabel_->setText(useAllEdgesEditor_->isChecked()
            ? tr("Todas las aristas de la operación base")
            : tr("Referencias seleccionadas: %1").arg(count));
        if (summaryLabel) {
            summaryLabel->setText(fillet
                ? tr("Radio editable y control explícito de las aristas de redondeo.")
                : tr("Distancia editable y control explícito de las aristas de chaflán."));
        }
    }
    setStatus(tr("Operación lista para edición."));
}

void SolidPartDesignMvp::applyChanges()
{
    App::DocumentObject* object = selectedObject();
    const QString kind = featureKind(object);
    if (!object || (kind != QStringLiteral("Revolution")
                    && kind != QStringLiteral("Fillet")
                    && kind != QStringLiteral("Chamfer"))) {
        setStatus(tr("Seleccione una Revolución, un Redondeo o un Chaflán."), true);
        return;
    }
    if (valueEditor_->value() <= 0.0) {
        setStatus(tr("El valor debe ser mayor que cero."), true);
        return;
    }
    if ((kind == QStringLiteral("Fillet") || kind == QStringLiteral("Chamfer"))
        && !useAllEdgesEditor_->isChecked() && referenceCount(object) == 0) {
        setStatus(tr("Seleccione al menos una arista o active todas las aristas."), true);
        return;
    }

    App::Document* document = object->getDocument();
    bool transactionOpen = false;
    bool changed = false;
    try {
        document->openTransaction("SolidFreeCAD guided Part Design edit");
        transactionOpen = true;

        const char* valueProperty = kind == QStringLiteral("Revolution")
            ? "Angle"
            : (kind == QStringLiteral("Fillet") ? "Radius" : "Size");
        if (auto* value = propertyAs<App::PropertyQuantity>(object, valueProperty)) {
            if (std::abs(value->getValue() - valueEditor_->value()) > 1e-9) {
                value->setValue(valueEditor_->value());
                changed = true;
            }
        }

        if (kind == QStringLiteral("Revolution")) {
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
        else if (auto* useAll = propertyAs<App::PropertyBool>(object, "UseAllEdges")) {
            if (useAll->getValue() != useAllEdgesEditor_->isChecked()) {
                useAll->setValue(useAllEdgesEditor_->isChecked());
                changed = true;
            }
        }

        if (changed) {
            document->recompute();
            document->commitTransaction();
            transactionOpen = false;
            refreshSelection();
            setStatus(tr("Operación actualizada. Use Deshacer para revertirla."));
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
        setStatus(tr("No se pudo actualizar la operación: %1")
                      .arg(QString::fromUtf8(exception.what())), true);
    }
    catch (const std::exception& exception) {
        if (transactionOpen) {
            document->abortTransaction();
        }
        setStatus(tr("No se pudo actualizar la operación: %1")
                      .arg(QString::fromUtf8(exception.what())), true);
    }
    catch (...) {
        if (transactionOpen) {
            document->abortTransaction();
        }
        setStatus(tr("No se pudo actualizar la operación."), true);
    }
}

void SolidPartDesignMvp::setStatus(const QString& message, bool error)
{
    if (!statusLabel_ && propertyPanel_) {
        statusLabel_ = propertyPanel_->findChild<QLabel*>(
            QStringLiteral("SolidFreeCADPropertyStatus")
        );
    }
    if (!statusLabel_) {
        return;
    }
    statusLabel_->setProperty("error", error);
    statusLabel_->setText(message);
    statusLabel_->style()->unpolish(statusLabel_);
    statusLabel_->style()->polish(statusLabel_);
}

}  // namespace SolidFreeCAD
