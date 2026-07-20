#include "SolidIconFactory.h"

#include <QColor>
#include <QIcon>
#include <QLinearGradient>
#include <QPainter>
#include <QPainterPath>
#include <QPen>
#include <QPixmap>
#include <QPolygonF>

#include <cmath>

namespace
{
const QColor ink("#26343e");
const QColor blue("#2f8fc7");
const QColor blueLight("#86d2ee");
const QColor blueDark("#1f648e");
const QColor orange("#f28b2c");
const QColor orangeDark("#c85f16");
const QColor red("#d84d43");
const QColor green("#35a66f");
const QColor purple("#8a63b8");
const QColor yellow("#f1c84b");
const QColor pale("#eaf4fa");

QPen outline(const QColor& color = ink, qreal width = 1.35)
{
    QPen pen(color, width, Qt::SolidLine, Qt::RoundCap, Qt::RoundJoin);
    pen.setCosmetic(true);
    return pen;
}

void drawArrow(QPainter& painter,
               const QPointF& from,
               const QPointF& to,
               const QColor& color,
               qreal width = 2.1)
{
    painter.setPen(outline(color, width));
    painter.setBrush(Qt::NoBrush);
    painter.drawLine(from, to);

    const qreal angle = std::atan2(to.y() - from.y(), to.x() - from.x());
    const qreal length = 4.2;
    const qreal spread = 0.62;
    QPolygonF head;
    head << to
         << QPointF(to.x() - length * std::cos(angle - spread),
                    to.y() - length * std::sin(angle - spread))
         << QPointF(to.x() - length * std::cos(angle + spread),
                    to.y() - length * std::sin(angle + spread));
    painter.setPen(Qt::NoPen);
    painter.setBrush(color);
    painter.drawPolygon(head);
}

void drawIsoBlock(QPainter& painter, const QRectF& rect, bool hollow = false)
{
    const qreal x = rect.left();
    const qreal y = rect.top();
    const qreal w = rect.width();
    const qreal h = rect.height();
    const qreal dx = w * 0.23;
    const qreal dy = h * 0.19;

    QPolygonF top;
    top << QPointF(x + dx, y)
        << QPointF(x + w, y + dy)
        << QPointF(x + w - dx, y + h * 0.43)
        << QPointF(x, y + h * 0.24);
    QPolygonF left;
    left << QPointF(x, y + h * 0.24)
         << QPointF(x + w - dx, y + h * 0.43)
         << QPointF(x + w - dx, y + h)
         << QPointF(x, y + h * 0.79);
    QPolygonF right;
    right << QPointF(x + w - dx, y + h * 0.43)
          << QPointF(x + w, y + dy)
          << QPointF(x + w, y + h * 0.74)
          << QPointF(x + w - dx, y + h);

    painter.setPen(outline());
    painter.setBrush(blueLight);
    painter.drawPolygon(top);
    painter.setBrush(blue);
    painter.drawPolygon(left);
    painter.setBrush(blueDark);
    painter.drawPolygon(right);

    if (hollow) {
        painter.setPen(outline(QColor("#eff8fc"), 1.4));
        painter.setBrush(QColor(245, 250, 252, 225));
        painter.drawRoundedRect(QRectF(x + w * 0.25, y + h * 0.40, w * 0.42, h * 0.30), 2, 2);
    }
}

void drawDimension(QPainter& painter)
{
    painter.setPen(outline(blueDark, 1.55));
    painter.drawLine(QPointF(6, 10), QPointF(6, 25));
    painter.drawLine(QPointF(26, 10), QPointF(26, 25));
    painter.drawLine(QPointF(6, 14), QPointF(26, 14));
    painter.setBrush(red);
    painter.setPen(Qt::NoPen);
    painter.drawPolygon(QPolygonF() << QPointF(6, 14) << QPointF(10, 11.5) << QPointF(10, 16.5));
    painter.drawPolygon(QPolygonF() << QPointF(26, 14) << QPointF(22, 11.5) << QPointF(22, 16.5));
    painter.setPen(outline(ink, 1.2));
    painter.drawLine(QPointF(11, 23), QPointF(21, 23));
    painter.drawEllipse(QPointF(11, 23), 1.7, 1.7);
    painter.drawEllipse(QPointF(21, 23), 1.7, 1.7);
}

void drawCircularArrow(QPainter& painter, const QRectF& bounds, const QColor& color)
{
    painter.setPen(outline(color, 2.0));
    painter.setBrush(Qt::NoBrush);
    painter.drawArc(bounds, 35 * 16, 275 * 16);
    const QPointF tip(bounds.right() - 1.5, bounds.center().y() - 3.0);
    painter.setPen(Qt::NoPen);
    painter.setBrush(color);
    painter.drawPolygon(QPolygonF() << tip << QPointF(tip.x() - 5, tip.y() - 1)
                                    << QPointF(tip.x() - 2, tip.y() + 4));
}

void drawSketchFrame(QPainter& painter)
{
    painter.setPen(outline(blueDark, 1.2));
    painter.setBrush(QColor(231, 246, 252, 210));
    painter.drawRoundedRect(QRectF(5, 5, 22, 22), 2.2, 2.2);
    painter.setPen(QPen(QColor(177, 213, 231), 0.8, Qt::DashLine));
    painter.drawLine(QPointF(16, 7), QPointF(16, 25));
    painter.drawLine(QPointF(7, 16), QPointF(25, 16));
}

void drawIcon(QPainter& painter, const QString& name)
{
    painter.setRenderHint(QPainter::Antialiasing, true);

    if (name == "PartDesign_Pad") {
        drawIsoBlock(painter, QRectF(5, 10, 21, 17));
        drawArrow(painter, QPointF(16, 13), QPointF(16, 3), orange);
    }
    else if (name == "PartDesign_Pocket") {
        drawIsoBlock(painter, QRectF(5, 7, 21, 19));
        painter.setPen(outline(red, 1.7));
        painter.setBrush(QColor(249, 236, 234));
        painter.drawEllipse(QRectF(12, 9, 8, 5));
        drawArrow(painter, QPointF(16, 5), QPointF(16, 17), red);
    }
    else if (name == "PartDesign_Hole") {
        painter.setPen(outline());
        painter.setBrush(blueLight);
        painter.drawRoundedRect(QRectF(5, 9, 22, 17), 2, 2);
        painter.setBrush(QColor("#f7fbfd"));
        painter.drawEllipse(QRectF(11, 12, 10, 10));
        painter.setPen(QPen(orangeDark, 1.1, Qt::DashLine));
        painter.drawLine(QPointF(16, 5), QPointF(16, 28));
    }
    else if (name == "PartDesign_Revolution" || name == "PartDesign_Groove") {
        painter.setPen(outline(blueDark, 1.5));
        painter.setBrush(QColor(99, 190, 227, 100));
        QPainterPath profile;
        profile.moveTo(8, 25);
        profile.lineTo(8, 8);
        profile.lineTo(15, 8);
        profile.lineTo(18, 13);
        profile.lineTo(13, 18);
        profile.lineTo(13, 25);
        profile.closeSubpath();
        painter.drawPath(profile);
        painter.setPen(QPen(ink, 1, Qt::DashLine));
        painter.drawLine(QPointF(16, 4), QPointF(16, 28));
        drawCircularArrow(painter, QRectF(11, 5, 16, 20),
                          name == "PartDesign_Groove" ? red : orange);
    }
    else if (name == "PartDesign_AdditivePipe" || name == "PartDesign_SubtractivePipe") {
        const QColor accent = name == "PartDesign_SubtractivePipe" ? red : orange;
        painter.setPen(outline(blueDark, 2.0));
        QPainterPath path;
        path.moveTo(5, 24);
        path.cubicTo(9, 8, 22, 26, 27, 8);
        painter.drawPath(path);
        painter.setPen(outline(accent, 1.5));
        painter.setBrush(QColor(accent.red(), accent.green(), accent.blue(), 75));
        painter.drawEllipse(QRectF(3, 20, 8, 6));
        painter.drawEllipse(QRectF(22, 5, 7, 6));
    }
    else if (name == "PartDesign_AdditiveLoft") {
        painter.setPen(outline(blueDark, 1.4));
        painter.setBrush(QColor(104, 194, 228, 70));
        QPainterPath loft;
        loft.moveTo(7, 24);
        loft.lineTo(11, 8);
        loft.lineTo(22, 6);
        loft.lineTo(26, 23);
        loft.closeSubpath();
        painter.drawPath(loft);
        painter.setBrush(blueLight);
        painter.drawEllipse(QRectF(5, 21, 22, 5));
        painter.setBrush(orange);
        painter.drawEllipse(QRectF(10, 5, 13, 5));
    }
    else if (name == "PartDesign_Fillet") {
        painter.setPen(outline(blueDark, 2.0));
        painter.drawLine(QPointF(6, 25), QPointF(6, 10));
        painter.drawLine(QPointF(6, 25), QPointF(23, 25));
        painter.setPen(outline(orange, 3.0));
        painter.drawArc(QRectF(6, 8, 19, 19), 180 * 16, 90 * 16);
    }
    else if (name == "PartDesign_Chamfer") {
        painter.setPen(outline(blueDark, 2.0));
        painter.drawLine(QPointF(6, 25), QPointF(6, 9));
        painter.drawLine(QPointF(6, 25), QPointF(24, 25));
        painter.setPen(outline(orange, 3.0));
        painter.drawLine(QPointF(6, 13), QPointF(18, 25));
    }
    else if (name == "PartDesign_Thickness") {
        drawIsoBlock(painter, QRectF(4, 7, 24, 20), true);
        painter.setPen(outline(orange, 1.6));
        painter.drawArc(QRectF(10, 12, 12, 9), 0, 180 * 16);
    }
    else if (name == "PartDesign_Draft") {
        painter.setPen(outline(blueDark, 1.5));
        painter.setBrush(QColor(80, 170, 211, 120));
        painter.drawPolygon(QPolygonF() << QPointF(8, 26) << QPointF(12, 7)
                                       << QPointF(23, 10) << QPointF(26, 26));
        drawArrow(painter, QPointF(23, 18), QPointF(28, 14), orange);
    }
    else if (name == "PartDesign_LinearPattern") {
        for (int i = 0; i < 3; ++i) {
            painter.setPen(outline(blueDark, 1.0));
            painter.setBrush(i == 0 ? orange : blueLight);
            painter.drawRoundedRect(QRectF(4 + i * 9, 11, 7, 9), 1.2, 1.2);
        }
        drawArrow(painter, QPointF(5, 25), QPointF(27, 25), blueDark, 1.5);
    }
    else if (name == "PartDesign_PolarPattern") {
        painter.setPen(outline(blueDark, 1.0));
        painter.setBrush(blueLight);
        painter.drawEllipse(QPointF(16, 16), 3, 3);
        for (int i = 0; i < 4; ++i) {
            const qreal a = i * 1.57079632679;
            painter.save();
            painter.translate(16 + 10 * std::cos(a), 16 + 10 * std::sin(a));
            painter.rotate(i * 90.0);
            painter.setBrush(i == 0 ? orange : blueLight);
            painter.drawRoundedRect(QRectF(-3, -3, 6, 6), 1, 1);
            painter.restore();
        }
        drawCircularArrow(painter, QRectF(5, 5, 22, 22), blueDark);
    }
    else if (name == "PartDesign_Mirrored" || name == "Sketcher_Symmetry") {
        painter.setPen(QPen(purple, 1.2, Qt::DashLine));
        painter.drawLine(QPointF(16, 4), QPointF(16, 28));
        painter.setPen(outline(blueDark, 1.3));
        painter.setBrush(blueLight);
        painter.drawPolygon(QPolygonF() << QPointF(5, 24) << QPointF(12, 8) << QPointF(13, 24));
        painter.setBrush(QColor(purple.red(), purple.green(), purple.blue(), 90));
        painter.drawPolygon(QPolygonF() << QPointF(27, 24) << QPointF(20, 8) << QPointF(19, 24));
    }
    else if (name == "PartDesign_Plane") {
        painter.setPen(outline(blueDark, 1.3));
        painter.setBrush(QColor(92, 187, 224, 95));
        painter.drawPolygon(QPolygonF() << QPointF(5, 21) << QPointF(12, 7)
                                       << QPointF(27, 11) << QPointF(20, 25));
        painter.setPen(QPen(orange, 1.2, Qt::DashLine));
        painter.drawLine(QPointF(16, 4), QPointF(16, 28));
    }
    else if (name == "PartDesign_Line") {
        painter.setPen(outline(orange, 2.2));
        painter.drawLine(QPointF(7, 25), QPointF(25, 7));
        painter.setBrush(blueDark);
        painter.setPen(Qt::NoPen);
        painter.drawEllipse(QPointF(7, 25), 2.1, 2.1);
        painter.drawEllipse(QPointF(25, 7), 2.1, 2.1);
    }
    else if (name == "PartDesign_Point") {
        painter.setPen(outline(blueDark, 1.5));
        painter.drawLine(QPointF(6, 16), QPointF(26, 16));
        painter.drawLine(QPointF(16, 6), QPointF(16, 26));
        painter.setPen(outline(orange, 2));
        painter.setBrush(yellow);
        painter.drawEllipse(QPointF(16, 16), 4, 4);
    }
    else if (name == "Sketcher_LeaveSketch") {
        painter.setPen(outline(green, 2.0));
        painter.setBrush(QColor(222, 247, 235));
        painter.drawRoundedRect(QRectF(5, 5, 22, 22), 3, 3);
        painter.drawPolyline(QPolygonF() << QPointF(9, 16) << QPointF(14, 21) << QPointF(24, 10));
    }
    else if (name == "Sketcher_CompDimensionTools") {
        drawSketchFrame(painter);
        drawDimension(painter);
    }
    else if (name == "Sketcher_CompLine") {
        drawSketchFrame(painter);
        painter.setPen(outline(blueDark, 2.2));
        painter.drawLine(QPointF(8, 23), QPointF(24, 9));
        painter.setBrush(red);
        painter.setPen(Qt::NoPen);
        painter.drawEllipse(QPointF(8, 23), 2, 2);
        painter.drawEllipse(QPointF(24, 9), 2, 2);
    }
    else if (name == "Sketcher_CompCreateRectangles") {
        drawSketchFrame(painter);
        painter.setPen(outline(blueDark, 2.0));
        painter.setBrush(QColor(73, 170, 215, 35));
        painter.drawRect(QRectF(8, 10, 16, 13));
        painter.setBrush(red);
        painter.setPen(Qt::NoPen);
        painter.drawEllipse(QPointF(8, 10), 1.5, 1.5);
        painter.drawEllipse(QPointF(24, 23), 1.5, 1.5);
    }
    else if (name == "Sketcher_CompCreateArc") {
        drawSketchFrame(painter);
        painter.setPen(outline(blueDark, 2.0));
        painter.setBrush(Qt::NoBrush);
        painter.drawEllipse(QRectF(8, 8, 16, 16));
        painter.setPen(outline(orange, 2.4));
        painter.drawArc(QRectF(8, 8, 16, 16), 20 * 16, 120 * 16);
    }
    else if (name == "Sketcher_CompCreateConic") {
        drawSketchFrame(painter);
        painter.setPen(outline(blueDark, 2.0));
        painter.setBrush(QColor(73, 170, 215, 28));
        painter.drawEllipse(QRectF(7, 11, 18, 11));
        painter.setPen(QPen(red, 1, Qt::DashLine));
        painter.drawLine(QPointF(7, 16.5), QPointF(25, 16.5));
    }
    else if (name == "Sketcher_CompSlot") {
        drawSketchFrame(painter);
        QPainterPath slot;
        slot.addRoundedRect(QRectF(7, 11, 18, 11), 5.5, 5.5);
        painter.setPen(outline(blueDark, 2.0));
        painter.setBrush(QColor(73, 170, 215, 30));
        painter.drawPath(slot);
    }
    else if (name == "Sketcher_CompCreateBSpline") {
        drawSketchFrame(painter);
        painter.setPen(outline(blueDark, 2.0));
        QPainterPath curve;
        curve.moveTo(7, 22);
        curve.cubicTo(10, 6, 19, 26, 26, 9);
        painter.drawPath(curve);
        painter.setBrush(red);
        painter.setPen(Qt::NoPen);
        for (const QPointF& point : {QPointF(7,22), QPointF(12,10), QPointF(20,22), QPointF(26,9)})
            painter.drawEllipse(point, 1.6, 1.6);
    }
    else if (name == "Sketcher_CompCurveEdition") {
        drawSketchFrame(painter);
        painter.setPen(outline(blueDark, 2.0));
        painter.drawLine(QPointF(6, 22), QPointF(26, 10));
        painter.setPen(outline(red, 1.5));
        painter.drawLine(QPointF(14, 10), QPointF(20, 21));
        painter.drawLine(QPointF(20, 10), QPointF(14, 21));
    }
    else if (name == "Sketcher_CompExternal") {
        drawSketchFrame(painter);
        painter.setPen(QPen(purple, 1.7, Qt::DashLine));
        painter.drawRect(QRectF(7, 9, 17, 14));
        drawArrow(painter, QPointF(8, 26), QPointF(14, 21), purple, 1.4);
    }
    else if (name == "Sketcher_Offset") {
        drawSketchFrame(painter);
        painter.setPen(outline(blueDark, 1.8));
        painter.drawRoundedRect(QRectF(8, 10, 16, 13), 2, 2);
        painter.setPen(outline(orange, 1.5));
        painter.drawRoundedRect(QRectF(11, 13, 10, 7), 1.5, 1.5);
    }
    else if (name == "Sketcher_Translate") {
        drawSketchFrame(painter);
        painter.setPen(outline(blueDark, 1.5));
        painter.setBrush(blueLight);
        painter.drawRect(QRectF(7, 13, 7, 7));
        painter.drawRect(QRectF(20, 9, 7, 7));
        drawArrow(painter, QPointF(13, 19), QPointF(21, 13), orange, 1.6);
    }
    else if (name == "Sketcher_Rotate") {
        drawSketchFrame(painter);
        painter.setPen(outline(blueDark, 1.5));
        painter.setBrush(blueLight);
        painter.drawRect(QRectF(7, 14, 7, 7));
        drawCircularArrow(painter, QRectF(11, 7, 16, 16), orange);
    }
    else if (name == "Sketcher_ValidateSketch") {
        drawSketchFrame(painter);
        painter.setPen(outline(green, 2.2));
        painter.drawPolyline(QPolygonF() << QPointF(9, 17) << QPointF(14, 22) << QPointF(24, 10));
    }
    else if (name == "Sketcher_SelectConstraints" ||
             name == "Sketcher_SelectElementsAssociatedWithConstraints") {
        drawSketchFrame(painter);
        painter.setPen(outline(blueDark, 1.6));
        painter.drawLine(QPointF(7, 22), QPointF(25, 10));
        painter.setPen(outline(red, 1.7));
        painter.drawEllipse(QPointF(10, 20), 3, 3);
        painter.drawEllipse(QPointF(22, 12), 3, 3);
        painter.drawLine(QPointF(12, 18), QPointF(20, 14));
    }
    else if (name == "Sketcher_ConstrainCoincidentUnified") {
        drawSketchFrame(painter);
        painter.setPen(outline(blueDark, 1.8));
        painter.drawLine(QPointF(7, 22), QPointF(16, 16));
        painter.drawLine(QPointF(25, 9), QPointF(16, 16));
        painter.setBrush(red);
        painter.setPen(Qt::NoPen);
        painter.drawEllipse(QPointF(16, 16), 3, 3);
    }
    else if (name == "Sketcher_CompHorVer") {
        drawSketchFrame(painter);
        painter.setPen(outline(blueDark, 2.0));
        painter.drawLine(QPointF(7, 11), QPointF(25, 11));
        painter.drawLine(QPointF(10, 7), QPointF(10, 25));
        painter.setPen(outline(red, 1.5));
        painter.drawText(QRectF(16, 15, 10, 9), Qt::AlignCenter, QStringLiteral("HV"));
    }
    else if (name == "Sketcher_ToggleConstruction") {
        drawSketchFrame(painter);
        painter.setPen(QPen(blueDark, 2.0, Qt::DashLine, Qt::RoundCap));
        painter.drawLine(QPointF(7, 24), QPointF(25, 8));
        painter.setPen(outline(orange, 1.2));
        painter.drawLine(QPointF(7, 27), QPointF(25, 11));
    }
    else if (name == "Sketcher_ViewSection") {
        drawSketchFrame(painter);
        painter.setPen(outline(blueDark, 1.8));
        painter.setBrush(QColor(142, 149, 184, 95));
        painter.drawRect(QRectF(8, 10, 16, 13));
        painter.setPen(QPen(QColor(80, 86, 112), 0.8, Qt::DashLine));
        painter.drawLine(QPointF(8, 10), QPointF(24, 23));
        painter.drawLine(QPointF(24, 10), QPointF(8, 23));
    }
}

QStringList customCommands()
{
    return {
        "PartDesign_Pad", "PartDesign_Pocket", "PartDesign_Hole",
        "PartDesign_Revolution", "PartDesign_Groove", "PartDesign_AdditivePipe",
        "PartDesign_SubtractivePipe", "PartDesign_AdditiveLoft", "PartDesign_Fillet",
        "PartDesign_Chamfer", "PartDesign_Thickness", "PartDesign_Draft",
        "PartDesign_LinearPattern", "PartDesign_PolarPattern", "PartDesign_Mirrored",
        "PartDesign_Plane", "PartDesign_Line", "PartDesign_Point",
        "Sketcher_LeaveSketch", "Sketcher_CompDimensionTools", "Sketcher_CompLine",
        "Sketcher_CompCreateRectangles", "Sketcher_CompCreateArc",
        "Sketcher_CompCreateConic", "Sketcher_CompSlot", "Sketcher_CompCreateBSpline",
        "Sketcher_CompCurveEdition", "Sketcher_CompExternal", "Sketcher_Offset",
        "Sketcher_Symmetry", "Sketcher_Translate", "Sketcher_Rotate",
        "Sketcher_ValidateSketch", "Sketcher_SelectConstraints",
        "Sketcher_SelectElementsAssociatedWithConstraints",
        "Sketcher_ConstrainCoincidentUnified", "Sketcher_CompHorVer",
        "Sketcher_ToggleConstruction", "Sketcher_ViewSection"
    };
}
}  // namespace

namespace SolidFreeCAD
{

bool hasCustomCommandIcon(const QString& commandName)
{
    return customCommands().contains(commandName);
}

QIcon customCommandIcon(const QString& commandName, const QSize& logicalSize)
{
    if (!hasCustomCommandIcon(commandName) || !logicalSize.isValid()) {
        return {};
    }

    const QSize size(qMax(16, logicalSize.width()), qMax(16, logicalSize.height()));
    QPixmap pixmap(size);
    pixmap.fill(Qt::transparent);

    QPainter painter(&pixmap);
    painter.setRenderHint(QPainter::Antialiasing, true);
    const qreal scaleX = size.width() / 32.0;
    const qreal scaleY = size.height() / 32.0;
    painter.scale(scaleX, scaleY);
    drawIcon(painter, commandName);
    painter.end();

    return QIcon(pixmap);
}

}  // namespace SolidFreeCAD
