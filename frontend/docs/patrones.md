# Patrones JavaScript del frontend

Decisiones y patrones de implementación utilizados en el frontend vanilla del proyecto.

→ Ver también: [Especificaciones del frontend](especificaciones-frontend.md) · [Diseño](diseño.md)

---

## Arquitectura general

Un archivo JS por página, sin bundler ni framework. Cada archivo es independiente y solo se carga en la página que lo necesita. No hay estado global compartido entre páginas — todo el estado vive en la URL (filtros) o en `localStorage` (tokens).

---

## URLSearchParams — filtros en la URL

`URLSearchParams` es el objeto nativo del navegador para leer y escribir los parámetros de la URL (la parte después del `?`).

**Leer parámetros al cargar la página:**

```javascript
const params = new URLSearchParams(window.location.search);
const tipo   = params.get('tipo')  ?? 'epa';   // null → 'epa'
const anio   = params.get('anio')  ?? '';
const pagina = parseInt(params.get('pagina') ?? '1', 10);
```

**Escribir parámetros al aplicar filtros:**

```javascript
const params = new URLSearchParams();
if (tipo)   params.set('tipo', tipo);
if (anio)   params.set('anio', anio);
if (pagina > 1) params.set('pagina', pagina);

const qs = params.toString(); // "tipo=epa&anio=2025&pagina=2"
```

Esto permite que la URL refleje siempre el estado de los filtros. Si el usuario copia la URL y la abre en otra pestaña, ve exactamente los mismos resultados.

---

## history.replaceState — URL sin recarga

`history.replaceState` actualiza la URL en la barra del navegador **sin recargar la página** y **sin añadir una entrada al historial**.

```javascript
const qs = params.toString();
history.replaceState({}, '', qs ? `?${qs}` : window.location.pathname);
```

**Por qué `replaceState` y no `pushState`:**

| | `pushState` | `replaceState` |
|---|---|---|
| Efecto | Añade entrada al historial | Reemplaza la entrada actual |
| Botón "Atrás" | Va a la URL anterior de la app | Va a la página anterior del navegador |
| Problema | Al aplicar filtros y pulsar "Atrás", el usuario tiene que pulsar varias veces para salir | Pulsar "Atrás" lleva directamente a la página anterior |

En el buscador, cada cambio de filtro actualiza la URL con `replaceState`. Si se usara `pushState`, aplicar 3 filtros crearía 3 entradas en el historial, y el usuario tendría que pulsar "Atrás" 4 veces para salir del buscador.

**Por qué no `window.location = "?params"`:**
`window.location` provoca recarga completa de la página, que perdería el estado del DOM, resetearía el formulario y haría una nueva petición de red. `history.replaceState` solo cambia la URL sin ningún efecto secundario.

---

## fetch con async/await

Todas las llamadas a la API usan `fetch` con `async/await`. El patrón estándar del proyecto:

```javascript
async function cargarDatos() {
    try {
        const r = await fetch(`${API_URL}/solicitudes/?tipo=epa`);
        if (!r.ok) throw new Error(`Error ${r.status}`);  // siempre comprobar r.ok
        const datos = await r.json();
        // usar datos...
    } catch (err) {
        console.error('Error cargando datos:', err);
        // mostrar mensaje de error al usuario
    }
}
```

**Por qué comprobar `r.ok` antes de `.json()`:** `fetch` solo lanza excepción en errores de red (sin conexión). Un 404 o 500 del servidor NO lanza excepción — devuelve una respuesta con `ok: false`. Si se llama a `.json()` sin comprobar `r.ok`, se parsea el JSON de error del backend como si fueran datos válidos, lo que produce bugs silenciosos.

---

## Optional chaining `?.` y nullish coalescing `??`

**Optional chaining (`?.`):** accede a propiedades que podrían no existir sin lanzar `TypeError`.

```javascript
// Sin optional chaining — lanza TypeError si representante es null
const nombre = datos.representante.nombre;

// Con optional chaining — devuelve undefined si representante es null/undefined
const nombre = datos.representante?.nombre;

// Útil en cadenas largas
const ciudad = datos.entidad?.direccion?.municipio?.nombre;
```

**Nullish coalescing (`??`):** valor por defecto solo cuando el resultado es `null` o `undefined` (a diferencia de `||`, que también activa con `0`, `''` o `false`).

```javascript
const importe = datos.importe ?? 0;      // 0 si null/undefined
const nombre  = datos.nombre  ?? 'N/D';  // 'N/D' si null/undefined

// Diferencia con ||:
const pagina = params.get('pagina') || 1;   // malo: '0' → 1 (0 es falsy)
const pagina = params.get('pagina') ?? 1;   // bueno: solo null/undefined → 1
```

---

## Autenticación en el cliente

Las páginas protegidas (`privado.html`, `exclusivo.html`, `admin.html`) verifican el token al cargar con este patrón:

```javascript
async function verificarAcceso() {
    let token = localStorage.getItem('access_token');

    // Intentar renovar si no hay token o está caducado
    if (!token || tokenCaducado(token)) {
        const nuevoToken = await renovarToken();
        if (!nuevoToken) {
            window.location.href = 'login.html';
            return null;
        }
        token = nuevoToken;
    }

    // Verificar rol con el backend
    const perfil = await fetch(`${API_URL}/privado/perfil`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!perfil.ok) {
        window.location.href = 'login.html';
        return null;
    }
    return { token, perfil: await perfil.json() };
}
```

**Por qué verificar con el backend y no solo leer el JWT:** el JWT puede ser válido (firma correcta, no caducado) pero el usuario puede haber sido desactivado por un admin en ese tiempo. La verificación con `/privado/perfil` siempre refleja el estado actual de la BD. Si el usuario está desactivado, el backend devuelve 403.

**Navbar dinámico:** `navbar.js` detecta el token en `localStorage` y sustituye el botón "Acceder" por "Mi perfil" + "Cerrar sesión" sin hacer ninguna petición al servidor. Es solo lectura del `localStorage` — rápido y sin latencia.

---

## Inserción segura de HTML con DOM API

Para insertar contenido con posibles caracteres especiales, se usa la DOM API en lugar de `innerHTML`:

```javascript
// Peligroso: vulnerable a XSS si titulo viene del servidor
elemento.innerHTML = `<h2>${titulo}</h2>`;

// Seguro: textContent escapa automáticamente < > & "
elemento.textContent = titulo;

// Para estructuras mixtas (texto + etiquetas controladas):
const h2 = document.createElement('h2');
h2.textContent = titulo;        // texto escapado
const span = document.createElement('span');
span.className = 'tag';
span.textContent = ' — Extra';  // texto escapado
h2.appendChild(span);
contenedor.appendChild(h2);
```

`innerHTML` solo se usa cuando el HTML viene de cadenas plantilla controladas (no de datos de usuario o del servidor), como `elemento.innerHTML = datos.map(d => `<li>${d.nombre}</li>`).join('')` — donde `d.nombre` viene de una fuente conocida y controlada.

---

## Delegación de eventos

En lugar de añadir un `addEventListener` a cada botón generado dinámicamente, se usa un único listener en el contenedor padre:

```javascript
// Malo: añade N listeners (uno por botón), y si se regenera el HTML los pierdes
document.querySelectorAll('.btn-accion').forEach(btn => {
    btn.addEventListener('click', manejarAccion);
});

// Bueno: un solo listener en el contenedor, funciona aunque el HTML se regenere
tabla.addEventListener('click', function(e) {
    const btn = e.target.closest('[data-accion]');
    if (!btn) return;
    const accion = btn.dataset.accion;   // 'desactivar', 'activar', 'hacer-admin'
    const id     = btn.dataset.id;
    manejarAccion(accion, id);
});
```

Los botones del panel de administración usan atributos `data-*` para transportar la información de cada acción sin variables globales:

```html
<button data-accion="desactivar" data-id="42" data-valor="prueba@test.com">
    Desactivar
</button>
```

---

## Persistencia de filtros entre página y ficha

Al hacer clic en una fila del buscador se abre un **modal inline** sin abandonar `buscador.html` — la URL del buscador no cambia, los filtros siguen visibles y el usuario puede cerrar el modal y seguir navegando sin perder nada.

Desde el pie del modal, el enlace **"Ver página completa →"** abre `entidad.html?cif=...` en una **pestaña nueva**. El CIF va en la URL, lo que permite guardar o compartir el enlace a una entidad concreta.

Los filtros del buscador se guardan en la URL del buscador (no en `localStorage`):

```text
/buscador.html?tipo=epa&anio=2025&estado=concedida
```

Ventajas:
- La URL con filtros es compartible y marcable como favorito
- Si el usuario navega fuera y vuelve, el botón "Atrás" restaura exactamente los mismos filtros
- Sin código extra de serialización/deserialización

---

## Formateo de importes

Los importes monetarios se formatean con `Intl.NumberFormat`:

```javascript
function formatearImporte(euros) {
    return new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(euros);
    // → "1.968.611 €"
}
```

`Intl.NumberFormat` usa los separadores de miles correctos para el locale español (punto) y el símbolo de moneda en su posición habitual.

---

## Optimización de carga

### `defer` en todos los scripts

Todos los `<script src="...">` del proyecto usan el atributo `defer`:

```html
<!-- Scripts al final del body con defer -->
<script src="js/navbar.js" defer></script>
<script src="https://cdn.jsdelivr.net/.../chart.js" defer></script>
<script src="js/home.js" defer></script>
```

Sin `defer`, el navegador detiene el parsing del HTML en cuanto encuentra un `<script>`, lo descarga y ejecuta. Con `defer`:

1. El script se descarga **en paralelo** mientras el HTML sigue parseándose.
2. Se ejecuta **en orden de aparición** después de que el HTML esté completamente parseado.
3. Es compatible con `DOMContentLoaded` — los scripts diferidos ejecutan justo antes de que ese evento dispare, así que los listeners `document.addEventListener('DOMContentLoaded', ...)` funcionan correctamente.

El orden se preserva: si `chart.js` aparece antes que `home.js`, siempre ejecuta primero aunque ambos estén diferidos. Esto garantiza que las dependencias (Chart.js debe estar disponible cuando `home.js` lo usa) se respetan.

**Por qué funciona en bottom-of-body aunque el HTML ya esté parseado:** con `defer`, el navegador inicia la descarga del script al encontrar la etiqueta, incluso si está al final del body. Sin `defer`, la descarga también empieza al encontrar la etiqueta, pero bloquea el parser. La diferencia es que `defer` empieza la descarga antes si el script está en el `<head>`, y en cualquier caso nunca bloquea el parser.

### `fetchpriority` en imagen hero

```html
<img src="assets/img/home/handcat.webp"
     fetchpriority="high"
     class="portada-split__imagen-real">
```

El navegador asigna prioridades de descarga a los recursos: alta para CSS, media para imágenes visibles, baja para las que están fuera de pantalla. Por defecto, no sabe que la imagen hero es el elemento más importante de la página.

`fetchpriority="high"` sube la prioridad de esa imagen al máximo, lo que mejora el **LCP** (Largest Contentful Paint): el tiempo que tarda en aparecer el contenido principal visible. Es especialmente efectivo para imágenes grandes above-the-fold como un hero.

No usarlo en imágenes de footer, sidebar o fuera de pantalla — de hecho las imágenes que no son visibles en el primer scroll llevan `loading="lazy"` (prioridad opuesta).

### Estados de carga visibles

Las páginas que hacen peticiones asíncronas muestran feedback mientras esperan:

| Página | Indicador |
|--------|-----------|
| `index.html`, estadísticas, buscador, `entidad.html` | Spinner giratorio (`.spinner`, azul) |
| `exclusivo.html` (tabla de convocatorias) | Skeleton loader verde — dos bloques con cabecera oscura y filas animadas que simulan la forma de la tabla real |

El skeleton de `exclusivo.html` usa una animación CSS de shimmer (gradiente que se desplaza horizontalmente). El color verde oscuro de la cabecera coincide con `--nav-oscuro`, el mismo que usan los `<th>` de la tabla real, dando continuidad visual entre el estado de carga y el contenido final.

El skeleton desaparece automáticamente cuando el JS inyecta la tabla con `contenedor.innerHTML = ...` — no requiere lógica adicional de show/hide.
