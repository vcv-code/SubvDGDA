# Especificaciones Técnicas del Frontend
## Proyecto BDNS/DGDA — Subvenciones de Bienestar Animal

**Proyecto:** Análisis de Subvenciones de Bienestar Animal y Colonias Felinas  
**Curso:** 2º DAW — Proyecto Final de Ciclo  
**Issues cubiertas:** 7B (Estructura HTML/CSS/JS) · 7C (Lógica fetch/filtros/gráficos) · 7D (Mejoras de frontend + reorganización de estadísticas en EPAs y EELL + página Recursos)  
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
│   ├── home.js                  → Lógica de index.html (métricas + gráficos generales con GET /estadisticas/)
│   ├── solicitudes.js           → Lógica del buscador
│   ├── estadisticas-epas.js     → Lógica de estadísticas EPAs (importe medio, distribución, nuevos vs recurrentes, top beneficiarios)
│   ├── estadisticas-eell.js     → Lógica de estadísticas EELL (% ayuntamientos, top provincias, concentración, ranking CCAA)
│   ├── recursos.js              → Lógica del directorio de recursos (pendiente de endpoint)
│   ├── auth.js                  → Lógica de login y registro (JWT)
│   ├── privado.js               → Control de acceso y contenido de zona privada
│   └── entidad.js               → Lógica de la ficha de entidad
│
├── assets/
│   ├── logo.png                → Logotipo del proyecto (también usado como favicon)
│   ├── perro-gato.png          → Foto para la portada (portada-split)
│   ├── animales-login.png      → Foto decorativa en login.html
│   ├── animales-registro.png   → Foto decorativa en registro.html
│   └── wireframes_...pdf       → Wireframes de referencia (issue 7A)
│
├── index.html               → Página de inicio (Home) — métricas + gráficos generales
├── solicitudes.html         → Buscador de solicitudes con filtros
├── estadisticas-epas.html   → Estadísticas de Entidades Protectoras de Animales (Issue 7D)
├── estadisticas-eell.html   → Estadísticas de Entidades Locales / Ayuntamientos (Issue 7D)
├── recursos.html            → Directorio de organizaciones y sitios de interés (Issue 7D)
├── login.html               → Formulario de inicio de sesión
├── registro.html            → Formulario de creación de cuenta
├── privado.html             → Zona exclusiva para usuarios registrados
├── entidad.html             → Ficha de entidad con historial y desglose de agrupaciones
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

**Estructura actual del navbar (Issue 7D) — Opción A, 6 enlaces directos:**

| Posición | Enlace | Destino | Clase especial |
|---|---|---|---|
| 1 | Inicio | `index.html` | `activo` en home |
| 2 | Buscador | `solicitudes.html` | `activo` en buscador |
| 3 | EPAs | `estadisticas-epas.html` | `activo` en EPAs |
| 4 | EELL | `estadisticas-eell.html` | `activo` en EELL |
| 5 | Recursos | `recursos.html` | `activo` en recursos |
| 6 | Acceder | `login.html` | `.btn-login` (botón verde) |

Todas las páginas del proyecto han sido actualizadas para incluir este navbar con los 6 enlaces. El patrón de accesibilidad (`role="navigation"`, `aria-label`, `aria-current="page"`) y los estilos se mantienen uniformes en todas las páginas.

**¿Por qué fijo?** En páginas largas como la Home o el Buscador, el usuario necesita poder navegar a otras secciones sin tener que volver al inicio de la página.

**¿Por qué Opción A (dos enlaces directos) y no dropdown?** Se descartó el menú desplegable porque el stack vanilla JS no tiene CSS/JS de dropdown incluido, la accesibilidad (teclado, `focus-within`, mobile touch) requeriría código extra, y dos enlaces directos funcionan igual de bien con la cantidad actual de páginas.

**Cambios en Issue 7D:** el nombre del proyecto en el navbar se actualizó de "Bienestar Animal" a **"Subvenciones DGDA"** y el color del texto pasó a negro (`var(--color-negro)`) para armonizar con el logotipo. Se eliminó el enlace a `estadisticas.html` (el dashboard de gráficos se integró en `index.html`) y se añadieron los enlaces directos a "EPAs" y "EELL" más "Recursos".

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

**HTML** (presente en `solicitudes.html`, `entidad.html`, `index.html`, `recursos.html`, `estadisticas-epas.html` y `estadisticas-eell.html`):

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

**HTML** (presente en `solicitudes.html`, `entidad.html`, `index.html`, `recursos.html`, `estadisticas-epas.html` y `estadisticas-eell.html`):

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

**Propósito:** Presentar el proyecto, mostrar las cifras clave y dar acceso rápido a las herramientas principales. Desde Issue 7D también alberga los gráficos de evolución temporal que antes estaban en `estadisticas.html`.

**Cambios en Issues 7C/7D:**
- Favicon configurado con `<link rel="icon" href="assets/logo.png">`.
- Metadatos Open Graph (`og:title`, `og:description`, `og:image`) añadidos en el `<head>`.
- KPI "Entidades únicas" conectado con el dato real de la API (`datos.entidades_unicas`).
- Botón "Conócenos" → sustituido por "Ver solicitudes" enlazando a `solicitudes.html`.
- Spinner de carga sobre las métricas.
- Caja de error visual si el backend no responde.
- **Nueva sección de gráficos** con fondo verde (`fondo-stats`), usando el endpoint existente `GET /estadisticas/`.

**Secciones:**

| Sección | Contenido | Datos |
|---|---|---|
| Portada partida | Título "Sobre el proyecto" + descripción + foto de animales | Estático |
| Datos y métricas | 3 tarjetas: total solicitudes, importe concedido, entidades únicas | API `/estadisticas/` |
| Gráficos (nueva) | Evolución importe por año (línea), distribución estados (donut), EPA vs EELL por año (barras agrupadas), KPI tasa de éxito | API `/estadisticas/` |

Las secciones "Convocatorias recientes" y "Transparencia" se eliminaron para simplificar la página y centrar el foco en los datos clave.

**Gráficos implementados en `js/home.js`:**

| Función | Tipo Chart.js | Canvas ID | Datos |
|---|---|---|---|
| `crearGraficoLinea(porAnio)` | `line` | `home-grafico-linea` | Suma EPA+EELL de `por_anio` |
| `crearGraficoDonut(datos)` | `doughnut` + `cutout: '62%'` | `home-grafico-donut` | Totales concedidas / resto |
| `crearGraficoBarras(porAnio)` | `bar` agrupado | `home-grafico-barras` | `por_anio` separado por tipo |
| `mostrarTasaExito(datos)` | KPI HTML | `home-tasa-exito` | `total_concedidas / total_registros` |

**Archivo JS:** `js/home.js` — una sola petición a `/estadisticas/` alimenta todos los bloques (métricas + gráficos).

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

**Exportación CSV:** el botón "↓ Descargar CSV" construye la URL `/solicitudes/export` con todos los filtros activos (`buscar`, `tipo`, `anio`, `estado`, `ccaa`, `provincia`, `linea`) —sin `pagina` ni `limite`— y redirige con `window.location.href`. El backend genera y sirve el fichero CSV completo. No hay lógica de generación CSV en el cliente. El CSV incluye la columna `tramo` (rama 10a).

**Paginación:** 50 resultados por página. Parámetros `limite` y `pagina` en la URL de la API.

**Enlace a ficha:** al hacer clic en cualquier fila se navega a `entidad.html?cif=...`.

**Persistencia de filtros en URL** (rama 10a): al ejecutar una búsqueda, los filtros activos se escriben como parámetros en la URL de la página (`solicitudes.html?tipo=eell&anio=2025&estado=concedida`). Al volver desde la ficha de entidad, el botón "Volver al buscador" usa `history.back()`, lo que restaura la URL con parámetros y relanza la búsqueda automáticamente. Al limpiar filtros, la URL vuelve a `solicitudes.html` sin parámetros. El evento `popstate` (botón Atrás del navegador) tiene el mismo comportamiento.

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

**Propósito:** Mostrar el historial completo de participación de una entidad en todas las convocatorias.

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

### 5.5 Recursos — `recursos.html`

**Propósito:** Directorio estático de organizaciones, iniciativas y campañas relevantes en materia de protección animal, gestión ética de colonias felinas, fauna urbana y movimientos actuales. Esta página no depende del backend: todo el contenido procede del documento funcional entregado por el equipo y se integra directamente en HTML.

**Estado:** Contenido completamente implementado (Issue 7D). Logos integrados en todos los bloques (Issue 7E). No existe `recursos.js` activo: no hay fetch ni lógica dinámica.

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
- Rangos de distribución: `< 5.000 €`, `5.000–15.000 €`, `15.000–30.000 €`, `30.000–60.000 €`, `> 60.000 €`.
- Colores de gráficos: tonos verdes (`verdeOscuro #2E7D32`, `verdeMedio #66BB6A`, `verdeClaro #A5D6A7`) para EPAs; el top beneficiarios usa azul.

---

### 5.7 Estadísticas EELL — `estadisticas-eell.html` + `js/estadisticas-eell.js` (Issue 7D)

**Propósito:** Análisis específico de las convocatorias de Entidades de la Administración Local (ayuntamientos): % de ayuntamientos con ayuda, importe medio EELL, ratio de exclusión, top provincias por importe, concentración top 10% vs resto, ranking de CCAA y distribución geográfica (mapa pendiente).

**Estado:** Completamente implementada y conectada al backend. Endpoint `GET /estadisticas/eell` disponible.

**Fondo visual:** usa la clase `.fondo-stats`. Enlace "→ Ver estadísticas EPAs" en la cabecera.

**Estructura HTML:**

| Bloque | ID | Descripción |
|---|---|---|
| Spinner | `#spinner` | Patrón estándar del proyecto |
| Caja de error | `#error-box` | Patrón estándar del proyecto |
| KPIs | `.grid-4` | 4 tarjetas de métricas EELL |
| Top provincias | `#grafico-top-provincias` | Canvas oculto + placeholder |
| Concentración top 10% | `#grafico-concentracion` | Canvas donut oculto + placeholder |
| Ranking CCAA | `#ranking-ccaa` | `<ul>` rellenable por JS + `#ranking-ccaa-pendiente` |
| Mapa CCAA | `#mapa-ccaa-container` | Placeholder con 🗺️ — pendiente de decisión técnica |

**KPIs (pendientes de datos):**

| ID | Label | Dato esperado |
|---|---|---|
| `#kpi-pct-ayuntamientos` | % Ayuntamientos con ayuda | `datos.pct_ayuntamientos_con_ayuda` |
| `#kpi-importe-medio-eell` | Importe medio EELL | `datos.importe_medio` |
| `#kpi-ratio-exclusion` | Ratio de exclusión | `datos.ratio_exclusion` (0–1, se muestra × 100 %) |
| `#kpi-ccaa-top` | CCAA con más concesiones | `datos.ccaa_top` |

**Gráficos preparados en `estadisticas-eell.js`:**

| Función | Tipo Chart.js | Canvas | Datos |
|---|---|---|---|
| `poblarGraficoTopProvincias(topProvincias)` | `bar` horizontal (`indexAxis: 'y'`), top 15 | `grafico-top-provincias` | `[{provincia, importe_total}]` |
| `poblarGraficoConcentracion(concentracion)` | `doughnut`, `cutout: '62%'`, leyenda abajo | `grafico-concentracion` | `{top_10_pct, resto_pct}` |
| `poblarRankingCcaa(porCcaa)` | Lista HTML (hasta 19: 17 CCAA + Ceuta + Melilla) | `#ranking-ccaa` | `[{ccaa, importe_total, num_concesiones}]` |

**Mapa CCAA — pendiente:**

El diseño en PDF define un mapa de calor de España por comunidad autónoma, con interacción hover y click. Queda en espera de decisión sobre la librería de mapas (SVG inline, Leaflet, D3-geo…). Mientras tanto se muestra el ranking CCAA como alternativa funcional.

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
| Nueva página `recursos.html` + `js/recursos.js` con contenido estático real y pendiente dinámico | ✔ Completado |
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
