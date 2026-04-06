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

## Modelo de datos (comparativa diagramas ER)

<table align="center">
  <tr>
    <th>Original</th>
    <th>Revisado</th>
  </tr>
  <tr>
    <td><img src="docs/img/modelo-datos-er-v1.png" width="400"></td>
    <td><img src="docs/img/Modelo-ER-Def.jpg" width="400"></td>
  </tr>
</table>

---

## Tecnologías 

| Área | Tecnologías |
|-----|-------------|
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Backend | Python |
| Base de datos | MySQL / MariaDB |
| Infraestructura | Docker, Nginx |
| Control de versiones | Git, GitHub |
| Fuentes de datos | API BDNS, XML BOE, PDFs oficiales (DGDA) |

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

👉 Esto obliga a usar los documentos oficiales del BOE (XML y PDF) como fuente principal.

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

### Pipeline real implementado

```
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
Carga en base de datos (cargar_dataset.py)
  · 6 pasos: convocatorias → beneficiarios → solicitudes
             → concesiones → agrupaciones → agrupacion_miembros
  · Los municipios miembro sin registro propio en el dataset
    se insertan en beneficiarios en el paso 2
```

---

## Procesamiento de datos

### Entidades Locales (EELL)

- 2023 → PDF (pdfplumber, diseño en dos pasadas para celdas multilinea)
- 2024 → PDF (pdfplumber, misma arquitectura)
- 2025 → XML BOE + Excel manual (beneficiarias publicadas como imagen)

Scripts:

- `parser_eell_PDF_base.py` → EELL 2023 y 2024
- `parser_eell_BOE_2025.py` → EELL 2025

> La resolución EELL 2025 publica las tablas de entidades beneficiarias como imágenes incrustadas en el BOE, lo que impide extraerlas directamente del XML. Los datos se obtuvieron de un Excel complementario (`eell_2025_beneficiarias.xlsx`) leído con `openpyxl`.

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

> En la resolución EPA 2025 las cabeceras de las columnas cambian respecto a años anteriores: aparece "Cuantía concedida a la entidad" (que contiene la palabra *entidad*) y la cabecera de puntuación varía entre anexos. Esto rompe el mapeo por palabras clave del parser base. El parser 2025 usa extracción heurística por contenido de celda: importes > 100 para el campo importe, valores entre 0 y 100 para puntuación.

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

---

## Validación de datos

Se han implementado controles automáticos:

- conteo por año  
- conteo por estado  
- detección de CIF faltantes  
- eliminación de duplicados por clave (tipo + num_expediente + anio)  

Ejemplo (resultado actual):

| Año  | EPA  | EELL | Total |
|------|------|------|-------|
| 2021 | 328  | —    | 328   |
| 2022 | 653  | —    | 653   |
| 2023 | 651  | 593  | 1244  |
| 2024 | 881  | 1137 | 2018  |
| 2025 | 840  | 1315 | 2155  |

Por estado: concedida=2623, no_beneficiaria=2627, excluida=643, desistida=505.

Estos controles permiten garantizar la calidad del dataset antes de su integración en la base de datos y su uso en la aplicación.

---

## Dataset final

Campos:

- `anio` → año de la resolución
- `tipo` → `epa` o `eell`
- `num_expediente` → número de expediente
- `entidad` → nombre de la entidad
- `cif` → CIF/NIF
- `puntuacion` → puntuación obtenida
- `importe` → importe concedido (0 si no aplica)
- `estado` → `concedida`, `no_beneficiaria`, `excluida`, `desistida`
- `tramo` → 1, 2 o 3 (solo EELL 2025 concedidas; `null` en el resto)
- `causa_exclusion` → código de causa (solo excluidas EELL; `null` en el resto)
- `provincia` → provincia de la entidad, derivada del CIF (solo EELL; `null` para EPA)
- `ccaa` → comunidad autónoma, derivada del CIF (solo EELL; `null` para EPA)
- `periodo_meses` → duración del periodo subvencionable: `6` (EPA 2023 y 2024) o `12` (resto)
- `es_agrupacion` → `true` si la concesión es una agrupación de ayuntamientos (solo EELL 2025 concedidas); `false` en el resto
- `municipios_agrupacion` → lista de `{cif, nombre, importe_asignado}` con todos los municipios miembro, incluido el representante (solo cuando `es_agrupacion=true`); `null` en el resto

Características:

- normalizado
- sin duplicados (clave: tipo + num_expediente + anio)
- consistente entre fuentes heterogéneas
- trazable por año y tipo

**Total de registros: 6398** (EPA: 3353 · EELL: 3045)

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
    data_extractor/
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

### Extracción de datos

`scripts/data_extractor/`

### Procesamiento

`scripts/data_processing/`

### Backend (API)

```
backend/app/
  db.py              → conexión SQLAlchemy: motor, sesiones y get_db
  models.py          → tablas de la BD como clases Python (ORM)
  schemas.py         → forma de los datos que devuelve la API (Pydantic)
  main.py            → aplicación FastAPI con los routers registrados
  routers/
    convocatorias.py → GET /convocatorias/
    solicitudes.py   → GET /solicitudes/  (filtros: anio, tipo, estado, paginación)
    estadisticas.py  → GET /estadisticas/ (totales agregados por año para gráficos)
```

La documentación interactiva de la API (generada automáticamente por FastAPI) está disponible en `http://localhost:8000/docs` con el servidor arrancado.

---

## Estado actual

Fase: **backend en desarrollo**

✔ parsing XML BOE (EPAs 2021–2025)
✔ parsing PDF (EELL 2023–2024)
✔ parsing XML BOE + Excel manual (EELL 2025)
✔ limpieza y normalización de estados
✔ dataset unificado (6398 registros · EPA: 3353 · EELL: 3045)
✔ fix deduplicación cross-year (clave tipo + expediente + anio)
✔ campo provincia y ccaa para EELL (derivados del CIF, con overrides manuales)
✔ campo periodo_meses (6 para EPA 2023/2024, 12 para el resto)
✔ agrupaciones EELL 2025: campos es_agrupacion y municipios_agrupacion en todo el pipeline
✔ modelo físico de base de datos (MariaDB, `docker/init/modelo-fisico.sql`)
✔ entorno Docker (docker-compose con MariaDB + FastAPI)
✔ script de carga del dataset a la base de datos (`scripts/data_processing/cargar_dataset.py`)
✔ primera carga completa verificada (8 convocatorias, 3103 beneficiarios, 6398 solicitudes, 2623 concesiones, 13 agrupaciones, 72 miembros)
✔ backend FastAPI: modelos ORM, schemas Pydantic y 3 endpoints verificados
  · GET /convocatorias/ → lista las 8 convocatorias
  · GET /solicitudes/   → filtros por año, tipo y estado con paginación
  · GET /estadisticas/  → totales por año y tipo para gráficos (14.835.479,86 € globales)

Pendiente:

- tests con pytest
- autenticación (JWT + roles: público, registrado, admin)
- frontend de visualización

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
pip install -r requeriments.txt
```

### Archivos de dependencias

El proyecto tiene dos archivos de requisitos con propósitos distintos:

- **`requeriments.txt` (raíz)** — librerías para el entorno local de desarrollo. Incluye tanto las herramientas de procesamiento de datos (pdfplumber, beautifulsoup, pandas…) como las del backend (fastapi, sqlalchemy…). Es lo que se instala en el `venv` de la máquina de desarrollo.
- **`backend/requirements.txt`** — librerías que se instalan *dentro del contenedor Docker* del backend. Solo incluye lo que necesita FastAPI para funcionar (fastapi, uvicorn, sqlalchemy, pymysql y las de autenticación). No lleva pdfplumber ni pandas porque el contenedor no procesa datos, solo sirve la API.

---

## Docker — desarrollo vs despliegue completo

El proyecto usa Docker Compose con dos servicios definidos en `docker/docker-compose.yml`:

- **`db`** — contenedor MariaDB con la base de datos. Siempre corre en Docker porque necesita persistencia (volumen), credenciales y un schema fijo.
- **`backend`** — contenedor con la aplicación FastAPI. Está definido pero no se arranca durante el desarrollo activo.

### Durante el desarrollo (situación actual)

Solo se arranca el contenedor de la base de datos. El backend se ejecuta directamente en el `venv` local con uvicorn:

```bash
# En una terminal: arrancar solo la BD
cd docker
docker compose up -d db

# En otra terminal: arrancar el backend local (desde la raíz del proyecto)
uvicorn backend.app.main:app --reload --port 8000
```

El flag `--reload` hace que el servidor se reinicie automáticamente cada vez que se guarda un archivo Python. Así no hay que reconstruir ninguna imagen Docker con cada cambio.

### Despliegue completo (cuando el backend esté terminado)

Se levantan los dos contenedores juntos. El backend corre dentro de su propio contenedor, igual que en producción:

```bash
cd docker
docker compose up --build    # primera vez (construye la imagen del backend)
docker compose up -d         # arranques posteriores (sin reconstruir)
docker compose down          # parar (conserva los datos)
docker compose down -v       # parar y borrar la BD completa (reset total)
```

---

## Base de datos

Arranque del contenedor y carga inicial (ejecutar desde el bash de VSCode):

```bash
# Arrancar el contenedor de BD (desde docker/)
cd docker
docker compose up -d db

# Verificar que está healthy
docker compose ps

# Aplicar el schema (solo si el volumen es nuevo o fue eliminado)
docker exec -i bdns_dgda_db mariadb -uroot -proot < init/modelo-fisico.sql

# Cargar el dataset (desde la raíz del proyecto)
cd ..
python -m scripts.data_processing.cargar_dataset

# Verificar recuentos
docker exec bdns_dgda_db mariadb -uroot -proot bdns_dgda -e "
SELECT 'convocatorias'        AS tabla, COUNT(*) AS filas FROM convocatorias
UNION ALL SELECT 'beneficiarios',       COUNT(*) FROM beneficiarios
UNION ALL SELECT 'solicitudes',         COUNT(*) FROM solicitudes
UNION ALL SELECT 'concesiones',         COUNT(*) FROM concesiones
UNION ALL SELECT 'agrupaciones',        COUNT(*) FROM agrupaciones
UNION ALL SELECT 'agrupacion_miembros', COUNT(*) FROM agrupacion_miembros;"
```

> El script `docker-entrypoint-initdb.d` solo ejecuta el schema cuando el volumen Docker está vacío (primera creación). Si el volumen existe pero está vacío, aplicar el schema manualmente con el paso 3.

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
