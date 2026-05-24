# Historial de implementación

Registro completo de funcionalidades desarrolladas por orden cronológico.

---

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
✔ backend FastAPI: modelos ORM, schemas Pydantic, primeros endpoints verificados
  · GET /convocatorias/ → lista las 8 convocatorias
  · GET /solicitudes/   → filtros por año, tipo, estado, CIF exacto, búsqueda parcial por nombre, CCAA, provincia y línea; ordenación server-side (`?orden=entidad-az|importe-desc|importe-asc`); respuesta paginada con `total` y `resultados`
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
✔ auditoría de seguridad backend — bcrypt rounds=12 explícito · email_verificado default=0 coherente · índices BD en estado/provincia/ccaa · TTL access token 15 min · anti-enumeración en registro (201 siempre) · 195 tests pasando (2 HTTPS dependen del CN del cert del entorno)
✔ navbar hamburguesa en ≤768px — menú desplegable con animación X, rayita ámbar en hover, cierre con Esc/click fuera/click en enlace; botón añadido en las 18 páginas HTML
✔ panel de admin restaurado — cabeceras rojas, badges de rol/estado, botones ghost, fondo pastel rojo
✔ zona privada restaurada — dos columnas, privado-card, fondo pastel morado, títulos verde oscuro
✔ sistema de color semántico — cuatro roles diferenciados:
  · Verde institucional (`#1A3429`, `#2DC26C`) — acciones de contenido, gráficas, estructura
  · Ámbar (`#D97706`) — acento interactivo: botón "Acceder", cards disponibles, avisos
  · Morado (`#7C3AED`) — zona privada (privado.html, exclusivo.html)
  · Rojo oscuro (`#7F1D1D`) — panel de administración
✔ paleta de fondos en home — alternancia verde/crema en 6 secciones:
  · Verde (`#DFF0E1`): hero, convocatorias, visión general
  · Crema (`#FAF4EE`): métricas, resoluciones, registro
  · Buscador y estadísticas: fondo crema (`fondo-crema`)
✔ imagen hero (`handcat.webp`) — mano acercándose a un gato callejero; descargada de Pixabay (licencia libre); alternativas disponibles en `assets/img/home/`
✔ gráficas unificadas — colores `#1A3429` / `#2DC26C` en home.js, estadisticas-epas.js y estadisticas-eell.js
✔ formatter manual de importes — separador de miles garantizado independiente del locale del navegador
✔ modal de entidad en buscador (`buscador.html`)
  · reemplaza la navegación a `entidad.html` por un modal inline sin salir del buscador
  · muestra nombre, CIF, CCAA (solo si disponible), total recibido, nº solicitudes e histórico con expediente
  · histórico ordenado de más reciente a más antiguo; importes con separador de miles garantizado
  · CCAA oculta automáticamente para EPAs (el dato no está disponible en asociaciones)
✔ navbar responsive en tres breakpoints (900 / 768 / 600 px)
  · texto del logo oculto en pantallas muy pequeñas; links y botón "Acceder" reducidos progresivamente
✔ retoques visuales rama 17 (home, buscador, estadísticas)
  · hero: imagen cubre altura del texto sin bandas verdes; centrado en desktop con max-width 1200px
  · aviso de convocatorias en ámbar más visible (#D97706)
  · tablas de convocatorias: cabecera verde, filas blancas, responsive correcto
  · KPI cards de estadísticas: números verdes centrados restaurados (revertido refactor Miyuki)
  · separador de miles en importes con formatter manual (independiente del locale del navegador)
  · URL de la DGDA en footer actualizada a dsca.gob.es en todos los ficheros HTML
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
✔ tests automáticos con pytest (223 funciones / 321 ejecuciones — smoke, funcionales, unitarios, seguridad, rendimiento, configuración; 305 pasan sin Docker; 16 requieren Docker+Nginx levantados para la suite completa)
  · — Pipeline de datos —
  · test_unificar_datasets.py (21): funciones de normalización del pipeline de datos
  · test_parser_epa2025.py (22): helpers y flujo completo del parser EPA 2025
  · — API pública —
  · test_smoke.py (3): arranque de la API y endpoint /health
  · test_convocatorias.py (3): endpoint /convocatorias/
  · test_solicitudes.py (16): filtros, paginación, búsqueda parcial, estructura, exportación CSV y campo tramo
  · test_estadisticas.py (24): /estadisticas/, /estadisticas/epas y /estadisticas/eell — estructura, cálculos, nuevos/recurrentes, concentración
  · test_agrupaciones.py (7): endpoint /agrupaciones/ — estructura, importes correctos, representante con nombre
  · test_avisos.py (6): endpoint /avisos/ — convocatorias pendientes de resolución
  · — Autenticación y acceso —
  · test_auth.py (10): registro, login, acceso con/sin token
  · test_verificacion_email.py (10): registro crea usuario no verificado, token en BD, email enviado, login bloqueado sin verificar, token válido activa cuenta, login tras verificar, token inválido/usado/expirado, reset activa email_verificado
  · test_refresh_token.py (7): refresh token — login devuelve token, renovación, rotación, token inválido, logout revoca, cambio contraseña revoca tokens
  · test_recuperar_password.py (9): recuperación contraseña — email existente/inexistente, token creado en BD, email enviado, reset válido, token inválido/usado/expirado, contraseña débil
  · test_privado.py (6): zona privada — cambiar contraseña y nombre/alias
  · test_admin.py (24): panel de administración — control de acceso (401/403), estado del sistema, CRUD de usuarios, eliminación con cascada de tokens, protección auto-edición, gestión de avisos, reactivar aviso, historial de resueltas, protección 409 con solicitudes, logs de acceso y de error
  · — Infraestructura —
  · test_logging.py (5): middleware de logging y configuración del logger
  · test_https_config.py (9): certificado SSL, configuración Nginx HTTPS y seguridad TLS
  · test_cache_headers.py (4): cabeceras Cache-Control en /convocatorias/ y /estadisticas/
  · test_rate_limiting.py (7): configuración de rate limiting en Nginx para /auth/login, /auth/registro y /auth/recuperar
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
  · `buscador.html` — buscador con filtros, tabla paginada, columna Año, badges de estado, botón CSV
  · `estadisticas-epas.html` — análisis de EPAs: importe medio, mediana, distribución, nuevos vs recurrentes, top beneficiarios
  · `estadisticas-eell.html` — análisis de EELL: % ayuntamientos con ayuda, top provincias, concentración, ranking CCAA
  · `recursos.html` — directorio de organizaciones de protección animal y campañas actuales (contenido estático)
  · `entidad.html` — ficha de entidad con historial, badges de estado y bloque de agrupación EELL
  · `login.html` / `registro.html` — autenticación con validación client-side
  · `privado.html` — zona exclusiva con control de acceso JWT
  · `admin.html` — panel de administración exclusivo para rol `admin`
✔ integración JS con la API REST: fetch a todos los endpoints, paginación, autenticación con Bearer token
✔ CORS configurable mediante variable de entorno `CORS_ORIGINS` en `docker/.env`
  · Desarrollo: `CORS_ORIGINS=*` (permite cualquier origen)
  · Producción: `CORS_ORIGINS=https://mi-dominio.com` (sin tocar código)
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
      1. Detección de resoluciones: para cada convocatoria del año con `fecha_resolucion=NULL`,
         consulta `GET /bdnstrans/api/convocatorias/{num_convoc}` en la API BDNS buscando el campo
         `fechaResolucion`. Si ya está publicada, actualiza la BD → el banner desaparece
         automáticamente sin intervención manual (BDNS suele actualizarse 1-2 días tras el BOE).
      2. Detección de nuevas convocatorias: si aún no se han registrado EELL y/o EPA del año
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
✔ rate limiting en Nginx para prevenir fuerza bruta, spam y abuso
  · zona `login:10m rate=10r/m` — 10 peticiones/minuto por IP en `/auth/login` (burst=5)
  · zona `registro:10m rate=5r/m` — 5 peticiones/minuto por IP en `/auth/registro` (burst=3)
  · zona `recuperar:10m rate=3r/m` — 3 peticiones/minuto por IP en `/auth/recuperar` (burst=2) — previene spam de emails de recuperación
  · todos con `limit_req_status 429`; Nginx rechaza sin llegar al backend
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
✔ medidas anti-bots y seguridad en registro
  · rate limiting `POST /auth/registro`: zona `registro:10m rate=5r/m`, `burst=3 nodelay`
  · honeypot: campo `sitio_web` oculto; si llega relleno → éxito falso sin crear cuenta
  · verificación de email al registrarse: tabla `verificacion_tokens`, `GET /auth/verificar`, bloqueo login con 403
  · reenvío de verificación `POST /auth/reenviar-verificacion`: invalida tokens anteriores, siempre 200
✔ zona privada ampliada `privado.html` (perfil) + `exclusivo.html` (contenido exclusivo: tabla resumen, resoluciones BOE)
✔ panel de administración reorganizado: Avisos primero, botón "← Volver al perfil" en banner
✔ páginas de error `404.html` y `50x.html` con imagen ilustrativa + `error_page` en Nginx
✔ aviso legal (`aviso-legal.html`), política de privacidad (`privacidad.html`) y sección de cookies
✔ footer actualizado con aviso legal y privacidad en todas las páginas; resoluciones BOE en home pública
✔ mejoras estadísticas y home gráficas home reordenadas, tasa éxito/fracaso, leyenda rosco con descripciones, tooltip desglose EPA/EELL, colores badges corregidos, KPIs centrados, top beneficiarios EPA con zoom y abreviaciones, rangos distribución importes ajustados a datos reales
✔ modal de conclusiones por gráfica botón "¿Qué conclusiones se sacan?" al pie de cada tarjeta de gráfica abre un modal con la gráfica como fondo tenue y texto interpretativo encima; compartido entre home, EPAs y EELL mediante `js/modal-grafica.js`; 9 gráficas cubiertas
✔ página Recursos renovada fondos de color por sección (verde/azul/ámbar/rosa), logos actualizados y normalizados, textos de descripción revisados
✔ cron — corrección `detectar_tipo` añadida palabra clave `"PROTECCI"` para detectar convocatorias EPA cuyo título en BDNS usa "protección animal" en lugar de "entidades privadas/asociaciones"; resolvía que la EPA 2026 se omitía silenciosamente
✔ cron — auto-detección de resoluciones nueva función `comprobar_resoluciones()` que en cada ejecución consulta `GET /bdnstrans/api/convocatorias/{num_convoc}` para cada convocatoria con `fecha_resolucion=NULL`; si BDNS ya publica la fecha, la actualiza en la BD → el banner de avisos desaparece automáticamente sin intervención manual
✔ resoluciones pendientes dinámicas en home `cargarPendientesResoluciones()` en `home.js` lee `/avisos/` e inyecta automáticamente entradas "Resolución pendiente de publicación" en las listas BOE de EELL y EPA; al resolverse, desaparecen solas
✔ logs de error del backend en panel de admin nuevo endpoint `GET /admin/logs/errores?n=N` que sirve `logs/app/error.log`; nueva sección en `admin.html` con borde rojo sutil; subtítulos aclaratorios en todas las secciones del panel; CSS del panel migrado de `<style>` inline a `styles.css`
✔ toggle visibilidad de contraseña botón con icono de ojo en todos los campos de contraseña (`login.html`, `registro.html`, `privado.html`, `reset-password.html`); lógica compartida en `js/utils.js`; al volver a pulsar se oculta de nuevo
✔ nombre/alias de usuario columna `nombre` (VARCHAR 100, nullable) en tabla `usuarios`; campo opcional en registro; `PUT /privado/cambiar-nombre` para actualizarlo desde el perfil; `GET /privado/perfil` lo expone; saludo en `privado.html` usa el nombre si existe; tabla de usuarios del panel admin muestra nombre + email cuando está definido
✔ Makefile con targets para el día a día: `start`, `stop`, `restart`, `build`, `reset-db`, `cargar`, `test`, `logs`, `backup`, `shell-db`, `mailpit`
✔ optimización de imágenes Docker: `backend/Dockerfile` migrado de `python:3.11` a `python:3.11-slim` (~700 MB menos); `pandas` eliminado de `requeriments.txt` (no se usaba)
✔ script de instalación automática (`install.sh`): comprueba prerequisitos por OS, crea `.env` con SECRET_KEY aleatoria, genera certificado SSL, añade dominio a `/etc/hosts` con confirmación, detecta instalaciones existentes y no sobreescribe datos, carga el dataset en primera instalación
✔ script de desinstalación (`uninstall.sh`): elimina contenedores, volúmenes (BD y datos), imagen Docker, certificado SSL, `.env`, `venv/` y la entrada de `/etc/hosts`; explica en lenguaje llano qué hace cada paso y pide confirmación antes de cada operación irreversible; aviso específico para WSL2
✔ revisión de accesibilidad WCAG 2.2 (Bloque A–C)
  · `--color-foco: #2E6B4F` (~5.1:1 en blanco) sustituye `--color-primario` en hover/focus interactivos (Issue 14)
  · `aria-hidden="true"` en manchas de color decorativas de las leyendas (rosco y barras)
  · colores primera leyenda del rosco corregidos para coincidir con el objeto `COLORES` de `home.js`
  · `aria-current="page"` en el enlace activo del navbar en todas las páginas (ya existía; verificado)
  · `title="Entidades Protectoras de Animales"` en el enlace EPAs del navbar en todas las páginas
  · etiquetas de sección `<h2>` en lugar de `<span>` en los 4 bloques del panel de administración
  · CSS `.admin-*` y `.tarjeta`/`.agrupacion-detalle` migrados de inline/ausentes a `styles.css` (Secciones 29 y 30)
✔ footer limpio en todas las páginas
  · eliminados enlaces "Documentación" y "Contacto" (rotos; sin página de destino real)
  · URL de GitHub corregida al repositorio real: `https://github.com/vcv-code/analisis-bdns-dgda`
  · estructura uniforme en las 18 páginas HTML: GitHub · Aviso legal · Privacidad
✔ reorganización de assets en subcarpetas (`img/`, `img/home/`, `img/logos/`, `wireframes/`, `guia-estilo/`)
  · todas las rutas actualizadas en los 19 HTML y en `styles.css`
  · referencia rota a `animales-login.png` corregida; extensión `gato-portada.jpeg` → `.jpg` corregida
✔ mejoras visuales del home (rama 18)
  · títulos de sección unificados a `1.75rem` en toda la página
  · paddings entre secciones revisados y uniformes (identificados con DevTools)
  · breakpoint del hero ampliado a `1024px` para evitar texto demasiado estrecho en pantallas medias
  · banners de avisos limitados al 70% del ancho (antes ocupaban el 100%)
  · columnas del hero cambiadas a 50/50 (antes 55/45)
  · subtítulo explicativo añadido a la sección "Convocatorias"
✔ páginas de error rediseñadas
  · `404.html`: estructura propia (`pagina-404__imagen` / `pagina-404__contenido`) para controlar el tamaño de la imagen independientemente del contenedor
  · `50x.html`: rutas convertidas a absolutas para funcionar desde cualquier URL de la API; nuevo diseño con frase simpática, imagen y botón "Reintentar"
  · clase base compartida `.pagina-error` extraída en `styles.css`; eliminados todos los inline styles
✔ CSS refactorizado
  · clases `.pagina-404`, `.pagina-50x` y base `.pagina-error` añadidas a `styles.css`
  · modificador `.auth-page--centrado` extraído del HTML a CSS
  · `.convocatorias-subtitulo` añadida para gestionar el margen desde CSS
✔ Mapa choropleth CCAA — mapa de calor interactivo con Leaflet 1.9.4
  · Movido de `estadisticas-eell.html` a `exclusivo.html` (contenido premium para usuarios registrados)
  · `estadisticas-eell.html` queda con 4 gráficas simétricas como `estadisticas-epas.html`
  · GeoJSON de alta resolución en `assets/geojson/ccaa.geojson` (19 CCAA, ~600 KB)
  · Paleta de tonos tierra (beige → caramelo → marrón oscuro); rojo para CCAA sin subvenciones
  · Hover: oscurece el color propio del polígono (función `oscurecer` en `mapa-ccaa.js`)
  · Escala de cuartiles reales (p25/p50/p75) redondeados a valores "bonitos"
  · Zoom con rueda, indicador de nivel en esquina, tile sin etiquetas (CartoDB nolabels)
  · Función extraída a `js/mapa-ccaa.js` independiente; acepta callback `onClickCCAA`
✔ Modal top 10 municipios (clic en CCAA del mapa)
  · Dos columnas: acumulado todos los años / último año con resolución (detectado automáticamente)
  · Agrupaciones EELL expandidas: llama a `GET /agrupaciones/{id_solic}` para mostrar municipios individuales en lugar del nombre de la agrupación
  · Subtítulo del mapa con rango de años dinámico desde `GET /estadisticas/`
  · CSS: `.modal-ccaa__*` en `styles.css`; cierra con Esc, clic fuera o botón ×
✔ CORS configurable por variable de entorno `CORS_ORIGINS` en `docker/.env`
  · Sin cambio de comportamiento en desarrollo (`*` por defecto)
  · En producción: cambiar a `CORS_ORIGINS=https://dominio.com` sin tocar código
✔ Renombrado `solicitudes.html` → `buscador.html`
  · URL del buscador cambiada a `/buscador.html` en todos los HTML, JS y CSS
  · `solicitudes.html` se conserva como legacy (cualquier enlace externo antiguo sigue funcionando)
  · `solicitudes.js` conserva su nombre (es el script, no la página)
✔ Mejoras visuales zona privada y exclusiva
  · Badges "ZONA PRIVADA" y "MI CUENTA" eliminados — redundantes con el contexto
  · Botones "Volver a mi perfil" y "← Volver al perfil" (admin): fondo semitransparente visible en reposo, hover más sólido
  · Card de acceso a contenido exclusivo: fondo verde suave, borde verde, sombra y flecha animada al hover
  · Cabeceras de tablas `resumen-tabla` actualizadas al verde oscuro institucional (`--nav-oscuro`)
  · Título "Área exclusiva" ampliado a 1.6rem; texto de descripción actualizado con contenido real
✔ Responsive `.grid-2` mejorado
  · Breakpoint de colapso de `.grid-2` subido de 600px a 768px (independiente de `.grid-3`)
  · Evita que dos tablas o tarjetas densas queden aplastadas en tablets y móviles grandes
  · `.grid-3` mantiene su breakpoint original (600px) sin cambios
✔ Ordenación server-side en el buscador
  · Nuevo parámetro `?orden=` en `GET /solicitudes/`: `entidad-az` (defecto), `importe-desc`, `importe-asc`
  · El backend aplica `ORDER BY` en SQL (subconsulta correlacionada sobre `concesiones.importe`) antes del `OFFSET`/`LIMIT`, garantizando orden correcto a través de todas las páginas
  · El frontend pasa `orden` al backend; cambiar el selector relanza la búsqueda desde página 1
  · El criterio de orden se persiste en la URL (excepto `entidad-az` por defecto)
  · Antes: ordenación client-side sobre los 50 resultados de la página actual (bug)
✔ Distribución de importes EPA corregida
  · Eliminado el rango `> 10.000 €`: verificado en BD que el importe máximo real es exactamente 10.000 €
  · Los 8 registros con importe = 10.000 € reclasificados al rango `8.000–10.000 €` (ajuste del límite superior a 10.001 en el backend)
  · Gráfico en `estadisticas-epas.html` muestra ahora 5 barras sin la barra fantasma
✔ Reordenación de gráficas en Home
  · Fila 1: Evolución del importe por año (línea) + EPA vs EELL por año (barras agrupadas)
  · Fila 2: Distribución por estado (rosco) + Tasa de éxito/fracaso (KPI)
  · Antes: línea + rosco arriba, barras + KPI abajo
✔ Modal de conclusiones — contenido HTML completo
  · 9 modales con textos analíticos reales de varios párrafos escritos por la autora
  · Renderizado con `innerHTML` (soporte de `<p>`, `<ul>`, `<li>`, `<a>`)
  · Título muestra "Gráfica — Conclusiones" con el sufijo en gris; etiqueta CONCLUSIONES separada eliminada
  · Modal de Evolución incluye sección de fuentes con 3 enlaces externos verificados
  · Panel ampliado a 720px / 82vh; fuente a 1rem
✔ Navbar — fuente unificada y responsive mejorado
  · Todos los enlaces del navbar a 1.15rem (antes 0.95rem); Mi perfil y Cerrar sesión al mismo tamaño
  · Nuevo breakpoint 769–1024px reduce a 1rem para evitar solapamiento en pantallas medianas
✔ Auditoría responsive móvil — 8 correcciones
  · Hamburguesa: navbar.js añadido a privado.html, exclusivo.html y admin.html — no tenía event listeners tras login
  · Footer: links centrados en móvil (align-items: center + justify-content: center)
  · Tabla buscador: valores siempre alineados a la derecha en modo card (text-align: right + align-items: flex-start)
  · Tablas admin: overflow-x: auto en móvil (overflow: hidden del panel lo bloqueaba)
  · Tabla resumen exclusivo: table-layout: auto + min-width: 520px en móvil para forzar scroll horizontal
  · Badge DISPONIBLE/PRÓXIMAMENTE: padding-top extra en móvil para no solapar el primer elemento
  · Filtros buscador: text-align: left explícito en móvil; botones centrados
  · Modal top municipios CCAA: una columna en ≤768px (antes dos columnas muy estrechas)
✔ Navbar — mejoras de navegación y responsive
  · Link "Exclusivo" añadido: navbar.js lo inyecta al iniciar sesión; pre-renderizado en privado.html, exclusivo.html y admin.html
  · Link "Mi perfil" añadido en exclusivo.html y privado.html con aria-current="page" cuando es la página activa
  · Breakpoint hamburguesa subido de 768px a 900px — necesario por el aumento de items en navbar
  · Rango 901–1024px mantiene font-size 1rem; >1024px usa 1.15rem
  · navbar__user-controls: gap cambiado a var(--espacio-lg) = 32px para igualar separación con otros links; align-items: baseline para alineación tipográfica correcta
  · Navbar z-index 1000→1200 — los controles de Leaflet (z-index 1000 por defecto) tapaban el menú
  · Hamburguesa z-index 999→1001 — por encima de controles Leaflet
  · Botón "Cerrar sesión" en hamburguesa: font-size 1rem (antes 0.85rem), separador entre "Mi perfil" y "Exclusivo"
  · Modal top municipios: columna única en ≤768px
✔ Mapa de calor CCAA — interacción táctil completa
  · Un toque: muestra caja de info centrada con nombre, importe y concesiones (reemplaza tooltip de Leaflet)
  · Doble toque: abre modal top municipios (doubleClickZoom deshabilitado en touch)
  · Tooltips de Leaflet desenlazados en móvil (unbindTooltip) — sustituidos por div propio `.mapa-info-central` con z-index 1200
  · Hint contextual sobre el mapa: texto inicial → cambia a "Doble toque para ver el top" al tocar → vuelve tras 8s
  · Auto-cierre del info box tras 8 segundos sin doble toque
  · Tooltip pane de Leaflet subido a z-index 1050 via JS (encima de controles Leaflet)
  · fitBounds sobre el GeoJSON en móvil para mostrar España completa en el viewport
  · Leyenda reducida en móvil: font-size 0.68rem, padding 6px 8px, cuadros 10px
  · Hint text `.mapa-ccaa-hint`: display none en desktop, visible en ≤768px en cursiva gris
  · Eliminado subtítulo "Escala de quintiles sobre importe total concedido"
✔ Modal conclusiones — fixes de calidad
  · Título construido con DOM API (textContent + appendChild) en lugar de innerHTML para evitar XSS
  · Cuerpo con flex: 1 + min-height: 0 para que el scroll interno funcione correctamente en modales largos
  · Modal de top municipios: columna única en ≤768px
✔ Error-box en estadísticas EPAs y EELL ante fallos de red
  · El bloque `error-box` ya se mostraba en errores HTTP, pero los errores de red (fetch lanzando excepción) dejaban la página en blanco con solo `console.error`
  · El catch ahora muestra el error-box con mensaje fallback ("No se pudo conectar con el servidor") si no había uno previo del backend
✔ Saludo neutro y visibilidad de rol en zona privada
  · Saludo cambiado de "Bienvenida" (femenino) a "Hola," (neutro) — compatible con cualquier género
  · Rol mostrado solo si es `admin` ("Rol: administrador"); usuarios registrados ven solo la fecha de alta
✔ Accesibilidad — scope en cabeceras de tabla
  · `scope="col"` añadido en todas las `<th>` de `index.html` (tablas de convocatorias), `entidad.html` (historial y agrupación) y la tabla dinámica de `exclusivo.js`
  · Completa WCAG 1.3.1 (relaciones en tablas) para lectores de pantalla
✔ Nombre de archivo dinámico en la exportación CSV del buscador
  · El botón "↓ Descargar CSV" genera el nombre a partir de los filtros activos: `solicitudes_[tipo]_[anio]_[estado]_[ccaa].csv` (ej: `solicitudes_epa_2024_concedida.csv`); sin filtros → `solicitudes.csv`
  · Cambiado de `window.location.href` a `fetch + Blob + <a download>` para poder controlar el nombre sin tocar el backend
  · Mejora añadida: si el backend devuelve 400 (demasiados resultados), el mensaje de error ahora aparece en la tabla en lugar de mostrar el JSON en blanco en el navegador
✔ Enlace "Ver página completa →" en el modal de entidad del buscador
  · Pie del modal (`modal-pie`) con enlace a `entidad.html?cif=...` en pestaña nueva
  · `modal-entidad.js` actualiza el `href` con el CIF codificado al abrir el modal
  · CSS `.modal-enlace-pagina` añadido a `styles.css`; `.modal-pie` ya existía pero no estaba conectado al HTML
  · `entidad.html` deja de ser una página huérfana — accesible desde la UI sin necesidad de construir la URL manualmente
✔ Reorganización de imágenes de `assets/img/`
  · `gato500.webp` y `perro-gato.png` movidos de `assets/img/home/` a `assets/img/`
  · `home/` queda exclusivamente con las alternativas del hero (`handcat.webp` y reservas)
  · Referencias actualizadas en `50x.html`, `login.html` y `registro.html`
  · `onerror` circular en `registro.html` corregido (apuntaba a sí misma en el fallback)
✔ Correcciones de accesibilidad en `privado.html`
  · `role="status"` y `aria-live="polite"` añadidos a los mensajes de éxito `#cambiar-nombre-ok` y `#cambiar-password-ok` — antes eran `<p>` sin semántica ARIA
✔ Limpieza de código muerto y cabeceras JSDoc
  · `obtenerToken()` eliminada de `exclusivo.js` — función definida pero nunca llamada; la renovación de token ya la gestiona `intentarRenovarToken()`
  · Cabeceras JSDoc añadidas a los 4 archivos JS que carecían de ellas: `navbar.js`, `utils.js`, `recuperar-password.js`, `reset-password.js`
✔ Auditoría de código — fixes aplicados tras revisión exhaustiva
  · Backend: `buscar` con `max_length=200` y `limite` con `ge=1, le=500` — un usuario podía pedir `?limite=999999` y forzar una consulta de un millón de filas
  · Backend: `GET /solicitudes/export` limitado a 5.000 resultados — sin filtros intentaba exportar los ~6.400 registros completos en memoria
  · Nginx: rate limiting en `POST /auth/recuperar` (3 req/min) — sin límite era posible mandar emails de recuperación en bucle a cualquier usuario
  · Backend: funciones SMTP envueltas en try/except con `logger.error` (antes podían silenciar errores de envío)
  · Backend: login fallido registra `logger.warning` con el email (auditoría de intentos de acceso)
  · Test: `test_epas_distribucion_tiene_todos_los_rangos` actualizado de 6 a 5 rangos (coherente con corrección de datos)
  · README: páginas utilitarias `404.html`, `50x.html`, `aviso-legal.html` y `privacidad.html` añadidas a la lista
  · SRI (Subresource Integrity): atributos `integrity` y `crossorigin` añadidos a los 5 recursos CDN externos — Chart.js (3 páginas) y Leaflet JS + CSS (exclusivo.html); si el CDN fuese comprometido el navegador rechaza el recurso en lugar de ejecutarlo
  · Buscador — doble entrada en historial al llegar desde enlace de convocatoria: `history.pushState` cambiado a `history.replaceState` en `sincronizarUrl()`; antes había que pulsar Atrás dos veces para volver a Home
✔ Enlaces a las bases reguladoras en la sección "Convocatorias" de la home
  · Bajo la tabla EPA: enlaces a las bases reguladoras de 2021 (BOE-A-2021-16021) y a la modificación de 2024 publicada por la DGDA
  · Bajo la tabla EELL: enlace a las bases reguladoras de 2023 publicadas por la DGDA
  · Reutilizada la clase `.convocatorias-nota` ya existente (mismo tamaño y color discreto que el asterisco del período subvencionable)
  · Nueva regla CSS `.convocatorias-nota a` con color azul institucional (`--color-azul`) coherente con el enlace "Volver al inicio" de las páginas legales, subrayado por convención web (se quita en hover)
  · Atributos `target="_blank" rel="noopener noreferrer"` y `aria-label` descriptivo en cada enlace (incluye el formato del documento y el origen — BOE o DGDA)
