"""Runtime compatibility fixes for the alpha.7 interface prototype.

Kept separate while the visual prototype is iterated so the alpha.6 base remains
untouched.  The module patches only document activation and state refresh, then
re-exports the regular workspace entry points.
"""
from __future__ import annotations

import FreeCAD as App
import FreeCADGui as Gui

from SolidFreeCAD import ProfessionalWorkspace as _workspace


def _safe_refresh(self):
    names = list(App.listDocuments().keys())
    current_name = App.ActiveDocument.Name if App.ActiveDocument else ""
    previous = self.documents.blockSignals(True)
    self.documents.clear()
    self.documents.addItem("—")
    for name in names:
        doc = App.getDocument(name)
        self.documents.addItem(doc.Label or name, name)
    index = self.documents.findData(current_name)
    self.documents.setCurrentIndex(index if index >= 0 else 0)
    self.documents.blockSignals(previous)

    doc = App.ActiveDocument
    obj = _workspace._selected_object()
    if doc is None:
        self.breadcrumb.setText("Inicio  ›  Sin documento")
        self.state.setText("Sin documento")
        self.state.setProperty("state", "idle")
    elif obj is None:
        self.breadcrumb.setText(f"{doc.Label or doc.Name}  ›  Modelo")
        frozen = bool(getattr(doc, "RecomputesFrozen", False))
        self.state.setText("Recomputación pausada" if frozen else "Modelo actualizado")
        self.state.setProperty("state", "warning" if frozen else "ok")
    else:
        self.breadcrumb.setText(f"{doc.Label or doc.Name}  ›  {obj.Label or obj.Name}")
        shape_state = _workspace._shape_state(obj)
        self.state.setText(shape_state)
        self.state.setProperty("state", "warning" if "errores" in shape_state else "ok")
    self.state.style().unpolish(self.state)
    self.state.style().polish(self.state)


def _safe_activate_document(self, index):
    name = self.documents.itemData(index)
    if not name:
        return
    try:
        App.setActiveDocument(name)
        gui_document = Gui.activeDocument()
        if gui_document is not None:
            gui_document.activeView().fitAll()
        self.refresh()
    except Exception as exc:
        App.Console.PrintWarning(f"SolidFreeCAD: no se pudo activar {name}: {exc}\n")


_workspace.ContextController.refresh = _safe_refresh
_workspace.ContextController.activate_document = _safe_activate_document

show_workspace = _workspace.show_workspace
hide_workspace = _workspace.hide_workspace
