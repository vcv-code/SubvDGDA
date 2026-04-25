/**
 * home.js — Lógica de la página de inicio (index.html)
 * ──────────────────────────────────────────────────────
 * Este archivo gestiona toda la interacción dinámica de index.html.
 * Se conecta con la API REST del backend mediante fetch() y rellena
 * los bloques de métricas con datos reales.
 *
 * PETICIONES A LA API:
 *   · GET /estadisticas/   → Métricas generales + datos por año
 *
 * BLOQUES QUE SE ACTUALIZAN:
 *   1. Tarjetas de métricas (Sección 2) — Registros, Importe, Entidades
 *
 * CONCEPTOS CLAVE USADOS:
 *   · fetch()           → Petición HTTP asíncrona al servidor
 *   · async / await     → Forma moderna de manejar código asíncrono
 *   · try / catch       → Manejo de errores de red o del servidor
 *   · .json()           → Convierte la respuesta HTTP en objeto JavaScript
 *   · Intl.NumberFormat → Formatea números según el idioma (1234 → 1.234)
 */


// ─────────────────────────────────────────────────────────────
// CONFIGURACIÓN
// ─────────────────────────────────────────────────────────────

/**
 * URL base de la API.
 * Si el puerto o la dirección del backend cambia, solo hay que
 * modificarlo aquí. Principio DRY (Don't Repeat Yourself).
 */
const API_URL = '';


// ─────────────────────────────────────────────────────────────
// UTILIDADES DE FORMATO
// ─────────────────────────────────────────────────────────────

/**
 * formatearNumero(numero)
 * Convierte un número a formato español con puntos de millar.
 * Ejemplo: 6398 → "6.398"
 *
 * Usamos Intl.NumberFormat en lugar de regex porque es la forma
 * estándar de JS para internacionalización (i18n).
 */
function formatearNumero(numero) {
    return new Intl.NumberFormat('es-ES', {
        maximumFractionDigits: 0
    }).format(numero);
}

/**
 * formatearImporte(numero)
 * Convierte un importe grande a formato legible con sufijo M€.
 * Ejemplo: 14800000 → "14,8 M€"
 *
 * ¿Por qué dividir entre 1.000.000?
 * Los importes en la BBDD están en euros. Para mostrarlos en la
 * sección de transparencia usamos millones para que sean más
 * comprensibles a primera vista.
 */
function formatearImporte(numero) {
    const millones = numero / 1_000_000;
    return new Intl.NumberFormat('es-ES', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }).format(millones) + ' M€';
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN PRINCIPAL: cargarDatos
// Hace una única petición a /estadisticas/ y con esa respuesta
// actualiza TODOS los bloques de la página.
// ─────────────────────────────────────────────────────────────

/**
 * cargarDatos()
 * Función asíncrona principal que se llama cuando el DOM está listo.
 *
 * ¿Por qué una sola petición para todo?
 * El endpoint /estadisticas/ ya devuelve todos los datos que
 * necesitamos: totales globales (total_registros, importe_global,
 * total_concedidas) y el desglose por año y tipo (por_anio).
 * Hacer una sola petición es más eficiente que hacer tres.
 */
async function cargarDatos() {
    try {
        // ── Paso 1: Petición al servidor ──────────────────────────────
        const respuesta = await fetch(`${API_URL}/estadisticas/`);

        // Si el servidor responde con un error (4xx o 5xx), lo lanzamos
        // manualmente para que lo capture el catch.
        if (!respuesta.ok) {
            throw new Error(`El servidor devolvió el código: ${respuesta.status}`);
        }

        // ── Paso 2: Parsear el JSON ────────────────────────────────────
        /**
         * El endpoint devuelve un objeto con esta forma:
         * {
         *   total_registros:  number,
         *   total_concedidas: number,
         *   importe_global:   number,
         *   por_anio: [
         *     { anio, tipo, total, concedidas, no_beneficiarias,
         *       excluidas, desistidas, importe_total },
         *     ...
         *   ]
         * }
         */
        const datos = await respuesta.json();

        // ── Paso 3: Actualizar las métricas de la página ──────────────
        mostrarMetricas(datos);

    } catch (error) {
        // Si hay cualquier fallo (sin conexión, backend caído, JSON inválido...)
        // mostramos mensajes de error en cada bloque afectado.
        console.error('Error al cargar datos de la API:', error);
        mostrarErrores();
    }
}


// ─────────────────────────────────────────────────────────────
// BLOQUE 1: MÉTRICAS (Sección 2 de index.html)
// ─────────────────────────────────────────────────────────────

/**
 * mostrarMetricas(datos)
 * Rellena las tres tarjetas verdes con los totales globales.
 *
 * Tarjeta 1 → Registros totales      (datos.total_registros)
 * Tarjeta 2 → Importe concedido      (datos.importe_global)
 * Tarjeta 3 → Entidades únicas       (datos.entidades_unicas — pendiente backend)
 *
 * @param {Object} datos - Objeto completo de /estadisticas/
 */
function mostrarMetricas(datos) {
    // Ocultamos el spinner de carga
    document.getElementById('metricas-carga').style.display = 'none';

    // Tarjeta 1: Registros totales
    document.getElementById('total-solicitudes').textContent =
        formatearNumero(datos.total_registros);

    // Tarjeta 2: Importe total concedido
    document.getElementById('importe-total').textContent =
        formatearImporte(datos.importe_global);

    // Tarjeta 3: Entidades únicas
    // PENDIENTE DE BACKEND: cuando el schema EstadisticasOut incluya
    // 'entidades_unicas', se mostrará aquí automáticamente.
    document.getElementById('total-entidades').textContent =
        datos.entidades_unicas !== undefined
            ? formatearNumero(datos.entidades_unicas)
            : '—';

    // Mostramos las tarjetas (estaban en display:none)
    document.getElementById('card-total').style.display     = '';
    document.getElementById('card-importe').style.display   = '';
    document.getElementById('card-entidades').style.display = '';
}


// ─────────────────────────────────────────────────────────────
// MANEJO DE ERRORES
// ─────────────────────────────────────────────────────────────

/**
 * mostrarErrores()
 * Reemplaza los spinners de carga por mensajes de error en cada
 * bloque de la página. Se llama desde el catch de cargarDatos().
 */
function mostrarErrores() {
    const mensajeError = `
        <div class="estado-error">
            No se pudieron cargar los datos.<br>
            Comprueba que el backend está activo (Docker o uvicorn)
        </div>
    `;

    // Sección de métricas
    const cargaMetricas = document.getElementById('metricas-carga');
    if (cargaMetricas) cargaMetricas.innerHTML = mensajeError;
}


// ─────────────────────────────────────────────────────────────
// PUNTO DE ENTRADA
// ─────────────────────────────────────────────────────────────

/**
 * DOMContentLoaded
 * Este evento se dispara cuando el navegador ha terminado de
 * construir el árbol DOM (todos los elementos HTML están en
 * memoria), pero antes de que se carguen imágenes u otros
 * recursos externos.
 *
 * ¿Por qué esperar a este evento?
 * Si llamáramos a cargarDatos() directamente al cargar el script,
 * podría ejecutarse antes de que los elementos del HTML estuvieran
 * listos, y document.getElementById() devolvería null.
 */
document.addEventListener('DOMContentLoaded', () => {
    cargarDatos();
});
