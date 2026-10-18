# SolidFreeCAD Desktop 0.1.0-alpha.13

Interfaz propia para diseño mecánico con el motor oficial **FreeCAD 1.1.1**.
La ventana conserva un CommandManager superior, un único panel izquierdo
Modelo/Propiedades y un visor central. Los menús, iconos y controladores de
SolidFreeCAD son originales.

## Iniciar

En el paquete portable Windows, extraiga **toda la carpeta** y ejecute
`SolidFreeCAD.exe`. El instalador añade los accesos directos correspondientes.

Para ejecutar el código fuente, abra `START_SOLIDFREECAD.FCMacro` desde una
instalación de FreeCAD 1.1.1 y ejecútelo, conservando la carpeta `sfc8` junto al
macro. También puede abrir `SolidFreeCADStandalone.py` desde FreeCAD.

## Funciones disponibles

- Pieza y cuerpo Part Design, documentos FCStd, importación y exportación STEP.
- Croquis en XY, XZ, YZ y sobre caras planas de un cuerpo Part Design.
- Línea, rectángulo y círculo con dos clics y vista preliminar transitoria.
- Polilínea con clics sucesivos; vuelva al inicio para cerrar o pulse Enter para
  terminar abierta. Los extremos coincidentes de líneas quedan vinculados con
  restricciones nativas para mantener el perfil al cambiar cotas.
- Arco de tres puntos: inicio, punto intermedio y final; vista preliminar curva.
- Ranura recta por longitud total y ancho, formada por dos líneas y dos arcos
  tangentes. Sus radios y tramos rectos se editan desde Cotas y relaciones.
- Recorte nativo del tramo elegido entre intersecciones. Esc termina la
  herramienta; Cancelar el croquis restaura los tramos eliminados.
- Ajuste geométrico del cursor al origen, extremos y centros; inferencia
  horizontal y vertical para líneas. Las líneas ajustadas a puntos añaden
  coincidencia; el ajuste visual de arcos, círculos y rectángulos independientes
  no añade relaciones entre esas entidades.
- Rectángulos y círculos por medidas con cotas nativas; edición de longitudes,
  radios, diámetros, ángulo de línea respecto a X, horizontal y vertical desde
  Propiedades. Relacione dos entidades mediante tangencia, concentricidad,
  paralelismo, perpendicularidad o igualdad.
- Saliente/Base paramétrico nativo, incluidos perfiles con agujeros.
- Corte extruido por profundidad o por todo.
- Revolución con ángulo, dirección y eje horizontal/vertical del croquis.
- Redondeo y chaflán sobre una o varias aristas seleccionadas con Ctrl + clic.
- Patrones lineales y circulares nativos de una operación Saliente, Corte o
  Revolución, con 2–100 instancias, eje X/Y/Z del cuerpo e inversión. El patrón
  lineal usa separación entre instancias; el circular usa ángulo total.
- Comprobación de cada instancia del patrón: una copia fuera del cuerpo o un
  saliente desconectado impide confirmar y muestra la instancia problemática.
- Vista preliminar diferida al cambiar parámetros, inversión y simetría.
- Aceptar/cancelar mediante transacciones nativas y Deshacer/Rehacer.
- Árbol jerárquico con filtro, selección, edición por doble clic, cambio de nombre
  y visibilidad. La eliminación protege las referencias posteriores.
- Búsqueda de comandos, atajos, medición y comprobación BRep.
- Vistas isométrica, frontal, superior y derecha; sombreado o alámbrico.

## Flujo de ejemplo

1. Cree **Nueva pieza** y un **Nuevo croquis** sobre Planta (XY).
2. Dibuje un rectángulo o introduzca su ancho y alto en Propiedades.
3. Acepte el croquis y seleccione **Saliente/Base**.
4. Cambie la profundidad: la operación nativa genera la vista preliminar.
5. Confirme y seleccione una cara plana superior del sólido.
6. Cree otro croquis, dibuje un círculo y acepte.
7. Seleccione **Corte extruido** y active **Por todo** para perforar la pieza.
8. Seleccione el Corte en el árbol y elija Patrón lineal o Patrón circular.
   Defina eje, separación o ángulo e instancias; confirme la vista preliminar.
9. Seleccione las aristas deseadas con Ctrl + clic y aplique Redondeo o Chaflán.
10. Guarde FCStd para conservar las operaciones y exporte STEP para intercambio.
11. Doble clic en una operación del árbol para modificarla; confirme o cancele.

En un patrón circular de 360°, las instancias se distribuyen sin duplicar la
original al final. En un ángulo menor, la primera y la última definen los extremos
del arco. La ranura requiere longitud total mayor que ancho. El recorte usa las
intersecciones disponibles en el croquis; sin intersecciones, el motor puede
eliminar la entidad completa.

`Esc` cancela primero la herramienta de dibujo. Un segundo `Esc` revierte la
edición del croquis. Los comandos de archivo y cambio de documento se bloquean
mientras una operación está activa. Cerrar SolidFreeCAD devuelve los documentos
abiertos a la ventana de FreeCAD, incluido el trabajo todavía sin guardar.

## Alcance de esta versión

Esta entrega completa el flujo básico de modelado de piezas. **No incluye**
ensamblajes con relaciones, chapa metálica, planos TechDraw, superficies,
barridos ni el conjunto completo de restricciones Sketcher. Los patrones se
limitan a una operación, una dirección y ejes de origen del cuerpo: todavía no
incluyen matrices de dos direcciones, trayectorias ni patrones de acabados.
Los prototipos anteriores de esas áreas no se muestran como comandos funcionales.
Los sólidos estáticos de alpha.11 conservan sus formas al abrirlos; no se
convierten automáticamente en operaciones paramétricas nuevas. STEP conserva
geometría, mientras que FCStd conserva el historial paramétrico.

Las referencias topológicas se guardan con el mecanismo nativo de FreeCAD.
Cambios grandes de topología pueden requerir volver a seleccionar una cara o
arista. Los croquis sobre caras se limitan a superficies planas de Part Design. Al crear
un croquis en un plano de referencia, el sólido se oculta temporalmente para
que el perfil quede visible; Aceptar o Cancelar restaura la visibilidad previa.

## Comprobación reproducible

`tests/solidfreecad_standalone_runtime.py` se ejecuta dentro de FreeCAD 1.1.1.
Comprueba geometría y volúmenes conocidos, huecos, caras soportadas, edición,
cancelación, Undo/Redo, historial FCStd, intercambio STEP, callbacks del visor,
filtro y búsqueda; también ranuras tangentes, arcos, relaciones, recorte y patrones
con volúmenes analíticos, edición y rollback. Captura la interfaz en 1366×768 y
1920×1080 y los PropertyManager de croquis y patrones.

El workflow `.github/workflows/windows-alpha13-standalone.yml` verifica el SHA-256
del motor oficial, ejecuta las pruebas reales en Windows y genera los paquetes
portable e instalador solo después de aprobarlas. La validación de escalado DPI
y sesiones prolongadas en una estación física Windows sigue pendiente.

El motor y las dependencias conservan sus avisos y licencias en `Runtime`.
