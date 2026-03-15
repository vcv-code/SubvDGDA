# Análisis de subvenciones de bienestar animal (BDNS + DGDA)

Proyecto intermodular de **2º FPGS Desarrollo de Aplicaciones Web (DAW)**.

Consiste en el desarrollo de una **plataforma web para analizar subvenciones públicas relacionadas con bienestar animal en España**, centralizando información actualmente dispersa y permitiendo su consulta, filtrado y visualización a partir de datos abiertos y documentos oficiales.

---

## Objetivos del proyecto

El sistema permitirá:

- centralizar información de subvenciones públicas
- consultar convocatorias y beneficiarios
- aplicar filtros por año, territorio y tipo de beneficiario
- mostrar resultados en tablas
- generar gráficos de análisis
- ofrecer información útil a entidades que quieran solicitar subvenciones

El proyecto busca facilitar el análisis y comprensión de las políticas públicas de bienestar animal a partir de datos abiertos.

---

## Documentación técnica

La documentación detallada del proyecto se encuentra en la carpeta `docs`.

- [Análisis de la API BDNS](docs/api-bdns.md)
- [Modelo de datos del sistema](docs/modelo-datos.md)

---

## Arquitectura prevista del sistema

El sistema sigue una arquitectura cliente–servidor basada en una API REST:

```
API externa BDNS + PDFs oficiales
      ↓
Backend Python
      ↓
Base de datos MySQL / MariaDB
      ↓
API propia
      ↓
Frontend
```

---

## Modelo de datos (diagrama ER)

El modelo de datos del sistema se describe en detalle en la documentación técnicase y se ha diseñado para permitir análisis estadísticos sobre subvenciones públicas, como evolución de financiación por año, entidades con mayor financiación o causas más frecuentes de exclusión.

![Modelo de datos](docs/img/modelo-datos-er.png)

---

## Tecnologías 

| Área | Tecnologías |
|-----|-------------|
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Backend | Python, API REST |
| Base de datos | MySQL / MariaDB |
| Infraestructura | Docker, Nginx |
| Control de versiones | Git, GitHub |
| Fuentes de datos | API BDNS, PDFs oficiales |

### Frontend

El frontend permitirá explorar los datos mediante filtros y visualizaciones.

### Backend

El backend será responsable de:

- consultar APIs externas
- procesar los datos
- almacenarlos en base de datos
- exponerlos al frontend mediante una API

### Base de datos

Se almacenarán:

- convocatorias
- concesiones
- beneficiarios
- importes
- metadatos de las subvenciones

### Infraestructura

La aplicación se desplegará mediante contenedores Docker y un servidor Nginx como proxy inverso.

---

## Fuentes de datos analizadas

Los datos se obtienen de fuentes externas, se procesan y almacenan para permitir su análisis y visualización.

### Base de Datos Nacional de Subvenciones (BDNS)

Documentación oficial:

https://www.infosubvenciones.es/bdnstrans/doc

Endpoints explorados:

- `/convocatorias/busqueda`
- `/concesiones/busqueda`

---

### Líneas de subvención analizadas

**Subvenciones a entidades de protección animal**

Convocatorias identificadas en BDNS desde **2021 en adelante**.

**Subvenciones a entidades locales para la gestión de colonias felinas**

Convocatorias identificadas desde **2023 en adelante**.

---

### Resultados de la investigación inicial

Las convocatorias aparecen correctamente en la API.

Sin embargo, las **concesiones de la Dirección General de Derechos de los Animales (DGDA)** no aparecen en el endpoint público, aunque existen resoluciones oficiales con beneficiarios.

En cambio, las concesiones de **otras administraciones (locales y autonómicas)** sí aparecen en la API.

Esto implica que la API pública **no contiene toda la información necesaria para el análisis**.

---

### Datos disponibles en los PDFs oficiales

Como alternativa, se prevé utilizar los **PDFs de resoluciones publicados en la página web oficial de la DGDA**, que contienen tablas estructuradas con información detallada.

#### Datos de asociaciones

Los campos incluyen:

- CIF
- expediente
- entidad
- línea de actuación
- puntuación
- importe concedido

#### Datos de entidades locales

Los campos incluyen:

- NIF
- expediente
- entidad local
- porcentaje de cofinanciación
- número de actuaciones
- puntuación
- importe concedido

En algunos casos aparecen **agrupaciones de entidades con reparto de importes**.

---

## Estrategia técnica prevista

Debido a las limitaciones de la API BDNS, la estrategia técnica prevista es **combinar dos fuentes de datos**.

```
API BDNS
   ↓
obtener convocatorias
   ↓
detectar documentos PDF asociados
   ↓
extraer tablas de los PDFs
   ↓
convertir a JSON
   ↓
guardar en base de datos
   ↓
mostrar resultados en frontend
```

Esto permitirá construir un **dataset estructurado de beneficiarios y concesiones**.

---

## Herramientas para extracción de PDF

Se evaluarán diferentes librerías de Python para extraer tablas:

- `tabula-py`
- `camelot`
- `pdfplumber`

La elección dependerá de cuál funcione mejor con las tablas de las resoluciones.

---

## Estructura provisional del proyecto

```
backend/
    api/            # endpoints de la API
    services/       # lógica de negocio
    models/         # modelos de datos

frontend/
    js/             # scripts del frontend
    css/            # estilos
    assets/         # imágenes y recursos

data/
    raw/            # datos originales descargados
    processed/      # datos procesados

scripts/
    ingestion/      # descarga de datos desde BDNS
    pdf_extraction/ # extracción de datos de PDFs

docs/
    img/            # diagramas e imágenes de la documentación

docker/
    configuración de contenedores
```

Descripción general:

- **backend/** → lógica del servidor y API
- **frontend/** → interfaz web
- **data/** → datos descargados o procesados
- **scripts/** → scripts de obtención y procesamiento de datos
- **docs/** → documentación técnica del proyecto
- **docker/** → configuración de contenedores

---

## Estado actual del proyecto

Fase actual: **análisis de fuentes de datos y diseño del modelo de datos del sistema**.

Se ha confirmado que:

- la API BDNS funciona correctamente
- las convocatorias están disponibles
- las concesiones de la DGDA no aparecen en el endpoint público
- los datos de beneficiarios existen en PDFs estructurados

Por tanto, el proyecto probablemente requerirá **combinar datos de la API BDNS con extracción de información de PDFs**.

### Datos de ejemplo de la API

Para facilitar el desarrollo y análisis inicial de la API BDNS se han incluido algunos ejemplos de respuestas JSON en:

```
data/raw/
```

Estos archivos contienen respuestas reales de la API correspondientes a convocatorias de subvenciones relacionadas con bienestar animal.

Actualmente se incluyen ejemplos de:

- convocatorias de subvenciones a entidades de protección animal
- convocatorias de subvenciones a entidades locales para gestión de colonias felinas
- una convocatoria individual utilizada para analizar la estructura completa de la respuesta de la API

Estos datos se utilizan como referencia para el análisis del modelo de datos y el desarrollo del backend.

---

## Desarrollo

Clonar el repositorio:

```bash
git clone git@github.com:vcv-code/analisis-bdns-dgda.git
cd analisis-bdns-dgda
```

Crear rama de desarrollo:

```bash
git checkout -b dev
git push -u origin dev
```

Flujo de trabajo:

```
main
dev
feature/*
```

---

## Gestión del proyecto

La planificación y seguimiento de tareas se realiza mediante **GitHub Projects**.

Las funcionalidades y tareas de desarrollo se registran como **Issues**, que posteriormente se organizan en un tablero tipo Kanban con columnas como:

- Backlog
- To do
- In progress
- Review
- Done

Cada funcionalidad o investigación se desarrolla en una rama `feature/*` y posteriormente se integra en la rama `dev` mediante Pull Requests.