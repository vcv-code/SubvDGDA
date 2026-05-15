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
- [Tests automáticos](docs/tests.md)  
- [Diseño del frontend](frontend/docs/diseño.md)  
- [Especificaciones del frontend](frontend/docs/especificaciones-frontend.md)  

---

## Arquitectura prevista del sistema

El sistema sigue una arquitectura cliente–servidor basada en una API REST:

```text
API externa BDNS + PDFs oficiales
      ↓
Backend Python
      ↓
Base de datos MySQL / MariaDB
      ↓
API propia (FastAPI)
      ↓
Nginx (proxy inverso, puerto 80)
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
    <td><img src="docs/img/modelo-datos-er-v1.png" width="400" alt="Diagrama ER original"></td>
    <td><img src="docs/img/Modelo-ER-Def.jpg" width="400" alt="Diagrama ER definitivo"></td>
  </tr>
</table>

---

## Tecnologías

| Área | Tecnologías |
|-----|-------------|
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Backend | Python, FastAPI, SQLAlchemy, JWT (python-jose), bcrypt |
| Base de datos | MySQL / MariaDB |
| Tests | pytest, SQLite en memoria |
| Infraestructura | Docker, Nginx, scheduler Python (cron en contenedor), Mailpit (SMTP dev) |
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

Interfaz web para explorar los datos mediante filtros y visualizaciones. La carpeta `frontend/` contiene:

- `docs/diseño.md` — guía visual completa: paleta de colores, tipografía, espaciado y componentes base
- `docs/especificaciones-frontend.md` — especificaciones técnicas de implementación: componentes, páginas, integración con la API y decisiones de diseño justificadas
- `css/styles.css` — hoja de estilos compartida por todas las páginas (variables CSS, componentes, layout)
- `js/` — un archivo JS por página (`home.js`, `solicitudes.js`, `estadisticas-epas.js`, `estadisticas-eell.js`, `auth.js`, `privado.js`, `exclusivo.js`, `admin.js`, `entidad.js`, `recuperar-password.js`, `reset-password.js`, `modal-grafica.js`, `utils.js`)
- `assets/` — logotipo, imágenes y wireframes en PDF
- `index.html`, `estadisticas-epas.html`, `estadisticas-eell.html`, `recursos.html`, `solicitudes.html`, `entidad.html`, `login.html`, `registro.html`, `privado.html`, `exclusivo.html`, `admin.html`, `recuperar-password.html`, `reset-password.html`, `verificar-email.html` — páginas implementadas

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

<https://www.infosubvenciones.es/bdnstrans/doc>

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

```text
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

```text
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

```text
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

```text
backend/app/
  db.py              → conexión SQLAlchemy: motor, sesiones y get_db
  models.py          → tablas de la BD como clases Python (ORM)
  schemas.py         → forma de los datos que devuelve la API (Pydantic)
  auth.py            → hashing de contraseñas (bcrypt) y generación/validación de tokens JWT
  dependencies.py    → dependencias FastAPI: get_current_user y require_rol
  main.py            → aplicación FastAPI con los routers registrados y manejadores de error personalizados
  routers/
    convocatorias.py → GET /convocatorias/
    solicitudes.py   → GET /solicitudes/  (filtros: anio, tipo, estado, cif, buscar, ccaa, provincia, línea; paginación con total)
    estadisticas.py  → GET /estadisticas/ · GET /estadisticas/epas · GET /estadisticas/eell
    agrupaciones.py  → GET /agrupaciones/{id_solic} (desglose de municipios miembro de una agrupación EELL)
    avisos.py        → GET /avisos/ (convocatorias del año en curso sin resolución; usadas para el banner de la web)
    auth.py          → POST /auth/registro · GET /auth/verificar · POST /auth/login · POST /auth/refresh · POST /auth/logout · POST /auth/recuperar · POST /auth/reset
    privado.py       → GET /privado/perfil · GET /privado/resumen-exclusivo · GET /privado/resumen-tabla · PUT /privado/cambiar-contrasena
    · privado.html → perfil del usuario: datos, cambiar contraseña, enlace a exclusivo.html
    · exclusivo.html → contenido exclusivo: resumen tabla, resoluciones BOE, próximas funcionalidades
```

La documentación interactiva de la API (generada automáticamente por FastAPI) está disponible en `http://localhost:8000/docs` con el servidor arrancado.

#### Autenticación

El sistema usa JWT (JSON Web Tokens) con tres niveles de acceso:

| Nivel | Rutas accesibles |
|-------|-----------------|
| Sin token | `/convocatorias/`, `/solicitudes/`, `/estadisticas/*`, `/avisos/` |
| `registrado` | Todo lo anterior + `/privado/*` |
| `admin` | Todo lo anterior + gestión de usuarios |

Flujo: el cliente hace POST a `/auth/login` → recibe un `access_token` (60 min) y un `refresh_token` (30 días) → envía el access token en la cabecera `Authorization: Bearer <token>`. Cuando el access token caduca, puede renovarlo con POST `/auth/refresh` sin volver a hacer login. POST `/auth/logout` revoca el refresh token en el servidor. Cambiar la contraseña también revoca todos los refresh tokens activos del usuario.

Las contraseñas se hashean con `bcrypt` directamente (sin `passlib`, que tiene problemas de compatibilidad con versiones recientes de bcrypt). El registro valida que la contraseña tenga al menos 8 caracteres, una mayúscula, una minúscula y un número.

#### Manejadores de error personalizados

Los errores HTTP devuelven siempre un JSON estructurado con tres campos en lugar del detalle genérico de FastAPI:

```json
{
  "error": 404,
  "mensaje": "Recurso no encontrado",
  "sugerencia": "Comprueba la URL o los parámetros de la petición"
}
```

| Código | Cuándo ocurre |
|--------|--------------|
| 401 | Petición a ruta protegida sin token o con token inválido |
| 403 | Token válido pero sin permisos suficientes |
| 404 | Ruta o recurso inexistente |
| 422 | Datos de entrada que no superan la validación Pydantic |
| 500 | Error interno no controlado |

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

- **`requeriments.txt` (raíz)** — librerías para el entorno local de desarrollo. Contiene únicamente las herramientas de procesamiento de datos y scripts: `pdfplumber`, `beautifulsoup4`, `lxml`, `pandas`, `openpyxl`, `requests` y `PyMySQL`. Es lo que se instala en el `venv` de la máquina de desarrollo para ejecutar los parsers y cargar datos. Todas las versiones están fijadas.
- **`backend/requirements.txt`** — librerías que se instalan *dentro del contenedor Docker* del backend. Solo incluye lo que necesita FastAPI para funcionar (`fastapi`, `uvicorn`, `sqlalchemy`, `pymysql`, `bcrypt`, `python-jose`, `email-validator`, `httpx` y `pytest`). No lleva pdfplumber ni pandas porque el contenedor no procesa datos, solo sirve la API. Todas las versiones están fijadas.

---

## Docker — arrancar el sistema

El proyecto usa Docker Compose con cinco servicios definidos en `docker/docker-compose.yml`:

| Servicio   | Imagen              | Función                                                   | Puerto externo    |
|------------|---------------------|-----------------------------------------------------------|-------------------|
| `db`       | mariadb:11          | Base de datos MariaDB con el dataset cargado              | 3307              |
| `backend`  | Python (build)      | API FastAPI                                               | ninguno (interno) |
| `nginx`    | nginx:alpine        | Proxy inverso, punto de entrada                           | 80, 443           |
| `cron`     | Python (scheduler)  | Tareas programadas: comprobación BDNS y health check      | ninguno           |
| `mailpit`  | axllent/mailpit     | Servidor SMTP de desarrollo — atrapa emails sin enviarlos | 1025 (SMTP), 8025 (web UI) |
| `adminer`  | adminer             | Interfaz web para explorar la BD                          | 8080              |

El backend no expone su puerto al exterior — solo Nginx y el cron pueden acceder a él dentro de la red Docker.

Mailpit está disponible en `http://localhost:8025`. Cualquier email que el backend "envíe" (recuperación de contraseña) queda atrapado aquí sin llegar a ningún destinatario real.

El servicio `cron` usa un scheduler Python propio (`docker/cron/scheduler.py`) que implementa la misma lógica que un crontab sin depender de binarios externos: registra todo en stdout (visible con `docker logs bdns_cron`) y hereda las variables de entorno del `docker-compose.yml`. Sus logs se persisten en `logs/cron/`.

Adminer está disponible en `http://localhost:8080` con Docker levantado. En el formulario de acceso: **Sistema** → MySQL · **Servidor** → `db` · usuario y contraseña según el `.env`.

### Modo desarrollo (día a día)

Solo la BD corre en Docker. El backend se ejecuta localmente con uvicorn, lo que permite ver cambios al guardar sin reconstruir imágenes.

```bash
# Terminal 1 — arrancar la BD
cd docker
docker compose up -d db

# Terminal 2 — arrancar el backend (desde la raíz del proyecto)
source venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000
```

API disponible en `http://localhost:8000/docs`

### Despliegue completo (3 contenedores con Nginx)

#### Primera vez (volumen vacío o tras `down -v`)

```bash
# 1. Arrancar todos los servicios y construir la imagen del backend
cd docker
docker compose up --build -d

# 2. Verificar que los tres contenedores están en marcha
docker compose ps

# 3. Cargar el dataset en la BD (solo una vez)
cd ..
source venv/bin/activate
python -m scripts.data_processing.cargar_dataset

# 4. Verificar recuentos esperados
docker exec bdns_dgda_db mariadb -uroot -proot bdns_dgda -e "
SELECT 'convocatorias'        AS tabla, COUNT(*) AS filas FROM convocatorias
UNION ALL SELECT 'beneficiarios',       COUNT(*) FROM beneficiarios
UNION ALL SELECT 'solicitudes',         COUNT(*) FROM solicitudes
UNION ALL SELECT 'concesiones',         COUNT(*) FROM concesiones
UNION ALL SELECT 'agrupaciones',        COUNT(*) FROM agrupaciones
UNION ALL SELECT 'agrupacion_miembros', COUNT(*) FROM agrupacion_miembros;"
```

Resultado esperado: 8 · 3103 · 6398 · 2623 · 13 · 72

#### Arranques posteriores (volumen con datos)

```bash
cd docker
docker compose up -d        # arranca los tres contenedores sin reconstruir
```

#### Parar el sistema

```bash
docker compose down          # para los contenedores, conserva los datos
docker compose down -v       # para y borra el volumen (reset total de la BD)
```

> El schema SQL se aplica automáticamente la primera vez que el volumen está vacío (via `docker-entrypoint-initdb.d`). Si el volumen existe pero la BD está vacía, aplicarlo manualmente:

```bash
docker exec -i bdns_dgda_db mariadb -uroot -proot < init/modelo-fisico.sql
```

#### Solución de problemas en WSL2 (Windows)

Si el contenedor `bdns_nginx` no arranca con el error `failed to create shim task` o `no such file or directory` al montar volúmenes, es un problema conocido de Docker Desktop + WSL2 con bind mounts de archivos individuales. La solución es recrear los contenedores desde cero:

```bash
cd docker
docker compose down
docker compose up -d
```

Si el error persiste, asegúrate de que el volumen de Nginx monta el **directorio** `./nginx` y no el archivo individual `./nginx/nginx.conf`. El archivo de configuración debe llamarse `default.conf` dentro de esa carpeta.

#### Config de Nginx no se aplica tras editar `default.conf`

Editar `default.conf` cambia el fichero en disco (volumen), pero Nginx **no recarga la config automáticamente** — sigue usando la versión anterior en memoria. Síntoma habitual: añades un bloque `location` o una zona de rate limiting y parece no tener efecto.

```bash
# Verificar sintaxis antes de recargar (falla seguro si hay error)
docker exec bdns_nginx nginx -t

# Aplicar la nueva config sin cortar conexiones activas
docker exec bdns_nginx nginx -s reload
```

#### Contenedor cron — supercronic no arranca (`Failed to fork exec`)

La versión v0.2.33 de supercronic presenta un bug de inicialización en entornos Docker Desktop + WSL2: el proceso muere inmediatamente con `level=fatal msg="Failed to fork exec: no such file or directory"` antes de leer el crontab, aunque el binario sea válido y el crontab correcto (verificado con `supercronic -test`). En modo `--debug` sí arranca, lo que apunta a una race condition en la secuencia de inicialización.

Solución implementada: se sustituyó supercronic por un **scheduler Python propio** (`docker/cron/scheduler.py`) que implementa la misma lógica de ejecución sin depender de binarios externos. El comportamiento es idéntico al crontab original y no presenta el problema.

---

### Actualizar datos o código sin perder nada

El sistema tiene tres capas independientes. Cada una se actualiza de forma diferente:

| Capa | Cuándo actualizar | Cómo | Afecta a los datos |
|------|------------------|------|--------------------|
| **Frontend** (HTML/CSS/JS) | Cambio en `frontend/` | Ninguna acción — Nginx lee el volumen en tiempo real | No |
| **Backend** (Python/FastAPI) | Cambio en `backend/` | `docker compose up -d --build backend` | No — la BD está en volumen separado |
| **Config Nginx** (`default.conf`) | Cambio en `docker/nginx/` | `docker exec bdns_nginx nginx -s reload` | No |
| **Base de datos** (nuevo campo / tabla) | Cambio en `modelo-fisico.sql` | Migración SQL manual + rebuild backend | Solo añade estructura |
| **Base de datos** (nuevo año / resolución) | Nuevo dataset parseado | `python -m scripts.data_processing.cargar_dataset` con el nuevo JSON | Solo añade filas, nunca borra |

**Caché del navegador** (JS/CSS): si el navegador muestra una versión antigua del frontend después de un cambio, Ctrl+Shift+R fuerza la recarga ignorando la caché local. En DevTools → Network → "Disable cache" para depurar sin caché.

**Caché HTTP de la API** (Cache-Control): los endpoints `/convocatorias/` (1 día) y `/estadisticas/` (1 hora) devuelven cabeceras `Cache-Control`. FastAPI no cachea internamente — los datos siempre vienen de la BD. Si se actualiza la BD y se quiere que el navegador vea los nuevos datos antes de que expire la caché, basta con hacer Ctrl+Shift+R.

**Volumen de la BD**: `docker compose down` para los contenedores pero **conserva** el volumen con todos los datos. Solo `docker compose down -v` borra el volumen — usar únicamente para reset total desde cero.

---

## Tests

El proyecto tiene **249 pruebas en total**: 197 automáticas con pytest y 52 manuales verificadas en el navegador con Docker levantado.

| Nivel | Cantidad | Herramienta |
|-------|----------|-------------|
| Automáticos | 195 | pytest (sin Docker) |
| Manuales | 52 | Navegador + DevTools |

Los tests automáticos verifican los endpoints de la API y el sistema de autenticación sin necesidad de tener Docker levantado. Usan una base de datos SQLite en memoria que se crea y destruye en cada test.

### Ejecutar todos los tests

```bash
source venv/bin/activate
pytest -v
```

### Ejecutar por módulo

```bash
pytest tests/test_smoke.py              # arranque de la API y /health
pytest tests/test_convocatorias.py
pytest tests/test_solicitudes.py        # filtros, paginación y exportación CSV
pytest tests/test_estadisticas.py       # /estadisticas/, /estadisticas/epas y /estadisticas/eell
pytest tests/test_auth.py               # registro, login y zona privada
pytest tests/test_agrupaciones.py       # endpoint /agrupaciones/ con relaciones completas
pytest tests/test_avisos.py             # endpoint /avisos/ — convocatorias pendientes de resolución
pytest tests/test_cache_headers.py      # cabeceras Cache-Control en /convocatorias/ y /estadisticas/
pytest tests/test_rate_limiting.py      # configuración de rate limiting en Nginx
pytest tests/test_privado.py            # cambiar contraseña desde la zona privada
pytest tests/test_refresh_token.py      # refresh token, rotación y logout
pytest tests/test_logging.py            # middleware y configuración de logging
pytest tests/test_verificacion_email.py # verificación de email al registro
pytest tests/test_admin.py              # panel de administración completo
pytest tests/test_unificar_datasets.py  # funciones de normalización del pipeline
pytest tests/test_parser_epa2025.py     # helpers y flujo del parser EPA 2025
```

### Resultado esperado

```text
181 passed   # excluyendo test_https_config.py y test_rate_limiting.py (requieren Docker+Nginx)
197 passed   # suite completa con Docker levantado
```

Para el detalle completo de cada test (tipo, técnica de caja y qué comprueba exactamente) ver [`docs/tests.md`](docs/tests.md).

### Pruebas de integración end-to-end (manuales)

Complementan a los tests automáticos verificando el stack completo: Nginx → FastAPI → MariaDB real. Se realizan desde `http://localhost/docs` con Docker levantado y cubren filtros con datos reales, paginación, flujo de registro y login, acceso con y sin token, y la respuesta de los manejadores de error. Ver la sección "Prueba manual rápida" en [`docs/tests.md`](docs/tests.md).

#### Pruebas manuales del panel de administración (rama 12a)

Realizadas con Docker levantado, usuario admin activo y una cuenta de prueba adicional (`prueba@test.com`).

| Prueba | Resultado | Observaciones |
|---|---|---|
| Acceso a `admin.html` sin token (incógnito) | ✅ Redirige a `login.html` | JS verifica token antes de cargar |
| Acceso a `admin.html` con token de usuario `registrado` | ✅ Redirige a `privado.html` | Backend devuelve 403 en `/privado/perfil` con rol insuficiente |
| Carga del panel completo (admin) | ✅ 4 secciones cargan en paralelo | health OK · 9 convocatorias · 6398 solicitudes · 4 usuarios |
| Última convocatoria detectada | ✅ Muestra convocatoria EELL 2026 | Derivado de la BD, no del cron |
| Tabla de usuarios | ✅ 4 usuarios con rol, estado, fecha | Fila propia marcada con `(tú)` sin botones de acción |
| Desactivar usuario | ✅ 403 al intentar login posterior | Badge cambia a "Inactivo"; login devuelve 403 correctamente |
| Botón "Panel de administración" en `privado.html` | ✅ Solo visible para rol `admin` | Oculto con `display:none`; mostrado por JS al confirmar rol |
| Aviso activo EELL 2026 | ✅ Aparece en sección Avisos | Convocatoria sin `fecha_resolucion` del año en curso |
| Logs de acceso | ✅ Muestra historial de peticiones | Refleja en tiempo real las llamadas realizadas durante las pruebas |

| Reactivar usuario | ✅ Login funciona tras activar | Badge vuelve a "Activo", 403 desaparece |
| Hacer admin a otro usuario | ✅ Usuario accede a admin.html | Botón aparece en privado.html al volver a entrar |
| Quitar admin | ✅ Redirige a privado.html | admin.html ya no accesible |
| Usuario inactivo en tabla | ✅ Muestra badge "Inactivo" con botón "Activar" | user@example.com visible correctamente |
| Selector de logs (50 líneas) | ✅ Recarga con número correcto | Logs reflejan intentos fallidos del proceso de debug |

Pendiente: "Marcar resuelta" en aviso EELL 2026 (no bloqueante para el commit).

---

## Flujo de trabajo

El proyecto sigue un flujo basado en main + dev + feature/*, un modelo híbrido entre Git Flow y GitHub Flow, adaptado a equipos pequeños.

### Estructura

main (producción, estable)
 │
 └── dev (desarrollo)
       │
       ├── feature/*(funcionalidad)
       └── feature/*(funcionalidad)

### Orden

1. Cada funcionalidad se desarrolla en una rama feature/*
2. Se hacen commits sobre esa rama
3. Se integra en dev mediante Pull Request (preferiblemente con squash)
4. dev actúa como entorno de integración
5. Cuando es estable, se fusiona en main

### Motivos

Hemos elegido este tipo de flujo porque lo hemos utilizado ambas en las prácticas de empresa y porque separa desarrollo (dev) de producción (main), reduciendo errores y permitiendonos trabajar en paralelo de forma segura, manteniendo un flujo claro y sencillo, adecuado para equipos pequeños y proyectos pequeños o medianos con desarrollo activo, como es el caso.

Otros flujos más simples (todo en main) son arriesgados, y los más complejos (Git Flow completo) añaden complejidad innecesaria.

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

## Mejoras futuras

Mejoras identificadas pero no planificadas para el desarrollo actual:

- **`num_convoc` en convocatorias históricas (2021–2025):** el campo existe en el modelo pero está a NULL para las convocatorias cargadas desde CSV/PDF (las fuentes históricas no incluían el número BDNS). Se podría rellenar manualmente consultando la web de infosubvenciones.es para cada convocatoria. No afecta a ninguna funcionalidad actual.
- **Campo `linea` para EPA 2024** — la Orden modificada ya estaba en vigor pero el BOE de 2024 no desglosa la línea por entidad en las tablas parseadas. Si se revisa el parser, el campo `linea` ya está preparado en el modelo.
- **Cofinanciación EELL** — aporta puntos en la evaluación pero no modifica el importe concedido. Solo disponible en el ANEXO V del XML 2025; no existe en los PDF de 2023/2024.
- **Causas de exclusión EPA** — el BOE las incluye pero con un formato diferente al de EELL, por lo que requieren un parser específico.
- **Provincia/CCAA para EPA (asociaciones)** — no es derivable del CIF tipo G de forma estándar.
- **Autogeneración de `models.py`** — usar `sqlacodegen` para generar el ORM de SQLAlchemy directamente desde el esquema de la BD, en lugar de mantenerlo a mano.
- **Login con terceros (OAuth)** - integración con Google.
- **CAPTCHA en registro** *(mejora de producción avanzada)*: reCAPTCHA o hCaptcha para bloquear bots sofisticados. Requiere dependencia de terceros y añade fricción al usuario; desproporcionado para este proyecto.
- **Blocklist de dominios desechables** *(mejora de producción avanzada)*: bloquear `mailinator.com`, `guerrillamail.com` y similares al registrarse. Hay cientos de dominios y se actualizan constantemente — coste de mantenimiento muy alto para el beneficio obtenido.
- **Puerto de base de datos**: en producción eliminar la exposición del puerto `3307` en `docker-compose.yml`; la BD y el backend se comunican dentro de la red Docker sin necesidad de exponer el puerto al host.
- **Dominio real y certificado Let's Encrypt**: sustituir el certificado autofirmado por uno de Let's Encrypt (gratuito, renovación automática, confiado por todos los navegadores).
- **CORS con dominio específico**: sustituir `allow_origins=["*"]` en `main.py` por el dominio real una vez definido.
- **Refactor CSS inline**: las páginas complejas (`index.html`, `estadisticas-*.html`, `solicitudes.html`) aún tienen inline styles de diseño. Los casos sencillos ya se migraron a clases CSS; lo que queda requiere verificación visual página a página.

---

## Estado actual

Fase: **backend completado · HTTPS activo · cron verificado · caché y rate limiting activos · autenticación completa con verificación de email y recuperación de contraseña · Mailpit activo · frontend integrado · tramo y agrupaciones expuestos · UX buscador mejorada · panel de administración activo · zona privada ampliada · medidas anti-bots activas · cron con auto-detección de resoluciones · modal de conclusiones en gráficas**

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
  · GET /solicitudes/   → filtros por año, tipo, estado, CIF exacto, búsqueda parcial por nombre, CCAA, provincia y línea; respuesta paginada con `total` y `resultados`
  · GET /estadisticas/      → totales por año y tipo para gráficos (14.835.479,86 € globales)
  · GET /estadisticas/epas  → análisis EPA: importe medio, mediana, distribución de importes, nuevos vs recurrentes, top beneficiarios por año
  · GET /estadisticas/eell  → análisis EELL: % ayuntamientos con ayuda, ranking CCAA, top provincias, concentración del importe
✔ Nginx como servidor web y proxy inverso (`docker/nginx/default.conf`)
  · escucha en el puerto 80
  · sirve los archivos estáticos del frontend directamente (HTML, CSS, JS, imágenes)
  · redirige las rutas de la API al backend (puerto 8000 interno, no expuesto al exterior)
  · acceso a la app en `http://localhost/` y a la API en `http://localhost/docs`
  · cabeceras de seguridad: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`
✔ Adminer como interfaz web de la base de datos (`http://localhost:8080`)
  · sin instalar nada en el equipo; se levanta con el resto de contenedores
✔ autenticación JWT con tres niveles de acceso
  · POST /auth/registro → crea usuario con contraseña hasheada (bcrypt)
  · POST /auth/login    → devuelve token JWT (expira en 60 minutos)
  · GET  /privado/perfil, /privado/resumen-exclusivo → solo usuarios registrados
  · validación de contraseña en el registro: mínimo 8 caracteres, mayúscula, minúscula y número
  · roles: registrado (por defecto) y admin
✔ campo `tramo` EELL 2025 expuesto en API, frontend y CSV
  · `SolicitudOut` incluye `tramo: Optional[int]`
  · badge `T1`/`T2`/`T3` en resultados del buscador y en ficha de entidad
  · leyenda de tramos (población del municipio) encima de la tabla, visible solo cuando aplica
  · CSV de exportación incluye columna `tramo`
✔ bugs corregidos en ficha de agrupación EELL
  · representante mostraba `[object Object]` → corregido a `datos.representante.nombre`
  · importes de miembros mostraban `—` → campo `importe_asignado` (nombre correcto del schema)
✔ persistencia de filtros del buscador en la URL
  · los filtros activos se escriben como parámetros en la URL al buscar
  · al volver con el botón "Volver al buscador" o con Atrás, los resultados se restauran
  · limpiar filtros borra también los parámetros de la URL
✔ bug corregido en exportación CSV: los filtros `provincia` y `linea` no se enviaban al backend
✔ bloque "Convocatorias" en la Home (`index.html`)
  · tabla separada por tipo (EELL / EPA) con año, fecha de convocatoria (BOE) y acceso rápido al buscador
  · fechas de convocatoria obtenidas de la API BDNS; fechas de resolución de la API del BOE
  · convocatorias pendientes de resolución (sin `fecha_resolucion`) muestran estado "Pendiente de resolución"
  · datos incluidos en `cargar_dataset.py` para nuevos despliegues (no requieren UPDATE manual)
✔ Mailpit como servidor SMTP de desarrollo (`http://localhost:8025`)
  · contenedor `axllent/mailpit` en docker-compose; puerto 1025 (SMTP) y 8025 (web UI)
  · el backend envía emails vía `smtplib` con variables de entorno `SMTP_HOST=mailpit` y `SMTP_PORT=1025`
  · los emails quedan atrapados en Mailpit sin llegar a destinatarios reales
✔ recuperación de contraseña por email
  · POST /auth/recuperar — genera token opaco (15 min, un solo uso) e envía enlace por email
  · POST /auth/reset — valida token, valida contraseña nueva y actualiza en BD
  · tabla `reset_tokens` en BD con campo `usado` y FK con CASCADE
  · páginas `recuperar-password.html` y `reset-password.html` con formularios y feedback
  · respuesta idéntica si el email existe o no (evita enumeración de usuarios)
✔ tests automáticos con pytest (195 tests — smoke, funcionales, unitarios, seguridad, rendimiento, configuración)
  · test_smoke.py (3): arranque de la API y endpoint /health
  · test_convocatorias.py (3): endpoint /convocatorias/
  · test_solicitudes.py (16): filtros, paginación, búsqueda parcial, estructura, exportación CSV y campo tramo
  · test_estadisticas.py (24): /estadisticas/, /estadisticas/epas y /estadisticas/eell — estructura, cálculos, nuevos/recurrentes, concentración
  · test_auth.py (10): registro, login, acceso con/sin token
  · test_agrupaciones.py (7): endpoint /agrupaciones/ — estructura, importes correctos, representante con nombre
  · test_logging.py (5): middleware de logging y configuración del logger
  · test_https_config.py (9): certificado SSL, configuración Nginx HTTPS y seguridad TLS
  · test_avisos.py (6): endpoint /avisos/ — convocatorias pendientes de resolución
  · test_cache_headers.py (4): cabeceras Cache-Control en /convocatorias/ y /estadisticas/
  · test_rate_limiting.py (7): configuración de rate limiting en Nginx para /auth/login y /auth/registro
  · test_privado.py (6): cambiar contraseña — contraseña actual incorrecta, nueva débil, cambio correcto, login con nueva/vieja contraseña
  · test_verificacion_email.py (10): registro crea usuario no verificado, token en BD, email enviado, login bloqueado sin verificar, token válido activa cuenta, login tras verificar, token inválido/usado/expirado, reset activa email_verificado
  · test_refresh_token.py (7): refresh token — login devuelve token, renovación, rotación, token inválido, logout revoca, cambio contraseña revoca tokens
  · test_recuperar_password.py (9): recuperación contraseña — email existente/inexistente, token creado en BD, email enviado, reset válido, token inválido/usado/expirado, contraseña débil
  · test_admin.py (24): panel de administración — control de acceso (401/403), estado del sistema, CRUD de usuarios, eliminación con cascada de tokens, protección auto-edición, gestión de avisos, reactivar aviso, historial de resueltas, protección 409 con solicitudes, logs de acceso y de error
  · test_unificar_datasets.py (21): funciones de normalización del pipeline de datos
  · test_parser_epa2025.py (22): helpers y flujo completo del parser EPA 2025
  · BD de prueba SQLite en memoria (no requiere Docker)
✔ manejadores de error personalizados (401, 403, 404, 422, 500)
  · JSON estructurado con campos error, mensaje y sugerencia
  · sin exponer internos del servidor en errores 500
✔ HTTPS con dominio local (`subvencionesDGDA.local`) y certificado autofirmado
  · certificado generado con openssl (CN + SAN para compatibilidad con navegadores modernos)
  · Nginx termina el SSL en el puerto 443; el backend no necesita saber nada de SSL
  · HTTP (puerto 80) redirige automáticamente a HTTPS con código 301
  · TLS 1.2 y 1.3 únicamente; cabecera `Strict-Transport-Security` activa
  · ver sección "Configuración HTTPS local" en [`docs/referencia-tecnica.md`](docs/referencia-tecnica.md) para reproducir el entorno
✔ sistema de logs: registro de cada petición HTTP (IP, método, ruta, código, latencia) y errores 500
  · logger de aplicación con rotación automática de archivos (`logs/app/`)
  · access log y error log de Nginx con formato personalizado (`logs/nginx/`)
  · persistencia mediante volúmenes Docker: los logs sobreviven reinicios del contenedor
✔ endpoint GET /health → `{"status": "ok"}` para monitorización del servicio
✔ agrupaciones EELL 2025 expuestas en la API
  · campo `es_agrupacion` en cada solicitud de tipo SolicitudOut
  · GET /agrupaciones/{id_solic} → desglose completo de municipios miembro con importes
✔ exportación CSV: GET /solicitudes/export con los mismos filtros que /solicitudes/ y sin paginación
✔ diseño del frontend: wireframes, guía de estilos, logo y estructura de páginas (`frontend/`)
✔ maquetación HTML + CSS: estructura completa de todas las páginas con diseño responsive
  · `index.html` — portada con métricas dinámicas, spinners y banner de avisos activos
  · `solicitudes.html` — buscador con filtros, tabla paginada, columna Año, badges de estado, botón CSV
  · `estadisticas-epas.html` — análisis de EPAs: importe medio, mediana, distribución, nuevos vs recurrentes, top beneficiarios
  · `estadisticas-eell.html` — análisis de EELL: % ayuntamientos con ayuda, top provincias, concentración, ranking CCAA
  · `recursos.html` — directorio de organizaciones de protección animal y campañas actuales (contenido estático)
  · `entidad.html` — ficha de entidad con historial, badges de estado y bloque de agrupación EELL
  · `login.html` / `registro.html` — autenticación con validación client-side
  · `privado.html` — zona exclusiva con control de acceso JWT
  · `admin.html` — panel de administración exclusivo para rol `admin`
✔ integración JS con la API REST: fetch a todos los endpoints, paginación, autenticación con Bearer token
✔ CORS habilitado en el backend para desarrollo local
✔ clave JWT segura configurada en variables de entorno (`.env`)
✔ filtros avanzados CCAA, provincia y línea conectados al backend en el buscador
✔ ficha de entidad (`entidad.html`): historial de solicitudes por CIF, badges de estado, desglose agrupación EELL
✔ respuesta paginada con total: `GET /solicitudes/` devuelve `{"total": N, "resultados": [...]}` para mostrar "Página X de Y"
✔ tarjeta "Entidades únicas" en el dashboard: `GET /estadisticas/` expone `entidades_unicas` (3.067 beneficiarios distintos)
✔ favicon en todas las páginas HTML
✔ meta tags OG (`og:title`, `og:description`, `og:image`) en todas las páginas
✔ navbar: texto "Subvenciones DGDA" en todas las páginas; spinner y error-box unificados en home, solicitudes y entidad
✔ tabla solicitudes: columna Expediente → Año, badges de estado, ordenación por defecto A→Z, botón descargar CSV
✔ mejoras de accesibilidad: `role="navigation"` y `aria-label` en navbar
✔ `especificaciones-frontend.md` totalmente actualizado y sincronizado con la implementación real
✔ servicio cron como contenedor independiente en docker-compose (`docker/cron/`)
  · `scheduler.py` — scheduler Python puro que orquesta las tareas sin binarios externos
  · `check_bdns.py` — lógica en dos pasos en cada ejecución:
      1. **Detección de resoluciones**: para cada convocatoria del año con `fecha_resolucion=NULL`,
         consulta `GET /bdnstrans/api/convocatorias/{num_convoc}` en la API BDNS buscando el campo
         `fechaResolucion`. Si ya está publicada, actualiza la BD → el banner desaparece
         automáticamente sin intervención manual (BDNS suele actualizarse 1-2 días tras el BOE).
      2. **Detección de nuevas convocatorias**: si aún no se han registrado EELL y/o EPA del año
         actual, busca en la API BDNS por "protección animal" y "colonias felinas", detecta el tipo
         por palabras clave del título (`detectar_tipo`) y las inserta con `fecha_resolucion=NULL`.
         Estado persistido en `logs/cron/estado_YYYY.json`.
      Tipo EELL: busca "ENTIDADES LOCALES" o "EELL" en el título.
      Tipo EPA: busca "ENTIDADES PRIVADAS", "ASOCIACIONES" o "PROTECCI" (cubre "protección animal").
      Frecuencia: cada 2 días en abr–may, cada 4 días en mar–jun.
  · `health_check.py` — llama a GET /health cada 6 horas y loguea el resultado
  · logs persistidos en `logs/cron/` como volumen Docker
✔ GET /avisos/ — devuelve convocatorias del año actual con fecha_resolucion=NULL para el banner de la web
✔ banner de avisos en `index.html`: aparece cuando el cron inserta una nueva convocatoria y desaparece
  automáticamente cuando el cron detecta la resolución en la API BDNS (fecha_resolucion se actualiza sola).
  El enlace al BOE en la sección "Resoluciones oficiales" sí requiere actualización manual en index.html.
✔ cambiar contraseña desde la zona privada
  · PUT /privado/cambiar-contrasena — valida contraseña actual con bcrypt, aplica las mismas reglas de fortaleza del registro
  · formulario en privado.html con feedback de error (actual incorrecta, nueva débil) y confirmación de éxito
✔ refresh token y "Recuérdame"
  · tabla refresh_tokens en BD: token opaco (64 hex), expiración 30 días, flag revocado
  · login genera siempre un refresh token; rotación en cada uso (el token anterior queda revocado)
  · POST /auth/refresh — devuelve nuevo access token + nuevo refresh token
  · POST /auth/logout — revoca el refresh token en el servidor
  · checkbox "Recuérdame" en login.html: si marcado, guarda el refresh token en localStorage
  · privado.js renueva automáticamente el access token al cargar si hay refresh token guardado
✔ cabeceras Cache-Control en endpoints de datos estáticos
  · GET /convocatorias/ → `Cache-Control: public, max-age=86400` (1 día; datos cambian 1-2 veces al año)
  · GET /estadisticas/  → `Cache-Control: public, max-age=3600`  (1 hora)
  · implementado en los routers FastAPI mediante parámetro `Response`
✔ rate limiting en Nginx para prevenir fuerza bruta y creación masiva de cuentas
  · zona `login:10m rate=10r/m` — 10 peticiones/minuto por IP en `/auth/login` (burst=5)
  · zona `registro:10m rate=5r/m` — 5 peticiones/minuto por IP en `/auth/registro` (burst=3)
  · ambos con `limit_req_status 429`; el resto de la API no está limitada
✔ panel de administración (`admin.html` + `js/admin.js`)
  · acceso exclusivo para usuarios con rol `admin`; redirige a login o privado si no procede
  · GET /admin/estado → salud del sistema, conteo de convocatorias/solicitudes/usuarios, última convocatoria detectada
  · GET /admin/usuarios → listado completo de usuarios con email, rol, estado y fecha de alta
  · PATCH /admin/usuarios/{id}/rol → cambiar rol entre `registrado` y `admin` (protegido: no puede cambiar el propio)
  · PATCH /admin/usuarios/{id}/activo → activar o desactivar cuenta (protegido: no puede desactivar la propia)
  · DELETE /admin/usuarios/{id} → elimina el usuario permanentemente, borrando en cascada sus tokens (protegido: no puede borrarse a sí mismo; 404 si no existe)
  · GET /admin/avisos?incluir_resueltas=true → por defecto solo sin resolución; con el param devuelve también las resueltas (historial desplegable en el panel)
  · PATCH /admin/avisos/{id}/desactivar → marca la convocatoria como resuelta (desaparece del banner)
  · PATCH /admin/avisos/{id}/reactivar → elimina la fecha de resolución y vuelve a activar el aviso y el banner
  · DELETE /admin/avisos/{id} → elimina la convocatoria (rechaza con 409 si tiene solicitudes asociadas)
  · GET /admin/logs?n=100 → últimas N líneas de `logs/app/access.log` (máx. 500)
  · GET /admin/logs/errores?n=100 → últimas N líneas de `logs/app/error.log` (máx. 500)
  · `/admin/` añadido al proxy Nginx junto al resto de rutas de la API
✔ **medidas anti-bots y seguridad en registro** (rama 12)
  · rate limiting `POST /auth/registro`: zona `registro:10m rate=5r/m`, `burst=3 nodelay`
  · honeypot: campo `sitio_web` oculto; si llega relleno → éxito falso sin crear cuenta
  · verificación de email al registrarse: tabla `verificacion_tokens`, `GET /auth/verificar`, bloqueo login con 403
  · reenvío de verificación `POST /auth/reenviar-verificacion`: invalida tokens anteriores, siempre 200
✔ zona privada ampliada (rama 12): `privado.html` (perfil) + `exclusivo.html` (contenido exclusivo: tabla resumen, resoluciones BOE)
✔ panel de administración reorganizado: Avisos primero, botón "← Volver al perfil" en banner
✔ páginas de error `404.html` y `50x.html` con imagen ilustrativa + `error_page` en Nginx (rama 13)
✔ aviso legal (`aviso-legal.html`), política de privacidad (`privacidad.html`) y sección de cookies
✔ footer actualizado con aviso legal y privacidad en todas las páginas; resoluciones BOE en home pública
✔ mejoras estadísticas y home (rama 13): gráficas home reordenadas, tasa éxito/fracaso, leyenda rosco con descripciones, tooltip desglose EPA/EELL, colores badges corregidos, KPIs centrados, top beneficiarios EPA con zoom y abreviaciones, rangos distribución importes ajustados a datos reales
✔ modal de conclusiones por gráfica (rama 13): botón "¿Qué conclusiones se sacan?" al pie de cada tarjeta de gráfica abre un modal con la gráfica como fondo tenue y texto interpretativo encima; compartido entre home, EPAs y EELL mediante `js/modal-grafica.js`; 9 gráficas cubiertas
✔ página Recursos renovada (rama 13): fondos de color por sección (verde/azul/ámbar/rosa), logos actualizados y normalizados, textos de descripción revisados
✔ cron — corrección `detectar_tipo` (rama 13): añadida palabra clave `"PROTECCI"` para detectar convocatorias EPA cuyo título en BDNS usa "protección animal" en lugar de "entidades privadas/asociaciones"; resolvía que la EPA 2026 se omitía silenciosamente
✔ cron — auto-detección de resoluciones (rama 13): nueva función `comprobar_resoluciones()` que en cada ejecución consulta `GET /bdnstrans/api/convocatorias/{num_convoc}` para cada convocatoria con `fecha_resolucion=NULL`; si BDNS ya publica la fecha, la actualiza en la BD → el banner de avisos desaparece automáticamente sin intervención manual
✔ resoluciones pendientes dinámicas en home (rama 13): `cargarPendientesResoluciones()` en `home.js` lee `/avisos/` e inyecta automáticamente entradas "Resolución pendiente de publicación" en las listas BOE de EELL y EPA; al resolverse, desaparecen solas
✔ logs de error del backend en panel de admin (rama 15): nuevo endpoint `GET /admin/logs/errores?n=N` que sirve `logs/app/error.log`; nueva sección en `admin.html` con borde rojo sutil; subtítulos aclaratorios en todas las secciones del panel; CSS del panel migrado de `<style>` inline a `styles.css`
✔ toggle visibilidad de contraseña (rama 15): botón con icono de ojo en todos los campos de contraseña (`login.html`, `registro.html`, `privado.html`, `reset-password.html`); lógica compartida en `js/utils.js`; al volver a pulsar se oculta de nuevo

### Pendientes

- **Revisión accesibilidad (pasada ligera)**: verificar jerarquía de headings, `alt` en imágenes, landmarks semánticos. Riesgo bajo — no tocar contrastes ni tamaños de fuente antes de entrega (Miyuki).
- **Footer**: revisar los enlaces de GitHub, Documentación y Contacto.
- **Mapa de calor CCAA** en `estadisticas-eell.html`: datos disponibles en `GET /estadisticas/eell`; falta integrar Leaflet/D3-geo + GeoJSON (Miyuki).
- **Ficha de entidad como modal/popup** en el buscador, en lugar de navegar a página separada (Miyuki).
- **Conclusiones en modales de gráficas**: revisar y ajustar los textos interpretativos (Vero).
- **Script de instalación automática**: instala dependencias, carga BD, añade `subvencionesDGDA.local` al `/etc/hosts` (Vero).

---

## Notas técnicas

- `data/raw/` no se versiona completo; se mantienen ejemplos representativos. Los scripts sobrescriben resultados al volver a ejecutarse — el sistema es reproducible desde cero.
- El campo `email_verificado` en `usuarios` tiene `DEFAULT 1` en la migración (para no bloquear cuentas existentes), pero `POST /auth/registro` siempre lo establece a `0` explícitamente.
- `min-height: calc(100vh - var(--altura-nav))` en `.fondo-stats` causaba un espacio vacío grande antes del footer cuando el contenido no llenaba la pantalla — se eliminó en rama 13.
- Chart.js: `formatearEjeY` usa `.toFixed(0)` que redondea 7,5 → 8, generando ticks duplicados si el rango del eje es pequeño y `stepSize` no es múltiplo entero de 1000. Solución: callback personalizado `(k % 1 === 0 ? k : k.toFixed(1)) + ' K'`.
- CSS: las clases del ranking CCAA en `estadisticas-eell.js` usaban `ranking-lista__item` (BEM incorrecto) mientras el CSS definía `.ranking-item`. Corregido en rama 13 — el ranking aparecía sin formato hasta entonces.

---

### Bugs encontrados durante la implementación del panel de administración (rama 12a)

Durante el desarrollo se detectaron tres bugs antes de las pruebas manuales, en la revisión del código y al ejecutar los tests:

**1. `/admin/` ausente en la configuración de Nginx** *(crítico)*

`docker/nginx/default.conf` tenía una expresión regular para las rutas de la API que no incluía `admin`:

```nginx
# Antes — /admin/ llegaba al servidor de estáticos, devolvía 404
location ~ ^/(convocatorias|solicitudes|...|avisos|health|...)(/|$) { ... }

# Después — /admin/ se redirige correctamente al backend
location ~ ^/(convocatorias|solicitudes|...|admin|avisos|health|...)(/|$) { ... }
```

Sin este cambio, todas las llamadas AJAX del panel habrían devuelto 404 o cargado el HTML de Nginx en lugar de la respuesta JSON del backend.

**2. `GET /privado/perfil` no devolvía `id_usuario`** *(medio)*

El endpoint de perfil devolvía `email`, `rol` y `miembro_desde`, pero no `id_usuario`. El JavaScript de `admin.js` necesita el `id_usuario` del admin en sesión para bloquear los botones de "Desactivar" y "Quitar admin" sobre la propia fila (protección anti-autoedición). Sin ese campo, `miId` siempre era `null` y los botones de protección nunca se ocultaban en el frontend (aunque el backend sí rechazaba las peticiones con 400).

```python
# Antes
return {"email": usuario.email, "rol": usuario.rol, "miembro_desde": usuario.created_at}

# Después
return {"id_usuario": usuario.id_usuario, "email": usuario.email, "rol": usuario.rol, "miembro_desde": usuario.created_at}
```

**3. `cargarAvisos` en `admin.js` no comprobaba `r.ok`** *(menor)*

Si el token caducaba en mitad de una sesión larga (el access token dura 60 minutos), la respuesta del backend sería un JSON de error `{"detail": "Token inválido o expirado"}` en lugar de un array. Sin comprobar `r.ok`, el código intentaba iterar sobre ese objeto, no encontraba `length` y mostraba "No hay avisos activos" en lugar de un mensaje de error. Corregido añadiendo `if (!r.ok) return` antes de parsear el JSON.

---

### Tests que fallaron en la primera ejecución (rama 12a)

Al ejecutar `test_admin.py` por primera vez, dos tests fallaron y pusieron de manifiesto diferencias concretas entre SQLite (BD de tests) y MariaDB (BD de producción):

**`test_listar_avisos_devuelve_sin_resolucion`** — el helper de test insertaba una convocatoria con `fecha_resolucion="2025-01-01"` (string). SQLite acepta strings en columnas DATE en MariaDB pero el dialecto SQLAlchemy para SQLite lanza `TypeError: SQLite Date type only accepts Python date objects as input`. Corregido pasando `date(2025, 1, 1)` (objeto `datetime.date`). Esto no es un problema en producción con MariaDB, que acepta ambos formatos, pero sí revela que los tests deben usar tipos Python correctos siempre.

**`test_eliminar_aviso_con_solicitudes_devuelve_409`** — el helper creaba un `Beneficiario` con `tipo_benef="epa"`, que no es un valor válido en el ENUM del modelo (`asociacion` o `entidad_local`). MariaDB almacena strings y no valida el ENUM al escribir en modo no estricto, pero SQLAlchemy sí lo valida en memoria al hacer `db.refresh()`. Corregido usando `tipo_benef="asociacion"`. Este caso ilustra la diferencia habitual entre SQLite/SQLAlchemy y MariaDB en la validación de ENUMs: en tests hay que ceñirse a los valores del modelo Python, no confiar en la tolerancia de la BD.

---

### Decisiones y problemas técnicos de implementaciones anteriores

#### Cron — Supercronic incompatible con Docker + WSL2 (rama 9e)

La primera aproximación para el scheduler fue usar [Supercronic](https://github.com/aptible/supercronic), un cron diseñado para contenedores Docker. Falló con un error de fork al arrancar en el entorno Docker + WSL2 incluso con la opción `--debug`. Solución: scheduler implementado directamente en Python (`docker/cron/scripts/scheduler.py`) usando `time.sleep()` y comprobaciones de hora/día. Sin dependencias de binarios externos, sin permisos especiales, reproducible en cualquier entorno. Lección: en Docker, preferir código Python antes que binarios del sistema cuando el entorno de destino (WSL2) puede tener restricciones de llamadas al sistema.

#### HTTPS — `subjectAltName` obligatorio en navegadores modernos (rama 9a)

Al generar el certificado autofirmado con `openssl`, es imprescindible incluir la extensión `subjectAltName (SAN)` además del `Common Name (CN)`. Chrome (desde 2017) y otros navegadores modernos rechazan certificados que no tengan el dominio también en el SAN, aunque el CN coincida exactamente. Sin SAN, el navegador muestra error de certificado aunque HTTPS esté configurado correctamente. El comando `openssl req` requiere el flag `-addext "subjectAltName=DNS:subvencionesDGDA.local"` o el uso de un archivo de extensiones.

#### HTTPS — flag `-nodes` en `openssl` (rama 9a)

Al generar la clave privada, hay que incluir `-nodes` (no DES) para que la clave no esté protegida por contraseña. Sin este flag, OpenSSL protege la clave con una contraseña que hay que introducir manualmente cada vez que Nginx arranca. En un contenedor Docker, el inicio es no interactivo — sin `-nodes`, Nginx se quedaría bloqueado esperando la contraseña y el contenedor no arrancaría.

#### `limit_req_zone` en `default.conf` (rama 9f)

La directiva `limit_req_zone` de Nginx debe ir dentro del bloque `http {}`, no dentro de un bloque `server {}`. En este proyecto la configuración se divide en archivos en `conf.d/`, que Nginx incluye automáticamente dentro del bloque `http {}` del archivo principal. Por eso colocar `limit_req_zone` al inicio de `default.conf` (fuera de cualquier bloque `server {}`) es correcto — al ser incluido, queda dentro del `http {}` implícito. Si se intentara poner dentro de un bloque `server {}`, Nginx rechazaría la configuración con error al arrancar.

#### Comparar fechas UTC con MariaDB DATETIME naive (rama 9h)

MariaDB almacena el tipo `DATETIME` sin información de zona horaria. SQLAlchemy lo lee como un objeto `datetime` de Python sin timezone (naive). Al compararlo con `datetime.now(timezone.utc)` (que sí tiene timezone, aware), Python lanza `TypeError: can't compare offset-naive and offset-aware datetimes`. Solución: añadir UTC al datetime leído de la BD antes de comparar:

```python
# rt.expira_en es naive (viene de MariaDB)
if rt.expira_en.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
    # token expirado
```

Esto ocurre en los endpoints `/auth/refresh` y `/auth/reset` al validar la expiración del token.

#### Pydantic v2 antepone "Value error," a los mensajes de validación (rama 9g)

Cuando un `@field_validator` lanza `ValueError`, Pydantic v2 prefija automáticamente el mensaje con `"Value error, "`. En el frontend, el error llega como `{"detail": [{"msg": "Value error, La contraseña debe tener al menos 8 caracteres"}]}`. Sin limpiarlo, el usuario vería ese prefijo técnico. Solución en el JS:

```javascript
const raw = datos.detail?.[0]?.msg ?? 'Error de validación';
alerta.textContent = raw.replace(/^Value error,\s*/i, '');
```

Afecta a todos los endpoints que usan `@field_validator`: registro, cambiar contraseña y reset de contraseña.

#### `unittest.mock.patch` — parchear el módulo que usa la función, no el que la define (rama 11b)

Para mockear `enviar_email_recuperacion` en los tests de recuperación de contraseña, hay que parchear la referencia en el router (`backend.app.routers.auth.enviar_email_recuperacion`), no la función original en `backend.app.auth`. Cuando el router hace `from ..auth import enviar_email_recuperacion`, crea su propia referencia local a la función. Si se parchea la función en su módulo de origen, el router sigue usando su referencia local sin parchear. Regla general: parchear siempre en el módulo que usa la función, no en el que la define.

#### Respuesta idéntica en `/auth/recuperar` independientemente de si el email existe (rama 11b)

El endpoint devuelve exactamente el mismo mensaje tanto si el email está registrado como si no: `"Si ese email está registrado, recibirás un enlace en breve"`. Esto es una decisión de seguridad deliberada para evitar la enumeración de usuarios: si la respuesta fuera diferente según si el email existe, un atacante podría automatizar peticiones con listas de emails y descubrir qué cuentas están registradas en el sistema. La misma respuesta en ambos casos no filtra ninguna información.
