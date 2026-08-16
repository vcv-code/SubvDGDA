# Auditoría de calidad — Frontend

## Proyecto BDNS/DGDA · Subvenciones de Bienestar Animal · 2º DAW 2026

> **Cómo leer este documento:**  
> `[x]` = verificado y hecho · `[ ]` = pendiente de verificación manual o sin implementar  
> Los ítems marcados con 🔗 requieren coordinación con la parte de backend.

---

## 1. Estructura y archivos

- [x] Todos los archivos HTML están en `frontend/`
- [x] Todos los scripts JS están en `frontend/js/`
- [x] La hoja de estilos compartida está en `frontend/css/styles.css`
- [x] Los assets (logo, imágenes) están en `frontend/assets/`
- [x] La documentación técnica está en `frontend/docs/`
- [x] No hay archivos `.DS_Store`, `thumbs.db` ni temporales en el repositorio (proyecto en Linux/WSL2 — estos archivos no se generan)
- [x] No hay credenciales ni tokens hardcodeados en ningún archivo JS

### Inventario de páginas HTML (19 archivos)

| Archivo | Propósito | Verificado |
|---|---|---|
| `index.html` | Portada / KPIs generales | [x] |
| `buscador.html` | Buscador de solicitudes | [x] |
| `estadisticas-epas.html` | Estadísticas EPAs | [x] |
| `estadisticas-eell.html` | Estadísticas EELL | [x] |
| `recursos.html` | Recursos y enlaces útiles | [x] |
| `login.html` | Inicio de sesión | [x] |
| `verificar-email.html` | Confirmación de email | [x] |
| `recuperar-password.html` | Solicitud de recuperación | [x] |
| `reset-password.html` | Restablecimiento de contraseña | [x] |
| `privado.html` | Zona privada (usuario) | [x] |
| `exclusivo.html` | Contenido exclusivo (resoluciones) | [x] |
| `admin.html` | Panel de administración | [x] |
| `entidad.html` | Ficha de entidad — accesible desde "Ver página completa →" en el modal del buscador o por URL directa | [x] |
| `aviso-legal.html` | Aviso legal | [x] |
| `privacidad.html` | Política de privacidad | [x] |
| `404.html` | Página de error 404 | [x] |
| `50x.html` | Página de error 500/502/503/504 | [x] |

---

## 2. Accesibilidad (WCAG 2.1 nivel AA)

### 2.1 Skip navigation

- [x] Todas las páginas tienen `<a class="skip-nav" href="#contenido-principal">` justo después de `<body>` (19/19)
- [x] Todos los `<main>` tienen `id="contenido-principal"`
- [x] El enlace es visible al recibir foco de teclado (con fondo verde oscuro y texto blanco)
- [x] El ratio de contraste del skip-nav es ≥ 4.5:1 (nuestro valor: 12:1 ✓)

### 2.2 Roles ARIA y semántica

- [x] Los `<canvas>` de Chart.js tienen `role="img"` y `aria-label` descriptivo (4 páginas con gráficas)
- [x] Los `<nav>` tienen `aria-label` único por página — 19/19 (navbar principal + nav del footer)
- [x] Los formularios de autenticación tienen `aria-labelledby` apuntando al H1 de la tarjeta (login, registro, recuperar-password, reset-password)
- [x] El `<pre>` de logs en `admin.html` tiene `aria-live="polite"` y `aria-label="Últimas líneas del log de acceso del servidor"`
- [x] Las páginas de error tienen ARIA: `404.html` usa `aria-label="Página no encontrada"` en el contenedor; `50x.html` usa `aria-labelledby`

### 2.3 Formularios

- [x] Todos los campos `<input>` tienen `<label>` asociado explícito (`for` + `id`)
- [x] Los mensajes de error usan `role="alert"` y `aria-live="polite"` — en todas las páginas con formulario
- [x] Los mensajes de éxito usan `role="status"` y `aria-live="polite"` — corregido en `privado.html` (cambiar-nombre-ok, cambiar-password-ok)
- [x] Los campos requeridos son identificables — atributo HTML `required` presente en todos los campos obligatorios
- [x] El campo "confirmar contraseña" muestra error de coincidencia en cliente antes de enviar (`auth.js` y `privado.js`)

### 2.4 Navegación y enlaces externos

- [x] Los enlaces que abren en pestaña nueva tienen `rel="noopener noreferrer"` — sin excepciones
- [x] Los enlaces a boe.es tienen `title="Se abre en una pestaña nueva"` — todos en `index.html`
- [x] Los enlaces con `aria-label` son descriptivos (ningún "haz clic aquí" ni "más información")
- [ ] La navegación es operativa completamente por teclado (Tab + Enter + Esc) — verificación manual pendiente

---

## 3. Rendimiento

### 3.1 Imágenes

- [x] El logo en navbar tiene `width="49" height="54"` en todas las páginas (prevención CLS) — 19/19
- [x] El logo en footer tiene `width="33" height="36" loading="lazy"` en todas las páginas — 19/19
- [x] La imagen hero de `index.html` no tiene `width`/`height` HTML — decisión intencionada: el contenedor CSS de altura fija ya previene el CLS; añadir las dimensiones naturales del archivo podría crear un salto visual antes de que el CSS aplique

### 3.2 Fuentes y CSS

- [x] `<link rel="preconnect">` para Google Fonts en todas las páginas — 19/19
- [x] No hay CSS muerto en `styles.css` — clases obsoletas (`.hero`, `.seccion-transparencia`, `.footer` antiguo) ya eliminadas
- [x] El índice de secciones en `styles.css` refleja el estado actual — 28 secciones

### 3.3 JavaScript

- [x] No hay `console.log` de depuración en código de producción
- [x] `obtenerToken()` eliminada de `exclusivo.js` (era código muerto — nunca se llamaba)
- [x] Los fetch de datos manejan correctamente los estados de error (mensajes visuales en todos los catch principales)

---

## 4. Responsive

- [x] El diseño es funcional en múltiples tamaños — verificado con Chrome DevTools (pantalla normal, tablet y móvil)
- [x] Las tablas de datos tienen `overflow-x: auto` en contenedor (`.tabla-scroll`) — definido en CSS, aplicado dinámicamente en `exclusivo.js`
- [x] Los gráficos Chart.js reducen altura a 220px (barras) / 180px (donut) en ≤480px — confirmado en `styles.css`
- [x] La cuadrícula `.privado-grid` colapsa a columna única en ≤640px
- [x] Los formularios de autenticación son utilizables en móvil
- [x] El navbar no desborda en pantallas estrechas — responsive en 3 breakpoints (900/768/600px); texto del logo oculto en ≤600px
- [x] `.privado-dos-columnas` colapsa a columna única en ≤768px

---

## 5. Autenticación y sesión

### 5.1 Flujo de login / registro 🔗

- [x] `POST /auth/login` → guarda `token` y `refresh_token` en `localStorage`
- [x] `POST /auth/registro` → redirige a `verificar-email.html` con indicación de revisar el correo
- [x] `POST /auth/refresh` → renueva el access token con el refresh token
- [x] `POST /auth/logout` → revoca el refresh token en el servidor (fire-and-forget)

### 5.2 Deep link post-login

- [x] `sessionStorage.setItem('redirect_post_login', window.location.href)` antes de cada redirección a login por sesión ausente o expirada
- [x] Tras login exitoso, `auth.js` consume el deeplink y redirige a la URL guardada (o a `privado.html` si no hay ninguna)
- [x] `sessionStorage.removeItem('redirect_post_login')` se ejecuta tras consumir el deeplink

### 5.3 Verificación de email

- [x] `GET /auth/verificar?token=<token>` → muestra éxito + botón login
- [x] Token inválido / caducado → muestra error + sección de reenvío
- [x] URL sin `?token=` → muestra error + sección de reenvío
- [x] 🔗 `POST /auth/reenviar-verificacion` implementado en backend
- [x] La respuesta del reenvío es siempre positiva (sin revelar si el email existe)
- [x] El botón de reenvío se deshabilita tras el primer envío exitoso (se re-habilita si hay error para permitir reintento)

### 5.4 Zona privada

- [x] `privado.html` redirige a login si no hay token (con deeplink guardado)
- [x] `exclusivo.html` redirige a login si no hay token (con deeplink guardado)
- [x] `admin.html` redirige a login si no hay token y a `privado.html` si el rol no es admin
- [x] El cambio de contraseña valida coincidencia de campos en cliente antes de llamar a la API

---

## 6. Integración con la API REST 🔗

### 6.1 Endpoints existentes (verificar que responden correctamente)

| Endpoint | Página | Estado |
|---|---|---|
| `GET /estadisticas/home` | `index.html` | [x] |
| `GET /estadisticas/epas` | `estadisticas-epas.html` | [x] |
| `GET /estadisticas/eell` | `estadisticas-eell.html` | [x] |
| `GET /solicitudes` (con filtros) | `buscador.html` | [x] |
| `GET /solicitudes/?cif=` | `entidad.html` + modal de `buscador.html` | [x] |
| `GET /privado/perfil` | `privado.html` | [x] |
| `GET /privado/resumen-exclusivo` | `exclusivo.html` | [x] |
| `GET /admin/logs` | `admin.html` | [x] |
| `PUT /privado/cambiar-contrasena` | `privado.html` | [x] |

### 6.2 Endpoints backend requeridos

| Endpoint | Página | Estado |
|---|---|---|
| `POST /auth/reenviar-verificacion` | `verificar-email.html` | [x] 🔗 |

### 6.3 Manejo de errores HTTP

- [x] 401 → borrar token + guardar deeplink + redirigir a login
- [x] 403 → mostrar mensaje de acceso denegado (no redirigir)
- [x] 422 → mostrar el mensaje de validación de Pydantic al usuario (prefijo "Value error," limpiado en JS)
- [x] 500/502/503 → mostrar error genérico sin exponer detalles técnicos
- [x] Error de red (sin conexión) → mostrar mensaje de error en cada bloque afectado (catch en todos los fetch principales)

---

## 7. Páginas de error (Nginx)

- [x] `404.html` existe y es accesible en `frontend/404.html`
- [x] `50x.html` existe y es accesible en `frontend/50x.html`
- [x] 🔗 `docker/nginx/default.conf` incluye:

  ```nginx
  error_page 404 /404.html;
  error_page 500 502 503 504 /50x.html;
  ```

- [x] Las páginas de error no dependen del backend ni de JS externo (estáticas servidas por Nginx)
- [x] Las páginas de error tienen navbar y footer funcionales
- [x] La página `50x.html` tiene botón "Reintentar" con `window.location.reload()`

---

## 8. SEO y metadatos

- [x] Todas las páginas tienen `<title>` único y descriptivo
- [x] Todas las páginas tienen `<meta name="description">` con contenido relevante (19/19)
- [x] `404.html` y `50x.html` tienen `<meta name="robots" content="noindex">`
- [x] El favicon está referenciado en todas las páginas (19/19)
- [x] Las páginas de datos tienen Open Graph tags (`og:title`, `og:description`, `og:image`) — `index`, `buscador`, `estadisticas-epas`, `estadisticas-eell`

---

## 9. Documentación

### 9.1 Documentación del frontend (`frontend/docs/`)

| Archivo | Contenido | Estado |
|---|---|---|
| `diseño.md` | Paleta de colores, tipografía, espaciado, logo, wireframes y árbol de archivos | [x] |
| `especificaciones-frontend.md` | Stack tecnológica, componentes compartidos, especificación de cada página y decisiones técnicas | [x] |
| `patrones.md` | Patrones JS: URLSearchParams, history.replaceState, fetch/async-await, auth cliente, delegación de eventos, formateo | [x] |
| `auditoria-frontend.md` | Este documento — checklist de calidad del frontend | [x] |

### 9.2 Documentación del proyecto (`docs/` y `README.md`)

| Archivo | Contenido | Estado |
|---|---|---|
| `README.md` | Visión general, tecnologías, arquitectura del sistema, sección frontend con todas las páginas, instalación y estado del proyecto | [x] |
| `docs/autenticacion.md` | Flujo JWT, access/refresh token, rotación, verificación email, honeypot — referencia directa para `auth.js` y páginas protegidas | [x] |
| `docs/referencia-tecnica.md` | Endpoints de la API, configuración Docker, Nginx, SSL, logs y comandos de mantenimiento | [x] |
| `docs/modelo-datos.md` | Esquema de BD, entidades principales (convocatorias, beneficiarios, solicitudes, concesiones, agrupaciones) y diagramas ER | [x] |
| `docs/pipeline-datos.md` | Fuentes de datos (API BDNS, XML/PDF/Excel BOE), parsers por tipo y año, problemas resueltos y organización del dataset | [x] |
| `docs/tests.md` | Estrategia de tests, tabla completa de los 246 tests automáticos (344 ejecuciones) y pruebas manuales E2E del frontend | [x] |
| `docs/historial-implementacion.md` | Registro cronológico de todas las funcionalidades implementadas por rama | [x] |

### 9.3 Cabeceras en archivos de código

- [x] `styles.css` tiene índice de 28 secciones al inicio del archivo
- [x] Los 16 archivos JS tienen cabecera con propósito, endpoints y página asociada
- [x] `404.html` y `50x.html` incluyen comentarios con la configuración de Nginx requerida

---

## 10. Despliegue y configuración Docker

- [x] 🔗 `docker-compose.yml` levanta correctamente frontend (Nginx) + backend (FastAPI) + base de datos
- [x] 🔗 `docker/nginx/default.conf` incluye proxy inverso para `/auth/*`, `/solicitudes`, `/estadisticas/*`, `/privado/*`, `/admin/*`
- [x] 🔗 Las variables de entorno sensibles están en `.env` (no en el repositorio)
- [x] 🔗 `.gitignore` excluye `.env`, `__pycache__`, `node_modules`, `*.pyc`
- [x] El frontend es accesible en `https://subvencionesDGDA.local` tras `docker compose up`

---

## 11. Pruebas manuales

### Flujos críticos a verificar en el navegador

- [x] **Flujo de registro completo:** registro → email de verificación → verificación → login
- [x] **Flujo de reenvío:** registro → enlace expirado → reenvío → nuevo enlace → verificación
- [x] **Deep link:** acceder directamente a `privado.html` sin sesión → login → aterrizar en `privado.html`
- [x] **Cambio de contraseña:** contraseña actual incorrecta muestra error; correcta muestra éxito
- [x] **Buscador con filtros:** filtrar por año, tipo, estado, CCAA; paginación funciona con botones compactos
- [x] **Ficha de entidad:** desde buscador → clic en fila → modal inline con historial, expediente, importes y CCAA (cuando disponible)
- [x] **Enlace "Ver página completa →":** en el pie del modal → abre `entidad.html?cif=...` en pestaña nueva con el historial completo
- [x] **Error 404:** navegar a `https://subvencionesDGDA.local/ruta-inexistente` → aparece `404.html`
- [x] **Error 50x:** parar el backend → acceder a `buscador.html` (Nginx sirve el estático, sin backend la API falla y se muestra `50x.html`)
- [x] **Responsividad:** verificar portada, buscador y estadísticas en Chrome DevTools (pantalla normal, tablet y móvil)

### Accesibilidad — prueba con teclado

- [ ] En todas las páginas: Tab hasta el skip-nav → Enter → foco salta al contenido principal
- [ ] En `login.html`: completar formulario solo con teclado → enviar → redirigir a privado
- [ ] En `buscador.html`: usar los filtros y el botón "Buscar" solo con teclado
