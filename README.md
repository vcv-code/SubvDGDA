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
- `js/` — un archivo JS por página (`home.js`, `solicitudes.js`, `estadisticas-epas.js`, `estadisticas-eell.js`, `recursos.js`, `auth.js`, `privado.js`, `entidad.js`, `recuperar-password.js`, `reset-password.js`)
- `assets/` — logotipo, imágenes y wireframes en PDF
- `index.html`, `estadisticas-epas.html`, `estadisticas-eell.html`, `recursos.html`, `solicitudes.html`, `entidad.html`, `login.html`, `registro.html`, `privado.html`, `recuperar-password.html`, `reset-password.html` — páginas implementadas

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
    auth.py          → POST /auth/registro · POST /auth/login · POST /auth/refresh · POST /auth/logout · POST /auth/recuperar · POST /auth/reset
    privado.py       → GET /privado/perfil · GET /privado/resumen-exclusivo · PUT /privado/cambiar-contrasena
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

## Estado actual

Fase: **backend completado · HTTPS activo · cron verificado · caché y rate limiting activos · autenticación completa con recuperación de contraseña · Mailpit activo · frontend integrado · tramo y agrupaciones expuestos · UX buscador mejorada**

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
✔ tests automáticos con pytest (157 tests — smoke, funcionales, unitarios, seguridad, rendimiento, configuración)
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
  · test_rate_limiting.py (5): configuración de rate limiting en Nginx para /auth/login
  · test_privado.py (6): cambiar contraseña — contraseña actual incorrecta, nueva débil, cambio correcto, login con nueva/vieja contraseña
  · test_refresh_token.py (7): refresh token — login devuelve token, renovación, rotación, token inválido, logout revoca, cambio contraseña revoca tokens
  · test_recuperar_password.py (9): recuperación contraseña — email existente/inexistente, token creado en BD, email enviado, reset válido, token inválido/usado/expirado, contraseña débil
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
  · ver [`docs/https.md`](docs/https.md) para reproducir el entorno
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
  · `check_bdns.py` — consulta la API BDNS en temporada (mar–jun), detecta nuevas convocatorias DGDA,
    inserta en BD con fecha_resolucion=NULL, guarda estado en `logs/cron/estado_YYYY.json`
    (frecuencia por tramos: cada 2 días en abr–may, cada 4 días en mar–jun)
  · `health_check.py` — llama a GET /health cada 6 horas y loguea el resultado
  · logs persistidos en `logs/cron/` como volumen Docker
✔ GET /avisos/ — devuelve convocatorias del año actual con fecha_resolucion=NULL para el banner de la web
✔ banner de avisos en `index.html`: aparece cuando el cron inserta una nueva convocatoria y desaparece
  automáticamente cuando a fin de año se carga la resolución del BOE (fecha_resolucion ya no es NULL)
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
✔ rate limiting en Nginx para prevenir fuerza bruta en el login
  · `limit_req_zone $binary_remote_addr zone=login:10m rate=10r/m` — 10 peticiones/minuto por IP
  · `location = /auth/login` con `burst=5 nodelay` y `limit_req_status 429`
  · el resto de la API no está limitada

Pendiente:

### Pendientes de frontend

- **Mapa de calor CCAA** en `estadisticas-eell.html`: el ranking CCAA ya funciona, pero el mapa choropleth está pendiente de decisión técnica (SVG inline, Leaflet o D3-geo).
- Avisos y notas en la web: indicar que los datos pueden contener errores y que conviene contrastarlos con las fuentes oficiales
- Ficha de entidad como modal/popup: mostrar en overlay al hacer clic en una fila, conservando la búsqueda al cerrar
- Contenido de la página privada (`privado.html`): tabla resumen con datos por año y estado, separada por tipo
- **Footer — revisar enlaces**: actualmente muestra GitHub, Documentación y Contacto. Pendiente: sustituir por Aviso legal (obligatorio si se publica) y decidir si mantener Contacto (valorar implicaciones de privacidad según los datos que se exponen).
- **Home — sección de PDFs oficiales**: hay espacio vacío entre los gráficos y el footer. Posible sección con los documentos BOE de cada convocatoria: título, enlace para ver en el BOE y enlace de descarga directa. Futura adición, no urgente.
- Política de privacidad y aviso legal
- Accesibilidad (a11y): revisar contraste, navegación por teclado y atributos ARIA
- **Página Recursos — colores por sección**: los logos ya están uniformes (height 80px + object-fit:contain). Pendiente: asignar un color de fondo diferente a cada una de las 4 secciones (Protección animal, Colonias felinas, EPAs, EELL) para diferenciarlas visualmente.
- **Refactor CSS inline** *(post-entrega, solo si hay tiempo)*: el proyecto acumula estilos inline en el HTML que deberían estar como clases en `styles.css`. No es urgente ni afecta a la funcionalidad, pero mejora el mantenimiento. Hacerlo página por página comprobando visualmente que nada se rompe. Regla para código nuevo: `display:none` en HTML está bien; todo lo demás va a `styles.css`.

### Pendientes de backend y API

- Panel de administración: endpoint y dashboard para que los usuarios con rol `admin` puedan gestionar cuentas (listar, activar/desactivar, cambiar rol)

### Pendientes de infraestructura y despliegue

- Dominio real y certificado Let's Encrypt: en producción sustipues stuir el certificado autofirmado por uno de Let's Encrypt (gratuito, renovación automática, confiado por todos los navegadores)
- CORS con dominio específico: sustituir `allow_origins=["*"]` en `main.py` por el dominio real una vez definido
- Script de instalación automática: script (SSH u otro mecanismo visto en clase) que instale dependencias con versiones fijadas, descargue y cargue la base de datos, y deje el sistema listo para arrancar; debe incluir la adición automática de `subvencionesDGDA.local` al `/etc/hosts` (requiere permisos de administrador — en Linux con `sudo tee -a`, en Windows con PowerShell como admin)
- Puerto de base de datos: en producción eliminar la exposición del puerto `3307` en `docker-compose.yml`; la BD y el backend se comunican dentro de la red Docker

### Pendientes de usuarios y autenticación

- Login con terceros (OAuth) *(mejora futura, fuera del alcance de la entrega)*: integración con Google y/o GitHub; los wireframes ya contemplan los botones de acceso social

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
| **Base de datos** (nuevo año / resolución) | Nuevo dataset parseado | `python -m scripts.data_processing.cargar_dataset` con el nuevo JSON | Solo añade filas, nunca borra |

**Caché del navegador** (JS/CSS): si el navegador muestra una versión antigua del frontend después de un cambio, Ctrl+Shift+R fuerza la recarga ignorando la caché local. En DevTools → Network → "Disable cache" para depurar sin caché.

**Caché HTTP de la API** (Cache-Control): los endpoints `/convocatorias/` (1 día) y `/estadisticas/` (1 hora) devuelven cabeceras `Cache-Control`. FastAPI no cachea internamente — los datos siempre vienen de la BD. Si se actualiza la BD y se quiere que el navegador vea los nuevos datos antes de que expire la caché, basta con hacer Ctrl+Shift+R.

**Volumen de la BD**: `docker compose down` para los contenedores pero **conserva** el volumen con todos los datos. Solo `docker compose down -v` borra el volumen — usar únicamente para reset total desde cero.

---

## Tests

El proyecto tiene **193 pruebas en total**: 148 automáticas con pytest y 45 manuales verificadas en el navegador con Docker levantado.

| Nivel | Cantidad | Herramienta |
|-------|----------|-------------|
| Automáticos | 148 | pytest (sin Docker) |
| Manuales | 45 | Navegador + DevTools |

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
pytest tests/test_unificar_datasets.py  # funciones de normalización del pipeline
pytest tests/test_parser_epa2025.py     # helpers y flujo del parser EPA 2025
```

### Resultado esperado

```text
130 passed   # excluyendo test_https_config.py y test_rate_limiting.py (requieren Docker+Nginx)
148 passed   # suite completa con Docker levantado
```

Para el detalle completo de cada test (tipo, técnica de caja y qué comprueba exactamente) ver [`docs/tests.md`](docs/tests.md).

### Pruebas de integración end-to-end (manuales)

Complementan a los tests automáticos verificando el stack completo: Nginx → FastAPI → MariaDB real. Se realizan desde `http://localhost/docs` con Docker levantado y cubren filtros con datos reales, paginación, flujo de registro y login, acceso con y sin token, y la respuesta de los manejadores de error. Ver la sección "Prueba manual rápida" en [`docs/tests.md`](docs/tests.md).

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

---

## Notas técnicas

- data/raw/ no se versiona completo
- se mantienen ejemplos
- los scripts sobrescriben resultados
- sistema reproducible
