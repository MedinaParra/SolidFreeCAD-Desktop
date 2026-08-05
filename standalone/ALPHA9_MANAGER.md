# SolidFreeCAD alpha.9 — administrador contextual único

## Cambio principal

Alpha.9 elimina el panel de propiedades derecho de alpha.8 y lo sustituye por un solo administrador persistente a la izquierda.

El mismo espacio alterna entre:

- Modelo: árbol de historial paramétrico;
- Propiedades: definición contextual de la operación actual;
- Configuraciones: variantes dimensionales futuras.

## Mecánica de operación

### Croquis

1. `Nuevo croquis` crea un `Sketcher::SketchObject` directamente.
2. El administrador cambia de Modelo a Propiedades.
3. Aparecen aceptar/cancelar, selección de plano, parámetros, entidades y relaciones.
4. Aceptar conserva el croquis y vuelve al árbol.
5. Cancelar elimina el croquis nuevo y vuelve al árbol.

### Saliente/Base

1. `Saliente/Base` selecciona el croquis activo.
2. El administrador muestra perfil, profundidad, inversión y vista preliminar.
3. El sólido no se crea hasta pulsar aceptar.
4. Cancelar no modifica el documento.

## Reglas arquitectónicas

- no existe `PropertyPanel` derecho;
- no se usa la TaskView nativa de FreeCAD;
- no se permite `Gui.runCommand()`;
- la ventana standalone continúa siendo propietaria de menú, ribbon y administrador;
- FreeCAD se conserva como motor de documentos, Sketcher, Part, OpenCASCADE y FCStd.

## Propiedad intelectual

La interacción se inspira en patrones generales de CAD paramétrico profesional. El código, nombres visuales y recursos pertenecen a SolidFreeCAD y no incluyen elementos propietarios de SolidWorks.
