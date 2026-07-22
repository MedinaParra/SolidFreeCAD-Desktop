#pragma once

#include <QObject>
#include <QPointer>
#include <QString>

#include <boost/signals2/connection.hpp>

#include <Gui/Selection/Selection.h>

class QCheckBox;
class QDoubleSpinBox;
class QGroupBox;
class QLabel;
class QPushButton;
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

class SolidPartDesignMvp final : public QObject, private Gui::SelectionObserver
{
public:
    explicit SolidPartDesignMvp(QObject* parent = nullptr);
    ~SolidPartDesignMvp() override;

    bool install(Gui::MainWindow* mainWindow);
    void uninstall();
    bool isInstalled() const;

private:
    void onSelectionChanged(const Gui::SelectionChanges& message) override;

    void buildFeatureEditor();
    void applyRibbonScope();
    void refreshSelection();
    void applyChanges();

    App::DocumentObject* selectedObject() const;
    QString featureKind(App::DocumentObject* object) const;
    int referenceCount(App::DocumentObject* object) const;
    void setStatus(const QString& message, bool error = false);

    Gui::MainWindow* mainWindow_ = nullptr;
    QPointer<QWidget> propertyPanel_;
    QPointer<QGroupBox> featureGroup_;
    QPointer<QLabel> valueCaption_;
    QPointer<QDoubleSpinBox> valueEditor_;
    QPointer<QCheckBox> reversedEditor_;
    QPointer<QCheckBox> midplaneEditor_;
    QPointer<QCheckBox> useAllEdgesEditor_;
    QPointer<QLabel> referenceLabel_;
    QPointer<QPushButton> applyButton_;
    QPointer<QLabel> statusLabel_;
    QPointer<QTimer> scopeTimer_;
    boost::signals2::connection commandChangedConnection_;
    bool installed_ = false;
};

}  // namespace SolidFreeCAD
