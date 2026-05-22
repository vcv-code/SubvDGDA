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

El backend (`bdns_api`, puerto 8000) **no expone ningún puerto al host** — solo es accesible desde dentro de la red Docker interna. Nginx actúa como única puerta de entrada.

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
FROM python:3.11-slim          # imagen mínima: ~75 MB vs ~900 MB de la completa

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

El cron usa `python:3.12-slim` (versión independiente del backend) y solo instala lo que necesita. Sin imagen base compartida: si una imagen falla, la otra sigue funcionando.

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

```text
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

### Zona privada (rol: `registrado`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/privado/perfil` | Datos del usuario en sesión (`id_usuario`, `email`, `rol`, `nombre`) |
| `PUT` | `/privado/cambiar-nombre` | Actualizar alias |
| `PUT` | `/privado/cambiar-contrasena` | Cambiar contraseña · revoca todos los refresh tokens |
| `GET` | `/privado/resumen-exclusivo` | Datos para el mapa choropleth CCAA |
| `GET` | `/privado/resumen-tabla` | Tabla resumen de solicitudes por convocatoria |

### Panel de administración (rol: `admin`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/admin/estado` | Estado del sistema: número de usuarios, solicitudes y convocatorias |
| `GET` | `/admin/usuarios` | Lista completa de usuarios |
| `PATCH` | `/admin/usuarios/{id}/rol` | Cambiar rol (`registrado` ↔ `admin`) |
| `PATCH` | `/admin/usuarios/{id}/activo` | Activar o desactivar cuenta |
| `DELETE` | `/admin/usuarios/{id}` | Eliminar usuario |
| `GET` | `/admin/avisos` | Lista de avisos activos |
| `PATCH` | `/admin/avisos/{id}/desactivar` | Desactivar aviso |
| `PATCH` | `/admin/avisos/{id}/reactivar` | Reactivar aviso |
| `DELETE` | `/admin/avisos/{id}` | Eliminar convocatoria sin resolución (409 si tiene solicitudes) |
| `GET` | `/admin/logs` | Últimas N líneas del log de acceso |
| `GET` | `/admin/logs/errores` | Últimas N líneas del log de errores |

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
| Honeypot en registro | Campo `sitio_web` oculto: si llega relleno, se devuelve éxito falso sin crear cuenta |
| Verificación de email | Las cuentas nuevas tienen `email_verificado=0`; el login bloquea con 403 hasta verificar |
| Reenvío de verificación | `POST /auth/reenviar-verificacion` invalida tokens anteriores y envía nuevo enlace; siempre devuelve 200 |
| HTTPS | Certificado autofirmado, TLS 1.2 y 1.3 únicamente |
| Cabeceras de seguridad | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `HSTS: max-age=31536000` |
| Panel de admin | Solo accesible para usuarios con `rol = 'admin'` |
| Sesión activa en login/registro | Si hay token en `localStorage`, `login.html` y `registro.html` redirigen automáticamente a `privado.html` sin mostrar el formulario |
| Navbar en páginas públicas | `js/navbar.js` detecta el token en `localStorage` y reemplaza el botón "Acceder" por "Mi perfil" + "Cerrar sesión" sin necesidad de petición al servidor |
| SRI en recursos CDN | Atributos `integrity="sha384-..."` y `crossorigin="anonymous"` en los 5 recursos externos (Chart.js ×3, Leaflet JS, Leaflet CSS); el navegador verifica el hash antes de ejecutar/aplicar el recurso |

---

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

### Criterio de selección de frecuencias

La frecuencia se diseñó a partir del histórico de publicaciones de la DGDA:

- **Convocatorias:** los años analizados (2021–2025) muestran que la DGDA publica las convocatorias EPA y EELL entre marzo y mayo. Comprobar cada 2 días en abril–mayo garantiza que el banner de aviso aparece en la home en menos de 48 horas tras la publicación oficial.
- **Resoluciones:** se publican con más variabilidad (normalmente en noviembre–diciembre para EPA y EELL del mismo año). El cron las comprueba en cada ejecución —independientemente del mes— porque la fase de detección de resoluciones siempre corre.
- **Cada 4 días fuera de temporada (marzo y junio):** suficiente para detectar publicaciones tardías o adelantadas sin generar peticiones innecesarias a la API de BDNS.
- **No se comprueba julio–febrero:** la DGDA no ha publicado convocatorias en esos meses en ninguno de los años analizados. El cron se puede ampliar fácilmente si eso cambia.

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
| **Honeypot** | Campo oculto en un formulario. Si llega relleno, es un bot — se simula éxito sin crear la cuenta. |
| **CDN** | Red de distribución de contenidos. Aquí se usa para cargar Chart.js y Google Fonts desde servidores externos. |
| **Bearer token** | Formato de autenticación HTTP: `Authorization: Bearer <token>`. El cliente lo envía en cada petición protegida. |
| **HSTS** | HTTP Strict Transport Security. Cabecera que obliga al navegador a usar siempre HTTPS con este dominio. |
| **TLS** | Transport Layer Security. Protocolo de cifrado de la conexión HTTPS (versiones 1.2 y 1.3 activas). |
| **SQLite en memoria** | Base de datos temporal que vive en RAM durante los tests, sin tocar MariaDB. Rápida y aislada por test. |
| **StaticPool** | Configuración de SQLAlchemy para que SQLite en memoria comparta una única conexión entre threads (necesario en tests). |
