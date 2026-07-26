"""Static validation for the SolidFreeCAD Classic v3 SVG pack."""
from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MODULE_ROOT = REPOSITORY_ROOT / "overlay" / "Mod"
sys.path.insert(0, str(MODULE_ROOT))

from SolidFreeCAD.ClassicIcons import ensure_icon_pack  # noqa: E402

icon_root = Path(ensure_icon_pack())
icons = sorted(icon_root.rglob("*.svg"))
if len(icons) != 75:
    raise SystemExit(f"Expected 75 classic SVG icons, found {len(icons)}")

required = {
    "archivo/nuevo.svg",
    "croquis/nuevo_croquis.svg",
    "cotas_relaciones/cota_inteligente.svg",
    "operaciones/saliente_base.svg",
    "operaciones/corte_extruir.svg",
    "operaciones/revolucion.svg",
    "superficies/superficie_extruida.svg",
    "vistas/isometrica.svg",
    "propertymanager/aceptar.svg",
    "propertymanager/cancelar.svg",
    "eje_parametrico/crear_eje.svg",
}
relative = {path.relative_to(icon_root).as_posix() for path in icons}
missing = sorted(required - relative)
if missing:
    raise SystemExit(f"Required classic icons are missing: {missing}")

for path in icons:
    root = ET.parse(path).getroot()
    if root.attrib.get("viewBox") != "0 0 24 24":
        raise SystemExit(f"Invalid classic icon viewBox: {path}")
    if any(str(node.tag).endswith("image") for node in root.iter()):
        raise SystemExit(f"Raster content embedded in SVG: {path}")
    text = path.read_text(encoding="utf-8")
    if 'stroke-width=".72"' not in text:
        raise SystemExit(f"Classic thin-stroke rule is missing: {path}")

print(f"Validated {len(icons)} SolidFreeCAD Classic v3 SVG icons")
