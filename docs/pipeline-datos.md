# Pipeline de datos

Documentación técnica del proceso completo de obtención, extracción, transformación y carga del dataset de subvenciones de bienestar animal (BDNS + DGDA).

→ Ver también: [Modelo de datos](modelo-datos.md)

---

## API BDNS

La API pública BDNS (<https://www.infosubvenciones.es/bdnstrans/doc>) es el punto de partida del pipeline. Da las convocatorias completas, pero **de las concesiones de la DGDA solo publica las de una de las ocho convocatorias resueltas** — el resto solo existe en los documentos oficiales del BOE. El apartado siguiente detalla la comprobación.

### Endpoints utilizados

**`GET /convocatorias/busqueda`** — convocatorias registradas en la BDNS.

Campos principales: `id`, `numeroConvocatoria`, `descripcion`, `fechaRecepcion`, `nivel1` / `nivel2` / `nivel3` (organismo convocante jerárquico).

**`GET /concesiones/busqueda`** — concesiones con beneficiarios e importes.

Campos principales: `id`, `codConcesion`, `fechaConcesion`, `beneficiario`, `importe`, `numeroConvocatoria`, `nivel1` / `nivel2` / `nivel3`.

### Qué publica realmente la BDNS de la DGDA

**Comprobado el 13 de septiembre de 2026 preguntando a la API por las 19
convocatorias de la Dirección General, una a una.** Conviene tener el dato medido
y no de oído, porque es la justificación de que exista todo el pipeline del BOE y
es lo primero que alguien va a rebatir.

| Convocatoria | Concesiones en la BDNS |
|---|---|
| EPA 2021 · 2023 · 2024 · 2025 · 2026 | 0 |
| EELL 2023 · 2024 · 2025 · 2026 | 0 |
| Certámenes y premios (7 convocatorias) | 0 |
| Subvención nominativa PGE 2023 | 1 |
| **EPA 2022** (nº 645245) | **592** |

La DGDA ha comunicado concesiones **una sola vez**: las de 2022, dadas de alta el
14 de febrero de 2023. Comprobado también que no están registradas en otro sitio:
`/minimis/busqueda` y `/ayudasestado/busqueda` devuelven 0 para las ocho
convocatorias del proyecto.

En cifras del propio dataset, **2.030 concesiones y 12.835.954 €** corresponden a
convocatorias que nunca se comunicaron. El total real de lo que no llegó a la BDNS
es **2.031 y 12.840.639,32 €**: hay que sumar una concesión de 4.684,91 € de la
convocatoria de 2022 que sí se comunicó, pero de cuyas 593 concedidas la BDNS solo
registró 592 (ver más abajo). La portada publica la primera cifra, que es la que se
calcula sola desde la API, y por eso dice «de convocatorias que nunca se
comunicaron» y no «en total» — decir lo segundo contradiría al párrafo siguiente de
la propia página.

**Matiz que hay que tener claro para no equivocarse: los PDF sí están.** La ficha
de cada convocatoria (`GET /convocatorias?numConv=<n>`, campo `documentos`) trae
los documentos que la DGDA ha ido subiendo, y **de las ocho convocatorias
resueltas las ocho tienen su resolución de concesión**, varias con sus anexos de
estimadas, desestimadas y desistidas:

| Convocatoria | Fichero de resolución en la BDNS |
|---|---|
| EPA 2021 | `Resolución Concesion Subvenciones Convocatoria 2021.pdf` |
| EPA 2022 | `Resolución Concesión Subvenciones 2022.pdf` + anexos I, II y III |
| EPA 2023 | `RESOLUCION 2023 CON ANEXOS.pdf` |
| EPA 2024 | `Resolución Concesión Subvenciones EPA2024.pdf` |
| EPA 2025 | `report_Resol_conc_conv_epas_2025.pdf` |
| EELL 2023 | `report_231207_Resolución Concesión EELL.pdf` + anexos |
| EELL 2024 | `Resolucion con Anexos.pdf` |
| EELL 2025 | `Resol_conc_EELL_2025.pdf` |

Las de 2026 no la tienen porque aún no están resueltas: solo convocatoria y
listados de admitidos y excluidos.

Así que **la afirmación correcta no es «no están las resoluciones», sino «no están
las concesiones como datos»**. Son cosas distintas: lo que el artículo 18.2 obliga
a remitir es el registro de cada concesión —beneficiario, importe, fecha—, que es
lo que aparece en la pestaña Concesiones, se puede filtrar, agregar y descargar en
CSV, XLSX, JSON o XML. Un PDF colgado en la ficha no es eso: para explotarlo hay
que parsearlo, que es exactamente el trabajo que hace este pipeline. Decirlo mal
es además fácil de rebatir, porque cualquiera que abra la ficha ve los PDF.

**Esto no es un hueco legal, es un incumplimiento.** El artículo 18.2 de la Ley
38/2003 General de Subvenciones obliga a las administraciones concedentes a
remitir a la BDNS «información sobre las convocatorias **y las resoluciones de
concesión recaídas**», y el artículo 20.2 concreta que debe incluir
«identificación de los beneficiarios, importe de las subvenciones otorgadas». El
RD 130/2019 fija el plazo: antes de que acabe el mes siguiente al de la concesión.
La única excepción es para concesiones de 100 € o menos, y aquí la más pequeña es
de 600 €. El órgano concedente de las ocho convocatorias —EELL incluidas— es la
DGDA: los ayuntamientos son beneficiarios, no concedentes, así que la obligación
no es suya.

### Por qué el volcado de 2022 tampoco habría bastado

Aun en el único año disponible, `/concesiones/busqueda` devuelve **solo las
concedidas**. No trae puntuaciones, ni causas de exclusión, ni las solicitudes que
no obtuvieron nada:

| Estado | Registros | % |
|---|---|---|
| concedida | 2.623 | 41,0 % |
| no beneficiaria | 2.627 | 41,1 % |
| excluida | 641 | 10,0 % |
| desistida | 505 | 7,9 % |

**El 59 % del dataset no existe en la BDNS de ninguna forma**, ni las 5.250
puntuaciones ni las 641 causas de exclusión. El buscador de exclusiones sería
imposible de construir desde esta fuente. El formato nunca fue el obstáculo —hay
CSV, XLSX, JSON y XML—: la BDNS publica quién cobró, y el BOE publica quién pidió,
cuánto puntuó y por qué se quedó fuera.

### El cruce de 2022, y lo que revela

Comparadas una a una las 592 concesiones de la BDNS con las 593 concedidas de 2022
del dataset, difieren en exactamente dos cosas, y las dos a favor del BOE:

1. **A la BDNS le falta una concesión.** `G90180365` (Protectora de Animales La
   Sexta Huella, 4.684,91 €), que es justo la diferencia entre los dos importes
   totales (1.999.525,45 € frente a 1.994.840,54 €). Fue denegada en la resolución
   de 2022 por causa 10 y **concedida después**, publicada en el BOE de 2023 pero
   perteneciente al expediente `SUBV2022659` de la convocatoria de 2022 — el caso
   que `resolver_anio_epa` detecta y reatribuye. La BDNS se quedó con la foto de
   febrero de 2023 y no la actualizó.
2. **La BDNS arrastra un CIF que el BOE ya rectificó.** Registra `G72307358` para
   Gatos de El Puerto, cuando el **BOE-A-2023-13752** lo corrigió a `G72296254`.
   La corrección oficial nunca se propagó.

Es decir: para el único año en que ambas fuentes coinciden, la reconstruida desde
el BOE está más completa y más al día que la oficial.

### Lo concedido no es lo que se queda cada entidad

Un tercer hueco del artículo 20.2, que exige publicar los importes «efectivamente
percibidos» y las «resoluciones de reintegros».

**Las dos líneas NO cobran igual, y es fácil equivocarse aquí:**

| | Norma | Pago |
|---|---|---|
| Entidades locales | [Orden DSA/1352/2022](https://www.boe.es/buscar/act.php?id=BOE-A-2023-104), art. 19 | «se realizará **con carácter anticipado** por el 100 por ciento de la subvención concedida». Sin condición y sin garantía (art. 18) |
| Protectoras | [Orden DSA/1045/2021](https://www.boe.es/buscar/act.php?id=BOE-A-2021-16021), art. 14 | El anticipo del 100 % solo procede «**cuando la naturaleza de los gastos subvencionables lo permita**»; para gastos ya realizados se paga «una vez dictada la resolución de concesión» |

En la práctica, como la resolución EPA llega con el periodo subvencionable ya
cumplido, **la protectora adelanta el dinero de su bolsillo y cobra después**. En
EELL sí lo recibe antes de gastarlo. Lo confirmó la autora del proyecto, que es
beneficiaria, y se verificó contra el texto consolidado de ambas órdenes.

En los dos casos hay que justificar, y lo no justificado se **reintegra con
intereses de demora**; en EELL, ejecutar menos del 60 % del proyecto ya es
incumplimiento parcial.

Nada de eso se publica, así que el dataset solo puede contener **lo concedido**.
Los campos `importe` de esta web son eso, no lo que cada entidad acabó reteniendo.

**Lo único que se sabe viene de una solicitud de transparencia** (septiembre de
2026). El Ministerio respondió que ninguna entidad local renunció en 2023, 2024 ni
2025 y que no consta expediente de reintegro alguno, y facilitó los expedientes que
**no presentaron la justificación en plazo**:

| Convocatoria | Sin justificar en plazo | Importe | Nota |
|---|---|---|---|
| EELL 2023 | 5 de 60 concedidas (8,3 %) | 188.250 € | tras requerimiento solo 2 presentaron |
| EELL 2024 | **21 de 55 (38,2 %)** | 624.986 € | se les requiere el trámite |
| EELL 2025 | — | — | en ejecución, aún no vencen |

**Verificado**: los 26 expedientes que cita la respuesta se cruzaron uno a uno con
`dataset_unificado.json`. Existen los 26, los 26 constan como `concedida` y el
nombre coincide en todos. El documento es coherente con el BOE hasta el número de
expediente, lo que descarta que sea una respuesta genérica.

Tres cautelas al usar estas cifras:

1. **No justificar en plazo no es haber devuelto el dinero.** Es un trámite
   incumplido cuyo paso siguiente es el requerimiento.
2. **Es una foto a la fecha de la respuesta.** La convocatoria de 2025 sigue en
   ejecución y sus justificaciones no han vencido, así que un «ninguna» de hoy no
   cierra el asunto.
3. **Solo cubre entidades locales**, que es por lo que se preguntó. De las
   protectoras no hay equivalente, y eso no permite suponer que allí no ocurra.

Los numeradores (5 y 21) son transcritos: no salen de ninguna resolución del BOE y
no se pueden calcular. Los denominadores (60 y 55) sí son del dataset, y son
convocatorias cerradas que ya no cambian.

### Parámetros de la API que conviene no volver a averiguar

El filtro por convocatoria del endpoint de concesiones es **`numeroConvocatoria`**.
Los nombres intuitivos (`numConv`, `codigoBDNS`, `idConvocatoria`) **no dan error**:
se ignoran en silencio y la respuesta devuelve las concesiones de toda España, lo
que se confunde fácilmente con «aquí no hay filtro que valga». La API también
responde `ERR_MANTENIMIENTO_BBDD` con HTTP 200 en sus ventanas de mantenimiento,
así que cualquier script que la consulte debe mirar el cuerpo, no el código HTTP.

---

## Fuentes alternativas (BOE)

Para cubrir la ausencia de datos en la API se combinan dos tipos de documentos oficiales:

**XMLs del BOE** — fuente principal cuando están disponibles. Formato estructurado que elimina los problemas de extracción. Usados para EPA 2021–2025 y EELL 2025. Parser: `BeautifulSoup`.

**PDFs de resoluciones** — usados para EELL 2023–2024, donde no existe XML. Presentan limitaciones: tablas con diseños complejos, saltos de página y, en el caso de EELL 2025, parte del listado de beneficiarias fue publicado como **imágenes escaneadas dentro del PDF**, lo que impidió la extracción automática. Esos datos tuvieron que obtenerse del Excel complementario que publicó la DGDA. Parser: `pdfplumber`.

En conjunto, el dataset se construye de tres fuentes: API BDNS (convocatorias), XMLs BOE (resoluciones EPA y EELL 2025) y PDFs BOE + Excel (resoluciones EELL 2023–2024).

---

## Estrategia técnica

La API BDNS proporciona las convocatorias, pero las concesiones de la DGDA solo están comunicadas para 2022 (ver §API BDNS) y aun así sin puntuaciones ni exclusiones. Se utiliza un pipeline adicional basado en documentos oficiales del BOE (XML, PDF, Excel) para reconstruir los datos completos.

```text
API BDNS
↓
Convocatorias
↓
Relación con PDFs
↓
Datos completos
```

### Pipeline real implementado

```text
XML / PDF BOE (DGDA) + Excel manual (EELL 2025)
↓
Parsing (pdfplumber / BeautifulSoup / openpyxl)
↓
JSON por año (data/processed/)
  · EELL 2025: incluye es_agrupacion y municipios_agrupacion
    (leído de las hojas Entidades_beneficiarias y Municipios del xlsx)
↓
Unificación y normalización de estados (unificar_datasets.py)
↓
Dataset unificado (data/final/dataset_unificado.json)
↓
Normalización de causas de exclusión (normalizar_causa_exclusion.py)
  · Deja causa_exclusion como código(s) canónicos separados por ";"
    validados contra el catálogo data/final/causas_exclusion.json
↓
Carga en base de datos (cargar_dataset.py)
  · 7 pasos: convocatorias → beneficiarios → solicitudes
             → concesiones → agrupaciones → agrupacion_miembros
             → causas_exclusion (catálogo código→motivo por tipo y año)
  · Los municipios miembro sin registro propio en el dataset
    se insertan en beneficiarios en el paso 2
  · Paso 1 (convocatorias): consulta los snapshots BDNS de
    data/raw/convBDNS/ vía scripts/data_processing/bdns_lookup.py
    para obtener num_convoc, fecha_convocatoria y titulo_convoc
    oficiales. Los diccionarios _FECHAS y _TITULO de cargar_dataset.py
    quedan como fallback para casos sin BDNS (típicamente años
    futuros antes de que la DGDA publique en BDNS).
```

**Dos propiedades del pipeline que no son evidentes y conviene tener presentes:**

1. **`unificar_datasets.py` revierte la normalización de causas.** Reconstruye `dataset_unificado.json` desde los JSON procesados, donde `causa_exclusion` está tal cual la publica el BOE (`10, 12, 16`). Ejecutarlo suelto deshace el trabajo de `normalizar_causa_exclusion.py` en ~370 registros. Los dos pasos van siempre juntos y en ese orden: **`make dataset`** los encadena.
2. **`cargar_dataset.py` es aditivo, no sincronizador.** Antes de insertar una solicitud comprueba si ya existe por `(num_expediente, id_convoc)` y, si está, la salta. Nunca hace `UPDATE` ni `DELETE`. Eso lo hace idempotente y seguro para poblar una BD vacía o añadir una convocatoria nueva, pero significa que **un cambio en registros ya cargados no llega a la BD volviendo a ejecutarlo**: hay que recrearla con **`make reset-db`** (`docker compose down -v && up -d` + carga). No hace falta esperar a la BD a mano; `up -d` ya bloquea hasta que su healthcheck pasa, porque backend, cron y adminer declaran `condition: service_healthy`.

### Integración con BDNS en la carga (`bdns_lookup.py`)

El módulo `scripts/data_processing/bdns_lookup.py` actúa de **puente** entre los snapshots BDNS (descargados por `scripts/ingestion/bdns_client.py`, ver §API BDNS) y el paso 1 de `cargar_dataset.py`. Lee el snapshot más reciente de cada patrón (`*_convocatorias_proteccion_animal.json` y `*_convocatorias_colonias_felinas.json`), detecta el tipo (`epa` / `eell`) por palabras clave del título y devuelve un índice `{(anio, tipo): {num_convoc, fecha_convocatoria, titulo, bdns_id}}`.

`cargar_convocatorias()` consulta primero el índice BDNS:

- Si encuentra la `(anio, tipo)` → usa los datos oficiales y deja `_FECHAS` solo para validación cruzada (avisa si difieren).
- Si no la encuentra → usa los diccionarios hardcodeados como fallback y deja `num_convoc` a `NULL`.

Esto sustituye el flujo anterior, en el que las fechas y títulos se mantenían a mano en `_FECHAS` / `_TITULO` y `num_convoc` quedaba siempre vacío para las históricas — perdiéndose la trazabilidad a la ficha BDNS oficial.

**El snapshot se queda viejo, y conviene saber cuándo importa y cuándo no.** El
que había en `data/raw/convBDNS/` era del **22 de marzo de 2026**, anterior a las
dos convocatorias de ese año: **EPA 904714** (registrada el 11/05/2026) y
**EELL 897468** (08/04/2026). Se ha regenerado el 13 de septiembre de 2026 y ya
están las diez.

Esto **no era un defecto de la base de datos en producción**. `cargar_convocatorias()`
solo crea las convocatorias que aparecen en el dataset, y el dataset llega hasta
2025: las de 2026 las insertó `check_bdns.py`, que consulta la API en directo y
las da de alta con su `num_convoc` correcto. Los diccionarios `_FECHAS` y
`_TITULO` tienen entradas de 2026 esperando a que haya datos que cargar.

Donde sí habría mordido es en el futuro: cuando se publique la resolución de 2026
y sus solicitudes entren en el dataset, una carga desde cero con el snapshot viejo
habría dejado `num_convoc` a `NULL` para ese año, perdiendo el enlace a la ficha
oficial. Conviene por tanto **regenerar el snapshot antes de incorporar un año
nuevo**, lanzando `scripts/ingestion/bdns_client.py`.

---

## Procesamiento de datos

### Entidades Locales (EELL)

- 2023 → PDF (pdfplumber, diseño en dos pasadas para celdas multilinea)
- 2024 → PDF (pdfplumber, misma arquitectura)
- 2025 → XML BOE + Excel manual (beneficiarias publicadas como imagen)

Scripts:

- `parser_eell_PDF_base.py` → EELL 2023 y 2024
- `parser_eell_BOE_2025.py` → EELL 2025

> La resolución EELL 2025 publica las tablas de entidades beneficiarias como imágenes incrustadas en el BOE, lo que impide extraerlas directamente del XML. Las tablas se **transcribieron manualmente** desde las imágenes a un Excel complementario (`eell_2025_beneficiarias.xlsx`) que el parser lee después con `openpyxl`. Este fichero es por tanto una entrada manual del pipeline, no un artefacto generado.

---

### Entidades de Protección Animal (EPA)

- 2021 → XML BOE
- 2022 → XML BOE
- 2023 → XML BOE
- 2024 → XML BOE
- 2025 → XML BOE

Scripts:

- `parser_EPAs_BOE_base.py` → EPA 2021–2024 (lógica común)
- `parser_EPAs_BOE_2025.py` → EPA 2025 (estructura diferente)
- `parser_EPAs_admitidas_2024.py` → línea de subvención EPA 2024 (ver nota)

> En la resolución EPA 2025 las cabeceras de las columnas cambian respecto a años anteriores: aparece "Cuantía concedida a la entidad" (que contiene la palabra *entidad*) y la cabecera de puntuación varía entre anexos. Esto rompe el mapeo por palabras clave del parser base. El parser 2025 usa extracción heurística por contenido de celda: importes > 100 para el campo importe, valores entre 0 y 100 para puntuación.

> **Línea de subvención EPA 2024.** El BOE de concesión 2024 no desglosa la línea (colonias felinas / animales abandonados) por entidad, así que las concesiones quedaban con `linea = NULL`. La "relación definitiva de admitidas y excluidas" (PDF de la Sede, `data/raw/epas/2024/relacion-def-admitidas-EPA2024.pdf`) sí trae esa columna en el Anexo I. `parser_EPAs_admitidas_2024.py` la extrae por texto anclando el CIF (la línea es lo que va **después** del CIF, para no confundirse con nombres que contienen "COLONIAS") y `enriquecer_linea_epa2024.py` la añade a `epas_2024.json` cruzando por `num_expediente`. Cruce completo: 628/628 concedidas (627 con línea + 1 "No aplica" → NULL). Desde 2025 el XML sí incluye la línea directamente, sin este paso.

### Causas de exclusión

Los anexos de excluidas/desestimadas del BOE indican por entidad el/los **código(s) de causa** ("Motivo de desestimación", "Causas de exclusión", "Criterios de exclusión"). Ambos parsers EPA capturan esa columna cuando existe (los parsers EELL ya lo hacían); las tablas-leyenda embebidas (cabeceras "Ref./Motivo") se descartan solas porque no tienen columna de expediente ni de entidad.

Particularidades resueltas:

- **Numeración por convocatoria**: cada (tipo, año) usa su propia numeración de causas. La leyenda código→motivo vive en `data/final/causas_exclusion.json`, transcrita de las tablas de referencia revisadas manualmente y cotejada con los anexos oficiales (la fuente publicada tiene huecos y erratas: p. ej. EPA 2025 omite el motivo del código 11 y dos resoluciones ponen "Ley 38/2033"). Es dato de referencia histórico e inmutable — excepción documentada a la regla de no hardcodear.
- **Separadores inconsistentes**: `4; 5`, `6, 7, 8`, `2. 6.a` e incluso `16.18.19.` (sin espacios), con códigos que llevan punto propio (`6.a`, `3.1`). `normalizar_causa_exclusion.py` tokeniza **guiado por el catálogo** (match voraz del código válido más largo en cada posición) y guarda el resultado canónico separado por `;`. Validación: 643/643 excluidas resuelven contra el catálogo.
- **EPA 2021 en texto libre**: ese anexo no usa códigos sino el motivo literal; se mapea a código por match exacto del texto contra el catálogo (21/21).
- **Desistidas por no subsanar (EELL 2023, ANEXO IV)**: 198 ayuntamientos "se tienen por desistidos al no haber subsanado en plazo" (causa 18). El BOE los clasifica como **desistidas**, no excluidas, y así se mantienen (fuera del buscador de exclusiones, por consistencia con el resto de años, donde las desistidas tampoco aparecen).
- **Conciliación con el Excel de referencia**: EPA 2022 muestra 58 excluidas frente a las 60 del anexo por dos motivos, ambos correctos: `SUBV2022271` aparece también como concedida y la deduplicación intra-año conserva la concedida; y `SUBV2022659` (La Sexta Huella) se resolvió a favor en el BOE de 2023, así que su registro de 2022 pasa a concedida (ver "Duplicados cross-year"). Por lo mismo, EPA 2023 muestra 12 en vez de 13: `2023B628` (Amibichos) se resolvió a favor en el BOE de 2024. Los desajustes de ±1 en EELL quedaron cerrados sin tocar datos: EELL 2025 ya era correcto (303 excluidas, cotejadas por NIF contra el ANEXO III del XML oficial) y en EELL 2024 el Ayuntamiento de Oñati (`EXP2024/007460`) aparece a la vez en el ANEXO II —desestimada, 52,31 puntos— y en el ANEXO III —excluida, con la causa en blanco—; ante la contradicción de la fuente se mantiene como `no_beneficiaria`, de ahí 84 y no 85.

---

### Formatos del `num_expediente` por año y tipo

El identificador oficial del BOE para cada solicitud cambia entre años y entre tipos. Conservamos los valores exactos publicados en el BOE — no los unificamos — porque son la única forma de cruzar nuestro dataset con el documento original. Estado de los formatos verificado en el dataset:

**EPA (asociaciones)** — formato cambia cada par de años:

| Año | Formato dominante | Ejemplo | N | Notas |
|---|---|---|---:|---|
| 2021 | `SUBV` + 3 díg + año (4 díg) | `SUBV0012021` | 328 | Año al final |
| 2022 | `SUBV` + año (4 díg) + 3 díg | `SUBV2022001` | 653 | Año al inicio — inversión |
| 2023 | año + `B` + 3 díg | `2023B002` | 649 | Formato nuevo, ruptura |
| 2023 | `SUBV2022659` (cross-year) | — | 1 | Resolución desplazada (entidad de 2022) |
| 2023 | `2023PF01` | — | 1 | Caso único |
| 2024 | año + `B` + 3 díg | `2024B651` | 881 | Mismo que 2023 |
| 2025 | año + `B` + 3 díg | `2025B001` | 730 | Mismo |
| 2025 | `SIN_EXP_2025_NNN` | `SIN_EXP_2025_001` | 110 | IDs **sintéticos** generados por `cargar_epas()` para excluidas que el BOE no numera |

**EELL (entidades locales)** — más consistente, pero 23 casos sin año en 2025:

| Año | Formato dominante | Ejemplo | N | Notas |
|---|---|---|---:|---|
| 2023 | `EXP` + año + `/` + 6 díg | `EXP2023/007446` | 592 | Estándar |
| 2023 | `EXP2023/...SI` | `EXP2023/009021SI` | 1 | Sufijo único |
| 2024 | `EXP` + año + `/` + 6 díg | `EXP2024/003873` | 1137 | Estándar |
| 2025 | `EXP` + año + `/` + 6 díg | `EXP2025/008399` | 1292 | Estándar |
| 2025 | `EXP/` + 5–6 díg **sin año** | `EXP/98789`, `EXP/100024` | 23 | Solo en `no_beneficiaria` (19) y `excluida` (4) — convención BOE |

Implicación para la búsqueda: `GET /solicitudes/?buscar=...` admite tokens de **≥ 4 caracteres** sobre `num_expediente` además del nombre. Permite buscar por número exacto (`100024`, `EXP/100024`, `2024B651`) o por nombre, todo desde el mismo campo. Tokens más cortos solo se buscan en nombre para evitar explosión de resultados.

---

## Herramientas de extracción

Se utiliza:

- `pdfplumber` → extracción de tablas desde PDF
- `BeautifulSoup` → parsing de XML del BOE
- `openpyxl` → lectura de Excel (correcciones manuales EELL 2025)

Alternativas evaluadas para PDF:

- `tabula-py`
- `camelot`

---

## Problemas encontrados y soluciones

### Problemas generales

1. Datos incompletos en BDNS → uso de PDFs
2. PDFs inconsistentes → parsers separados
3. Saltos de línea → normalización
4. Múltiples CIF → selección del primero válido
5. Puntuaciones no numéricas → `NULL`
6. Importes europeos → conversión a `float`
7. Filas partidas → reconstrucción

---

### Problemas específicos EELL

#### Parsing 2023–2024

Problemas: filas partidas, importes mal parseados y valores null
Soluciones: limpieza de texto, normalización y conversión de datos

#### XML BOE 2025

Problemas: sin importes, inconsistencia nif/cif y sin estado
Soluciones: parsing con BeautifulSoup, unificación de campo `cif` y `"estado": "concedida"`

**Formato de expediente heterogéneo:** el XML del BOE 2025 incluye dos esquemas de numeración para los expedientes EELL:

- `EXP2025/NNNNN` — formato estándar con año, presente en el Excel principal
- `EXP/NNNNN` — formato sin año, usado por 23 entidades que aparecen solo en el XML (no en el Excel), todas con estado `excluida` o `no_beneficiaria`

No son duplicados de las mismas entidades: los números no coinciden entre formatos. El parser acepta ambos (`if exp.startswith("EXP")`). Sin impacto económico. Si el BOE de años futuros vuelve a usar este formato mixto, habrá que verificar que no aparezca la misma entidad con ambos identificadores en el mismo año.

#### Integración Excel

Problema: importes manuales
Solución: Excel + merge por expediente

#### CIF

Problemas: `"None"` como string y ausencias
Solución: `limpiar_cif()` y normalización a `null`

#### Estado

Problema: valores null
Solución: inclusión en parsers y normalización

---

### Problemas del proceso de unificación (unificar_datasets.py)

#### Duplicados cross-year (mismo número de expediente en años distintos)

Situación detectada: cuatro expedientes aparecían en más de un año del dataset.

- **SUBV2022021** — mismo código de expediente en el BOE de 2021 (Amores Perros Cádiz) y 2022 (Can Terrassa). Probablemente error del BOE al reutilizar el número.
- **SUBV2022271** — la protectora Peludosos aparece dos veces dentro del JSON de 2022 (concedida con importe y denegada sin importe). Publicada en dos anexos distintos del BOE. Se conserva la concedida (prioridad al registro con importe > 0).
- **SUBV2022659** — La Sexta Huella aparece en el BOE de 2022 como excluida (causa 10) y en el de 2023 como concedida con 4.684,91 €. **Es la misma solicitud**: el recurso se resolvió a favor y la resolución salió publicada un año tarde.
- **2023B628** — Amibichos aparece en el BOE de 2023 como excluida y en el de 2024 como concedida con 4.028,42 €. Mismo caso.
- **SUBV2032021** — Mes Que Gossos, con `anio` 2032 por una errata en el número de expediente. No es cross-year real.

**Problema adicional detectado:** el campo `anio` en los JSON de origen refleja el año del número de expediente (ej: SUBV2022659 → anio=2022), no el año del BOE que publica el registro. Con la tolerancia ±1 original, los registros cross-year colapsaban bajo el mismo año aunque estuvieran en ficheros distintos.

Solución implementada:

- Se cambia la clave de deduplicación de `(tipo, num_expediente)` a `(tipo, num_expediente, anio)`.
- Regla de prioridad intra-año: cuando dos registros compiten por la misma clave, se prefiere el que tiene importe > 0 sobre el que tiene importe = 0. Si ambos tienen o ambos no tienen importe, prevalece el último procesado.
- El campo `anio` se fija al año del **fichero fuente**, no al que trae el JSON, salvo en las **resoluciones tardías** (ver más abajo). Esto evita que expedientes distintos que comparten número colapsen bajo la misma clave.

**Resoluciones tardías (`resolver_anio_epa`).** Una solicitud presentada en el año N cuya resolución no se publica hasta el BOE de N+1 aparece en el fichero de N+1 pero pertenece económicamente a la convocatoria de N. Atribuirla al año del fichero infla los importes de N+1. Por eso se reatribuye al año que declara el JSON, pero **solo cuando está probado que es la misma solicitud**: el mismo `num_expediente` **y** el mismo `cif` tienen que existir también en el fichero del año declarado.

Esa condición es imprescindible, porque hay dos falsos positivos que no deben reatribuirse:

| Caso | Por qué NO se reatribuye |
|------|--------------------------|
| `SUBV2022021` | En el BOE de 2021 es Amores Perros Cádiz (`G01779131`) y en el de 2022 es Can Terrassa (`G66561812`). El BOE **reutilizó el número** para otra entidad: el CIF no coincide, así que cada una se queda en su año. |
| `SUBV2032021` | Declara `anio` 2032 por errata. No existe fichero de 2032, así que se queda en el año de su BOE (2021). |

Reatribuir sin comprobar el CIF volvería a colapsar registros distintos bajo la misma clave — exactamente el fallo que arregló el cambio de clave.

Resultado: se reatribuyen **dos** registros (`SUBV2022659` → 2022, `2023B628` → 2023). Al caer en el año donde ya estaba su versión excluida, la prioridad intra-año conserva la concedida, de modo que cada solicitud queda con **un solo registro y su estado final**. El importe global no cambia (14.835.479,86 € concedidos); solo se reparte al año correcto: EPA 2022 +4.684,91 €, EPA 2023 −656,49 €, EPA 2024 −4.028,42 €. El total de registros pasa de 6398 a **6396**, y `periodo_meses` sigue al año reatribuido, no al del fichero.

#### El periodo subvencionable no es el año de la convocatoria

Éste es el punto que más confunde a quien consulta los datos, incluidas las
propias entidades: **el año de una convocatoria no es el año de gasto que
financia.**

| Convocatoria | Periodo subvencionable | Meses |
|---|---|---|
| EPA 2021 | año 2022 | 12 |
| EPA 2022 | año 2023 | 12 |
| EPA 2023 | **1.er semestre de 2024** | 6 |
| EPA 2024 | **2.º semestre de 2024** | 6 |
| EPA 2025 | año 2025 | 12 |
| EPA 2026 | año 2026 | 12 |
| EELL 2023 | **1 oct 2023 – 31 mar 2024** | **6** |
| EELL 2024 | año 2025 | 12 |
| EELL 2025 | año 2026 | 12 |
| EELL 2026 | no declarado en el extracto | 12 |

Las EPA de 2021 a 2024 financiaban el año siguiente y a partir de 2025 se
realinearon; las EELL siguen desfasadas un año. Dos consecuencias que conviene
tener presentes: **ninguna convocatoria EPA financió el año 2021**, y las EPA de
2023 y 2024 no son dos años consecutivos sino **las dos mitades de 2024**.

**Corrección de un dato que estaba mal.** Hasta agosto de 2026 el pipeline daba
`periodo_meses = 12` a todas las EELL, con el comentario «las EELL siempre
tienen periodo anual». No es cierto: la de 2023 fue de seis meses. Los importes
EELL de 2023 no eran comparables con los de otros años sin normalizar, y no se
estaban normalizando.

**De dónde sale el dato.** De ningún campo de la API: solo aparece en la prosa
del extracto del BOE, apartado «Objeto». La BDNS sí devuelve ese texto íntegro
en `anuncios[].texto` del endpoint `convocatorias?numConv=<n>`, que es como se
obtuvo. Parsear prosa automáticamente sería frágil, así que está transcrito una
sola vez en `_PERIODO_SUBVENCIONABLE` (`scripts/data_processing/cargar_dataset.py`)
con la cita literal de cada convocatoria al lado, y de ahí pasa a la base de
datos en los campos `periodo_anio` y `periodo_matiz`. El frontend solo pinta lo
que le llega: un año nuevo aparece en blanco hasta que alguien transcriba su
extracto, en vez de mostrar un dato inventado.

Contexto normativo relevante: el 17 de mayo de 2024 se modifica la Orden sobre las Bases de las subvenciones para EPAs (publicada en BOE el 29 de mayo 2024). Entre otros cambios, se crean dos líneas diferenciadas: animales abandonados y gestión de colonias felinas. Estas líneas aparecen por primera vez en la resolución de 2025.

#### Derivación de provincia y CCAA para EELL desde el CIF

El CIF de las entidades locales españolas codifica la provincia en sus posiciones 1–2 (ej: `P3802200J` → código `38` → Santa Cruz de Tenerife). Se implementó una función de extracción que permite añadir los campos `provincia` y `ccaa` a todos los registros EELL.

Casos especiales gestionados:

- **Mancomunidades y Consells Comarcals** con códigos de provincia no estándar (56, 64, 67, 53, 79): se resuelven mediante un diccionario de overrides manuales por CIF completo. Ejemplos:
  - P5606301I (Mancomunidad Cijara, Extremadura)
  - P6400601H (Mancomunidad Los Pedroches, Córdoba/Andalucía)
  - P6700008C (Consell Comarcal Alt Empordà, Girona/Cataluña)
  - S7900010E (Ciudad Autónoma de Melilla)
  - G79458618 (Mancomunidad El Molar, Madrid)
- **Asociaciones (G-type CIF)** en el dataset EELL: corresponden a entidades que desistieron o fueron excluidas. Se dejan con `provincia=null` y `ccaa=null`.
- **Mancomunidades que cruzan varias provincias**: `provincia=null` pero `ccaa` asignada.

Para las EPAs (asociaciones con CIF tipo G), la provincia no es derivable del CIF de forma estándar. Se deja como mejora futura (`null`).

11 registros EELL permanecen sin provincia (0,4% del total EELL): 7 asociaciones desistidas/excluidas + 1 empresa + 1 asociación excluida + 2 más con CIF no resoluble.

#### Punto final tipográfico en nombres de entidad

El BOE termina con `.` el 80 % de los nombres de entidad (2 478 de 3 103 únicos en el dataset de junio 2026) como convención tipográfica de tabla. Eso provoca apariciones inconsistentes ("ASOCIACIÓN X." en una resolución, "ASOCIACIÓN X" en otra) y ruido visual en la UI.

Verificación SQL: cero nombres con punto solo en posición intermedia (`LIKE '%.%' AND NOT LIKE '%.'`). El punto es siempre final.

Solución: `limpiar_entidad()` en `unificar_datasets.py` aplica `.rstrip('.').strip()`. La normalización es segura — no hay siglas legales como "S.L." que dependan del punto final, y la deduplicación de beneficiarios se hace por CIF, no por nombre.

#### Escapes Unicode rotos en nombres de entidad

Algunos parsers (PDF/XML) generan secuencias del tipo `uXXXX` sin la barra invertida — el carácter Unicode original quedó codificado como su escape Python (`Ç` para `Ç`) y en algún paso se perdió la barra. Ejemplos detectados: `PUu00C7OL`, `CADAQUu00C9S`, `MAu00C7ANET`, `ANIu00D1ON`, `VALLu00C8S`, `ASSOCIACIu00D3`. Total: 6 beneficiarios (todos catalanes/aragoneses/valencianos con `Ç`, `É`, `È`, `Ñ`, `Ó`).

Solución: `_arreglar_escapes_unicode()` en `unificar_datasets.py` convierte `uXXXX` → carácter Unicode **solo dentro del rango Latin-1 Suplemento (U+00A0–U+00FF)**, que cubre los acentos y caracteres latinos comunes en castellano, catalán, gallego, etc. Esa restricción evita falsos positivos: nombres legítimos como `AYUNTAMIENTO DE UBEDA` (donde `UBEDA` es una secuencia "U" + 4 hex puramente casual) no se tocan porque `U+BEDA` cae fuera del rango protegido.

---

#### Erratas del origen corregidas (`corregir_identidad`)

Algunas entidades salían partidas en dos fichas porque el BOE publicó su CIF con
una errata en un año concreto, o directamente sin CIF. El histórico de esas
entidades se veía incompleto: faltaban años y faltaba dinero.

Se corrigen en `unificar_datasets.py`, en el único punto por el que pasan todos
los registros, y **no en la base de datos**, para que sobrevivan a un `reset-db`
y a cualquier recarga. El criterio es el mismo que en `resolver_anio_epa`: solo
se toca lo que está **probado** contra una fuente oficial.

| Entidad | Qué pasaba | Corrección | Verificado en |
|---|---|---|---|
| ASSOCIACIÓ GAT I CUA | El BOE de 2024 transpuso dos dígitos (`…37041` → `…34071`), y ese año quedaba fuera del histórico | `G16734071` → `G16737041` | Los otros tres años (2022, 2023, 2025) llevan el mismo CIF, y la BDNS registra con él la concesión de 2022 |
| ASOCIACIÓN "GATOS DE EL PUERTO" | El registro de 2022 conserva el NIF anterior a la rectificación del BOE | `G72307358` → `G72296254` | **BOE-A-2023-13752**, corrección de errores de la convocatoria 2022 |
| LAS ALMAS DE COCOA | El registro de 2021 salió sin CIF | Se le asigna `G67811000` | Sus registros de 2022 y 2024, y la concesión de 2022 en la BDNS |
| AYUNTAMIENTO DE CARLET | El BOE lo nombra «Casavieja» | Nombre → Carlet | Web municipal y diccionario del INE |
| AYUNTAMIENTO DE CARRIÓN DE CALATRAVA | El BOE lo nombra «Castilforte» | Nombre → Carrión de Calatrava | Web municipal y diccionario del INE |
| ASOCIACIÓN PROYECTO CES GATOS TORREVIEJA | El BOE de 2024 le pone un NIF con «B», de sociedad limitada | `B54999156` → `G54999156` | Inscrita en el Registro de Asociaciones de Alicante: siendo asociación, su NIF empieza por G |
| SOS PELUDOS LEPEROS | Dos NIF distintos en 2024 y 2025 | `G56705338` → `G56725328` | **Sin fuente externa** — ver más abajo |

En los dos municipios **el CIF sí era correcto**, solo el nombre estaba mal. Por
eso la provincia, el mapa y las estadísticas por comunidad ya eran correctos
antes de la corrección, y las seis solicitudes afectadas eran todas
`no_beneficiaria`: no había ni un euro mal atribuido. Casavieja (Ávila,
`P0505400B`) y Castilforte (Guadalajara, `P1909200F`) **existen** y aparecen en
el dataset con su propio CIF; no se tocan.

**El caso de SOS PELUDOS LEPEROS es distinto al resto** y conviene tenerlo
presente: es la única entrada de la tabla que **no** está verificada contra una
fuente externa. Sus dos NIF validan, difieren en dos posiciones (no es una
transposición limpia) y ninguno aparece en la web indexada asociado a entidad
alguna. Tampoco se resolverá solo: sus dos solicitudes son `no_beneficiaria`,
así que nunca llegará a la BDNS, que solo publica concesiones. Se adopta el de
2025 por ser la publicación más reciente de la misma autoridad. Es una decisión
consciente y revisable, no un hecho comprobado.

**Cómo comprobar un NIF dudoso**, por orden de solidez:

1. **Corrección de errores en el BOE.** Es lo que zanjó Gatos de El Puerto.
2. **BDNS**, `concesiones/busqueda?nifCif=<CIF>`. Su campo `beneficiario` trae
   NIF y nombre juntos. Confirmó Gat i Cua y Las Almas de Cocoa.
3. **Consulta pública de asociaciones** del Ministerio del Interior. No publica
   el NIF, pero sí confirma que la entidad es una asociación —y por tanto que su
   NIF empieza por G—, que es lo que resolvió Torrevieja. Ojo: si la entidad
   está en un registro autonómico, la consulta nacional la lista pero no ofrece
   ficha de detalle.
4. **La propia entidad.** Muchas protectoras publican su CIF para donativos.

**Contraste con la BDNS.** El endpoint `concesiones/busqueda?nifCif=<CIF>` de
`infosubvenciones.es` permite comprobar un NIF contra una fuente oficial
distinta del BOE, y su campo `beneficiario` trae NIF y nombre juntos. Tiene un
límite importante: de nuestras convocatorias solo están cargadas las concesiones
de la de **2022** (`645245`), y solo publica **concedidas**, así que no sirve
para nada que sea `no_beneficiaria`, `excluida` o `desistida`.

#### Detección de estos casos (`scripts/revisar_duplicados.py`)

Herramienta de auditoría, no parte del pipeline. Recorre las entidades cargadas
y avisa de cuatro cosas: posibles duplicados por nombre, entidades sin CIF, CIF
que no cuadra con la comunidad declarada, y municipios cuyo nombre no cuadra con
la provincia de su CIF.

Para lo último cruza con el diccionario de municipios del INE, que **no se
versiona** (fichero de terceros); se descarga de `www.ine.es` y se coloca en
`data/raw/ine/diccionario_municipios.xlsx`, o se indica con la variable
`INE_MUNICIPIOS`. Sin él, las otras tres comprobaciones siguen funcionando.

Un aviso importante sobre el método: **los tres dígitos de municipio del CIF no
son el código del INE**. Los asigna Hacienda por orden de alta. Traducir el CIF
a un nombre por esa vía da falsos positivos masivos (715 de 1.759 en la prueba).
Lo que sí es fiable son los **dos dígitos de provincia**, así que la
comprobación va al revés: se busca el nombre en el INE y se mira si alguna de
sus provincias coincide con la del CIF. Así, de 1.750 ayuntamientos salieron 7
sospechosos, de los que 4 eran nombres abreviados, 1 el cambio de provincia de
Gátova y 2 los errores reales de la tabla anterior.

## Organización del proyecto

```text
data/
  raw/        → datos originales (XMLs y PDFs del BOE)
  processed/  → JSONs intermedios por año y fuente
  final/      → dataset unificado listo para cargar
```

Separación por fuentes dentro de cada carpeta:

- `eell/` → entidades locales
- `epas/` → protección animal
- `convBDNS/` → datos de la API BDNS

Esta separación evita mezclar fuentes, facilita el debugging por año y mejora la trazabilidad del pipeline.
