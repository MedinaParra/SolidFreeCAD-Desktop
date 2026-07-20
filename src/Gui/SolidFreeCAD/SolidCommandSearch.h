#pragma once

#include <QLineEdit>

#include <boost/signals2/connection.hpp>

class QStringListModel;

namespace SolidFreeCAD
{

class SolidCommandSearch final : public QLineEdit
{
public:
    explicit SolidCommandSearch(QWidget* parent = nullptr);
    ~SolidCommandSearch() override;

    void refreshCatalog();

private:
    void executeCurrentCommand();

    QStringListModel* model_ = nullptr;
    boost::signals2::scoped_connection commandChangedConnection_;
};

}  // namespace SolidFreeCAD
