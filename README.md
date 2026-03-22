# Análisis de subvenciones de bienestar animal (BDNS + DGDA)

Proyecto intermodular de **2º FPGS Desarrollo de Aplicaciones Web (DAW)**.

---

## Autores

Proyecto desarrollado por:

- Miyuki Salvador
- Verónica Corpa

---

## Objetivos del proyecto

El proyecto consiste en el desarrollo de una **plataforma web para analizar subvenciones públicas relacionadas con bienestar animal en España**, centralizando información actualmente dispersa y permitiendo su consulta, filtrado y visualización a partir de datos abiertos y documentos oficiales.

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

<p align="center">
  <a href="docs/img/modelo-datos-er.png">
    <img src="docs/img/modelo-datos-er.png" width="750">
  </a>
</p>

---

## Tecnologías 

| Área | Tecnologías |
|-----|-------------|
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Backend | Python |
| Base de datos | MySQL / MariaDB |
| Infraestructura | Docker, Nginx |
| Control de versiones | Git, GitHub |
| Fuentes de datos | API BDNS, PDFs oficiales |

---

## Descripción general del proyecto

- **backend/** → lógica del servidor y API  
- **frontend/** → interfaz web  
- **data/** → datos descargados o procesados  
- **scripts/** → scripts de obtención y procesamiento de datos  
- **docs/** → documentación técnica del proyecto  
- **docker/** → configuración de contenedores  

### Frontend

Permitirá explorar los datos mediante filtros y visualizaciones.

### Backend

Responsable de:

- consultar APIs externas  
- procesar los datos  
- almacenarlos en base de datos  
- exponerlos mediante API  

### Base de datos

Almacenará:

- convocatorias  
- concesiones  
- beneficiarios  
- importes  
- metadatos  

---

## Fuentes de datos analizadas

### API BDNS

https://www.infosubvenciones.es/bdnstrans/doc  

Endpoints:

- `/convocatorias/busqueda`  
- `/concesiones/busqueda`  

---

### Líneas analizadas

- **Protectoras (EPA)** → desde 2021  
- **Entidades locales (EELL)** → desde 2023  

---

### Limitación detectada

Las concesiones de la **DGDA no aparecen en la API pública**, aunque sí existen en resoluciones oficiales.

👉 Esto obliga a usar PDFs como fuente principal.

---

## PDFs oficiales (DGDA)

Contienen:

- beneficiarios  
- puntuaciones  
- importes  
- estados  

### Datos de asociaciones (EPA)

- CIF  
- expediente  
- entidad  
- puntuación  
- importe  

### Datos de entidades locales (EELL)

- NIF  
- expediente  
- entidad  
- puntuación  
- importe  

Existen agrupaciones de entidades sin desglose individual de importe.

---

## Estrategia técnica

```
API BDNS
↓
Convocatorias
↓
Relación con PDFs
↓
Datos completos
```

Nota:
La API BDNS proporciona información de convocatorias, pero no incluye los beneficiarios reales de las subvenciones de la DGDA.  
Por ello, se utiliza un pipeline adicional basado en PDFs oficiales para reconstruir los datos completos de concesiones.

### Pipeline real implementado (EELL)

```
XML / PDF (DGDA)
↓
Parsing (pdfplumber / BeautifulSoup)
↓
JSON por año (data/processed/)
↓
Correcciones manuales (Excel 2025)
↓
Merge por número de expediente
↓
Dataset unificado (data/final/)
```

---

## Procesamiento de datos

### Entidades Locales (EELL)

- 2023 → PDF  
- 2024 → PDF  
- 2025 → XML BOE  

Scripts:

- `parser_eell_base.py`  
- `parser_eell_2025.py`  

---

### Entidades de Protección Animal (EPA)

- 2021  
- 2022  
- 2023 (caso especial)  
- 2024  
- 2025  

Arquitectura:

- `parser_epa_base.py` → lógica común  
- `parser_epa_2021_22_24_25.py` → parser general  
- `parser_epa_2023.py` → parser específico  

---

## Herramientas de extracción

Se utiliza:

- `pdfplumber`

Alternativas evaluadas:

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

- filas partidas  
- importes mal parseados  
- valores null  

Soluciones:

- limpieza de texto  
- normalización  
- conversión de datos  

#### XML BOE 2025

Problemas:

- sin importes  
- inconsistencia nif/cif  
- sin estado  

Soluciones:

- parsing con BeautifulSoup  
- unificación de campo `cif`  
- `"estado": "concedida"`  

#### Integración Excel

Problema:

- importes manuales  

Solución:

- Excel + merge por expediente  

#### CIF

Problemas:

- `"None"` como string  
- ausencias  

Solución:

- `limpiar_cif()`  
- normalización a `null`  

#### Estado

Problema:

- valores null  

Solución:

- inclusión en parsers  
- normalización  

---

## Validación de datos

Se han implementado controles automáticos:

- conteo por año  
- conteo por estado  
- detección de CIF faltantes  
- eliminación de duplicados (año + expediente)  

Ejemplo:

- Registros por año: `{2023: 592, 2024: 1138, 2025: 991}`  
- Registros por estado: `{'concedida': 2721}`  

Estos controles permiten garantizar la calidad del dataset antes de su integración en la base de datos y su uso en la aplicación.

---

## Dataset final

Campos:

- año  
- expediente  
- CIF/NIF  
- entidad  
- puntuación  
- importe  

Características:

- normalizado  
- sin duplicados  
- consistente  
- trazable  

Total de registros: 2721

---

## Organización del proyecto y pipeline de datos

Se ha reorganizado el proyecto siguiendo una arquitectura típica de ingeniería de datos:

```
data/
  raw/        → datos originales
  processed/  → datos transformados
  final/      → dataset unificado
```

Separación por fuentes:

- `eell/` → entidades locales  
- `epas/` → protección animal  
- `convBDNS/` → API BDNS  

Esto permite:

- evitar mezclar fuentes  
- facilitar debugging  
- mejorar trazabilidad  

---

## Estructura del proyecto

```
data/
  raw/
    eell/
    epas/
    convBDNS/
  processed/
    eell/
    epas/
  final/
    dataset_unificado.json

scripts/
    ingestion/
    pdf_extraction/
    data_processing/

backend/
frontend/
docs/
docker/
```

---

## Scripts principales

### BDNS

`scripts/ingestion/bdns_client.py`

### PDF extracción

`scripts/pdf_extraction/`

### Procesamiento

`scripts/data_processing/`

---

## Estado actual

Fase: **procesamiento de datos EELL completado**

✔ parsing PDF  
✔ parsing XML  
✔ limpieza  
✔ dataset unificado  

En progreso:

- validación de EPAs  

Pendiente:

- base de datos  
- API  
- frontend  

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

Sincronizar repositorio:
```bash
git checkout dev
git pull
```

---

## Entorno de trabajo

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Flujo de trabajo

```
main → estable  
dev → desarrollo  
feature/* → funcionalidades  
```

---

## Gestión del proyecto

La planificación y seguimiento de tareas se realiza mediante **GitHub Projects** con metodología Kanban. 

Las funcionalidades y tareas de desarrollo se registran como **Issues**, que posteriormente se organizan en un tablero tipo Kanban con columnas como: 

- Backlog 
- To do 
- In progress 
- Review 
- Done 

Cada funcionalidad o investigación se desarrolla en una rama feature/* y posteriormente se integra en la rama dev mediante Pull Requests.

---

## Notas técnicas

- data/raw/ no se versiona completo
- se mantienen ejemplos
- los scripts sobrescriben resultados
- sistema reproducible
