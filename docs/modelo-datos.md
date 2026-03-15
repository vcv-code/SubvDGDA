# Modelo de datos del sistema

## 1. Introducción

En esta fase del proyecto se ha diseñado el modelo de datos que permitirá almacenar y analizar la información obtenida a partir de las distintas fuentes utilizadas en la aplicación.

Las fuentes principales de datos son:

- La API de la Base de Datos Nacional de Subvenciones (BDNS), que proporciona información sobre convocatorias.
- Los documentos oficiales publicados por la Dirección General de los Derechos de los Animales (DGDA), que contienen información detallada sobre solicitudes, concesiones y exclusiones.

A partir del análisis de estas fuentes se ha diseñado un modelo relacional que representa las diferentes entidades implicadas en el proceso administrativo de concesión de subvenciones.

---

## 2. Fuentes de datos analizadas

### API BDNS

La API oficial de la Base de Datos Nacional de Subvenciones permite consultar información estructurada sobre convocatorias públicas.

Entre los campos más relevantes analizados se encuentran:

- numeroConvocatoria
- descripcion
- fechaRecepcion
- organoConvocante

Estos datos permiten identificar las convocatorias relacionadas con subvenciones de bienestar animal y utilizarlas como base para el modelo de datos.

### Documentos oficiales (PDF)

La información publicada por la Dirección General de los Derechos de los Animales se presenta en forma de documentos PDF que incluyen tablas con información detallada sobre:

- solicitudes presentadas
- solicitudes admitidas
- solicitudes excluidas
- concesiones definitivas
- entidades beneficiarias

Estos documentos contienen información que no aparece estructurada en la API BDNS y que resulta necesaria para realizar análisis más completos.

---

## 3. Proceso de transformación de los datos

El diseño del modelo de datos se ha realizado a partir del análisis de los datos disponibles y siguiendo un proceso de transformación desde la información original hacia un modelo relacional.

Este proceso se ha desarrollado en tres pasos principales:

1. Identificación de las entidades principales presentes en los datos.
2. Identificación de las relaciones entre dichas entidades.
3. Conversión de las entidades y relaciones en tablas de una base de datos relacional.

## 4. Entidades principales del modelo de datos

A partir del análisis de los datos obtenidos de la API BDNS y de los documentos oficiales en formato PDF, se identificaron las principales entidades implicadas en el proceso de concesión de subvenciones.

Estas entidades representan los distintos elementos del procedimiento administrativo y permiten estructurar la información en una base de datos relacional.

Las entidades principales identificadas son:

- Convocatorias
- Beneficiarios
- Solicitudes
- Concesiones
- Líneas de actuación
- Agrupaciones de entidades locales
- Miembros de agrupaciones
- Causas de exclusión

A continuación se describe cada una de estas entidades.

---

### 4.1 Convocatorias

La entidad **Convocatorias** representa cada convocatoria oficial de subvenciones publicada por la administración pública.

La información sobre convocatorias se obtiene principalmente a través de la API de la Base de Datos Nacional de Subvenciones (BDNS).

Cada convocatoria puede recibir múltiples solicitudes por parte de entidades interesadas.

Campos principales:

- id_convoc (PK)
- num_convoc
- titulo_convoc
- fecha_convocatoria
- anio_convocatoria
- estado_subv
- fecha_resolucion

El campo `titulo_convoc` corresponde al campo **descripcion** devuelto por la API.

El campo `anio_convocatoria` se añade de forma explícita para facilitar consultas estadísticas y la generación de gráficos de evolución temporal en el frontend.

---

### 4.2 Beneficiarios

La entidad **Beneficiarios** representa las entidades que solicitan las subvenciones.

Estas entidades pueden ser principalmente de dos tipos:

- asociaciones de protección animal
- entidades locales (ayuntamientos)

Campos principales:

- id_benef (PK)
- cif_benefic
- nombre_benefic
- tipo_benefic

Un beneficiario puede presentar varias solicitudes en distintas convocatorias.

---

### 4.3 Solicitudes

La entidad **Solicitudes** representa cada solicitud presentada por una entidad para participar en una convocatoria de subvenciones.

Cada solicitud está asociada a una convocatoria concreta y a una entidad beneficiaria.

Campos principales:

- id_solic (PK)
- id_convoc (FK)
- id_benef (FK)
- estado_solicitud
- num_exped
- puntuacion
- fecha_solicitud

Los valores posibles del campo `estado_solicitud` incluyen:

- concedida
- denegada
- excluida
- desistida

---

### 4.4 Concesiones

La entidad **Concesiones** representa las subvenciones que finalmente han sido concedidas.

Solo existe una concesión cuando la solicitud correspondiente ha sido aprobada.

Campos principales:

- id_conces (PK)
- id_soli (FK)
- id_linea (FK)
- importe_conced

Cada concesión está asociada a una solicitud concreta.

---

### 4.5 Líneas de actuación

Las subvenciones analizadas se agrupan en distintas **líneas de actuación**.

En el caso de las subvenciones estudiadas se identifican principalmente dos líneas:

- gestión de colonias felinas
- atención a animales abandonados

Se puede representar mediante una tabla específica:

Campos:

- id_linea (PK)
- codigo_linea
- nombre_linea

Sin embargo, dado que el número de valores es reducido y estable, en la implementación final también sería posible simplificar este modelo utilizando un campo ENUM en la tabla de concesiones.

---

### 4.6 Agrupaciones de entidades locales

En determinadas convocatorias, especialmente en el caso de subvenciones dirigidas a entidades locales, las solicitudes pueden presentarse en forma de **agrupaciones de ayuntamientos**.

Estas agrupaciones tienen una entidad representante y varios miembros.

Campos principales:

- id_agrup (PK)
- id_conces (FK)
- id_represent (FK)
- cofinanciacion
- num_actuaciones

La entidad representante corresponde a uno de los beneficiarios que actúa como coordinador de la agrupación.

---

### 4.7 Miembros de agrupación

La entidad **Miembros de agrupación** representa los ayuntamientos que forman parte de una agrupación.

Campos principales:

- id_agrupM (PK)
- id_agrup (FK)
- id_benefic (FK)
- importe_conced

Esto permite modelar correctamente las subvenciones compartidas entre varias entidades.

---

### 4.8 Causas de exclusión

Las solicitudes que no cumplen los requisitos establecidos pueden ser excluidas por distintos motivos.

Estos motivos se recogen en un catálogo de **causas de exclusión**.

Campos:

- id_causa (PK)
- descrip_exclu

---

### 4.9 Relación entre solicitudes y causas de exclusión

Una misma solicitud puede estar asociada a varias causas de exclusión.

Para representar esta relación se utiliza una tabla intermedia.

Tabla: **Solicitud_causas**

Campos:

- id_soli (FK)
- id_causa (FK)

Clave primaria compuesta:

- (id_soli, id_causa)

Este modelo permite representar una relación de tipo **muchos a muchos** entre solicitudes y causas de exclusión.

## 5. Relaciones entre entidades

Una vez identificadas las entidades principales del sistema, se definieron las relaciones existentes entre ellas. Estas relaciones reflejan el funcionamiento real del proceso administrativo de concesión de subvenciones.

### Convocatorias y solicitudes

CONVOCATORIAS 1 ─── N SOLICITUDES

Una convocatoria puede recibir múltiples solicitudes presentadas por distintas entidades.

Cada solicitud pertenece únicamente a una convocatoria concreta.

---

### Beneficiarios y solicitudes

BENEFICIARIOS 1 ─── N SOLICITUDES

Una misma entidad puede presentar varias solicitudes en diferentes convocatorias.

Cada solicitud pertenece a un único beneficiario.

---

### Solicitudes y concesiones

SOLICITUDES 1 ─── 0..1 CONCESIONES

Una solicitud puede terminar en concesión o no.

Si la solicitud es aprobada se genera una concesión; en caso contrario puede quedar como denegada, excluida o desistida.

---

### Líneas de actuación y concesiones

LINEAS_ACTUACION 1 ─── N CONCESIONES

Cada concesión está asociada a una única línea de actuación.

Una misma línea puede tener múltiples concesiones dentro de una convocatoria.

---

### Concesiones y agrupaciones

CONCESIONES 1 ─── 0..1 AGRUPACIONES

En determinadas subvenciones dirigidas a entidades locales, las concesiones pueden corresponder a agrupaciones de ayuntamientos.

En estos casos se registra la agrupación asociada a la concesión.

---

### Agrupaciones y miembros de agrupación

AGRUPACIONES 1 ─── 1..N AGRUPACION_MIEMBROS

Cada agrupación está formada por varios ayuntamientos.

Aunque en la práctica el número mínimo de miembros suele ser dos, en el modelo se define la relación como 1..N para mantener flexibilidad en el diseño.

---

### Beneficiarios y miembros de agrupación

BENEFICIARIOS 1 ─── N AGRUPACION_MIEMBROS

Un mismo ayuntamiento puede participar en distintas agrupaciones en diferentes convocatorias o años.

---

### Solicitudes y causas de exclusión

SOLICITUDES N ─── N CAUSAS_EXCLUSION

Una solicitud puede estar asociada a varias causas de exclusión.

A su vez, una misma causa de exclusión puede aplicarse a múltiples solicitudes.

Esta relación se implementa mediante la tabla intermedia **Solicitud_causas**, que contiene las claves foráneas de ambas entidades.

## 6. Decisiones de diseño del modelo de datos

Durante el proceso de diseño del modelo de datos se tomaron diversas decisiones para adaptar la estructura de la base de datos a las características reales de las fuentes de información utilizadas en el proyecto.

Estas decisiones buscan equilibrar la normalización de los datos, la facilidad de consulta y la simplicidad de implementación del sistema.

---

### 6.1 Campo año_convocatoria

Inicialmente el modelo solo contemplaba el campo `fecha_convocatoria`. Sin embargo, para realizar análisis estadísticos y generar visualizaciones por año (por ejemplo, evolución de subvenciones entre 2021 y 2025) sería necesario utilizar funciones como:
```
YEAR(fecha_convocatoria)
```

Esto complica las consultas y puede afectar al rendimiento cuando se realizan agregaciones o filtros por año.

Por este motivo se decidió añadir el campo `anio_convocatoria`, que permite realizar consultas más simples y facilita la generación de gráficos en el frontend mediante librerías como Chart.js.

---

### 6.2 Estados de la convocatoria

Las convocatorias de subvenciones pasan por diversas fases administrativas, como por ejemplo:

- apertura de solicitudes
- subsanaciones
- listas provisionales
- listas definitivas
- resolución de concesiones
- justificación de subvenciones

Sin embargo, esta información no se encuentra estructurada en la API BDNS y suele aparecer únicamente en documentos administrativos publicados en formato PDF.

Automatizar la detección de estos estados requeriría un sistema de scraping documental que analizara continuamente nuevas publicaciones en el BOE o en la web de la Dirección General de los Derechos de los Animales.

Dado que este proceso excede el alcance del proyecto, se plantea utilizar un modelo simplificado del estado de la convocatoria o incluso calcularlo dinámicamente desde el backend.

Por ejemplo:

- si existe resolución → convocatoria resuelta
- si no existe resolución → convocatoria abierta

---

### 6.3 Código y fecha de concesión

En algunos documentos oficiales aparece información como el código de concesión o la fecha de publicación de la resolución en el BOE.

Sin embargo, estos datos no resultan esenciales para los objetivos de análisis del proyecto y su inclusión complicaría innecesariamente el modelo.

Por este motivo se decidió no incorporar inicialmente campos como `cod_conces` o `fecha_concesion`.

---

### 6.4 Representación de las líneas de actuación

Las subvenciones analizadas incluyen un número reducido de líneas de actuación, principalmente relacionadas con:

- gestión de colonias felinas
- atención a animales abandonados

En el diseño conceptual del modelo se incluyó una tabla específica para representar estas líneas de actuación.

No obstante, en la implementación final podría simplificarse este diseño utilizando un campo `ENUM` dentro de la tabla de concesiones, ya que el número de valores posibles es limitado y estable.

---

### 6.5 Representación de las causas de exclusión

En los documentos PDF oficiales se indica que una solicitud puede estar excluida por varias causas, representadas mediante códigos numéricos.

Una posible simplificación habría sido almacenar estas causas directamente como texto o como un campo JSON dentro de la tabla de solicitudes.

Por ejemplo: "16,18,19" o [16,18,19]


Sin embargo, esta aproximación dificultaría la realización de consultas analíticas, como por ejemplo identificar cuáles son las causas de exclusión más frecuentes.

Por este motivo se optó por mantener una estructura normalizada mediante las tablas:

- `causas_exclusion`
- `solicitud_causas`

Esto permite modelar correctamente una relación muchos a muchos y facilita el análisis posterior de los datos.

## 7. Diagrama entidad–relación del modelo

A partir de las entidades identificadas y de las relaciones definidas entre ellas se elaboró un diagrama entidad–relación (ER) que representa la estructura general del modelo de datos del sistema.

Este diagrama permite visualizar de forma clara las entidades principales del modelo, sus atributos y las relaciones existentes entre ellas, sirviendo como base conceptual para la posterior implementación de la base de datos relacional.

El modelo representa el flujo administrativo de una convocatoria de subvenciones, desde la publicación de la convocatoria hasta la resolución de concesiones, incluyendo las solicitudes presentadas por las entidades, las posibles agrupaciones de ayuntamientos y las causas de exclusión.

En el diagrama se incluyen las siguientes entidades principales:

- Convocatorias
- Beneficiarios
- Solicitudes
- Concesiones
- Líneas de actuación
- Agrupaciones
- Miembros de agrupación
- Causas de exclusión
- Solicitud_causas

Cabe destacar que la entidad **Líneas de actuación** se mantiene en el diagrama con un propósito conceptual y académico, ya que permite representar explícitamente la relación entre las subvenciones concedidas y la línea de actuación correspondiente.

No obstante, dado que el número de líneas de actuación es reducido y estable, en la implementación final del sistema podría simplificarse mediante el uso de un campo ENUM dentro de la tabla de concesiones.

### Diagrama entidad–relación

![Diagrama entidad-relación del modelo de datos](img/modelo-datos-er.png)

## 8. Herramientas utilizadas para el diseño del modelo

Para el diseño del modelo de datos y la elaboración del diagrama entidad–relación se utilizaron distintas herramientas especializadas en modelado de bases de datos.

### diagrams.net (draw.io)

La herramienta principal utilizada para el diseño conceptual del modelo fue **diagrams.net (draw.io)**.

Esta herramienta permite crear diagramas de forma visual mediante el uso de entidades, relaciones y conectores, facilitando la representación gráfica del modelo de datos.

Entre sus principales ventajas destacan:

- uso gratuito
- funcionamiento online
- facilidad de uso
- disponibilidad de plantillas para diagramas ER
- posibilidad de exportar los diagramas en formatos como PNG o PDF

El diagrama entidad–relación incluido en esta documentación fue elaborado utilizando esta herramienta.

### dbdiagram.io

Otra herramienta útil para el diseño de modelos de bases de datos es **dbdiagram.io**, que permite generar diagramas a partir de una definición textual de las tablas.

Esta herramienta resulta especialmente útil cuando el modelo ya se encuentra definido a nivel lógico y se desea generar rápidamente un diagrama de las relaciones entre tablas.

### MySQL Workbench

Una vez implementada la base de datos, es posible utilizar **MySQL Workbench** para generar automáticamente un diagrama entidad–relación a partir de las tablas existentes.

Esta funcionalidad, denominada *Reverse Engineering*, permite visualizar gráficamente la estructura real de la base de datos, incluyendo:

- tablas
- atributos
- claves primarias
- claves foráneas
- relaciones entre tablas

Este tipo de diagramas resulta especialmente útil para documentar la estructura final del sistema.
