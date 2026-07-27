# Modelo de datos del sistema

## 1. Introducción

El modelo de datos del sistema se ha diseñado a partir de la integración de dos fuentes principales:

- La API de la Base de Datos Nacional de Subvenciones (BDNS), que proporciona información estructurada sobre convocatorias públicas.
- Los documentos oficiales publicados por la Dirección General de los Derechos de los Animales (DGDA), que contienen información sobre concesiones y exclusiones.

Tras el proceso de extracción, limpieza y unificación, se obtiene un **dataset final consolidado** que combina la información de convocatorias con los datos de concesiones publicados en los documentos oficiales.

La implementación física de la base de datos utiliza **MariaDB 11**, desplegada mediante un contenedor Docker (ver sección 6.8).

---

## 2. Fuentes de datos utilizadas

### 2.1 API BDNS

La API BDNS permite obtener información sobre convocatorias públicas, incluyendo:

- código BDNS
- descripción
- organismo convocante
- fecha de publicación
- año

Esta información se utiliza para construir la tabla **convocatorias**, que actúa como referencia para las concesiones.

### 2.2 Documentos oficiales (PDF y XML)

Los documentos oficiales publicados por la DGDA contienen:

- listados de concesiones
- importes concedidos
- puntuaciones
- entidades beneficiarias
- causas de exclusión (EELL 2023–2025 y EPA 2021–2025; leyenda propia por convocatoria)
- tramos (solo en EELL 2025)

---

## 3. Proceso de transformación de los datos

El diseño del modelo de datos se ha realizado a partir del análisis de los datos disponibles y siguiendo un proceso de transformación desde la información original hacia un modelo relacional.

Este proceso se ha desarrollado en tres pasos principales:

1. Identificación de las entidades principales presentes en los datos.
2. Identificación de las relaciones entre dichas entidades.
3. Conversión de las entidades y relaciones en tablas de una base de datos relacional.

---

## 4. Entidades principales del modelo de datos

A partir del análisis de los datos obtenidos de la API BDNS y de los documentos oficiales, se identificaron las principales entidades implicadas en el proceso de concesión de subvenciones.

Las entidades del **modelo implementado** son:

- Convocatorias
- Beneficiarios
- Solicitudes
- Concesiones
- Agrupaciones de entidades locales
- Miembros de agrupación
- Causas de exclusión (catálogo código→motivo por tipo y año; ver §4.7)

---

### 4.1 Convocatorias

La entidad **Convocatorias** representa cada convocatoria oficial de subvenciones publicada por la administración pública.

La información sobre convocatorias se obtiene principalmente a través de la API BDNS.

Cada convocatoria puede recibir múltiples solicitudes por parte de entidades interesadas.

Campos principales:

- id_convoc (PK)
- num_convoc
- titulo_convoc
- tipo_convoc — ENUM: `epa`, `eell`
- anio_convocatoria
- fecha_convocatoria
- fecha_fin_plazo — fin del plazo de solicitud (NULL hasta que se conoce); el banner de la home muestra "plazo abierto/cerrado" según esta fecha
- fecha_resolucion

El campo `titulo_convoc` corresponde al campo **descripcion** devuelto por la API. El campo `anio_convocatoria` se añade de forma explícita para facilitar consultas estadísticas y la generación de gráficos de evolución temporal en el frontend.

---

### 4.2 Beneficiarios

La entidad **Beneficiarios** representa las entidades que solicitan las subvenciones.

Estas entidades pueden ser de dos tipos:

- asociaciones de protección animal
- entidades locales (ayuntamientos)

Campos principales:

- id_benef (PK)
- cif — UNIQUE
- nombre
- tipo_benef — ENUM: `asociacion`, `entidad_local`

Un beneficiario puede presentar varias solicitudes en distintas convocatorias. En el caso de las entidades locales, estas pueden participar adicionalmente en agrupaciones de ayuntamientos, tanto como representante como en calidad de miembro.

> Para las entidades locales (EELL), los campos `provincia` y `ccaa` se derivan del CIF a través del código de provincia estándar INE (posiciones 1–2). Se generan en el dataset unificado y se almacenan en la tabla `solicitudes` (no en `beneficiarios`, ya que para EPA estos campos son siempre `null`). El endpoint `GET /solicitudes/` los expone y permite filtrar por ellos con los parámetros `?provincia=` y `?ccaa=`.

---

### 4.3 Solicitudes

La entidad **Solicitudes** representa cada solicitud presentada por una entidad para participar en una convocatoria de subvenciones.

Cada solicitud está asociada a una convocatoria concreta y a una entidad beneficiaria.

Campos principales:

- id_solic (PK)
- id_convoc (FK → convocatorias)
- id_benef (FK → beneficiarios)
- num_expediente — UNIQUE. Para registros EPA sin número de expediente real se generan IDs sintéticos con formato `SIN_EXP_YYYY_NNN`.
- puntuacion
- estado — ENUM: `concedida`, `no_beneficiaria`, `excluida`, `desistida`
- causa_exclusion — código(s) de causa separados por `;` (p. ej. `2;6.a`); solo para `estado = excluida`, `NULL` en el resto. La leyenda código→motivo está en la tabla `causas_exclusion` (§4.7)

Los cuatro valores posibles del campo `estado` cubren los distintos resultados del proceso administrativo:

- **concedida** — solicitud aprobada y subvención concedida
- **no_beneficiaria** — admitida pero fuera del cupo presupuestario; en EELL todos los años, en EPA desde 2024
- **excluida** — rechazada por incumplimiento de requisitos formales; en EELL todos los años, en EPA 2021–2023 (el BOE las denomina "denegadas" pero tienen causa de exclusión formal)
- **desistida** — la entidad solicitante renunció al proceso

---

### 4.4 Concesiones

La entidad **Concesiones** representa las subvenciones que finalmente han sido concedidas.

Solo existe una concesión cuando el estado de la solicitud correspondiente es `concedida`.

Campos principales:

- id_conces (PK)
- id_solic (FK → solicitudes) — UNIQUE (relación 1:1 con solicitudes)
- importe — DECIMAL(12,2)
- linea — ENUM: `animales_abandonados`, `colonias_felinas`. NULL para años anteriores a 2025 y para todas las EELL (ver decisión 6.4)
- tramo — TINYINT. Campo específico de EELL 2025 que indica el tramo de subvención asignado. NULL para convocatorias que no aplican.

---

### 4.5 Agrupaciones de entidades locales

En determinadas convocatorias EELL, las solicitudes pueden presentarse en forma de **agrupaciones de ayuntamientos**. Estas agrupaciones tienen una entidad representante y varios miembros.

Campos principales:

- id_agrup (PK)
- id_conces (FK → concesiones) — UNIQUE: una agrupación por concesión
- id_represent (FK → beneficiarios) — ayuntamiento que actúa como representante
- num_municipios — número total de municipios que forman la agrupación

El ayuntamiento representante aparece también como miembro en `agrupacion_miembros`, con su importe individual asignado.

> **Mejora futura:** el BOE incluye un campo de cofinanciación por parte del propio ayuntamiento. Aporta puntos extra en la evaluación pero no modifica el importe concedido. Solo está disponible en el ANEXO V del XML 2025 (no beneficiarias) y no existe en los PDF de 2023/2024, por lo que su incorporación al modelo se pospone a una fase futura.

---

### 4.6 Miembros de agrupación

La entidad **Miembros de agrupación** representa los ayuntamientos que forman parte de una agrupación.

Campos principales:

- id_agrupM (PK)
- id_agrup (FK → agrupaciones)
- id_benef (FK → beneficiarios)
- importe_asignado — importe individual asignado a este municipio dentro de la agrupación

---

### 4.7 Causas de exclusión

Las solicitudes excluidas indican en los documentos oficiales el/los motivo(s) de exclusión, codificados. La entidad **causas_exclusion** es el **catálogo** código→motivo, y cada convocatoria (tipo + año) usa su propia numeración, por lo que el código solo tiene sentido junto a tipo y año.

Campos:

- id_causa (PK)
- tipo_convoc — ENUM: `epa`, `eell`
- anio
- codigo — tal como aparece en la resolución (`1`, `6.a`, `3.1`, `B`…) · UNIQUE junto a (tipo_convoc, anio)
- motivo
- articulo — artículo de la convocatoria, si la leyenda lo indica (`NULL` si no)

El catálogo se carga desde `data/final/causas_exclusion.json` (paso 7 de `cargar_dataset.py`), transcrito de las tablas de referencia revisadas manualmente y cotejado con los anexos oficiales del BOE (que contienen huecos y erratas). Cubre EPA 2021–2025 y EELL 2023–2025 (137 causas).

> **Decisión de diseño frente al modelo conceptual inicial:** el diagrama conceptual preveía una relación N:M `solicitudes`↔`causas_exclusion` resuelta con una tabla intermedia `solicitud_causas`. Se implementó en su lugar el campo `solicitudes.causa_exclusion` con los códigos canónicos separados por `;` + el catálogo como tabla de consulta, sin tabla intermedia. Motivo: es dato histórico de solo lectura (nunca se actualiza causa a causa), el volumen es pequeño (643 excluidas) y la API resuelve el filtrado por código con match por token exacto, con lo que la tabla intermedia solo añadiría complejidad de carga y joins sin aportar funcionalidad.

---

## 5. Relaciones entre entidades

### CONVOCATORIAS — SOLICITUDES

```
CONVOCATORIAS (1) ── Generan ── (N) SOLICITUDES
```

Una convocatoria puede recibir múltiples solicitudes. Cada solicitud pertenece únicamente a una convocatoria concreta.

---

### BENEFICIARIOS — SOLICITUDES

```
BENEFICIARIOS (1) ── Son presentadas por ── (N) SOLICITUDES
```

Un mismo beneficiario puede presentar solicitudes en distintas convocatorias. Cada solicitud la presenta un único beneficiario.

---

### SOLICITUDES — CONCESIONES

```
SOLICITUDES (1) ── Generan ── (0..1) CONCESIONES
```

Solo se genera una concesión cuando el estado de la solicitud es `concedida`. Las solicitudes con otros estados (no_beneficiaria, excluida, desistida) no generan concesión.

---

### CONCESIONES — AGRUPACIONES

```
CONCESIONES (1) ── Tienen ── (0..1) AGRUPACIONES
```

Solo las concesiones de convocatorias EELL pueden tener una agrupación asociada. Las concesiones EPA nunca generan agrupación.

---

### AGRUPACIONES — AGRUPACIÓN MIEMBROS

```
AGRUPACIONES (1) ── (1..N) AGRUPACIÓN_MIEMBROS
```

Toda agrupación está formada por al menos un ayuntamiento miembro.

---

### BENEFICIARIOS — AGRUPACIONES (como representante)

```
BENEFICIARIOS (0..1) ── Representados por ── (1) AGRUPACIONES
```

Cada agrupación tiene exactamente un ayuntamiento que actúa como representante. Un beneficiario puede serlo de como máximo una agrupación.

---

### BENEFICIARIOS — AGRUPACIÓN MIEMBROS

```
BENEFICIARIOS (1) ── Integrados en ── (N) AGRUPACIÓN_MIEMBROS
```

Un mismo ayuntamiento puede figurar como miembro en distintas agrupaciones a lo largo de diferentes convocatorias.

---

### SOLICITUDES — SOLICITUD_CAUSAS — CAUSAS_EXCLUSIÓN *(fase futura)*

```
SOLICITUDES (1) ── Pueden tener ── (N) SOLICITUD_CAUSAS (N) ── (1) CAUSAS_EXCLUSIÓN
```

Una solicitud excluida puede tener varias causas, y una misma causa puede aplicarse a muchas solicitudes. Relación N:M resuelta mediante tabla puente. No implementada en el modelo físico actual.

---

## 6. Decisiones de diseño del modelo de datos

Durante el proceso de diseño se tomaron diversas decisiones para adaptar la estructura a las características reales de las fuentes de información, equilibrando normalización, facilidad de consulta y simplicidad de implementación.

---

### 6.1 Campo anio_convocatoria

Inicialmente el modelo solo contemplaba el campo `fecha_convocatoria`. Para análisis estadísticos y visualizaciones por año sería necesario usar `YEAR(fecha_convocatoria)`, lo que complica las consultas. Por ello se añadió el campo `anio_convocatoria` explícito, que simplifica filtros y facilita la generación de gráficos en el frontend.

---

### 6.2 Cinco estados posibles de una solicitud

El modelo contempla cuatro estados en lugar de los tres inicialmente previstos:

- `concedida`, `no_beneficiaria`, `excluida`, `desistida`

El estado `no_beneficiaria` no fue identificado en el diseño inicial: se añadió al analizar los datos reales del dataset unificado. Aplica a EELL en todos los años (admitidas pero fuera del cupo) y a EPA desde 2024 (no alcanzan la puntuación mínima). En EPA 2021–2023 el BOE denomina "denegadas" a solicitudes que en realidad tienen causa de exclusión formal, por lo que se reclasifican como `excluida` durante la unificación.

---

### 6.3 IDs sintéticos para registros EPA sin expediente

Algunos registros EPA anteriores a 2024 no incluyen número de expediente en los documentos oficiales. Para no descartarlos se generan identificadores sintéticos con el formato `SIN_EXP_YYYY_NNN`. Esto permite cargar todos los registros respetando la restricción UNIQUE del campo `num_expediente`.

---

### 6.4 Simplificación de las líneas de actuación (ENUM en lugar de tabla)

En el diseño conceptual inicial se incluyó una tabla **LINEAS_ACTUACION** para representar las distintas líneas de subvención (colonias felinas, protección animal, EELL).

Durante el desarrollo se tomó la decisión de **eliminar esta tabla** y sustituirla por un campo ENUM directamente en la tabla `concesiones`. El ENUM ha evolucionado en dos pasos:

**Versión inicial (diseño conceptual):** tres valores `colonias_felinas`, `proteccion_animal`, `eell`.

**Versión implementada (modelo físico actual):** dos valores:

```sql
linea ENUM('animales_abandonados', 'colonias_felinas') NULL
```

Los cambios respecto al diseño inicial son:
- `proteccion_animal` → renombrado a `animales_abandonados`, para reflejar la denominación exacta de la Orden modificada del 17 de mayo de 2024 (publicada en BOE el 29 de mayo de 2024), que crea dos líneas diferenciadas: *animales abandonados* y *gestión de colonias felinas*. Estas líneas aparecen por primera vez en la resolución EPA 2025.
- `eell` → eliminado. Las concesiones de entidades locales ya se identifican por `convocatorias.tipo_convoc = 'eell'`, por lo que añadir este valor al ENUM sería redundante.
- El campo es `NULL` para convocatorias anteriores a 2025 (EPA y todas las EELL), donde el BOE no desglosa por línea.

> **Mejora futura:** la resolución EPA 2024 (semestral, BOE-A-2024-23749) se publica tras la entrada en vigor de la Orden modificada del 29 de mayo de 2024, por lo que en teoría ya distingue entre las dos líneas. Sin embargo, el BOE de 2024 no desglosa la línea por entidad de forma directa en las tablas parseadas. Si en el futuro se revisa el parser de 2024 para extraer ese dato, el campo `linea` ya está preparado en el modelo para recibirlo.

**Justificación:** el número de líneas es reducido (2 valores), estable en el tiempo, y no requiere atributos adicionales. Mantener una tabla separada añadiría JOINs innecesarios sin aportar flexibilidad real. Esta simplificación se refleja en el diagrama ER definitivo, donde LINEAS_ACTUACION ya no aparece como entidad.

---

### 6.5 Campo tramo en concesiones

Las concesiones EELL 2025 incluyen un campo `tramo` que indica la banda de subvención asignada. Es específico de esa convocatoria y no aplica a las demás. Se incorpora directamente en `concesiones` como `TINYINT NULL`, en lugar de crear una subtabla o subtipo que complicase el modelo.

---

### 6.6 Causas de exclusión como fase futura

Los documentos oficiales indican que una solicitud puede ser excluida por varias causas (códigos numéricos). Almacenarlas como texto o JSON en `solicitudes` dificultaría consultas analíticas (causas más frecuentes, distribución por tipo, etc.).

Por ello se mantiene la estructura normalizada `causas_exclusion` + `solicitud_causas` en el **modelo conceptual**, representada en el diagrama con asterisco (*) y la nota "Tablas conceptuales. No se implementan en el modelo físico actual del proyecto por viabilidad técnica."

La implementación se pospone a una fase futura, ya que la extracción automática de causas desde los documentos oficiales requiere un trabajo de parsing adicional. **Estas tablas no están incluidas en `docker/init/modelo-fisico.sql`**: se añadirán en su momento junto con el script de carga de datos correspondiente.

> **Pendiente de validación:** el campo `causa_exclusion` del dataset JSON contiene los códigos capturados para las EELL (2023, 2024 y 2025), pero no han sido verificados sistemáticamente contra la fuente original (Excel de resoluciones). Esta validación se realizará cuando se implemente la carga de causas en la base de datos.

---

### 6.7 EPA y EELL unificadas en una única tabla de solicitudes

Los datos de convocatorias EPA y EELL comparten la misma estructura principal y se unifican en una única tabla `solicitudes`. La distinción se realiza a través de `convocatorias.tipo_convoc` (ENUM `epa` / `eell`). Esto simplifica las consultas transversales sin necesidad de JOINs adicionales.

---

### 6.8 Elección de MariaDB como sistema gestor de base de datos

Para la implementación física de la base de datos se optó por **MariaDB 11** en lugar de MySQL, por los siguientes motivos:

- Es el motor por defecto en distribuciones Linux (Ubuntu/Debian), lo que facilita el despliegue en entornos reales.
- Es compatible al 100 % con MySQL en sintaxis SQL, por lo que el script `modelo-fisico.sql` funciona en ambos sistemas sin modificaciones.
- Ofrece mejor rendimiento en operaciones de lectura intensiva y es de licencia totalmente libre.

La base de datos se despliega mediante **Docker Compose** con la imagen `mariadb:11.8`, expuesta en el puerto `3307` del host (para evitar conflictos con instalaciones locales de MySQL que usan el puerto 3306). El esquema se inicializa automáticamente al arrancar el contenedor a través del script `docker/init/modelo-fisico.sql`.

---

### 6.9 Arranque de la base de datos

La base de datos se despliega con Docker Compose desde la carpeta `docker/`. Los comandos imprescindibles, ejecutados desde el bash del proyecto, son:

```bash
# 1. Arrancar solo el contenedor de BD (el backend requiere imagen Python,
#    que puede fallar en entornos sin acceso a Docker Hub)
cd docker
docker compose up -d db

# 2. Verificar que el contenedor está en marcha y healthy
docker compose ps

# 3. Aplicar el schema (solo necesario si el volumen es nuevo o fue eliminado;
#    si el volumen ya existía con datos, omitir este paso)
docker exec -i bdns_dgda_db mariadb -uroot -proot < init/modelo-fisico.sql

# 4. Cargar el dataset unificado en la BD (desde la raíz del proyecto)
cd ..
python -m scripts.data_processing.cargar_dataset

# 5. Verificar los recuentos de la carga
docker exec bdns_dgda_db mariadb -uroot -proot bdns_dgda -e "
SELECT 'convocatorias'       AS tabla, COUNT(*) AS filas FROM convocatorias
UNION ALL SELECT 'beneficiarios',      COUNT(*) FROM beneficiarios
UNION ALL SELECT 'solicitudes',        COUNT(*) FROM solicitudes
UNION ALL SELECT 'concesiones',        COUNT(*) FROM concesiones
UNION ALL SELECT 'agrupaciones',       COUNT(*) FROM agrupaciones
UNION ALL SELECT 'agrupacion_miembros',COUNT(*) FROM agrupacion_miembros;"
```

Recuentos esperados tras la primera carga completa:

| Tabla | Filas |
|---|---|
| convocatorias | 8 |
| beneficiarios | 3103 |
| solicitudes | 6396 |
| concesiones | 2623 |
| agrupaciones | 13 |
| agrupacion_miembros | 72 |

> **Nota sobre el schema:** el script `docker-entrypoint-initdb.d` solo se ejecuta cuando el volumen Docker está vacío (primera creación). Si el contenedor se recrea con un volumen existente vacío, hay que aplicar el schema manualmente con el paso 3.

---

### 6.10 Pipeline de agrupaciones EELL 2025

Las agrupaciones de ayuntamientos de EELL 2025 requieren un tratamiento especial en todo el pipeline, ya que un único expediente agrupa varios municipios con importes individuales.

**Fuente de datos:** el archivo `data/raw/eell/2025/eell_2025_beneficiarias.xlsx` contiene dos hojas:

- **`Entidades_beneficiarias`** (40 filas): una por entidad beneficiaria. Incluye las columnas `¿Agrupación?` (Sí/No) y `Nº municipios`. Esta hoja es la única fuente para saber si una concesión es una agrupación.
- **`Municipios`** (99 filas): una por municipio miembro. Incluye NIF individual, nombre, expediente del representante e importe asignado a ese municipio. El ayuntamiento representante aparece como primera fila de su grupo.

**Por qué el representante aparece también como miembro:** el importe total de la concesión se divide entre todos los municipios de la agrupación, incluido el representante. Para que los importes individuales sumen el total de la concesión (diff=0.00 verificado en los 13 casos), el representante debe estar en `agrupacion_miembros` con su importe asignado propio.

**Propagación por el pipeline:**

1. `parser_eell_BOE_2025.py` — lee ambas hojas del xlsx y añade a cada registro concedido los campos `es_agrupacion` (bool) y `municipios_agrupacion` (lista de `{cif, nombre, importe_asignado}`).
2. `unificar_datasets.py` — propaga `es_agrupacion` y `municipios_agrupacion` al dataset unificado. Para todos los demás registros (EPA, EELL 2023/2024, no concedidas) estos campos son `False` / `null`.
3. `cargar_dataset.py` — paso 2 (beneficiarios) recorre también los `municipios_agrupacion` para insertar en `beneficiarios` los 36 municipios miembro que no tienen registro propio en el dataset. Sin este paso, las FK de `agrupacion_miembros` fallarían. Los pasos 5 y 6 insertan en `agrupaciones` y `agrupacion_miembros`.

**Cifras EELL 2025:**

| Tramo | Aytos. individuales | Agrupaciones | Municipios en agrup. | Total municipios |
|---|---|---|---|---|
| 1 | 16 | 6 | 22 | 38 |
| 2 | 3 | 6 | 39 | 42 |
| 3 | 8 | 1 | 11 | 19 |
| **Total** | **27** | **13** | **72** | **99** |

---

### 6.11 Campo periodo_meses en convocatorias

Las convocatorias EPA de 2023 y 2024 cubrieron un **periodo subvencionable semestral (6 meses)** en lugar del anual habitual (12 meses). Las convocatorias EELL tienen siempre periodo anual.

Esta diferencia es relevante para el análisis comparativo de importes: los importes concedidos en 2023 y 2024 (EPA) corresponden a 6 meses de actividad, por lo que no son directamente comparables con los de otros años sin normalizar.

En el dataset JSON unificado se añade el campo `periodo_meses` (entero: 6 o 12) a todos los registros. En el modelo relacional, este campo está implementado en la tabla `convocatorias` como `TINYINT NOT NULL DEFAULT 12`, lo que permite filtrarlo en consultas analíticas sin necesidad de lógica en el frontend.

Contexto normativo: el 17 de mayo de 2024 se modifica la Orden sobre las Bases reguladoras de las subvenciones EPA (publicada en BOE el 29 de mayo 2024). Entre otros cambios, se crean dos líneas diferenciadas: animales abandonados y gestión de colonias felinas. Estas líneas aparecen por primera vez en la resolución de 2025.

---

### 6.12 Deduplicación por (tipo, num_expediente, anio)

Durante la unificación del dataset se detectaron casos en que el mismo número de expediente aparecía en más de un año:

- Entidades que desistieron en una convocatoria y volvieron a solicitar al año siguiente (ej: SUBV2022659 excluida en 2022, concedida en 2023).
- Un número de expediente reutilizado por error en el BOE en dos años distintos (SUBV2022021).
- Un mismo expediente publicado dos veces dentro del mismo año en distintos anexos (SUBV2022271, Peludosos: concedida con importe en un anexo y denegada sin importe en otro).

La clave de deduplicación se cambió de `(tipo, num_expediente)` a `(tipo, num_expediente, anio)`, donde `anio` es siempre el año del fichero fuente (año de la convocatoria), no el que codifica el número de expediente. Esto permite conservar los registros legítimamente distintos (misma entidad en años distintos) y eliminar solo los duplicados reales (misma entidad, mismo expediente, mismo año).

Adicionalmente, para los duplicados intra-año se aplica una regla de prioridad: si uno de los registros tiene importe > 0 y el otro tiene importe = 0, se conserva el que tiene importe (la concedida real). Esto resuelve el caso de SUBV2022271, donde el registro correcto es el concedida con importe 2.560,77 €.

---

## 7. Diagrama entidad–relación del modelo

El diagrama ER ha evolucionado a lo largo del proyecto para reflejar las decisiones de diseño tomadas durante el análisis de los datos reales. A continuación se muestran las dos versiones con los cambios realizados.

---

### 7.1 Diagrama inicial

El primer diagrama fue elaborado en la fase de análisis inicial, antes de procesar el dataset completo. Incluía todas las entidades identificadas conceptualmente, entre ellas LINEAS_ACTUACION como tabla independiente y las entidades de causas de exclusión conectadas al modelo principal.

![Diagrama ER inicial](img/modelo-datos-er-v1.png)

---

### 7.2 Diagrama definitivo

El diagrama definitivo refleja el modelo implementado realmente, con todas las simplificaciones y ajustes derivados del análisis de los datos.

![Diagrama ER definitivo](img/Modelo-ER-Def.jpg)

---

### 7.3 Cambios entre versiones

Los principales cambios entre el diagrama inicial y el definitivo son:

**Entidades eliminadas o simplificadas:**
- **LINEAS_ACTUACION** desaparece como entidad independiente. Pasa a ser un campo ENUM dentro de `concesiones` (ver decisión 6.4).

**Entidades marcadas como fase futura:**
- **CAUSAS_EXCLUSIÓN** y **SOLICITUD_CAUSAS** se mantienen en el diagrama con asterisco (*) y trazo diferenciado, indicando que forman parte del diseño conceptual pero no están implementadas en el modelo físico actual (ver decisión 6.6).

**Relaciones añadidas o corregidas:**
- Se añaden los rombos **"Representados por"** e **"Integrados en"** para las relaciones entre BENEFICIARIOS y las entidades de agrupaciones, que en el diagrama inicial no estaban etiquetadas.
- Se corrigen cardinalidades en la relación BENEFICIARIOS–AGRUPACIONES: cada agrupación tiene exactamente **1** representante (no N).

**Estados de solicitud:**
- Se añade el estado **no_beneficiaria**, no contemplado en el diseño inicial pero presente en los datos reales.
- Se elimina **denegada** del modelo: en EPA 2021–2023 equivale a `excluida` (causa formal), en EPA 2024–2025 equivale a `no_beneficiaria` (puntuación insuficiente). La reclasificación se aplica en `unificar_datasets.py`.

---

## 8. Herramientas utilizadas para el diseño del modelo

### diagrams.net (draw.io)

Herramienta principal utilizada para el diseño conceptual del modelo. Permite crear diagramas ER de forma visual con entidades, relaciones y conectores. Entre sus ventajas destacan el uso gratuito, el funcionamiento online y la posibilidad de exportar en PNG o JPG. Tanto el diagrama inicial como el definitivo han sido elaborados con esta herramienta.

### dbdiagram.io

Herramienta complementaria útil para generar diagramas a partir de una definición textual de las tablas. Permite visualizar rápidamente las relaciones entre tablas a partir del script SQL del modelo físico (`modelo-fisico.sql`), lo que facilita validar la estructura antes de implementarla.
