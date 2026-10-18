"""SolidFreeCAD standalone shell package."""


def show_standalone():
    from .window_alpha12 import show_standalone as show
    return show()


__all__ = ["show_standalone"]
