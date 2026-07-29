# Historial de implementación

Registro completo de funcionalidades desarrolladas por orden cronológico.

---

✔ parsing XML BOE (EPAs 2021–2025)
✔ parsing PDF (EELL 2023–2024)
✔ parsing XML BOE + Excel manual (EELL 2025)
✔ limpieza y normalización de estados
✔ dataset unificado (6396 registros · EPA: 3351 · EELL: 3045)
✔ fix deduplicación cross-year (clave tipo + expediente + anio)
✔ campo provincia y ccaa para EELL (derivados del CIF, con overrides manuales)
✔ campo periodo_meses (6 para EPA 2023/2024, 12 para el resto)
✔ agrupaciones EELL 2025: campos es_agrupacion y municipios_agrupacion en todo el pipeline
✔ modelo físico de base de datos (MariaDB, `docker/init/modelo-fisico.sql`)
✔ entorno Docker (docker-compose con MariaDB + FastAPI)
✔ script de carga del dataset a la base de datos (`scripts/data_processing/cargar_dataset.py`)
✔ primera carga completa verificada (8 convocatorias, 3103 beneficiarios, 6396 solicitudes, 2623 concesiones, 13 agrupaciones, 72 miembros)
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
  · KPI cards de estadísticas: números verdes centrados restaurados (refactor revertido)
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
  · URL de GitHub corregida al repositorio real: `https://github.com/vcv-code/SubvDGDA`
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
✔ Mecanismos de contingencia ante fallos externos
  · Calendario del cron extendido a noviembre–enero (publicación de resoluciones): cada 2 días en noviembre y diciembre, cada 4 días en enero — antes solo cubría marzo–junio
  · Helper `_get_bdns_con_retry` en `check_bdns.py` con backoff exponencial 2 s → 4 s → 8 s; tras 3 fallos consecutivos registra el error y reintenta en la siguiente ejecución programada
  · Healthchecks Docker (curl) en `db`, `backend`, `nginx` y `mailpit` con `restart: unless-stopped`; backend espera `service_healthy` de MariaDB antes de arrancar
  · Fallback local de CDN: `frontend/assets/vendor/` con `chart.umd.min.js`, `leaflet.js` y `leaflet.css` verificados por hash SHA-384 contra el `integrity` del CDN; atributo `onerror` carga la copia local si `cdn.jsdelivr.net` o `unpkg.com` no responden
  · Tests añadidos: `test_scheduler.py` (119 casos parametrizados sobre calendario y ventana horaria) y `test_check_bdns.py` (helper de retry)
✔ Robustez del script de instalación
  · Timeout de espera de MariaDB ampliado de 60 s a 180 s + opción interactiva de extender 60 s más antes de abortar (WSL2 lento puede tardar 2-3 min en crear el datadir)
  · Convocatorias 2026 (EPA y EELL) insertadas también en reinstalaciones, no solo en la primera instalación — necesarias para los avisos de la home
  · Detección explícita de `python3-venv` y `ensurepip` en la Fase 2 con mensaje claro indicando el paquete a instalar (`sudo apt install python3.X-venv`)
  · Si la usuaria responde "N" a crear el venv pero la BD está vacía, el script crea igualmente un venv mínimo en la fase de carga porque `cargar_dataset.py` necesita PyMySQL
✔ LICENSE dual y footer
  · `LICENSE` en raíz con doble régimen: código "All Rights Reserved" + contenido (memoria, documentación, capturas) bajo Creative Commons BY-NC-ND 4.0
  · Footer de los 19 HTMLs actualizado con la mención dual y enlace a `LICENSE`
✔ Makefile — backup y restore de BD
  · `make backup`: genera `backup_YYYYMMDD_HHMMSS.sql` con `mariadb-dump` desde el contenedor
  · `make restore FILE=<archivo>`: restaura un dump previo, útil entre reinstalaciones
✔ Manuales reescritos y consolidados
  · `manuales/manual-usuario.md` y `manuales/manual-instalacion.md` reorganizados con TL;DR, requisitos previos coherentes con el script (incluye `python3-venv` y aviso Windows/Linux/macOS), verificación post-instalación con queries SQL, comandos make, modo desarrollo, instalación detallada en WSL2 (dos2unix, carpeta doble) y resolución de problemas
  · Bloques markdown con lenguaje (`text`, `bash`) en todos los fences; blockquotes corregidos
  · Tabla de espacio en disco actualizada con el desglose real por imagen Docker (~1,5 GB total)
✔ Unificación de versiones de Python, pin de MariaDB y arreglo del venv en `install.sh`
  · Python unificado a `3.12-slim` en backend y cron (antes el backend iba en 3.11): elimina la deriva, las librerías compartidas (`PyMySQL`, `bcrypt`) se comportan igual en ambos contenedores
  · MariaDB pineada a `mariadb:11.8` (antes `mariadb:11` flotante): reproducibilidad sin riesgo, la BD ya estaba en 11.8.x; no se eligió `11.4` LTS porque MariaDB no permite arrancar una menor sobre datos creados por una mayor (exigiría borrar el volumen y recargar el dataset)
  · `install.sh`: el venv ahora instala también `backend/requirements.txt` en los dos bloques (primera instalación y fase 7 opcional). Antes `make test` fallaba de fábrica por `ModuleNotFoundError: No module named 'pytest'`. Tamaño del venv actualizado en mensajes y manual: ~50 MB → ~175 MB
  · `docs/referencia-tecnica.md`: nueva sección "Versiones de las tecnologías y por qué" con tabla razonada de cada elección y los principios de selección (tamaño primero, pin a versión menor, coherencia entre servicios, reciente sin necesidad de LTS); nueva subsección "Recrear contenedores cuando algo va mal" con tabla de patrones (`down && up` para bind mounts rotos tras reinicio WSL2 vs `--force-recreate` para contenedores atascados pese a `make restart`)
  · `manuales/manual-instalacion.md`: entrada de troubleshooting "Los tests fallan" actualizada para incluir `backend/requirements.txt`; nueva entrada de troubleshooting para `--force-recreate`; comando de creación manual del venv en la sección "Ejecutar los tests" actualizado a `pip install -r requeriments.txt -r backend/requirements.txt`; tamaño del venv en desinstalación actualizado a ~175 MB
  · Verificado: 321 tests pasando con la nueva configuración (Python 3.12.13 en backend, MariaDB 11.8.8)
✔ Integración real de los snapshots BDNS en la carga del dataset
  · Hasta ahora los JSON de `data/raw/convBDNS/` eran un callejón sin salida: `bdns_client.py` los escribía pero ningún script los leía. Las fechas se copiaban a mano al diccionario `_FECHAS` de `cargar_dataset.py` y `num_convoc` quedaba siempre `NULL` para las 8 convocatorias históricas
  · Nuevo módulo `scripts/data_processing/bdns_lookup.py` que lee el snapshot más reciente de cada patrón (`*_convocatorias_proteccion_animal.json`, `*_convocatorias_colonias_felinas.json`), detecta el tipo (`epa` / `eell`) por palabras clave del título (lógica espejo de `check_bdns.py:detectar_tipo()`) y devuelve un índice `{(anio, tipo): {num_convoc, fecha_convocatoria, titulo, bdns_id}}`
  · `cargar_dataset.py:cargar_convocatorias()` ahora prefiere BDNS como fuente: `num_convoc`, `titulo_convoc` y `fecha_convocatoria` salen del índice BDNS si existe la entrada; si no, fallback a `_TITULO` y `_FECHAS` hardcodeados (para años futuros aún no publicados en BDNS). `fecha_resolucion` sigue saliendo de `_FECHAS` porque los snapshots de búsqueda BDNS no incluyen resolución; el cron la rellena automáticamente cuando se publica
  · Validación cruzada: si la fecha BDNS difiere de la hardcodeada, se imprime un aviso en el log de la carga (no falla — la fuente oficial gana — pero queda registro para auditoría). Verificado en la carga actual: 0 discrepancias, las 8 fechas hardcodeadas coinciden exactamente con BDNS
  · Política de fichero: se usa el snapshot más reciente que cumpla el patrón (orden alfabético = orden cronológico por el prefijo `YYYY-MM-DD_`). Re-ejecutar `bdns_client.py` crea un fichero nuevo al lado del anterior sin pisarlo; el siguiente install lo recoge automáticamente
  · `docs/pipeline-datos.md`: diagrama del pipeline ampliado para mencionar el lookup BDNS en el paso 1; nueva subsección "Integración con BDNS en la carga (`bdns_lookup.py`)" explicando el módulo
  · Verificado: tras `make reset-db` + `bash install.sh`, las 8 convocatorias históricas se cargan con `num_convoc` poblado desde BDNS (591891, 645245, 696633, 696605, 768855, 765190, 830399, 823367); las 2 de 2026 mantienen su `num_convoc` desde `install.sh`; total 10 convocatorias con `num_convoc IS NOT NULL`; 321 tests pasando
  · `README.md`: nueva línea sobre `bdns_lookup.py` paralela a la de `bdns_client.py` en la sección BDNS de "Scripts de datos"
  · Limpieza colateral: `lxml==6.0.2` eliminado de `requeriments.txt` (verificado por grep: 0 imports en `scripts/` y `backend/`); README y `pipeline-datos.md` aclaran que `eell_2025_beneficiarias.xlsx` se transcribió manualmente de las imágenes del BOE (es entrada manual del pipeline, no artefacto generado)
✔ Buscador: fix del filtro por dígitos y limpieza de puntos finales en nombres de entidad
  · Bug detectado en el buscador: al escribir "4" (entidad "4 GATOS Y TU" de Zaragoza, o las que empiezan por "7 I 7", "4 PETJADES…") el filtro no aplicaba. Causa en `backend/app/routers/solicitudes.py:_palabras_clave()`: tiraba todo token de longitud ≤ 2, incluidos los dígitos sueltos
  · Fix: cambiar la condición a `len(p) > 2 or p.isdigit()`. Las stopwords y los tokens cortos no numéricos (`tu`, `ti`, `lo`) se siguen filtrando; los dígitos pasan. Verificado en vivo: buscar "4" devuelve 36 resultados (antes 2155, devolvía todo) y "4 GATOS Y TU" encuentra la entidad correcta
  · Limpieza de puntos finales tipográficos en `beneficiarios.nombre`: el BOE termina con `.` el 80 % de los nombres (2 478 / 3 103) como convención de tabla. Cero nombres con punto solo en medio (verificado por SQL). `unificar_datasets.py:limpiar_entidad()` ahora hace `.rstrip('.').strip()` para que el siguiente install limpio nunca tenga puntos. El `dataset_unificado.json` se regenera con la nueva normalización y la BD actual se limpia con `UPDATE beneficiarios SET nombre = TRIM(TRAILING '.' FROM nombre)` (2 478 filas actualizadas, 0 restantes)
  · Empty state del buscador mejorado: el bloque "tabla-vacia" pasa de una línea de texto gris a un estado vacío con icono SVG de lupa, título destacado ("No se han encontrado solicitudes"), sugerencia ("Prueba a cambiar los filtros o a buscar con otras palabras.") y CTA "Limpiar filtros" que reutiliza `limpiarFiltros()`. Aplicado a `buscador.html` y `solicitudes.html` (alias legacy). Nuevas clases `.estado-vacio`, `.estado-vacio__icono`, `.estado-vacio__titulo`, `.estado-vacio__sub` en `styles.css`
  · Bug pre-existente expuesto y arreglado: `mostrarSinResultados()` en `solicitudes.js` no abría el contenedor padre `#resultados-card` (que `ocultarTodosEstados()` esconde), por lo que el empty state quedaba invisible aunque su `display` estuviera abierto. Añadido `if (resultadosCard) resultadosCard.style.display = '';` en la función
  · Escapes Unicode rotos en nombres de entidad: 6 beneficiarios EELL/EPA tenían `uXXXX` sin barra invertida (`PUu00C7OL`, `CADAQUu00C9S`, `MAu00C7ANET`, `ANIu00D1ON`, `VALLu00C8S`, `ASSOCIACIu00D3`) por una pérdida del backslash en algún paso del parseo PDF/XML. Nueva función `_arreglar_escapes_unicode()` en `unificar_datasets.py` que convierte `uXXXX` → carácter Unicode solo dentro de U+00A0–U+00FF (Latin-1 Suplemento), evitando falsos positivos como `UBEDA` o `CIUDADANA`. `limpiar_entidad()` la aplica tras el `rstrip('.')`. La BD actual se actualiza con `UPDATE beneficiarios SET nombre = REPLACE(nombre, 'u00C7', 'Ç')` etc. para los 5 codepoints implicados
  · Verificación final de calidad del nombre de beneficiario tras los fixes: 0 con punto final, 0 con `u00XX`, 0 con espacios dobles, 0 con leading/trailing space, 0 con HTML entities, 0 con coma o punto y coma final, 0 con paréntesis sin cerrar, 0 nombres vacíos. Los 4 matches restantes de `u[0-9A-Fa-f]{4}` (UBEDA, UCEDA, CIUDADANA × 2) son texto legítimo, fuera del rango Latin-1
  · `docs/pipeline-datos.md`: dos nuevas subsecciones ("Punto final tipográfico en nombres de entidad" y "Escapes Unicode rotos en nombres de entidad") dentro de "Problemas del proceso de unificación"
  · Buscador extendido a `num_expediente`: el filtro `buscar` del endpoint `GET /solicitudes/` ahora aplica `OR` entre `Beneficiario.nombre.ilike(...)` y `Solicitud.num_expediente.ilike(...)` para tokens de longitud ≥ 4. Permite localizar una solicitud por su número del BOE (`EXP/100024`, `2024B651`, `100024`) o por nombre desde el mismo campo. Tokens cortos como "4" o "20" siguen filtrando solo por nombre para evitar explosión (un dígito casa con el 60 % de los expedientes). Mismo cambio aplicado al endpoint de exportación CSV. Placeholder del input en `buscador.html`/`solicitudes.html` actualizado a "Nombre o nº de expediente..."
  · `docs/pipeline-datos.md`: nueva subsección "Formatos del `num_expediente` por año y tipo" en "Procesamiento de datos" con la tabla completa (EPA 2021 invierte año al final, 2022 lo lleva al inicio, 2023+ es `año+B+NNN`; EELL es `EXP+año/NNNNNN` con 23 casos 2025 sin año). Decisión documentada: no se unifican los formatos para preservar la trazabilidad con el BOE
  · Wrap line del símbolo € en celdas estrechas: el espacio normal entre cifra y € permitía al navegador partir la línea ("35.520,80" arriba y "€" abajo) cuando la columna quedaba justa. Sustituido por **non-breaking space (U+00A0)** en los 7 sitios donde se formatea el importe en JS: `solicitudes.js`, `modal-entidad.js`, `entidad.js` (2 ocurrencias), `estadisticas-epas.js`, `estadisticas-eell.js`, `mapa-ccaa.js`, `exclusivo.js`. Ahora la cifra y la unidad siempre van juntas
  · 321 tests pasando tras todos los cambios
✔ Botón "volver arriba" y autoría única
  · Nuevo componente compartido `js/scroll-arriba.js` + clase `.btn-subir` en `styles.css`: botón flotante fijo en la esquina inferior derecha que aparece al superar 600px de scroll y vuelve al inicio (`window.scrollTo({ top: 0 })`, suavizado por el `scroll-behavior: smooth` del `<html>`). Cargado en las 12 páginas con navbar, justo después de `navbar.js`; en las páginas cortas no llega a mostrarse. Listener de scroll `passive` agrupado en `requestAnimationFrame`. Accesibilidad: `aria-label`, `:focus-visible` y respeto de `prefers-reduced-motion`
  · `z-index: 1100` para quedar por debajo de modales (2000/9999) y navbar (1200) sin taparlos
  · Documentado en `frontend/docs/especificaciones-frontend.md` (nueva sección 4.10) y `frontend/docs/patrones.md` (componentes compartidos y orden de scripts)
  · Autoría única: retirada la coautoría de los footers (21 HTML), `LICENSE`, `README.md` y este historial; ajustados los plurales del `LICENSE` a singular femenino (`la titular`)
✔ Formulario de contacto y actualización del repositorio
  · Nuevo endpoint `POST /contacto/` (`backend/app/routers/contacto.py`): reenvía el mensaje por email reutilizando el `smtplib` de `auth.py` (`enviar_email_contacto`, buzón configurable con la env `EMAIL_CONTACTO`). Antispam por capas: honeypot `sitio_web` (mismo patrón que el registro) + rate limiting en Nginx (zona `contacto`, 3 req/min, burst 2). Si el SMTP falla devuelve **503** con mensaje honesto (a diferencia del fire-and-forget del resto de envíos)
  · Validación en `ContactoIn` (`schemas.py`): email (`EmailStr`) y mensaje (10–2000) obligatorios; nombre opcional (máx 100). En el formulario, email y mensaje van marcados con asterisco y leyenda "* Campos obligatorios". Página `contacto.html` (formulario centrado de una columna, layout propio `.contacto-card`, distinto de la "auth-card" de login) con checkbox de consentimiento y honeypot; `js/contacto.js` autocontenido; clase `.input-campo--area` para el `textarea`. Enlace **Contacto** añadido al footer de las 20 páginas. Nueva sección "Formulario de contacto" en `privacidad.html`
  · `tests/test_contacto.py`: 9 tests (envío con mock SMTP, honeypot, validación ×3, 503, config Nginx ×2). Total **232 funciones / 330 ejecuciones** pasando
  · Repositorio actualizado de `vcv-code/analisis-bdns-dgda` (viejo, a archivar) a **`vcv-code/SubvDGDA`** en todas las referencias: footers de los 21 HTML, comandos `git clone` del README y manuales, y enlaces en `referencia-tecnica.md`
  · Documentado en `README.md`, `docs/tests.md`, `docs/referencia-tecnica.md` (endpoints), `frontend/docs/especificaciones-frontend.md` y `frontend/docs/auditoria-frontend.md`
✔ De-academización e identidad de producción
  · El proyecto deja de presentarse como trabajo académico y pasa a ser un proyecto personal independiente sin ánimo de lucro. Retirado el marco educativo del texto visible: `aviso-legal.html` (Titularidad → "proyecto independiente"; quitada "licencia educativa"; Contacto → formulario) y `privacidad.html` (Responsable del tratamiento → titular discreto contactable por el formulario, sin nombre ni asociación). Footers de los 21 HTML: "FP DAW 2026" → "independiente y sin ánimo de lucro". Limpiados los comentarios internos `Curso: 2º DAW` y la justificación "defendible en el TFG"
  · Anonimato: la atribución de copyright pasa de "Verónica Corpa" a **«Recopilación y Análisis de Subvenciones DGDA»** en los footers, el `LICENSE` (copyright, titularidad y cláusula BY) y la sección de licencia del `README`. El `LICENSE` pierde también el marco académico (tribunal/IES/2º DAW) y remite al formulario de contacto
  · `README`: intro reescrita reconociendo el origen (la idea venía de antes, tomó forma como proyecto de 2º FPGS DAW y se ha ampliado más allá de lo académico). La sección "Autora" mantiene el nombre por ahora (decisión de la titular)
  · Política de privacidad: derechos de acceso/rectificación/supresión ejercitables a través del formulario de contacto
✔ Modo mantenimiento programado
  · Nueva página `frontend/mantenimiento.html` (autónoma, sin navbar ni JS al backend, rutas absolutas, `noindex`) reutilizando las clases `.pagina-error`/`.pagina-50x`
  · Nginx (`docker/nginx/default.conf`): si existe el fichero-bandera `maintenance.on` en la raíz del frontend, devuelve **503** para todo (→ `error_page 503` → `mantenimiento.html`), salvo assets, la propia página y `/healthz` (para que renderice y Docker siga viendo Nginx vivo). El 503 se separa de `50x.html` (que pasa a cubrir solo 500/502/504); los 503 del backend (p. ej. SMTP caído en `/contacto/`) NO se interceptan y llegan tal cual al cliente
  · La bandera se lee en cada petición → activar/desactivar **no requiere reload**. Atajos `make mantenimiento-on` / `make mantenimiento-off` (touch/rm del fichero, ignorado en `.gitignore`)
  · `tests/test_mantenimiento.py`: 4 tests de configuración (bandera, `error_page 503`, separación del 50x, existencia de la página). Total **236 funciones / 334 ejecuciones**. `nginx -t` valida la sintaxis
✔ Estado del plazo de solicitud en el banner de convocatorias
  · **Fase 1 — dato + banner:** nuevo campo `fecha_fin_plazo` en `convocatorias` (modelo ORM, `modelo-fisico.sql` y `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` en `install.sh` para BD ya existentes, sin borrar datos). `AvisoOut.estado_plazo` (computed field): `sin_fecha` / `abierto` (hoy ≤ fin) / `cerrado` (ya venció); `home.js` lo pinta como "Convocatoria 2026 (plazo cerrado) — …". Fechas 2026 cargadas en `install.sh` (INSERT + UPDATE idempotentes): EPA fin 2026-06-15, EELL fin 2026-06-10
  · **Fase 2 — gestión:** endpoint `PATCH /admin/avisos/{id}/fin-plazo` (rol admin) para fijar o borrar (con null) la fecha. En el panel admin, cada aviso activo muestra un badge del estado del plazo (abierto/cerrado/⚠ falta fecha) + un input de fecha y botón "Guardar plazo". El cron (`check_bdns.py`) registra un **WARNING de acción requerida** cuando inserta una convocatoria nueva sin fecha de plazo, para que se rellene desde el panel
  · Auto-detección del plazo descartada: BDNS no da el fin de plazo de forma fiable y scrapear la web DGDA es frágil; para 2 convocatorias/año, el alta manual avisada por el cron es lo robusto
  · `tests/test_avisos.py` (+4: sin_fecha/abierto/cerrado/último día) y `tests/test_admin.py` (+5: fijar fecha, abierto, borrar con null, 404, requiere admin). Total **245 funciones / 343 ejecuciones**
✔ Retoques de recursos y página de mantenimiento
  · Imagen propia en `mantenimiento.html` (`assets/img/gati-manten.webp`) en lugar del logo provisional
  · Los 4 bloques de `recursos.html` pasan de un único verde a un **tono pastel distinto por categoría**: protección (verde), colonias (azul), especializadas (lila), campañas (rosa)
  · **CSS migrado**: el bloque `<style>` embebido en `recursos.html` se traslada a `styles.css` (sección "Página de recursos"), siguiendo la norma de no usar CSS dentro del HTML
  · Nueva nota en recursos: si hay información incorrecta/desactualizada o una organización no quiere aparecer, puede escribir por el formulario de contacto del pie
  · Footer (compartido por todas las páginas): cuando marca + enlaces no caben en una línea, ya no se parten a la izquierda (`space-between` con wrap) sino que se apilan y **centran**. Punto de quiebre del apilado subido de 600px a 850px en `styles.css`
✔ Home: enlaces oficiales en una tabla única por tipo de entidad
  · `num_convoc` expuesto en `ConvocatoriaOut` (`GET /convocatorias/`) para poder enlazar a BDNS (+1 test en `test_convocatorias.py`)
  · Se fusionan la tabla de "Convocatorias" y la sección "Resoluciones oficiales" en **una sola tabla por tipo** (EPA / EELL): Año · Fecha de convocatoria · Fecha de resolución · Acceso directo
  · La **fecha de convocatoria** enlaza a la ficha oficial en **BDNS** (`infosubvenciones.es/.../convocatoria/{num_convoc}`, incluye BOE y PDFs); la **fecha de resolución** enlaza al **BOE** (URLs en un mapa en `home.js`). El botón **"Ver →"** (búsqueda filtrada) solo aparece cuando hay resolución (antes no hay datos)
  · Detalles: el año se omite en las fechas si coincide con la columna Año; fechas-enlace subrayadas (`.tabla-convoc td a:not(.btn)`); las convocatorias sin resolver muestran "Pendiente" / "—"
  · Separador sutil (`border-top`) entre las secciones de tablas y de gráficas (ambas verdes; antes las separaba la sección crema de resoluciones, ya fusionada)
  · Total **246 funciones / 344 ejecuciones**
✔ Buscador: accesos directos a primera y última página
  · Botones **« Primera** / **Última »** en la paginación de `buscador.html` (y su alias `solicitudes.html`), a los lados de Anterior/Siguiente. Se **ocultan** (atributo `hidden`) cuando ya se está en esa página, en vez de deshabilitarse. Nuevos listeners en `js/solicitudes.js` que saltan a la página 1 y a la última
  · Aspecto de enlace (nueva clase `.btn-enlace` en `styles.css`): sin recuadro ni fondo, texto negro y subrayado solo al hover, para distinguirlos de los botones verdes Anterior/Siguiente
  · Regla `.btn[hidden]` en `styles.css`: sin ella, el `display:inline-block` de `.btn` (más específico que el `display:none` implícito del atributo) mantendría visibles los botones pese a `hidden`
✔ Trampa de foco en el menú hamburguesa (WCAG 2.4.3)
  · Con el menú abierto en móvil/tablet (≤900px), el foco del teclado queda **atrapado dentro de la navbar**: al tabular desde el último elemento vuelve al primero (y con Shift+Tab al revés), en lugar de escaparse al contenido oculto tras el panel. Todo en `js/navbar.js`, sin tocar el backend
  · Al **abrir** el menú se lleva el foco al primer enlace: el botón hamburguesa está después en el DOM, así que sin esto el Tab saltaría directo a la página
  · **Esc** cierra y devuelve el foco al botón; el handler de teclado ahora solo actúa con el menú abierto, para no robar el foco (p. ej. al cerrar un modal en otras páginas)
  · Los elementos enfocables se recalculan en cada Tab (`offsetParent !== null` para coger solo los visibles), porque el menú de usuario se genera dinámicamente al iniciar sesión y en móvil los enlaces solo existen visibles con el menú abierto
✔ Estadísticas EELL: tramos de importe y recurrencia de entidades
  · Nuevo análisis en `GET /estadisticas/eell`: **distribución por tramos de importe** (`distribucion_importes`, 5 tramos de <10.000&nbsp;€ a ≥75.000&nbsp;€, más anchos que los de EPA porque las EELL manejan importes mayores y dispersos) y **recurrencia** (`recurrencia_por_anio` con nuevas/recurrentes por año, `entidades_repiten` y `total_entidades`). Hallazgo: solo **5 de 150** entidades han recibido ayuda en más de un año (2023–2025); apenas hay continuidad entre convocatorias
  · La query de concesiones EELL pasa a incluir `anio_convocatoria` y el nombre del beneficiario; la clasificación nueva/recurrente usa el primer año de concesión de cada beneficiario (mismo criterio que el análisis EPA). Schema: `EellAnioRecurrencia` (con `recurrentes_nombres`) + 4 campos nuevos en `EstadisticasEellOut` (con defaults, para no romper la rama sin datos)
  · **Frontend** (a petición de la usuaria): el gráfico de **tramos de importe** (barras, con descarga PNG y modal de conclusiones) sustituye al donut de *concentración del importe*, cuyas conclusiones analíticas se conservan reaprovechadas en el modal de tramos. El **KPI "Entidades que repiten"** sustituye al de *CCAA con mayor importe concedido*. Se añade una tabla nuevas/recurrentes por año con una nota-resumen. `ccaa_top` y `concentracion` se siguen calculando en el backend aunque ya no se pinten
  · En la tabla, los recurrentes (>0) llevan un **asterisco** que remite, bajo la nota, a la lista de ayuntamientos concretos que repiten cada año. Los nombres vienen de la API (`recurrentes_nombres`), no hardcodeados, para que se actualicen solos si el cron añade nuevas convocatorias
  · `tests/test_estadisticas.py`: 3 tests nuevos (distribución de tramos, recurrencia con un año, y recurrencia con fixture multiaño `db_eell_multianio` que verifica también los nombres) + 2 ampliados (estructura y ceros); el bloque EELL pasa de 11 a 14. Total **347 funciones** pasando
✔ Línea de subvención para EPA 2024 (colonias felinas / animales abandonados)
  · El BOE de concesión 2024 no desglosa la línea por entidad, así que las concesiones EPA 2024 tenían `linea = NULL`. La "relación definitiva de admitidas y excluidas" (PDF de la Sede) sí trae la columna "Línea de subvención" en el Anexo I, y el expediente (`2024Bxxx`) permite cruzarla con las concesiones ya cargadas
  · Nuevo `scripts/data_extractor/parser_EPAs_admitidas_2024.py`: parseo por texto con buffer por expediente; la línea se lee **después del CIF** para no confundirse con nombres que contienen "COLONIAS" (p. ej. "ASOC COLONIAS GATUNAS"). Recupera también los expedientes y nombres multilínea que `extract_tables()` se salta. Cruce: **628/628** concedidas (627 con línea + 1 "No aplica" → NULL)
  · `scripts/data_processing/enriquecer_linea_epa2024.py` añade `linea` a `epas_2024.json` (mismo esquema que 2025) y `unificar_datasets.py` la propaga al dataset final; así una instalación limpia ya carga la línea. Reparto EPA 2024: **322 colonias · 305 abandonados · 1 NULL**
  · El buscador ya filtraba por línea (construido para 2025): solo hubo que ampliar el gating del frontend para mostrar el filtro también en EPA 2024. Sin cambios de esquema ni de backend (más allá del texto de ayuda del parámetro)
  · `tests/test_parser_epa_admitidas_2024.py`: 10 tests (normalización, detección de anexo, anclaje por CIF incl. nombre con "COLONIAS" pero línea OTROS, y un test de integración contra el PDF real). PDF fuente en `data/raw/epas/2024/`
✔ Umbral de puntuación (corte de concesión por año) en el inicio
  · `GET /estadisticas/` devuelve `umbrales`: por año/tipo, `hubo_corte` (existen no_beneficiarias = entidades admitidas que se quedaron fuera por puntuación) y la puntuación mínima con la que se obtuvo concesión. Para EPA con línea (2024+) el umbral va **por línea** (cada línea tiene su presupuesto y su corte). Schema `UmbralAnio` + `UmbralLinea`
  · Hallazgo confirmado con datos: en EPA **no hubo corte hasta 2024** (2021–2023 todas las admitidas obtuvieron ayuda); en 2025 el corte se disparó en la línea de abandonados (colonias 35 vs abandonados 55). En EELL siempre hubo corte (77 / 77,55 / 79)
  · Nueva tabla en `index.html` (bajo Convocatorias y resoluciones) con un texto introductorio que explica el corte (presupuesto limitado, para no dar cuantías ridículas; fórmulas de cálculo no públicas; la solución de fondo sería ampliar presupuesto). `home.js` la puebla desde el mismo `/estadisticas/` (sin fetch extra); "Sin corte" donde no lo hubo
  · `tests/test_estadisticas.py`: +4 (estructura, lista vacía sin datos, sin corte, y corte por línea con fixture `db_umbrales`). Total suite en verde
✔ Retoques de estadísticas EELL y tabla de exclusivo
  · **EELL**: se retira la tabla "Entidades nuevas y recurrentes". La info pasa al KPI **"Entidades que repiten"**, cuyo número (dinámico) lleva un **asterisco** que remite a una **nota fija bajo los 4 KPIs** con los ayuntamientos concretos que repiten (nombres hardcodeados por decisión de la usuaria; comentario en el HTML para actualizarla al salir las resoluciones EELL 2026). Aclarada la cifra: 150 entidades únicas / 155 concesiones. `poblarRecurrencia` simplificada (solo el KPI); limpiadas la función huérfana `formatearLista` y el CSS de la tabla. El endpoint sigue devolviendo `recurrencia_por_anio`/`recurrentes_nombres` (ya no se pintan)
  · **Exclusivo**: en la tabla "Resumen de solicitudes por convocatoria", el importe de 2021 (EPA) lleva un **asterisco** con una **nota al pie bajo la tabla de protectoras** que explica el bajo importe de ese primer año (presupuesto de 3 M€ infrautilizado por escasa difusión y complejidad del trámite; recorte posterior de 1 M€). Nota editorial fija
  · Clase CSS `.nota-asterisco` genérica reutilizada por ambas notas. Cambio solo de frontend (sin backend ni tests)
✔ Panel admin: logs del cron y paginación de usuarios
  · **Logs del cron**: nueva sección en `admin.html` con dos sub-bloques (comprobación BDNS `bdns_check.log` y health check `health_check.log`), con el mismo patrón que los logs de la app. Endpoint `GET /admin/logs/cron?fichero=bdns|health&n=` (reaprovecha la lógica de `ver_logs`). Los logs del cron viven en `../logs/cron`; se montan **en solo lectura** en el backend (`../logs/cron:/app/cronlogs:ro` + env `CRON_LOG_DIR`), porque antes el backend no los veía. Al aplicar el nuevo volumen hay que recrear el contenedor (`down && up -d`, no `restart`)
  · **Paginación `/admin/usuarios`**: el endpoint pasa a devolver `{ usuarios, total }` (schema `UsuariosPaginadosOut`) con parámetros `pagina`/`limite` (20 por página); la tabla del panel añade controles Anterior/Siguiente con "Página X de Y · N usuarios" (reutiliza `.paginacion`). Adaptados los tests de admin que leían la respuesta como lista
  · **Retry del cron ya existía**: `check_bdns.py` ya reintentaba las llamadas a BDNS 3 veces con backoff 2s/4s/8s; se retira ese ítem de "Mejoras futuras" (no había nada que hacer)
  · `tests/test_admin.py`: +5 (paginación, y logs del cron: requiere admin, fichero inválido, lectura con `tmp_path`+`monkeypatch`, y fichero no disponible). Suite **366** en verde
✔ Nota aclaratoria sobre la cofinanciación (EELL)
  · Tras comprobar las fuentes reales, se **descarta** incorporar la cofinanciación al dataset: en 2023 la resolución la trae vacía en 558 de 593 entidades y en 2024 no figura en la resolución de concesión (métricas además incomparables, % vs €). Documentado como limitación en el README (sección "Limitaciones conocidas del dato de origen") y retirado de "Mejoras futuras"
  · En el **inicio**, bajo el texto del umbral de puntuación, se añade una frase que aclara qué es la cofinanciación (fondos propios que **suman puntos** pero **no cambian el importe concedido**) y por qué no se muestra por entidad. Solo texto; sin cambios de datos ni backend
✔ Buscador de exclusiones (EELL) con causa oficial
  · **Catálogo de causas** `data/final/causas_exclusion.json`: leyenda código → motivo por (tipo, año) para EPA 2021–2025 y EELL 2023–2025 (137 causas). Cada convocatoria usa su **propia numeración** (el "5" de 2022 no es el "5" de 2023), así que la leyenda va siempre ligada a tipo+año. Transcrito de las tablas revisadas por la usuaria y **cotejado con los anexos oficiales** (se corrigieron por el camino: EPA 2024 cód. 9, EPA 2025 cód. 11–14, EELL 2025 completo 1–41 según el ANEXO III oficial —la tabla resumen 1–25 no casaba con los datos—, y dos erratas "38/2033"→"38/2003")
  · **Parsers EPA** (`parser_EPAs_BOE_base.py` + `parser_EPAs_BOE_2025.py`): capturan la columna de causa de los anexos de excluidas/desestimadas ("Motivo de desestimación" / "Causas de exclusión" / "Criterios de exclusión"). Cambio **aditivo** verificado con diff campo a campo contra los JSON commiteados: 0 cambios en los demás campos. EELL ya la extraía; `unificar_datasets.py` deja de forzarla a NULL en EPA
  · **Normalización** `scripts/data_processing/normalizar_causa_exclusion.py`: los anexos usan separadores inconsistentes (`;`, `, `, `. `, e incluso `16.18.19.`) y códigos con punto propio (`6.a`, `3.1`), así que se tokeniza **guiado por el catálogo** (match voraz del código válido más largo) y se guarda canónico separado por `;`. EPA 2021 publica el motivo como **texto libre**: se mapea a código por match exacto contra el catálogo. Resultado: 643/643 excluidas con causa validada (0 tokens fuera de catálogo)
  · Conciliación con el Excel de referencia de la usuaria: cuadra todo salvo EPA 2022 (59 vs 60: SUBV2022271 aparece también como **concedida** y el dedup se queda la concedida, correcto) y ±1 en EELL 2024/2025 (pendiente de ajuste manual). Las **198 "desistidas por no subsanar"** de EELL 2023 (ANEXO IV, causa 18) se quedan como desistidas y **fuera** del buscador, por consistencia con el resto de años
  · **BD y API**: columna `solicitudes.causa_exclusion` + tabla catálogo `causas_exclusion` (modelo físico + ORM); `cargar_dataset.py` pasa a 7 pasos (carga la causa y el catálogo). `GET /solicitudes/` y `/solicitudes/export` devuelven la causa y aceptan `?causa=` con **match por token exacto** ("6" no casa con "16" ni "6.a"; LIKE portable MariaDB/SQLite). Nuevo `GET /solicitudes/causas` con la leyenda completa agrupada (Cache-Control 1 día). De paso se corrigió un bug latente: `HTTPException` sin importar en el límite de 5000 filas del export
  · **Frontend**: sección "Buscador de exclusiones (EELL)" al final de `buscador.html` (y su alias `solicitudes.html`), debajo del buscador general. Solo EELL (los datos EPA quedan en BD/API), 20 resultados por página, filtros Entidad/Año/CCAA/Causa —el de causa es **dependiente del año** y se rellena con la leyenda de la API—, chip **rojo** (color estado excluida) con los códigos y **modal** con el motivo completo de cada uno (ahí se muestra también el expediente, retirado de la tabla). JS en `js/exclusiones.js` como IIFE con IDs prefijados `exc-` para convivir con `solicitudes.js`; paginación con scroll a la propia sección; CSV con `estado=excluida&tipo=eell` fijos
  · `tests/test_solicitudes.py`: +6 (causa en la respuesta, filtro por token exacto, código con punto, estructura del catálogo, Cache-Control y columna en el CSV) + cabecera CSV actualizada. Suite **372** en verde
✔ Gráficas de exclusiones en las páginas de estadísticas (EPA y EELL)
  · `GET /estadisticas/epas` y `/eell` devuelven un bloque `exclusiones` calculado por el helper compartido `_stats_exclusiones`: `por_anio` (nº de excluidas por convocatoria) y `causas_frecuentes` (top 8 **solo del último año**, porque cada convocatoria usa su propia numeración de causas; el motivo se resuelve contra la tabla catálogo). Una solicitud con varias causas ("2;6.a") suma en cada una. Schemas `ExclusionesStats` + `ExclusionAnio` + `CausaFrecuente`
  · Fila nueva de **pareja de gráficas** en ambas páginas (simétrica con la parrilla existente): "Exclusiones por año" (barras) y "Causas de exclusión más frecuentes" (barras horizontales con el código en el eje y el **motivo completo en el tooltip**; el subtítulo indica el año). En **rojo** `#C62828` (color del estado excluida). Botón PNG y modal de conclusiones como el resto, con textos basados en los datos reales (EELL 2025: el Programa de gestión ética de colonias felinas concentra 88+79 exclusiones; EPA 2025: documentación registral — inscripción 44, tarjeta fiscal 43+21, estatutos 38)
  · `tests/test_estadisticas.py`: +3 con fixture `db_exclusiones` (conteo por año, causas solo del último año con multivalor, y bloque vacío sin datos). Suite **375** en verde
✔ Retirado el bloque "¿Por qué crear una cuenta?" del inicio
  · Primer paso del giro del proyecto hacia web pública sin cuentas: se elimina de `index.html` la sección final que promocionaba el registro (con sus tarjetas "Disponible / Próximamente" ya desfasadas: dos de los "próximamente" —causas de exclusión y umbral de puntuación— son hoy contenido público)
  · Limpieza asociada en `styles.css`: sección 34.2 completa, su media query y una regla suelta (−164 líneas), sin referencias residuales
  · El registro y la zona exclusiva siguen funcionando (login, registro.html, exclusivo.html); solo se deja de promocionar desde la portada
✔ Contenido antes exclusivo, ahora público: resumen por convocatoria (inicio) y mapa de calor CCAA (estadísticas EELL)
  · Primer paso del giro a web pública sin cuentas: se **libera** el contenido que estaba tras login en `exclusivo.html`, sin borrar nada (esa página sigue intacta para registrados mientras exista el registro)
  · **Tabla resumen** por convocatoria (recuento por estado + importe) → nueva sección en banda crema al final del inicio. Endpoint público `GET /estadisticas/resumen-convocatorias` (Cache-Control 1 h); la lógica de agregación se **extrae a una función compartida** `construir_resumen_tabla`, y `/privado/resumen-tabla` pasa a delegar en ella (sin duplicar). El render HTML se extrae a `js/resumen-tabla.js` (`window.renderResumenTabla`), usado por la home y por exclusivo
  · **Mapa de calor CCAA** (choropleth Leaflet) → nueva sección bajo las gráficas de estadísticas EELL. Su JS (`js/mapa-ccaa.js`) ya usaba `por_ccaa` de `GET /estadisticas/eell`, que es público, así que **no hizo falta backend**. El modal "Top municipios" (clic en una CCAA) se **extrae** de `exclusivo.js` a un módulo compartido `js/modal-ccaa.js` (`window.abrirModalCCAA`, auto-conecta el cierre); usa endpoints públicos (`/solicitudes/?ccaa=…` y `/agrupaciones/…`)
  · `exclusivo.js` queda más ligero: delega el render de la tabla y el modal del mapa en los módulos compartidos (mismo comportamiento para registrados)
  · `tests/test_estadisticas.py`: +3 (endpoint público, Cache-Control, y que el privado sigue pidiendo login). Suite **378** en verde
✔ Reordenadas las secciones del inicio
  · Nuevo orden: Hero → Datos (cifras) → Convocatorias → Resumen por convocatoria → Gráficas → Umbral. Se intercambian Umbral y Resumen respecto al orden previo, dejando las dos tablas (Convocatorias + Resumen) juntas y el umbral como cierre explicativo (corte por puntuación + cofinanciación) antes del footer. Las bandas de color siguen alternando (verde/blanco/verde/crema/verde/crema). Solo HTML, sin cambios de JS (las secciones se pueblan por `id`, no por orden)
✔ Retoques visuales del inicio/EELL y `exclusivo.html` reservado a admin
  · **Retoques**: cabeceras de las tablas resumen del inicio al verde estándar de tablas (`--color-verde-tabla`) en vez del oscuro; tabla del umbral en **horizontal** (filas EPA/EELL, columnas por año, construida en `poblarUmbrales`); el **mapa CCAA** de estadísticas EELL pasa a ir **debajo de los KPIs**; y se retira "de calor" del título del mapa ("Mapa por CCAA", no es un heatmap). Corregido de paso un `<div>` sin cerrar **pre-existente** en la sección de gráficas del inicio
  · **`exclusivo.html` → solo admin**: como el resumen y el mapa ya son públicos, la página no ofrecía nada exclusivo. `exclusivo.js` redirige a `privado.html` si el rol no es admin; en `privado.html` el bloque "Área exclusiva" y el enlace "Exclusivo" del navbar solo se muestran a admin (`privado.js`). Se conserva la página para futuro contenido exclusivo. No afecta al acceso del panel admin (que va por Mi perfil → botón Panel admin). Paso alineado con el pivote a web pública [[project_produccion_roadmap]]
✔ Pulido: conclusiones interanuales EELL, tipografía, tabla de tests y arreglos del mapa
  · **Conclusiones interanuales EELL**: los modales "Top provincias" y "Tramos de importe" añaden un párrafo de evolución 2023-2025 con cifras reales del dataset (cómo cambia el reparto por CCAA —Castilla-La Mancha y Andalucía ganan peso, Murcia y Canarias caen—, y cómo sube el importe medio 32k→35k→49k con menos concesiones pero mayores). Se retira el "solo usuarios registrados" de esos textos (el mapa y los rankings ya son públicos)
  · **Tipografía**: suelo de 0.875rem en ~20 textos de lectura que iban en 0.78-0.85 (subtítulos, descripciones, errores de formulario, requisitos de contraseña, créditos del footer, textos de modales); se deja el *chrome* (badges, chips, leyenda del mapa, logs) y las celdas de tablas en su tamaño
  · **docs/tests.md**: la tabla numerada obsoleta (199 filas) se sustituye por un resumen por archivo (23 filas, funciones/ejecuciones) regenerable con `pytest --collect-only`; recuentos al día (280 funciones / 378 ejecuciones)
  · **Arreglos**: el modal de conclusiones no dejaba hacer scroll con textos largos (`.modal-grafica__contenido` con `flex:1`+`min-height:0` en vez de `height:100%`); la tarjeta del mapa EELL no cerraba su `<div>` y su fondo blanco envolvía las gráficas de debajo (cerrada la card, retirado el `</div>` huérfano); el zoom del mapa se acota a **2-8** (antes llegaba a 1 y a 9+)
  · Se retira de "Mejoras futuras" el ítem de conclusiones comparativas EELL (implementado) y el de mostrar exclusiones EPA en el buscador (descartado: el análisis ya está en las gráficas)
✔ Resoluciones tardías EPA reatribuidas a su convocatoria
  · **Problema**: una solicitud presentada en el año N cuya resolución no se publica hasta el BOE de N+1 se atribuía al año del fichero, inflando los importes de N+1. Afectaba a dos casos con dinero real: **La Sexta Huella** (`SUBV2022659`, 4.684,91 € contados en 2023 en vez de 2022) y **Amibichos** (`2023B628`, 4.028,42 € contados en 2024 en vez de 2023)
  · **Solución** (`resolver_anio_epa` en `unificar_datasets.py`): se reatribuye el registro al año que declara el JSON de origen, pero **solo si el mismo `num_expediente` y el mismo `cif` existen también en el fichero de ese año**. La comprobación del CIF es imprescindible: sin ella se reatribuirían `SUBV2022021` (número reutilizado por el BOE para Amores Perros Cádiz en 2021 y Can Terrassa en 2022 — CIF distinto) y `SUBV2032021` (errata de año, no hay fichero de 2032), y ambos colapsarían bajo la misma clave de deduplicación
  · **Efecto**: al caer en el año donde ya estaba su versión excluida, la prioridad intra-año conserva la concedida, y cada solicitud queda con un solo registro y su estado final. Importe global sin cambios (14.835.479,86 € concedidos), solo repartido: EPA 2022 **+4.684,91 €**, EPA 2023 **−656,49 €**, EPA 2024 **−4.028,42 €**. Total de registros **6398 → 6396** (EPA 3353 → 3351); excluidas EPA 2022 59 → 58 y 2023 13 → 12. Duplicados intra-año siguen en **0**. `periodo_meses` pasa a seguir al año reatribuido, no al del fichero
  · **Tests**: +8 en `test_unificar_datasets.py` cubriendo los dos casos reatribuidos y los dos falsos positivos. Suite **386** en verde
  · Actualizados README, `manuales/manual-instalacion.md`, `docs/modelo-datos.md`, `docs/pipeline-datos.md` (sección "Duplicados cross-year" reescrita) y `docs/tests.md`
✔ Pipeline: dos trampas corregidas al hilo de lo anterior
  · **`make dataset` (nuevo)**: encadena `unificar_datasets.py` + `normalizar_causa_exclusion.py`. Hacía falta porque el primero reconstruye el dataset desde los JSON procesados y deja las causas en crudo (`10, 12, 16`), revirtiendo la normalización de ~370 registros. Ejecutarlos por separado era un pie de banco fácil de pisar
  · **`make reset-db` arreglado**: su bucle de espera usaba `mariadb -uroot -proot`, y la contraseña real es `${MYSQL_ROOT_PASSWORD}` (`rootpass_bdns`), así que nunca conectaba y el target se colgaba indefinidamente. Se retira el bucle entero: `docker compose up -d` ya bloquea hasta que el healthcheck de `db` pasa, porque backend, cron y adminer declaran `condition: service_healthy`
  · **Documentado que `cargar_dataset.py` es aditivo** (salta por `(num_expediente, id_convoc)`, nunca actualiza ni borra), en README, manual de instalación y `pipeline-datos.md`. En el README, `make cargar` estaba descrito como "recarga el dataset sin borrar el volumen", que inducía a error: si cambian registros ya cargados hay que ir a `make reset-db`
✔ Retirado el registro público; el alta de usuarios pasa al panel admin
  · **Motivo**: con todo el contenido ya público, las cuentas de público no aportaban nada. Se retira el auto-registro y se conserva el login para la administradora y el panel admin
  · **`POST /admin/usuarios` (nuevo)**, protegido por rol `admin`. Era imprescindible: el panel sabía listar, cambiar rol, activar y borrar usuarios, pero **no crearlos**, así que sin este endpoint la única forma de dar acceso a alguien habría sido insertar la fila a mano en MariaDB generando el hash bcrypt. Dos diferencias deliberadas respecto al registro retirado: devuelve **409** si el email existe (el anti-enumeración protegía un endpoint público; a la administradora hay que decirle el motivo) y permite **fijar el rol** al crear, en vez de crear y hacer luego un PATCH
  · **Retirado**: `POST /auth/registro`, el schema `RegistroIn`, `registro.html`, el enlace "Regístrate aquí" de `login.html`, el módulo de registro de `auth.js` (~130 líneas) y la zona `registro` del rate limiting de Nginx, que sin `location` que la usara solo reservaba 10 MB de memoria compartida. Con el formulario público desaparece también su **honeypot**, que solo tenía sentido frente a un formulario abierto
  · **Frontend**: formulario de alta plegable (`<details>`) en la sección Usuarios del panel, con email, nombre, contraseña y rol; validación en cliente antes de enviar y recarga del listado al crear. CSS en `styles.css` (`.admin-alta*`), sin estilos inline
  · **Limpieza al hilo**: la validación de contraseña estaba **duplicada en tres schemas**; se extrae a `validar_password_segura()` en `schemas.py`. En el frontend, `cumpleRequisitosPassword` y `todosRequisitosOk` se mueven de `auth.js` a `utils.js` para poder reutilizarlas en el panel. Retirado también el pre-relleno `prefill_email`/`prefill_password` de `auth.js`, que quedaba muerto (solo lo escribía el registro)
  · **Tests**: los que sembraban usuarios llamando a `POST /auth/registro` (en `test_admin.py`, `test_verificacion_email.py`, `test_recuperar_password.py` y `test_auth.py`) pasan a sembrar en BD mediante el fixture `crear_usuario` de `conftest.py`; era la mayor parte del trabajo, más que el borrado en sí. +12 tests del alta en `test_admin.py`. Suite **390** en verde
  · **Verificado en vivo**: `POST /auth/registro` y `registro.html` devuelven 404; el alta responde 201 y el email de verificación llega a Mailpit; duplicado 409, contraseña débil 422, sin token 401, y el login de la cuenta nueva 403 hasta verificar
✔ `make reset-db` blindado: backup automático y redescubrimiento de convocatorias
  · **Contexto**: un `reset-db` durante el desarrollo se llevó por delante las 2 convocatorias de 2026 y con ellas los avisos del banner de inicio. El dataset llega a 2025; las del año en curso las descubre el cron consultando BDNS y viven solo en la BD
  · **(A) Backup automático**: `reset-db` ejecuta `make backup` tras confirmar y antes de borrar. Los volcados pasan a `backups/`, añadido a `.gitignore` junto a `backup_*.sql` — antes `make backup` escribía en la raíz del proyecto sin ninguna regla que lo ignorase, con riesgo de commitear un volcado con usuarios y hashes de contraseña
  · **(B) `redescubrir-convocatorias` (nuevo)**: relanza `check_bdns.py` al final. **Borrar el fichero de estado no es opcional**: `check_bdns.py` guarda en `logs/cron/estado_<año>.json` qué convocatorias ya registró y, si constan las dos, se salta la búsqueda entera. Ese fichero es un espejo de la BD, así que hay que resetear ambos a la vez o quedan desincronizados y el cron no repondría nada. El paso no corta el target si falla (necesita red y BDNS respondiendo)
  · **Bug latente encontrado al probarlo**: el healthcheck de `db` en `docker-compose.yml` no tenía **`start_period`**. Con volumen nuevo, MariaDB tarda ~1 min en inicializar los ficheros y cargar `modelo-fisico.sql`, pero los fallos contaban desde el segundo 0: se agotaban los 5 reintentos (~50 s) y el contenedor quedaba `unhealthy` justo antes de estar listo, con lo que backend, cron y adminer no arrancaban y `up -d` fallaba. Añadido `start_period: 180s`, durante el cual los fallos no cuentan (no ralentiza el arranque normal). Afectaba también a la **primera instalación**, no solo a `reset-db`
  · **Verificado ejecutando el `reset-db` completo**: backup creado, BD recreada, 6396 solicitudes cargadas y el cron insertando las 2 convocatorias de 2026 con sus ids y títulos normalizados. Lo único que sigue sin reponerse son las `fecha_fin_plazo`, que son dato propio y no de BDNS — documentado en el target, el README y el manual
✔ Retiradas las credenciales del repositorio: la cuenta de administración se crea al instalar
  · **Motivo**: `docker/init/modelo-fisico.sql` llevaba dentro el hash bcrypt de `admin@demo.com` / `Admin1234!`, e `install.sh` sembraba además `usuario@demo.com`. Mientras un hash válido viviese en el repositorio, cualquiera que lo leyese conocía la contraseña de administración de **todo despliegue nuevo**: bastaba con abrir el dominio y entrar. Era el obstáculo para poder hacer público el repositorio
  · **`scripts/crear_admin.sh` (nuevo)**: pide email y contraseña, valida las mismas reglas que el backend (`validar_password_segura`) y da de alta la cuenta. No hace nada si ya existe un admin. Admite `ADMIN_EMAIL`/`ADMIN_PASSWORD` para uso no interactivo, y falla con un mensaje claro si no hay cuenta y tampoco se puede preguntar
  · **Detalles de implementación**: el hash lo genera el contenedor del backend con `hashear_password`, la misma función que usa la web al cambiar una contraseña, en vez de reimplementar bcrypt en bash — así no hay dos formas de derivarlo que puedan divergir. La contraseña viaja por **stdin y no por argv**, porque los argumentos de un proceso son visibles para cualquiera que liste procesos. La cuenta nace con `email_verificado=1`: la crea quien administra el servidor, no hay dirección que confirmar, y sin eso el login devolvería 403 sin nadie que pudiera verificar a nadie
  · **Retirado**: la siembra de usuarios de `modelo-fisico.sql` y las dos de `install.sh`, más el bloque de credenciales de su resumen final
  · **Sin riesgo de quedarse fuera**: `install.sh` invoca el script tras levantar los contenedores, y **`make reset-db` también**, porque recrear la BD dejaba la instalación sin ninguna cuenta con la que entrar. Nuevo target `make crear-admin` para el resto de casos
  · **Verificado**: alta no interactiva, login real con la cuenta creada (200), contraseña débil rechazada, no-op si ya hay admin, y error claro sin variables ni terminal. Comprobado además que no queda ningún hash bcrypt ni credencial en los ficheros versionados
  · Actualizados README, `manuales/manual-instalacion.md` y `manuales/manual-usuario.md`, que documentaban las cuentas de demo como si siempre existieran
