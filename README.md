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

El sistema permite:

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

- [Referencia técnica](docs/referencia-tecnica.md) — arquitectura, seguridad, HTTPS, cron, logs, tests y comandos
- [Modelo de datos](docs/modelo-datos.md) — esquema de la BD y relaciones
- [Tests automáticos](docs/tests.md) — cobertura y técnicas
- [API BDNS externa](docs/api-bdns.md) — endpoints y estructura de la fuente de datos
- [Especificaciones del frontend](frontend/docs/especificaciones-frontend.md) — componentes, páginas y decisiones de diseño
- [Diseño del frontend](frontend/docs/diseño.md) — paleta, tipografía y guía visual
- [Historial de implementación](docs/historial-implementacion.md) — registro completo de funcionalidades desarrolladas

---

## Arquitectura del sistema

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
Nginx (proxy inverso, puerto 80 → redirige a 443 HTTPS)
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
| Herramientas de desarrollo | Makefile, VS Code (extensions.json incluido) |
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
- `assets/` — recursos estáticos organizados en subcarpetas: `img/` (logo, error404), `img/home/` (imágenes de portada), `img/logos/` (logos de entidades), `wireframes/` (capturas de diseño por pantalla), `guia-estilo/` (paleta, tipografía y PDF de wireframes)
- `scripts/` — utilidades de desarrollo (ver abajo)
- `index.html`, `estadisticas-epas.html`, `estadisticas-eell.html`, `recursos.html`, `buscador.html`, `entidad.html`, `login.html`, `registro.html`, `privado.html`, `exclusivo.html`, `admin.html`, `recuperar-password.html`, `reset-password.html`, `verificar-email.html` — páginas de contenido
- `404.html`, `50x.html` — páginas de error personalizadas (servidas por Nginx con `error_page`)
- `aviso-legal.html`, `privacidad.html` — páginas legales con aviso legal y política de privacidad

#### Scripts de desarrollo (`frontend/scripts/`)

- **`color-privado.sh`** — cambia los colores del banner y fondo de `privado.html` y `exclusivo.html` sin tocar el código a mano. Edita las variables CSS `--banner-privado`, `--fondo-privado` y `--hover-privado` en `styles.css`.

  ```bash
  # Interactivo (pregunta los colores uno a uno)
  ./frontend/scripts/color-privado.sh

  # Con argumentos directos
  ./frontend/scripts/color-privado.sh "#2D6A4F" "#FAF4EE" "#E8F2EC"

  # Solo cambiar el banner, dejar el resto igual
  ./frontend/scripts/color-privado.sh "#1A3429" "" ""
  ```

#### Variables CSS de la zona privada

Las páginas `privado.html` y `exclusivo.html` usan tres variables globales en `:root` (editables con el script o a mano):

| Variable | Valor actual | Uso |
|---|---|---|
| `--banner-privado` | `#2D6A4F` | Fondo del banner superior |
| `--fondo-privado` | `#FAF4EE` | Fondo del cuerpo de la página |
| `--hover-privado` | `#E8F2EC` | Hover de la tarjeta de acceso a exclusivo |

### Backend

Responsable de:

- consultar APIs externas  
- procesar los datos  
- almacenarlos en base de datos  
- exponerlos mediante API  

### Base de datos

Almacena:

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

Esto obliga a usar los documentos oficiales del BOE (XML y PDF) como fuente principal.

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

Problemas: filas partidas, importes mal parseados y valores null  
Soluciones: limpieza de texto, normalización y conversión de datos  

#### XML BOE 2025

Problemas: sin importes, inconsistencia nif/cif y sin estado  
Soluciones: parsing con BeautifulSoup, unificación de campo `cif` y `"estado": "concedida"`  

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
    privado.py       → GET /privado/perfil · PUT /privado/cambiar-nombre · PUT /privado/cambiar-contrasena · GET /privado/resumen-exclusivo · GET /privado/resumen-tabla
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

El endpoint `POST /auth/reset` revoca todos los refresh tokens activos del usuario al restablecer la contraseña, igual que hace `PUT /privado/cambiar-contrasena`.

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

### Instalación automática (recomendada)

Clona el repositorio y ejecuta el script de instalación:

```bash
git clone git@github.com:vcv-code/analisis-bdns-dgda.git
cd analisis-bdns-dgda
bash install.sh
```

El script comprueba los prerequisitos, crea el `.env`, genera el certificado SSL, levanta los contenedores y carga el dataset. Guía paso a paso con confirmación antes de cada acción que requiere permisos o modifica el sistema.

Para desinstalar y limpiar todo el entorno:

```bash
bash uninstall.sh
```

El script explica en lenguaje llano qué elimina en cada paso (contenedores, volúmenes con los datos, imagen Docker, `/etc/hosts`, `.env`, `venv/`) y pide confirmación antes de cada operación irreversible. En WSL2 avisa que también hay que editar el `hosts` de Windows.

#### Primeros pasos tras la instalación

1. Abre el navegador en la URL que muestra el script al terminar (`https://subvencionesDGDA.local` o `http://localhost`).
2. **Aviso de certificado** — el navegador mostrará *"No es seguro"* o *"Tu conexión no es privada"*. Es normal: el certificado es autofirmado para desarrollo local. Haz clic en **Avanzado → Acceder a subvencionesDGDA.local** (o equivalente en tu navegador) para continuar.
3. Para acceder al panel de administración, inicia sesión con:
   - Email: `admin@demo.com`
   - Contraseña: `Admin1234!`

**Prerequisitos:** Docker con `docker compose` v2 · Python 3.10+ · openssl
**Plataforma:** Linux · macOS · WSL2 (Windows con WSL2 y Docker Desktop)
**Espacio en disco:** ~1 GB (imágenes Docker) + ~50 MB opcionales si se crea el venv
**Descarga primera vez:** ~300-400 MB de imágenes Docker (según las que ya tengas cacheadas)

#### Flujos posibles según las respuestas

El script hace tres preguntas y toma varias decisiones automáticas:

**Pregunta 1 — `¿Continuar? [s/N]`**

| Respuesta | Resultado |
|-----------|-----------|
| `s` | La instalación continúa |
| `N` (o Enter) | El script se aborta sin modificar nada en el sistema |

##### Decisiones automáticas (sin preguntar)

Antes de continuar el script detecta si ya existen recursos y los reutiliza sin sobreescribir:

| Recurso | Si ya existe | Si no existe |
|---------|-------------|--------------|
| `docker/.env` | Se reutiliza | Se crea con contraseñas de desarrollo y `SECRET_KEY` aleatoria |
| Certificado SSL | Se reutiliza | Se genera con `openssl` (válido 1 año) |
| Base de datos con datos | No se toca | Se carga el dataset completo (primera instalación) |
| `venv/` | Se reutiliza | Primera instalación: se crea automáticamente para poder cargar el dataset. Reinstalación: se pregunta (ver pregunta 3) |
| Dominio en `/etc/hosts` | Se detecta, no se pregunta | Se pregunta (ver pregunta 2) |

El script crea también un **usuario administrador de demo** si no existe ninguno:

| Campo | Valor |
|-------|-------|
| Email | `admin@demo.com` |
| Contraseña | `Admin1234!` |
| Rol | `admin` |

Este usuario permite acceder al panel de administración en cualquier instalación limpia. Si ya existe una cuenta con ese email (instalaciones previas), `INSERT IGNORE` lo omite sin error.

Además, **siempre** (sin importar si hay datos o no):

- **Migraciones de esquema** — el script aplica `CREATE TABLE IF NOT EXISTS` y `ALTER TABLE … ADD COLUMN IF NOT EXISTS` para que la BD esté al día con el código. Son seguras de repetir: si las tablas o columnas ya existen, no hacen nada.
- **Rebuild del backend** — la imagen Docker del backend se reconstruye para que el código en ejecución coincida siempre con el código del repositorio. Gracias al caché de Docker (solo se re-ejecuta la capa de código, no `pip install`), el rebuild tarda ~10-20 s en instalaciones existentes.

#### Actualizar el proyecto (después de `git pull`)

Cada vez que se actualice el código con `git pull`, ejecutar el script es suficiente para aplicar todos los cambios:

```bash
git pull
bash install.sh   # responde 's' para continuar
```

El script detecta la BD existente, aplica las migraciones pendientes y reconstruye el backend. Los datos no se tocan.

> **Nota sobre el certificado SSL:** el certificado no forma parte del repositorio (está en `.gitignore`). Si por cualquier motivo el fichero `docker/ssl/server.crt` desapareciera (por ejemplo, tras una limpieza manual o un `git pull` en una máquina nueva), volver a ejecutar `bash install.sh` lo regenera automáticamente.
>
> **Instalación en una segunda máquina:** `bash install.sh` funciona igual en cualquier equipo con Docker. Genera un `.env` nuevo con su propia `SECRET_KEY` y `CORS_ORIGINS=*`. Los datos de subvenciones se cargan desde el dataset del repositorio, así que la BD queda idéntica. Las cuentas de usuario (registro, admin) **no** se transfieren entre máquinas — solo existe el usuario demo `admin@demo.com` / `Admin1234!` que crea el script. Si necesitas las mismas cuentas en el portátil, créalas manualmente desde el panel de administración.
>
> **Desinstalar:** `bash uninstall.sh` elimina los contenedores, volúmenes (BD y datos), certificado SSL, `docker/.env` y opcionalmente la imagen Docker y el `venv/`. También elimina la entrada de `/etc/hosts` (con confirmación, requiere sudo). La operación es irreversible para los datos.

**Pregunta 2 — `¿Añadir subvencionesDGDA.local a /etc/hosts? [s/N]`**

Esta pregunta solo aparece si el dominio no está ya en `/etc/hosts`.

| Respuesta | Resultado |
|-----------|-----------|
| `s` | Se añade el dominio con `sudo`. La app queda disponible en `https://subvencionesDGDA.local` con HTTPS completo. |
| `N` (o Enter) | El dominio no se toca. La instalación **continúa igualmente**. La app queda disponible en `http://localhost` (sin HTTPS). Ver limitaciones abajo. |

Limitaciones de acceder por `http://localhost` en vez del dominio local:

- Sin HTTPS — el navegador no mostrará el candado
- Las cookies con el flag `Secure` no se enviarán (puede afectar a la sesión en algunos navegadores)
- El enlace de recuperación de contraseña que llega por email usa la URL del dominio — no funcionará si el dominio no está en `/etc/hosts`

Para añadirlo manualmente en cualquier momento:

```bash
echo '127.0.0.1 subvencionesDGDA.local' | sudo tee -a /etc/hosts
```

**Pregunta 3 — `¿Crear entorno virtual Python (venv)? (solo para tests y scripts) [s/N]`**

Esta pregunta solo aparece si no existe ya un `venv/`. El script informa de que ocupa ~50 MB y que **no es necesario para usar la aplicación web**.

| Respuesta | Resultado |
|-----------|-----------|
| `s` | Se crea el `venv` y se instalan las dependencias de `requeriments.txt` |
| `N` (o Enter) | No se crea. La aplicación web **funciona igualmente**. Solo es necesario para ejecutar los tests (`make test`) y los scripts de parseo de datos. |

Para crearlo manualmente después si se necesita:

```bash
python3 -m venv venv && source venv/bin/activate && pip install -r requeriments.txt
```

### Instalación manual

Clonar el repositorio:

```bash
git clone git@github.com:vcv-code/analisis-bdns-dgda.git
cd analisis-bdns-dgda
```

Sincronizar repositorio:

```bash
git checkout dev
git pull
```

---

## Entorno de trabajo

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requeriments.txt
```

### Archivos de dependencias

El proyecto tiene dos archivos de requisitos con propósitos distintos:

- **`requeriments.txt` (raíz)** — librerías para el entorno local de desarrollo. Contiene únicamente las herramientas de procesamiento de datos y scripts: `pdfplumber`, `beautifulsoup4`, `lxml`, `openpyxl`, `requests` y `PyMySQL`. Es lo que se instala en el `venv` de la máquina de desarrollo para ejecutar los parsers y cargar datos. Todas las versiones están fijadas.
- **`backend/requirements.txt`** — librerías que se instalan *dentro del contenedor Docker* del backend. Solo incluye lo que necesita FastAPI para funcionar (`fastapi`, `uvicorn`, `sqlalchemy`, `pymysql`, `bcrypt`, `python-jose`, `email-validator`, `httpx` y `pytest`). No lleva pdfplumber ni pandas porque el contenedor no procesa datos, solo sirve la API. Todas las versiones están fijadas.

### Extensiones de VS Code recomendadas

El proyecto incluye `.vscode/extensions.json` con extensiones recomendadas. Al abrir la carpeta en VS Code aparece una notificación para instalarlas, o filtra por `@recommended` en el panel de extensiones.

| Extensión | Para qué |
|---|---|
| Python + Pylance + Pylint | Backend — autocompletado, tipos y linting |
| autoDocstring | Genera docstrings de Python con un atajo |
| Docker | Gestión de contenedores desde VS Code |
| Remote - WSL | Abre el proyecto desde Windows en WSL2 |
| Auto Rename Tag | Cierra etiquetas HTML automáticamente |
| Makefile Tools | Resaltado y soporte para el Makefile |
| Markdown All in One + markdownlint | README y documentación |
| Error Lens | Muestra errores y avisos inline sin pasar el ratón |
| Code Spell Checker (+ Spanish) | Corrector ortográfico en español |

---

## Docker — arrancar el sistema

El proyecto usa Docker Compose con seis servicios definidos en `docker/docker-compose.yml`:

| Servicio   | Imagen              | Función                                                   | Puerto externo    |
|------------|---------------------|-----------------------------------------------------------|-------------------|
| `db`       | mariadb:11          | Base de datos MariaDB con el dataset cargado              | 3307              |
| `backend`  | Python 3.11-slim (build) | API FastAPI                                          | ninguno (interno) |
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

### Despliegue completo (stack completo con Docker Compose)

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

## Makefile — atajos para el día a día

El proyecto incluye un `Makefile` en la raíz con los comandos más habituales:

| Comando | Qué hace |
|---|---|
| `make start` | Levanta todos los contenedores |
| `make stop` | Para los contenedores (conserva los datos) |
| `make restart` | Para y vuelve a levantar |
| `make build` | Reconstruye la imagen del backend |
| `make build-cron` | Reconstruye la imagen del cron |
| `make reload-nginx` | Recarga la config de Nginx sin reiniciar |
| `make reset-db` | Borra el volumen y recarga el dataset desde cero (pide confirmación) |
| `make cargar` | Recarga el dataset sin borrar el volumen |
| `make test` | Ejecuta los tests con pytest |
| `make test-v` | Tests con salida detallada |
| `make logs` | Últimas 100 líneas de logs del backend |
| `make logs-cron` | Últimas 50 líneas de logs del cron |
| `make logs-nginx` | Últimas 50 líneas de logs de Nginx |
| `make backup` | Vuelca la BD a un archivo `backup_YYYYMMDD_HHMMSS.sql` |
| `make shell-db` | Abre la consola MariaDB dentro del contenedor |
| `make mailpit` | Abre Mailpit en el navegador (o muestra la URL) |
| `make uninstall` | Ejecuta `uninstall.sh` para limpiar todo el entorno |

### Windows

`make` no está disponible de serie en Windows. Opciones:

- **Recomendada:** usar WSL2 y ejecutar desde la terminal Linux — `make` funciona directamente
- **Alternativa:** instalar `make` con `winget install GnuWin32.Make` y ejecutar desde PowerShell
- **Sin instalar nada:** copiar el comando del target directamente del `Makefile` y ejecutarlo en la terminal

---

## Tests

El proyecto tiene **249 pruebas en total**: 197 automáticas con pytest y 52 manuales verificadas en el navegador con Docker levantado.

| Nivel | Cantidad | Herramienta |
|-------|----------|-------------|
| Automáticos | 197 | pytest (sin Docker) |
| Manuales | 52 | Navegador + DevTools |

Los tests automáticos cubren el pipeline de datos (parsers y unificación), los endpoints de la API, el sistema de autenticación completo y la configuración de infraestructura, sin necesidad de tener Docker levantado. Usan una base de datos SQLite en memoria que se crea y destruye en cada test.

### Ejecutar todos los tests

```bash
source venv/bin/activate
pytest -v
```

### Ejecutar por módulo

```bash
# — Pipeline de datos (base del proyecto) —
pytest tests/test_unificar_datasets.py  # normalización y deduplicación del dataset
pytest tests/test_parser_epa2025.py     # helpers y flujo del parser EPA 2025

# — API pública (sin autenticación) —
pytest tests/test_smoke.py              # arranque de la API y /health
pytest tests/test_convocatorias.py      # listado de convocatorias
pytest tests/test_solicitudes.py        # filtros, paginación y exportación CSV
pytest tests/test_estadisticas.py       # /estadisticas/, /estadisticas/epas y /estadisticas/eell
pytest tests/test_agrupaciones.py       # endpoint /agrupaciones/ con relaciones completas
pytest tests/test_avisos.py             # endpoint /avisos/ — convocatorias pendientes de resolución

# — Autenticación y acceso —
pytest tests/test_auth.py               # registro y login básico
pytest tests/test_verificacion_email.py # verificación de email al registrarse
pytest tests/test_refresh_token.py      # refresh token, rotación y logout
pytest tests/test_recuperar_password.py # recuperación de contraseña por email
pytest tests/test_privado.py            # zona privada: cambiar contraseña y nombre
pytest tests/test_admin.py              # panel de administración completo

# — Infraestructura —
pytest tests/test_logging.py            # middleware y configuración de logging
pytest tests/test_https_config.py       # certificado SSL y configuración Nginx HTTPS
pytest tests/test_cache_headers.py      # cabeceras Cache-Control en /convocatorias/ y /estadisticas/
pytest tests/test_rate_limiting.py      # configuración de rate limiting en Nginx
```

### Resultado esperado

```text
181 passed   # excluyendo test_https_config.py y test_rate_limiting.py (requieren Docker+Nginx)
197 passed   # suite completa con Docker levantado
```

Para el detalle completo de cada test (tipo, técnica de caja y qué comprueba exactamente) ver [`docs/tests.md`](docs/tests.md).

### Pruebas de integración end-to-end (manuales)

Complementan a los tests automáticos verificando el stack completo: Nginx → FastAPI → MariaDB real. Se realizan desde `http://localhost/docs` con Docker levantado y cubren filtros con datos reales, paginación, flujo de registro y login, acceso con y sin token, y la respuesta de los manejadores de error. Ver la sección "Prueba manual rápida" en [`docs/tests.md`](docs/tests.md).

#### Pruebas manuales del panel de administración

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
| Usuario inactivo en tabla | ✅ Muestra badge "Inactivo" con botón "Activar" | user@example .com visible correctamente |
| Selector de logs (50 líneas) | ✅ Recarga con número correcto | Logs reflejan intentos fallidos del proceso de debug |

---

## Flujo de trabajo

El proyecto sigue un flujo basado en main + dev + feature/*, un modelo híbrido entre Git Flow y GitHub Flow, adaptado a equipos pequeños.

### Estructura

```text
main (producción, estable)
 │
 └── dev (desarrollo)
       │
       ├── feature/*(funcionalidad)
       └── feature/*(funcionalidad)
```

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

## Estado actual

Fase: **backend completado · HTTPS activo · cron con auto-detección de resoluciones · caché y rate limiting activos · autenticación completa (JWT · refresh token · verificación email · recuperación contraseña) · Mailpit activo · frontend integrado · panel de administración completo con visor de logs · zona privada con nombre/alias editable · medidas anti-bots activas · modal de conclusiones con textos reales · instalación y desinstalación automatizadas (install.sh + uninstall.sh + Makefile) · revisión accesibilidad WCAG 2.2 completada · CSS limpio y consolidado en styles.css · navbar responsive con hamburguesa ≤900px · modal de entidad unificado · sistema de color coherente (verde/crema/morado/ámbar) · imagen hero (Pixabay, licencia libre) · auditoría de seguridad completada · ordenación server-side en buscador · auditoría responsive móvil completada · mapa táctil con doble toque · navbar con Exclusivo y Mi perfil**


→ Ver [historial completo de implementación](docs/historial-implementacion.md)

---

## Notas técnicas

- `solicitudes.html` se conserva intencionalmente aunque la URL pública es ahora `buscador.html`. Actúa como redirección de compatibilidad para cualquier enlace externo o marcador guardado antes del renombrado. No es un archivo huérfano: es legacy deliberado.
- `data/raw/` no se versiona completo; se mantienen ejemplos representativos. Los scripts sobrescriben resultados al volver a ejecutarse — el sistema es reproducible desde cero.
- El campo `email_verificado` en `usuarios` tiene `DEFAULT 1` en la migración (para no bloquear cuentas existentes), pero `POST /auth/registro` siempre lo establece a `0` explícitamente.
- El campo `nombre` en `usuarios` es nullable — los usuarios existentes quedan intactos. Migración para instalaciones ya existentes: `ALTER TABLE usuarios ADD COLUMN nombre VARCHAR(100) NULL AFTER email;`
- El botón "Cerrar sesión" del navbar usa la clase `btn-login` (igual que "Acceder"). Antes tenía `btn-login btn-texto` o inline `background:none` que eliminaban el fondo verde pero dejaban el texto blanco, haciéndolo invisible. Corregido usando solo `btn-login` con `border: none` y `font-family: inherit` en el CSS para cubrir los defaults del elemento `<button>`.
- `min-height: calc(100vh - var(--altura-nav))` en `.fondo-stats` causaba un espacio vacío grande antes del footer cuando el contenido no llenaba la pantalla — se anuló con `min-height: auto` en el override de `.pagina-inicio .fondo-stats`.
- Chart.js: `formatearEjeY` usa `.toFixed(0)` que redondea 7,5 → 8, generando ticks duplicados si el rango del eje es pequeño y `stepSize` no es múltiplo entero de 1000. Solución: callback personalizado `(k % 1 === 0 ? k : k.toFixed(1)) + ' K'`.
- CSS: las clases del ranking CCAA en `estadisticas-eell.js` usaban `ranking-lista__item` (BEM incorrecto) mientras el CSS definía `.ranking-item`. Corregido — el ranking aparecía sin formato hasta entonces.

---

### Bugs encontrados durante la implementación del panel de administración

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

### Tests que fallaron en la primera ejecución

Al ejecutar `test_admin.py` por primera vez, dos tests fallaron y pusieron de manifiesto diferencias concretas entre SQLite (BD de tests) y MariaDB (BD de producción):

**`test_listar_avisos_devuelve_sin_resolucion`** — el helper de test insertaba una convocatoria con `fecha_resolucion="2025-01-01"` (string). SQLite acepta strings en columnas DATE en MariaDB pero el dialecto SQLAlchemy para SQLite lanza `TypeError: SQLite Date type only accepts Python date objects as input`. Corregido pasando `date(2025, 1, 1)` (objeto `datetime.date`). Esto no es un problema en producción con MariaDB, que acepta ambos formatos, pero sí revela que los tests deben usar tipos Python correctos siempre.

**`test_eliminar_aviso_con_solicitudes_devuelve_409`** — el helper creaba un `Beneficiario` con `tipo_benef="epa"`, que no es un valor válido en el ENUM del modelo (`asociacion` o `entidad_local`). MariaDB almacena strings y no valida el ENUM al escribir en modo no estricto, pero SQLAlchemy sí lo valida en memoria al hacer `db.refresh()`. Corregido usando `tipo_benef="asociacion"`. Este caso ilustra la diferencia habitual entre SQLite/SQLAlchemy y MariaDB en la validación de ENUMs: en tests hay que ceñirse a los valores del modelo Python, no confiar en la tolerancia de la BD.

---

### Decisiones y problemas técnicos de implementaciones anteriores

#### Cron — Supercronic incompatible con Docker + WSL2

La primera aproximación para el scheduler fue usar [Supercronic](https://github.com/aptible/supercronic), un cron diseñado para contenedores Docker. Falló con un error de fork al arrancar en el entorno Docker + WSL2 incluso con la opción `--debug`. Solución: scheduler implementado directamente en Python (`docker/cron/scripts/scheduler.py`) usando `time.sleep()` y comprobaciones de hora/día. Sin dependencias de binarios externos, sin permisos especiales, reproducible en cualquier entorno. Lección: en Docker, preferir código Python antes que binarios del sistema cuando el entorno de destino (WSL2) puede tener restricciones de llamadas al sistema.

#### HTTPS — `subjectAltName` obligatorio en navegadores modernos

Al generar el certificado autofirmado con `openssl`, es imprescindible incluir la extensión `subjectAltName (SAN)` además del `Common Name (CN)`. Chrome (desde 2017) y otros navegadores modernos rechazan certificados que no tengan el dominio también en el SAN, aunque el CN coincida exactamente. Sin SAN, el navegador muestra error de certificado aunque HTTPS esté configurado correctamente. El comando `openssl req` requiere el flag `-addext "subjectAltName=DNS:subvencionesDGDA.local"` o el uso de un archivo de extensiones.

#### HTTPS — flag `-nodes` en `openssl`

Al generar la clave privada, hay que incluir `-nodes` (no DES) para que la clave no esté protegida por contraseña. Sin este flag, OpenSSL protege la clave con una contraseña que hay que introducir manualmente cada vez que Nginx arranca. En un contenedor Docker, el inicio es no interactivo — sin `-nodes`, Nginx se quedaría bloqueado esperando la contraseña y el contenedor no arrancaría.

#### `limit_req_zone` en `default.conf`

La directiva `limit_req_zone` de Nginx debe ir dentro del bloque `http {}`, no dentro de un bloque `server {}`. En este proyecto la configuración se divide en archivos en `conf.d/`, que Nginx incluye automáticamente dentro del bloque `http {}` del archivo principal. Por eso colocar `limit_req_zone` al inicio de `default.conf` (fuera de cualquier bloque `server {}`) es correcto — al ser incluido, queda dentro del `http {}` implícito. Si se intentara poner dentro de un bloque `server {}`, Nginx rechazaría la configuración con error al arrancar.

#### Comparar fechas UTC con MariaDB DATETIME naive

MariaDB almacena el tipo `DATETIME` sin información de zona horaria. SQLAlchemy lo lee como un objeto `datetime` de Python sin timezone (naive). Al compararlo con `datetime.now(timezone.utc)` (que sí tiene timezone, aware), Python lanza `TypeError: can't compare offset-naive and offset-aware datetimes`. Solución: añadir UTC al datetime leído de la BD antes de comparar:

```python
# rt.expira_en es naive (viene de MariaDB)
if rt.expira_en.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
    # token expirado
```

Esto ocurre en los endpoints `/auth/refresh` y `/auth/reset` al validar la expiración del token.

#### Pydantic v2 antepone "Value error," a los mensajes de validación

Cuando un `@field_validator` lanza `ValueError`, Pydantic v2 prefija automáticamente el mensaje con `"Value error, "`. En el frontend, el error llega como `{"detail": [{"msg": "Value error, La contraseña debe tener al menos 8 caracteres"}]}`. Sin limpiarlo, el usuario vería ese prefijo técnico. Solución en el JS:

```javascript
const raw = datos.detail?.[0]?.msg ?? 'Error de validación';
alerta.textContent = raw.replace(/^Value error,\s*/i, '');
```

Afecta a todos los endpoints que usan `@field_validator`: registro, cambiar contraseña y reset de contraseña.

#### `unittest.mock.patch` — parchear el módulo que usa la función, no el que la define

Para mockear `enviar_email_recuperacion` en los tests de recuperación de contraseña, hay que parchear la referencia en el router (`backend.app.routers.auth.enviar_email_recuperacion`), no la función original en `backend.app.auth`. Cuando el router hace `from ..auth import enviar_email_recuperacion`, crea su propia referencia local a la función. Si se parchea la función en su módulo de origen, el router sigue usando su referencia local sin parchear. Regla general: parchear siempre en el módulo que usa la función, no en el que la define.

#### Respuesta idéntica en `/auth/recuperar` independientemente de si el email existe

El endpoint devuelve exactamente el mismo mensaje tanto si el email está registrado como si no: `"Si ese email está registrado, recibirás un enlace en breve"`. Esto es una decisión de seguridad deliberada para evitar la enumeración de usuarios: si la respuesta fuera diferente según si el email existe, un atacante podría automatizar peticiones con listas de emails y descubrir qué cuentas están registradas en el sistema. La misma respuesta en ambos casos no filtra ninguna información.

---

---

## Limitaciones conocidas del dato de origen

- **Punto final en nombres de entidades**: la BDNS registra los nombres tal cual los declararon las entidades en su momento. Algunas incluyen punto final ("ASOCIACIÓN GATO AYUD.") y otras no. Es una inconsistencia de la fuente, no un bug. No se normaliza en el frontend para no crear divergencias con el CSV exportado y la API.

- **Expedientes con resolución tardía — aparecen en dos convocatorias**: algunas entidades presentaron solicitud en un año pero la resolución se publicó en el BOE del año siguiente. El pipeline las registra en ambas convocatorias porque cada dataset se procesa de forma independiente. Casos identificados:
  - **EPA** — *La Sexta Huella* (`SUBV2022659`): excluida en 2022, concedida en 2023; aparece dos veces en EPA 2023, lo que infla ligeramente su importe acumulado en estadísticas (~9.130 € en vez de ~4.446 €).
  - **EPA** — *Amibichos* (`2023B628`): excluida en 2023, concedida en 2024; aparece dos veces en EPA 2024.
  - **EELL** — *Casavieja* y *Castilforte*: ambas `no_beneficiaria` en 2023, sin impacto económico.
  - El número de expediente puede variar en formato entre años (`SUBV…`, `2023B…`, sin prefijo), lo que dificulta la deduplicación automática cross-year.
  - Causa raíz: `cargar_dataset.py` asigna cada solicitud a la convocatoria de su dataset sin comprobar si el expediente ya existe en otra convocatoria. La corrección requeriría lógica adicional en el pipeline de carga.

---

## Mejoras futuras

Mejoras identificadas durante el desarrollo, no planificadas para la entrega actual. Agrupadas por ámbito.

### Datos y análisis

- **`num_convoc` en convocatorias históricas (2021–2025):** el campo existe en el modelo pero está a NULL para las convocatorias cargadas desde CSV/PDF (las fuentes históricas no incluían el número BDNS). Se podría rellenar manualmente consultando infosubvenciones.es. No afecta a ninguna funcionalidad actual.
- **Campo `linea` para EPA 2024** — la Orden modificada ya estaba en vigor pero el BOE de 2024 no desglosa la línea por entidad en las tablas parseadas. Si se revisa el parser, el campo `linea` ya está preparado en el modelo.
- **Cofinanciación EELL** — aporta puntos en la evaluación pero no modifica el importe concedido. Solo disponible en el ANEXO V del XML 2025; no existe en los PDF de 2023/2024.
- **Causas de exclusión EPA** — el BOE las incluye pero con un formato diferente al de EELL; requieren un parser específico.
- **Provincia/CCAA para EPA (asociaciones)** — no es derivable del CIF tipo G de forma estándar.

### Funcionalidades y UX

- **Paginación en `/admin/usuarios`** — la tabla de usuarios no pagina; con pocos usuarios actuales no es problema pero escalaría mal.
- **Retry en cron si BDNS API no responde** — el cron falla silenciosamente si BDNS devuelve error; añadir reintentos con backoff exponencial.
- **Logs de cron en panel admin** — mostrar `bdns_check.log` y `health_check.log` en el panel. Requiere: montar `../logs/cron` en el contenedor backend, dos endpoints nuevos en `admin.py` y dos secciones en `admin.html` / `admin.js`.
- **Trampa de foco en menú hamburguesa** — el menú cierra con Esc y click fuera, pero Tab no cicla dentro del menú abierto. Mejora de accesibilidad WCAG 2.4.3 pendiente.
- **Autogeneración de `models.py`** — usar `sqlacodegen` para generar el ORM de SQLAlchemy directamente desde el esquema de la BD, en lugar de mantenerlo a mano.
- **Login con terceros (OAuth)** — integración con Google.
- **Conclusiones en modales EELL/home** — los textos de los modales de estadísticas EELL podrían ampliarse con análisis comparativos entre convocatorias.

### Producción y seguridad

- **Dominio real y certificado Let's Encrypt** — sustituir el certificado autofirmado por uno de Let's Encrypt (gratuito, renovación automática, confiado por todos los navegadores).
- **Puerto de base de datos** — en producción eliminar la exposición del puerto `3307` en `docker-compose.yml`; la BD y el backend se comunican dentro de la red Docker sin necesidad de exponer el puerto al host.
- **CORS con dominio específico** — cambiar `CORS_ORIGINS=*` por `CORS_ORIGINS=https://mi-dominio.com` en `docker/.env` (ya implementado mediante variable de entorno, solo requiere configuración).
- **CAPTCHA en registro** — reCAPTCHA o hCaptcha para bloquear bots sofisticados. Requiere dependencia de terceros y añade fricción al usuario; desproporcionado para este proyecto en su estado actual.
- **Blocklist de dominios desechables** — bloquear `mailinator.com`, `guerrillamail.com` y similares al registrarse. Hay cientos de dominios y se actualizan constantemente; coste de mantenimiento alto para el beneficio obtenido.
