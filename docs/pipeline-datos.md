# Pipeline de datos

Documentación técnica del proceso completo de obtención, extracción, transformación y carga del dataset de subvenciones de bienestar animal (BDNS + DGDA).

→ Ver también: [Modelo de datos](modelo-datos.md)

---

## API BDNS

La API pública BDNS (<https://www.infosubvenciones.es/bdnstrans/doc>) es el punto de partida del pipeline. Proporciona datos de convocatorias, pero **no incluye los beneficiarios reales de las subvenciones de la DGDA** — esos datos solo existen en los documentos oficiales del BOE.

### Endpoints utilizados

**`GET /convocatorias/busqueda`** — convocatorias registradas en la BDNS.

Campos principales: `id`, `numeroConvocatoria`, `descripcion`, `fechaRecepcion`, `nivel1` / `nivel2` / `nivel3` (organismo convocante jerárquico).

**`GET /concesiones/busqueda`** — concesiones con beneficiarios e importes.

Campos principales: `id`, `codConcesion`, `fechaConcesion`, `beneficiario`, `importe`, `numeroConvocatoria`, `nivel1` / `nivel2` / `nivel3`.

El problema: las concesiones gestionadas por la DGDA **no aparecen** en este endpoint. Solo están disponibles en las resoluciones publicadas en el BOE, lo que obliga a construir un pipeline adicional de parseo de documentos.

---

## Fuentes alternativas (BOE)

Para cubrir la ausencia de datos en la API se combinan dos tipos de documentos oficiales:

**XMLs del BOE** — fuente principal cuando están disponibles. Formato estructurado que elimina los problemas de extracción. Usados para EPA 2021–2025 y EELL 2025. Parser: `BeautifulSoup`.

**PDFs de resoluciones** — usados para EELL 2023–2024, donde no existe XML. Presentan limitaciones: tablas con diseños complejos, saltos de página y, en el caso de EELL 2025, parte del listado de beneficiarias fue publicado como **imágenes escaneadas dentro del PDF**, lo que impidió la extracción automática. Esos datos tuvieron que obtenerse del Excel complementario que publicó la DGDA. Parser: `pdfplumber`.

En conjunto, el dataset se construye de tres fuentes: API BDNS (convocatorias), XMLs BOE (resoluciones EPA y EELL 2025) y PDFs BOE + Excel (resoluciones EELL 2023–2024).

---

## Estrategia técnica

La API BDNS proporciona información de convocatorias, pero no incluye los beneficiarios reales de las subvenciones de la DGDA. Se utiliza un pipeline adicional basado en documentos oficiales del BOE (XML, PDF, Excel) para reconstruir los datos completos de concesiones.

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

### Integración con BDNS en la carga (`bdns_lookup.py`)

El módulo `scripts/data_processing/bdns_lookup.py` actúa de **puente** entre los snapshots BDNS (descargados por `scripts/ingestion/bdns_client.py`, ver §API BDNS) y el paso 1 de `cargar_dataset.py`. Lee el snapshot más reciente de cada patrón (`*_convocatorias_proteccion_animal.json` y `*_convocatorias_colonias_felinas.json`), detecta el tipo (`epa` / `eell`) por palabras clave del título y devuelve un índice `{(anio, tipo): {num_convoc, fecha_convocatoria, titulo, bdns_id}}`.

`cargar_convocatorias()` consulta primero el índice BDNS:

- Si encuentra la `(anio, tipo)` → usa los datos oficiales y deja `_FECHAS` solo para validación cruzada (avisa si difieren).
- Si no la encuentra → usa los diccionarios hardcodeados como fallback y deja `num_convoc` a `NULL`.

Esto sustituye el flujo anterior, en el que las fechas y títulos se mantenían a mano en `_FECHAS` / `_TITULO` y `num_convoc` quedaba siempre vacío para las históricas — perdiéndose la trazabilidad a la ficha BDNS oficial.

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
- **Conciliación con el Excel de referencia**: EPA 2022 muestra 59 excluidas frente a las 60 del anexo porque `SUBV2022271` aparece también como concedida y la deduplicación intra-año conserva la concedida (correcto). Quedan ±1 en EELL 2024/2025 pendientes de ajuste manual (fila partida en el PDF / expediente sintético duplicado).

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
- **SUBV2022659** — La Sexta Huella aparece en 2022 como excluida y en 2023 como concedida. Desistió en 2022 y volvió a solicitar en 2023.
- **2023B628** — Amibichos aparece en 2023 como excluida y en 2024 como concedida. Mismo caso.

**Problema adicional detectado:** el campo `anio` en los JSON de origen refleja el año del número de expediente (ej: SUBV2022659 → anio=2022), no el año de la convocatoria. Con la tolerancia ±1 original, los registros cross-year colapsaban bajo el mismo año aunque estuvieran en ficheros distintos.

Solución implementada:

- Se cambia la clave de deduplicación de `(tipo, num_expediente)` a `(tipo, num_expediente, anio)`.
- El campo `anio` del registro se fija siempre al año del fichero fuente (`anio_fallback`), no al que trae el JSON. Esto garantiza que el mismo expediente en distintas convocatorias tenga años diferentes.
- Resultado: SUBV2022271 (intra-año 2022) se deduplica conservando la concedida; los otros tres conservan ambos registros en años distintos.
- Regla de prioridad intra-año: cuando dos registros compiten por la misma clave, se prefiere el que tiene importe > 0 sobre el que tiene importe = 0. Si ambos tienen o ambos no tienen importe, prevalece el último procesado.

#### Periodo subvencionable semestral en EPAs 2023 y 2024

Las convocatorias EPA de 2023 y 2024 cubrieron un periodo semestral (6 meses) en lugar del anual habitual. Esto no afecta a la estructura del dataset pero sí al análisis comparativo de importes entre años.

Solución: se añade el campo `periodo_meses` a todos los registros (6 para EPA 2023/2024, 12 para el resto de EPA y para todos los EELL).

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
