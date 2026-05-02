# Especificaciones Técnicas del Frontend
## Proyecto BDNS/DGDA — Subvenciones de Bienestar Animal

**Proyecto:** Análisis de Subvenciones de Bienestar Animal y Colonias Felinas  
**Curso:** 2º DAW — Proyecto Final de Ciclo  
**Issues cubiertas:** 7B (Estructura HTML/CSS/JS) · 7C (Lógica fetch/filtros/gráficos) · 7D (Mejoras de frontend + páginas Recursos y Estadísticas avanzadas)  
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
El frontend se ha construido con **HTML5 + CSS3 + JavaScript Vanilla** y se prevé añadir **Bootstrap** (diseño responsivo adicional) y **Chart.js** (gráficos) en la issue 7C.

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

### Bootstrap y Chart.js (issue 7C)

Estas dos librerías se importan desde CDN (Content Delivery Network) directamente en el HTML, sin necesidad de instalación local. Son herramientas ampliamente usadas en el sector profesional y reconocibles en la defensa del proyecto.

---

## 2. Estructura de archivos

```
frontend/
│
├── css/
│   └── styles.css          → Hoja de estilos compartida por todas las páginas
│
├── js/
│   ├── home.js                      → Lógica de index.html
│   ├── solicitudes.js               → Lógica del buscador
│   ├── estadisticas.js              → Lógica del dashboard con Chart.js
│   ├── estadisticas-avanzadas.js    → Lógica de estadísticas avanzadas (KPIs, gráficos CCAA, ranking)
│   ├── recursos.js                  → Lógica del directorio de recursos (pendiente de endpoint)
│   ├── auth.js                      → Lógica de login y registro (JWT)
│   ├── privado.js                   → Control de acceso y contenido de zona privada
│   └── entidad.js                   → Lógica de la ficha de entidad
│
├── assets/
│   ├── logo.png                → Logotipo del proyecto (también usado como favicon)
│   ├── perro-gato.png          → Foto para la portada (portada-split)
│   ├── animales-login.png      → Foto decorativa en login.html
│   ├── animales-registro.png   → Foto decorativa en registro.html
│   └── wireframes_...pdf       → Wireframes de referencia (issue 7A)
│
├── index.html                       → Página de inicio (Home)
├── solicitudes.html                 → Buscador de solicitudes con filtros
├── estadisticas.html                → Dashboard de gráficos con Chart.js
├── estadisticas-avanzadas.html      → Análisis avanzado: CCAA, EPA vs EELL, ranking (Issue 7D)
├── recursos.html                    → Directorio de organizaciones y sitios de interés (Issue 7D)
├── login.html                       → Formulario de inicio de sesión
├── registro.html                    → Formulario de creación de cuenta
├── privado.html                     → Zona exclusiva para usuarios registrados
├── entidad.html                     → Ficha de entidad con historial y desglose de agrupaciones
├── diseño.md                        → Guía visual del proyecto (issue 7A)
└── especificaciones-frontend.md     → Este documento
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
| `--color-azul` | `#1565C0` | Azul institucional — badge Agrupación, spinner |
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

Barra de navegación fija (`position: fixed`) de 80px de altura. Contiene el logo y el nombre **"Subvenciones DGDA"** a la izquierda (texto en negro, alineado visualmente con el logo) y los enlaces de navegación a la derecha. El enlace de la página actual recibe la clase `activo` que aplica un subrayado verde; también se añade `aria-current="page"` para accesibilidad.

El botón "Acceder" tiene un estilo diferente (fondo verde, texto blanco) para destacarlo como la acción principal de autenticación.

**Estructura actual del navbar (Issue 7D) — 6 enlaces, en este orden:**

| Posición | Enlace | Destino | Clase especial |
|---|---|---|---|
| 1 | Inicio | `index.html` | `activo` en home |
| 2 | Buscador | `solicitudes.html` | `activo` en buscador |
| 3 | Estadísticas | `estadisticas.html` | `activo` en estadísticas |
| 4 | Estadísticas avanzadas | `estadisticas-avanzadas.html` | `activo` en estadísticas avanzadas |
| 5 | Recursos | `recursos.html` | `activo` en recursos |
| 6 | Acceder | `login.html` | `.btn-login` (botón verde) |

Todas las páginas del proyecto han sido actualizadas para incluir este navbar con los 6 enlaces. El patrón de accesibilidad (`role="navigation"`, `aria-label`, `aria-current="page"`) y los estilos se mantienen uniformes en todas las páginas.

**¿Por qué fijo?** En páginas largas como la Home o el Buscador, el usuario necesita poder navegar a otras secciones sin tener que volver al inicio de la página.

**Cambios en Issue 7D:** el nombre del proyecto en el navbar se actualizó de "Bienestar Animal" a **"Subvenciones DGDA"** y el color del texto pasó a negro (`var(--color-negro)`) para armonizar con el logotipo. Además se añadieron los enlaces a "Estadísticas avanzadas" y "Recursos".

### 4.2 Footer

Footer en dos zonas:
- **Zona principal** (verde claro `#E1FEE5`): logo del proyecto a la izquierda, enlaces GitHub / Documentación / Contacto a la derecha.
- **Zona de créditos** (verde más oscuro `#bbfdc3`): crédito de los datos (BDNS y DGDA) y aviso de proyecto educativo.

**Sticky footer:** El footer siempre aparece al pie de la ventana, incluso cuando el contenido es corto. Se consigue con `display: flex; flex-direction: column; min-height: 100vh` en el `body` y `flex: 1` en `main`.

### 4.3 Tarjetas (Cards)

Se usan tres variantes de tarjeta:

- **`.card`** — tarjeta base: fondo blanco, sombra suave, bordes redondeados.
- **`.card-metrica-verde`** — tarjeta de métrica: fondo verde suave, número grande y label encima.
- **`.card-anio`** — tarjeta de convocatoria por año: año en grande, estado "Cerrada", líneas EPA/EELL con importe y enlace a resultados.

### 4.4 Badges de estado y agrupación

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

### 4.5 Grids

Se usan dos grids CSS para distribuir tarjetas:
- **`.grid-3`** — 3 columnas en escritorio, 2 en tablet, 1 en móvil.
- **`.grid-2`** — 2 columnas en escritorio y tablet, 1 en móvil.

Los breakpoints son 900px (tablet) y 600px (móvil).

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

**HTML** (presente en `solicitudes.html`, `entidad.html`, `estadisticas.html`, `index.html`, `recursos.html` y `estadisticas-avanzadas.html`):

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

**HTML** (presente en `solicitudes.html`, `entidad.html`, `estadisticas.html`, `index.html`, `recursos.html` y `estadisticas-avanzadas.html`):

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

## 5. Páginas del sistema

### 5.1 Home — `index.html`

**Propósito:** Presentar el proyecto, mostrar las cifras clave y dar acceso rápido a las herramientas principales.

**Cambios en Issues 7C/7D:**
- Favicon configurado con `<link rel="icon" href="assets/logo.png">`.
- Metadatos Open Graph (`og:title`, `og:description`, `og:image`) añadidos en el `<head>`.
- KPI "Entidades únicas" conectado con el dato real de la API (`datos.entidades_unicas`).
- Botón "Conócenos" → sustituido por "Ver solicitudes" enlazando a `solicitudes.html`.
- Spinner de carga sobre las métricas.
- Caja de error visual si el backend no responde.

**Secciones:**

| Sección | Contenido | Datos |
|---|---|---|
| Portada partida | Título "Sobre el proyecto" + descripción + foto de animales | Estático |
| Datos y métricas | 3 tarjetas: total solicitudes, importe concedido, entidades únicas | API `/estadisticas/` |

Las secciones "Convocatorias recientes" y "Transparencia" se eliminaron para simplificar la página y centrar el foco en los datos clave.

**Archivo JS:** `js/home.js` — una sola petición a `/estadisticas/` alimenta todos los bloques.

### 5.2 Buscador — `solicitudes.html`

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

**Control de orden:** encima de la tabla aparece `.tabla-controles` con el recuento de resultados a la izquierda y a la derecha el selector de orden y el botón de exportación. Opciones de orden: Entidad (A → Z), Importe mayor → menor, Importe menor → mayor. La ordenación es client-side sobre los resultados de la página actual.

**Exportación CSV:** el botón "↓ Descargar CSV" construye la URL `/solicitudes/export` con los filtros activos (`buscar`, `tipo`, `ccaa`, `anio`, `estado`) —sin `pagina` ni `limite`— y redirige con `window.location.href`. El backend genera y sirve el fichero CSV completo (todos los resultados de la búsqueda, sin paginación). No hay lógica de generación CSV en el cliente.

```javascript
function descargarCSV() {
    const filtros = leerFiltros();
    const params  = new URLSearchParams();
    if (filtros.nombre) params.set('buscar', filtros.nombre);
    if (filtros.tipo)   params.set('tipo',   filtros.tipo);
    if (filtros.ccaa)   params.set('ccaa',   filtros.ccaa);
    if (filtros.anio)   params.set('anio',   filtros.anio);
    if (filtros.estado) params.set('estado', filtros.estado);
    window.location.href = `${API_URL}/solicitudes/export?${params.toString()}`;
}
```

**Paginación:** 50 resultados por página. Parámetros `limite` y `pagina` en la URL de la API.

**Enlace a ficha:** al hacer clic en cualquier fila se navega a `entidad.html?cif=...`.

**Parámetros por URL:** la página acepta `?anio=`, `?tipo=` y `?estado=` para pre-rellenar filtros desde enlaces externos.

**Archivo JS:** `js/solicitudes.js`.

### 5.3 Estadísticas — `estadisticas.html`

**Propósito:** Dashboard con visualizaciones de datos.

**Cambios en Issue 7D:** spinner de carga y caja de error visual añadidos.

**KPIs (fila superior, orden definitivo):**

| Posición | KPI | Cálculo |
|---|---|---|
| 1 | Registros totales | `datos.total_registros` |
| 2 | Importe concedido € | `datos.importe_global` |
| 3 | Entidades únicas | `datos.entidades_unicas` (dato real de la API) |
| 4 | % Concedido | `(total_concedidas / total_registros) × 100` (client-side) |

**Gráficos implementados:**

| Gráfico | Tipo | Datos |
|---|---|---|
| Evolución del importe por año | Línea | `/estadisticas/` → `por_anio.importe_total` |
| Distribución por estado | Donut | `/estadisticas/` → totales por estado |
| EPA vs EELL por año (M€) | Barras agrupadas | `/estadisticas/` → `por_anio` por tipo |
| Top 5 entidades por importe | Ranking HTML | Endpoint pendiente de backend |

**Librería:** Chart.js 4.4.0 importada desde CDN jsDelivr. Se usa `new Chart()` con tipos `line`, `doughnut` y `bar`.

### 5.4 Ficha de entidad — `entidad.html` + `js/entidad.js`

**Propósito:** Mostrar el historial completo de participación de una entidad en todas las convocatorias.

**Cambios en Issue 7D:** desglose de municipios para solicitudes que pertenecen a una agrupación EELL.

**Contenido de la página:**
- Nombre de la entidad
- CIF
- Bloque `#agrupacion-detalle` (oculto por defecto, visible si hay agrupación)
- Tabla de historial con: Año de convocatoria, Tipo (EPA/EELL), Estado (badge de color), Importe concedido, Número de expediente

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
- `#agrupacion-representante` → `datos.representante`
- `#agrupacion-num-municipios` → `datos.num_municipios`
- `#agrupacion-miembros > tbody` → lista de miembros con `nombre`, `cif` e `importe_asignado`

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
1. El usuario hace clic en una fila de `solicitudes.html`.
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

### 5.5 Recursos — `recursos.html` + `js/recursos.js` (Issue 7D)

**Propósito:** Directorio de organizaciones, portales de datos públicos y referencias útiles para entidades que trabajan en bienestar animal o solicitan subvenciones públicas.

**Estado:** Estructura completa implementada. El contenido dinámico queda pendiente hasta que el backend exponga el endpoint `GET /recursos/`.

**Estructura HTML:**

| Bloque | ID / clase | Descripción |
|---|---|---|
| Spinner de carga | `#spinner .spinner` | Visible mientras se espera respuesta del backend |
| Caja de error | `#error-box .error-box` | Muestra `mensaje` + `sugerencia` en errores 4xx/5xx |
| Cabecera | `.seccion__cabecera` | Título y subtítulo estáticos |
| Contenedor dinámico | `#recursos-contenido` | JS insertará aquí las tarjetas de recursos |
| Placeholder inicial | `#recursos-placeholder .card` | Visible hasta que el endpoint esté disponible |

**Archivo JS — `recursos.js`:**

- `cargarRecursos()` — patrón idéntico al del resto del proyecto (spinner → fetch comentado con TODO → catch → finally).
- `pintarRecursos(recursos)` — agrupa los recursos por categoría y construye un `<div class="grid-3">` por categoría con `<article class="card">` por recurso.
- `crearTarjetaRecurso(recurso)` — devuelve un `<article class="card">` con logo (opcional), nombre como enlace externo y descripción.
- `mostrarSinResultados()` — muestra mensaje cuando el endpoint devuelve array vacío.

**Endpoint pendiente de backend:**

```
GET /recursos/
Respuesta esperada: [
  {
    nombre:      string,
    url:         string,
    descripcion: string,
    categoria:   string,
    logo:        string | null
  },
  ...
]
```

**Notas de implementación:**
- No se ha creado CSS nuevo para esta página; usa las clases existentes (`.card`, `.grid-3`, `.seccion`, etc.).
- El placeholder usa `class="card"` (no `.tarjeta`, que no existe en `styles.css`).
- El fetch real está completamente comentado en `recursos.js`; descomenterlo cuando el backend implemente el endpoint.

---

### 5.6 Estadísticas avanzadas — `estadisticas-avanzadas.html` + `js/estadisticas-avanzadas.js` (Issue 7D)

**Propósito:** Análisis detallado por CCAA, comparativa EPA vs EELL, líneas de actuación EPA 2025 y ranking de comunidades autónomas por importe concedido. Complementa a `estadisticas.html` sin modificarla.

**Estado:** Estructura completa implementada. Los datos dinámicos quedan pendientes hasta que el backend exponga los endpoints `GET /estadisticas/avanzadas/` y `GET /estadisticas/por-ccaa/`.

**Fondo visual:** usa la clase `.fondo-stats` (verde suave) para mantener coherencia visual con `estadisticas.html`.

**Estructura HTML:**

| Bloque | ID | Descripción |
|---|---|---|
| Spinner | `#spinner` | Patrón estándar del proyecto |
| Caja de error | `#error-box` | Patrón estándar del proyecto |
| KPIs avanzados | `#kpis-avanzados .grid-4` | 4 tarjetas de métricas avanzadas |
| Gráfico CCAA | `#grafico-ccaa-container` | Canvas oculto + placeholder "Pendiente de endpoint" |
| Gráfico tasa concesión | `#grafico-tasa-container` | Canvas oculto + placeholder "Pendiente de endpoint" |
| Gráfico líneas EPA 2025 | `#grafico-lineas-container` | Canvas oculto (donut) + placeholder |
| Ranking CCAA | `#ranking-ccaa` | Lista `<ul>` rellenable por JS |

**KPIs implementados (pendientes de datos):**

| ID | Label | Dato esperado |
|---|---|---|
| `#kpi-importe-medio-epa` | Importe medio EPA | Por entidad concedida |
| `#kpi-importe-medio-eell` | Importe medio EELL | Por entidad concedida |
| `#kpi-ccaa-top` | CCAA con más concesiones | EELL 2023–2025 |
| `#kpi-agrupaciones` | Agrupaciones EELL | Con desglose municipal |

**Gráficos preparados en `estadisticas-avanzadas.js`:**

| Función | Tipo Chart.js | Canvas | Endpoint |
|---|---|---|---|
| `poblarGraficoCcaa()` | Barras horizontales (`bar` + `indexAxis: 'y'`) | `#grafico-ccaa` | `/estadisticas/por-ccaa/` |
| `poblarGraficoTasa()` | Líneas (`line`) | `#grafico-tasa` | `/estadisticas/avanzadas/` |
| `poblarGraficoLineas()` | Donut (`doughnut`) | `#grafico-lineas` | `/estadisticas/avanzadas/` |
| `poblarRankingCcaa()` | Lista HTML (top 10) | `#ranking-ccaa` | `/estadisticas/por-ccaa/` |

**Endpoints pendientes de backend:**

```
GET /estadisticas/avanzadas/
Respuesta esperada: {
  importe_medio_epa:    number,
  importe_medio_eell:   number,
  ccaa_top:             string,
  num_agrupaciones:     number,
  tasa_concesion:       [{ anio, tasa_epa, tasa_eell }, ...],
  lineas_epa_2025:      { abandonados: number, colonias: number }
}

GET /estadisticas/por-ccaa/
Respuesta esperada: [
  { ccaa: string, importe_total: number, num_concesiones: number },
  ...
]
```

**Notas de implementación:**
- La página es **independiente** de `estadisticas.html`; no reutiliza ni modifica su código.
- Chart.js 4.4.0 se importa desde CDN jsDelivr, igual que en `estadisticas.html`.
- Todos los canvas están ocultos con `style="display:none;"` y solo se muestran cuando hay datos reales.
- Los fetch están completamente comentados en `estadisticas-avanzadas.js`; descomenterlos cuando el backend implemente los endpoints.
- Incluye un enlace "← Volver a Estadísticas generales" que lleva a `estadisticas.html`.

---

### 5.7 Login y Registro — `login.html` / `registro.html`

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

### 5.8 Zona exclusiva — `privado.html` + `js/privado.js`

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

## 6. Integración con la API REST

### Endpoints disponibles y su uso en el frontend

| Endpoint | Método | Parámetros / Body | Páginas que lo usan |
|---|---|---|---|
| `/estadisticas/` | GET | — | Home (métricas), Estadísticas (KPIs y gráficos) |
| `/solicitudes/` | GET | `anio`, `tipo`, `estado`, `buscar`, `ccaa`, `provincia`, `linea`, `limite`, `pagina` | Buscador |
| `/solicitudes/?cif=` | GET | `cif` | Ficha de entidad |
| `/solicitudes/export` | GET | `anio`, `tipo`, `estado`, `buscar`, `ccaa` (sin `pagina` ni `limite`) | Buscador (botón CSV) |
| `/agrupaciones/{id_solic}` | GET | — | Ficha de entidad (desglose de municipios) |
| `/estadisticas/avanzadas/` | GET | — | Estadísticas avanzadas (KPIs, tasa concesión, líneas EPA 2025) — **pendiente de backend** |
| `/estadisticas/por-ccaa/` | GET | — | Estadísticas avanzadas (gráfico CCAA, ranking) — **pendiente de backend** |
| `/recursos/` | GET | — | Recursos (tarjetas de directorio) — **pendiente de backend** |
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
| Estadísticas avanzadas | ⏳ `/estadisticas/avanzadas/` | Pendiente — fetch comentado en `estadisticas-avanzadas.js` |
| Distribución por CCAA | ⏳ `/estadisticas/por-ccaa/` | Pendiente — fetch comentado en `estadisticas-avanzadas.js` |
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

La exportación CSV se delega completamente al backend (`GET /solicitudes/export`) en lugar de generarla con `Blob` + `URL.createObjectURL` en el cliente. Razones:
- El backend puede exportar **todos** los registros que coinciden con los filtros, sin limitarse a los 50 de la página actual.
- No se necesita tener los datos cargados en memoria del navegador.
- El formato, la codificación (UTF-8 con BOM) y el separador los controla el backend de forma centralizada.

---

## 10. Pendientes de implementación

### Issue 7D — Completado

| Tarea | Estado |
|---|---|
| Badge "Agrupación" en el buscador | ✔ Completado |
| Desglose de municipios en ficha de entidad | ✔ Completado |
| Botón "Descargar CSV" → endpoint `/solicitudes/export` | ✔ Completado |
| Spinners de carga en solicitudes, entidad, estadísticas y home | ✔ Completado |
| Caja de error visual para 401/403/404/422/500 | ✔ Completado |
| Favicon en todas las páginas HTML | ✔ Completado |
| Metadatos OG en index, entidad y estadísticas | ✔ Completado |
| Botón "Conócenos" → "Ver solicitudes" | ✔ Completado |
| KPI entidades únicas conectado con `entidades_unicas` de la API | ✔ Completado |
| Navbar renombrado a "Subvenciones DGDA" | ✔ Completado |
| Navbar actualizado a 6 enlaces (añadidos Estadísticas avanzadas y Recursos) | ✔ Completado |
| Columna "Año" en lugar de "Expediente" en la tabla del buscador | ✔ Completado |
| Orden inicial A→Z y eliminación de "Por defecto" en el select | ✔ Completado |
| Nueva página `recursos.html` + `js/recursos.js` (estructura + placeholder) | ✔ Completado |
| Nueva página `estadisticas-avanzadas.html` + `js/estadisticas-avanzadas.js` (estructura + gráficos preparados) | ✔ Completado |

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
| Ranking de entidades | `GET /estadisticas/ranking` | Por implementar |
| Estadísticas avanzadas (KPIs, tasa, líneas EPA) | `GET /estadisticas/avanzadas/` | `estadisticas-avanzadas.js` |
| Distribución geográfica por CCAA | `GET /estadisticas/por-ccaa/` | `estadisticas-avanzadas.js` |
| Directorio de recursos | `GET /recursos/` | `recursos.js` |

### Pendientes futuros del frontend

- Mejorar los mensajes de error visibles al usuario (traducir a lenguaje natural).
- Ficha de entidad como modal/popup para conservar el contexto de búsqueda al cerrar.
- Política de privacidad y aviso legal.
- Contenido de la zona privada: tabla resumen por año/estado/tipo.
- Activar gráficos y KPIs de `estadisticas-avanzadas.html` cuando el backend implemente los endpoints.
- Poblar `recursos.html` con datos reales cuando el backend implemente `GET /recursos/`.

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

*Última actualización: 2 de mayo de 2026 — Paso 19 del Issue 7D. Refleja estado final tras Issues 7B, 7C y 7D (incluyendo páginas `recursos.html` y `estadisticas-avanzadas.html`).*
