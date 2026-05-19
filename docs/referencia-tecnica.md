# Referencia técnica del proyecto

Datos concretos del sistema para consulta rápida.

---

## Contenedores Docker

| Contenedor | Imagen | Función |
|---|---|---|
| `bdns_nginx` | nginx:alpine | Proxy inverso: sirve el frontend estático y redirige las rutas `/api` al backend. Gestiona HTTPS y rate limiting. |
| `bdns_api` | python:3.11-slim (build local) | Backend FastAPI (uvicorn, puerto 8000 interno). Expone la API REST. |
| `bdns_dgda_db` | mariadb:11 | Base de datos principal. |
| `bdns_cron` | python:3.12-slim (build local) | Scheduler Python: comprueba periódicamente la API BDNS para detectar nuevas convocatorias. |
| `bdns_mailpit` | axllent/mailpit | Servidor SMTP de desarrollo. Captura los emails enviados sin llegar a destino real. |
| `bdns_adminer` | adminer | Interfaz web para administrar la BD directamente. Solo para desarrollo. |

### Puertos expuestos al host

| Puerto | Servicio | Uso |
|---|---|---|
| 80 | nginx | HTTP → redirige a HTTPS |
| 443 | nginx | HTTPS (dominio: `subvencionesDGDA.local`) |
| 3307 | MariaDB | Acceso externo a la BD (interno: 3306) |
| 8025 | Mailpit | Interfaz web para ver emails capturados |
| 1025 | Mailpit | Puerto SMTP |
| 8080 | Adminer | Interfaz web de administración de BD |

---

## Fuentes de datos y pipeline

### Fuentes

| Fuente | Tipo | Contenido | Herramienta de extracción |
|---|---|---|---|
| API BDNS (infosubvenciones.es) | REST/JSON | Convocatorias EPA y EELL | `bdns_client.py` (requests) |
| BOE (XML) | XML | Resoluciones EELL 2025 | `parser_eell_BOE_2025.py` (BeautifulSoup) |
| BOE (PDF) | PDF | Resoluciones EPAs 2021–2025 | `parser_EPAs_BOE_base.py`, `parser_EPAs_BOE_2025.py` (pdfplumber) |
| PDF resoluciones EELL | PDF | Resoluciones EELL 2023–2024 | `parser_eell_PDF_base.py` (pdfplumber, dos pasadas) |
| Excel manual (DGDA) | XLSX | EELL 2025 (beneficiarias y municipios) | `parser_eell_BOE_2025.py` (openpyxl) |

### Pipeline de datos

```
Fuentes externas (API / PDF / XML / XLSX)
        ↓
  scripts/parsers → data/processed/  (9 JSON por año y tipo)
        ↓
  unificar_datasets.py → data/final/dataset_unificado.json
        ↓
  cargar_dataset.py → Base de datos (6 pasos respetando FKs)
```

### Archivos JSON generados

- `data/processed/epas/` → 5 archivos (2021–2025)
- `data/processed/eell/` → 3 archivos (2023–2025)
- `data/final/dataset_unificado.json` → dataset completo normalizado

---

## Base de datos

10 tablas en total.

### Tablas de datos

| Tabla | Contenido |
|---|---|
| `convocatorias` | Convocatorias anuales EPA y EELL |
| `beneficiarios` | Entidades solicitantes (protectoras y ayuntamientos) |
| `solicitudes` | Una fila por solicitud presentada en una convocatoria |
| `concesiones` | Solo solicitudes con estado concedida e importe > 0 |
| `agrupaciones` | Concesiones presentadas como agrupación de ayuntamientos (solo EELL) |
| `agrupacion_miembros` | Municipios miembros de cada agrupación EELL |

### Tablas de usuarios y autenticación

| Tabla | Contenido |
|---|---|
| `usuarios` | Cuentas de acceso a la plataforma (`nombre` VARCHAR 100 nullable — alias opcional) |
| `refresh_tokens` | Tokens de larga duración para renovar el access token |
| `reset_tokens` | Tokens de un solo uso para recuperar contraseña |
| `verificacion_tokens` | Tokens de un solo uso para confirmar email al registrarse |

*Nota: tablas `causas_exclusion` y `solicitud_causas` están diseñadas pero no implementadas.*

---

## Seguridad

### Autenticación y tokens

| Elemento | Valor |
|---|---|
| Access token (JWT) | Expira en **60 minutos** |
| Refresh token | Expira en **30 días** |
| Token recuperación de contraseña | Expira en **15 minutos** (un solo uso) |
| Token verificación de email | Expira en **24 horas** (un solo uso) |
| Algoritmo hash contraseñas | bcrypt |
| Al cambiar contraseña | Se revocan todos los refresh tokens activos del usuario |

### Rate limiting (Nginx)

| Endpoint | Límite | Burst |
|---|---|---|
| `POST /auth/login` | 10 req/min por IP | 5 |
| `POST /auth/registro` | 5 req/min por IP | 3 |

### Otras medidas

| Medida | Descripción |
|---|---|
| Honeypot en registro | Campo `sitio_web` oculto: si llega relleno, se devuelve éxito falso sin crear cuenta |
| Verificación de email | Las cuentas nuevas tienen `email_verificado=0`; el login bloquea con 403 hasta verificar |
| Reenvío de verificación | `POST /auth/reenviar-verificacion` invalida tokens anteriores y envía nuevo enlace; siempre devuelve 200 |
| HTTPS | Certificado autofirmado, TLS 1.2 y 1.3 únicamente |
| Cabeceras de seguridad | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `HSTS: max-age=31536000` |
| Panel de admin | Solo accesible para usuarios con `rol = 'admin'` |
| Sesión activa en login/registro | Si hay token en `localStorage`, `login.html` y `registro.html` redirigen automáticamente a `privado.html` sin mostrar el formulario |
| Navbar en páginas públicas | `js/navbar.js` detecta el token en `localStorage` y reemplaza el botón "Acceder" por "Mi perfil" + "Cerrar sesión" sin necesidad de petición al servidor |

---

## Configuración HTTPS local

Nginx actúa como **terminador SSL**: recibe las peticiones HTTPS del navegador, descifra el tráfico y lo reenvía al backend por HTTP interno. El backend no necesita saber nada de SSL.

### Reproducir el entorno (instalación nueva)

1. Generar el certificado autofirmado (válido 1 año):

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/ssl/server.key \
  -out docker/ssl/server.crt \
  -subj "/CN=subvencionesDGDA.local/O=DAW/C=ES" \
  -addext "subjectAltName=DNS:subvencionesDGDA.local,DNS:localhost"
```

El `subjectAltName` es obligatorio — sin él, Chrome y Firefox rechazan la conexión.

1. Añadir al `/etc/hosts` del sistema (Windows: `C:\Windows\System32\drivers\etc\hosts`, requiere Bloc de notas como admin):

```text
127.0.0.1 subvencionesDGDA.local
```

1. `cd docker && docker compose up -d`
1. Acceder a `https://subvencionesDGDA.local` — aceptar el aviso de certificado autofirmado.

### Archivos generados

| Archivo | Versionar | Nota |
|---|---|---|
| `docker/ssl/server.crt` | No (`.gitignore`) | Certificado público — cada máquina genera el suyo |
| `docker/ssl/server.key` | No (`.gitignore`) | Clave privada — cada máquina genera la suya |

Cert y key deben ser del mismo par generado con el mismo `openssl`. Si uno proviene de git y el otro es local, Nginx falla al arrancar con `key values mismatch`.

---

## Cron (scheduler)

El contenedor `bdns_cron` ejecuta `scheduler.py` con dos tareas:

| Tarea | Frecuencia |
|---|---|
| `health_check.py` | Cada 6 horas (00:00, 06:00, 12:00, 18:00 UTC) |
| `check_bdns.py` (marzo) | Cada 4 días a las 08:00 UTC |
| `check_bdns.py` (abril–mayo) | Cada 2 días a las 08:00 UTC |
| `check_bdns.py` (junio) | Cada 4 días a las 08:00 UTC |

La frecuencia mayor en abril–mayo es porque es cuando suelen publicarse las convocatorias de la DGDA.

`check_bdns.py` ejecuta dos fases en cada llamada:

1. **Detección de resoluciones** (siempre): consulta `GET /bdnstrans/api/convocatorias/{num_convoc}` para cada convocatoria con `fecha_resolucion = NULL` del año actual. Si BDNS ya publica la fecha, la actualiza en la BD y el banner de la home desaparece automáticamente.
2. **Detección de nuevas convocatorias** (solo si faltan): busca nuevas convocatorias DGDA del año actual en la API BDNS por palabras clave del título. Si encuentra una nueva, la inserta con `fecha_resolucion = NULL`.

Los títulos que devuelve la API BDNS son los títulos oficiales del BOE, que pueden ser muy largos (p. ej. *"Subvenciones a entidades locales destinadas a mejorar e impulsar el control poblacional de colonias felinas, correspondiente al año 2026"*). El cron normaliza el título antes de insertarlo usando un diccionario interno, de forma que todos los registros mantengan el mismo formato corto independientemente de lo que devuelva la API.

Detección de tipo por palabras clave en el título:

| Tipo | Palabras clave |
|---|---|
| `eell` | `"ENTIDADES LOCALES"`, `"EELL"` |
| `epa` | `"ENTIDADES PRIVADAS"`, `"ASOCIACIONES"`, `"PROTECCI"` (cubre "protección animal") |

### Lanzar el cron manualmente

```bash
docker exec bdns_cron python3 /app/scripts/check_bdns.py
```

### Mantenimiento anual — qué actualizar en el código

El cron actualiza las BDs en ejecución automáticamente. Para que instalaciones nuevas arranquen con los datos correctos sin esperar al cron, hay que mantener dos sitios en el código cada año:

| Evento | Fichero | Qué cambiar |
|--------|---------|-------------|
| Sale convocatoria nueva | `scripts/data_processing/cargar_dataset.py` | Añadir `(año, tipo): (fecha_conv, None)` en `_FECHAS` |
| Sale convocatoria nueva | `install.sh` | Añadir `INSERT ... WHERE NOT EXISTS` en el bloque de migraciones |
| Sale resolución | `scripts/data_processing/cargar_dataset.py` | Cambiar `None` → fecha en `_FECHAS` |
| Sale resolución | `install.sh` | Añadir `UPDATE ... WHERE fecha_resolucion IS NULL` en migraciones |

Sin estas actualizaciones la app funciona igualmente (el cron lo compensa), pero una instalación nueva hecha inmediatamente después del `git pull` tardará horas en ver los datos correctos.

---

## Instalación

```bash
git clone git@github.com:vcv-code/analisis-bdns-dgda.git
cd analisis-bdns-dgda
bash install.sh
```

**Prerequisitos:** Docker con `docker compose` v2 · Python 3.10+ · openssl
**Plataforma:** Linux · macOS · WSL2 (Windows requiere Docker Desktop con integración WSL2)
**Descarga primera vez:** ~300-400 MB de imágenes Docker
**Espacio en disco:** ~1 GB (imágenes Docker) + ~50 MB opcionales si se crea el venv (solo necesario para tests y scripts de parseo)

El script detecta instalaciones existentes y no sobreescribe datos. Si la BD ya tiene solicitudes, solo levanta los contenedores. Para reinstalar desde cero: `make reset-db`.

### Qué se descarga en la primera instalación

| Imagen | Uso | Tamaño aproximado |
|--------|-----|-------------------|
| `mariadb:11` | Base de datos | ~120 MB |
| `python:3.11-slim` | Backend y cron (compartida) | ~75 MB |
| `nginx:alpine` | Proxy inverso | ~11 MB |
| `adminer` | Interfaz web de BD | ~13 MB |
| `axllent/mailpit` | SMTP de desarrollo | ~13 MB |

En instalaciones posteriores las imágenes ya están cacheadas localmente — arrancar el entorno es instantáneo.

---

## Comandos de referencia

| Acción | Comando |
|---|---|
| Levantar entorno | `cd docker && docker compose up -d` |
| Parar y recrear (tras reinicio WSL2) | `cd docker && docker compose down && docker compose up -d` |
| Rebuild del backend | `cd docker && docker compose up --build -d backend` |
| Recargar config nginx | `docker exec bdns_nginx nginx -s reload` |
| Verificar config nginx | `docker exec bdns_nginx nginx -t` |
| Rebuild backend + reiniciar | `cd docker && docker compose down && docker compose up -d` (tras reinicio WSL2) |
| Ver logs nginx | `docker logs bdns_nginx --tail 50` |
| Ejecutar tests | `source venv/bin/activate && python -m pytest tests/ -q` |
| Lanzar cron manualmente | `docker exec bdns_cron python3 /app/scripts/check_bdns.py` |
| Rebuild del cron | `cd docker && docker compose up --build -d cron` |

---

## Librerías del backend

| Librería | Versión | Para qué se usa |
|---|---|---|
| **FastAPI** | 0.135.3 | Framework principal de la API REST. Define todos los routers y el middleware de logging. |
| **uvicorn** | 0.42.0 | Servidor ASGI que arranca FastAPI en el puerto 8000 dentro del contenedor. |
| **SQLAlchemy** | 2.0.48 | ORM: define los modelos de datos y ejecuta las consultas a MariaDB. |
| **PyMySQL** | 1.1.2 | Driver que conecta SQLAlchemy con MariaDB (`mysql+pymysql://...`). |
| **bcrypt** | 5.0.0 | Hash y verificación de contraseñas en registro y login. |
| **python-jose** | 3.5.0 | Genera y valida los JWT (access token y refresh token) con algoritmo HS256. |
| **cryptography** | 46.0.5 | Soporte criptográfico requerido por python-jose para la firma HS256. |
| **email-validator** | 2.3.0 | Valida el formato del email en el schema del registro. **Importante:** la versión 2.x rechaza dominios especiales/reservados (`.local`, `.test`, `.example`, `.internal`, `.localhost`) con error 422. Los emails de desarrollo o demo deben usar un TLD público válido (`@demo.com`, `@example.com`). |
| **pytest** | 9.0.3 | Framework de tests. |
| **httpx** | 0.28.1 | Cliente HTTP que simula peticiones a la API en los tests (`TestClient`). |

### Librerías del frontend (CDN)

No hay bundler ni Node.js. Todo es HTML + CSS + JS vanilla servido por Nginx.

| Librería | Versión | Usado en | Para qué |
|---|---|---|---|
| **Chart.js** | 4.4.0 | `index.html`, `estadisticas-epas.html`, `estadisticas-eell.html` | Gráficas de línea, barras y donut. |
| **Google Fonts (Inter)** | — | Todos los HTML | Tipografía: pesos 400, 600 y 700. |

### Librerías de los scripts de datos (parsers)

| Librería | Para qué |
|---|---|
| **requests** | Descarga convocatorias de la API BDNS con paginación. |
| **pdfplumber** | Extrae texto y tablas de los PDFs del BOE (EPAs 2021–2025, EELL 2023–2024). |
| **BeautifulSoup** | Parsea el XML del BOE para resoluciones EELL 2025. |
| **openpyxl** | Lee el Excel manual de EELL 2025 (hojas de beneficiarias y municipios). |

---

## Sistema de logs

### Logs del backend

- **Formato:** `"YYYY-MM-DD HH:MM:SS | LEVEL | mensaje"`
- **Qué se registra:**
  - Cada petición HTTP: `"IP | METHOD /ruta | STATUS | Xms"`
  - Errores 500: `"METHOD /ruta | TipoExcepcion: mensaje"`
- **Destinos (en Docker):**
  - Consola: siempre activa
  - `logs/app/access.log` — rotación cada 5 MB, 5 copias de backup
  - `logs/app/error.log` — solo errores, misma rotación

### Logs de Nginx

- **Formato:** `"IP | fecha | request | status | tiempo_respuesta"`
- **Destinos:**
  - `logs/nginx/access.log` — todas las peticiones HTTP y HTTPS
  - `logs/nginx/error.log` — nivel `warn` en adelante

---

## Tests

- **Base de datos:** SQLite en memoria (`:memory:`) con `StaticPool` — todas las conexiones comparten la misma instancia, sin necesidad de MariaDB levantado
- **Fixtures en `conftest.py`:** `client` (crea/destruye tablas por test) y `db` (sesión para insertar datos)
- **Total:** 197 tests pasando, 0 fallando (actualizado 2026-05-15)

| Archivo | Qué testea |
|---|---|
| `test_smoke.py` | `GET /` y `GET /health` responden correctamente |
| `test_auth.py` | Registro, login, refresh token, recuperación y reset de contraseña |
| `test_refresh_token.py` | Renovación del access token con refresh token |
| `test_recuperar_password.py` | Solicitud y validación del token de reset |
| `test_verificacion_email.py` | Flujo completo de verificación de email post-registro |
| `test_privado.py` | Endpoints del área privada: cambiar contraseña y nombre/alias |
| `test_admin.py` | Control de acceso, gestión de usuarios y avisos, visor de logs de acceso y de error |
| `test_avisos.py` | CRUD de avisos de convocatorias |
| `test_convocatorias.py` | `GET /convocatorias/` devuelve JSON válido |
| `test_solicitudes.py` | Filtros, paginación y búsqueda en `/solicitudes/` |
| `test_estadisticas.py` | Endpoints de estadísticas EPA/EELL con datos reales insertados |
| `test_agrupaciones.py` | Clasificación y consulta de agrupaciones EELL |
| `test_logging.py` | El middleware loguea IP, método, ruta, código y duración |
| `test_https_config.py` | Certificado SSL presente, TLS 1.2+, cabeceras de seguridad |
| `test_cache_headers.py` | Headers `Cache-Control` en respuestas estáticas y dinámicas |
| `test_rate_limiting.py` | Configuración de zonas de rate limiting en `nginx/default.conf` |
| `test_parser_epa2025.py` | Funciones puras del parser XML de EPAs 2025 |
| `test_unificar_datasets.py` | Script de unificación EPA/EELL en `dataset_unificado.json` |

---

## Glosario

| Término | Definición breve |
|---|---|
| **BDNS** | Base de Datos Nacional de Subvenciones. API pública del gobierno con datos de convocatorias. |
| **DGDA** | Dirección General de Derechos de los Animales. Organismo que gestiona las subvenciones de bienestar animal. |
| **EPA** | Entidades Protectoras de Animales. Protectoras y refugios que pueden solicitar subvenciones DGDA. |
| **EELL** | Entidades Locales. Ayuntamientos y mancomunidades que también pueden solicitar estas subvenciones. |
| **BOE** | Boletín Oficial del Estado. Fuente oficial donde se publican convocatorias y resoluciones. |
| **Convocatoria** | Llamada oficial a solicitar una subvención, con plazos y requisitos. Una por año y tipo (EPA o EELL). |
| **Solicitud** | Candidatura de una entidad a una convocatoria. Puede terminar en cualquier estado. |
| **Concesión** | Solicitud con estado "concedida" e importe asignado. |
| **No beneficiaria** | Estado de una solicitud que puntúa pero queda fuera por falta de presupuesto. |
| **Excluida** | Estado de una solicitud rechazada por problemas en la documentación o tramitación. |
| **Desistida** | Estado de una solicitud abandonada por la entidad (no completó el trámite en plazo). |
| **Agrupación** | Concesión EELL presentada conjuntamente por varios ayuntamientos; el importe no se desglosa por municipio. |
| **JWT** | JSON Web Token. Formato estándar para transmitir la identidad del usuario de forma segura y sin estado en servidor. |
| **Access token** | Token de corta duración (60 min) que autoriza cada petición a la API. |
| **Refresh token** | Token de larga duración (30 días) que permite obtener un nuevo access token sin volver a hacer login. |
| **ORM** | Object-Relational Mapper. Capa que traduce entre objetos Python y filas de la BD (aquí: SQLAlchemy). |
| **ASGI** | Interfaz estándar entre servidor web y aplicación Python asíncrona (aquí: uvicorn + FastAPI). |
| **Proxy inverso** | Servidor que recibe las peticiones del cliente y las redirige al servicio correcto internamente (aquí: Nginx → FastAPI). |
| **Rate limiting** | Límite de peticiones por IP en un intervalo de tiempo para frenar ataques de fuerza bruta. |
| **Honeypot** | Campo oculto en un formulario. Si llega relleno, es un bot — se simula éxito sin crear la cuenta. |
| **CDN** | Red de distribución de contenidos. Aquí se usa para cargar Chart.js y Google Fonts desde servidores externos. |
| **Bearer token** | Formato de autenticación HTTP: `Authorization: Bearer <token>`. El cliente lo envía en cada petición protegida. |
| **HSTS** | HTTP Strict Transport Security. Cabecera que obliga al navegador a usar siempre HTTPS con este dominio. |
| **TLS** | Transport Layer Security. Protocolo de cifrado de la conexión HTTPS (versiones 1.2 y 1.3 activas). |
| **SQLite en memoria** | Base de datos temporal que vive en RAM durante los tests, sin tocar MariaDB. Rápida y aislada por test. |
| **StaticPool** | Configuración de SQLAlchemy para que SQLite en memoria comparta una única conexión entre threads (necesario en tests). |
