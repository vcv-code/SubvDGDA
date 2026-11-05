# EPA 2026 — propuesta provisional de resolución de concesión

`propuesta-provisional-EPA2026.pdf` — firmada el **4 de noviembre de 2026** a las
10:22 por el director general de Derechos de los Animales y publicada en la BDNS
ese mismo día. 32 páginas. CSV `GEN-6261-763b-e06f-fd37-c138-a494-5f2d-cd33`.

La copia guardada viene de la sede electrónica y pesa 667.266 bytes; la que
sirve la BDNS pesa 653.520. **Son el mismo documento**: comprobado que las dos
tienen 32 páginas, el mismo texto al carácter y los mismos 759 expedientes. La
diferencia es el envoltorio de «informe de firma» que añade la sede.

## Dónde se publica: aquí NO es como en EELL

Esta propuesta **se publica en la Base de Datos Nacional de Subvenciones**
(antecedente NOVENO y disposición octava.5 de la convocatoria), no en el portal
del Ministerio. La de EELL va al revés: portal del Ministerio, por el art. 13.4
de la Orden DSA/1352/2022. Son órdenes de bases distintas —EPA se rige por la
**Orden DSA/1045/2021**, modificada por la **Orden DCA/505/2024**— y conviene no
dar por hecho que un trámite funciona igual en las dos líneas.

Eso tiene dos consecuencias prácticas:

1. **El enlace no caduca.** La ficha de la convocatoria en la BDNS
   (`infosubvenciones.es/bdnstrans/GE/es/convocatorias/904714`) va acumulando
   documentos; cuando salga la definitiva seguirá ahí. El PDF suelto de la
   provisional de EELL, en cambio, desaparece del portal. **Ojo a la ruta: la
   canónica es la plural.** `convocatoria/:id` existe pero es un redirect
   heredado, y como la BDNS es una aplicación de una sola página, una ruta mal
   escrita no da 404: devuelve la misma cáscara y se queda en blanco.
2. **El plazo de alegaciones es exacto, no aproximado.** Son diez días hábiles
   «contados a partir del día siguiente al de la **publicación** en la BDNS», y
   esa fecha es pública. La da la propia API:

   ```
   GET /bdnstrans/api/convocatorias?vpd=GE&numConv=904714
   ```

   devuelve la lista de `documentos`, y el de la propuesta provisional (id
   `1549551`) lleva `datPublicacion: 2026-11-04`. Diez días hábiles desde el 5,
   sin festivos nacionales por medio, dan el **miércoles 18 de noviembre de
   2026**. Es la diferencia con EELL: allí el plazo corre desde una notificación
   individual que no se publica, y por eso la web dice «en torno al».

   Esa misma llamada es la forma de saber qué documentos hay sin mirar la web a
   ojo, y la que conviene usar cuando toque detectar la definitiva.

## Lo que dice

| | |
|---|---|
| Convocatoria | Resolución de 5 de mayo de 2026 · BOE de 13 de mayo · 1.994.971,58 € |
| Solicitudes registradas | 759 |
| Admitidas a trámite | 676 · excluidas a trámite 83 |
| **Propuestas como subvencionables** | **444** |
| Excluidas | 119 |
| No financiables por insuficiencia de crédito | 196 |
| Puntuación mínima, colonias felinas | 41 |
| Puntuación mínima, animales abandonados | 45,55 |

La Comisión de Valoración se reunió el **3 de noviembre de 2026**: un día antes
de la firma. Los tres anexos juntos suman los 759 expedientes (444 + 119 + 196),
así que el documento da cuenta de todas las solicitudes presentadas.

## El anexo de beneficiarias no dice la línea — pero el importe sí

**Anexo I** (las 444 propuestas) trae CIF, expediente, entidad, puntos e importe,
y **no** la línea de actuación. **Anexo III** (las 196 no financiables) sí la
trae. Así que, tal cual, se sabe en qué línea compitió quien se quedó fuera pero
no quien entró.

Se recupera igualmente, porque **el importe es la puntuación multiplicada por una
constante distinta en cada línea**:

| Línea | Beneficiarias | Importe | €/punto | Corte |
|---|---:|---:|---:|---:|
| Colonias felinas | 219 | **1.000.000,00 €** | 73,5231 | 41,00 |
| Animales abandonados | 225 | 994.971,58 € | 66,7818 | 45,55 |
| | **444** | **1.994.971,58 €** | | |

Tres cosas confirman la deducción: las 444 filas y la suma cuadran al céntimo con
el documento; la desviación máxima respecto de la constante es de **0,002 €/punto**,
puro redondeo; y el corte que sale de los importes —41,00 y 45,55— coincide
**exactamente** con el que declara el propio documento sin que se le haya dado esa
información. El millón redondo para colonias enseña además que el reparto entre
líneas estaba fijado de antemano, no salió de la valoración.

## El corte no «baja»: depende de la línea

Comparado con las resoluciones definitivas de años anteriores:

| Año | Colonias felinas | Animales abandonados |
|---|---:|---:|
| 2024 | 30,00 | 30,00 |
| 2025 | 35,00 | 55,00 |
| 2026 *(provisional)* | **41,00** | **45,55** |

En colonias felinas el listón **sube** (de 35 a 41) y en animales abandonados
**baja** casi diez puntos (de 55 a 45,55). Antes de 2024 no hay corte comparable:
se concedía al 77–92 % de quien solicitaba y los mínimos andaban por 5–10 puntos.

**Cuidado con la comparación**, eso sí: 2026 es una **provisional** y los años
anteriores son **definitivas**. Las renuncias liberan crédito, así que el corte
definitivo de 2026 puede bajar todavía respecto de estos números. Compara
peras con peras solo cuando salga la definitiva.

## Qué NO hacer con esto todavía

**No cargarlo en la base de datos.** Hay diez días hábiles de alegaciones y la
propuesta «no pone fin al procedimiento ni crea derechos» (punto CUARTO). El
pipeline se construye sobre resoluciones definitivas; mezclar un estado
intermedio rompería esa garantía.

## Lo que sí está publicado en la web

`frontend/estadisticas-epas.html` lleva un aviso (`#aviso-provisional-epa-2026`)
con estas cifras y un enlace a la ficha de la BDNS. El banner de la portada lo
menciona, en la entrada `'epa-2026'` de `DOCS_PROVISIONALES` (`frontend/js/home.js`).

**Hay que retirar las dos cosas al cargar la definitiva.** No hace falta
acordarse: `tests/test_aviso_provisional_2026.py` falla en cuanto aparezcan
registros EPA de 2026 en el dataset con el aviso todavía puesto.
