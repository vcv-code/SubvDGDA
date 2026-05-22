# Análisis de subvenciones de bienestar animal (BDNS + DGDA)

Proyecto intermodular de **2º FPGS Desarrollo de Aplicaciones Web (DAW)**.

---

## Autores

Proyecto desarrollado por:

- [Miyuki Salvador](https://github.com/ImiuCreative)
- [Verónica Corpa](https://github.com/vcv-code)

---

## Índice

- **Proyecto**
  - [Objetivos del proyecto](#objetivos-del-proyecto)
  - [Tecnologías](#tecnologías)
  - [Estructura del proyecto](#estructura-del-proyecto)
  - [Documentación técnica](#documentación-técnica)
  - [Arquitectura del sistema](#arquitectura-del-sistema)
- **Datos**
  - [Fuentes de datos analizadas](#fuentes-de-datos-analizadas)
  - [Fuentes oficiales DGDA (BOE)](#fuentes-oficiales-dgda-boe)
  - [Pipeline de datos](#pipeline-de-datos)
  - [Scripts de datos](#scripts-de-datos)
  - [Validación de datos](#validación-de-datos)
  - [Dataset final](#dataset-final)
- **Aplicación**
  - [Descripción general del proyecto](#descripción-general-del-proyecto)
    - [Base de datos](#base-de-datos)
    - [Backend](#backend)
    - [Frontend](#frontend)
      - [Capturas](#capturas)
      - [Compatibilidad de navegadores](#compatibilidad-de-navegadores)
- **Instalación y uso**
  - [Desarrollo](#desarrollo)
    - [Requisitos del sistema](#requisitos-del-sistema)
  - [Entorno de trabajo](#entorno-de-trabajo)
  - [Docker — arrancar el sistema](#docker--arrancar-el-sistema)
    - [Nginx — qué hace exactamente](#nginx--qué-hace-exactamente)
    - [Tamaño de las imágenes Docker](#tamaño-de-las-imágenes-docker)
  - [Makefile — atajos para el día a día](#makefile--atajos-para-el-día-a-día)
  - [Tests](#tests)
    - [Automáticos (pytest)](#ejecutar-todos-los-tests)
    - [Manuales — integración E2E](#pruebas-de-integración-end-to-end-manuales)
- **Proceso y estado**
  - [Flujo de trabajo](#flujo-de-trabajo)
  - [Gestión del proyecto](#gestión-del-proyecto)
  - [Estado actual](#estado-actual)
  - [Buenas prácticas aplicadas](#buenas-prácticas-aplicadas)
- **Apéndices**
  - [Notas técnicas](#notas-técnicas)
  - [Limitaciones conocidas del dato de origen](#limitaciones-conocidas-del-dato-de-origen)
  - [Mejoras futuras](#mejoras-futuras)

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
- [Pipeline de datos](docs/pipeline-datos.md) — API BDNS, parsers, herramientas, problemas resueltos y organización del dataset
- [Modelo de datos](docs/modelo-datos.md) — esquema de la BD y relaciones
- [Sistema de autenticación](docs/autenticacion.md) — JWT, access/refresh token, rotación, verificación email, honeypot
- [Tests automáticos](docs/tests.md) — cobertura y técnicas
- [Especificaciones del frontend](frontend/docs/especificaciones-frontend.md) — componentes, páginas y decisiones de diseño
- [Diseño del frontend](frontend/docs/diseño.md) — paleta, tipografía y guía visual
- [Patrones JavaScript](frontend/docs/patrones.md) — URLSearchParams, history, fetch, auth cliente, delegación de eventos
- [Historial de implementación](docs/historial-implementacion.md) — registro completo de funcionalidades desarrolladas

---

## Arquitectura del sistema

El sistema sigue una arquitectura cliente–servidor basada en una API REST. Todos los servicios corren en contenedores Docker orquestados con `docker compose`.

```text
API externa BDNS + PDFs/XML BOE
          ↓  (scripts de parseo, se ejecutan una vez)
    Base de datos MariaDB
          ↓
    Backend FastAPI  ←──── Cron (sincronización automática con BDNS)
          ↓
    Nginx (puerto 443 HTTPS)
     ├── /api/*  → proxy al backend (puerto 8000 interno)
     └── /*      → archivos estáticos del frontend
          ↓
    Navegador (HTML + CSS + JS vanilla)
```

**Flujo de una petición típica:**

1. El navegador carga `buscador.html` desde Nginx (archivo estático)
2. El JS hace `fetch('/solicitudes/?tipo=epa&...')` al mismo dominio
3. Nginx redirige la petición al backend FastAPI
4. FastAPI consulta MariaDB y devuelve JSON
5. El JS pinta los resultados en la tabla

**Cron:** contenedor independiente que cada pocos días comprueba la API de BDNS para detectar nuevas convocatorias y actualizar la `fecha_resolucion` de las convocatorias pendientes cuando BDNS la publica (hace desaparecer el aviso de la home automáticamente). El contenido de las resoluciones —beneficiarios e importes— no se descarga automáticamente: requiere ejecutar los parsers del BOE manualmente.

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

## Estructura del proyecto

```text
analisis-bdns-dgda/
├── .gitignore              ← archivos excluidos del repositorio (venv, .env, SSL, datos raw…)
├── install.sh              ← instalación automática
├── uninstall.sh            ← desinstalación guiada
├── Makefile                ← atajos de desarrollo
├── requeriments.txt        ← dependencias Python para scripts locales (parsers, carga de datos)
│
├── backend/
│   ├── app/
│   │   ├── routers/        ← endpoints FastAPI
│   │   ├── models.py       ← ORM SQLAlchemy
│   │   ├── schemas.py      ← validación Pydantic
│   │   └── auth.py         ← JWT y funciones de autenticación
│   └── requirements.txt    ← dependencias del contenedor Docker (FastAPI, SQLAlchemy…)
│
├── frontend/
│   ├── css/styles.css      ← hoja de estilos compartida
│   ├── js/                 ← un archivo JS por página
│   ├── assets/             ← imágenes, logos, wireframes
│   ├── docs/               ← especificaciones y diseño frontend
│   └── *.html              ← páginas de la aplicación
│
├── docker/
│   ├── docker-compose.yml  ← define los 6 servicios, red interna y volúmenes
│   ├── nginx/default.conf  ← proxy inverso + HTTPS + rate limiting
│   ├── cron/               ← scheduler Python
│   └── init/               ← SQL inicial y migraciones
│
├── data/
│   ├── raw/                ← XMLs y PDFs del BOE descargados
│   ├── processed/          ← JSONs intermedios por año
│   └── final/dataset_unificado.json
│
├── scripts/
│   ├── data_processing/    ← parsers EPA y EELL, carga de BD
│   └── ingestion/          ← cliente API BDNS
│
├── docs/                   ← referencia técnica, modelo datos, tests
│   └── img/                ← diagramas ER y capturas de pantalla (README)
└── tests/                  ← 223 funciones de test pytest (321 ejecuciones)
```

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

## Fuentes oficiales DGDA (BOE)

Las resoluciones de concesión no aparecen en la API BDNS — se obtienen directamente de los documentos oficiales publicados en el BOE.

### Datos de protectoras (EPA) — XML BOE

| Campo | Descripción |
|-------|-------------|
| CIF | Identificador fiscal de la entidad |
| Expediente | Número de expediente de la solicitud |
| Entidad | Nombre de la protectora |
| Puntuación | Puntuación obtenida en la evaluación |
| Importe | Importe concedido (€) |
| Estado | Concedida / No beneficiaria / Excluida / Desistida |

### Datos de ayuntamientos (EELL) — PDF (2023–2024) y XML+Excel (2025)

| Campo | Descripción |
|-------|-------------|
| NIF / CIF | Identificador fiscal del ayuntamiento |
| Expediente | Número de expediente |
| Entidad | Nombre del ayuntamiento o mancomunidad |
| Puntuación | Puntuación obtenida |
| Importe | Importe concedido (€) |
| Estado | Concedida / No beneficiaria / Excluida / Desistida |
| Tramo | Tramo poblacional (T1/T2/T3) — solo EELL 2025 |

**Agrupaciones municipales:** varios ayuntamientos pueden presentarse conjuntamente. En ese caso el importe aparece a nombre del representante, pero en EELL 2025 el Excel complementario incluye el desglose individual por municipio miembro (`agrupacion_miembros`), con el importe asignado a cada uno.

---

## Pipeline de datos

La API BDNS proporciona convocatorias pero no incluye los beneficiarios reales de las subvenciones de la DGDA. Los datos de concesiones se obtienen de documentos oficiales del BOE (XML, PDF, Excel) y se procesan mediante un pipeline de parseo, normalización y carga:

```text
XML / PDF / Excel BOE (DGDA)
      ↓  pdfplumber · BeautifulSoup · openpyxl
JSON por año (data/processed/)
      ↓  unificar_datasets.py
data/final/dataset_unificado.json
      ↓  cargar_dataset.py
MariaDB — 6 pasos: convocatorias → beneficiarios → solicitudes
          → concesiones → agrupaciones → agrupacion_miembros
```

Fuentes por tipo:

- **EPA** (protectoras) — XML BOE · 2021–2025 · parser base + parser 2025 separado por cambio de cabeceras
- **EELL** (ayuntamientos) — PDF 2023–2024 + XML y Excel 2025 (tablas publicadas como imagen en el BOE)

Los principales problemas técnicos resueltos (parsers inconsistentes entre años, duplicados cross-year, derivación de provincia/CCAA desde CIF, periodo semestral EPA 2023–2024) están documentados en detalle en [docs/pipeline-datos.md](docs/pipeline-datos.md).

---

## Scripts de datos

Los scripts transforman los datos crudos (XMLs, PDFs, Excel del BOE) en el dataset unificado que después se carga en la base de datos. El pipeline completo se describe en [docs/pipeline-datos.md](docs/pipeline-datos.md).

### BDNS

`scripts/ingestion/bdns_client.py` — consulta la API pública de BDNS para obtener convocatorias y comprobar si se ha publicado la fecha de resolución de convocatorias pendientes.

### Extracción de datos

`scripts/data_extractor/` — descarga los documentos del BOE (XML y PDF) con los datos de concesiones.

### Procesamiento

`scripts/data_processing/` — parsers para cada tipo de fuente (EPA XML, EELL PDF/Excel), normalización de estados, unificación del dataset y carga en la base de datos (`cargar_dataset.py`).

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

## Descripción general del proyecto

### Base de datos

**Motor:** MariaDB 11 en contenedor Docker. El esquema se crea automáticamente al instalar (`docker/init/modelo-fisico.sql`). SQLAlchemy actúa como ORM entre Python y la BD.

**Tablas principales:**

| Grupo | Tablas |
|-------|--------|
| Datos de subvenciones | `convocatorias`, `beneficiarios`, `solicitudes`, `concesiones` |
| Agrupaciones EELL | `agrupaciones`, `agrupacion_miembros` |
| Usuarios y autenticación | `usuarios`, `refresh_tokens`, `reset_tokens`, `verificacion_tokens` |

**Acceso en desarrollo:**

```bash
make shell-db          # consola MariaDB dentro del contenedor
http://localhost:8080  # Adminer (interfaz web, usuario/contraseña en docker/.env)
```

Ver el esquema completo con relaciones en [docs/modelo-datos.md](docs/modelo-datos.md).

#### Diagramas ER

<table>
  <tr>
    <th>Original</th>
    <th>Revisado</th>
  </tr>
  <tr>
    <td><img src="docs/img/modelo-datos-er-v1.png" width="360" alt="Diagrama ER original"></td>
    <td><img src="docs/img/Modelo-ER-Def.jpg" width="360" alt="Diagrama ER definitivo"></td>
  </tr>
</table>

### Backend

API REST construida con **FastAPI** (Python), **SQLAlchemy** como ORM y **MariaDB** como base de datos. Se sirve con `uvicorn` dentro de un contenedor Docker; Nginx actúa como proxy inverso y punto de entrada HTTPS.

**Autenticación y sesión:**
JWT con doble token: `access_token` de corta duración (15 min) para cada petición y `refresh_token` persistente (30 días) para renovarlo sin volver a hacer login. Las contraseñas se hashean con `bcrypt` directamente (sin passlib). El registro valida mínimo 8 caracteres, mayúscula, minúscula y número. Cambiar o restablecer la contraseña revoca todos los refresh tokens activos del usuario.

**Seguridad:**

- Rate limiting en Nginx (HTTP 429 sin llegar al backend): `POST /auth/login` (10 req/min, burst 5), `POST /auth/registro` (5 req/min, burst 3), `POST /auth/recuperar` (3 req/min, burst 2)
- Cabeceras de seguridad en todas las respuestas: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Strict-Transport-Security` (HSTS 1 año)
- SRI (`integrity`) en los 5 recursos CDN del frontend (Chart.js ×3, Leaflet JS, Leaflet CSS)
- Cabeceras `Cache-Control`: `/convocatorias/` (1 día) y `/estadisticas/` (1 hora)
- Parámetros de búsqueda validados (`buscar` máx. 200 caracteres, `limite` entre 1 y 500); exportación CSV limitada a 5.000 registros
- Honeypot en el registro: campo `sitio_web` oculto — si llega relleno (bot), se devuelve éxito falso sin crear cuenta
- Anti-enumeración en registro: intentar crear una cuenta con un email ya existente devuelve `201` sin crear duplicado — igual que `/auth/recuperar`, la respuesta no revela si el email estaba registrado
- Verificación de email obligatoria: cuentas nuevas con `email_verificado=0`; el login bloquea con 403 hasta confirmar

**Estructura:**

| Archivo | Función |
|---------|---------|
| `models.py` | Tablas de la BD como clases Python (ORM SQLAlchemy) |
| `schemas.py` | Forma de los datos devueltos (Pydantic v2) |
| `auth.py` | Hashing bcrypt y generación/validación JWT |
| `dependencies.py` | `get_current_user` y `require_rol` |
| `routers/` | Un router por dominio: convocatorias, solicitudes, estadísticas, agrupaciones, avisos, auth, privado, admin |

**Roles y acceso:**

| Rol | Quién es | Páginas y rutas accesibles |
|-----|----------|---------------------------|
| Sin token | Usuario no registrado | Home, buscador, estadísticas, recursos · API: `/convocatorias/`, `/solicitudes/`, `/estadisticas/*`, `/avisos/` |
| `registrado` | Cuenta verificada | Todo lo anterior + `privado.html`, `exclusivo.html` · API: `/privado/*` |
| `admin` | Administrador | Todo lo anterior + `admin.html` · API: `/admin/*` |

**Errores personalizados:** los errores HTTP devuelven siempre JSON estructurado con tres campos:

```json
{ "error": 404, "mensaje": "Recurso no encontrado", "sugerencia": "Comprueba la URL o los parámetros de la petición" }
```

| Código | Cuándo |
|--------|--------|
| 401 | Sin token o token inválido |
| 403 | Token válido pero sin permisos suficientes |
| 404 | Ruta o recurso inexistente |
| 422 | Datos de entrada que no superan la validación Pydantic |
| 500 | Error interno no controlado |

**Páginas de error HTML (Nginx):** `404.html` y `50x.html` se sirven directamente desde Nginx con `error_page` — funcionan aunque el backend esté caído. El middleware registra cada petición en `logs/`.

Ver listado completo de endpoints en [docs/referencia-tecnica.md](docs/referencia-tecnica.md) · Flujo JWT y tokens en [docs/autenticacion.md](docs/autenticacion.md).

### Frontend

Interfaz web construida con **HTML5 + CSS3 + JavaScript vanilla** (sin frameworks). Se sirve directamente desde Nginx como archivos estáticos; toda la lógica de datos viene de la API.

**Páginas principales:**

| Página | Descripción |
|--------|-------------|
| `index.html` | Home con métricas, gráficas de evolución e información de convocatorias activas |
| `buscador.html` | Buscador de solicitudes con filtros, paginación, ordenación server-side y exportación CSV con nombre de archivo dinámico según filtros activos |
| `estadisticas-epas.html` | Análisis de protectoras: importes, media/mediana, nuevas vs recurrentes, top beneficiarios |
| `estadisticas-eell.html` | Análisis de ayuntamientos: ranking CCAA/provincias, concentración del importe |
| `exclusivo.html` | Resumen por convocatoria y mapa de calor CCAA (solo usuarios registrados) |
| `privado.html` | Perfil del usuario: cambiar nombre, contraseña y acceso al contenido exclusivo |
| `admin.html` | Panel de administración: gestión de usuarios, avisos y logs (solo rol `admin`) |
| `entidad.html` | Ficha de entidad con historial completo de solicitudes por CIF — accesible desde el enlace "Ver página completa →" del modal del buscador o por URL directa (`entidad.html?cif=...`) |
| `recursos.html` | Directorio de organizaciones de protección animal y campañas |
| `login.html` · `registro.html` | Acceso y creación de cuenta con verificación de email |
| `recuperar-password.html` · `reset-password.html` | Flujo de recuperación de contraseña por email |
| `aviso-legal.html` · `privacidad.html` | Páginas legales: aviso legal y política de privacidad |
| `404.html` · `50x.html` | Páginas de error personalizadas servidas por Nginx |

**Estados de carga:**
Las páginas con peticiones asíncronas muestran feedback visual mientras esperan la respuesta: spinner giratorio (home, estadísticas, buscador, ficha de entidad) y skeleton loader animado en verde para la tabla de `exclusivo.html` — barras con shimmer que simulan la forma de la tabla antes de que lleguen los datos.

**Optimización de carga:**

- `defer` en todos los `<script>` — los scripts se descargan en paralelo con el HTML y ejecutan en orden después del parsing, sin bloquear el renderizado. Compatible con `DOMContentLoaded`.
- `fetchpriority="high"` en la imagen hero de `index.html` — prioriza la descarga de la imagen más visible (LCP) frente al resto de recursos.
- Caché de assets en Nginx: imágenes y fuentes (`expires 1y`), CSS y JS (`expires 1h`) — el navegador reutiliza los archivos estáticos entre páginas sin consultar al servidor.

**Arquitectura JS:**
Un archivo JS por página, sin bundler ni framework. La comunicación con la API usa `fetch` con `async/await`. En las páginas protegidas se verifica el `access_token` al cargar; si ha caducado se renueva con `/auth/refresh` antes de redirigir al login. La navegación usa `history.replaceState` (no `pushState`) para evitar entradas duplicadas al pulsar "atrás" desde páginas con filtros en la URL.

**Responsive:**
Una sola hoja de estilos compartida (`styles.css`) con variables CSS para colores, espaciado y tipografía. Breakpoints en 600px (grid 2→1 columna), 768px (modales y tablas) y 900px (menú hamburguesa). El navbar tiene z-index 1200 para quedar por encima de los controles de Leaflet (z-index 1000 por defecto).

**Visualizaciones:**

- **Chart.js** — gráficas de barras, líneas, donut y distribución en las páginas de estadísticas. Cada gráfica abre un modal con conclusiones en HTML (`<p>`, `<ul>`, `<a>`).
- **Leaflet + GeoJSON** — mapa choropleth por CCAA en `exclusivo.html`. En táctil (`pointer: coarse`): un toque muestra tooltip central, doble toque abre el modal de detalle.

Ver componentes y decisiones de diseño en [frontend/docs/especificaciones-frontend.md](frontend/docs/especificaciones-frontend.md) · Paleta, tipografía y guía visual en [frontend/docs/diseño.md](frontend/docs/diseño.md).

#### Capturas

![Página de inicio](docs/img/screenshots/home-intro.webp)
*Página de inicio: banners de convocatorias activas, descripción del proyecto y métricas principales*

![Gráficas de análisis](docs/img/screenshots/home-graficas.webp)
*Evolución del importe por año, comparativa EPA vs EELL, distribución por estado y tasa de éxito*

![Buscador de solicitudes](docs/img/screenshots/buscador.webp)
*Buscador con filtros, badges de estado, tramos EELL, ordenación y exportación CSV*

![Mapa de calor por CCAA](docs/img/screenshots/exclusivo-mapa.webp)
*Contenido exclusivo: mapa choropleth interactivo por comunidad autónoma (solo usuarios registrados)*

#### Compatibilidad de navegadores

La aplicación usa APIs modernas (ES2017+, `fetch`, CSS custom properties, `URLSearchParams`, `URL.createObjectURL`). No es compatible con Internet Explorer.

| Navegador | Compatibilidad | Notas |
|-----------|---------------|-------|
| **Chrome 80+** | ✅ Completa | Recomendado. Probado en desarrollo |
| **Edge 80+** | ✅ Completa | Mismo motor que Chrome (Chromium) |
| **Firefox 75+** | ✅ Completa | |
| **Safari 14+** | ✅ Con matiz | El certificado autofirmado puede requerir añadirlo manualmente al llavero del sistema (Acceso a Llaveros) antes de que Safari lo acepte |
| **Navegadores móviles** | ✅ Completa | Diseño responsive verificado. El mapa choropleth de CCAA tiene soporte táctil (un toque = info, doble toque = detalle) |
| **Internet Explorer** | ❌ No soportado | Sin soporte de `fetch`, `async/await` ni CSS variables |

**Nota sobre el certificado autofirmado:** todos los navegadores mostrarán un aviso de "conexión no segura" la primera vez. En Chrome y Firefox basta con hacer clic en "Avanzado" → "Continuar". Safari en macOS puede requerir aceptar el certificado en Preferencias del Sistema → Llaveros.

La carpeta `frontend/` contiene:

- `docs/diseño.md` — guía visual completa: paleta de colores, tipografía, espaciado y componentes base
- `docs/especificaciones-frontend.md` — especificaciones técnicas de implementación: componentes, páginas, integración con la API y decisiones de diseño justificadas
- `css/styles.css` — hoja de estilos compartida por todas las páginas (variables CSS, componentes, layout)
- `js/` — un archivo JS por página (`home.js`, `solicitudes.js`, `estadisticas-epas.js`, `estadisticas-eell.js`, `auth.js`, `privado.js`, `exclusivo.js`, `admin.js`, `entidad.js`, `recuperar-password.js`, `reset-password.js`, `modal-grafica.js`, `utils.js`)
- `assets/` — recursos estáticos organizados en subcarpetas: `img/` (logo, error404), `img/home/` (imágenes de portada), `img/logos/` (logos de entidades), `wireframes/` (capturas de diseño por pantalla), `guia-estilo/` (paleta, tipografía y PDF de wireframes)
- `scripts/` — utilidades de desarrollo (ver abajo)
- `index.html`, `estadisticas-epas.html`, `estadisticas-eell.html`, `recursos.html`, `buscador.html`, `entidad.html`, `login.html`, `registro.html`, `privado.html`, `exclusivo.html`, `admin.html`, `recuperar-password.html`, `reset-password.html`, `verificar-email.html` — páginas de contenido (`solicitudes.html` se conserva como alias legacy de `buscador.html` para compatibilidad con enlaces externos)
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

---

## Desarrollo

### Requisitos del sistema

| Requisito | Valor | Notas |
|-----------|-------|-------|
| **Sistema operativo** | Linux · macOS · Windows con WSL2 | En Windows se requiere WSL2 + Docker Desktop con integración WSL2 activa |
| **Docker** | 24+ con `docker compose` v2 | Imprescindible. Incluye todos los servicios (BD, backend, Nginx, cron) |
| **Python** | 3.10+ | Solo necesario para ejecutar tests y scripts de parseo. La app web funciona sin él |
| **openssl** | Cualquier versión reciente | Para generar el certificado SSL autofirmado en la instalación |
| **Espacio en disco** | ~1,5 GB | ~1 GB imágenes Docker (primera descarga) + ~10 MB dataset + ~50 MB venv opcional |
| **RAM** | 4 GB mínimo recomendado | MariaDB + FastAPI + Nginx corren en paralelo dentro de Docker |
| **Editor** | VS Code recomendado | El proyecto incluye `.vscode/extensions.json` con extensiones preconfiguradas. Cualquier editor funciona |
| **Conexión a internet** | Solo en la primera instalación | Para descargar las imágenes Docker (~300–400 MB). Después la app funciona completamente offline: Chart.js y Leaflet tienen fallback local en `frontend/assets/vendor/` que se carga automáticamente vía `onerror` si los CDN no responden. Google Fonts es el único recurso CDN sin fallback local — sin conexión y sin caché, la tipografía cae al `font-family` de sistema por defecto, sin romper la app |

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
3. El script crea dos cuentas de demo (ver tabla de credenciales más abajo). Para el panel de administración usa `admin@demo.com` / `Admin1234!`.

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

El script crea dos usuarios de demo si no existen:

| Rol | Email | Contraseña | Acceso |
|-----|-------|------------|--------|
| `admin` | `admin@demo.com` | `Admin1234!` | Panel de administración + zona privada + contenido exclusivo |
| `registrado` | `usuario@demo.com` | `User1234!` | Zona privada + contenido exclusivo |

Si ya existen (instalaciones previas), `INSERT IGNORE` los omite sin error.

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
> **Instalación en una segunda máquina:** `bash install.sh` funciona igual en cualquier equipo con Docker. Genera un `.env` nuevo con su propia `SECRET_KEY` y `CORS_ORIGINS=*`. Los datos de subvenciones se cargan desde el dataset del repositorio, así que la BD queda idéntica. Las cuentas de usuario (registro, admin) **no** se transfieren entre máquinas — existen los dos usuarios demo que crea el script (`admin@demo.com` y `usuario@demo.com`). Si necesitas las mismas cuentas en el portátil, créalas manualmente desde el panel de administración.
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

`venv/` es un **entorno virtual Python** aislado que se crea en la máquina de desarrollo. Permite instalar las librerías de los scripts (parsers, carga de datos) sin mezclarlas con el Python del sistema ni con el de otros proyectos.

**Solo es necesario para:**

- Ejecutar los scripts de parseo de datos (`scripts/data_processing/`)
- Ejecutar los tests con `pytest` (`make test`)

**No es necesario para usar la aplicación web** — el backend corre dentro de Docker con su propio entorno aislado (`backend/requirements.txt` se instala en el contenedor). Un usuario que solo quiera arrancar y usar la app puede saltarse este paso.

`venv/` no se versiona (está en `.gitignore`) porque es específico de cada máquina y pesa ~50 MB. `install.sh` lo crea automáticamente si se necesita.

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

| Servicio  | Contenedor       | Imagen                   | Función                                                   | Puerto externo         |
|-----------|------------------|--------------------------|-----------------------------------------------------------|------------------------|
| `db`      | `bdns_dgda_db`   | mariadb:11               | Base de datos MariaDB con el dataset cargado              | 3307 (interno: 3306)   |
| `backend` | `bdns_api`       | python:3.11-slim (build) | API FastAPI                                               | ninguno (interno 8000) |
| `nginx`   | `bdns_nginx`     | nginx:alpine             | Proxy inverso, HTTPS, archivos estáticos                  | 80 (HTTP), 443 (HTTPS) |
| `cron`    | `bdns_cron`      | python:3.12-slim (build) | Scheduler: comprobación BDNS y health check               | ninguno                |
| `mailpit` | `bdns_mailpit`   | axllent/mailpit          | SMTP de desarrollo — atrapa emails sin enviarlos          | 1025 (SMTP), 8025 (UI) |
| `adminer` | `bdns_adminer`   | adminer                  | Interfaz web para explorar la BD                          | 8080                   |

El backend no expone su puerto al exterior — solo Nginx y el cron pueden acceder a él dentro de la red Docker interna.

**Acceso en desarrollo** (con Docker levantado):

| Qué | URL |
|-----|-----|
| Aplicación web | `https://subvencionesDGDA.local` o `http://localhost` |
| API — Swagger UI | `https://subvencionesDGDA.local/docs` (Docker) · `http://localhost:8000/docs` (dev) |
| Adminer — explorador de BD | `http://localhost:8080` · Sistema: MySQL · Servidor: `db` |
| Mailpit — bandeja de emails | `http://localhost:8025` |

Mailpit intercepta todos los emails que el backend intenta enviar (recuperación de contraseña, verificación) sin que lleguen a ningún destinatario real.

El servicio `cron` usa un scheduler Python propio (`docker/cron/scheduler.py`) — sin supercronic ni binarios del sistema — que ejecuta dos tareas:

- **`health_check.py`** — cada 6 horas, verifica que el backend responde correctamente.
- **`check_bdns.py`** — detecta nuevas convocatorias o resoluciones en la API BDNS. Frecuencia variable según temporada: cada 2 días en abril–mayo (pico de publicación de convocatorias DGDA) y en noviembre–diciembre (pico de publicación de resoluciones); cada 4 días en marzo, junio y enero. No se ejecuta entre febrero y octubre porque la DGDA no publica en esos meses. Opera en dos fases: primero actualiza `fecha_resolucion` en convocatorias pendientes del año en curso (el banner de aviso de la home desaparece automáticamente); después busca si ha aparecido alguna convocatoria nueva.

Registra todo en stdout (`docker logs bdns_cron`) y en `logs/cron/`. El cron puede lanzarse manualmente con `docker exec bdns_cron python3 /app/scripts/check_bdns.py`.

### Nginx — qué hace exactamente

Nginx gestiona todo el tráfico de entrada y cumple cinco funciones en un solo proceso:

- **Terminador SSL** — recibe HTTPS del navegador, descifra el tráfico TLS (1.2/1.3) y lo reenvía al backend por HTTP interno. El backend no necesita saber nada de certificados.
- **Servidor de archivos estáticos** — sirve directamente `frontend/*.html`, `css/`, `js/` y `assets/` sin pasar por Python. Las páginas de error `404.html` y `50x.html` se sirven incluso si el backend está caído.
- **Proxy inverso** — las rutas `/auth`, `/solicitudes`, `/estadisticas`, `/privado`, `/admin`, etc. se redirigen al contenedor `bdns_api` (puerto 8000, no expuesto al exterior).
- **Rate limiting** — tres zonas definidas con `limit_req_zone` al inicio de `default.conf`. Al superarse el límite, Nginx devuelve HTTP 429 directamente sin consumir recursos del backend.
- **Healthcheck propio** — sirve `GET /healthz` con un 200 "ok" fijo (sin pasar por el backend y sin redirigir a HTTPS). Lo consume el healthcheck de Docker para saber si Nginx está vivo independientemente de que el backend lo esté.

Editar `default.conf` no recarga la config automáticamente: hay que ejecutar `docker exec bdns_nginx nginx -s reload` (o `make reload-nginx`). Antes de recargar conviene verificar la sintaxis con `docker exec bdns_nginx nginx -t`.

### Tamaño de las imágenes Docker

Las imágenes están optimizadas para reducir el peso del entorno (~700 MB menos respecto a imágenes base completas):

| Imagen base | Tamaño | En lugar de | Ahorro |
|-------------|--------|-------------|--------|
| `python:3.11-slim` (backend) | ~75 MB | `python:3.11` (~900 MB) | ~825 MB |
| `python:3.12-slim` (cron) | ~75 MB | `python:3.12` (~900 MB) | ~825 MB |
| `nginx:alpine` | ~11 MB | `nginx` (~190 MB) | ~180 MB |

Además, ambos Dockerfiles usan `pip install --no-cache-dir` para no almacenar la caché de pip dentro de la imagen, y copian `requirements.txt` antes que el código de la aplicación — así Docker solo repite el `pip install` cuando cambian las dependencias, no en cada cambio de código.

El backend instala además `curl` (~6 MB) sobre la imagen slim: lo usa el healthcheck de Docker para verificar `/health` y queda disponible para depurar la conectividad desde dentro del contenedor (`docker exec bdns_api curl http://db:3306`). El resto de la optimización slim se mantiene; tras la instalación se borra la caché de apt (`rm -rf /var/lib/apt/lists/*`) para no dejar ~30 MB residuales dentro de la imagen.

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

El proyecto tiene **275 pruebas en total**: 223 funciones de test automáticas con pytest (321 ejecuciones por uso de `@pytest.mark.parametrize`) y 52 manuales verificadas en el navegador con Docker levantado.

| Nivel | Cantidad | Herramienta |
|-------|----------|-------------|
| Automáticos | 223 funciones / 321 ejecuciones | pytest (sin Docker) |
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
305 passed   # excluyendo test_https_config.py y test_rate_limiting.py (requieren Docker+Nginx)
321 passed   # suite completa con Docker levantado
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

### Infraestructura y despliegue

- HTTPS activo (TLS 1.2/1.3, certificado autofirmado, redirección HTTP→HTTPS)
- Docker: Nginx + FastAPI + MariaDB + cron + Mailpit en contenedores
- Instalación y desinstalación automatizadas (`install.sh` + `uninstall.sh` + Makefile)

### API y autenticación

- Autenticación completa: JWT · refresh token · verificación email · recuperación contraseña
- Caché y rate limiting activos (Nginx); medidas anti-bots
- Cron con auto-detección de resoluciones BDNS
- Auditoría de seguridad completada (parámetros, SRI, SMTP, logs de acceso)

### Interfaz web

- Buscador con ordenación server-side; exportación CSV
- Panel de administración completo con visor de logs
- Zona privada con nombre/alias editable; contenido exclusivo con mapa CCAA táctil
- Modal de conclusiones con textos reales en las 9 gráficas
- Navbar responsive (hamburguesa ≤900px) · sistema de color coherente · imagen hero
- Auditoría responsive móvil completada

### Calidad del código

- CSS limpio y consolidado en `styles.css`; accesibilidad WCAG 2.2 revisada
- 223 funciones de test automáticas / 321 ejecuciones (pytest)

→ Ver [historial completo de implementación](docs/historial-implementacion.md)

---

## Buenas prácticas aplicadas

Criterios de calidad tenidos en cuenta a lo largo del desarrollo, más allá de la funcionalidad básica.

### Seguridad

- **Contraseñas** — hash bcrypt con `rounds=12`; validación de fortaleza en registro y cambio (mínimo 8 caracteres, mayúscula, minúscula, número)
- **Sesión** — doble token JWT: access token de 15 min + refresh token de 30 días con rotación en cada uso; revocación en cascada al cambiar contraseña
- **Rate limiting** — Nginx bloquea con HTTP 429 antes de llegar al backend: login (10 req/min), registro (5 req/min), recuperar contraseña (3 req/min)
- **Cabeceras de seguridad** — `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Strict-Transport-Security` (HSTS 1 año)
- **SRI** — atributo `integrity` en los 5 recursos CDN externos (Chart.js ×3, Leaflet JS y CSS); el navegador verifica el hash antes de ejecutarlos
- **Honeypot** — campo oculto `sitio_web` en el registro; si llega relleno (bot), se devuelve éxito falso sin crear cuenta
- **Anti-enumeración** — registro y recuperación de contraseña devuelven siempre la misma respuesta, exista o no el email
- **Validación de parámetros** — `buscar` máx. 200 caracteres, `limite` entre 1 y 500, exportación CSV limitada a 5.000 filas
- **Verificación de email** — cuentas nuevas con `email_verificado=0`; login bloqueado hasta verificar
- **HTTPS** — TLS 1.2/1.3 únicamente; certificado autofirmado con `subjectAltName` (requisito Chrome/Firefox)

### Accesibilidad (WCAG 2.1 AA)

- **Skip navigation** — enlace "Saltar al contenido" en las 19 páginas; foco visible con contraste 12:1
- **Roles ARIA** — `role="navigation"`, `aria-label` en todos los `<nav>`, `role="img"` en todos los `<canvas>`, `aria-live` en mensajes de error y éxito
- **Formularios** — todos los campos con `<label>` explícito (`for` + `id`); errores con `role="alert"`, confirmaciones con `role="status"`
- **Foco de teclado** — trampa de foco en modales (Tab/Shift+Tab ciclan dentro); cierre con Esc; foco devuelto al elemento que abrió el modal al cerrar
- **Responsive y táctil** — diseño verificado en Chrome DevTools; mapa choropleth con interacción táctil específica (un toque = info, doble toque = detalle)

### Rendimiento

- **`defer`** en todos los `<script>` — descarga en paralelo, ejecución ordenada tras el parsing; sin bloqueo del renderizado
- **`fetchpriority="high"`** en la imagen hero — mejora el LCP (Largest Contentful Paint)
- **`loading="lazy"`** en todas las imágenes fuera del viewport inicial
- **Caché Nginx** — imágenes y fuentes: `expires 1y`; CSS y JS: `expires 1h`
- **Cache-Control en la API** — `/convocatorias/` 1 día, `/estadisticas/` 1 hora
- **Imágenes Docker slim** — `python:3.11-slim` (~75 MB vs ~900 MB de la imagen completa); `--no-cache-dir` en pip

### Calidad y mantenibilidad

- **223 funciones de test automáticas** (321 ejecuciones con `@pytest.mark.parametrize`) — pipeline de datos, endpoints públicos, autenticación completa, zona privada, panel admin, infraestructura (HTTPS, rate limiting, caché, logs), scheduler del cron, retry con backoff de la API BDNS
- **Healthchecks Docker** en `db`, `backend` y `nginx` — detectan cuelgues que no matarían el proceso (deadlocks, bucles infinitos), donde `restart: unless-stopped` no actuaría. `docker compose ps` muestra `(healthy)` o `(unhealthy)` por servicio. El cron no tiene healthcheck Docker porque no expone HTTP; su monitorización es interna vía `restart: unless-stopped` y los logs de `bdns_check.log` / `health_check.log`.
- **Manejo de errores** — todos los `fetch` tienen bloque `catch` con mensaje visible al usuario; errores HTTP distinguen 401/403/422/500
- **Sin código muerto** — sin `console.log` en producción, sin funciones definidas y nunca llamadas
- **Cabeceras JSDoc** — los 16 archivos JS documentan propósito, endpoints que usan y página asociada
- **CSS consolidado** — una sola hoja de estilos con índice de 28 secciones. Los `style=` inline que quedan son principalmente `display:none` para toggle por JavaScript (~60 ocurrencias); las ~30 restantes (tipografía y márgenes puntuales) están identificadas como mejora pendiente

### Contingencia ante fallos externos

Mecanismos que mantienen el sistema operativo (o degradado de forma controlada) ante caídas de servicios externos o internos.

**Resumen rápido:**

| Qué puede fallar | Mecanismo | Resultado para el usuario |
|---|---|---|
| API BDNS no responde | Retry con backoff (2s → 4s → 8s) en el cron | La web sigue intacta (los datos están en MariaDB local); el cron reintenta en su próximo ciclo |
| Backend FastAPI se cuelga sin morir | Healthcheck Docker cada 30s | `docker compose ps` muestra `(unhealthy)`; visibilidad inmediata del problema |
| Backend FastAPI cae | `restart: unless-stopped` + `error_page` Nginx | El contenedor se reinicia automáticamente; mientras tanto el usuario ve `50x.html` amable, no pantalla en blanco |
| MariaDB cae | `restart: unless-stopped` + `depends_on: service_healthy` | El contenedor se reinicia y el backend espera a que la BD esté lista antes de aceptar peticiones |
| Nginx cae | `restart: unless-stopped` | Docker reinicia el contenedor automáticamente |
| CDN externo (`jsdelivr`, `unpkg`) caído o lento | Fallback local en `assets/vendor/` vía `onerror` | Las gráficas y el mapa siguen renderizando con los archivos locales |
| CDN sirve archivo manipulado | SRI (`integrity`) en los 5 recursos CDN | El navegador rechaza el archivo y dispara el fallback local |
| Mailpit/SMTP caído | `try/except` no bloqueante en envío de emails | El registro y la recuperación funcionan igual; solo no llega el email (el usuario puede pedir reenvío) |
| Sesión del usuario caduca | Refresh token automático | El usuario sigue navegando sin volver a hacer login |
| Datos perdidos por error | `make backup` + volúmenes Docker persistentes | La BD se restaura desde un `.sql` fechado |

A continuación, el detalle por dominio.

#### Datos

- **Dataset versionado en el repositorio** (`data/final/dataset_unificado.json`, 6.398 registros): la web funciona sin necesidad de la API BDNS ni del BOE en runtime. Las consultas del usuario van a MariaDB local, no a servicios externos.
- **`make backup` + volúmenes Docker persistentes**: la BD sobrevive a `docker compose down` y se puede restaurar desde un `.sql` fechado.

#### API BDNS (servicio externo)

- **Calendario del cron extendido a noviembre–enero**: las resoluciones DGDA se publican en esa ventana y antes el cron estaba dormido. Ahora se detectan automáticamente y el banner de aviso de la home desaparece sin intervención manual.
- **Reintentos con backoff exponencial (2s → 4s → 8s)**: el helper `_get_bdns_con_retry` absorbe blips puntuales de BDNS de hasta ~15s. Sin retry, una sola incidencia hacía perder hasta 4 días hasta el siguiente ciclo del cron.
- **Timeout de 30s por petición** y captura explícita de `requests.RequestException`: el cron nunca queda colgado en una llamada ni se rompe por errores de red.

#### Servicios Docker

- **`restart: unless-stopped`** en los 6 contenedores: auto-recuperación tras crash o reinicio del sistema. No revive contenedores parados a mano con `docker compose down`.
- **Healthchecks** en `db`, `backend` y `nginx`: detectan cuelgues que no matarían el proceso (deadlocks, conexiones agotadas), donde el restart no actúa. `docker compose ps` muestra `(healthy)` o `(unhealthy)` por servicio. El cron no tiene healthcheck Docker porque no expone HTTP; su monitorización es interna vía logs.
- **`depends_on: service_healthy`**: el backend espera a que MariaDB esté lista antes de arrancar; el cron espera al backend. Evita errores de conexión en el arranque ordenado.

#### Nginx y backend

- **Páginas `404.html` y `50x.html`** servidas por Nginx con `error_page`: se siguen viendo aunque el backend esté caído. Sin JavaScript, sin llamadas a la API.
- **Endpoint `/healthz` propio de Nginx** (fuera de la redirección HTTPS): permite verificar que Nginx vive independientemente de que el backend esté disponible.

#### Frontend (peticiones, errores y CDN)

- **Todos los `fetch` con `try/catch`**: si la API devuelve 4xx/5xx o no responde, se muestra `error-box` con mensaje y sugerencia en lugar del spinner colgado indefinidamente.
- **Mapa CCAA degrada a "Mapa no disponible"** si la inicialización de Leaflet falla.
- **Recursos CDN con SRI (`integrity`)**: el navegador rechaza ficheros modificados o corruptos, evitando ataques de cadena de suministro.
- **Fallback local de CDN** (`frontend/assets/vendor/chart.umd.min.js`, `leaflet.js`, `leaflet.css`): si `cdn.jsdelivr.net` o `unpkg.com` están caídos, el atributo `onerror` del `<script>` o `<link>` carga el archivo desde el propio dominio. Las versiones locales se descargaron con los mismos hashes SHA-384 que los SRI declarados, verificación criptográfica de integridad. Coste: ~370 KB añadidos al repositorio.

#### Autenticación

- **SMTP envuelto en `try/except` no bloqueante**: si Mailpit/SMTP cae, el registro y la recuperación de contraseña funcionan igual; solo no llega el email. La cuenta queda creada con `email_verificado=0`, y se puede desbloquear desde el panel de administración o reenviando el email.
- **Refresh token automático**: si el access token de 15 min caduca, el JS lo renueva en background con el refresh token (30 días) sin pedir al usuario que vuelva a hacer login.

#### Tests de contingencia

- **SQLite en memoria** como sustituto de MariaDB en los tests originales (mock de BD).
- **`unittest.mock.patch`** para mockear envíos de email (mock de SMTP).
- **Tests parametrizados del scheduler** del cron (21 funciones / 119 ejecuciones) verifican el calendario completo sin esperar a noviembre.
- **Tests del retry de BDNS con backoff** (5 funciones) mockean `requests.get` y `time.sleep` para reproducir los 4 escenarios de fallo sin tocar la API real.

### UX y experiencia de uso

- **Estados de carga** — spinner en peticiones de datos; skeleton loader animado en tabla de contenido exclusivo
- **Feedback de errores** — mensajes de error visibles en tabla/formulario cuando la API falla o el servidor no responde
- **Persistencia de filtros** — los filtros del buscador se guardan en la URL; compartible, marcable y restaurado al pulsar "Atrás"
- **Deep link post-login** — si el usuario accede a una página protegida sin sesión, se redirige al login y vuelve automáticamente a la página original tras autenticarse
- **Exportación CSV con nombre dinámico** — el nombre del archivo refleja los filtros activos (ej: `solicitudes_epa_2024_concedida.csv`)
- **Renovación automática de sesión** — el access token se renueva silenciosamente con el refresh token sin que el usuario tenga que volver a hacer login

---

## Notas técnicas

- `solicitudes.html` se conserva intencionalmente aunque la URL pública es ahora `buscador.html`. Actúa como redirección de compatibilidad para cualquier enlace externo o marcador guardado antes del renombrado. No es un archivo huérfano: es legacy deliberado.
- `data/raw/` no se versiona completo; se mantienen ejemplos representativos. Los scripts sobrescriben resultados al volver a ejecutarse — el sistema es reproducible desde cero.
- El campo `email_verificado` en `usuarios` tiene `DEFAULT 1` en la migración (para no bloquear cuentas existentes), pero `POST /auth/registro` siempre lo establece a `0` explícitamente.
- El campo `nombre` en `usuarios` es nullable — los usuarios existentes quedan intactos. Migración para instalaciones ya existentes: `ALTER TABLE usuarios ADD COLUMN nombre VARCHAR(100) NULL AFTER email;`
- Chart.js: `formatearEjeY` usa `.toFixed(0)` que redondea 7,5 → 8, generando ticks duplicados si el rango del eje es pequeño y `stepSize` no es múltiplo entero de 1000. Solución: callback personalizado `(k % 1 === 0 ? k : k.toFixed(1)) + ' K'`.
- `history.replaceState` vs `pushState` en el buscador: al usar `pushState` cada cambio de filtro añadía una entrada al historial. Al hacer clic en una convocatoria y pulsar "Atrás", el navegador volvía al estado anterior del filtro en lugar de salir del buscador, obligando a pulsar "Atrás" varias veces. Cambiado a `replaceState` — actualiza la URL sin añadir entradas al historial.
- Mapa choropleth (`exclusivo.html`) parpadeaba al cargar: Leaflet inicializaba el mapa antes de que llegaran los datos de la tabla, que al inyectarse empujaban el mapa hacia abajo causando un salto visual. Corregido con `await cargarResumenTabla(token)` antes de `cargarMapaCCAA()` — el mapa solo se inicializa cuando el DOM ya tiene su posición definitiva.
- GeoJSON de CCAA: el archivo original era una versión muy simplificada (~5 KB) en la que los bordes de las comunidades quedaban irregulares y poco precisos. Se sustituyó por un GeoJSON de mayor resolución (~618 KB), lo que mejoró visiblemente la forma de los polígonos en el mapa choropleth.
- `activo` y `email_verificado` en `models.py` están definidos como `Column(SmallInteger)` en lugar de `Column(Boolean)`. Funcionan igual porque MariaDB almacena `BOOLEAN` como `TINYINT(1)` internamente, pero el tipo semántico es incorrecto: el ORM no valida que solo entren `True`/`False`. Cambiarlo requeriría un `ALTER TABLE` en la BD existente — no justificado en este entorno.
- La función `cerrarSesion` está definida en `navbar.js`, `privado.js`, `exclusivo.js` y `admin.js`. La duplicación es conocida: `navbar.js` la necesita para páginas donde el botón se inyecta dinámicamente, mientras los otros tres tenían su propia implementación antes de que se añadiera `navbar.js` a esas páginas. La solución limpia sería un `utils-auth.js` compartido, pero introducirlo al final del proyecto supone un riesgo innecesario.

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

#### Sesión expirada no renovaba automáticamente — el refresh token se ignoraba

Las páginas protegidas (`privado.html`, `exclusivo.html`, `admin.html`) verificaban el access token al cargar. Si el token existía en `localStorage` pero había caducado (15 min), el código lo usaba directamente, recibía 401 y redirigía al login **sin intentar el refresh token** — este solo se usaba cuando el `localStorage` estaba completamente vacío.

Síntoma: el usuario se autenticaba, cambiaba de página después de 15 minutos y era expulsado aunque su refresh token (30 días) siguiera siendo válido.

Solución: el manejador de 401 en `fetchAutenticado` y `verificarAcceso` ahora llama a `intentarRenovarToken()` antes de redirigir. Si la renovación tiene éxito, reintenta la petición con el token nuevo. Solo redirige al login si el refresh token también ha caducado o fue revocado. Ver [docs/autenticacion.md](docs/autenticacion.md) para el flujo completo.

#### Respuesta idéntica en `/auth/recuperar` independientemente de si el email existe

El endpoint devuelve exactamente el mismo mensaje tanto si el email está registrado como si no: `"Si ese email está registrado, recibirás un enlace en breve"`. Esto es una decisión de seguridad deliberada para evitar la enumeración de usuarios: si la respuesta fuera diferente según si el email existe, un atacante podría automatizar peticiones con listas de emails y descubrir qué cuentas están registradas en el sistema. La misma respuesta en ambos casos no filtra ninguna información.

---

## Limitaciones conocidas del dato de origen

- **Punto final en nombres de entidades**: la BDNS registra los nombres tal cual los declararon las entidades en su momento. Algunas incluyen punto final ("ASOCIACIÓN GATO AYUD.") y otras no. Es una inconsistencia de la fuente, no un bug. No se normaliza en el frontend para no crear divergencias con el CSV exportado y la API.

- **Expedientes con resolución tardía — aparecen en dos convocatorias**: algunas entidades presentaron solicitud en un año pero la resolución se publicó en el BOE del año siguiente. El pipeline las registra en ambas convocatorias porque cada dataset se procesa de forma independiente. Casos identificados:
  - **EPA** — *La Sexta Huella* (`SUBV2022659`): excluida en 2022, concedida en 2023; aparece dos veces en EPA 2023, lo que infla ligeramente su importe acumulado en estadísticas (~9.130 € en vez de ~4.446 €).
  - **EPA** — *Amibichos* (`2023B628`): excluida en 2023, concedida en 2024; aparece dos veces en EPA 2024.
  - **EELL** — *Casavieja* (`EXP2023/008788`, `EXP2025/011681`) y *Castilforte* (`EXP2023/008510`, `EXP2024/007382`): `no_beneficiaria` en todos sus años, sin impacto económico. Castilforte aparece en 2023 y 2024; Casavieja en 2023 y 2025.
  - El número de expediente puede variar en formato entre años (`SUBV…`, `2023B…`, sin prefijo), lo que dificulta la deduplicación automática cross-year.
  - Causa raíz: `cargar_dataset.py` asigna cada solicitud a la convocatoria de su dataset sin comprobar si el expediente ya existe en otra convocatoria. La corrección requeriría lógica adicional en el pipeline de carga.

- **Formatos de expediente heterogéneos en EELL 2025**: el BOE XML de 2025 usa el formato `EXP/NNNNN` (sin año) para 23 entidades, mientras que el Excel principal usa `EXP2025/NNNNN`. No se trata de duplicados de las mismas entidades — son registros distintos que el BOE referencia con diferente esquema de numeración. Todas son `excluida` o `no_beneficiaria`, sin impacto económico. La deduplicación no puede unirlas automáticamente porque los números no coinciden entre fuentes.

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

- **Entidades favoritas** — permitir a usuarios registrados marcar hasta un máximo razonable de entidades (p.ej. 20) como favoritas para hacerles seguimiento. Las entidades marcadas se mostrarían en `exclusivo.html` con su último estado y el importe acumulado, sin necesidad de buscarlas cada vez. Requiere: tabla `usuario_favoritos` (`id_usuario` FK + `cif` + `fecha`), dos endpoints (`POST /privado/favoritos`, `DELETE /privado/favoritos/{cif}`, `GET /privado/favoritos`), botón de marcado en el modal del buscador y en `entidad.html`, y sección dedicada en la zona exclusiva.
- **Paginación en `/admin/usuarios`** — la tabla de usuarios no pagina; con pocos usuarios actuales no es problema pero escalaría mal.
- **Retry en cron si BDNS API no responde** — el cron falla silenciosamente si BDNS devuelve error; añadir reintentos con backoff exponencial.
- **Logs de cron en panel admin** — mostrar `bdns_check.log` y `health_check.log` en el panel. Requiere: montar `../logs/cron` en el contenedor backend, dos endpoints nuevos en `admin.py` y dos secciones en `admin.html` / `admin.js`.
- **Trampa de foco en menú hamburguesa** — el menú cierra con Esc y click fuera, pero Tab no cicla dentro del menú abierto. Mejora de accesibilidad WCAG 2.4.3 pendiente.
- **Autogeneración de `models.py`** — usar `sqlacodegen` para generar el ORM de SQLAlchemy directamente desde el esquema de la BD, en lugar de mantenerlo a mano.
- **Login con terceros (OAuth)** — integración con Google.
- **Conclusiones comparativas en modales EELL** — los dos modales de estadísticas EELL ("Top provincias" y "Concentración del importe") analizan el estado agregado pero no comparan la evolución entre las tres convocatorias disponibles (2023, 2024, 2025). Ampliar los textos con tendencias interanuales (p.ej. qué CCAA ganó o perdió peso, si la concentración aumenta) añadiría valor analítico. Los modales de home y EPA ya tienen conclusiones completas.

### Producción y seguridad

- **Dominio real y certificado Let's Encrypt** — sustituir el certificado autofirmado por uno de Let's Encrypt (gratuito, renovación automática, confiado por todos los navegadores).
- **Puerto de base de datos** — en producción eliminar la exposición del puerto `3307` en `docker-compose.yml`; la BD y el backend se comunican dentro de la red Docker sin necesidad de exponer el puerto al host.
- **CORS con dominio específico** — cambiar `CORS_ORIGINS=*` por `CORS_ORIGINS=https://mi-dominio.com` en `docker/.env` (ya implementado mediante variable de entorno, solo requiere configuración).
- **CAPTCHA en registro** — reCAPTCHA o hCaptcha para bloquear bots sofisticados. Requiere dependencia de terceros y añade fricción al usuario; desproporcionado para este proyecto en su estado actual.
- **Blocklist de dominios desechables** — bloquear `mailinator.com`, `guerrillamail.com` y similares al registrarse. Hay cientos de dominios y se actualizan constantemente; coste de mantenimiento alto para el beneficio obtenido.
