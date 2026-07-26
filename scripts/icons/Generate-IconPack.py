"""Generate the original core SVG icon set used by SolidFreeCAD alpha.4."""
from __future__ import annotations

import argparse
import html
import json
import zipfile
from pathlib import Path

P = {
    "o": "#384653", "b": "#2678D8", "b2": "#70B7F4", "c": "#25AFC4",
    "l": "#E4EFF7", "m": "#B8CFDF", "s": "#7993A5", "v": "#7759C5",
    "a": "#E89A2D", "r": "#D95050", "w": "#FFFFFF",
}


def svg(title: str, body: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'role="img" aria-label="{html.escape(title)}"><title>{html.escape(title)}</title>'
        f'<g stroke="{P["o"]}" stroke-width="1.35" stroke-linecap="round" '
        f'stroke-linejoin="round">{body}</g></svg>'
    )


def cube(front: str | None = None) -> str:
    front = front or P["m"]
    return (
        f'<path d="M4 10L9 7l8 3-5 3Z" fill="{P["l"]}"/>'
        f'<path d="M4 10l8 3v7l-8-3Z" fill="{front}"/>'
        f'<path d="M12 13l5-3v7l-5 3Z" fill="{P["s"]}"/>'
    )


def arrow(path: str, head: str, color: str | None = None) -> str:
    color = color or P["b"]
    return f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.8"/><path d="{head}" fill="{color}" stroke="{color}"/>'


def definitions() -> dict[str, tuple[str, str]]:
    plane = f'<path d="M4 6l14-2 2 13-14 3Z" fill="{P["v"]}" fill-opacity=".16" stroke="{P["v"]}"/>'
    shaft = (
        f'<path d="M3 10h4V8h5v2h6v4h-6v2H7v-2H3Z" fill="{P["m"]}"/>'
        f'<ellipse cx="3" cy="12" rx="1.5" ry="2" fill="{P["l"]}"/>'
        f'<ellipse cx="18" cy="12" rx="1.5" ry="2" fill="{P["s"]}"/>'
        f'<path d="M8 8h3v2H8Z" fill="{P["b"]}" stroke="{P["b"]}"/>'
    )
    return {
        "file/file_new.svg": ("Nueva pieza", f'<path d="M6 3.5h7l4 4V20H6Z" fill="{P["l"]}"/><path d="M13 3.5v4h4" fill="none"/><path d="M9 14h6M12 11v6" stroke="{P["b"]}" stroke-width="1.8"/>'),
        "file/file_open.svg": ("Abrir", f'<path d="M3.5 7h6l1.5 2h9.5l-2.2 9H5.3Z" fill="{P["m"]}"/><path d="M5 7V5h6l1.5 2" fill="{P["l"]}"/>'+arrow("M15 5l2 2", "M19 9l-3-.7 2-2Z")),
        "file/file_save.svg": ("Guardar", f'<path d="M5 3.5h13v17H5Z" fill="{P["l"]}"/><path d="M8 3.5v5h7v-5M8 14h7v6H8Z" fill="{P["m"]}"/><path d="M10 16h3" stroke="{P["b"]}" stroke-width="1.8"/>'),
        "sketch/sketch_new.svg": ("Nuevo croquis", plane+f'<path d="M8 15l2-6 6 5Z" fill="none" stroke="{P["v"]}" stroke-width="1.8"/><circle cx="8" cy="15" r=".8" fill="{P["b"]}"/><circle cx="10" cy="9" r=".8" fill="{P["b"]}"/>'),
        "feature/feature_pad.svg": ("Extruir saliente", cube(P["b2"])+f'<path d="M8 10l4-2 4 2-4 2Z" fill="{P["b"]}" stroke="{P["b"]}"/>'+arrow("M12 8V5", "M12 3.5l-1.5 3h3Z")),
        "feature/feature_pocket.svg": ("Corte por extrusión", cube()+f'<path d="M8 10l4-2 4 2-4 2Z" fill="{P["b2"]}"/><path d="M9 11v4l3 1.4 3-1.4v-4" fill="{P["s"]}"/>'+arrow("M12 4v4", "M12 10l-1.5-3h3Z")),
        "feature/feature_revolve.svg": ("Revolución", f'<path d="M8 17V7h3l3 3v7Z" fill="{P["m"]}"/><path d="M7 5v14" stroke-dasharray="2 1"/><path d="M7 8c7-3 11 1 10 6" fill="none" stroke="{P["c"]}" stroke-width="2"/><path d="M17 14l-2.5-1 1-2.5" fill="{P["c"]}" stroke="{P["c"]}"/>'),
        "feature/feature_fillet.svg": ("Redondeo", cube()+f'<path d="M12 13c3 0 5-2 5-5" fill="none" stroke="{P["b"]}" stroke-width="2.4"/>'),
        "feature/feature_chamfer.svg": ("Chaflán", cube()+f'<path d="M12 13l5-5v5l-2.5 2.5Z" fill="{P["b"]}"/>'),
        "view/view_fit.svg": ("Ajustar a pantalla", cube()+f'<path d="M3 8V3h5M16 3h5v5M21 16v5h-5M8 21H3v-5" fill="none" stroke="{P["b"]}" stroke-width="1.8"/>'),
        "shaft/shaft_create.svg": ("Crear eje paramétrico", shaft+f'<circle cx="19" cy="18" r="3.2" fill="{P["b"]}" stroke="white"/><path d="M17.5 18h3M19 16.5v3" stroke="white" stroke-width="1.6"/>'),
        "shaft/shaft_edit.svg": ("Editar eje", shaft+f'<path d="M15 19l1-3 4-4 2 2-4 4Z" fill="{P["a"]}"/>'),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="build/SolidFreeCAD_IconPack_Core_v1")
    parser.add_argument("--zip-path", default="")
    args = parser.parse_args()
    root = Path(args.output_root).resolve()
    icons_root = root / "icons"
    items = definitions()
    for relative, (title, body) in items.items():
        path = icons_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg(title, body), encoding="utf-8")
    manifest = {"name": "SFC Mechanical Icon System Core", "version": "1.0.0", "grid": "24x24", "count": len(items), "icons": sorted(items)}
    root.mkdir(parents=True, exist_ok=True)
    (root / "icon-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (root / "README.md").write_text("# SolidFreeCAD core icons\n\nOriginal SVG artwork for SolidFreeCAD.\n", encoding="utf-8")
    zip_path = Path(args.zip_path).resolve() if args.zip_path else root.with_suffix(".zip")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in root.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(root.parent))
    print(f"Generated {len(items)} SVG icons at {root}")
    print(f"Package: {zip_path}")


if __name__ == "__main__":
    main()
