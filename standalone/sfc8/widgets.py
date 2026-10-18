"""A compact CommandManager using the same actions as menus and search."""
from .qt import QtCore, QtWidgets


class CommandButton(QtWidgets.QToolButton):
    def __init__(self, action, large=False, parent=None):
        super().__init__(parent)
        self.setDefaultAction(action)
        self.setAutoRaise(True)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon if large else QtCore.Qt.ToolButtonTextBesideIcon)
        self.setIconSize(QtCore.QSize(30, 30) if large else QtCore.QSize(18, 18))
        self.setMinimumHeight(66 if large else 29)
        self.setMinimumWidth(72 if large else 94)


class Ribbon(QtWidgets.QTabWidget):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setObjectName("SFC12Ribbon")
        self.setDocumentMode(True)
        self.setTabPosition(QtWidgets.QTabWidget.South)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.addTab(self._page([
            ("Crear", [("sketch", True), ("pad", True), ("revolution", True)]),
            ("Quitar material", [("pocket", True)]),
            ("Acabados", [("fillet", True), ("chamfer", True)]),
            ("Editar", [("edit", False), ("visibility", False)]),
            ("Archivo", [("export", False), ("save_as", False)]),
        ]), "Operaciones")
        self.addTab(self._page([
            ("Entidades", [("line", True), ("rectangle", True), ("circle", True)]),
            ("Por medidas", [("rectangle_numeric", False), ("circle_numeric", False)]),
            ("Relaciones", [("dimension", True)]),
            ("Croquis", [("accept", True), ("cancel", False)]),
        ]), "Croquis")
        self.addTab(self._page([
            ("Inspección", [("measure", True), ("validate", True)]),
            ("Intercambio", [("open", True), ("export", True)]),
        ]), "Evaluar")
        self.addTab(self._page([
            ("Orientación", [("iso", True), ("front", True), ("top", True), ("right", True)]),
            ("Visualización", [("fit", True), ("shaded", False), ("wireframe", False)]),
        ]), "Vista")

    def _page(self, groups):
        scroll = QtWidgets.QScrollArea()
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        page = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(page)
        row.setContentsMargins(4, 2, 4, 2)
        row.setSpacing(3)
        for title, commands in groups:
            frame = QtWidgets.QFrame()
            frame.setObjectName("RibbonGroup")
            group = QtWidgets.QVBoxLayout(frame)
            group.setContentsMargins(5, 0, 8, 0)
            group.setSpacing(0)
            grid = QtWidgets.QGridLayout()
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setSpacing(1)
            column, small_row = 0, 0
            for key, large in commands:
                button = CommandButton(self.owner.actions[key], large, frame)
                if large:
                    if small_row:
                        column, small_row = column + 1, 0
                    grid.addWidget(button, 0, column, 2, 1)
                    column += 1
                else:
                    grid.addWidget(button, small_row, column)
                    small_row += 1
                    if small_row == 2:
                        column, small_row = column + 1, 0
            group.addLayout(grid)
            caption = QtWidgets.QLabel(title)
            caption.setObjectName("GroupCaption")
            caption.setAlignment(QtCore.Qt.AlignCenter)
            group.addWidget(caption)
            row.addWidget(frame)
        row.addStretch(1)
        scroll.setWidget(page)
        return scroll
