#pragma once

#include <QPointer>
#include <QString>
#include <QStyle>

#include <QObject>

#include <Gui/Selection/Selection.h>

class QCheckBox;
class QDockWidget;
class QDoubleSpinBox;
class QLabel;
class QLineEdit;
class QPushButton;
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

class SolidPropertyManager final : public QObject, private Gui::SelectionObserver
{
public:
    explicit SolidPropertyManager(QObject* parent = nullptr);
    ~SolidPropertyManager() override;

    bool install(Gui::MainWindow* mainWindow);
    void uninstall();
    bool isInstalled() const;

private:
    void onSelectionChanged(const Gui::SelectionChanges& message) override;

    void buildPanel();
    void enhanceModelTree();
    void refreshSelection();
    void applyChanges();
    void editSketch();

    App::DocumentObject* selectedObject() const;
    QString featureKind(App::DocumentObject* object) const;
    void setStatus(const QString& message, bool error = false);
    void setFeatureControls(const QString& kind);

    Gui::MainWindow* mainWindow_ = nullptr;
    QPointer<QDockWidget> dock_;
    QPointer<QDockWidget> modelDock_;
    QPointer<QWidget> panel_;
    QPointer<QLabel> objectLabel_;
    QPointer<QLabel> typeLabel_;
    QPointer<QLabel> summaryLabel_;
    QPointer<QLabel> statusLabel_;
    QPointer<QLabel> lengthCaption_;
    QPointer<QLineEdit> labelEditor_;
    QPointer<QDoubleSpinBox> lengthEditor_;
    QPointer<QCheckBox> reversedEditor_;
    QPointer<QCheckBox> midplaneEditor_;
    QPointer<QPushButton> editSketchButton_;
    QPointer<QPushButton> applyButton_;
    QPointer<QPushButton> reloadButton_;
    bool splitApplied_ = false;
};

}  // namespace SolidFreeCAD
