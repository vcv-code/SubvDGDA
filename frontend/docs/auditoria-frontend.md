# Auditoría de calidad — Frontend
## Proyecto BDNS/DGDA · Subvenciones de Bienestar Animal · 2º DAW 2026

> **Cómo usar este documento:**  
> Marca cada ítem con ✅ (hecho), ⚠️ (pendiente/parcial) o ❌ (no aplica).  
> Los ítems marcados con 🔗 requieren coordinación con la parte de backend.

---

## 1. Estructura y archivos

- [ ] Todos los archivos HTML están en `frontend/`
- [ ] Todos los scripts JS están en `frontend/js/`
- [ ] La hoja de estilos compartida está en `frontend/css/styles.css`
- [ ] Los assets (logo, imágenes) están en `frontend/assets/`
- [ ] La documentación técnica está en `frontend/docs/`
- [ ] No hay archivos `.DS_Store`, `thumbs.db` ni temporales en el repositorio
- [ ] No hay credenciales ni tokens hardcodeados en ningún archivo JS

### Inventario de páginas HTML (16 archivos)

| Archivo | Propósito | Verificado |
|---|---|---|
| `index.html` | Portada / KPIs generales | [ ] |
| `buscador.html` | Buscador de solicitudes | [ ] |
| `estadisticas-epas.html` | Estadísticas EPAs | [ ] |
| `estadisticas-eell.html` | Estadísticas EELL | [ ] |
| `recursos.html` | Recursos y enlaces útiles | [ ] |
| `login.html` | Inicio de sesión | [ ] |
| `registro.html` | Registro de usuario | [ ] |
| `verificar-email.html` | Confirmación de email | [ ] |
| `privado.html` | Zona privada (usuario) | [ ] |
| `exclusivo.html` | Contenido exclusivo (resoluciones) | [ ] |
| `admin.html` | Panel de administración | [ ] |
| `entidad.html` | Ficha de entidad | [ ] |
| `aviso-legal.html` | Aviso legal | [ ] |
| `privacidad.html` | Política de privacidad | [ ] |
| `404.html` | Página de error 404 | [ ] |
| `50x.html` | Página de error 500/502/503/504 | [ ] |

---

## 2. Accesibilidad (WCAG 2.1 nivel AA)

### 2.1 Skip navigation

- [ ] Todas las páginas tienen `<a class="skip-nav" href="#contenido-principal">` justo después de `<body>`
- [ ] Todos los `<main>` tienen `id="contenido-principal"`
- [ ] El enlace es visible al recibir foco de teclado (con fondo verde oscuro y texto blanco)
- [ ] El ratio de contraste del skip-nav es ≥ 4.5:1 (nuestro valor: 12:1 ✓)

### 2.2 Roles ARIA y semántica

- [ ] Los `<canvas>` de Chart.js tienen `role="img"` y `aria-label` descriptivo
- [ ] Los `<nav>` tienen `aria-label` único por página
- [ ] Los formularios de autenticación tienen `aria-labelledby` apuntando al H1 de la tarjeta
- [ ] El `<pre>` de logs en `admin.html` tiene `aria-live="polite"` y `aria-label`
- [ ] Las tarjetas de error (404, 50x) tienen `aria-labelledby`

### 2.3 Formularios

- [ ] Todos los campos `<input>` tienen `<label>` asociado explícito (`for` + `id`)
- [ ] Los mensajes de error usan `role="alert"` y `aria-live="polite"`
- [ ] Los mensajes de éxito usan `role="status"` y `aria-live="polite"`
- [ ] Los campos requeridos son identificables (no solo por color)
- [ ] El campo "confirmar contraseña" muestra error de coincidencia en cliente antes de enviar

### 2.4 Navegación y enlaces externos

- [ ] Los enlaces que abren en pestaña nueva tienen `rel="noopener noreferrer"`
- [ ] Los 8 enlaces a boe.es en `exclusivo.html` tienen `title="Se abre en una pestaña nueva"`
- [ ] Los enlaces con `aria-label` son descriptivos (no "haz clic aquí")
- [ ] La navegación es operativa completamente por teclado (Tab + Enter + Esc)

---

## 3. Rendimiento

### 3.1 Imágenes

- [ ] El logo en navbar tiene `width="49" height="54"` en todas las páginas (prevención CLS)
- [ ] El logo en footer tiene `width="33" height="36" loading="lazy"` en todas las páginas
- [ ] No hay imágenes sin dimensiones explícitas en el viewport inicial

### 3.2 Fuentes y CSS

- [ ] `<link rel="preconnect">` para Google Fonts en todas las páginas
- [ ] No hay CSS muerto en `styles.css` (bloques `.hero`, `.seccion-transparencia` y `.footer` antiguo eliminados)
- [ ] El índice de secciones en `styles.css` refleja el estado actual (28 secciones)

### 3.3 JavaScript

- [ ] No hay `console.log` de depuración en código de producción
- [ ] No hay funciones definidas pero nunca llamadas (`obtenerToken()` eliminada)
- [ ] Los fetch de datos manejan correctamente los estados de error y de carga (spinner visible)

---

## 4. Responsive

- [ ] El diseño es funcional en 320px, 375px, 768px, 1024px y 1440px de ancho
- [ ] Las tablas de datos tienen `overflow-x: auto` en contenedor (`.tabla-scroll`)
- [ ] Los gráficos Chart.js reducen altura a 220px (barras) / 180px (donut) en ≤480px
- [ ] La cuadrícula `.privado-grid` colapsa a columna única en ≤640px
- [ ] Los formularios de autenticación son utilizables en móvil
- [x] El navbar no desborda en pantallas estrechas — responsive en 3 breakpoints (900/768/600px); texto del logo oculto en ≤600px
- [x] `.privado-dos-columnas` colapsa a columna única en ≤768px

---

## 5. Autenticación y sesión

### 5.1 Flujo de login / registro 🔗

- [ ] `POST /auth/login` → guarda `token` y `refresh_token` en `localStorage`
- [ ] `POST /auth/registro` → redirige a `verificar-email.html` con indicación de revisar el correo
- [ ] `POST /auth/refresh` → renueva el access token con el refresh token
- [ ] `POST /auth/logout` → revoca el refresh token en el servidor (fire-and-forget)

### 5.2 Deep link post-login

- [ ] `sessionStorage.setItem('redirect_post_login', window.location.href)` antes de cada redirección a login por sesión ausente o expirada
- [ ] Tras login exitoso, `auth.js` consume el deeplink y redirige a la URL guardada (o a `privado.html` si no hay ninguna)
- [ ] `sessionStorage.removeItem('redirect_post_login')` se ejecuta tras consumir el deeplink

### 5.3 Verificación de email

- [ ] `GET /auth/verificar?token=<token>` → muestra éxito + botón login
- [ ] Token inválido / caducado → muestra error + sección de reenvío
- [ ] URL sin `?token=` → muestra error + sección de reenvío
- [ ] 🔗 `POST /auth/reenviar-verificacion` implementado en backend
- [ ] La respuesta del reenvío es siempre positiva (sin revelar si el email existe)
- [ ] El botón de reenvío se deshabilita tras el primer envío exitoso

### 5.4 Zona privada

- [ ] `privado.html` redirige a login si no hay token (con deeplink guardado)
- [ ] `exclusivo.html` redirige a login si no hay token (con deeplink guardado)
- [ ] `admin.html` redirige a login si no hay token y a `privado.html` si el rol no es admin
- [ ] El cambio de contraseña valida coincidencia de campos en cliente antes de llamar a la API

---

## 6. Integración con la API REST 🔗

### 6.1 Endpoints existentes (verificar que responden correctamente)

| Endpoint | Página | Estado |
|---|---|---|
| `GET /estadisticas/home` | `index.html` | [ ] |
| `GET /estadisticas/epas` | `estadisticas-epas.html` | [ ] |
| `GET /estadisticas/eell` | `estadisticas-eell.html` | [ ] |
| `GET /solicitudes` (con filtros) | `buscador.html` | [ ] |
| `GET /entidades/:cif` | `entidad.html` | [ ] |
| `GET /privado/perfil` | `privado.html` | [ ] |
| `GET /privado/contenido-exclusivo` | `exclusivo.html` | [ ] |
| `GET /admin/logs` | `admin.html` | [ ] |
| `PUT /privado/cambiar-contrasena` | `privado.html` | [ ] |

### 6.2 Endpoints nuevos requeridos por esta issue

| Endpoint | Página | Estado |
|---|---|---|
| `POST /auth/reenviar-verificacion` | `verificar-email.html` | [ ] 🔗 |

### 6.3 Manejo de errores HTTP

- [ ] 401 → borrar token + guardar deeplink + redirigir a login
- [ ] 403 → mostrar mensaje de acceso denegado (no redirigir)
- [ ] 422 → mostrar el mensaje de validación de Pydantic al usuario
- [ ] 500/502/503 → mostrar error genérico sin exponer detalles técnicos
- [ ] Error de red (sin conexión) → mostrar mensaje "No se pudo conectar con el servidor"

---

## 7. Páginas de error (Nginx)

- [ ] `404.html` existe y es accesible en `frontend/404.html`
- [ ] `50x.html` existe y es accesible en `frontend/50x.html`
- [ ] 🔗 `docker/nginx/default.conf` incluye:
  ```nginx
  error_page 404 /404.html;
  error_page 500 502 503 504 /50x.html;
  ```
- [ ] Las páginas de error no dependen del backend ni de JS externo
- [ ] Las páginas de error tienen navbar y footer funcionales (para orientar al usuario)
- [ ] La página `50x.html` tiene botón "Reintentar" con `window.location.reload()`

---

## 8. SEO y metadatos

- [ ] Todas las páginas tienen `<title>` único y descriptivo
- [ ] Todas las páginas tienen `<meta name="description">` con contenido relevante
- [ ] `404.html` y `50x.html` tienen `<meta name="robots" content="noindex">`
- [ ] El favicon está referenciado en todas las páginas (`assets/logo.png`)
- [ ] Las páginas de sección de datos tienen Open Graph tags (`og:title`, `og:description`, `og:image`)

---

## 9. Documentación

- [ ] `especificaciones-frontend.md` está actualizado con todas las issues (7B, 7C, 7D, 7F)
- [ ] Las secciones 12.1–12.20 documentan las decisiones técnicas principales
- [ ] El `README.md` del proyecto incluye instrucciones de despliegue con Docker
- [ ] Los comentarios en el código explican el "por qué" (no solo el "qué")
- [ ] Los archivos `404.html` y `50x.html` incluyen comentarios con la configuración de Nginx requerida

---

## 10. Despliegue y configuración Docker

- [ ] 🔗 `docker-compose.yml` levanta correctamente frontend (Nginx) + backend (FastAPI) + base de datos
- [ ] 🔗 `docker/nginx/default.conf` incluye proxy inverso para `/auth/*`, `/solicitudes`, `/estadisticas/*`, `/privado/*`, `/admin/*`
- [ ] 🔗 Las variables de entorno sensibles están en `.env` (no en el repositorio)
- [ ] 🔗 `.gitignore` excluye `.env`, `__pycache__`, `node_modules`, `*.pyc`
- [ ] El frontend es accesible en `http://localhost` tras `docker-compose up`

---

## 11. Pruebas manuales pre-entrega

### Flujos críticos a verificar en el navegador

- [ ] **Flujo de registro completo:** registro → email de verificación → verificación → login
- [ ] **Flujo de reenvío:** registro → enlace expirado → reenvío → nuevo enlace → verificación
- [ ] **Deep link:** acceder directamente a `privado.html` sin sesión → login → aterrizar en `privado.html`
- [ ] **Cambio de contraseña:** contraseña actual incorrecta muestra error; correcta muestra éxito
- [x] **Buscador con filtros:** filtrar por año, tipo, estado, CCAA; paginación funciona con botones compactos
- [x] **Ficha de entidad:** desde buscador → clic en fila → modal inline con historial, expediente, importes y CCAA (cuando disponible)
- [ ] **Error 404:** navegar a `http://localhost/ruta-inexistente` → aparece `404.html`
- [ ] **Error 50x:** parar el backend → navegar a cualquier página con API → aparece `50x.html`
- [ ] **Responsividad:** verificar portada, buscador y estadísticas en Firefox DevTools 375px

### Accesibilidad — prueba con teclado

- [ ] En todas las páginas: Tab hasta el skip-nav → Enter → foco salta al contenido principal
- [ ] En `login.html`: completar formulario solo con teclado → enviar → redirigir a privado
- [ ] En `buscador.html`: usar los filtros y el botón "Buscar" solo con teclado

---

*Generado automáticamente como parte del bloque de tareas 4.11 — Issue 7F (Revisión Final Frontend)*  
*Fecha: mayo 2026 · Proyecto educativo sin fines comerciales*
