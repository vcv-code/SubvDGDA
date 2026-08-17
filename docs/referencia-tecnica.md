# Referencia técnica del proyecto

Datos concretos del sistema para consulta rápida.

---

## Contenedores Docker

| Contenedor | Imagen | Función |
|---|---|---|
| `bdns_nginx` | nginx:alpine | Proxy inverso: sirve el frontend estático y redirige las rutas `/api` al backend. Gestiona HTTPS y rate limiting. |
| `bdns_api` | python:3.12-slim (build local) | Backend FastAPI (uvicorn, puerto 8000 interno). Expone la API REST. |
| `bdns_dgda_db` | mariadb:11.8 | Base de datos principal. |
| `bdns_cron` | python:3.12-slim (build local) | Scheduler Python: comprueba periódicamente la API BDNS para detectar nuevas convocatorias. |
| `bdns_mailpit` | axllent/mailpit | Servidor SMTP de desarrollo. Captura los emails enviados sin llegar a destino real. |
| `bdns_adminer` | adminer | Interfaz web para administrar la BD directamente. Solo para desarrollo. |

### Puertos expuestos al host

| Puerto | Servicio | Uso |
|---|---|---|
| 80 | nginx | HTTP → redirige a HTTPS |
| 443 | nginx | HTTPS (dominio: `subvencionesDGDA.local`) |
| 3307 | MariaDB | Acceso a la BD desde el propio equipo (interno: 3306) — **solo `127.0.0.1`** |
| 8025 | Mailpit | Interfaz web para ver emails capturados — **solo `127.0.0.1`** |
| 1025 | Mailpit | Puerto SMTP — **solo `127.0.0.1`** |
| 8080 | Adminer | Interfaz web de administración de BD — **solo `127.0.0.1`** |

Los puertos marcados como `127.0.0.1` se publican **solo en la interfaz local**: se llega a ellos desde el propio equipo, pero no desde la red. En un servidor eso es lo que impide que Adminer o Mailpit queden accesibles desde internet — y no basta con el cortafuegos, porque Docker escribe sus reglas por delante de las de ufw. Desde fuera se llega por túnel SSH: `ssh -L 8080:localhost:8080 servidor`.

El backend (`bdns_api`, puerto 8000) **no expone ningún puerto al host** — solo es accesible desde dentro de la red Docker interna. Nginx actúa como única puerta de entrada.

---

## Versiones de las tecnologías y por qué

| Tecnología | Versión | Tipo de pin | Por qué esa elección |
|---|---|---|---|
| **Python** (backend y cron) | `3.12-slim` | Versión menor | Moderna y con soporte (oct 2023). `slim` reduce la imagen de ~900 MB a ~75 MB. Unificada entre backend y cron (antes el backend iba en 3.11) para coherencia y para que las librerías compartidas (`PyMySQL`, `bcrypt`) se comporten igual. Pin a menor recibe parches sin saltar a 3.13. |
| **MariaDB** | `mariadb:11.8` | Versión menor | Serie actual de MariaDB. Pin a `11.8` da reproducibilidad (antes era `mariadb:11` flotante, que cambiaba en cada `build`). **No se eligió 11.4 LTS** porque MariaDB no permite arrancar una versión menor sobre datos creados por una mayor — pasar de 11.8 a 11.4 exigiría borrar el volumen y recargar el dataset. |
| **Nginx** | `nginx:alpine` | Sin pin | La imagen `alpine` ya es mínima (~25 MB). Funcionalidad de proxy estable, sin riesgo en versión rolling. |
| **Mailpit** | `axllent/mailpit` | Sin pin | Solo desarrollo, no crítico. |
| **Adminer** | `adminer` | Sin pin | Solo desarrollo, no crítico. |

### Principios de selección

1. **Tamaño primero** en imágenes core (backend, cron, nginx): todas son `slim` o `alpine`. Python `slim` ahorra ~825 MB respecto a la completa.
2. **Pin a versión menor** para Python y MariaDB: protege de saltos accidentales a la siguiente menor pero sigue recibiendo parches de seguridad de la actual.
3. **Coherencia entre servicios de aplicación**: backend y cron usan la misma menor de Python para que las librerías comunes funcionen igual en ambos entornos.
4. **Reciente y soportado**, no necesariamente LTS: para un proyecto académico, una serie actual y con soporte vigente basta. En producción, MariaDB 11.4 LTS (soportada hasta 2029) sería el siguiente paso natural, pero implica empezar el volumen desde cero.

---

## docker-compose.yml — decisiones de configuración

### Arranque ordenado con healthcheck

MariaDB tarda unos segundos en inicializarse completamente tras arrancar el proceso. Sin control de orden, el backend podría intentar conectarse antes de que la BD esté lista.

```yaml
db:
  healthcheck:
    test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
    interval: 10s
    retries: 5

backend:
  depends_on:
    db:
      condition: service_healthy   # espera a que el healthcheck pase
```

`service_healthy` es más fiable que `service_started` (que solo espera a que el proceso arranque, no a que esté listo para recibir conexiones). `adminer` y `cron` también dependen de `db` con `service_healthy`.

### Healthchecks de runtime (backend y nginx)

Más allá del arranque ordenado, `backend` y `nginx` tienen healthchecks que se ejecutan continuamente para detectar **cuelgues que no matarían el proceso** (deadlocks, bucles infinitos, conexiones agotadas). Sin healthcheck, `restart: unless-stopped` no actúa porque el proceso sigue "vivo" desde el punto de vista de Docker, aunque no responda.

```yaml
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 20s

nginx:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost/healthz"]
    interval: 30s
    timeout: 5s
    retries: 3
    start_period: 5s
```

`docker compose ps` muestra `(healthy)` o `(unhealthy)` por servicio en la columna STATUS. El resumen:

| Servicio | Healthcheck | Comando | Motivo |
|---|---|---|---|
| `db` | Sí (oficial MariaDB) | `healthcheck.sh --connect --innodb_initialized` | Asegura arranque ordenado del backend |
| `backend` | Sí (propio) | `curl -f http://localhost:8000/health` | Detecta cuelgues que no matan el proceso |
| `nginx` | Sí (propio) | `curl -f http://localhost/healthz` | Verifica que Nginx responde a HTTP independientemente del backend |
| `cron` | No | — | No expone HTTP. Su salud se ve en `logs/cron/health_check.log` y `restart: unless-stopped` cubre los crashes |
| `mailpit` | Sí (de fábrica) | Heredado de la imagen oficial | No lo configuramos nosotros |
| `adminer` | No | — | Herramienta de desarrollo, no crítica |

**Sobre `/healthz` en Nginx:** es un endpoint propio definido en `docker/nginx/default.conf` dentro del bloque HTTP (puerto 80). Devuelve `200 "ok"` directamente sin pasar por el backend y **sin redirigir a HTTPS** — de ese modo el healthcheck verifica que Nginx vive aunque el backend esté caído.

```nginx
server {
    listen 80;
    location = /healthz {
        access_log off;
        add_header Content-Type text/plain;
        return 200 "ok\n";
    }
    location / {
        return 301 https://$host$request_uri;
    }
}
```

**Sobre `curl` en lugar de `wget`:** la imagen `nginx:alpine` trae ambos, pero el `wget` de BusyBox resuelve `localhost` a IPv6 (`::1`) y Nginx solo escucha en IPv4 → el healthcheck fallaba con `Connection refused`. Usar `curl` (que prueba IPv4 correctamente) es además consistente con el healthcheck del backend.

**Sobre `curl` en el backend:** se instala en `backend/Dockerfile` con `apt-get install -y --no-install-recommends curl` (~6 MB sobre la imagen slim). Además del healthcheck, queda disponible para depurar la conexión backend↔BD desde dentro del contenedor (`docker exec bdns_api curl -v http://db:3306`).

### Red interna Docker y DNS automático

Docker Compose crea una red privada para todos los servicios. Cada servicio es accesible por su nombre desde cualquier otro contenedor:

```yaml
backend:
  environment:
    DB_HOST: db          # resuelve al contenedor bdns_dgda_db
    SMTP_HOST: mailpit   # resuelve al contenedor bdns_mailpit

cron:
  environment:
    BACKEND_INTERNAL_URL: http://backend:8000   # accede al backend sin pasar por Nginx
```

El cron se comunica con el backend directamente por HTTP interno, no a través de Nginx/HTTPS.

### Volúmenes y bind mounts

```yaml
db:
  volumes:
    - db_data:/var/lib/mysql          # volumen nombrado: persiste entre down/up
    - ./init/modelo-fisico.sql:/docker-entrypoint-initdb.d/modelo-fisico.sql
    #  └── MariaDB aplica este SQL automáticamente la primera vez que el volumen está vacío

nginx:
  volumes:
    - ./nginx:/etc/nginx/conf.d:ro    # config de Nginx (read-only)
    - ./ssl:/etc/nginx/ssl:ro         # certificado SSL (read-only)
    - ../frontend:/usr/share/nginx/html:ro  # frontend como bind mount (read-only)
    - ../logs/nginx:/var/log/nginx    # logs accesibles desde el host

backend:
  volumes:
    - ../logs/app:/app/logs           # logs del backend accesibles desde el host
```

El frontend se monta como bind mount directo en Nginx. Cualquier cambio en `frontend/` se refleja inmediatamente sin reconstruir la imagen ni reiniciar el contenedor.

El volumen nombrado `db_data` garantiza que los datos de MariaDB sobreviven a `docker compose down` (solo se pierden con `docker compose down -v`).

### restart: unless-stopped

Todos los servicios tienen `restart: unless-stopped`. El contenedor se reinicia automáticamente si falla o si Docker Desktop arranca con el sistema, **excepto** si se paró explícitamente con `docker compose down`. Útil en un entorno de desarrollo que se usa a diario.

### Recrear contenedores cuando algo va mal

Dos patrones cubren la mayoría de incidencias en Docker Desktop + WSL2:

| Síntoma | Comando | Por qué |
|---|---|---|
| Tras reiniciar Windows / WSL2 / Docker Desktop, algún contenedor falla por errores de volúmenes o bind mounts | `cd docker && docker compose down && docker compose up -d` | Los bind mounts de WSL2 usan rutas con hash que cambian al reiniciar. Los contenedores viejos referencian el hash antiguo. `down && up` los recrea con bind mounts frescos. Nunca `docker compose restart <servicio>` suelto en este escenario. |
| Un contenedor está atascado pese a haberlo reiniciado: no responde, no recoge una imagen recién reconstruida, conexión persistente envenenada | `cd docker && docker compose up --force-recreate -d` | `up -d` solo recrea si detecta cambios en la configuración; si el problema es de estado interno (proceso colgado, capas obsoletas) no lo nota. `--force-recreate` ignora la comparación y mata + crea de nuevo cada contenedor. Reservar para casos puntuales — no usar como rutina. |

Si ambos comandos fallan, el siguiente nivel es `docker compose down -v` (borra el volumen `db_data`, **pierdes los datos** de la BD) + `bash install.sh` para empezar desde cero.

### Variables de entorno y .env

Ningún secreto está hardcodeado en `docker-compose.yml`. Todos los valores sensibles se leen de `docker/.env`:

```text
${MYSQL_ROOT_PASSWORD}   ${MYSQL_USER}   ${MYSQL_PASSWORD}
${MYSQL_DATABASE}        ${SECRET_KEY}   ${CORS_ORIGINS}
```

`docker/.env` se genera automáticamente en `install.sh` con contraseñas aleatorias y no se versiona (`.gitignore`). Cada instalación tiene sus propias credenciales.

---

## Dockerfiles

### Backend (`backend/Dockerfile`)

```dockerfile
FROM python:3.12-slim          # imagen mínima: ~75 MB vs ~900 MB de la completa

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# └── requirements antes que el código: Docker cachea esta capa y no repite
#     pip install si solo cambia el código de la aplicación

COPY app ./app                 # solo se re-ejecuta si cambia el código

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`--no-cache-dir` evita que pip almacene la caché de descarga dentro de la imagen, reduciendo su tamaño final.

### Cron (`docker/cron/Dockerfile`)

```dockerfile
FROM python:3.12-slim

RUN pip install --no-cache-dir requests pymysql
# Solo dos dependencias: no necesita FastAPI, SQLAlchemy ni nada del backend

RUN mkdir -p /app/logs/cron /app/scripts

COPY scripts/     /app/scripts/
COPY scheduler.py /app/scheduler.py

CMD ["python3", "/app/scheduler.py"]
```

El cron usa `python:3.12-slim` — la misma versión menor que el backend (ver sección [Versiones de las tecnologías](#versiones-de-las-tecnologías-y-por-qué)). Cada Dockerfile construye su propia imagen: si una falla, la otra sigue funcionando.

---

## Fuentes de datos y pipeline

### Fuentes

| Fuente | Tipo | Contenido | Herramienta de extracción |
|---|---|---|---|
| API BDNS (infosubvenciones.es) | REST/JSON | Convocatorias EPA y EELL | `bdns_client.py` (requests) |
| BOE (XML) | XML | Resoluciones EELL 2025 | `parser_eell_BOE_2025.py` (BeautifulSoup) |
| BOE (XML) | XML | Resoluciones EPAs 2021–2025 (incl. causas de exclusión) | `parser_EPAs_BOE_base.py`, `parser_EPAs_BOE_2025.py` (BeautifulSoup) |
| PDF resoluciones EELL | PDF | Resoluciones EELL 2023–2024 | `parser_eell_PDF_base.py` (pdfplumber, dos pasadas) |
| Excel manual (DGDA) | XLSX | EELL 2025 (beneficiarias y municipios) | `parser_eell_BOE_2025.py` (openpyxl) |

### Pipeline de datos

```text
Fuentes externas (API / PDF / XML / XLSX)
        ↓
  scripts/parsers → data/processed/  (9 JSON por año y tipo)
        ↓
  unificar_datasets.py → data/final/dataset_unificado.json
        ↓
  normalizar_causa_exclusion.py → causas como códigos canónicos ";"
        ↓
  cargar_dataset.py → Base de datos (7 pasos respetando FKs)
```

### Archivos JSON generados

- `data/processed/epas/` → 5 archivos (2021–2025)
- `data/processed/eell/` → 3 archivos (2023–2025)
- `data/final/dataset_unificado.json` → dataset completo normalizado
- `data/final/causas_exclusion.json` → catálogo código→motivo de causas de exclusión por (tipo, año); revisado a mano contra los anexos oficiales, se carga en la tabla `causas_exclusion`

---

## Recursos y URLs externas

Listado consolidado de todos los servicios y documentos externos a los que el proyecto se conecta o referencia.

### APIs públicas — BDNS

El sistema BDNS (Base de Datos Nacional de Subvenciones), gestionado por la IGAE del Ministerio de Hacienda, se expone en **dos dominios públicos distintos**:

| Tipo | Dominio | Uso en el proyecto |
|---|---|---|
| **Portal público (UI web)** | `https://www.pap.hacienda.gob.es/bdnstrans/GE/es/index` | Enlace en el footer de la web (referencia visible para el usuario final) |
| **API REST (JSON)** | `https://www.infosubvenciones.es/bdnstrans/api` | Endpoint que consulta el cron (`check_bdns.py`) y el cliente de ingesta (`bdns_client.py`) |

Endpoints concretos de la API que el proyecto usa:

| Recurso | URL completa | Uso |
|---|---|---|
| Búsqueda paginada de convocatorias | `https://www.infosubvenciones.es/bdnstrans/api/convocatorias/busqueda` | Detección de nuevas convocatorias DGDA |
| Detalle de una convocatoria | `https://www.infosubvenciones.es/bdnstrans/api/convocatorias/{num_convoc}` | Comprobación del campo `fechaResolucion` cuando BDNS publica la resolución |

### Bases reguladoras (PDF)

Enlazadas desde la sección "Convocatorias" de la home (bajo cada tabla).

| Documento | URL | Origen |
|---|---|---|
| Bases reguladoras EPAs 2021 | [`BOE-A-2021-16021.pdf`](https://www.boe.es/boe/dias/2021/10/01/pdfs/BOE-A-2021-16021.pdf) | BOE |
| Modificación bases EPAs 2024 | [`Modificacion-BBRR.pdf`](https://www.dsca.gob.es/sites/default/files/derechos-sociales/derechos-animales/docs/Modificacion-BBRR.pdf) | DGDA |
| Bases reguladoras EELL 2023 | [`bases-reguladoras.pdf`](https://www.dsca.gob.es/sites/default/files/derechos-sociales/bases-reguladoras.pdf) | DGDA |

### Resoluciones oficiales (BOE)

Enlazadas desde la sección "Resoluciones oficiales" de la home (8 enlaces hardcodeados en `index.html` con `target="_blank"`).

| Año | Tipo | URL |
|---|---|---|
| 2025 | EPA | [`BOE-A-2025-27109`](https://www.boe.es/buscar/doc.php?id=BOE-A-2025-27109) |
| 2024 | EPA | [`BOE-A-2024-23749`](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-23749) |
| 2023 | EPA | [`BOE-A-2023-23529`](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2023-23529) |
| 2022 | EPA | [`BOE-A-2022-22122`](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2022-22122) |
| 2021 | EPA | [`BOE-A-2022-602`](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2022-602) (publicada en enero 2022) |
| 2025 | EELL | [`BOE-A-2025-27204`](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-27204) |
| 2024 | EELL | [`BOE-A-2024-24205`](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-24205) |
| 2023 | EELL | [`BOE-A-2024-662`](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-662) (publicada en enero 2024) |

Las resoluciones EPA/EELL 2025 también se obtienen en formato XML para el parseo de beneficiarios (`https://www.boe.es/diario_boe/xml.php?id=BOE-A-AAAA-NNNNN`). Las de 2023 y 2024 se parsean del PDF original con `pdfplumber`.

### Web institucional DGDA

| URL | Uso |
|---|---|
| `https://www.dsca.gob.es/es/derechos-sociales/derechos-animales/subvenciones` | Página oficial DGDA sobre las subvenciones; enlazada desde el footer, aviso legal y privacidad |

### Recursos del frontend cargados de CDN

Detalle completo (versión, propósito, fallback) más abajo en la sección "Librerías del frontend (CDN con fallback local)" dentro del bloque "Librerías del backend". Resumen de URLs:

| Librería | URL CDN | Fallback local |
|---|---|---|
| Chart.js 4.4.0 | `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js` | `frontend/assets/vendor/chart.umd.min.js` |
| Leaflet 1.9.4 (JS) | `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js` | `frontend/assets/vendor/leaflet.js` |
| Leaflet 1.9.4 (CSS) | `https://unpkg.com/leaflet@1.9.4/dist/leaflet.css` | `frontend/assets/vendor/leaflet.css` |
| Google Fonts (Inter) | `https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap` | Sin fallback local (degrada a `font-family` de sistema) |

### Servicios de mapas

| Servicio | URL | Uso |
|---|---|---|
| OpenStreetMap tiles | `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` | Capa base del mapa choropleth en `exclusivo.html` (consumido por Leaflet) |

### Repositorios y desarrollo

| Recurso | URL | Uso |
|---|---|---|
| Repositorio GitHub | `https://github.com/vcv-code/SubvDGDA` | Código fuente, issues y PRs del proyecto |
| Texto oficial CC BY-NC-ND 4.0 | `https://creativecommons.org/licenses/by-nc-nd/4.0/deed.es` | Licencia del contenido (footer y `LICENSE`) |

---

## Endpoints de la API

La documentación interactiva completa (Swagger UI) está en `/docs` — accesible en `https://subvencionesDGDA.local/docs` con Docker levantado, o en `http://localhost:8000/docs` en modo desarrollo.

### Públicos (sin autenticación)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado del servidor |
| `GET` | `/convocatorias/` | Lista de convocatorias · `Cache-Control: 1 día` |
| `GET` | `/solicitudes/` | Solicitudes con filtros: `anio`, `tipo`, `estado`, `cif`, `buscar`, `ccaa`, `provincia`, `linea`, `orden`, `limite`, `offset` |
| `GET` | `/solicitudes/export` | Exportación CSV (máx. 5.000 filas) |
| `GET` | `/estadisticas/` | Métricas globales · `Cache-Control: 1 hora` |
| `GET` | `/estadisticas/epas` | Análisis de protectoras |
| `GET` | `/estadisticas/eell` | Análisis de ayuntamientos |
| `GET` | `/estadisticas/resumen-convocatorias` | Tabla resumen por tipo y año (recuento por estado + importe) · `Cache-Control: 1 hora` · se muestra en el inicio |
| `GET` | `/solicitudes/causas` | Leyenda código→motivo de causas de exclusión por tipo y año · `Cache-Control: 1 día` |
| `GET` | `/agrupaciones/{id_solic}` | Municipios miembro de una agrupación EELL |
| `GET` | `/avisos/` | Convocatorias del año en curso sin resolución |

### Autenticación (sin token)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/auth/registro` | Crear cuenta · devuelve 201 · inicia verificación de email |
| `GET` | `/auth/verificar` | Confirmar email con `?token=...` |
| `POST` | `/auth/reenviar-verificacion` | Reenviar email de verificación |
| `POST` | `/auth/login` | Login · devuelve `access_token` (15 min) + `refresh_token` (30 días) |
| `POST` | `/auth/refresh` | Renovar access token · rota el refresh token |
| `POST` | `/auth/logout` | Revocar refresh token |
| `POST` | `/auth/recuperar` | Solicitar enlace de reset · respuesta idéntica exista o no el email |
| `POST` | `/auth/reset` | Restablecer contraseña con token · revoca todos los refresh tokens |

### Contacto (público)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/contacto/` | Envía un mensaje de contacto por email · honeypot antispam + rate limiting (3 req/min) · 503 si el SMTP falla |

### Zona privada (rol: `registrado`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/privado/perfil` | Datos del usuario en sesión (`id_usuario`, `email`, `rol`, `nombre`) |
| `PUT` | `/privado/cambiar-nombre` | Actualizar alias |
| `PUT` | `/privado/cambiar-contrasena` | Cambiar contraseña · revoca todos los refresh tokens |
| `GET` | `/privado/resumen-exclusivo` | Datos para el mapa choropleth CCAA |
| `GET` | `/privado/resumen-tabla` | Tabla resumen de solicitudes por convocatoria (misma lógica que el endpoint público `/estadisticas/resumen-convocatorias`; se conserva para la página de registrados) |

### Panel de administración (rol: `admin`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/admin/estado` | Estado del sistema: número de usuarios, solicitudes y convocatorias |
| `GET` | `/admin/usuarios` | Lista paginada de usuarios (`pagina`, `limite`; devuelve `{ usuarios, total }`) |
| `PATCH` | `/admin/usuarios/{id}/rol` | Cambiar rol (`registrado` ↔ `admin`) |
| `PATCH` | `/admin/usuarios/{id}/activo` | Activar o desactivar cuenta |
| `DELETE` | `/admin/usuarios/{id}` | Eliminar usuario |
| `GET` | `/admin/avisos` | Lista de avisos activos |
| `PATCH` | `/admin/avisos/{id}/desactivar` | Desactivar aviso |
| `PATCH` | `/admin/avisos/{id}/reactivar` | Reactivar aviso |
| `PATCH` | `/admin/avisos/{id}/fin-plazo` | Fijar o borrar (null) la fecha de fin de plazo de solicitud |
| `DELETE` | `/admin/avisos/{id}` | Eliminar convocatoria sin resolución (409 si tiene solicitudes) |
| `GET` | `/admin/logs` | Últimas N líneas del log de acceso |
| `GET` | `/admin/logs/errores` | Últimas N líneas del log de errores |
| `GET` | `/admin/logs/cron` | Últimas N líneas de un log del cron (`fichero=bdns\|health`) |

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
| Access token (JWT) | Expira en **15 minutos** |
| Refresh token | Expira en **30 días** |
| Token recuperación de contraseña | Expira en **15 minutos** (un solo uso) |
| Token verificación de email | Expira en **24 horas** (un solo uso) |
| Algoritmo hash contraseñas | bcrypt |
| Al cambiar contraseña | Se revocan todos los refresh tokens activos del usuario |

### Rate limiting (Nginx)

| Endpoint | Límite | Burst | Motivo |
|---|---|---|---|
| `POST /auth/login` | 10 req/min por IP | 5 | Previene fuerza bruta de contraseñas |
| `POST /auth/registro` | 5 req/min por IP | 3 | Previene creación masiva de cuentas |
| `POST /auth/recuperar` | 3 req/min por IP | 2 | Previene spam de emails de recuperación |

Los tres devuelven HTTP 429 directamente desde Nginx sin llegar al backend cuando se supera el límite.

#### Algoritmo token bucket

Nginx implementa rate limiting con el algoritmo **token bucket** (cubo de tokens):

- El cubo tiene capacidad para `burst + 1` tokens.
- Los tokens se reponen al ritmo del `rate` (10r/m = 1 token cada 6 segundos).
- Cada petición consume un token. Si el cubo está vacío → 429.

Con `rate=10r/m` y `burst=5`:

- Se permiten **6 peticiones inmediatas** (1 del rate + 5 del burst).
- A partir de la 7ª petición en el mismo instante → 429.
- En un minuto completo no se pueden superar ~10 peticiones sostenidas.

**Metáfora:** un grifo llena un vaso a ritmo de 10 gotas por minuto. El vaso tiene capacidad para 6 gotas. Puedes beber las 6 de golpe (burst), pero tienes que esperar a que el grifo lo vuelva a llenar antes de poder beber más. El rate sostenido no cambia.

**Por qué 429 y no 503:** 503 significa "servicio no disponible". 429 significa "el servidor está bien, pero tú estás enviando demasiadas peticiones". Son situaciones distintas y el código de error correcto es el 429.

**Por qué `/auth/refresh` y `/auth/logout` no tienen rate limiting:** estos endpoints requieren presentar un refresh token válido de 64 caracteres aleatorios — sin ese token previo no hay nada que atacar por fuerza bruta. Limitarlos penalizaría usuarios legítimos (por ejemplo, múltiples pestañas renovando sesión a la vez) sin añadir protección real.

### Límites de datos en la API

| Endpoint | Límite | Motivo |
|---|---|---|
| `GET /solicitudes/` `?buscar=` | Máx. 200 caracteres | Previene queries LIKE muy largas en BD |
| `GET /solicitudes/` `?limite=` | Entre 1 y 500 | Previene peticiones de millones de filas |
| `GET /solicitudes/export` | Máx. 5.000 resultados | Previene exportaciones masivas sin filtros; devuelve 400 si se supera |

### Otras medidas

| Medida | Descripción |
|---|---|
| Honeypot en el formulario de contacto | Campo `sitio_web` oculto: si llega relleno, se devuelve éxito falso sin enviar nada |
| Sin registro público | No existe alta autoservicio: las cuentas se crean desde `POST /admin/usuarios`, protegido por rol admin |
| Verificación de email | Las cuentas nuevas tienen `email_verificado=0`; el login bloquea con 403 hasta verificar |
| Reenvío de verificación | `POST /auth/reenviar-verificacion` invalida tokens anteriores y envía nuevo enlace; siempre devuelve 200 |
| HTTPS | Certificado autofirmado, TLS 1.2 y 1.3 únicamente |
| Cabeceras de seguridad | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `HSTS: max-age=31536000` |
| Panel de admin | Solo accesible para usuarios con `rol = 'admin'` |
| Sesión activa en login/registro | Si hay token en `localStorage`, `login.html` y `registro.html` redirigen automáticamente a `privado.html` sin mostrar el formulario |
| Navbar en páginas públicas | `js/navbar.js` detecta el token en `localStorage` y añade al final del menú "Mi perfil", "Exclusivo" y "Cerrar sesión", sin necesidad de petición al servidor. El navbar no lleva botón "Acceder": el acceso está en el pie |
| SRI en recursos CDN | Atributos `integrity="sha384-..."` y `crossorigin="anonymous"` en los 5 recursos externos (Chart.js ×3, Leaflet JS, Leaflet CSS); el navegador verifica el hash antes de ejecutar/aplicar el recurso |

---

## Modo mantenimiento (Nginx)

Para paradas planificadas (despliegues, migraciones de BD, recargas de datos) hay un modo mantenimiento controlado por un **fichero-bandera** que Nginx comprueba en cada petición (sin reload):

- Si existe `maintenance.on` en la raíz del frontend, Nginx devuelve **503** para todo el tráfico (`error_page 503 → mantenimiento.html`), salvo los assets, la propia página de mantenimiento y `/healthz` (para que la página renderice y el healthcheck de Docker siga viendo Nginx vivo).
- El 503 de mantenimiento está **separado de `50x.html`** (que cubre 500/502/504). Los 503 que devuelve el backend (p. ej. SMTP caído en `/contacto/`) **no se interceptan** (`proxy_intercept_errors` desactivado) y llegan tal cual al cliente.
- Activar/desactivar: `make mantenimiento-on` / `make mantenimiento-off` (crea/borra el fichero, ignorado en `.gitignore`). El cambio es inmediato; no reinicia ni recarga nada.

## Rendimiento de carga del frontend

### Caché de assets estáticos (Nginx)

`docker/nginx/default.conf` define dos location blocks para cachear assets:

```nginx
location ~* \.(webp|png|jpg|jpeg|svg|gif|ico|woff2|woff|ttf|otf)$ {
    expires 1y;      # → Cache-Control: max-age=31536000
    try_files $uri =404;
}

location ~* \.(css|js)$ {
    expires 1h;      # → Cache-Control: max-age=3600
    try_files $uri =404;
}
```

- **Imágenes y fuentes** — 1 año: raramente cambian, el navegador no vuelve a pedirlas entre sesiones.
- **CSS y JS** — 1 hora: tiempo suficiente para evitar peticiones redundantes pero corto para que los cambios lleguen en el mismo día de trabajo.
- Las cabeceras de seguridad del servidor (`X-Frame-Options`, `X-Content-Type-Options`, etc.) siguen aplicando a estos bloques porque usan `expires`, no `add_header`, y la herencia de `add_header` no se rompe.

**Nota:** sin un sistema de cache busting (hash en el nombre del archivo), usar `expires` muy largo en CSS/JS haría que los cambios no llegaran hasta que expire la caché del navegador. La duración de 1 hora es el compromiso entre rendimiento y actualización en un entorno de desarrollo y demo.

### Scripts con `defer`

Todos los `<script src="...">` del proyecto usan el atributo `defer`:

```html
<script src="js/home.js" defer></script>
<script src="https://cdn.jsdelivr.net/.../chart.js" defer></script>
```

`defer` indica al navegador que descargue el script en paralelo mientras parsea el HTML, y que lo ejecute en orden después de que el parsing termine. Equivale a mover el script al final del `<body>` pero con descarga anticipada. Compatible con `DOMContentLoaded` porque los scripts diferidos ejecutan justo antes de que ese evento dispare.

El orden de ejecución se preserva: si `chart.js` viene antes que `home.js` en el documento, `chart.js` siempre ejecuta primero, aunque ambos estén diferidos.

### `fetchpriority` en la imagen hero

```html
<img src="assets/img/home/handcat.webp" fetchpriority="high">
```

El atributo `fetchpriority="high"` en la imagen hero de `index.html` indica al navegador que priorice su descarga frente a otros recursos de igual importancia. Mejora el LCP (Largest Contentful Paint) — la métrica que mide cuándo el usuario ve el contenido principal de la página.

---

## Breakpoints responsive del frontend

Todo el responsive del proyecto se hace con `@media (max-width: ...)` (mobile-first invertido) en una única hoja `frontend/css/styles.css`. No hay frameworks ni utilidades tipo Bootstrap; los breakpoints están definidos a mano y se aplican selectivamente a los componentes que los necesitan.

### Breakpoints principales

| Breakpoint | Frecuencia de uso | Aplica principalmente a |
|---|---|---|
| **900 px** | 4 reglas | Navbar: cambio a menú hamburguesa (≤900px). Grid de 3 columnas → 2 columnas. Se subió de 768 a 900 porque a 768 los items del navbar quedaban demasiado apretados |
| **768 px** | 9 reglas | Es el breakpoint más usado. `.grid-2` (cabeceras y bloques de dos columnas) colapsa a 1 columna. Ajustes de tipografía y padding en tablas, modales y tarjetas |
| **600 px** | 7 reglas | Móvil. `.grid-3` → 1 columna. **Crítico:** transformación de `.tabla-wrapper` del buscador a vista de tarjetas (`data-label` + `::before { content: attr(data-label) }`) para no obligar a scroll horizontal en pantallas estrechas |
| **480 px** | 4 reglas | Móvil pequeño. Reduce tamaños y márgenes en tarjetas de la home y elementos de hero |

### Breakpoints puntuales

| Breakpoint | Uso |
|---|---|
| `1024 px` con `min-width: 901 px` | Zona intermedia para evitar solapamiento del navbar en pantallas medianas: `.navbar__links a` baja a `1rem` |
| `1024 px` | Ajustes puntuales de espaciado en el hero |
| `680 px`, `640 px` | Ajustes específicos del modal de gráfica y del modal top-municipios (donde 600/768 producían diseño incómodo) |

### Filosofía aplicada

- **`.grid-2` colapsa antes que `.grid-3`** — dos columnas de contenido denso (tablas, tarjetas anchas) se aplastan más rápido que tres columnas de tarjetas pequeñas. Por eso `.grid-2` salta a 1 col en 768 px y `.grid-3` aguanta hasta 600 px.
- **Mismo breakpoint para varios componentes** — cuando un mismo punto (p. ej. 600 px) se usa para el grid y para la tabla del buscador, se reduce la cantidad de breakpoints distintos que el usuario percibe al redimensionar.
- **`pointer: coarse`** — para diferenciar interacción táctil de cursor, el mapa de CCAA en `exclusivo.html` usa la media query `(pointer: coarse)` además del breakpoint de tamaño. Un toque muestra tooltip; doble toque abre modal.

### Comprobar todos los breakpoints en CSS

```bash
grep -E "@media \(max-width: [0-9]+px\)|@media \(min-width: [0-9]+px\)" \
    frontend/css/styles.css | sort | uniq -c | sort -rn
```

Devuelve el conteo y la lista de breakpoints únicos usados en el proyecto.

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

Hay **dos sistemas de tareas programadas** y conviene no confundirlos:

| Dónde | Qué ejecuta | Por qué ahí |
|---|---|---|
| Contenedor `bdns_cron` (`scheduler.py`) | Comprobación de BDNS, salud y rotación de logs | Va con el proyecto: se comporta igual en local y en el servidor |
| `crontab` del servidor | Copia de seguridad de la base de datos | Necesita hablar con el contenedor de MariaDB, y darle al contenedor de cron acceso al demonio de Docker sería un permiso que no debe tener |

> **CUIDADO: hay dos cosas llamadas «crontab» y solo una funciona.**
>
> | | `docker/cron/crontab` | `crontab` del servidor |
> |---|---|---|
> | Qué es | Un fichero dentro del proyecto | El programador de tareas de Linux |
> | Quién lo ejecuta | **Nadie** | El sistema, siempre |
>
> El contenedor **no arranca `cron`**: arranca `scheduler.py`, un programa de
> Python propio. `docker/cron/crontab` quedó documentando la programación
> original y no tiene ningún efecto — ya pasó una vez que se añadió ahí una
> tarea y no se ejecutó jamás.
>
> **Al tocar el calendario del contenedor, el fichero que manda es
> `scheduler.py`** (su función `_jobs_for()`), y tiene tests.
>
> El `crontab` del servidor es otra cosa distinta y sí funciona: es el de
> Linux, corriendo fuera de los contenedores. Precisamente por estar fuera
> puede hablar con el contenedor de MariaDB, que es el motivo de que la copia
> de seguridad vaya ahí y no en `scheduler.py`.
>
> **De dónde viene esto, que sí tuvo que ver con WSL.** El contenedor iba a usar
> supercronic, un cron pensado para Docker. Falló con un error de *fork* al
> arrancar en Docker Desktop + WSL2 (bug de la versión v0.2.33), y por eso se
> escribió `scheduler.py` en Python. `docker/cron/crontab` es el resto de aquel
> intento.
>
> Ahora bien, **que ese fichero no se ejecute ya no depende de WSL**: es
> consecuencia de que el contenedor arranque `scheduler.py`. Ese mismo
> contenedor corre hoy en el servidor —Linux puro— y se comporta igual.
>
> Y una cosa distinta que sí es propia de WSL: allí el `cron` del sistema no
> suele estar en marcha, así que programar tareas del anfitrión en el portátil
> no funcionaría sin más. En el servidor sí.

### Tareas del contenedor

| Tarea | Frecuencia |
|---|---|
| `health_check.py` | Cada 6 horas (00:00, 06:00, 12:00, 18:00 UTC) |
| `rotar_logs.py` | Diaria, 04:15 UTC (retención de 30 días) |
| `check_bdns.py` (marzo) | Cada 4 días a las 08:00 UTC |
| `check_bdns.py` (abril–mayo) | Cada 2 días a las 08:00 UTC |
| `check_bdns.py` (junio) | Cada 4 días a las 08:00 UTC |
| `check_bdns.py` (noviembre–diciembre) | Cada 2 días a las 08:00 UTC |
| `check_bdns.py` (enero) | Cada 4 días a las 08:00 UTC |

### Criterio de selección de frecuencias

La frecuencia se diseñó a partir del histórico de publicaciones de la DGDA:

- **Convocatorias:** los años analizados (2021–2025) muestran que la DGDA publica las convocatorias EPA y EELL entre marzo y mayo. Comprobar cada 2 días en abril–mayo garantiza que el banner de aviso aparece en la home en menos de 48 horas tras la publicación oficial.
- **Resoluciones:** las resoluciones EPA y EELL del año en curso se publican habitualmente en noviembre–diciembre (a veces se cierran en enero del año siguiente, como ocurrió con EELL 2023). Comprobar cada 2 días en noviembre–diciembre garantiza que la `fecha_resolucion` se actualice en la BD —y el banner de aviso de la home desaparezca— en menos de 48 horas tras la publicación oficial.
- **Cada 4 días en meses laterales (marzo, junio, enero):** suficiente para detectar publicaciones adelantadas o tardías sin generar peticiones innecesarias a la API de BDNS.
- **No se ejecuta entre febrero y octubre (salvo marzo–junio):** la DGDA no ha publicado ni convocatorias ni resoluciones en esa franja en ninguno de los años analizados. El cron se puede ampliar fácilmente si eso cambia.

`check_bdns.py` ejecuta dos fases en cada llamada:

1. **Detección de resoluciones** (siempre): consulta `GET /bdnstrans/api/convocatorias/{num_convoc}` para cada convocatoria con `fecha_resolucion = NULL` del año actual. Si BDNS ya publica la fecha, la actualiza en la BD y el banner de la home desaparece automáticamente.
2. **Detección de nuevas convocatorias** (solo si faltan): busca nuevas convocatorias DGDA del año actual en la API BDNS por palabras clave del título. Si encuentra una nueva, la inserta con `fecha_resolucion = NULL`.

### Reintentos con backoff exponencial

Ambas fases consultan la API BDNS a través del helper interno `_get_bdns_con_retry(url, params)`, que aplica **3 intentos con backoff exponencial (2s → 4s → 8s)** ante errores transitorios. Cubre dos tipos de fallo:

- **Errores de red** (timeout, conexión rechazada, DNS): captura `requests.RequestException`.
- **Respuestas HTTP != 200** (5xx puntuales, 429 si saturamos): cuenta como intento fallido.

Justificación: con el calendario de cron actual (~75 ejecuciones al año concentradas en marzo–junio y noviembre–enero), un único fallo puntual de BDNS hacía perder hasta 4 días hasta el siguiente ciclo. Con 3 intentos y backoff, el cron absorbe blips de hasta ~15 s de duración. Si los 3 intentos fallan, la función devuelve `None` y el cron sigue con la siguiente convocatoria o abandona la búsqueda de forma controlada (loguea el error, no rompe el proceso).

El timeout por petición sigue siendo 30 s, así que el peor caso por convocatoria es `30s × 3 intentos + 2s + 4s = 96 s` (extremo improbable). En el caso medio (BDNS responde a la primera) la ejecución es idéntica a la versión anterior. Cubierto por `tests/test_check_bdns.py`.

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
git clone git@github.com:vcv-code/SubvDGDA.git
cd analisis-bdns-dgda
bash install.sh
```

**Prerequisitos:** Docker con `docker compose` v2 · Python 3.10+ · `python3-venv` (paquete aparte en Ubuntu/Debian: `sudo apt install python3.X-venv`) · openssl
**Plataforma:** Linux · macOS · WSL2 (Windows requiere Docker Desktop con integración WSL2)
**Descarga primera vez:** ~1,3 GB de imágenes Docker
**Espacio en disco:** ~1,5 GB total — desglose: backend ~360 MB · cron ~195 MB · MariaDB ~460 MB · Adminer ~170 MB · Nginx alpine ~90 MB · Mailpit ~50 MB · dataset + datos en BD ~50 MB · venv Python ~50 MB (opcional, solo para tests y scripts)

El script detecta instalaciones existentes y no sobreescribe datos. Si la BD ya tiene solicitudes, solo levanta los contenedores. Para reinstalar desde cero: `make reset-db`.

### Qué se descarga en la primera instalación

| Imagen | Uso | Tamaño aproximado |
|--------|-----|-------------------|
| `mariadb:11.8` | Base de datos | ~120 MB |
| `python:3.12-slim` | Backend y cron (compartida) | ~75 MB |
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
| Activar modo mantenimiento | `make mantenimiento-on` |
| Desactivar modo mantenimiento | `make mantenimiento-off` |
| Rebuild backend + reiniciar | `cd docker && docker compose down && docker compose up -d` (tras reinicio WSL2) |
| Ver logs nginx | `docker logs bdns_nginx --tail 50` |
| Ejecutar tests | `source venv/bin/activate && python -m pytest tests/ -q` |
| Lanzar cron manualmente | `docker exec bdns_cron python3 /app/scripts/check_bdns.py` |
| Rebuild del cron | `cd docker && docker compose up --build -d cron` |
| Copia de seguridad de la BD | `make backup` |
| Restaurar una copia | `make restore FILE=backups/backup_AAAAMMDD_HHMMSS.sql` |
| Abrir consola de la BD | `make shell-db` |

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

### Librerías del frontend (CDN con fallback local)

No hay bundler ni Node.js. Todo es HTML + CSS + JS vanilla servido por Nginx.

| Librería | Versión | Usado en | Para qué | Fallback |
|---|---|---|---|---|
| **Chart.js** | 4.4.0 | `index.html`, `estadisticas-epas.html`, `estadisticas-eell.html` | Gráficas de línea, barras y donut | `assets/vendor/chart.umd.min.js` |
| **Leaflet** (JS + CSS) | 1.9.4 | `exclusivo.html` | Mapa choropleth por CCAA con tiles de OpenStreetMap | `assets/vendor/leaflet.js` + `leaflet.css` |
| **Google Fonts (Inter)** | — | Todos los HTML | Tipografía: pesos 400, 600 y 700 | Sin fallback local (cae al `font-family` de sistema) |

**Cómo funciona el fallback de CDN:**

Los recursos cargados desde CDN llevan tres atributos:

- `integrity="sha384-..."`: el navegador verifica el hash antes de ejecutar/aplicar el recurso (SRI).
- `crossorigin="anonymous"`: requerido por SRI.
- `onerror="..."`: si el CDN no responde o el SRI falla, el handler crea dinámicamente un `<script>` o `<link>` apuntando a `/assets/vendor/`.

Las versiones locales en `frontend/assets/vendor/` se descargaron del mismo CDN y se verificaron comparando su hash SHA-384 con el `integrity` declarado en los HTMLs. La verificación criptográfica garantiza que los archivos locales son idénticos a los oficiales.

Google Fonts no tiene fallback porque la app degrada de forma aceptable sin la fuente Inter (se usa el `font-family` de sistema). Bundlear Inter localmente añadiría ~150 KB de WOFF2 al repositorio, no justificado para una degradación tan menor.

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

- **Formato:** el `combined` estándar más el tiempo de respuesta al final.

  ```text
  IP - - [fecha] "request" status bytes "referrer" "user-agent" tiempo_respuesta
  ```

  Se eligió el formato estándar en vez de uno propio para que lo entienda cualquier analizador sin configurarlo. Con GoAccess:

    ```bash
    goaccess access.log --log-format='%h %^[%d:%t %^] "%r" %s %b "%R" "%u" %T' \
                        --date-format='%d/%b/%Y' --time-format='%H:%M:%S' \
                        --num-tests=0
    ```

    Dos detalles que cuestan descubrir: `--log-format=COMBINED` **también**
    parsea estas líneas, pero descarta el tiempo de respuesta y el informe
    pierde la sección de páginas lentas sin que nada lo indique. Y
    `--num-tests=0` es imprescindible: un registro real siempre trae líneas
    que no encajan —bots, sondas, restos de un formato anterior— y sin él
    GoAccess aborta el informe entero al toparse con las primeras.

- **Destinos:**
  - `logs/nginx/access.log` — todas las peticiones HTTP y HTTPS
  - `logs/nginx/error.log` — nivel `warn` en adelante
- **El referrer solo aparece en las visitas que llegan de fuera.** Navegando dentro de la web sale siempre vacío (`"-"`), y no es un fallo: el sitio envía la cabecera `Referrer-Policy: no-referrer`, que le dice al navegador que no revele la procedencia. Eso no afecta a quien llega desde un buscador o desde otra web, porque ahí decide el sitio de origen. Si algún día interesara el recorrido *dentro* de la web, habría que pasar esa cabecera a `same-origin`, que lo permitiría sin revelar nada hacia fuera.
- **Los leen los dos generadores de informes**, y nadie más: `scripts/resumen_visitas.py` (resumen en español) y `scripts/informe_visitas.sh` (GoAccess). Ambos escriben en `informes/`, fuera de lo que Nginx sirve, porque el resultado contiene direcciones IP. El `access.log` que muestra el panel de administración es otro fichero distinto, `logs/app/access.log`, escrito por el backend.
- Se conservan **30 días** (`docker/cron/scripts/rotar_logs.py`) y lo que registran está declarado en `frontend/privacidad.html`, porque la IP es dato personal.

---

## Tests

- **Base de datos:** SQLite en memoria (`:memory:`) con `StaticPool` — todas las conexiones comparten la misma instancia, sin necesidad de MariaDB levantado
- **Fixtures en `conftest.py`:** `client` (crea/destruye tablas por test) y `db` (sesión para insertar datos)
- **Total:** ver [docs/tests.md](tests.md), que es la fuente única. Aquí no se
  repite el número a propósito: estaba duplicado y las dos copias se
  desincronizaron.

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

## Deuda técnica conocida — mejoras de BD

Estas mejoras se identificaron durante la auditoría final pero no se aplicaron porque requieren migraciones SQL sobre la BD existente. Quedan documentadas aquí para cuando se retome el proyecto.

### 1. `SmallInteger` → `Boolean` en campos lógicos

**Tablas afectadas:** `usuarios` (columnas `activo`, `email_verificado`)  
**Estado actual:** `Column(SmallInteger)` — funciona porque MariaDB guarda BOOLEAN como TINYINT(1), pero el tipo ORM no valida que solo entren `True/False`.  
**Mejora:** cambiar a `Column(Boolean)` en `backend/app/models.py`.  
**Migración necesaria:**

```sql
ALTER TABLE usuarios MODIFY activo TINYINT(1) NOT NULL DEFAULT 1;
ALTER TABLE usuarios MODIFY email_verificado TINYINT(1) NOT NULL DEFAULT 0;
```

No cambia datos, solo el tipo declarado. Compatible con el esquema existente.

### 2. Índices en tablas de tokens

**Tablas afectadas:** `refresh_tokens`, `reset_tokens`, `verificacion_tokens`  
**Columna sin índice:** `token` (se busca por este campo en cada login, logout y verificación)  
**Estado actual:** sin índice → MariaDB escanea todas las filas en cada búsqueda.  
**Impacto actual:** despreciable con pocos usuarios. Problemático a escala.  
**Mejora:** añadir índice único en `models.py`:

```python
# En cada modelo de token:
__table_args__ = (UniqueConstraint('token', name='uq_refresh_tokens_token'),)
```

**Migración necesaria:**

```sql
ALTER TABLE refresh_tokens ADD UNIQUE INDEX ix_refresh_token (token);
ALTER TABLE reset_tokens ADD UNIQUE INDEX ix_reset_token (token);
ALTER TABLE verificacion_tokens ADD UNIQUE INDEX ix_verificacion_token (token);
```

### 3. Duplicación de `cerrarSesion()` en tres archivos JS

**Archivos:** `js/navbar.js`, `js/privado.js`, `js/exclusivo.js`  
**Causa:** las páginas con navbar pre-renderizado (privado, exclusivo, admin) necesitaban su propio logout antes de que `navbar.js` se añadiese a esas páginas. Al añadirlo, se mantuvieron las implementaciones existentes para no romper nada.  
**Mejora:** crear `js/utils-auth.js` con la función compartida e importarla en los tres HTML antes de los scripts propios.  
**Riesgo si se hace:** bajo, pero requiere asegurarse de que los tres HTML cargan `utils-auth.js` antes de sus scripts propios.

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
| **Access token** | Token de corta duración (15 min) que autoriza cada petición a la API. |
| **Refresh token** | Token de larga duración (30 días) que permite obtener un nuevo access token sin volver a hacer login. |
| **ORM** | Object-Relational Mapper. Capa que traduce entre objetos Python y filas de la BD (aquí: SQLAlchemy). |
| **ASGI** | Interfaz estándar entre servidor web y aplicación Python asíncrona (aquí: uvicorn + FastAPI). |
| **Proxy inverso** | Servidor que recibe las peticiones del cliente y las redirige al servicio correcto internamente (aquí: Nginx → FastAPI). |
| **Rate limiting** | Límite de peticiones por IP en un intervalo de tiempo para frenar ataques de fuerza bruta. |
| **Honeypot** | Campo oculto en un formulario. Si llega relleno, es un bot — se simula éxito sin procesar el envío. |
| **CDN** | Red de distribución de contenidos. Aquí se usa para cargar Chart.js y Google Fonts desde servidores externos. |
| **Bearer token** | Formato de autenticación HTTP: `Authorization: Bearer <token>`. El cliente lo envía en cada petición protegida. |
| **HSTS** | HTTP Strict Transport Security. Cabecera que obliga al navegador a usar siempre HTTPS con este dominio. |
| **TLS** | Transport Layer Security. Protocolo de cifrado de la conexión HTTPS (versiones 1.2 y 1.3 activas). |
| **SQLite en memoria** | Base de datos temporal que vive en RAM durante los tests, sin tocar MariaDB. Rápida y aislada por test. |
| **StaticPool** | Configuración de SQLAlchemy para que SQLite en memoria comparta una única conexión entre threads (necesario en tests). |
