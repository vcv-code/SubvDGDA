# EELL 2026 — propuesta de resolución provisional

`propuesta-provisional-EELL2026.pdf` — firmada el 8 de octubre de 2026 a las
14:27 por el director general de Derechos de los Animales. 110 páginas.

## El plazo de alegaciones no tiene fecha pública

El punto CUARTO concede «un plazo de **diez días hábiles**, contado a partir del
día siguiente al de **la notificación**». La notificación es individual y no se
publica; el documento la distingue expresamente de la publicación en el portal,
que es el punto TERCERO (art. 13.4 de la Orden). Así que **no hay una fecha de
cierre única**:

- notificada el mismo 8 → vence el **23 de octubre de 2026** (viernes)
- notificada el 9 → vence el **26 de octubre de 2026** (lunes)

El 12 de octubre es Fiesta Nacional y en 2026 cae en lunes, lo que ya mete tres
días seguidos no hábiles tras el 9. Y los festivos autonómicos y locales de cada
entidad pueden moverlo todavía más. Por eso la web dice «en torno al 23 de
octubre» y advierte de que la fecha exacta depende de la notificación: dar una
fecha cerrada sería afirmar algo que el documento no dice.

En el mismo plazo, las propuestas como beneficiarias aceptan o renuncian; el
silencio se entiende como aceptación.

## Por qué está guardada aquí si no es la definitiva

**Porque no va al BOE.** El art. 13.4 de la Orden DSA/1352/2022 solo obliga a
publicar la propuesta provisional en el portal de subvenciones del Ministerio,
y de ahí desaparece cuando sale la definitiva. Al BOE llega únicamente esta
última. Si no se guarda ahora, el estado provisional de la convocatoria no se
puede reconstruir después.

Y ese estado tiene valor propio: comparar provisional con definitiva es la
única forma de medir **cuánto mueven las alegaciones, las renuncias y las
subsanaciones** — algo que no se sabe de ningún año anterior porque no se
conservó la provisional.

## Lo que dice

| | |
|---|---|
| Convocatoria | Resolución de 7 de abril de 2026 · 1.950.000 € |
| Solicitudes registradas | 1.142 |
| Admitidas y evaluadas | 985 |
| **Propuestas como beneficiarias** | **35** |
| Inadmitidas | 112 |
| Desistidas | 45 |
| Admitidas sin fondos por insuficiencia de crédito | 950 (tramo 1: 638 · tramo 2: 241 · tramo 3: 71) |
| Puntuación mínima subvencionable | tramo 1: 81 · tramos 2 y 3: 80 |

Importes por tramo: 868.799,02 € (T1), 836.165,75 € (T2), 245.035,23 € (T3).

## Cuánto se espera que cambie

De 2025 se conservan **las dos** versiones, y comparándolas se ve que la
provisional predijo la definitiva casi exactamente: las concedidas pasaron de
39 a 40, las 303 excluidas no se movieron y una entidad desistió. El detalle
está en `../2025/README.md`.

Si 2026 se comporta igual, las 35 propuestas serán 35 o 36. Con un solo año de
contraste no da para sentar una regla, pero sí para dejar de tratar la
provisional como una incógnita.

Lo que sí ha cambiado respecto a 2025 es **el listón**: las puntuaciones
mínimas suben de 79/80/79 a **81/80/80**. Con 1.142 solicitudes frente a 1.315,
hacen falta más puntos para entrar.

## Qué NO hacer con esto todavía

**No cargarlo en la base de datos.** Es provisional: hay diez días hábiles de
alegaciones desde la notificación, y las entidades propuestas pueden renunciar.
El pipeline del proyecto se construye sobre resoluciones definitivas del BOE, y
mezclar un estado intermedio rompería esa garantía.

Cuando salga la definitiva, se carga esa y este fichero se queda como
referencia de lo que cambió por el camino.

## Lo que sí está publicado en la web

`frontend/estadisticas-eell.html` lleva un aviso (`#aviso-provisional-2026`)
con las cifras de arriba, el plazo de alegaciones y un enlace al PDF **del
portal del Ministerio** (no a esta copia: `data/raw/` no se sirve por web). Está
ahí porque la página solo llega a 2025 y quien busque 2026 se quedaba sin nada.

El **banner de la portada** añade una frase que enlaza ese aviso, en la entrada
`'eell-2026'` de `DOCS_PROVISIONALES` (`frontend/js/home.js`). Enlaza la página
y no el PDF a propósito: la URL del Ministerio caduca y tenerla en dos ficheros
es garantía de corregir solo uno.

**Hay que retirar las dos cosas al cargar la definitiva**, o el aviso contradice a la propia
página: seguiría diciendo «las cifras llegan hasta 2025» con 2026 en los
gráficos. No hace falta acordarse:
`tests/test_aviso_provisional_2026.py` falla en cuanto aparezcan registros EELL
de 2026 en el dataset con el aviso todavía puesto, y el mensaje de error dice
qué tocar.
