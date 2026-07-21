#pragma once

#include <QIcon>
#include <QSize>
#include <QString>

namespace SolidFreeCAD
{

bool hasCustomCommandIcon(const QString& commandName);
QIcon customCommandIcon(const QString& commandName,
                        const QSize& logicalSize = QSize(32, 32));

}  // namespace SolidFreeCAD
