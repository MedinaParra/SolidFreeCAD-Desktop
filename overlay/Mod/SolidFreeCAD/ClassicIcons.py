"""Generate the original SolidFreeCAD Classic v3 SVG icon pack on demand."""
from __future__ import annotations

import os

_MODULE_DIR = os.path.dirname(__file__)
_TARGET_ROOT = os.path.join(_MODULE_DIR, "Resources", "icons", "classic")

_PATHS = """
croquis/poligono.svg
croquis/spline.svg
croquis/linea.svg
croquis/ranura.svg
croquis/simetria.svg
croquis/elipse.svg
croquis/circulo.svg
croquis/rectangulo.svg
croquis/convertir_entidades.svg
croquis/arco.svg
croquis/recortar.svg
croquis/nuevo_croquis.svg
croquis/equidistanciar.svg
superficies/superficie_extruida.svg
superficies/superficie_revolucion.svg
superficies/coser_superficies.svg
superficies/equidistanciar_superficie.svg
superficies/recortar_superficie.svg
referencias/plano_medio.svg
referencias/eje.svg
referencias/punto.svg
referencias/sistema_coordenadas.svg
referencias/plano.svg
vistas/posterior.svg
vistas/ajustar.svg
vistas/superior.svg
vistas/frontal.svg
vistas/ocultar_mostrar.svg
vistas/izquierda.svg
vistas/seccion.svg
vistas/derecha.svg
vistas/inferior.svg
vistas/isometrica.svg
vistas/zoom.svg
eje_parametrico/configurar_eje.svg
eje_parametrico/quitar_chavetero.svg
eje_parametrico/crear_eje.svg
eje_parametrico/agregar_chavetero.svg
eje_parametrico/editar_eje.svg
operaciones/revolucion.svg
operaciones/chaflan.svg
operaciones/rosca.svg
operaciones/nervio.svg
operaciones/patron_circular.svg
operaciones/barrido.svg
operaciones/simetria.svg
operaciones/loft.svg
operaciones/redondeo.svg
operaciones/cascaron.svg
operaciones/agujero.svg
operaciones/corte_extruir.svg
operaciones/patron_lineal.svg
operaciones/corte_revolucion.svg
operaciones/saliente_base.svg
cotas_relaciones/perpendicular.svg
cotas_relaciones/coincidente.svg
cotas_relaciones/cota_inteligente.svg
cotas_relaciones/vertical.svg
cotas_relaciones/horizontal.svg
cotas_relaciones/paralelo.svg
cotas_relaciones/tangente.svg
cotas_relaciones/igual.svg
cotas_relaciones/concentrico.svg
propertymanager/editar_croquis.svg
propertymanager/mensaje.svg
propertymanager/ayuda.svg
propertymanager/aceptar.svg
propertymanager/cancelar.svg
archivo/exportar.svg
archivo/abrir.svg
archivo/guardar_como.svg
archivo/guardar.svg
archivo/nuevo.svg
archivo/importar.svg
archivo/cerrar.svg
""".strip().splitlines()

_DEFS = """
<defs>
 <linearGradient id="gBlue" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".45" stop-color="#b9ddee"/><stop offset="1" stop-color="#6cc4e3"/></linearGradient>
 <linearGradient id="gGrey" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#d9dee2"/></linearGradient>
 <linearGradient id="gDark" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d9dee2"/><stop offset="1" stop-color="#aeb8bf"/></linearGradient>
</defs>
"""


def _wrap(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" role="img" aria-label="{title}">
<title>{title}</title>{_DEFS}<g fill="none" stroke="#263846" stroke-width=".72" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>'''


def _box() -> str:
    return '<path d="M4 10l5-2.5 9 3-5 2.5Z" fill="url(#gGrey)"/><path d="M4 10l9 3v7l-9-3Z" fill="url(#gBlue)"/><path d="M13 13l5-2.5v7L13 20Z" fill="url(#gDark)"/>'


def _doc() -> str:
    return '<path d="M6 3.5h8l4 4V20.5H6Z" fill="url(#gGrey)"/><path d="M14 3.5v4h4"/>'


def _shaft() -> str:
    return '<path d="M3 10h4V8h5v2h6v4h-6v2H7v-2H3Z" fill="url(#gGrey)"/><ellipse cx="3" cy="12" rx="1.5" ry="2" fill="#f4f6f7"/><ellipse cx="18" cy="12" rx="1.5" ry="2" fill="#aeb8bf"/><path d="M8 8h3v2H8Z" fill="#b9ddee"/>'


def _shape(relative: str) -> str:
    category, filename = relative.split("/", 1)
    name = filename[:-4]
    blue = '#1773ae'
    red = '#d8423a'
    green = '#4eae5b'

    if category == 'archivo':
        if name == 'abrir':
            return '<path d="M3.5 8h7l1.5 2h8.5L18 19H5Z" fill="#f4d349"/><path d="M5 8V6h6l1.5 2" fill="url(#gGrey)"/>'
        if name == 'guardar':
            return '<path d="M5 3.5h13l2 2V20.5H5Z" fill="url(#gBlue)"/><path d="M8 3.5h8v5H8Z" fill="#fff"/><path d="M8 13h9v7.5H8Z" fill="url(#gGrey)"/>'
        if name == 'guardar_como':
            return _doc() + '<path d="M10 18l1-3 6-6 2 2-6 6Z" fill="#f4d349"/>'
        if name in ('importar', 'exportar'):
            direction = 'M8 14h8l-2-2m2 2-2 2' if name == 'importar' else 'M9 14h8l-2-2m2 2-2 2'
            return _doc() + f'<path d="{direction}" stroke="{blue}" stroke-width="1.1"/>'
        if name == 'cerrar':
            return _doc() + f'<path d="M14 14l6 6m0-6-6 6" stroke="{red}" stroke-width="1.5"/>'
        return _doc()

    if category == 'croquis':
        if name == 'linea':
            return f'<path d="M5 18L18 5" stroke="{blue}" stroke-width=".9"/><circle cx="5" cy="18" r=".9" fill="#2e8cc8"/><circle cx="18" cy="5" r=".9" fill="#2e8cc8"/>'
        if name == 'rectangulo':
            return f'<rect x="5" y="6" width="14" height="12" fill="#fff" stroke="{blue}" stroke-width=".85"/>'
        if name == 'circulo':
            return f'<circle cx="12" cy="12" r="7" fill="#fff" stroke="{blue}" stroke-width=".85"/><circle cx="12" cy="12" r=".8" fill="#2e8cc8"/>'
        if name == 'arco':
            return f'<path d="M5 17A8.5 8.5 0 0 1 18 6" stroke="{blue}" stroke-width=".9"/>'
        if name == 'ranura':
            return f'<rect x="4" y="8" width="16" height="8" rx="4" fill="#fff" stroke="{blue}" stroke-width=".85"/>'
        if name == 'elipse':
            return f'<ellipse cx="12" cy="12" rx="8" ry="5" transform="rotate(-25 12 12)" fill="#fff" stroke="{blue}" stroke-width=".85"/>'
        if name == 'poligono':
            return f'<path d="M12 4l6 3v7l-6 5-6-5V7Z" fill="#fff" stroke="{blue}" stroke-width=".8"/>'
        if name == 'spline':
            return f'<path d="M4 17C7 5 12 18 20 6" stroke="{blue}" stroke-width="1"/><circle cx="4" cy="17" r=".65" fill="#2e8cc8"/><circle cx="20" cy="6" r=".65" fill="#2e8cc8"/>'
        if name == 'recortar':
            return f'<path d="M4 18L18 4M6 5l13 13" stroke="{blue}"/><path d="M8 8l8 8m0-8-8 8" stroke="#263846"/>'
        if name == 'simetria':
            return f'<path d="M12 3v18" stroke-dasharray="2 1"/><path d="M11 12H5m8 0h6" stroke="{blue}"/>'
        if name in ('equidistanciar', 'convertir_entidades'):
            return f'<path d="M5 18A9 9 0 0 1 18 5M8 20A12 12 0 0 1 21 8" stroke="{blue}"/>'
        return '<rect x="4" y="4" width="16" height="16" fill="url(#gGrey)"/><path d="M7 16l2-7h8v7Z" fill="#b9ddee" stroke="#1773ae"/>'

    if category == 'cotas_relaciones':
        if name == 'cota_inteligente':
            return f'<path d="M5 6v12m14-12v12M7 12h10"/><path d="M7 12l2-1v2Zm10 0-2-1v2Z" fill="{blue}" stroke="{blue}"/>'
        if name == 'horizontal': return f'<path d="M5 12h14" stroke="{blue}" stroke-width="1.1"/>'
        if name == 'vertical': return f'<path d="M12 5v14" stroke="{blue}" stroke-width="1.1"/>'
        if name == 'concentrico': return f'<circle cx="12" cy="12" r="7" stroke="{blue}"/><circle cx="12" cy="12" r="3.5" stroke="{blue}"/>'
        if name == 'perpendicular': return f'<path d="M5 18h14M12 5v13" stroke="{blue}"/><path d="M12 15h3v3" stroke="{green}"/>'
        if name == 'paralelo': return f'<path d="M6 17l6-10m0 12 6-10" stroke="{blue}"/>'
        if name == 'tangente': return f'<circle cx="9" cy="14" r="5" stroke="{blue}"/><path d="M4 7l15 9" stroke="{blue}"/><circle cx="12" cy="12" r=".9" fill="{green}"/>'
        if name == 'igual': return f'<path d="M5 8h5m4 0h5M5 16h5m4 0h5" stroke="{blue}"/><path d="M11 10h2m-2 4h2" stroke="{green}"/>'
        return f'<path d="M5 18L12 11l7-6" stroke="{blue}"/><circle cx="12" cy="11" r="1.4" fill="{green}"/>'

    if category == 'operaciones':
        base = _box()
        if name == 'saliente_base': return base + f'<path d="M8 10l4-2 4 2-4 2Z" fill="#b9ddee"/><path d="M12 8V4" stroke="{blue}"/>'
        if name == 'corte_extruir': return base + f'<path d="M8 10l4-2 4 2-4 2Z" fill="#fff"/><path d="M9 11v4l3 1.5 3-1.5v-4" fill="#7b878f" opacity=".5"/><path d="M12 5v5" stroke="{blue}"/>'
        if name in ('revolucion','corte_revolucion'):
            fill = 'url(#gBlue)' if name == 'revolucion' else 'url(#gGrey)'
            return f'<path d="M8 18V8h4l4 4v6Z" fill="{fill}"/><path d="M7 5v14" stroke-dasharray="2 1"/><path d="M7 8c7-3 11 1 10 6" stroke="{blue}"/>'
        if name == 'agujero': return base + '<ellipse cx="12" cy="11" rx="2.6" ry="1.3" fill="#b9ddee"/><ellipse cx="12" cy="11" rx="1.2" ry=".6" fill="#7b878f"/>'
        if name == 'redondeo': return base + f'<path d="M12 14q5 0 5-5" stroke="{blue}" stroke-width="1.1"/>'
        if name == 'chaflan': return base + f'<path d="M12 14l5-5v5l-3 3Z" fill="#b9ddee"/><path d="M12 14l5-5" stroke="{blue}"/>'
        if name == 'cascaron': return '<path d="M5 8l7-3 7 3-7 3Z" fill="url(#gGrey)"/><path d="M5 8v10l7 3V11Z" fill="url(#gBlue)"/><path d="M12 11l7-3v10l-7 3Z" fill="url(#gDark)"/><path d="M8 9l4-2 4 2-4 2Z" fill="#fff"/>'
        if name == 'rosca': return '<rect x="7" y="7" width="10" height="10" fill="url(#gGrey)"/><path d="M8 8l8 7m-8-4 6 5m-4-9 8 7" stroke="#1773ae"/>'
        if name in ('patron_lineal','patron_circular','simetria'): return base + f'<circle cx="5" cy="5" r="1.2" fill="{blue}"/><circle cx="19" cy="5" r="1.2" fill="{blue}"/><circle cx="19" cy="19" r="1.2" fill="{blue}"/>'
        if name in ('barrido','loft'): return f'<path d="M5 18C10 18 10 8 18 7" stroke="#5e6d77" stroke-dasharray="2 1"/><path d="M6 16c5-1 5-8 12-10v3c-5 0-6 8-10 9Z" fill="url(#gBlue)"/>'
        return base

    if category == 'superficies':
        if name == 'recortar_superficie': return f'<path d="M5 18Q12 4 19 18" fill="#b9ddee" fill-opacity=".4" stroke="{blue}"/><path d="M7 8l10 10m0-10L7 18" stroke="{red}"/>'
        if name == 'coser_superficies': return f'<path d="M4 17Q8 6 12 16Q16 5 20 17" fill="#b9ddee" fill-opacity=".35" stroke="{blue}"/><path d="M12 7v12" stroke="{green}" stroke-dasharray="2 1"/>'
        return f'<path d="M6 17V8l6-3 6 3v9l-6 3Z" fill="#b9ddee" fill-opacity=".4" stroke="{blue}"/>'

    if category == 'referencias':
        if name == 'punto': return '<circle cx="12" cy="12" r="2" fill="#2e8cc8"/>'
        if name == 'eje': return f'<path d="M5 19L19 5" stroke="{blue}" stroke-dasharray="2 1"/>'
        if name == 'sistema_coordenadas': return f'<path d="M9 16h11M9 16V5M9 16l-5 5"/><path d="M20 16l-2-1v2Z" fill="{red}"/><path d="M9 5l-1 2h2Z" fill="#263846"/><path d="M4 21l1-2 1 1Z" fill="{blue}"/>'
        return f'<path d="M4 17l4-10 12 3-4 10Z" fill="#b9ddee" fill-opacity=".6" stroke="{blue}"/>'

    if category == 'vistas':
        if name == 'zoom': return f'<circle cx="10" cy="10" r="6" fill="#fff" stroke="{blue}"/><path d="M14 14l6 6" stroke="#263846" stroke-width="1.4"/>'
        if name == 'ajustar': return f'<path d="M4 9V4h5m6 0h5v5m0 6v5h-5M9 20H4v-5" stroke="{blue}"/>'
        if name == 'ocultar_mostrar': return '<path d="M3 12Q7 6 12 6t9 6q-4 6-9 6t-9-6Z" fill="#fff"/><circle cx="12" cy="12" r="3" fill="url(#gBlue)"/>'
        return _box()

    if category == 'propertymanager':
        if name == 'aceptar': return f'<path d="M4 13l5 5L20 5" stroke="{green}" stroke-width="2"/>'
        if name == 'cancelar': return f'<path d="M6 6l12 12m0-12L6 18" stroke="{red}" stroke-width="1.8"/>'
        if name == 'ayuda': return f'<circle cx="12" cy="12" r="8" fill="url(#gBlue)"/><text x="12" y="16" font-size="11" text-anchor="middle" fill="#fff" stroke="none" font-family="Arial" font-weight="bold">?</text>'
        if name == 'mensaje': return '<path d="M4 6h16v11H9l-4 3v-3H4Z" fill="#fff59a"/><path d="M7 10h10m-10 3h7"/>'
        return '<rect x="4" y="4" width="16" height="16" fill="url(#gGrey)"/><path d="M14 18l1-3 4-4 2 2-4 4Z" fill="#f4d349"/>'

    if category == 'eje_parametrico':
        body = _shaft()
        if name == 'crear_eje': return body + f'<circle cx="19" cy="19" r="3" fill="{green}" stroke="#fff"/><path d="M17.5 19h3m-1.5-1.5v3" stroke="#fff"/>'
        if name == 'editar_eje': return body + '<path d="M15 21l1-3 4-4 2 2-4 4Z" fill="#f4d349"/>'
        if name == 'agregar_chavetero': return body + f'<path d="M7.5 7h4v3h-4Z" fill="#2e8cc8"/><circle cx="19" cy="19" r="3" fill="{green}" stroke="#fff"/>'
        if name == 'quitar_chavetero': return body + f'<path d="M7.5 7h4v3h-4Z" fill="#2e8cc8"/><circle cx="19" cy="19" r="3" fill="{red}" stroke="#fff"/>'
        return body + '<circle cx="19" cy="19" r="3" fill="#d9dee2"/><path d="M19 16.5v5m-2.5-2.5h5"/>'

    return _box()


def ensure_icon_pack() -> str:
    marker = os.path.join(_TARGET_ROOT, '.classic-v3-complete')
    if os.path.exists(marker):
        return _TARGET_ROOT
    for relative in _PATHS:
        destination = os.path.join(_TARGET_ROOT, *relative.split('/'))
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        title = os.path.splitext(os.path.basename(relative))[0].replace('_', ' ').title()
        with open(destination, 'w', encoding='utf-8') as handle:
            handle.write(_wrap(title, _shape(relative)))
    with open(marker, 'w', encoding='utf-8') as handle:
        handle.write(f'{len(_PATHS)} SVG icons\n')
    return _TARGET_ROOT


def icon_path(relative_path: str) -> str:
    ensure_icon_pack()
    return os.path.join(_TARGET_ROOT, *relative_path.split('/'))
