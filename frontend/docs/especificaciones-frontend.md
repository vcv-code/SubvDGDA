# Especificaciones Técnicas del Frontend
## Proyecto BDNS/DGDA — Subvenciones de Bienestar Animal

**Proyecto:** Análisis de Subvenciones de Bienestar Animal y Colonias Felinas  
**Curso:** 2º DAW — Proyecto Final de Ciclo  
**Issues cubiertas:** 7B (Estructura HTML/CSS/JS) · 7C (Lógica fetch/filtros/gráficos) · 7D (Mejoras de frontend + reorganización de estadísticas en EPAs y EELL + página Recursos) · 7F (Revisión final: accesibilidad, rendimiento, responsive, limpieza CSS/JS, páginas de error, reenvío de verificación)  
**Depende de:** Issue 7A (Diseño y wireframes, completada)

---

## Índice

1. [Justificación de la stack tecnológica](#1-justificación-de-la-stack-tecnológica)
2. [Estructura de archivos](#2-estructura-de-archivos)
3. [Sistema de diseño](#3-sistema-de-diseño)
4. [Componentes compartidos](#4-componentes-compartidos)
5. [Páginas del sistema](#5-páginas-del-sistema)
6. [Integración con la API REST](#6-integración-con-la-api-rest)
7. [Filtros condicionales del buscador](#7-filtros-condicionales-del-buscador)
8. [Accesibilidad — WCAG 2.1](#8-accesibilidad--wcag-21)
9. [Decisiones de diseño justificadas](#9-decisiones-de-diseño-justificadas)
10. [Pendientes de implementación](#10-pendientes-de-implementación)
11. [Flujo completo de autenticación](#11-flujo-completo-de-autenticación)

---

## 1. Justificación de la stack tecnológica

### Stack elegida
El frontend se ha construido con **HTML5 + CSS3 + JavaScript Vanilla** y **Chart.js** (gráficos). Bootstrap se descartó — el diseño responsive se implementó íntegramente con CSS Grid, Flexbox y variables CSS propias.

### ¿Por qué no se usa React, Vue ni Angular?

Esta decisión se tomó deliberadamente por tres razones:

**Coherencia con el nivel del ciclo.** Un proyecto de 2º DAW debe poder defenderse con los fundamentos del módulo. HTML, CSS y JS son contenidos directos del currículo. Usar un framework de terceros sin dominarlo podría convertirse en un punto débil en la exposición oral.

**Simplicidad en el flujo de trabajo.** Un frontend en React requiere Node.js, un bundler (Vite, Webpack) y un paso de `build` antes de desplegar. Con HTML/CSS/JS puro, el frontend se sirve directamente con Nginx sin ninguna compilación intermedia. Esto simplifica el `docker-compose.yml` y el flujo de ramas (`feature → dev → main`).

**Trazabilidad del código.** Para la memoria del TFG y para la defensa, cada línea de código es directamente legible. No hay transformaciones automáticas ni abstracciones de un framework que oculten la lógica real.

### Ventajas del stack elegido

| Ventaja | Detalle |
|---|---|
| Sin dependencias de build | El frontend funciona abriendo el HTML en el navegador |
| Despliegue directo | Nginx sirve los archivos estáticos sin configuración extra |
| Código defendible | Todo el código es JS estándar, explicable en la exposición |
| Compatibilidad universal | Funciona en cualquier navegador moderno sin transpilación |
| Mantenimiento sencillo | No hay `node_modules` que actualizar ni versiones de framework |

### Chart.js (issue 7C)

Chart.js se importa desde CDN directamente en los HTML que la necesitan, sin instalación local. Bootstrap se evaluó pero se descartó: el diseño responsive se resolvió con CSS Grid y Flexbox propios, evitando dependencias externas innecesarias.

---

## 2. Estructura de archivos

```
frontend/
│
├── css/
│   └── styles.css          → Hoja de estilos compartida por todas las páginas
│
├── js/
│   ├── home.js                  → Lógica de index.html (métricas + gráficos generales con GET /estadisticas/)
│   ├── solicitudes.js           → Lógica del buscador (buscador.html / solicitudes.html)
│   ├── estadisticas-epas.js     → Lógica de estadísticas EPAs (importe medio, distribución, nuevos vs recurrentes, top beneficiarios)
│   ├── estadisticas-eell.js     → Lógica de estadísticas EELL (% ayuntamientos, top provincias, concentración, ranking CCAA)
│   ├── exclusivo.js             → Resumen por convocatoria y mapa CCAA (zona registrada)
│   ├── mapa-ccaa.js             → Mapa choropleth por CCAA con Leaflet (usado por exclusivo.html)
│   ├── entidad.js               → Lógica de la ficha de entidad
│   ├── modal-entidad.js         → Modal de detalle de entidad desde el buscador
│   ├── modal-grafica.js         → Modal de conclusiones de las gráficas
│   ├── admin.js                 → Panel de administración (usuarios, avisos, logs)
│   ├── privado.js               → Control de acceso y contenido de zona privada
│   ├── auth.js                  → Lógica de login y registro (JWT)
│   ├── recuperar-password.js    → Envío del email de recuperación
│   ├── reset-password.js        → Validación y envío de la nueva contraseña
│   ├── contacto.js              → Envío del formulario de contacto (POST /contacto/)
│   ├── navbar.js                → Navbar dinámica compartida por todas las páginas
│   ├── scroll-arriba.js         → Botón flotante "volver arriba" (compartido)
│   └── utils.js                 → Utilidades compartidas (formato de importes, helpers)
│
├── assets/
│   ├── img/
│   │   ├── logo.png            → Logotipo del proyecto (favicon y navbar)
│   │   ├── error404.webp       → Imagen ilustrativa de la página 404
│   │   ├── home/               → Imágenes de portada (handcat.webp y alternativas)
│   │   └── logos/              → Logos de entidades (recursos.html)
│   ├── wireframes/             → Capturas de diseño por pantalla (PNG)
│   └── guia-estilo/            → Paleta, tipografía y PDF de wireframes completos
│
├── index.html               → Página de inicio (Home) — métricas + gráficos generales
├── buscador.html            → Buscador de solicitudes con filtros
├── estadisticas-epas.html   → Estadísticas de Entidades Protectoras de Animales (Issue 7D)
├── estadisticas-eell.html   → Estadísticas de Entidades Locales / Ayuntamientos (Issue 7D)
├── recursos.html            → Directorio de organizaciones y sitios de interés (Issue 7D)
├── exclusivo.html           → Resumen por convocatoria y mapa CCAA (solo usuarios registrados)
├── login.html               → Formulario de inicio de sesión
├── registro.html            → Formulario de creación de cuenta
├── verificar-email.html     → Confirmación del enlace de verificación de email
├── privado.html             → Zona privada / perfil del usuario registrado
├── admin.html               → Panel de administración (solo rol admin)
├── entidad.html             → Ficha de entidad con historial y desglose de agrupaciones
├── recuperar-password.html  → Solicitar enlace de recuperación de contraseña por email
├── reset-password.html      → Establecer nueva contraseña desde el enlace del email
├── contacto.html            → Formulario de contacto (honeypot + rate limiting)
├── aviso-legal.html         → Aviso legal
├── privacidad.html          → Política de privacidad
├── 404.html · 50x.html      → Páginas de error personalizadas servidas por Nginx
├── mantenimiento.html       → Página de mantenimiento programado (503, vía bandera en Nginx)
└── docs/
    ├── diseño.md                    → Guía visual del proyecto (issue 7A)
    └── especificaciones-frontend.md → Este documento
```

### ¿Por qué un JS por página?

Cada página tiene su propio archivo JavaScript en lugar de un único `main.js`. Esto tiene varias ventajas:
- El navegador solo carga el JS necesario para la página actual.
- El código de cada página es independiente y no interfiere con las demás.
- Es más fácil encontrar y depurar un error sabiendo exactamente en qué archivo buscar.

El único CSS compartido (`styles.css`) es la excepción justificada: todos los estilos base, variables y componentes se definen una sola vez para garantizar coherencia visual.

---

## 3. Sistema de diseño

### 3.1 Paleta de colores

Definida como **Custom Properties CSS** en `:root` para que un solo cambio de variable afecte a toda la aplicación.

| Variable CSS | Valor | Uso |
|---|---|---|
| `--color-primario` | `#47C079` | Verde naturaleza — acentos, hover |
| `--color-hover` | `#52E38E` | Verde claro — estado hover de links |
| `--color-fondo-verde` | `#E8F5E9` | Verde suave — fondos de secciones |
| `--color-verde-btn` | `#2E7D32` | Verde oscuro — botones primarios, títulos |
| `--color-azul` | `#1565C0` | Azul institucional — badge Agrupación, spinner, enlace "← Volver al inicio" de páginas legales |
| `--color-gris-claro` | `#F5F5F5` | Fondos de tabla, alternado de filas |
| `--color-gris-medio` | `#E0E0E0` | Bordes de inputs, separadores |
| `--color-gris-texto` | `#616161` | Texto secundario, labels |
| `--color-negro` | `#212121` | Texto principal |

**Colores de estado** (para los badges de la tabla de solicitudes):

| Estado | Color | Justificación |
|---|---|---|
| Concedida | `#2E7D32` (verde) | Verde = positivo, favorable |
| No beneficiaria | `#C62828` (rojo) | Rojo = denegado |
| Excluida | `#EF6C00` (naranja) | Naranja = advertencia |
| Desistida | `#6A1B9A` (morado) | Morado = neutral/inactivo |

Esta codificación de colores por estado facilita la lectura rápida de la tabla sin necesidad de leer el texto.

### 3.2 Tipografía

**Fuente:** Inter (Google Fonts) — pesos 400 (normal), 600 (semibold), 700 (bold).

**¿Por qué Inter?** Es una fuente de código abierto diseñada específicamente para interfaces digitales. Tiene excelente legibilidad a tamaños pequeños (14px en tablas) y a tamaños grandes (títulos). Es la fuente estándar en muchos dashboards profesionales.

| Elemento | Tamaño | Peso |
|---|---|---|
| Título principal (H1) | 2.6 rem | 700 |
| Títulos de sección (H2) | 1.8 rem | 700 |
| Subtítulos (H3) | 1.1 rem | 700 |
| Texto normal (p) | 1 rem (16px) | 400 |
| Texto de tabla (td) | 0.9 rem (14px) | 400 |
| Texto pequeño (labels, badges) | 0.78–0.85 rem | 400–600 |

### 3.3 Sistema de espaciado

Se usa una escala basada en **múltiplos de 8px**. Esta escala es estándar en diseño de interfaces (Google Material Design, Apple HIG) y produce resultados visuales armoniosos.

| Variable | Valor | Uso típico |
|---|---|---|
| `--espacio-xs` | 8px | Gap mínimo, padding de badges |
| `--espacio-sm` | 16px | Padding de inputs, gap entre botones |
| `--espacio-md` | 24px | Padding de cards |
| `--espacio-lg` | 32px | Padding horizontal del contenedor |
| `--espacio-xl` | 48px | Padding vertical de secciones |

### 3.4 Bordes y sombras

| Variable | Valor | Uso |
|---|---|---|
| `--radio-btn` | 8px | Bordes redondeados de botones |
| `--radio-card` | 12px | Bordes redondeados de tarjetas |
| `--radio-input` | 6px | Bordes redondeados de inputs |
| `--sombra-card` | `0 2px 8px rgba(0,0,0,0.08)` | Sombra sutil de tarjetas |
| `--sombra-nav` | `0 2px 6px rgba(0,0,0,0.1)` | Sombra del navbar |

---

## 4. Componentes compartidos

### 4.1 Navbar

Barra de navegación fija (`position: fixed`) de 80px de altura. Fondo verde oscuro institucional `#1A3429` en **todas las páginas**. Contiene el logo y el nombre **"Subvenciones DGDA"** a la izquierda (texto blanco, logo con `drop-shadow` sutil) y los enlaces de navegación a la derecha en blanco semitransparente. El enlace de la página actual recibe la clase `activo` que aplica blanco puro y subrayado CTA verde (`#2DC26C`); también se añade `aria-current="page"` para accesibilidad.

El botón "Acceder" / "Cerrar sesión" tiene estilo pill (`border-radius: 50px`, fondo `#2DC26C`, texto blanco) para destacarlo visualmente. Cuando hay sesión activa, `navbar.js` sustituye "Acceder" por "Mi perfil" (`.navbar__user-link`) + "Cerrar sesión" (`.btn-login` como `<button>`).

**Diseño visual unificado (Sesión 2026-05-17):**

| Elemento | Valor |
|---|---|
| Fondo | `#1A3429` (`--nav-oscuro`) |
| Logo imagen | Sin filtro de inversión; `drop-shadow` para contraste |
| Logo texto | `#FFFFFF` |
| Links | `rgba(255,255,255,0.80)` → hover `#FFFFFF` |
| Borde activo | `border-bottom: 2px solid #2DC26C` |
| Botón CTA | `background: #2DC26C`, pill `border-radius: 50px` |
| Contraste WCAG | Texto blanco sobre `#1A3429` > 7:1 ✔ |

**Estructura del navbar — Opción A, 6 enlaces directos:**

| Posición | Enlace | Destino | Clase especial |
|---|---|---|---|
| 1 | Inicio | `index.html` | `activo` en home |
| 2 | Buscador | `buscador.html` | `activo` en buscador |
| 3 | EPAs | `estadisticas-epas.html` | `activo` en EPAs |
| 4 | EELL | `estadisticas-eell.html` | `activo` en EELL |
| 5 | Recursos | `recursos.html` | `activo` en recursos |
| 6 | Acceder | `login.html` | `.btn-login` (pill verde) |

Todas las páginas del proyecto comparten este navbar unificado. El patrón de accesibilidad (`role="navigation"`, `aria-label`, `aria-current="page"`) se mantiene uniforme.

### 4.2 Footer

Footer en dos zonas, con fondo verde oscuro institucional `#1A3429` en **todas las páginas**, espejo visual del navbar:

- **Zona principal** (`#1A3429`): logo del proyecto (sin filtros de inversión, con `drop-shadow` sutil) a la izquierda; nombre **"Proyecto BDNS/DGDA"** en blanco puro `#FFFFFF`; enlaces GitHub / Aviso legal / Privacidad a la derecha en blanco semitransparente. Sin borde superior visible.
- **Zona de créditos** (`#142b20`): crédito de los datos (BDNS y DGDA) y aviso de proyecto educativo en texto blanco tenue.

| Elemento | Valor |
|---|---|
| Fondo zona principal | `#1A3429` |
| Fondo zona créditos | `#142b20` |
| Nombre proyecto (`<strong>`) | `#FFFFFF` — contraste máximo |
| Texto general | `rgba(255,255,255,0.88)` — WCAG AA > 7:1 |
| Texto créditos | `rgba(255,255,255,0.52)` |
| Logo | `drop-shadow` sutil, `height: 40px`, sin filtros de inversión |
| Borde superior | Ninguno |

**Sticky footer:** El footer siempre aparece al pie de la ventana, incluso cuando el contenido es corto. Se consigue con `display: flex; flex-direction: column; min-height: 100vh` en el `body` y `flex: 1` en `main`.

### 4.3 Tarjetas (Cards)

Se usan tres variantes de tarjeta:

- **`.card`** — tarjeta base: fondo blanco, sombra suave, bordes redondeados.
- **`.card-metrica-verde`** — tarjeta de métrica: fondo verde suave, número grande y label encima.
- **`.card-anio`** — tarjeta de convocatoria por año: año en grande, estado "Cerrada", líneas EPA/EELL con importe y enlace a resultados.

### 4.4 Badges de estado, agrupación y tramo

**Badges de estado de solicitud** — pequeñas etiquetas de color para los valores de estado. Se aplican con las clases `.badge-concedida`, `.badge-no-beneficiaria`, `.badge-excluida` y `.badge-desistida`. Los colores están justificados en la sección 3.1.

**Badge de agrupación** (Issue 7D) — etiqueta azul institucional que aparece junto al nombre de la entidad en el buscador cuando `s.es_agrupacion === true`. Se implementa con la clase `.badge-agrupacion`:

```css
.badge-agrupacion {
    background-color: var(--color-azul);
    color: white;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.75rem;
    margin-left: 6px;
}
```

En `crearFila()` de `solicitudes.js`, la celda de nombre se construye con `createTextNode` (nombre) más el `<span class="badge-agrupacion">Agrupación</span>` añadido condicionalmente. No se usa `innerHTML` para no exponer el nombre de la entidad a posible inyección HTML.

**Badge de tramo** (rama 10a) — etiqueta marrón oscuro que aparece junto al nombre en el buscador y junto al importe en la ficha de entidad cuando `s.tramo !== null`. Muestra `T1`, `T2` o `T3` según la población del municipio (tramos definidos en la resolución DGDA). Solo aplica a EELL 2025 concedidas. Clase `.badge-tramo`.

Junto con el badge, aparece una **leyenda de tramos** encima de la tabla (oculta si no hay resultados con tramo): `T1 ≤ 10.000 hab. · T2 10.001–50.000 hab. · T3 > 50.000 hab.`

### 4.5 Grids

Se usan dos grids CSS para distribuir tarjetas:

- **`.grid-3`** — 3 columnas en escritorio, 2 en tablet (≤900px), 1 en móvil (≤600px).
- **`.grid-2`** — 2 columnas en escritorio, 1 columna en tablet y móvil (≤768px).

Los breakpoints son: 900px (tablet para `.grid-3`), 768px (tablet/móvil para `.grid-2`) y 600px (móvil para `.grid-3`). `.grid-2` colapsa antes que `.grid-3` para evitar que dos columnas de contenido denso (tablas, tarjetas anchas) queden aplastadas en dispositivos medianos.

### 4.6 Auth Page (páginas de autenticación)

`login.html` y `registro.html` usan una **card partida en dos columnas** (split card) combinando dos referencias de diseño: la identidad visual del proyecto en el panel izquierdo, y la claridad institucional del **GOV.UK Design System** en el formulario derecho.

Estructura HTML:

```
.auth-fondo              → fondo verde suave (#E8F5E9), centra la card
  .auth-page             → max-width 920px
    .auth-page__servicio → enlace "← Subvenciones Bienestar Animal"
    .auth-card           → CSS Grid 45% / 55%, border-radius 20px
      .auth-card__imagen → columna izquierda: fondo #f0f5f1
        .auth-card__circulo   → círculo 300×300px verde oscuro, centrado
        .auth-card__blob      → blob 160×160px verde claro, esquina inf-der
        img.auth-card__foto   → foto animales centrada (88%), z-index: 1
      .auth-card__formulario → columna derecha: formulario
        h1.auth-card__titulo
        p.auth-card__subtitulo
        .auth-alerta          → alerta error/éxito (oculta por defecto)
        form
          .grupo-campo        → label + input + error en columna
            .etiqueta-campo   → label en negrita
            .input-campo      → input borde 2px negro
            .campo-error      → error (visible con clase .visible)
        .auth-card__enlace
        [sin botones sociales]
```

**Decisiones de diseño clave:**

| Elemento | Decisión | Justificación |
|---|---|---|
| Panel izquierdo con imagen | Identidad visual del proyecto | Comunica la temática (bienestar animal) de forma inmediata |
| Fondo verde suave `#E8F5E9` | Paleta del proyecto | Coherente con el resto de páginas (estadísticas, home) |
| Labels encima del input | Posición fija | Mejora usabilidad y legibilidad (GOV.UK, WCAG 1.3.1) |
| Inputs borde 2px negro | Alto contraste | Supera 3:1 en ratio de contraste, claro en cualquier contexto |
| Foco: outline 3px verde | Visible para teclado | WCAG 2.1 criterion 2.4.7 (Focus Visible) |
| Errores: borde izquierdo rojo | Patrón GOV.UK | Localiza el error sin depender solo del color (WCAG 1.4.1) |
| Imagen oculta en móvil | Responsive | Simplifica la UI en pantallas pequeñas |

### 4.7 Indicadores de contraseña en tiempo real

En `registro.html`, cuatro elementos `.password-req` muestran si cada requisito se cumple. Cuando el usuario escribe, `auth.js` añade o quita la clase `ok` en cada indicador con el evento `input`. El CSS convierte el punto `·` en una marca `✓` verde al añadir la clase `ok`. Los indicadores tienen `aria-live="polite"` para ser accesibles con lector de pantalla.

### 4.8 Spinners de carga (Issue 7D)

Todas las páginas que realizan peticiones `fetch` tienen un spinner visual que aparece antes de la petición y desaparece en el bloque `finally`.

**HTML** (presente en `buscador.html`, `entidad.html`, `index.html`, `recursos.html`, `estadisticas-epas.html` y `estadisticas-eell.html`):

```html
<div id="spinner" class="spinner"></div>
```

**CSS:**

```css
.spinner {
    display: none;
    margin: 20px auto;
    border: 4px solid #ddd;
    border-top: 4px solid var(--color-azul);
    border-radius: 50%;
    width: 32px;
    height: 32px;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
```

**Patrón JS** (idéntico en los cuatro archivos):

```javascript
async function cargarDatos() {
    document.getElementById('spinner').style.display = 'block';
    try {
        // ... fetch ...
    } catch (error) {
        // ...
    } finally {
        document.getElementById('spinner').style.display = 'none';
    }
}
```

### 4.9 Caja de error visual (Issue 7D)

Cuando el backend devuelve un código de error HTTP (401, 403, 404, 422, 500), el frontend muestra una caja de error estructurada con los campos `mensaje` y `sugerencia` del JSON de error del backend.

**HTML** (presente en `buscador.html`, `entidad.html`, `index.html`, `recursos.html`, `estadisticas-epas.html` y `estadisticas-eell.html`):

```html
<div id="error-box" class="error-box" style="display:none;">
    <h3>Error</h3>
    <p id="error-mensaje"></p>
    <p id="error-sugerencia"></p>
</div>
```

**CSS:**

```css
.error-box {
    background: #ffe5e5;
    border: 1px solid #ff8a8a;
    padding: 16px;
    border-radius: 6px;
    margin-top: 20px;
}
```

**Patrón JS** (idéntico en los cuatro archivos JS):

```javascript
if (!respuesta.ok) {
    let cuerpo = {};
    try { cuerpo = await respuesta.json(); } catch (_) {}
    document.getElementById('error-mensaje').textContent    = cuerpo.mensaje    || `Error ${respuesta.status}`;
    document.getElementById('error-sugerencia').textContent = cuerpo.sugerencia || '';
    document.getElementById('error-box').style.display      = 'block';
    throw new Error(`Error ${respuesta.status}`);
}
```

El backend devuelve siempre este formato en caso de error:

```json
{
  "error": 404,
  "mensaje": "Recurso no encontrado",
  "sugerencia": "Comprueba la URL o los parámetros de la petición"
}
```

---

### 4.10 Botón "volver arriba"

Botón flotante (`js/scroll-arriba.js` + clase `.btn-subir`) que permite regresar al inicio en las páginas largas. Componente compartido, igual filosofía que el navbar: un único script cargado en las **12 páginas con navbar** (contenido), justo después de `navbar.js`.

| Elemento | Valor |
|---|---|
| Posición | `position: fixed; bottom: 1.5rem; right: 1.5rem` |
| Forma | Círculo de 3rem, fondo `var(--color-verde-btn)`, flecha ↑ blanca |
| `z-index` | `1100` — por debajo de modales (2000/9999) y navbar (1200), por encima del contenido |
| Visibilidad | Oculto por defecto (`opacity: 0; visibility: hidden`); `scroll-arriba.js` añade `.btn-subir--visible` al superar **600px** de scroll |
| Scroll | `window.scrollTo({ top: 0 })`; el suavizado lo aporta `scroll-behavior: smooth` del `<html>` |

**Por qué no hace falta decidir página por página:** como solo aparece tras 600px de scroll, en las páginas cortas (login, error, ficha de entidad…) nunca llega a mostrarse aunque el script esté cargado. El umbral se recalcula dentro de un `requestAnimationFrame` (listener de scroll `passive`) para no penalizar el desplazamiento.

**Accesibilidad:** `aria-label="Volver al principio de la página"`, foco visible (`:focus-visible` con `outline` verde WCAG) y respeto de `prefers-reduced-motion` (sin transición ni desplazamiento del botón al aparecer).

---

## 5. Páginas del sistema

### 5.1 Home — `index.html`

**Propósito:** Presentar el proyecto, mostrar las cifras clave y dar acceso rápido a las herramientas principales. Desde Issue 7D también alberga los gráficos de evolución temporal que antes estaban en `estadisticas.html`.

**Cambios en Issues 7C/7D:**
- Favicon configurado con `<link rel="icon" href="assets/logo.png">`.
- Metadatos Open Graph (`og:title`, `og:description`, `og:image`) añadidos en el `<head>`.
- KPI "Entidades únicas" conectado con el dato real de la API (`datos.entidades_unicas`).
- Botón hero renombrado a "Ir al buscador" enlazando a `buscador.html`.
- Spinner de carga sobre las métricas.
- Caja de error visual si el backend no responde.
- **Nueva sección de gráficos** con fondo verde (`fondo-stats`), usando el endpoint existente `GET /estadisticas/`.

**Secciones:**

| Sección | Contenido | Datos |
|---|---|---|
| Portada partida | Título "Sobre el proyecto" + descripción + foto de animales + botón "Ir al buscador" | Estático |
| Datos y métricas | 3 tarjetas: total solicitudes, importe concedido, entidades únicas | API `/estadisticas/` |
| Convocatorias | Dos bloques (EELL / EPA) con año, fecha de convocatoria (BOE) y acceso rápido al buscador filtrado; pendientes sin `fecha_resolucion` muestran estado | API `/convocatorias/` |
| Gráficos | Fila 1: Evolución importe por año (línea) + EPA vs EELL por año (barras agrupadas). Fila 2: Distribución estados (donut) + KPI tasa de éxito | API `/estadisticas/` |

Las secciones "Convocatorias recientes" y "Transparencia" se eliminaron para simplificar la página y centrar el foco en los datos clave.

**Gráficos implementados en `js/home.js`:**

| Función | Tipo Chart.js | Canvas ID | Datos |
|---|---|---|---|
| `crearGraficoLinea(porAnio)` | `line` | `home-grafico-linea` | Suma EPA+EELL de `por_anio` |
| `crearGraficoDonut(datos)` | `doughnut` + `cutout: '62%'` | `home-grafico-donut` | Totales concedidas / resto |
| `crearGraficoBarras(porAnio)` | `bar` agrupado | `home-grafico-barras` | `por_anio` separado por tipo |
| `mostrarTasaExito(datos)` | KPI HTML | `home-tasa-exito` | `total_concedidas / total_registros` |

**Archivo JS:** `js/home.js` — tres funciones asíncronas independientes: `cargarDatos()` (métricas + gráficos desde `/estadisticas/`), `cargarAvisos()` (banner desde `/avisos/`) y `cargarConvocatorias()` (bloque convocatorias desde `/convocatorias/`).

### 5.2 Buscador — `buscador.html`

**Propósito:** Filtrar y consultar las solicitudes de subvención de la base de datos.

**Cambios en Issue 7D:**
- La columna **Expediente** se sustituyó por la columna **Año** en la tabla de resultados.
- El orden inicial de los resultados es **Entidad (A → Z)**; eliminada la opción "Por defecto" del selector de orden.
- Badge **"Agrupación"** (azul) aparece junto al nombre de la entidad cuando `es_agrupacion === true`.
- Botón **"↓ Descargar CSV"** en la barra `tabla-controles` (junto al selector de orden), visible solo cuando hay resultados.

**Filtros disponibles:**

La búsqueda por nombre se realiza server-side. El backend implementa el parámetro `?buscar=`; se ha eliminado el `.filter()` client-side de versiones anteriores.

| Filtro | Tipo | Soportado por API | Condición de visibilidad |
|---|---|---|---|
| Nombre de entidad | Texto libre | ✔ `?buscar=` | Siempre visible |
| Año | Select (2021–2025) | ✔ | Siempre visible |
| Tipo | Select (EPA / EELL) | ✔ | Siempre visible |
| Estado | Select (4 valores) | ✔ | Siempre visible |
| CCAA | Select (17 CCAA) | ✔ `?ccaa=` | Solo si Tipo = EELL |
| Provincia | Texto libre | ✔ `?provincia=` | Solo si Tipo = EELL |
| Línea de actuación | Select (2 valores) | ✔ `?linea=` | Solo si Tipo = EPA y Año = 2025 |

**Tabla de resultados — columnas:**

| Columna | Fuente del dato | Notas |
|---|---|---|
| Entidad | `s.beneficiario.nombre` | Puede incluir badge "Agrupación" |
| Año | `s.convocatoria.anio_convocatoria` | Sustituye a "Expediente" desde Issue 7D |
| Tipo | `s.convocatoria.tipo_convoc` | "epa" → "EPA" |
| Estado | `s.estado` | Badge de color (verde/rojo/naranja/morado) |
| Importe (€) | `s.importe` | `—` si es null |

**Control de orden:** encima de la tabla aparece `.tabla-controles` con el recuento de resultados a la izquierda y a la derecha el selector de orden y el botón de exportación. Opciones de orden: Entidad (A → Z), Importe mayor → menor, Importe menor → mayor. La ordenación es **server-side**: el parámetro `?orden=` se envía al backend, que aplica `ORDER BY` en SQL antes del `OFFSET`/`LIMIT`, garantizando que el orden sea correcto a través de todas las páginas. Cambiar el selector relanza la búsqueda desde la página 1.

**Exportación CSV:** el botón "↓ Descargar CSV" llama a `GET /solicitudes/export` con todos los filtros activos (`buscar`, `tipo`, `anio`, `estado`, `ccaa`, `provincia`, `linea`) —sin `pagina` ni `limite`—. El backend genera el CSV completo; el frontend lo recibe como `Blob` y dispara la descarga mediante un `<a download>` temporal con un nombre de archivo dinámico que refleja los filtros activos:

- Sin filtros → `solicitudes.csv`
- Con filtros → `solicitudes_[tipo]_[anio]_[estado]_[ccaa].csv` (ej: `solicitudes_epa_2024_concedida.csv`)

La CCAA se normaliza (sin tildes, espacios como guión bajo). Si el backend devuelve 400 (demasiados resultados), se muestra el mensaje de error en la tabla en lugar de redirigir a una página en blanco. El CSV incluye la columna `tramo` (rama 10a).

**Paginación:** 50 resultados por página. Parámetros `limite` y `pagina` en la URL de la API.

**Modal de entidad:** al hacer clic en cualquier fila se abre un modal inline (`modal-entidad.js`) con la ficha resumida de la entidad (nombre, CIF, CCAA, total recibido, nº solicitudes e histórico por año) sin abandonar el buscador. El pie del modal incluye el enlace "Ver página completa →" que abre `entidad.html?cif=...` en una pestaña nueva, permitiendo compartir o guardar la URL de una entidad concreta.

**Persistencia de filtros en URL** (rama 10a): al ejecutar una búsqueda, los filtros activos —incluido el criterio de orden— se escriben como parámetros en la URL de la página (`buscador.html?tipo=eell&anio=2025&estado=concedida&orden=importe-desc`). Al volver desde la ficha de entidad, el botón "Volver al buscador" usa `history.back()`, lo que restaura la URL con parámetros y relanza la búsqueda automáticamente. Al limpiar filtros, la URL vuelve a `buscador.html` sin parámetros. El evento `popstate` (botón Atrás del navegador) tiene el mismo comportamiento. El criterio `entidad-az` (por defecto) no se escribe en la URL para no añadir ruido.

`sincronizarUrl()` usa `history.replaceState` (no `pushState`) para evitar añadir entradas duplicadas al historial del navegador — con `pushState`, llegar al buscador desde un enlace de convocatoria requería pulsar Atrás dos veces para volver a Home.

La página también acepta parámetros en la URL al llegar desde enlaces externos (`?anio=2025`, `?tipo=eell`, etc.) — compatible con los enlaces de la Home.

**Archivo JS:** `js/solicitudes.js`.

### 5.3 Estadísticas generales → integradas en Home (Issue 7D)

**Decisión de arquitectura:** En la reorganización de Issue 7D se eliminó `estadisticas.html` como página independiente. Los gráficos generales de evolución temporal se integraron directamente en `index.html`, donde el usuario los ve en su primera visita sin necesidad de navegar a una sección separada. Los análisis específicos de EPA y EELL se trasladaron a páginas propias (`estadisticas-epas.html` y `estadisticas-eell.html`).

**Archivos eliminados:** `estadisticas.html` y `js/estadisticas.js` (se pueden eliminar con `git rm`).

**Qué sustituye a cada elemento de `estadisticas.html`:**

| Contenido anterior en `estadisticas.html` | Nuevo destino |
|---|---|
| KPIs: total registros, importe global, entidades únicas, % concedido | `index.html` (métricas) |
| Gráfico de evolución del importe por año (línea) | `index.html` (nueva sección gráficos) |
| Gráfico de distribución por estado (donut) | `index.html` (nueva sección gráficos) |
| Gráfico EPA vs EELL por año (barras agrupadas) | `index.html` (nueva sección gráficos) |
| Análisis por EPA: importes, beneficiarios, distribución | `estadisticas-epas.html` |
| Análisis por EELL: ayuntamientos, provincias, CCAA | `estadisticas-eell.html` |

**Librería:** Chart.js 4.4.0 importada desde CDN jsDelivr en las páginas que la usan (`index.html`, `estadisticas-epas.html`, `estadisticas-eell.html`).

### 5.4 Ficha de entidad — `entidad.html` + `js/entidad.js`

**Propósito:** Mostrar el historial completo de participación de una entidad en todas las convocatorias. Accesible desde el enlace "Ver página completa →" del modal del buscador o directamente por URL (`entidad.html?cif=...`), lo que permite compartir o marcar como favorito la ficha de una entidad concreta.

**Cambios en Issue 7D:** desglose de municipios para solicitudes que pertenecen a una agrupación EELL.

**Contenido de la página (orden visual):**
- Nombre de la entidad y CIF
- Leyenda de tramos (oculta si ninguna solicitud tiene tramo)
- Tabla de historial con: Año de convocatoria, Tipo (EPA/EELL), Estado (badge de color), Importe concedido + badge tramo, Número de expediente
- Bloque `#agrupacion-detalle` (oculto por defecto, visible debajo de la tabla si hay agrupación)

**Bloque de desglose de agrupación (`#agrupacion-detalle`):**

Aparece debajo de la tarjeta de datos principales cuando alguna solicitud del historial tiene `es_agrupacion === true`. La lógica está en `entidad.js`:

```javascript
solicitudes.forEach(s => {
    // ... pintar fila de la tabla ...
    if (s.es_agrupacion === true) {
        cargarAgrupacion(s.id_solic);
    }
});
```

La función `cargarAgrupacion(idSolic)` llama a `GET /agrupaciones/{id_solic}` y rellena:

- `#agrupacion-representante` → `datos.representante.nombre` (el campo `representante` es un objeto `BeneficiarioOut`; usar `.nombre` evita el bug `[object Object]`)
- `#agrupacion-num-municipios` → `datos.num_municipios`
- `#agrupacion-miembros > tbody` → lista de miembros con `nombre`, `cif` e `importe_asignado` (campo correcto del schema; no `importe`)

Si el endpoint devuelve error o aún no está disponible, el bloque queda oculto sin romper la página (error silencioso en `catch`).

**Estructura del bloque HTML:**

```html
<div id="agrupacion-detalle" class="agrupacion-detalle" style="display:none;">
    <h3>Municipios de la agrupación</h3>
    <p id="agrupacion-representante"></p>
    <p id="agrupacion-num-municipios"></p>
    <table id="agrupacion-miembros">
        <thead>
            <tr>
                <th>Nombre</th>
                <th>CIF</th>
                <th>Importe asignado (€)</th>
            </tr>
        </thead>
        <tbody></tbody>
    </table>
</div>
```

**Flujo de navegación:**
1. El usuario hace clic en una fila de `buscador.html`.
2. El JS redirige a `entidad.html?cif=XXXXXXXXX`.
3. `entidad.js` lee el parámetro `cif` y llama a `GET /solicitudes/?cif=`.
4. Se pinta la tabla con todas las solicitudes de esa entidad.
5. Si alguna solicitud tiene `es_agrupacion === true`, se llama a `GET /agrupaciones/{id_solic}` y se muestra el desglose.

**Estados visuales implementados:**
- Cargando… (con spinner)
- Error al cargar datos (caja `.error-box`)
- Entidad sin solicitudes
- Tabla con historial
- Bloque de municipios de agrupación (condicional)

### 5.5 Recursos — `recursos.html`

**Propósito:** Directorio estático de organizaciones, iniciativas y campañas relevantes en materia de protección animal, gestión ética de colonias felinas, fauna urbana y movimientos actuales. Esta página no depende del backend: todo el contenido procede del documento funcional entregado por el equipo y se integra directamente en HTML.

**Estado:** Contenido implementado (Issue 7D/7E). En proceso de ajuste visual. No existe `recursos.js` activo: no hay fetch ni lógica dinámica.

**Cambios visuales aplicados (rama 10a):**
- Logos uniformes: `height: 80px; object-fit: contain` en `.card-entidad img`. Eliminado `width="200"` hardcodeado.
- Orden de la tarjeta cambiado con CSS `order`: nombre → logo → descripción.
- Categoría/subtítulo oculto (`display: none`).
- Todo el contenido centrado (`text-align: center` en `.card-entidad`).

**Pendientes de mejora visual** *(página en proceso de ajuste)*:
- Color de fondo diferente para cada uno de los 4 bloques — referencia: panel de nueva pestaña de la usuaria.
- Decidir si eliminar definitivamente la categoría del HTML o mostrarla en otro formato.
- Ajustar altura del logo (80px) si algún logo queda demasiado pequeño o grande.
- Revisar aspecto general de las tarjetas una vez aplicados los colores por sección.

**Estructura visual:**

- **Grid responsive:**  
  - 3 columnas en escritorio (≥1024px)  
  - 2 columnas en tablet (≥768px)  
  - 1 columna en móvil  
- **Tarjetas:** cada entidad se representa con:
  - logo oficial (enlace externo)  
  - nombre  
  - categoría o ámbito (si aplica)  
  - descripción breve  
- **Navbar y footer:** se mantienen sin cambios.  
- **Contenido 100% estático:** sin dependencias del backend.

---

#### Optimización de imágenes — Issue 7E

**Directorio:** `assets/img/logos/`  
**Formato:** WebP

**Parámetros de conversión (Squoosh / cwebp):**

| Parámetro | Valor |
|---|---|
| Anchura máxima | 512 px (proporción preservada) |
| Calidad | 75–80 |
| Reducir paleta | Activado |
| Effort | 5 |

**Patrón de integración en `<article class="card-entidad">`:**

```html
<article class="card-entidad">
    <a href="https://url-oficial.org/" target="_blank" rel="noopener noreferrer">
        <img src="assets/img/logos/nombre-entidad.webp"
             alt="Logo Nombre Entidad"
             width="200"
             loading="lazy">
    </a>
    <p class="card-entidad__nombre">Nombre Entidad</p>
    <p class="card-entidad__categoria">Categoría</p>
    <p class="card-entidad__descripcion">Descripción breve.</p>
</article>
```

**Reglas aplicadas:**

- `<img>` siempre como primer hijo del `<article>`, dentro de `<a>`.
- Solo el logo es enlace; el resto de la tarjeta no es interactivo.
- Atributo `width="200"` únicamente — sin `height` para evitar deformación.
- `loading="lazy"` en todos los logos (rendimiento en página larga).
- `alt` con patrón `"Logo Nombre"` (accesibilidad).
- `target="_blank"` + `rel="noopener noreferrer"` en todos los enlaces externos.
- Sin estilos inline; sin contenedores adicionales alrededor del `<a>`.

---

#### Bloque 1 — Protección animal

Entidades de referencia en bienestar animal, activismo, apoyo a protectoras y operadores jurídicos:

| Entidad | Archivo logo | URL oficial |
|---|---|---|
| BASMA | `basma.webp` | https://piensosolidariobasma.org/ |
| FAADA | `logo-faada.webp` | https://faada.org/ |
| Animanaturalis | `logo-animaNaturalis.webp` | https://www.animanaturalis.org/ |
| Intercids | `Logo-Intercids-c.webp` | https://intercids.com/ |
| APDDA | `logo-apdda.webp` | https://apdda.es/ |
| AVATMA | `avatma-negativo-solo-logo.webp` | https://avatma.es/ |

---

#### Bloque 2 — Colonias felinas

Organizaciones y plataformas centradas en CER, gestión ética y divulgación:

| Entidad | Archivo logo | URL oficial |
|---|---|---|
| GEMFE | `logo-gemfe.webp` | https://gemfe.es/ |
| Plataforma GARRA | `logo-plataformaGarra.webp` | https://plataformagarra.es/ |
| Los gatos tienen ley | `Logo-losGatosTienenLey.webp` | https://losgatostienenley.es/ |
| FDCats | `logo-fdcats.webp` | https://fdcats.es/ |
| Los 4 de la Empandilla | `logo-losCuatroDeLaEmpandilla.webp` | https://los4delaempandilla.org/ |
| MeowMetrics | `logo-meowMetrics.webp` | https://meowmetrics.app/ |

---

#### Bloque 3 — Entidades especializadas

Organizaciones centradas en fauna urbana, silvestre o especies concretas:

| Entidad | Archivo logo | URL oficial |
|---|---|---|
| Plataforma Cotorras | `logo-pCotorras.webp` | https://plataformacotorras.es/ |
| Free Fox | `logo-freeFox.webp` | https://freefox.es/ |
| GREFA | `logo-grefa.webp` | https://grefa.org/ |
| Asociación EriSOS | `logo-erisos.webp` | https://erisos.org/ |
| SOS Vencejos | `logo-sosvencejos.webp` | https://sosvencejos.es/ |
| MALP | `logoMALP.webp` | https://misamigaslas palomas.es/ |

---

#### Bloque 4 — Campañas actuales

Movimientos, iniciativas legales y casos recientes de relevancia pública:

| Entidad | Archivo logo | URL oficial |
|---|---|---|
| Vets Unidos | `Logo-vetsUnidos.webp` | https://vetsunidos.es/ |
| Mismos perros, misma ley | `logo-mismosPerros.webp` | https://mismosperros.es/ |
| Santuarios no son granjas | `logo-santuariosNoGranjas.webp` | https://santuariosnosongranigas.es/ |
| La tortura no es cultura | `logo-torturaNoCultura.webp` | https://latorturanoecultura.es/ |
| Vivotecnia | `logo-vivotecnia.webp` | https://vivotecnia.es/ |
| Plataforma NAC | `logo-nac.webp` | https://noalacaza.es/ |

---

**Notas de implementación:**
- La página sustituye la versión previa que contenía únicamente enlaces básicos.
- Se mantiene coherencia visual con el resto del proyecto (tipografías, espaciados, estructura de secciones).
- Los logos WebP están en `assets/img/logos/`; no se requiere subdirectorio adicional por bloque.
- Las URLs oficiales de la tabla son aproximadas; verificar antes de publicar en producción.


---

### 5.6 Estadísticas EPAs — `estadisticas-epas.html` + `js/estadisticas-epas.js` (Issue 7D)

**Propósito:** Análisis específico de las convocatorias de Entidades Protectoras de Animales: importe medio, mediana, beneficiarios únicos, nuevas entidades, distribución de importes por rangos, media vs mediana por año, nuevos vs recurrentes y top beneficiarios.

**Estado:** Completamente implementada y conectada al backend. Endpoint `GET /estadisticas/epas` disponible.

**Fondo visual:** usa la clase `.fondo-stats` (verde suave). Enlace "→ Ver estadísticas EELL" en la cabecera.

**Estructura HTML:**

| Bloque | ID | Descripción |
|---|---|---|
| Spinner | `#spinner` | Patrón estándar del proyecto |
| Caja de error | `#error-box` | Patrón estándar del proyecto |
| KPIs | `.grid-4` | 4 tarjetas de métricas EPA |
| Distribución de importes | `#grafico-distribucion-importes` | Canvas oculto + placeholder |
| Media vs mediana por año | `#grafico-media-mediana` | Canvas oculto + placeholder |
| Nuevos vs recurrentes | `#grafico-nuevos-recurrentes` | Canvas oculto + placeholder |
| Top beneficiarios | `#grafico-top-beneficiarios` | Canvas oculto + placeholder |

**KPIs (pendientes de datos):**

| ID | Label | Dato esperado |
|---|---|---|
| `#kpi-importe-medio` | Importe medio EPA | `datos.importe_medio` |
| `#kpi-mediana` | Mediana del importe | `datos.mediana` |
| `#kpi-beneficiarios-unicos` | Beneficiarios únicos | `datos.beneficiarios_unicos` |
| `#kpi-nuevas-entidades` | Nuevas entidades | `datos.nuevas_entidades` |

**Gráficos preparados en `estadisticas-epas.js`:**

| Función | Tipo Chart.js | Canvas | Datos |
|---|---|---|---|
| `poblarGraficoDistribucion(distribucion)` | `bar` vertical | `grafico-distribucion-importes` | `[{rango, cantidad}]` |
| `poblarGraficoMediaMediana(porAnio)` | `bar` agrupado, 2 datasets | `grafico-media-mediana` | `porAnio[].media`, `porAnio[].mediana` |
| `poblarGraficoNuevosRecurrentes(porAnio)` | `bar` apilado (`stack: 'entidades'`) | `grafico-nuevos-recurrentes` | `porAnio[].nuevos`, `porAnio[].recurrentes` |
| `poblarGraficoTopBeneficiarios(porAnio)` | `bar` horizontal (`indexAxis: 'y'`) | `grafico-top-beneficiarios` | `porAnio[último].top_beneficiarios` |

**Endpoint `GET /estadisticas/epas`:**

```json
{
  "importe_medio":         number,
  "mediana":               number,
  "beneficiarios_unicos":  number,
  "nuevas_entidades":      number,
  "distribucion_importes": [{ "rango": string, "cantidad": number }, ...],
  "por_anio": [
    {
      "anio":              number,
      "media":             number,
      "mediana":           number,
      "nuevos":            number,
      "recurrentes":       number,
      "top_beneficiarios": [{ "nombre": string, "importe": number }, ...]
    }, ...
  ]
}
```

**Notas de implementación:**

- La mediana se calcula en Python con `statistics.median` (MariaDB no tiene función nativa equivalente).
- `nuevas_entidades` = beneficiarios cuya primera concesión es el año más reciente con datos.
- `nuevos`/`recurrentes` por año se calculan comparando contra el primer año de concesión histórico de cada beneficiario.
- Rangos de distribución (EPA): `< 2.000 €`, `2.000–4.000 €`, `4.000–6.000 €`, `6.000–8.000 €`, `8.000–10.000 €`. El rango `> 10.000 €` se eliminó al verificar que el importe máximo real en BD es exactamente 10.000 €; los 8 registros con ese importe se reclasificaron al rango anterior.
- Colores de gráficos: tonos verdes (`verdeOscuro #2E7D32`, `verdeMedio #66BB6A`, `verdeClaro #A5D6A7`) para EPAs; el top beneficiarios usa azul.

---

### 5.7 Estadísticas EELL — `estadisticas-eell.html` + `js/estadisticas-eell.js` (Issue 7D)

**Propósito:** Análisis específico de las convocatorias de Entidades de la Administración Local (ayuntamientos): % de ayuntamientos con ayuda, importe medio EELL, ratio de exclusión, top provincias por importe, concentración top 10% vs resto y top 5 CCAA. Estructura simétrica a `estadisticas-epas.html` (4 gráficas en 2 filas de 2).

**Estado:** Completamente implementada. El mapa choropleth CCAA se movió a `exclusivo.html` — ver sección 5.9.

**Fondo visual:** usa la clase `.fondo-stats`. Enlace "→ Ver estadísticas EPAs" en la cabecera.

**Estructura HTML (4 gráficas):**

| Bloque | ID | Descripción |
|---|---|---|
| KPIs | `.grid-4` | 4 tarjetas de métricas EELL |
| Top provincias | `#grafico-top-provincias` | Barras horizontales por importe |
| Concentración top 10% | `#grafico-concentracion` | Donut top 10% vs resto |
| Top 5 CCAA por subvención | `#top5-ccaa-lista` | Lista top 5 por importe |
| Top 5 CCAA por ayuntamientos | `#top5-concesiones-lista` | Lista top 5 por número de concesiones |

**KPIs:**

| ID | Label | Dato |
|---|---|---|
| `#kpi-pct-ayuntamientos` | % Ayuntamientos con ayuda | `datos.pct_ayuntamientos_con_ayuda` |
| `#kpi-importe-medio-eell` | Importe medio EELL | `datos.importe_medio` |
| `#kpi-ratio-exclusion` | Ratio de exclusión | `datos.ratio_exclusion` |
| `#kpi-ccaa-top` | CCAA con mayor importe concedido | `datos.ccaa_top` |

**Funciones en `estadisticas-eell.js`:**

| Función | Tipo | Elemento | Datos |
|---|---|---|---|
| `poblarGraficoTopProvincias` | `bar` horizontal | `#grafico-top-provincias` | `top_provincias[]` |
| `poblarGraficoConcentracion` | `doughnut` | `#grafico-concentracion` | `concentracion{}` |
| `poblarTop5Ccaa` | Lista HTML | `#top5-ccaa-lista` | `por_ccaa[]` |
| `poblarTop5Concesiones` | Lista HTML | `#top5-concesiones-lista` | `por_ccaa[]` |

> **Nota:** `poblarRankingCcaa` fue eliminada — el ranking completo de CCAA se muestra en `exclusivo.html` junto al mapa.

**Endpoint `GET /estadisticas/eell`:**

```json
{
  "pct_ayuntamientos_con_ayuda": number,
  "importe_medio":               number,
  "ratio_exclusion":             number,
  "ccaa_top":                    string,
  "por_ccaa": [
    { "ccaa": string, "importe_total": number, "num_concesiones": number }, ...
  ],
  "top_provincias": [
    { "provincia": string, "importe_total": number }, ...
  ],
  "concentracion": {
    "top_10_pct": number,
    "resto_pct":  number
  }
}
```

**Notas de implementación:**

- `pct_ayuntamientos_con_ayuda` = beneficiarios con al menos una concesión / total beneficiarios que solicitaron × 100.
- `ratio_exclusion` = (excluidas + desistidas) / total solicitudes EELL (valor 0–1; el frontend lo multiplica por 100 para mostrar %).
- `concentracion.top_10_pct` = % del importe acaparado por el decil superior de beneficiarios por importe acumulado.
- Colores de gráficos: azul institucional (`#1565C0`, `#90CAF9`) para EELL.

---

### 5.8 Login y Registro — `login.html` / `registro.html`

**Propósito:** Autenticación de usuarios mediante email y contraseña.

**Roles del sistema:**

| Rol | Permisos |
|---|---|
| Visitante (sin login) | Acceso completo a Home, Buscador y Estadísticas |
| Registrado | Acceso a la Zona Exclusiva |
| Admin | Gestión de usuarios (no hay panel admin en el frontend por ahora) |

**Diseño:** Card partida en dos columnas (max-width 920px) sobre fondo verde suave `#E8F5E9`. Panel izquierdo: fondo claro `#f0f5f1`, gran círculo geométrico verde oscuro centrado (`300×300px`, `border-radius: 50%`) con un blob secundario verde claro en la esquina inferior-derecha; la foto de animales se superpone centrada con `drop-shadow`. Panel derecho: formulario de calidad institucional (GOV.UK) con labels en negrita, inputs borde 2px, foco outline verde 3px y errores con borde izquierdo rojo. En móvil la imagen se oculta. Los botones sociales (Google, GitHub) han sido eliminados; el flujo de acceso es únicamente email + contraseña.

**Flujo de login (`login.html` + `auth.js`):**
1. El usuario introduce email y contraseña.
2. Validación client-side antes de enviar.
3. `POST /auth/login` con body JSON `{ email, password }`.
4. La API devuelve `{ access_token, token_type }` si las credenciales son correctas.
5. Se guarda `access_token` en `localStorage` con la clave `"token"`.
6. Se redirige a `privado.html`.
7. Si hay error (401): se muestra la alerta roja con el mensaje del servidor.

**Flujo de registro (`registro.html` + `auth.js`):**
1. El usuario rellena nombre (solo visual), email y contraseña.
2. Validación en tiempo real de los requisitos de contraseña.
3. `POST /auth/registro` con body JSON `{ email, password }`.
   - El campo nombre **no se envía** — el backend (`RegistroIn`) solo acepta `email` y `password`.
4. Si la respuesta es 201: mensaje de éxito y redirección a `login.html` tras 2 segundos.
5. Si hay error (400, email ya en uso): se muestra la alerta roja.

**Validaciones de contraseña** (mismas reglas que el backend, `RegistroIn.password_seguro`):

| Requisito | Implementación JS |
|---|---|
| Mínimo 8 caracteres | `password.length >= 8` |
| Al menos 1 mayúscula | `/[A-Z]/.test(password)` |
| Al menos 1 minúscula | `/[a-z]/.test(password)` |
| Al menos 1 número | `/[0-9]/.test(password)` |

**Prevención de doble envío:** El botón de submit se deshabilita mientras espera la respuesta del servidor (`btn.disabled = true`). Se restaura en el bloque `finally` del `try/catch`.

**Botones sociales (Google, GitHub):** Eliminados del HTML. El backend no implementa OAuth y la inclusión de botones deshabilitados generaba confusión en el usuario.

### 5.9 Zona exclusiva — `privado.html` + `js/privado.js`

**Propósito:** Perfil del usuario: cambio de contraseña, nombre/alias y acceso a `exclusivo.html`.

---

### 5.10 Contenido exclusivo — `exclusivo.html` + `js/exclusivo.js`

**Propósito:** Contenido reservado para usuarios registrados. Incluye tabla resumen de solicitudes por convocatoria, mapa choropleth interactivo de CCAA y modal de top municipios por CCAA.

**Control de acceso:** igual que `privado.html` — token JWT en localStorage, redirección a login si falta o expira.

**Secciones:**

| Sección | Descripción |
|---|---|
| Resumen de solicitudes | Tabla EPA + EELL + total global con desglose por estado e importe. Endpoint: `GET /privado/resumen-tabla` |
| Mapa choropleth CCAA | Mapa Leaflet 1.9.4 coloreado por importe concedido. Ver detalle abajo. |
| Próximamente | Causas de exclusión frecuentes y puntuación mínima por convocatoria (pendiente) |

**Mapa choropleth (`js/mapa-ccaa.js`):**

- Librería: Leaflet 1.9.4 + CartoDB Positron sin etiquetas
- GeoJSON: `assets/geojson/ccaa.geojson` (19 features, ~600 KB, nombres alineados con la API)
- Paleta: 4 bandas de tonos tierra (beige → caramelo → marrón) + rojo para CCAA sin subvenciones EELL
- Escala: cuartiles reales del dataset (p25/p50/p75) redondeados a valores "bonitos"
- Hover: oscurece el color propio del polígono (función `oscurecer(hex, factor)`)
- Clic: abre modal con top 10 municipios (ver abajo)
- Año mínimo/máximo detectado dinámicamente desde `GET /estadisticas/`
- El mapa acepta un callback `onClickCCAA` como segundo parámetro para desacoplar la lógica del modal

**Modal top 10 municipios (`exclusivo.js → abrirModalCCAA`):**

- Fetch: `GET /solicitudes/?ccaa=X&estado=concedida&limite=500`
- Para solicitudes con `es_agrupacion=true`: expande a municipios individuales via `GET /agrupaciones/{id_solic}`
- Dos columnas: acumulado todos los años / último año con resolución (detectado como `max(anio)`)
- Nota "Top N de M municipios" calculada dinámicamente
- Cierre: botón ×, clic en overlay o tecla Esc

---

### 5.11 Zona privada — `privado.html` + `js/privado.js` (renumerada)

**Propósito:** Contenido reservado para usuarios registrados.

**Control de acceso:**
1. Al cargar la página, `privado.js` comprueba `localStorage.getItem('token')`.
2. Si no hay token → `window.location.href = 'login.html'` (redirección inmediata).
3. Si hay token → petición autenticada al backend con el header `Authorization: Bearer <token>`.
4. Si el servidor responde 401 (token expirado o inválido) → borrar token y redirigir al login.

**Endpoints usados:**

| Endpoint | Respuesta |
|---|---|
| `GET /privado/perfil` | `{ email, rol, miembro_desde }` |
| `GET /privado/resumen-exclusivo` | `{ mensaje, contenido: string[] }` |

Las dos peticiones se lanzan en paralelo con `Promise.all()` para minimizar el tiempo de espera.

**Cierre de sesión:** `localStorage.removeItem('token')` + redirección a `login.html`. Los JWT son stateless, así que no hay "invalidación" en el servidor — simplemente dejamos de tener el token en el cliente.

---

### 5.12 Contacto — `contacto.html` + `js/contacto.js`

Formulario de contacto público. **Diseño propio** (no la `auth-card` de login/registro): una sola columna centrada (`.contacto-page` → `.contacto-card`) sobre fondo gris claro, para que se lea como un formulario y no como una pantalla de acceso.

**Campos:** nombre (opcional), correo electrónico y mensaje (obligatorios, marcados con asterisco `*` y leyenda "* Campos obligatorios"). El `textarea` usa la variante `.input-campo--area`. Checkbox de consentimiento de la política de privacidad obligatorio.

**Envío (`contacto.js`):** validación cliente (email válido, mensaje ≥ 10, consentimiento marcado) y `POST /contacto/`. Muestra alerta de éxito o error reutilizando el patrón `.auth-alerta` / `.auth-alerta--ok`. Es autocontenido (no carga `auth.js`).

**Antispam:** campo honeypot oculto `sitio_web` (mismo patrón que el registro) + rate limiting en Nginx (zona `contacto`, 3 req/min). El backend reenvía el mensaje por email (`POST /contacto/`); si el SMTP falla devuelve 503 y el formulario lo informa.

---

## 6. Integración con la API REST

### Endpoints disponibles y su uso en el frontend

| Endpoint | Método | Parámetros / Body | Páginas que lo usan |
|---|---|---|---|
| `/estadisticas/` | GET | — | Home (métricas + gráficos generales) |
| `/solicitudes/` | GET | `anio`, `tipo`, `estado`, `buscar`, `ccaa`, `provincia`, `linea`, `limite`, `pagina` | Buscador |
| `/solicitudes/?cif=` | GET | `cif` | Ficha de entidad |
| `/solicitudes/export` | GET | `anio`, `tipo`, `estado`, `buscar`, `ccaa` (sin `pagina` ni `limite`) | Buscador (botón CSV) |
| `/agrupaciones/{id_solic}` | GET | — | Ficha de entidad (desglose de municipios) |
| `/estadisticas/epas` | GET | — | Estadísticas EPAs (KPIs, distribución, media vs mediana, nuevos vs recurrentes, top) — **pendiente de backend** |
| `/estadisticas/eell` | GET | — | Estadísticas EELL (KPIs, top provincias, concentración, ranking CCAA) — **pendiente de backend** |
| `/recursos/` | GET | — | Recursos (tarjetas de directorio dinámico) — **pendiente de backend** |
| `/auth/login` | POST | JSON `{ email, password }` | Login |
| `/auth/registro` | POST | JSON `{ email, password }` | Registro |
| `/privado/perfil` | GET | Header `Authorization: Bearer <token>` | Zona Privada |
| `/privado/resumen-exclusivo` | GET | Header `Authorization: Bearer <token>` | Zona Privada |

### Estado de implementación de filtros

| Filtro | Backend | Notas |
|---|---|---|
| Búsqueda por nombre de entidad | ✔ `?buscar=` | Server-side; eliminado el `.filter()` client-side |
| Filtro por CCAA | ✔ `?ccaa=` | Campo `ccaa` en tabla `solicitudes`; solo EELL |
| Filtro por Provincia | ✔ `?provincia=` | Campo `provincia` en tabla `solicitudes`; solo EELL |
| Filtro por Línea | ✔ `?linea=` | Campo `linea` en tabla `concesiones`; solo EPA 2025 |
| Historial de entidad por CIF | ✔ `?cif=` | Implementado en Issue 7C |
| Exportación CSV | ✔ `/solicitudes/export` | Todos los filtros excepto paginación |
| Desglose de agrupación | ✔ `/agrupaciones/{id_solic}` | Solo cuando `es_agrupacion === true` |
| Estadísticas EPAs | ⏳ `/estadisticas/epas` | Pendiente — fetch comentado en `estadisticas-epas.js` |
| Estadísticas EELL | ⏳ `/estadisticas/eell` | Pendiente — fetch comentado en `estadisticas-eell.js` |
| Directorio de recursos | ⏳ `/recursos/` | Pendiente — fetch comentado en `recursos.js` |

### Patrón de llamada a la API (Issue 7D)

Todas las peticiones siguen el mismo patrón con spinner, error estructurado y finally:

```javascript
async function cargarDatos() {
    document.getElementById('spinner').style.display = 'block';
    try {
        const respuesta = await fetch(`${API_URL}/endpoint/`);

        if (!respuesta.ok) {
            let cuerpo = {};
            try { cuerpo = await respuesta.json(); } catch (_) {}
            document.getElementById('error-mensaje').textContent    = cuerpo.mensaje    || `Error ${respuesta.status}`;
            document.getElementById('error-sugerencia').textContent = cuerpo.sugerencia || '';
            document.getElementById('error-box').style.display      = 'block';
            throw new Error(`Error ${respuesta.status}`);
        }

        const datos = await respuesta.json();
        // Actualizar el DOM con los datos...

    } catch (error) {
        console.error('Error:', error);
        // Mostrar mensaje de error al usuario...
    } finally {
        document.getElementById('spinner').style.display = 'none';
    }
}
```

**¿Por qué `async/await`?** Es la forma moderna y legible de manejar código asíncrono en JavaScript. Alternativas como callbacks o `.then()` producen código más difícil de leer y depurar.

---

## 7. Filtros condicionales del buscador

El buscador tiene filtros que solo aparecen bajo ciertas condiciones. Esta lógica está implementada en `solicitudes.js` mediante la función `actualizarFiltrosCondicionales()`.

### Reglas

```
Si Tipo = "eell"
    → Mostrar CCAA y Provincia
    → Ocultar Línea

Si Tipo = "epa" Y Año = "2025"
    → Mostrar Línea
    → Ocultar CCAA y Provincia

En cualquier otro caso
    → Ocultar CCAA, Provincia y Línea
```

### Justificación

**CCAA y Provincia solo para EELL:** Las Entidades de la Administración Local son ayuntamientos, que tienen una ubicación geográfica concreta. Las EPA (asociaciones protectoras) pueden tener sede en cualquier municipio pero no se clasifican geográficamente del mismo modo en esta base de datos.

**Línea solo para EPA 2025:** El campo `linea` (animales abandonados / colonias felinas) solo existe en la convocatoria EPA del año 2025. En años anteriores y en todas las convocatorias EELL el campo es `null`.

### Implementación

Cuando un filtro condicional se oculta, su valor se limpia automáticamente para que no afecte a la siguiente búsqueda. Esto evita el error de enviar `?ccaa=andalucia` a la API cuando el usuario ha cambiado el tipo a EPA.

---

## 8. Accesibilidad — WCAG 2.1

Se aplican los criterios del nivel AA del estándar WCAG 2.1 (Web Content Accessibility Guidelines).

### Semántica HTML

| Elemento | Uso correcto en este proyecto |
|---|---|
| `<header>` | Contiene el `<nav>` en todas las páginas |
| `<nav>` | Barra de navegación principal y navegación del footer |
| `<main>` | Contenido principal de la página (uno por página) |
| `<footer>` | Pie de página |
| `<section>` | Bloques temáticos con `aria-labelledby` |
| `<h1>` a `<h3>` | Jerarquía de títulos sin saltar niveles |
| `<table>` | Solo para datos tabulares, nunca para maquetar |
| `<form>` | Panel de filtros del buscador |
| `<ul>` + `<li>` | Menú de navegación |

### Atributos ARIA

- `aria-label` y `aria-labelledby`: identifican bloques para lectores de pantalla.
- `role="navigation"` en los `<nav>`: refuerza la semántica para compatibilidad.
- `aria-current="page"`: indica al lector de pantalla qué enlace corresponde a la página actual.
- `aria-hidden="true"`: oculta elementos decorativos (como los separadores `|`) de los lectores de pantalla.
- `scope="col"` en `<th>`: indica que las cabeceras son de columna, no de fila.
- `role="alert"` y `aria-live="polite"` en las alertas de error: anunciadas al aparecer.

### Contraste de colores

El par de colores más crítico (texto `#616161` sobre fondo `#ffffff`) tiene una relación de contraste de **4.89:1**, que supera el mínimo de 4.5:1 del nivel AA.

### Teclado

Los botones del formulario son elementos `<button>` nativos, lo que los hace accesibles por tabulación sin configuración adicional. Los enlaces de la tabla son manejados con `addEventListener('click')` en el `<tr>`, que también responde al teclado.

---

## 9. Decisiones de diseño justificadas

### ¿Por qué portada partida (split) y no banner centrado?

El diseño anterior del proyecto usaba una portada dividida: texto a la izquierda e imagen de animales a la derecha. Se mantiene este enfoque porque:
- Comunica mejor la identidad del proyecto (bienestar animal) combinando información textual e imagen.
- Es un patrón reconocido en portales institucionales y de organizaciones del tercer sector.
- Resulta más atractivo visualmente que un bloque de texto centrado.

### ¿Por qué tarjetas de año y no tabla para las convocatorias recientes?

Las tarjetas permiten comparar rápidamente las tres últimas convocatorias (2025, 2024, 2023) de un vistazo, sin necesidad de leer una tabla fila a fila. Este patrón está ampliamente usado en portales de datos públicos como datos.gob.es.

### ¿Por qué un footer verde oscuro?

El footer forma parte de la identidad visual del proyecto. El verde oscuro (`#163a25`) pertenece a la misma paleta que el resto de la interfaz, refuerza la temática de naturaleza y bienestar animal, y diferencia claramente el pie de página del cuerpo de la web sin resultar tan genérico como un footer negro o gris.

### ¿Por qué paginación server-side y no client-side?

El dataset puede superar los 6.000 registros. Descargar todos los registros a la vez y paginarlos en el navegador sería ineficiente (carga inicial lenta, consumo de memoria) y poco escalable. Usando los parámetros `limite` y `pagina` del endpoint `/solicitudes/`, cada página solo descarga los 50 registros que necesita mostrar.

### ¿Por qué `URLSearchParams` para construir URLs de la API?

`URLSearchParams` es la forma estándar de JavaScript para construir cadenas de parámetros query. Escapa automáticamente caracteres especiales (espacios, tildes, etc.), evitando errores que sí ocurren al concatenar strings a mano.

### ¿Por qué el JS se carga al final del `<body>`?

Si el script se cargara en el `<head>`, se ejecutaría antes de que el navegador hubiera construido los elementos del DOM (tabla, botones, filtros). `document.getElementById()` devolvería `null` y el script fallaría. Al colocarlo al final del `<body>`, el HTML ya está en memoria cuando el script comienza a ejecutarse.

### ¿Por qué el CSV se genera en el backend y no en el cliente?

La generación del CSV se delega al backend (`GET /solicitudes/export`). Razones:

- El backend exporta **todos** los registros que coinciden con los filtros, sin limitarse a los 50 de la página actual.
- No se necesita tener los datos cargados en memoria del navegador.
- El formato, la codificación (UTF-8 con BOM) y el separador los controla el backend de forma centralizada.

La **descarga** sí ocurre en el cliente: el frontend recibe la respuesta como `Blob` y usa `URL.createObjectURL` + `<a download>` para disparar el guardado con un nombre de archivo dinámico. Esto combina lo mejor de ambos enfoques: el backend genera el contenido, el frontend controla el nombre del archivo.

---

## 10. Pendientes de implementación

### Issue 7D — Completado

| Tarea | Estado |
|---|---|
| Badge "Agrupación" en el buscador | ✔ Completado |
| Desglose de municipios en ficha de entidad | ✔ Completado |
| Botón "Descargar CSV" → endpoint `/solicitudes/export` | ✔ Completado |
| Spinners de carga en solicitudes, entidad, home, EPAs y EELL | ✔ Completado |
| Caja de error visual para 401/403/404/422/500 | ✔ Completado |
| Favicon en todas las páginas HTML | ✔ Completado |
| Metadatos OG en index, entidad, EPAs y EELL | ✔ Completado |
| Botón "Conócenos" → "Ver solicitudes" | ✔ Completado |
| KPI entidades únicas conectado con `entidades_unicas` de la API | ✔ Completado |
| Navbar renombrado a "Subvenciones DGDA" | ✔ Completado |
| Navbar reorganizado a 6 enlaces Opción A: Inicio, Buscador, EPAs, EELL, Recursos, Acceder | ✔ Completado |
| Columna "Año" en lugar de "Expediente" en la tabla del buscador | ✔ Completado |
| Orden inicial A→Z y eliminación de "Por defecto" en el select | ✔ Completado |
| Nueva página `recursos.html` con contenido estático real (sin `js/recursos.js`; el fetch dinámico queda pendiente) | ✔ Completado |
| Gráficos generales integrados en `index.html` usando `GET /estadisticas/` | ✔ Completado |
| Nueva página `estadisticas-epas.html` + `js/estadisticas-epas.js` (4 gráficos + 4 KPIs, conectados a `GET /estadisticas/epas`) | ✔ Completado |
| Nueva página `estadisticas-eell.html` + `js/estadisticas-eell.js` (3 gráficos + ranking CCAA + 4 KPIs, conectados a `GET /estadisticas/eell`) | ✔ Completado |

### Issue 7C — Completado

| Tarea | Estado | Notas |
|---|---|---|
| Ficha de entidad | ✔ Completado | `entidad.html` + `entidad.js` implementados |
| Conexión de filtros nuevos | ✔ Completado | CCAA, Provincia, Línea, buscar |
| Reordenación de filtros | ✔ Completado | Entidad → Tipo → Año → Estado |
| Separadores de miles | ✔ Completado | `parseFloat()` + `Intl.NumberFormat` |
| Ajustes CSS de paginación | ✔ Completado | Botones más compactos |
| Enlace DGDA en footer | ✔ Completado | Añadido en las 6 páginas |

### Pendientes de backend (Vero)

| Funcionalidad | Endpoint necesario | Consume |
|---|---|---|
| Directorio de recursos dinámico | `GET /recursos/` | `recursos.js` |

### Pendientes futuros del frontend

- Implementar mapa de calor de CCAA en `estadisticas-eell.html` (decisión técnica pendiente: SVG inline o librería de mapas).
- Poblar `recursos.html` con datos dinámicos cuando el backend implemente `GET /recursos/`.
- Eliminar con `git rm` los archivos obsoletos `estadisticas.html`, `js/estadisticas.js`, `estadisticas-avanzadas.html` y `js/estadisticas-avanzadas.js`.
- Mejorar los mensajes de error visibles al usuario (traducir a lenguaje natural).
- Ficha de entidad como modal/popup para conservar el contexto de búsqueda al cerrar.
- Política de privacidad y aviso legal.
- Contenido de la zona privada: tabla resumen por año/estado/tipo.

---

## 11. Flujo completo de autenticación

Este diagrama resume cómo se mueve el usuario entre las páginas de autenticación:

```
[Visitante] → login.html
                 │
                 ├─ Credenciales correctas → POST /auth/login
                 │     └─ localStorage.setItem('token', ...)
                 │           └─ window.location → privado.html
                 │
                 └─ Credenciales incorrectas → alerta roja (sin redirección)


[Visitante] → registro.html
                 │
                 ├─ Formulario válido → POST /auth/registro (201 Created)
                 │     └─ mensaje de éxito → setTimeout(2s) → login.html
                 │
                 └─ Email ya existente → alerta roja (400 Bad Request)


[privado.html carga]
                 │
                 ├─ Sin token en localStorage → window.location → login.html
                 │
                 ├─ Token presente → GET /privado/perfil + /privado/resumen-exclusivo
                 │     ├─ 200 OK → mostrar saludo + tarjetas de contenido
                 │     └─ 401 Unauthorized → borrar token → login.html
                 │
                 └─ [Botón cerrar sesión] → localStorage.removeItem('token')
                                               └─ window.location → login.html
```

---

*Última actualización: 4 de mayo de 2026 — Reorganización completa de estadísticas en Issue 7D. Refleja estado final tras Issues 7B, 7C y 7D: navbar Opción A con 6 enlaces directos, gráficos generales integrados en Home, páginas `estadisticas-epas.html` y `estadisticas-eell.html` con JS propio, y `recursos.html` con contenido estático real.*

---

## 12. Registro de ajustes post-wireframe

### 12.1 Límite de paginación en el buscador de solicitudes

**Archivo modificado:** `js/solicitudes.js`  
**Cambio:** `LIMITE = 50` → `LIMITE = 100`  
**Motivo:** El wireframe original (Pantalla 2 — Listado de solicitudes, Pág. 4) especifica server-side pagination con 100 registros por página (aprox. 64 páginas para los 6.398 registros actuales). El valor anterior de 50 era provisional.  
**Relación con backend:** El parámetro `limite` se pasa como query string a `GET /solicitudes/?limite=100&pagina=N`. El backend ya acepta cualquier valor; este cambio es exclusivamente de frontend.  
**Sin impacto en:** Lógica de filtros, exportación CSV, paginación (los cálculos usan `Math.ceil(total / LIMITE)` y se recalculan automáticamente).

### 12.2 Corrección de colores de badges de estado

**Archivo modificado:** `css/styles.css` (bloque `:root`, variables `--estado-*`)  
**Cambio:** Dos variables CSS actualizadas para alinearse con el wireframe (Pantalla 2 — Listado de solicitudes, Pág. 4-5):

| Variable | Antes | Después | Color |
|---|---|---|---|
| `--estado-excluida` | `#EF6C00` (naranja) | `#B45309` (ámbar) | según wireframe |
| `--estado-desistida` | `#6A1B9A` (morado) | `#6B7280` (gris) | según wireframe |

La tabla completa de badges queda: **verde** = concedida · **rojo** = no beneficiaria · **ámbar** = excluida · **gris** = desistida.  
Los valores elegidos superan el ratio de contraste WCAG AA (4.5:1) sobre fondo blanco con texto blanco.  
**Relación con backend:** Ninguna. Son estilos visuales puros.  
**Propagación automática:** Las clases `.badge-excluida` y `.badge-desistida` y cualquier otro elemento que use `var(--estado-excluida)` o `var(--estado-desistida)` se actualizan sin cambios adicionales.

### 12.3 Campo "confirmar contraseña" en registro y cambio de contraseña

**Archivos modificados:** `registro.html`, `privado.html`, `js/auth.js`, `js/privado.js`  
**Cambio:** Se añade un campo `<input type="password">` de confirmación en dos formularios, con validación client-side que bloquea el envío si las contraseñas no coinciden.

**En `registro.html`:**
- Nuevo campo `#registro-password-confirm` tras los indicadores de requisitos.
- Span de error `#error-password-confirm-reg` con mensaje "Las contraseñas no coinciden."
- `auth.js` (función `iniciarRegistro`): lee `#registro-password-confirm`, compara con `#registro-password` y activa/desactiva el error antes de hacer fetch.

**En `privado.html`:**
- Nuevo campo `#password-nueva-confirm` tras el campo `#password-nueva`.
- Span de error `#error-password-nueva-confirm` con mensaje "Las contraseñas no coinciden."
- `privado.js` (función `manejarCambiarPassword`): valida la coincidencia antes de enviar la petición `PUT /privado/cambiar-contrasena`. Si no coinciden, muestra el error y hace `return` sin llamar al backend.
- Al completar el cambio con éxito, el campo de confirmación también se limpia.

**Relación con backend:** Ninguna. El backend (`PUT /privado/cambiar-contrasena`) recibe `{ contrasena_actual, contrasena_nueva }` exactamente igual que antes. El campo de confirmación existe solo en el cliente para mejorar la seguridad UX.  
**Sin impacto en:** Flujo de login, tokens, ni ningún otro formulario.

### 12.4 Comentario obsoleto eliminado en home.js

**Archivo modificado:** `js/home.js` (función `mostrarMetricas`, línea ~197)  
**Cambio:** El comentario que decía `PENDIENTE DE BACKEND: cuando el schema EstadisticasOut incluya 'entidades_unicas'...` se ha reemplazado por un comentario descriptivo correcto: el campo ya existe y funciona desde el backend.  
**Motivo:** El campo `entidades_unicas` fue implementado en el backend (`EstadisticasOut` en `schemas.py`) y el endpoint `GET /estadisticas/` lo devuelve correctamente. El comentario era un recordatorio temporal que quedó sin actualizar.  
**Relación con backend:** Meramente documental. No hay cambio funcional.

### 12.5 Páginas aviso-legal.html y privacidad.html

**Archivos creados:** `aviso-legal.html`, `privacidad.html`  
**Archivos modificados:** todos los HTML del proyecto (footer de 12 páginas)

**Páginas creadas:** Dos páginas estáticas con contenido adecuado para un proyecto educativo de TFG:
- `aviso-legal.html`: titularidad (proyecto educativo DAW), finalidad (datos públicos BDNS/DGDA), responsabilidad, propiedad intelectual y contacto.
- `privacidad.html`: datos recogidos (email + contraseña bcrypt + tokens de sesión), finalidad, derechos del usuario, seguridad (HTTPS TLS 1.2/1.3, bcrypt, tokens revocables) y nota sobre datos públicos.

Ambas páginas tienen `<meta name="robots" content="noindex">` para excluirlas de los motores de búsqueda (igual que `admin.html`). Incluyen navbar y footer completos con los mismos enlaces que el resto del proyecto.

**Enlace "← Volver al inicio"** (en ambas páginas): usa la clase CSS `.legal-back-link` (definida en `styles.css` bajo la sección "PÁGINAS LEGALES"), no estilo inline. Color azul institucional (`var(--color-azul)`, `#1565C0`) en lugar del verde primario del resto del sitio — el azul es la convención web tradicional para enlaces de retorno y el lector lo identifica al instante. Tamaño `0.9rem`, ligeramente menor que el texto del cuerpo, para que actúe como elemento de navegación secundaria sin competir con el título de la página.

**Footer actualizado en:** `index.html`, `login.html`, `registro.html`, `buscador.html`, `estadisticas-epas.html`, `estadisticas-eell.html`, `entidad.html`, `privado.html`, `admin.html`, `recursos.html`, `recuperar-password.html`, `reset-password.html`. Se añadieron los enlaces "Aviso legal" y "Privacidad" al `<nav>` del footer usando el separador `footer-principal__sep` ya existente.

**Relación con backend:** Ninguna. Contenido estático puro.  
**Eliminado de "Pendientes":** El punto "Política de privacidad y aviso legal" que figuraba en la sección de pendientes del documento queda completado.

### 12.6 Tabla de solicitudes responsive — vista de tarjetas en móvil

**Archivos modificados:** `css/styles.css`, `js/solicitudes.js`

**Problema:** En pantallas estrechas (<600 px) la tabla de resultados del buscador desbordaba horizontalmente, obligando al usuario a hacer scroll lateral. La columna "Entidad" (la más ancha) quedaba cortada y los badges de estado eran difíciles de pulsar.

**Solución técnica — CSS (`styles.css`):**  
Se añadió un bloque `@media (max-width: 600px)` estrictamente acotado a `.tabla-wrapper`. El selector limita el impacto a la tabla de solicitudes y no afecta otras tablas del proyecto (p. ej. la de entidad, que usa `id` en lugar de clase). La técnica empleada es **data-label + `::before { content: attr(data-label) }`**: cada celda pasa a `display: flex; justify-content: space-between` y muestra el nombre de columna como prefijo usando su atributo HTML `data-label`. El `<thead>` se oculta con `display: none` porque la información ya está duplicada en los atributos. Las filas se convierten en tarjetas con borde, `border-radius` y sombra suave, reutilizando las variables CSS del sistema de diseño (`--radio-card`, `--color-gris-medio`, `--color-fondo-verde`).

**Solución técnica — JS (`solicitudes.js`):**  
En la función `crearFila()`, el `tr.innerHTML` se amplió para incluir el atributo `data-label` en cada `<td>`. El atributo es texto literal y no requiere lógica adicional. Los valores dinámicos (entidad, año, tipo, estado, importe) no se alteraron.

**Decisiones de diseño:**

| Alternativa descartada | Motivo |
|---|---|
| Scroll horizontal | Mal UX en móvil; obliga a gestos torpes |
| Generar tarjetas `<div>` con JS | Rompe la semántica de tabla; complica paginación |
| Tabla con `table-layout: fixed` + `overflow hidden` | Recorta texto sin notificarlo al usuario |
| Bootstrap u otra librería | Sin nuevas dependencias por requisito del proyecto |

**Columnas y sus `data-label`:**

| `<th>` visible | `data-label` en `<td>` |
|---|---|
| Entidad beneficiaria | `Entidad` |
| Año | `Año` |
| Tipo | `Tipo` |
| Estado | `Estado` |
| Importe concedido | `Importe` |

**Breakpoint elegido:** `600 px` — coincide con el breakpoint `sm` de referencia, que es el límite habitual entre móvil portrait y tablet. Las tarjetas de la página de inicio ya usan `480 px`; usar `600 px` para la tabla da más margen en dispositivos en el rango 481–600 px donde la tabla sigue siendo incómoda.

**Accesibilidad:** Ocultar `<thead>` con `display: none` es aceptable porque los `data-label` proporcionan el contexto de cada celda. Los lectores de pantalla en móvil seguirán leyendo el atributo a través del pseudo-elemento `::before`. Los badges de estado conservan su `aria-label`.

**Relación con backend:** Ninguna.  
**Archivos con cambios de comportamiento visual en otros breakpoints:** Ninguno (el bloque está completamente aislado en `@media (max-width: 600px) { .tabla-wrapper ... }`).  
**Eliminado de "Pendientes":** El punto "Tabla responsive en móvil (buscador de solicitudes)" de la sección 10.

### 12.7 Botón "Descargar PNG" en tarjetas de gráfico

**Archivos modificados:**
- `css/styles.css` — nueva clase `.btn-descargar-png` (sección 28)
- `index.html` — 3 botones en `#btn-dl-linea`, `#btn-dl-donut`, `#btn-dl-barras`
- `estadisticas-epas.html` — 4 botones: `#btn-dl-distribucion`, `#btn-dl-media-mediana`, `#btn-dl-nuevos`, `#btn-dl-top`
- `estadisticas-eell.html` — 2 botones: `#btn-dl-provincias`, `#btn-dl-concentracion`
- `js/home.js` — función `configurarDescarga()` + wire-up en los 3 gráficos
- `js/estadisticas-epas.js` — función `configurarDescarga()` + wire-up en los 4 gráficos
- `js/estadisticas-eell.js` — función `configurarDescarga()` + wire-up en los 2 gráficos

**Problema resuelto:** Los gráficos de Chart.js no ofrecen ninguna opción nativa de exportación en la UI. El usuario no podía guardar los gráficos para documentos, informes o presentaciones.

**Solución técnica:** Botón `<button class="btn-descargar-png">` insertado en el `card-grafico__cabecera` de cada tarjeta de gráfico. El botón empieza con `display:none` en el HTML y se muestra dinámicamente en el JS solo después de que el gráfico se haya pintado correctamente (`configurarDescarga()` recibe la instancia de `Chart.js`). El listener de click llama a `instancia.toBase64Image('image/png', 1)`, que devuelve una URL de datos PNG en alta calidad. Se crea un `<a>` temporal con `href = dataURL` y `download = nombreArchivo`, se dispara el click y se descarta, sin abrir nuevas ventanas ni redirigir.

**Función `configurarDescarga(instanciaChart, btnId, nombreArchivo)`:**
- Recibe la instancia devuelta por `new Chart(...)` (Chart.js siempre devuelve la instancia).
- Busca el botón en el DOM por su `id`. Si no existe (`null`), retorna silenciosamente.
- Muestra el botón (`display = 'inline-flex'`).
- Registra un único listener `'click'` que genera y descarga el PNG.
- La función está duplicada en los tres archivos JS porque cada script es independiente (sin módulos ES6 ni bundler). No se usa un archivo de utilidades compartido para mantener la stack sin pasos de build.

**Nombres de archivos descargados:**

| Página | Gráfico | `id` botón | Archivo PNG |
|---|---|---|---|
| `index.html` | Evolución importe | `btn-dl-linea` | `evolucion-importe.png` |
| `index.html` | Distribución estados | `btn-dl-donut` | `distribucion-estados.png` |
| `index.html` | EPA vs EELL | `btn-dl-barras` | `epa-vs-eell.png` |
| `estadisticas-epas.html` | Distribución importes | `btn-dl-distribucion` | `distribucion-importes-epa.png` |
| `estadisticas-epas.html` | Media vs mediana | `btn-dl-media-mediana` | `media-mediana-epa.png` |
| `estadisticas-epas.html` | Nuevos vs recurrentes | `btn-dl-nuevos` | `nuevos-recurrentes-epa.png` |
| `estadisticas-epas.html` | Top beneficiarios | `btn-dl-top` | `top-beneficiarios-epa.png` |
| `estadisticas-eell.html` | Top provincias | `btn-dl-provincias` | `top-provincias-eell.png` |
| `estadisticas-eell.html` | Concentración importe | `btn-dl-concentracion` | `concentracion-eell.png` |

**Gráficos sin botón de descarga (justificado):**

| Elemento | Motivo |
|---|---|
| Ranking CCAA (`estadisticas-eell.html`) | Es una lista HTML generada por JS, no un `<canvas>` de Chart.js. `toBase64Image()` no aplica. |
| Mapa CCAA (`estadisticas-eell.html`) | Pendiente de implementación técnica. |
| "Tasa de éxito global" (`index.html`) | Es texto plano, no un gráfico. |

**CSS — `.btn-descargar-png`:** Botón ghost (borde verde, fondo transparente) que en hover invierte a fondo verde + texto blanco. `flex-shrink: 0` evita que se comprima en el `card-grafico__cabecera` flex. `font-size: 0.72rem` para no competir visualmente con el título. El `:focus-visible` añade un halo verde de accesibilidad sin afectar a usuarios de ratón.

**Relación con backend:** Ninguna. La descarga ocurre enteramente en el cliente. `toBase64Image()` convierte el canvas de Chart.js a un data URL que el navegador trata como archivo descargable.

**Dependencia de versión:** `chart.toBase64Image(type, quality)` está disponible desde Chart.js 3.x. El proyecto usa Chart.js 4.4.0 (CDN en los HTML), por lo que es compatible.  
**Sin nuevas dependencias.**  
**Eliminado de "Pendientes":** El punto "Exportación de gráficos" de la sección 10.

### 12.8 Badges de tendencia ↑/↓ en KPIs del home

**Archivos modificados:** `index.html`, `js/home.js`, `css/styles.css` (sección 29 ya creada en 12.7)

**Problema resuelto:** Las tarjetas de métricas verdes del home mostraban solo el valor acumulado global sin ninguna referencia temporal. El usuario no podía saber si la cifra estaba creciendo o decayendo respecto al año anterior.

**Solución técnica:** Dos nuevas funciones en `home.js` calculan la variación interanual a partir de los datos que ya devuelve `GET /estadisticas/` (campo `por_anio[]`):

- `mostrarTendencias(datos)`: extrae los dos últimos años disponibles de `por_anio[]`, suma `total` e `importe_total` por año (sumando todos los tipos: EPA + EELL), y delega en `mostrarTendencia()`.
- `mostrarTendencia(id, actual, anterior, anioAnterior)`: calcula `((actual - anterior) / anterior) × 100`, aplica la clase CSS `.tendencia-badge--sube` (verde) o `.tendencia-badge--baja` (rojo), y escribe el texto `↑/↓ X,X % vs AAAA` en el `<span>` oculto.

Se llama desde `mostrarMetricas()` tras poblar los valores, garantizando que los badges solo aparecen cuando hay datos reales.

**KPIs con badge:**

| Tarjeta | Campo `por_anio` | ID badge |
|---|---|---|
| Registros totales | suma `d.total` | `tendencia-registros` |
| Importe Concedido | suma `d.importe_total` | `tendencia-importe` |

**KPI sin badge:** "Entidades únicas" — el campo `datos.entidades_unicas` es un escalar global del schema `EstadisticasOut`; no tiene desglose por año en la respuesta del endpoint, por lo que no es posible calcular la variación. El span no se añade al HTML de esa tarjeta para evitar confusión.

**Comportamiento defensivo:**
- Si `por_anio` está vacío → no se muestran badges (no hay datos).
- Si solo hay 1 año → no se muestran badges (necesitamos 2 para comparar).
- Si `anterior = 0` → `mostrarTendencia` retorna sin hacer nada (evita división por cero).
- Los badges arrancan con `display:none` en el HTML; el JS los muestra solo si tienen valor calculado.

**Accesibilidad:** Los spans tienen `aria-live="polite"` para que los lectores de pantalla anuncien el cambio cuando el JS los rellena. El contraste de colores cumple WCAG AA: `#2E7D32` sobre `#e8f5e9` = 5,4:1 · `#C62828` sobre `#fce4ec` = 5,1:1.

**Relación con backend:** Ninguna. Cálculo enteramente cliente.  
**Sin nuevas dependencias.**

### 12.9 Top 5 CCAA por importe en estadísticas EELL

**Archivos modificados:** `estadisticas-eell.html`, `js/estadisticas-eell.js`, `css/styles.css` (nueva sección 30)

**Problema resuelto:** La página EELL no ofrecía un resumen rápido de las comunidades autónomas líderes en recepción de fondos. El ranking de CCAA existente muestra las 17+2 CCAA en una lista sin jerarquía visual clara.

**Solución técnica — JS:** Nueva función `poblarTop5Ccaa(porCcaa)` en `estadisticas-eell.js`:
1. Ordena `por_ccaa[]` por `importe_total` descendente.
2. Toma los 5 primeros.
3. Construye un `<li>` por CCAA con: posición, nombre, barra proporcional CSS (ancho = `importe / importe_max × 100 %`) e importe formateado.
4. Oculta el placeholder "pendiente" y muestra la lista.
5. Actualiza el badge del encabezado a `Top 5` una vez cargado.
Se llama desde `cargarEstadisticasEell()` con `datos.por_ccaa || []`.

**Solución técnica — HTML:** Bloque nuevo insertado en `estadisticas-eell.html` como "fila 4" (después de las filas 2 y 3 existentes), dentro del mismo contenedor. Usa la clase `.card-grafico` existente para mantener consistencia visual. La lista `<ol id="top5-ccaa-lista">` arranca con `display:none`; el JS la muestra cuando tiene datos.

**Solución técnica — CSS (sección 30):** Clase `.top5-lista` (flex column, gap 10px) + `.top5-lista__item` (CSS grid 3 columnas: posición · nombre+barra · importe) + `.top5-lista__pista` (fondo gris claro, altura 6px) + `.top5-lista__fill` (relleno verde, transición 0,4s). Nuevo CSS mínimo sin romper estilos existentes.

**Datos usados:**

| Campo endpoint | Uso |
|---|---|
| `por_ccaa[].ccaa` | Nombre de la CCAA |
| `por_ccaa[].importe_total` | Valor para ordenar y para la barra |

**¿Por qué `por_ccaa` y no `top_provincias`?** El campo `top_provincias` ya alimenta el gráfico de barras horizontales existente en la fila 2. Usar `por_ccaa` para el Top 5 aporta información diferente (nivel autonómico vs provincial) y evita duplicar el mismo dato dos veces en la misma página.

**Relación con backend:** Ninguna. Los datos `por_ccaa[]` ya llegan en la respuesta de `GET /estadisticas/eell`.  
**Sin nuevas dependencias.**  
**Eliminado de "Pendientes":** El punto "Top 5 entidades EELL" de la sección 10.

---

### 12.10 Deep link post-login

**Archivos modificados:** `js/auth.js`, `js/privado.js`, `js/exclusivo.js`, `js/admin.js`

**Problema resuelto:** Un usuario que intentaba acceder directamente a `privado.html`, `exclusivo.html` o `admin.html` sin sesión activa era redirigido a `login.html` y, tras hacer login, aterrizaba siempre en `privado.html` perdiendo la URL de destino original.

**Solución técnica:** Patrón sessionStorage de dos pasos:

**Paso 1 — guardar destino antes de redirigir a login.** En cada punto de detección de sesión ausente o expirada:
```js
sessionStorage.setItem('redirect_post_login', window.location.href);
window.location.href = 'login.html';
```
Puntos modificados:
- `privado.js` → `fetchAutenticado()` (401), `cargarZonaPrivada()` (sin token, refresh fallido, catch), `manejarCambiarPassword()` (sin token)
- `exclusivo.js` → `fetchAutenticado()` (401), bloque DOMContentLoaded (sin token tras intento de renovación)
- `admin.js` → `verificarAcceso()` línea sin token y línea 401

**Excluidos intencionadamente:**
- `cerrarSesion()` en `privado.js`, `exclusivo.js` — logout explícito del usuario; no procede guardar deeplink.
- `admin.js` redirect a `privado.html` por rol insuficiente (no es falta de autenticación, es falta de autorización).

**Paso 2 — leer y consumir el deeplink tras login exitoso.** En `auth.js`, justo después de guardar el token:
```js
const destino = sessionStorage.getItem('redirect_post_login') || 'privado.html';
sessionStorage.removeItem('redirect_post_login');
window.location.href = destino;
```
`sessionStorage.removeItem` es crítico para evitar que un segundo login posterior reutilice una URL ya obsoleta.

**¿Por qué `sessionStorage` y no `localStorage`?** `sessionStorage` es tab-scoped: si el usuario abre una segunda pestaña con la URL privada, cada pestaña gestiona su propio deeplink de forma independiente. `localStorage` hubiera podido sobreescribir el destino de otra pestaña abierta simultáneamente.

**Relación con backend:** Ninguna. Lógica 100% cliente.  
**Sin nuevas dependencias.**

---

### 12.11 Top 5 CCAA por concesiones acumuladas

**Archivos modificados:** `estadisticas-eell.html`, `js/estadisticas-eell.js`

**Problema resuelto:** La página EELL mostraba el Top 5 por importe (tarea 2.4) pero no ofrecía una vista del volumen de actividad por CCAA medido en número de concesiones. Una comunidad puede concentrar muchas concesiones de importe reducido y no aparecer en el top por importe; el dato de `num_concesiones` del endpoint quedaba sin aprovechar visualmente.

**Solución técnica — JS:** Nueva función `poblarTop5Concesiones(porCcaa)` en `estadisticas-eell.js`, análoga a `poblarTop5Ccaa` pero ordenando por `num_concesiones` descendente y mostrando el recuento formateado (`toLocaleString('es-ES')`) en lugar del importe en euros. Se llama desde `cargarEstadisticasEell()` con `datos.por_ccaa || []`.

**Solución técnica — HTML:** La "fila 4" preexistente (card única) se convierte en `grid-2` para colocar en paralelo el Top 5 por importe y el nuevo Top 5 por concesiones. Reutiliza las mismas clases `.top5-lista`, `.top5-lista__item`, etc. sin añadir CSS nuevo.

**Datos usados:**

| Campo endpoint | Uso |
|---|---|
| `por_ccaa[].ccaa` | Nombre de la CCAA |
| `por_ccaa[].num_concesiones` | Valor para ordenar y para la barra proporcional |

**Relación con backend:** Ninguna. `num_concesiones` ya forma parte de la respuesta de `GET /estadisticas/eell` en cada objeto de `por_ccaa[]`.  
**Sin nuevas dependencias.**

---

### 12.12 `home2.html` — confirmación de no existencia

Verificado durante la revisión final: el archivo `home2.html` **no existe** en el repositorio. No hay referencia a él en ningún HTML, CSS, JS ni en la configuración de Nginx. No requiere ninguna acción.

---

### 12.13 Accesibilidad — Skip navigation

**Archivos modificados:** `css/styles.css`, los 16 archivos HTML del proyecto.

**Problema resuelto:** WCAG 2.4.1 Bypass Blocks (nivel A) — los usuarios de teclado debían tabular por toda la barra de navegación en cada página antes de llegar al contenido principal. Ninguna página tenía mecanismo de salto.

**Solución técnica:**

Estilos añadidos en `styles.css` (nueva sección 25 — Skip Navigation):
```css
.skip-nav {
    position: absolute; left: -9999px; top: 0;
    width: 1px; height: 1px; overflow: hidden; z-index: 9999;
    background: #1a3a1a; color: #fff;
    font-size: 0.9rem; font-weight: 600;
    padding: 10px 18px; border-radius: 0 0 6px 0;
    text-decoration: none; white-space: nowrap;
}
.skip-nav:focus {
    position: fixed; left: 0; top: 0;
    width: auto; height: auto; overflow: visible;
    outline: 3px solid var(--color-primario); outline-offset: 2px;
}
```

El elemento se coloca inmediatamente después del tag `<body>` en todos los HTML:
```html
<a class="skip-nav" href="#contenido-principal">Saltar al contenido principal</a>
```

El atributo `id="contenido-principal"` se añade al elemento `<main>` de cada página (respetando los atributos preexistentes). El enlace usa `href="#contenido-principal"` para mover el foco directamente al área de contenido.

**Contraste:** `#fff` sobre `#1a3a1a` = ratio 12:1 (supera el mínimo AA de 4.5:1 para texto normal).

**Relación con backend:** Ninguna.

---

### 12.14 Rendimiento — Dimensiones de imagen y lazy loading

**Archivos modificados:** Los 16 archivos HTML del proyecto.

**Problema resuelto:** Los navegadores no podían reservar espacio para las imágenes antes de cargarlas (CLS — Cumulative Layout Shift), y las imágenes del footer (below the fold) se cargaban de forma anticipada sin necesidad.

**Solución técnica:**

Logo en navbar — dimensiones explícitas para prevenir CLS (imagen real: 443×485px, escala CSS 54px de alto):
```html
<img src="assets/logo.png" alt="Logo Subvenciones Bienestar Animal" width="49" height="54">
```

Logo en footer — dimensiones + lazy loading (below the fold en todas las páginas):
```html
<img src="assets/logo.png" alt="Logo Subvenciones Bienestar Animal" width="33" height="36" loading="lazy">
```

Los valores `width`/`height` establecen el aspect ratio correcto (443÷485 ≈ 0.913). El navegador calcula el espacio exacto incluso antes de descargar el archivo.

**Relación con backend:** Ninguna.

---

### 12.15 Limpieza de CSS — eliminación de código muerto

**Archivos modificados:** `css/styles.css`

**Bloques eliminados** (confirmado mediante búsqueda en todos los HTML que ningún elemento los referenciaba):

| Bloque eliminado | Descripción |
|---|---|
| `.hero`, `.hero__titulo`, `.hero__subtitulo`, `.hero__acciones` | Sección hero original, sustituida por `.portada` en la issue 7B |
| `.seccion-transparencia`, `.transparencia__*` | Bloque de transparencia eliminado del index en revisiones anteriores |
| `.footer`, `.footer a`, `.footer a:hover`, `.footer__titulo` | Footer oscuro original, sustituido por `.footer-principal` |
| `.hero__titulo` dentro de `@media (max-width: 600px)` | Regla media query del hero eliminado |

**CSS restante actualizado:** El comentario de índice al inicio del archivo actualizado de 24 a 28 secciones, reflejando el estado real tras añadidos (skip-nav, chart responsive) y eliminaciones.

**Relación con backend:** Ninguna.

---

### 12.16 Limpieza de JS — eliminación de función muerta

**Archivos modificados:** `js/privado.js`

**Eliminada:** función `obtenerToken()` — definida en el archivo pero nunca llamada desde ningún punto. Adicionalmente, no incluía la lógica de deeplink de sessionStorage (tarea 3.1), lo que la hacía potencialmente peligrosa si alguien la hubiera conectado en el futuro.

**Accesibilidad mejorada:** `<pre id="logs-contenido">` en `admin.html` recibió `aria-label="Últimas líneas del log de acceso del servidor"` y `aria-live="polite"` para que los lectores de pantalla anuncien actualizaciones del log.

**Canvas accesibles:** Los elementos `<canvas>` en `estadisticas-epas.html` (×4), `estadisticas-eell.html` (×2) e `index.html` (×3) recibieron `role="img"` para que los lectores de pantalla los traten como imágenes descriptibles (WCAG 4.1.2).

**Relación con backend:** Ninguna.

---

### 12.17 Auditoría de rutas y enlaces

**Archivos modificados:** `entidad.html` (meta description), `exclusivo.html` (atributos BOE)

**Hallazgos y correcciones:**

`entidad.html` carecía de `<meta name="description">`. Añadido:
```html
<meta name="description" content="Consulta el historial completo de solicitudes de una entidad en todas las convocatorias de bienestar animal.">
```

Los 8 enlaces a `boe.es` en `exclusivo.html` abrían en pestaña nueva (`target="_blank"`) sin avisar al usuario. Añadido en cada uno:
```html
title="Se abre en una pestaña nueva"
```
Todos los enlaces externos ya tenían `rel="noopener noreferrer"` — confirmado correcto.

**Relación con backend:** Ninguna.

---

### 12.18 Responsive — revisión final

**Archivos modificados:** `css/styles.css`

**Verificado sin cambios:** `.tabla-scroll` ya tenía `overflow-x: auto` para `exclusivo.html`. La cuadrícula `.privado-grid` colapsaba correctamente en columna única a 640px.

**Añadido:** regla media query para reducir altura de gráficos Chart.js en pantallas muy pequeñas (≤480px):
```css
@media (max-width: 480px) {
    .chart-container         { height: 220px; }
    .chart-container--donut  { height: 180px; }
}
```

Esto evita que los gráficos de barras y de anillo desborden en pantallas de móvil estrecho, donde el canvas a 280px de alto resultaba excesivo.

**Relación con backend:** Ninguna.

---

### 12.19 Páginas de error — 404 y 50x

**Archivos creados:** `frontend/404.html`, `frontend/50x.html`

**Problema resuelto:** Nginx necesita páginas de error propias para responder con una interfaz coherente con el proyecto cuando la ruta no existe (404) o el backend falla (500/502/503/504). Sin estos archivos, el usuario veía la página de error genérica de Nginx.

**Configuración esperada en `docker/nginx/default.conf`:**
```nginx
error_page 404 /404.html;
error_page 500 502 503 504 /50x.html;
```

**Características comunes de ambas páginas:**
- Skip navigation (`class="skip-nav"`) — WCAG 2.4.1
- `<meta name="robots" content="noindex">` — evita indexación en buscadores
- `id="contenido-principal"` en `<main>`
- `aria-labelledby` en la tarjeta de error
- Navbar con todos los enlaces de navegación
- Footer accesible (logo con `loading="lazy" width="33" height="36"`)
- Reutilización de las clases CSS existentes (`auth-fondo`, `auth-card`, `btn-verde`, `btn-secundario`, `footer-principal`)
- Sin dependencias JS (fundamental en `50x.html`: el backend puede estar caído)

**Diferencias entre las páginas:**

| Aspecto | `404.html` | `50x.html` |
|---|---|---|
| Título H1 | "Página no encontrada" | "Error del servidor" |
| Código visual | "404" | "⚙️" |
| Mensaje | La ruta no existe | El servidor no pudo procesar la solicitud |
| Acciones | Volver al inicio + Ir al buscador | Volver al inicio + Reintentar (reload JS) |
| Dependencias JS | Ninguna | `window.location.reload()` inline mínimo |

**Relación con backend:** Ninguna (páginas estáticas servidas por Nginx antes de llegar al backend).

---

### 12.20 Reenvío de verificación de email

**Archivos modificados:** `verificar-email.html`

**Problema resuelto:** Si el enlace de verificación enviado por email caducaba o el usuario lo perdía, la página solo mostraba el error sin ofrecer ninguna salida. El usuario tenía que contactar con soporte o registrarse de nuevo.

**Solución técnica — HTML:** Nueva sección `#verif-reenviar` (oculta por defecto con `display:none`) insertada dentro de `.auth-card__formulario`, después del bloque de acción principal. Contiene un `<form id="form-reenviar">` con:
- Campo `<input type="email">` (autocomplete="email", required)
- Div de error `#reenviar-error` con `role="alert" aria-live="polite"`
- Div de éxito `#reenviar-ok` con `role="status" aria-live="polite"`
- Botón de envío `#btn-reenviar`

**Solución técnica — JS (inline `<script>`):** La sección se muestra llamando a `mostrarReenviar()` en dos casos:
1. No hay `?token=` en la URL (enlace incompleto)
2. La API responde con error al verificar el token (token inválido o caducado)

No se muestra si hay error de red (el problema es de conectividad, no de token).

El formulario llama a `POST /auth/reenviar-verificacion` con body `{ email }`.

**Seguridad — prevención de enumeración de usuarios:** La respuesta siempre muestra el mismo mensaje de éxito, independientemente de si el email existe o no en la base de datos:

> "Si esa dirección está registrada y pendiente de verificación, recibirás un nuevo email en breve. Revisa también el correo no deseado."

El botón se deshabilita tras un envío exitoso para evitar spam accidental. Se rehabilita solo si hay error de red.

**Endpoint requerido en backend:** `POST /auth/reenviar-verificacion`  
Body: `{ "email": string }`  
Respuesta esperada: siempre 200 (el backend no debe revelar si el email existe).

**Relación con backend:** Requiere implementar `POST /auth/reenviar-verificacion`.

---

### 12.21 Correcciones de accesibilidad y HTML (Sesión 2026-05-16)

**Atributo `title` faltante en `estadisticas-epas.html`**  
El enlace `<a href="estadisticas-epas.html" class="activo" aria-current="page">EPAs</a>` carecía del atributo descriptivo requerido para usuarios de lector de pantalla. Se añadió `title="Entidades Protectoras de Animales"`.

**Null bytes en `index.html`**  
El archivo acumuló 722 bytes nulos (posiciones 30901–31622) tras el script de reemplazo de URLs de GitHub. Se sanearon con Python (`data.rstrip(b'\x00')`). El archivo quedó en 30 901 bytes sin caracteres de control.

**URLs de GitHub corregidas en 18 páginas HTML**  
Todas las páginas contenían `href="https://github.com"` en el footer. Se actualizaron al repositorio real: `https://github.com/vcv-code/SubvDGDA`.

---

### 12.22 CSS — Section 32: Modal de conclusiones (añadida, Sesión 2026-05-16)

`modal-grafica.js` usaba las clases `.modal-grafica`, `.modal-grafica__panel`, `.card-grafico__trigger`, etc., que no tenían ninguna regla CSS. Se añadió la **Section 32** completa al final de `styles.css`:

| Selector | Función |
|---|---|
| `.card-grafico__trigger` | Botón pill "¿Qué conclusiones se sacan?" dentro de la tarjeta |
| `.modal-grafica` | Overlay posicionado en `fixed`, `display:none` por defecto |
| `.modal-grafica--visible` | Clase activa: `display:flex` |
| `.modal-grafica__backdrop` | Fondo semi-opaco, cierra al hacer clic |
| `.modal-grafica__panel` | Panel centrado `min(90vw, 720px)`, `max-height: 82vh` |
| `.modal-grafica__fondo` | PNG del gráfico como imagen de fondo tenue (`opacity:0.08`) |
| `.modal-grafica__cerrar` | Botón ✕ con `focus` automático al abrir |
| `.modal-grafica__titulo-tag` | Span `"— Conclusiones"` en gris dentro del `<h3>` del título |
| `.modal-grafica__texto p/ul/li` | Espaciado de párrafos y listas dentro del cuerpo |
| `.modal-grafica__fuentes` | Bloque de fuentes con borde superior, fuente 0.8rem |

**Actualización del contenido (2026-05-21):**

- Los textos de conclusiones pasaron de `textContent` (cadena plana) a `innerHTML` con HTML completo (`<p>`, `<ul>`, `<li>`, `<a>`). Los 9 modales tienen ahora textos analíticos de varios párrafos escritos por la autora.
- El título del modal muestra `"[Nombre gráfica] — Conclusiones"` con el sufijo en gris (`modal-grafica__titulo-tag`), eliminando la etiqueta `CONCLUSIONES` separada que había antes.
- El modal de "Evolución del importe" incluye una sección `.modal-grafica__fuentes` con 3 enlaces externos a fuentes verificadas.

---

### 12.23 CSS — Section 33: Estética visual (Sesión 2026-05-16, refinada 2026-05-17)

Toda la estética de `index.html` se encapsuló bajo el selector `body.pagina-inicio` para **impacto cero** en las otras 17 páginas.

#### 33.0 — Variables de página de inicio
```css
.pagina-inicio {
    --nav-oscuro:    #1A3429;
    --btn-cta:       #2DC26C;
    --btn-cta-hover: #25A85B;
    --hero-crema:    #F5EFE3;
    --texto-hero:    #132D1F;
    --card-radio:    16px;
    --sombra-calida: 0 4px 20px rgba(26, 52, 41, 0.11);
}
```

#### 33.1 — Navbar oscuro institucional *(neutralizado — Sesión 2026-05-17)*
Originalmente encapsulaba los estilos del navbar oscuro bajo `.pagina-inicio .navbar`: fondo `#1A3429`, texto blanco al 80 %, hover blanco puro con borde inferior CTA (`#2DC26C`), botón "Acceder"/"Cerrar sesión" pill verde brillante, `.navbar__user-link` y `.navbar__user-controls` (inyectados por `navbar.js`), logo sin filtro `invert/brightness` con `drop-shadow` sutil.

Neutralizado en la sesión de unificación: todos los estilos se migraron a **Section 3 global** (`.navbar { }`), y el bloque `.pagina-inicio .navbar { }` se reemplazó por un comentario. El navbar es idéntico en las 18 páginas del proyecto sin necesidad de override. Ver 12.27.

#### 33.2–33.4 — Hero layout + tipografía + CTA
- Contenedor a ancho completo, grid `55fr 45fr` (texto 55 %, imagen 45 %), `min-height: 280px`.
- Columna texto: padding interior con `clamp()`.
- Título: `clamp(2.2rem, 4vw, 3.4rem)`, color `--texto-hero`.
- Botón CTA: `border-radius: 50px`, `padding: 14px 36px`, verde brillante.

#### 33.5 — Imagen del hero (`<img>` HTML directo, sin clip-path)
La imagen se carga mediante una etiqueta `<img>` real en el HTML: `<img src="assets/img/home/handcat.webp">`. El contenedor `.portada-split__imagen` **no usa** `background-image` en CSS — la imagen es visible y semánticamente accesible. `object-fit: cover` mantiene la proporción sin deformar. Las imágenes alternativas están disponibles en `assets/img/home/`.

#### 33.6–33.9 — Secciones y tarjetas
- Sección datos: fondo `#FDFAF5` (crema suave).
- Métricas: fondo blanco, `border-top: 4px solid var(--btn-cta)`, radio 16 px, sombra cálida.
- `fondo-stats`: `#EEF3EE` (verde muy suave).
- Tarjetas gráfico: radio 16 px, sombra cálida.

#### 33.10 — Footer oscuro institucional *(neutralizado — Sesión 2026-05-17)*
El override `.pagina-inicio .footer-principal { background-color: #2E6B4F; border-top: 3px solid var(--color-arena); }` que existía en Section 31.5 fue **eliminado** en la sesión de unificación. Los estilos del footer son ahora globales (Section 17b) y se aplican igual en todas las páginas.

Los valores actuales (definidos en Section 17b, no en Section 33) son:

| Propiedad | Valor |
|---|---|
| Fondo | `#1A3429` — igual que el navbar |
| Texto principal | `rgba(255,255,255,0.88)` — contraste WCAG AA: > 7:1 |
| Nombre proyecto (`strong`) | `#FFFFFF` |
| Logo | `filter: drop-shadow(...)` sin inversión |
| Borde superior | Ninguno |
| Zona créditos | `#142b20` |

**Section 33.10 en styles.css:** eliminada. Contiene solo un comentario explicativo que señala la neutralización.

#### 33.11 — Responsive hero (≤768 px)
Grid de 1 columna, imagen arriba (`order: -1`), sin `clip-path`, `min-height: 200px`. La imagen del hero se carga desde el HTML (`<img src="assets/gato-portada.jpeg">`), por lo que no hay `background-position` ni `background-image` en esta sección.

---

### 12.24 CSS — Section 34: Ajustes adicionales (Sesión 2026-05-17)

#### 34.1 — Página 404 más compacta
Los `style=""` inline del HTML establecían `max-width:950px` (contenedor) y `max-width:620px` (imagen). Se sobrescriben con `!important` desde CSS sin modificar el HTML:

| Selector | Valor anterior (inline) | Valor nuevo (CSS) |
|---|---|---|
| `.auth-card--simple` | `max-width: 950px` | `max-width: 520px` |
| `.auth-card--simple img` | `max-width: 620px` | `max-width: 320px` |
| `.auth-card--simple .auth-card__formulario` | `padding: 0.75rem 2rem 2rem` | `padding: 0.5rem 1.75rem 1.75rem` |

El modificador `.auth-card--simple` es exclusivo de `404.html`.

#### 34.2 — Sección "Por qué registrarse" (index.html)
Nueva sección añadida antes del `<footer>` de `index.html`. Clases nuevas (prefijo `seccion-registro__`), sin interferir con ningún selector existente.

- Grid de 3 tarjetas (`border-top: 3px solid var(--btn-cta)`, radio 12 px, padding compacto).
- Iconos: **SVG inline** (no emojis) — barras de gráfico, campana, portapapeles con líneas.
- Beneficios: Informes personalizados · Alertas de convocatorias · Historial de solicitudes.
- Botón CTA pill verde (`border-radius: 50px`) enlazando a `registro.html`.
- Responsive: columna única en ≤ 768 px.

#### 34.3 — Layout de recuperar-password.html (Sesión 2026-05-17)
`recuperar-password.html` usa la misma clase `.auth-page` que login y registro, pero tiene diseño de una sola columna. Sin modificar el HTML, se scopa el ajuste con `:has(#recuperar-alerta)` (CSS nativo, sin JS):

```css
.auth-fondo:has(#recuperar-alerta) {
    align-items: flex-start;
    padding-top: 50px;
    padding-bottom: 50px;
}
.auth-page:has(#recuperar-alerta) {
    max-width: 460px;
}
```

- **Compatibilidad:** Chrome 105+, Firefox 121+, Safari 15.4+.  
- **Efecto:** la card se limita a 460 px, el enlace "← Volver a iniciar sesión" queda alineado con su borde izquierdo porque comparte el mismo contenedor ancho.

---

### 12.25 Correcciones de estética — Sesión 2026-05-17 (segunda ronda)

**Archivos modificados:** `css/styles.css`, `frontend/index.html`

#### Hero — eliminación de clip-path y reducción de altura

| Parámetro | Valor anterior | Valor nuevo |
|---|---|---|
| `grid-template-columns` | `45fr 55fr` (imagen mayor) | `55fr 45fr` (imagen ≤ 45 %) |
| `min-height` contenedor | `380px` | `280px` |
| `min-height` imagen | `380px` | `280px` |
| `clip-path` | `polygon(15% 0%, ...)` (3 dientes) | `none` |
| `background-position` | `center 12%` | `center 10%` |
| Móvil `min-height` | `220px` | `200px` |

#### Logo navbar — sin filtros de inversión

Eliminada la regla `filter: brightness(0) invert(1)` del logo en `.pagina-inicio .navbar__logo img`. Sustituida por `filter: drop-shadow(0 1px 4px rgba(0,0,0,0.45))` para dar profundidad sin alterar colores.

#### Footer — sin borde superior, nombre del proyecto en blanco puro

- Eliminado `border-top: 3px solid var(--btn-cta)`.
- Añadida regla `.footer-principal__marca strong { color: #FFFFFF; }` para máxima legibilidad del nombre "Proyecto BDNS/DGDA".
- Logo con `filter: drop-shadow(...)` (sin inversión), altura `40px`.

#### Sección "Por qué registrarse" — compactada

- `padding` reducido de `var(--espacio-xl)` a `var(--espacio-lg)`.
- Tarjetas: radio 12 px, padding `var(--espacio-md) var(--espacio-sm)`.
- Gap del grid: `var(--espacio-sm)` en lugar de `var(--espacio-md)`.
- Iconos SVG: `width/height: 28px` con `stroke` del color `--btn-cta`.
- Emojis eliminados del HTML y reemplazados por SVG inline accesibles con `aria-hidden="true"`.

---

### 12.26 Resumen de archivos modificados — Sesiones 2026-05-16 y 2026-05-17

| Archivo | Cambios aplicados |
|---|---|
| `css/styles.css` | Section 32 (modal), Section 33 (estética inicio + correcciones), Section 34 (ajustes) |
| `index.html` | Sección "Por qué registrarse" con SVG inline, null bytes saneados |
| `estadisticas-epas.html` | `title=` añadido al enlace EPAs |
| `404.html` + `50x.html` + 16 páginas | URLs de GitHub corregidas |
| `docs/especificaciones-frontend.md` | Secciones 12.21–12.26 integradas correctamente |

---

### 12.27 Unificación de navbar y footer — Sesión 2026-05-17

**Archivos modificados:** `css/styles.css`, `docs/especificaciones-frontend.md`

#### Contexto

Hasta esta sesión, el navbar oscuro (`#1A3429`) y el footer oscuro estaban encapsulados bajo `.pagina-inicio` (solo `index.html`). El resto de las 17 páginas mantenían el navbar blanco original y el footer verde claro. Esto generaba incoherencia visual entre páginas.

#### Cambios en `css/styles.css`

**Section 1 — Variables globales (`:root`):**  
Se añadieron las variables de identidad visual a `:root` para que estén disponibles en todas las páginas sin necesidad de heredarlas de `.pagina-inicio`:

```css
--nav-oscuro:    #1A3429;
--btn-cta:       #2DC26C;
--btn-cta-hover: #25A85B;
```

**Section 3 — Navbar (reescrita como global):**  
Se migraron todos los estilos oscuros del navbar de `.pagina-inicio .navbar` a `.navbar` (global). El navbar ahora es idéntico en las 18 páginas del proyecto:

- Fondo `#1A3429`, sombra `0 2px 14px rgba(0,0,0,0.28)`
- Logo texto `#FFFFFF`, logo img `drop-shadow` sin filtro de inversión
- Links `rgba(255,255,255,0.80)` → hover `#FFFFFF` con borde CTA
- Botón pill verde `#2DC26C`, hover `#25A85B`
- `.navbar__user-link` en blanco semitransparente (navbar.js)

**Section 17b — Footer (reescrita como global):**  
Se migraron todos los estilos oscuros del footer de `.pagina-inicio .footer-principal` a `.footer-principal` (global). El footer ahora es idéntico en las 18 páginas:

- Fondo `#1A3429`, sin borde superior (`border-top: none`)
- Nombre del proyecto (`<strong>`) en `#FFFFFF`
- Logo img `drop-shadow` sin inversión, `height: 40px`
- Zona créditos `#142b20`

**Section 33.1 y 33.10 — Neutralizadas:**  
Los overrides de `.pagina-inicio` para navbar y footer fueron reemplazados por comentarios que indican que los estilos están ahora en sus secciones globales.

#### Cabecera visual (hero con gato-portada.jpg)

La cabecera visual con imagen del gato (`portada-split`, `gato-portada.jpg`, `background-image`) es **exclusiva de `index.html`**. Está scoped bajo `.pagina-inicio .portada-split` y no se inserta en ninguna otra página. Verificado: solo aparece en `index.html`.

#### Impacto por página

| Página | Navbar antes | Navbar ahora | Footer antes | Footer ahora |
|---|---|---|---|---|
| `index.html` | Oscuro (Section 33.1) | Oscuro (Section 3 global) | Oscuro (Section 33.10) | Oscuro (Section 17b global) |
| 17 páginas restantes | Blanco | Oscuro | Verde claro | Oscuro |

---

### 12.28 Resumen de archivos modificados — Sesión 2026-05-17 (unificación)

| Archivo | Cambios aplicados |
|---|---|
| `css/styles.css` | Section 1 (vars globales), Section 3 (navbar global), Section 17b (footer global), Section 33.1/33.10 neutralizadas |
| `docs/especificaciones-frontend.md` | Secciones 4.1 y 4.2 actualizadas, 12.27–12.28 añadidas |

---

### 12.29 Corrección de imagen hero — Sesión 2026-05-17

**Problema:** El hero de `index.html` quedó roto tras la unificación de la sesión anterior. La imagen se cargaba vía `background-image` en CSS con `opacity: 0` en el `<img>`, lo que impedía su visualización correcta.

**Solución aplicada:**

- **`css/styles.css` — Section 33.5**: Eliminadas las propiedades `background-image: url('../assets/gato-portada.jpg')`, `background-size: cover` y `background-position: center 10%` del selector `.pagina-inicio .portada-split__imagen`. La imagen ahora se gestiona exclusivamente desde el HTML.
- **`css/styles.css` — Section 33.5**: Cambiado `opacity: 0` a `opacity: 1` en `.pagina-inicio .portada-split__imagen img`. La imagen es visible.
- **`css/styles.css` — Section 33.11** (responsive móvil): Eliminada la propiedad `background-position: center 10%` que ya no aplica al no haber background-image.
- **`index.html`**: Sustituido `<img src="assets/perro-gato.png">` por `<img src="assets/gato-portada.jpeg">` con alt text actualizado. Referencia a `perro-gato.png` eliminada del HTML.
- **`docs/especificaciones-frontend.md` — Section 33.5**: Descripción reescrita para reflejar la técnica correcta (imagen en HTML, no en CSS).

**Principio:** La imagen del hero se carga siempre vía etiqueta `<img>` en HTML, no vía `background-image` en CSS. Esto garantiza accesibilidad semántica y carga correcta por el navegador.

### 12.30 Resumen de archivos modificados — Sesión 2026-05-17 (restauración hero)

| Archivo | Cambios aplicados |
|---|---|
| `css/styles.css` | Section 33.5: eliminado background-image, opacity: 0 → 1; Section 33.11: eliminado background-position residual |
| `index.html` | `<img src>` cambiado de `perro-gato.png` a `gato-portada.jpeg` |
| `docs/especificaciones-frontend.md` | Section 33.5 reescrita, 12.29–12.30 añadidas |

---

### 12.31 Corrección de navbar/footer en index y layout de recuperar-password — Sesión 2026-05-17

**Problema 1 — Navbar blanco en index.html:**
La Section 31.4 del CSS contenía `.pagina-inicio .navbar { background-color: var(--color-blanco); }`, que sobreescribía el navbar verde oscuro global definido en Section 3. El índice aparecía con navbar blanco.

**Problema 2 — Footer diferente en index.html:**
La Section 31.5 del CSS contenía `.pagina-inicio .footer-principal { background-color: #2E6B4F; border-top: 3px solid var(--color-arena); }`, que divergía del footer global (#1A3429, sin borde) definido en Section 17b.

**Problema 3 — Contenedor recuperar-password.html demasiado ancho:**
`.auth-page` heredaba `max-width: 920px` (diseñado para login/registro de dos columnas). El enlace "← Volver a iniciar sesión" quedaba desalineado con la card de 480px.

**Soluciones aplicadas:**

- **`css/styles.css` — Section 31.4**: Neutralizada. Eliminado el bloque `.pagina-inicio .navbar { background-color: var(--color-blanco); }`. El navbar de index.html usa ahora el estilo global oscuro de Section 3.
- **`css/styles.css` — Section 31.5**: Neutralizada. Eliminado el bloque completo de overrides de footer en `.pagina-inicio`. El footer de index.html usa ahora el estilo global oscuro de Section 17b.
- **`css/styles.css` — Section 34.3** (nueva): Añadida sección específica para `recuperar-password.html`. Ver especificación técnica completa en [§ 34.3 de la Sección 12.24](#342--sección-por-qué-registrarse-indexhtml).

**Principio:** Los estilos de navbar y footer son globales (Sections 3 y 17b). Ninguna página tiene overrides de color para estos elementos. La clase `.pagina-inicio` solo aplica estilos propios del hero y secciones internas del index.

### 12.32 Resumen de archivos modificados — Sesión 2026-05-17 (navbar/footer/recuperar)

| Archivo | Cambios aplicados |
|---|---|
| `css/styles.css` | Section 31.4 neutralizada (navbar blanco eliminado); Section 31.5 neutralizada (footer override eliminado); Section 34.3 añadida (layout recuperar-password) |
| `docs/especificaciones-frontend.md` | 12.31–12.32 añadidas |

---

### 12.33 Tarea 13.1 — Modal de entidad en buscador.html (Sesión 2026-05-17)

Implementación completa del modal de ficha de entidad. Al hacer clic en una fila del buscador, en lugar de navegar a `entidad.html?cif=…`, se abre un modal en página con la ficha resumida.

**Archivos creados / modificados:**

| Archivo | Cambios |
|---|---|
| `css/styles.css` | Section 36 añadida (`.modal-backdrop`, `.modal-card`, `.modal-cabecera`, `.modal-cuerpo`, `.modal-pie`, `.modal-historico-tabla`, responsive ≤600 px) |
| `js/modal-entidad.js` | Nuevo. Expone `window.abrirModalEntidad(cif, nombre, openerEl)`. Fetch a `GET /solicitudes/?cif=`, rellena ficha, gestiona apertura/cierre (X, backdrop click, ESC), trampa de foco WCAG 2.4.3 |
| `buscador.html` | HTML del modal (`#modal-entidad`) añadido antes de los scripts. `<script src="js/modal-entidad.js">` añadido |
| `js/solicitudes.js` | `crearFila()`: reemplazado `window.location.href = entidad.html?cif=…` por `window.abrirModalEntidad(cif, nombre, tr)` |

**Comportamiento del modal:**
- Backdrop semitransparente (`rgba(0,0,0,0.55)`) + card centrada, máx. 640 px.
- Animación fade+scale de entrada (0.22 s).
- Muestra: nombre de entidad, CIF, CCAA, importe total concedido (solo concedidas), nº solicitudes, tabla histórica (año / tipo / estado+tramo / importe).
- Botón "Ver ficha completa →" abre `entidad.html?cif=…` en pestaña nueva.
- Cierre: botón × · clic en backdrop · tecla ESC.
- Foco devuelto al `<tr>` de origen al cerrar (WCAG 2.4.3).
- Bloquea scroll del `<body>` mientras está abierto.

---

### 12.34 Tarea 13.2 — Refactor CSS inline (Sesión 2026-05-17)

Extracción de estilos de layout, tipografía y color desde atributos `style=""` hacia clases reutilizables en `styles.css`. Los `style="display:none;"` funcionales (controlados por JS) se conservan intactos.

**Nuevas clases en `css/styles.css` (Section 35):**

| Clase | Propósito | Páginas |
|---|---|---|
| `.form-grupo--entidad` | `flex:2; min-width:200px` para campo de búsqueda de entidad | `buscador.html` |
| `.filtros__botones` | Flex row con gap y margin-top para botones de acción | `buscador.html` |
| `.leyenda-tramos` | Tipografía y color de la leyenda de tramos EELL | `buscador.html`, `entidad.html` |
| `.leyenda-tramos--entidad` | Variante con `margin-bottom:1rem` para entidad.html | `entidad.html` |
| `.info-resultados` | Tamaño y color del contador de resultados | `buscador.html` |
| `.tabla-controles__derecha` | Flex row para zona derecha de controles | `buscador.html` |
| `.form-grupo--orden` | Flex row sin margen para selector de orden | `buscador.html` |
| `.label-orden` | Tipografía compacta de la etiqueta del selector | `buscador.html` |
| `.select-orden` | `min-width:180px` para el select de orden | `buscador.html` |
| `.btn-csv` | `white-space:nowrap; font-size:0.88rem` para botón CSV | `buscador.html` |
| `.metricas-carga` | `grid-column:1/-1` en spinner de métricas | `index.html` |
| `.bloque-intro` | `margin-bottom:var(--espacio-lg)` para cabeceras de sección | `index.html`, `estadisticas-epas.html`, `estadisticas-eell.html` |
| `.bloque-titulo` | Tipografía `2rem/700/negro` de título de sección | `estadisticas-epas.html`, `estadisticas-eell.html` |
| `.bloque-titulo--md` | Variante `1.6rem` para secciones internas | `index.html` |
| `.bloque-subtitulo` | Color gris y `margin-top:4px` para subtítulo | Varias |
| `.bloque-actualizacion` | `margin-top:var(--espacio-xs)` para línea de fecha | Varias |
| `.link-fuente` | `font-size:0.9rem; color:var(--color-azul)` para fuentes | Varias |
| `.mb-lg` | Utilidad: `margin-bottom:var(--espacio-lg)` | Varias |
| `.mt-xl` | Utilidad: `margin-top:var(--espacio-xl)` | `index.html`, `estadisticas-eell.html` |
| `.convocatorias-bloque` | Layout centrado del bloque de convocatorias | `index.html` |
| `.sub-bloque__titulo` | H3 de sub-bloque (1.1rem/700) | `index.html` |
| `.sub-bloque__titulo--centrado` | Variante centrada del anterior | `index.html` |
| `.sub-bloque__subtitulo` | Párrafo descriptivo centrado de sub-bloque | `index.html` |
| `.card-grafico__titulo--centrado` | Título de tarjeta centrado | `index.html` |
| `.convocatorias-nota` | Nota tipográfica pequeña bajo tabla convocatorias | `index.html` |
| `.card-grafico__numero` | Número grande (`3.5rem/700/verde`) en tarjeta KPI | `index.html` |
| `.card-grafico__nota` | Texto secundario bajo el número | `index.html` |
| `.card-grafico__pie` | `margin-top:auto` + padding para pie de tarjeta | `index.html` |
| `.link-estadistica` | Enlace inline azul en tarjetas de gráfico | `index.html` |
| `.card-grafico--col` | Variante flex-column de `.card-grafico` | `index.html` |
| `.chart-container--centrado` | Flex centrado para placeholder de mapa | `estadisticas-eell.html` |
| `.mapa-placeholder` | Contenedor centrado del placeholder del mapa de calor | `estadisticas-eell.html` |
| `.mapa-placeholder__icono` | Icono emoji 2.5rem del placeholder | `estadisticas-eell.html` |
| `.mapa-placeholder__texto` | Texto 0.9rem del placeholder | `estadisticas-eell.html` |

---

### 12.35 Resumen de archivos modificados — Sesión 2026-05-17 (Tareas 13.1 y 13.2)

| Archivo | Cambios aplicados |
|---|---|
| `css/styles.css` | Sections 35 (refactor inline) y 36 (modal de entidad) añadidas |
| `js/modal-entidad.js` | Creado (modal de ficha de entidad) |
| `js/solicitudes.js` | `crearFila()`: navegación reemplazada por apertura de modal |
| `buscador.html` | HTML del modal añadido; clases refactorizadas; scripts actualizados |
| `index.html` | Clases refactorizadas (metricas-carga, bloques de gráficos) |
| `estadisticas-epas.html` | Cabecera y grids refactorizados (`.bloque-intro`, `.mb-lg`) |
| `estadisticas-eell.html` | Cabecera, grids y mapa placeholder refactorizados |
| `entidad.html` | Leyenda de tramos refactorizada |
| `docs/especificaciones-frontend.md` | 12.33–12.35 añadidas; 33.10, 33.11, 34.3 corregidas |

### 12.36 Correcciones puntuales — Sesión 2026-05-18

**Archivos modificados:** `buscador.html`, `admin.html`, `css/styles.css`

#### Bug botón CSV (`buscador.html`)
El botón `#btn-descargar-csv` tenía duplicado el atributo `class=""` (uno con `btn btn-secundario` y otro con `btn-csv`). Unificados en un único atributo: `class="btn btn-secundario btn-csv"`.

#### Inline styles en `<h2>` de admin.html
Los cuatro `<h2>` de las secciones de admin llevaban `style="font-size:inherit;font-weight:inherit;margin:0;"`. Creada clase `.titulo-admin` en `styles.css` (junto a los demás estilos de admin) con esas mismas propiedades. Inline styles eliminados y clase aplicada.

#### Restauración de colores de badges
Las variables de color de estado (en `:root`) se habían asignado de forma invertida. Corregido el swap:

| Variable | Valor anterior (incorrecto) | Valor restaurado |
|---|---|---|
| `--estado-no-beneficiaria` | `#C62828` (rojo) | `#B45309` (ámbar) |
| `--estado-excluida` | `#B45309` (ámbar) | `#C62828` (rojo) |

Ningún otro badge ni color fue modificado. Las clases `.badge-no-beneficiaria` y `.badge-excluida` consumen las variables — no requirieron cambios.

---

### 12.37 Ajustes finales de contenido, responsive y correcciones — 2026-05-21

**Archivos modificados:** `css/styles.css`, `js/home.js`, `js/estadisticas-epas.js`, `js/estadisticas-eell.js`, `js/modal-grafica.js`, `js/mapa-ccaa.js`, `js/solicitudes.js`, `privado.html`, `exclusivo.html`, `admin.html`, `backend/app/routers/estadisticas.py`, `backend/app/routers/solicitudes.py`

#### Navbar — tamaño de fuente unificado

- Fuente de `.navbar__links a` subida a `1.15rem` (antes `0.95rem`)
- `.navbar__user-link` (Mi perfil) ya no tiene `font-size` propio — hereda del selector general
- `.btn-login` (Acceder / Cerrar sesión) recibe `font-size: 1.15rem` explícito (los `<button>` no heredan de los `<a>`)
- Nuevo breakpoint `@media (max-width: 1024px) and (min-width: 769px)` reduce ambos a `1rem` para evitar solapamiento en pantallas medianas

#### Modal de conclusiones — contenido HTML completo

- `modal-grafica.js` cambia de `textContent` a `innerHTML`; el contenedor `.modal-grafica__texto` pasa de `<p>` a `<div>`
- El título muestra `"Título — Conclusiones"` con el sufijo en un `<span class="modal-grafica__titulo-tag">` en gris; se elimina la etiqueta `CONCLUSIONES` separada
- Nuevas reglas CSS: `.modal-grafica__texto p`, `ul`, `li`, `.modal-grafica__fuentes` (fuentes con borde superior)
- Panel ampliado a `720px` / `82vh`; fuente del cuerpo a `1rem` / line-height `1.65`
- Los 9 modales de conclusiones tienen ahora textos reales de varios párrafos

#### Distribución de importes EPA — corrección de rangos

- Eliminado el rango `> 10.000 €`: verificado en BD que el importe máximo real es exactamente 10.000 €
- Los 8 registros con importe = 10.000 € reclasificados al bucket `8.000–10.000 €` ajustando el límite superior a `10_001`
- `GET /estadisticas/epas` devuelve ahora 5 rangos en lugar de 6

#### Ordenación server-side en buscador

- `GET /solicitudes/` acepta nuevo parámetro `?orden=` con valores `entidad-az` (defecto), `importe-desc`, `importe-asc`
- El backend aplica `ORDER BY` en SQL mediante subconsulta correlacionada sobre `concesiones.importe`, antes del `OFFSET`/`LIMIT`
- El frontend pasa `?orden=` en cada petición; cambiar el select de orden lanza nueva búsqueda desde página 1
- El criterio de orden se incluye en la URL persistida (excepto `entidad-az` por defecto)
- Antes: la ordenación era client-side sobre los 50 resultados de la página activa (bug)

#### Reordenación de gráficas en Home

| Posición | Antes | Después |
|---|---|---|
| Fila 1 izquierda | Evolución (línea) | Evolución (línea) |
| Fila 1 derecha | Distribución (rosco) | EPA vs EELL (barras) |
| Fila 2 izquierda | EPA vs EELL (barras) | Distribución (rosco) |
| Fila 2 derecha | Tasa éxito (KPI) | Tasa éxito (KPI) |

#### Auditoría responsive móvil — 8 correcciones

**Hamburguesa tras login (JS):**
`navbar.js` no estaba incluido en `privado.html`, `exclusivo.html` ni `admin.html`. Al no haber event listeners, el botón hamburguesa no funcionaba en esas páginas tras hacer login. Se añade `<script src="js/navbar.js">` en los tres archivos. `actualizarNavbar()` devuelve early (no encuentra `a.btn-login`) sin tocar el DOM; `iniciarHamburguesa()` registra los listeners correctamente.

**Mapa táctil:**
En dispositivos touch, `mouseover` no se dispara. Al tocar una CCAA, ahora se muestra el tooltip (nombre + importe, 900 ms) antes de abrir el modal de top municipios.

**Footer links en móvil:**
Añadido `align-items: center` y `justify-content: center` a la zona y nav del footer en `@media (max-width: 600px)`.

**Tabla resultados buscador — alineación en móvil:**
Los valores de la tabla de resultados (modo card en ≤600px) tienen ahora `text-align: right` uniforme; el label `::before` mantiene `text-align: left`. Cambiado `align-items: center` → `flex-start` para nombres largos que ocupan varias líneas.

**Tablas admin — scroll horizontal en móvil:**
`@media (max-width: 768px)`: `.admin-seccion { overflow: visible }` y `.admin-seccion__cuerpo { overflow-x: auto }`. Antes, `overflow: hidden` en `.admin-seccion` bloqueaba el scroll de la tabla interior.

**Tabla resumen exclusivo — scroll horizontal en móvil:**
`@media (max-width: 768px)`: `.resumen-tabla-card { overflow: visible }` y `.resumen-tabla { table-layout: auto !important; min-width: 520px }`. El inline `style="table-layout:fixed"` del JS comprimía las columnas en lugar de forzar scroll.

**Badge DISPONIBLE / PRÓXIMAMENTE:**
Añadido `padding-top: calc(var(--espacio-sm) + 1.6rem)` a `.seccion-registro__card` en ≤768px para que el badge `position: absolute` no solape el primer ítem del listado.

**Filtros buscador:**
Añadido `text-align: left` explícito a `.filtros__fila .form-grupo` y sus labels en `@media (max-width: 600px)`. Botones centrados con `justify-content: center`.

#### Navbar — mejoras de navegación (segunda ronda)

- Breakpoint hamburguesa subido de `768px` a `900px` — el navbar ya tiene demasiados items para caber inline en pantallas intermedias
- Rango `901–1024px` mantiene `1rem`; solo `>1024px` usa `1.15rem`
- Link **"Exclusivo"** añadido: `navbar.js` lo inyecta en `actualizarNavbar()` como `<a class="navbar__user-link" href="exclusivo.html">`; pre-renderizado en `privado.html`, `exclusivo.html` (con `aria-current="page"`) y `admin.html`
- Link **"Mi perfil"** añadido en `exclusivo.html` (con `aria-current="page"`) y `privado.html`
- `navbar__user-controls`: `gap` cambiado a `var(--espacio-lg)` = 32px para igualar separación con otros links; `align-items: baseline` para alineación tipográfica correcta con otros enlaces
- Navbar `z-index` 1000→1200 — Leaflet fija sus controles a z-index 1000, el menú hamburguesa quedaba por debajo
- Hamburguesa `z-index` 999→1001
- Botón "Cerrar sesión" en hamburguesa: `font-size: 1rem` (igualado al resto); separador entre "Mi perfil" y "Exclusivo" con `border-top`; `width: 100%` en `navbar__user-link` para que el borde ocupe el ancho completo

#### Mapa de calor CCAA — interacción táctil completa

**Problema previo:** `mouseover` no se dispara en touch; el tooltip de Leaflet quedaba por debajo de controles (z-index 650 del pane vs 1000 de los controles).

**Solución implementada:**

- `doubleClickZoom: false` en touch (para usar doble toque propio)
- `unbindTooltip()` en todos los layers en touch — se sustituye por `.mapa-info-central`
- Tooltip pane subido a `z-index: 1050` vía `_mapaInstancia.getPane('tooltipPane').style.zIndex`
- **Un toque** (touchend): muestra `.mapa-info-central` (div absoluto centrado, z-index 1200) con nombre, importe y concesiones; resalta el polígono con hover
- **Doble toque** (≤400ms entre toques): cierra info, resetea estilo, abre modal top municipios
- **Auto-cierre** del info box tras 8s sin doble toque
- Hint contextual `.mapa-ccaa-hint` (solo móvil, `display: none` en desktop): texto inicial → "Doble toque para ver el top de municipios" al tocar → vuelve al original
- `fitBounds(capaGeojson.getBounds(), { padding: [8, 8] })` en `window.innerWidth <= 768` para ajustar automáticamente la vista a España
- Leyenda reducida en ≤768px: `font-size: 0.68rem`, `padding: 6px 8px`, cuadros de 10px
- Eliminado subtítulo "Escala de quintiles sobre importe total concedido" de la card del mapa

**Desktop:** sin cambios — `sticky: true`, `mouseover`/`mouseout`/`click` como siempre.

#### Modal conclusiones — fixes de calidad

- Título construido con `textContent + appendChild` en lugar de `innerHTML` (evita XSS con caracteres especiales en el título)
- `.modal-grafica__cuerpo` con `flex: 1; min-height: 0` para que el scroll interno funcione correctamente en flex containers con `max-height`
- Modal top municipios CCAA: `grid-template-columns: 1fr` en `≤768px` (antes `600px`) — en pantallas de 640-768px las dos columnas quedaban muy estrechas

### 12.38 Enlaces a bases reguladoras en la sección "Convocatorias" de la home — 2026-05-23

**Archivos modificados:** `index.html`, `css/styles.css`

**Problema:** la sección "Convocatorias" de la home muestra para cada año (2021–2026) la fecha de publicación en el BOE y un enlace directo a la resolución, pero **no** ofrecía acceso a las **bases reguladoras** — el documento normativo que define cómo se evalúan las solicitudes y cómo se reparten los importes. Para un proyecto de análisis de subvenciones, la base reguladora es la fuente legal de referencia.

**Solución:** se añade una línea breve bajo cada una de las dos tablas (EPA y EELL) con enlaces directos a los PDFs oficiales. Tres documentos en total:

| Tabla | Documento | Origen |
|---|---|---|
| EPA | Bases reguladoras EPAs 2021 | BOE (`BOE-A-2021-16021`) |
| EPA | Modificación bases EPAs 2024 | DGDA (web institucional) |
| EELL | Bases reguladoras EELL 2023 | DGDA (web institucional) |

**Implementación técnica:**

- Reutilizada la clase `.convocatorias-nota` ya existente (misma usada por el asterisco *"Período subvencionable de 6 meses"*). Mismo tamaño (`0.8rem`) y mismo color de texto (`--color-gris-texto`), por lo que no compite visualmente con la tabla.
- Nueva regla CSS `.convocatorias-nota a` con color `var(--color-azul)` (`#1565C0`) y `text-decoration: underline`, coherente con el enlace "Volver al inicio" de las páginas legales. El hover quita el subrayado como feedback visual. El verde primario heredado por defecto tenía poco contraste sobre el fondo verde claro de la sección.
- Atributos `target="_blank"` y `rel="noopener noreferrer"` en los tres enlaces (no exponen `window.opener`).
- `aria-label` descriptivo en cada enlace que indica el formato del documento (PDF) y su origen (BOE o DGDA), para lectores de pantalla.

**Relación con backend:** ninguna. Contenido estático puro.

Las siguientes tareas están planificadas pero no implementadas. Cada una tiene su especificación aquí y su referencia en el changelog cuando se complete.

### 13.1 Modal de entidad en buscador.html *(completada — 2026-05-17)*

Ver implementación completa en [§ 12.33](#1233-tarea-131--modal-de-entidad-en-solicitudeshtml-sesión-2026-05-17).

### 13.2 Refactor CSS inline *(completada — 2026-05-17)*

Ver implementación completa en [§ 12.34](#1234-tarea-132--refactor-css-inline-sesión-2026-05-17).

### 13.3 Mapa de calor de CCAA en estadísticas EELL

**Estado:** pendiente  
**Página:** `estadisticas-eell.html`  
**Objetivo:** Sustituir el placeholder actual del mapa por un mapa real de calor de comunidades autónomas que represente el importe total concedido por CCAA.

**Especificación técnica:**

- **Datos:** el endpoint `GET /estadisticas/eell/` ya devuelve `por_ccaa[]` con `ccaa`, `importe_total`, `num_concesiones`. No requiere cambios en el backend.
- **Librería propuesta:** [Leaflet.js](https://leafletjs.com/) con [GeoJSON de CCAA españolas](https://github.com/codeforgermany/click_that_hood/blob/main/public/data/spain-communities.geojson) o equivalente de dominio público.
- **Alternativa sin librería:** SVG estático de España con `<path>` por CCAA, coloreado dinámicamente con JS interpolando entre blanco y `var(--color-verde-btn)`.
- **Accesibilidad:** tabla de datos accesible como alternativa al mapa (WCAG 1.1.1 — Non-text Content).
- **CSS:** clases nuevas en Section 36 o 37, prefijo `.mapa-ccaa__`.
- **Selector de métrica:** botón o select que alterne entre "Importe total" y "Nº concesiones".

**Archivos afectados cuando se implemente:**

| Archivo | Cambio previsto |
|---|---|
| `estadisticas-eell.html` | Sustituir `#mapa-ccaa-container` placeholder por mapa real |
| `js/estadisticas-eell.js` | Función `pintarMapaCCAA(datosCcaa)` |
| `css/styles.css` | Nuevas clases `.mapa-ccaa__*` |

