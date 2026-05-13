/**
 * home.js — Lógica de la página de inicio (index.html)
 * ──────────────────────────────────────────────────────
 * Gestiona las métricas y los gráficos generales de index.html.
 * Una única petición a GET /estadisticas/ alimenta todos los bloques.
 *
 * PETICIONES A LA API:
 *   · GET /estadisticas/   → Métricas generales + datos por año
 *
 * BLOQUES QUE SE ACTUALIZAN:
 *   1. Tarjetas de métricas (Sección 2) — Registros, Importe, Entidades
 *   2. Gráfico de línea    → Evolución del importe total por año
 *   3. Gráfico de donut    → Distribución por estado
 *   4. Gráfico de barras   → EPA vs EELL por año
 *   5. KPI tasa de éxito   → % concedido global
 *
 * CONCEPTOS CLAVE USADOS:
 *   · fetch()           → Petición HTTP asíncrona al servidor
 *   · async / await     → Forma moderna de manejar código asíncrono
 *   · try / catch       → Manejo de errores de red o del servidor
 *   · Chart.js v4       → Librería de gráficos (cargada en el HTML)
 *   · Intl.NumberFormat → Formatea números según el idioma (1234 → 1.234)
 */


// ─────────────────────────────────────────────────────────────
// CONFIGURACIÓN
// ─────────────────────────────────────────────────────────────

const API_URL = '';

/** Años del sistema, usados como etiquetas en los gráficos */
const ANIOS = [2021, 2022, 2023, 2024, 2025];

/**
 * Paleta de colores para los gráficos.
 * Valores literales porque Chart.js no acepta variables CSS.
 */
const COLORES = {
    verdeOscuro:    '#2E7D32',
    verdeMedio:     '#66BB6A',
    verdeClaro:     '#A5D6A7',
    verdeFondo:     'rgba(71, 192, 121, 0.15)',
    azul:           '#1565C0',
    concedida:      '#2E7D32',
    noBeneficiaria: '#A5D6A7',
    excluida:       '#EF6C00',
    desistida:      '#C62828',
    grisTexto:      '#616161',
    grisMedio:      '#E0E0E0',
};

const OPCIONES_BASE = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
};


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
    document.getElementById('spinner').style.display = 'block';
    try {
        // ── Paso 1: Petición al servidor ──────────────────────────────
        const respuesta = await fetch(`${API_URL}/estadisticas/`);

        // Si el servidor responde con un error (4xx o 5xx), lo lanzamos
        // manualmente para que lo capture el catch.
        if (!respuesta.ok) {
            let cuerpo = {};
            try { cuerpo = await respuesta.json(); } catch (_) {}
            const errorBox        = document.getElementById('error-box');
            const errorMensaje    = document.getElementById('error-mensaje');
            const errorSugerencia = document.getElementById('error-sugerencia');
            if (errorBox) {
                errorMensaje.textContent    = cuerpo.mensaje    || `Error ${respuesta.status}`;
                errorSugerencia.textContent = cuerpo.sugerencia || '';
                errorBox.style.display      = 'block';
            }
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

        // ── Paso 3: Actualizar métricas y gráficos ────────────────────
        mostrarMetricas(datos);
        crearGraficoLinea(datos.por_anio);
        crearGraficoDonut(datos);
        crearGraficoBarras(datos.por_anio);
        mostrarTasaExito(datos);

    } catch (error) {
        // Si hay cualquier fallo (sin conexión, backend caído, JSON inválido...)
        // mostramos mensajes de error en cada bloque afectado.
        console.error('Error al cargar datos de la API:', error);
        mostrarErrores();
    } finally {
        document.getElementById('spinner').style.display = 'none';
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
    // El campo 'entidades_unicas' está disponible en GET /estadisticas/
    // (campo añadido en el schema EstadisticasOut del backend).
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
// UTILIDAD: descarga de gráfico como PNG
// ─────────────────────────────────────────────────────────────

/**
 * configurarDescarga(instanciaChart, btnId, nombreArchivo)
 * Muestra el botón de descarga de una tarjeta de gráfico y le
 * añade el listener que llama a chart.toBase64Image() (Chart.js 4.x)
 * para generar un PNG y descargarlo mediante un <a> temporal.
 *
 * @param {Chart}  instanciaChart  - Instancia de Chart.js ya creada.
 * @param {string} btnId           - ID del <button> en el HTML.
 * @param {string} nombreArchivo   - Nombre del archivo descargado (.png).
 */
function configurarDescarga(instanciaChart, btnId, nombreArchivo) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    btn.style.display = 'inline-flex';
    btn.addEventListener('click', () => {
        const url = instanciaChart.toBase64Image('image/png', 1);
        const a   = document.createElement('a');
        a.href     = url;
        a.download = nombreArchivo;
        a.click();
    });
}


// ─────────────────────────────────────────────────────────────
// UTILIDADES DE FORMATO (gráficos)
// ─────────────────────────────────────────────────────────────

function formatearMiles(n) {
    return new Intl.NumberFormat('es-ES', { maximumFractionDigits: 0 }).format(n);
}

function formatearMillones(n) {
    const m = n / 1_000_000;
    return new Intl.NumberFormat('es-ES', {
        minimumFractionDigits: 1, maximumFractionDigits: 1,
    }).format(m) + ' M€';
}

function formatearEjeY(n) {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + ' M';
    if (n >= 1_000)     return (n / 1_000).toFixed(0) + ' K';
    return n;
}


// ─────────────────────────────────────────────────────────────
// GRÁFICO 1: LÍNEA — Evolución del importe total por año
// Datos: GET /estadisticas/ → por_anio[].importe_total (EPA + EELL sumados)
// ─────────────────────────────────────────────────────────────

function crearGraficoLinea(porAnio) {
    const importesPorAnio = ANIOS.map(anio =>
        porAnio.filter(d => d.anio === anio)
               .reduce((suma, d) => suma + d.importe_total, 0)
    );

    new Chart(document.getElementById('home-grafico-linea'), {
        type: 'line',
        data: {
            labels: ANIOS,
            datasets: [{
                label: 'Importe total',
                data: importesPorAnio,
                borderColor:          COLORES.verdeOscuro,
                borderWidth:          2.5,
                fill:                 true,
                backgroundColor:      COLORES.verdeFondo,
                pointBackgroundColor: COLORES.verdeOscuro,
                pointRadius:          5,
                pointHoverRadius:     7,
                tension:              0.4,
            }],
        },
        options: {
            ...OPCIONES_BASE,
            scales: {
                x: {
                    grid:  { color: COLORES.grisMedio },
                    ticks: { font: { family: 'Inter', size: 11 }, color: COLORES.grisTexto },
                },
                y: {
                    beginAtZero: true,
                    grid:  { color: COLORES.grisMedio },
                    ticks: {
                        font:     { family: 'Inter', size: 11 },
                        color:    COLORES.grisTexto,
                        callback: (v) => formatearEjeY(v),
                    },
                },
            },
            plugins: {
                ...OPCIONES_BASE.plugins,
                tooltip: { callbacks: { label: (ctx) => ' ' + formatearMillones(ctx.raw) } },
            },
        },
    });
}


// ─────────────────────────────────────────────────────────────
// GRÁFICO 2: DONUT — Distribución por estado
// Datos: GET /estadisticas/ → totales de por_anio sumados
// ─────────────────────────────────────────────────────────────

function crearGraficoDonut(datos) {
    const totales = datos.por_anio.reduce(
        (acc, d) => {
            acc.concedidas      += d.concedidas;
            acc.noBeneficiarias += d.no_beneficiarias;
            acc.excluidas       += d.excluidas;
            acc.desistidas      += d.desistidas;
            return acc;
        },
        { concedidas: 0, noBeneficiarias: 0, excluidas: 0, desistidas: 0 }
    );

    new Chart(document.getElementById('home-grafico-donut'), {
        type: 'doughnut',
        data: {
            labels: ['Concedida', 'No beneficiaria', 'Excluida', 'Desistida'],
            datasets: [{
                data: [
                    totales.concedidas,
                    totales.noBeneficiarias,
                    totales.excluidas,
                    totales.desistidas,
                ],
                backgroundColor: [
                    COLORES.concedida,
                    COLORES.noBeneficiaria,
                    COLORES.excluida,
                    COLORES.desistida,
                ],
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 8,
            }],
        },
        options: {
            ...OPCIONES_BASE,
            cutout: '62%',
            plugins: {
                ...OPCIONES_BASE.plugins,
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct   = Math.round((ctx.raw / total) * 100);
                            return ` ${ctx.label}: ${formatearMiles(ctx.raw)} (${pct}%)`;
                        },
                    },
                },
            },
        },
    });
}


// ─────────────────────────────────────────────────────────────
// GRÁFICO 3: BARRAS — EPA vs EELL por año
// Datos: GET /estadisticas/ → por_anio[] filtrado por tipo
// ─────────────────────────────────────────────────────────────

function crearGraficoBarras(porAnio) {
    const importeEPA  = ANIOS.map(anio => {
        const d = porAnio.find(x => x.anio === anio && x.tipo === 'epa');
        return d ? d.importe_total : 0;
    });
    const importeEELL = ANIOS.map(anio => {
        const d = porAnio.find(x => x.anio === anio && x.tipo === 'eell');
        return d ? d.importe_total : 0;
    });

    new Chart(document.getElementById('home-grafico-barras'), {
        type: 'bar',
        data: {
            labels: ANIOS,
            datasets: [
                {
                    label: 'EPA',
                    data:  importeEPA,
                    backgroundColor: COLORES.verdeOscuro,
                    borderRadius:    4,
                    borderSkipped:   false,
                },
                {
                    label: 'EELL',
                    data:  importeEELL,
                    backgroundColor: COLORES.verdeMedio,
                    borderRadius:    4,
                    borderSkipped:   false,
                },
            ],
        },
        options: {
            ...OPCIONES_BASE,
            plugins: {
                legend: {
                    display:  true,
                    position: 'top',
                    labels: {
                        font:           { family: 'Inter', size: 11 },
                        color:          COLORES.grisTexto,
                        boxWidth:       12,
                        boxHeight:      12,
                        borderRadius:   3,
                        useBorderRadius: true,
                        padding:        16,
                    },
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` ${ctx.dataset.label}: ${formatearMillones(ctx.raw)}`,
                    },
                },
            },
            scales: {
                x: {
                    grid:  { display: false },
                    ticks: { font: { family: 'Inter', size: 11 }, color: COLORES.grisTexto },
                },
                y: {
                    beginAtZero: true,
                    grid:  { color: COLORES.grisMedio },
                    ticks: {
                        font:     { family: 'Inter', size: 11 },
                        color:    COLORES.grisTexto,
                        callback: (v) => formatearEjeY(v),
                    },
                },
            },
        },
    });
}


// ─────────────────────────────────────────────────────────────
// KPI: TASA DE ÉXITO GLOBAL
// Datos: GET /estadisticas/ → total_concedidas / total_registros
// ─────────────────────────────────────────────────────────────

function mostrarTasaExito(datos) {
    const el = document.getElementById('home-tasa-exito');
    if (!el) return;
    if (datos.total_registros > 0) {
        const pct = Math.round((datos.total_concedidas / datos.total_registros) * 100);
        el.textContent = pct + ' %';
    } else {
        el.textContent = '—';
    }
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
// ─────────────────────────────────────────────────────────────
// AVISOS: convocatorias del año en curso sin resolución
// ─────────────────────────────────────────────────────────────

/**
 * cargarAvisos()
 * Consulta GET /avisos/ y muestra un banner por cada convocatoria
 * detectada por el cron que aún no tiene resolución publicada.
 * Si no hay avisos activos, el contenedor permanece oculto.
 */
async function cargarAvisos() {
    const contenedor = document.getElementById('avisos-banner');
    if (!contenedor) return;

    try {
        const resp = await fetch(`${API_URL}/avisos/`);
        if (!resp.ok) return;

        const avisos = await resp.json();
        if (!avisos.length) return;

        const etiquetas = { eell: 'Entidades Locales', epa: 'Entidades Privadas' };

        contenedor.innerHTML = avisos.map(aviso => {
            const tipo  = etiquetas[aviso.tipo_convoc] || aviso.tipo_convoc.toUpperCase();
            const fecha = aviso.fecha_convocatoria
                ? new Date(aviso.fecha_convocatoria).toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })
                : 'fecha pendiente';
            return `
                <div class="aviso-banner">
                    <span class="aviso-banner__icono">📢</span>
                    <div class="aviso-banner__texto">
                        <strong>Convocatoria ${aviso.anio_convocatoria} — ${tipo}</strong>
                        <p>Publicada el ${fecha}. Los datos de solicitudes y concesiones estarán disponibles cuando se publique la resolución.</p>
                    </div>
                </div>`;
        }).join('');

        contenedor.style.display = 'block';

    } catch (_) {
        // El banner es informativo; si falla, no interrumpimos la página
    }
}


async function cargarConvocatorias() {
    const bloque = document.getElementById('convocatorias-bloque');
    if (!bloque) return;

    try {
        const resp = await fetch(`${API_URL}/convocatorias/`);
        if (!resp.ok) return;

        const convocatorias = await resp.json();
        if (!convocatorias.length) return;

        const porTipo = { eell: [], epa: [] };
        convocatorias.forEach(c => {
            if (porTipo[c.tipo_convoc]) porTipo[c.tipo_convoc].push(c);
        });

        const meses = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
        const fmtFecha = iso => {
            if (!iso) return '—';
            const [y, m, d] = iso.split('-');
            return `${parseInt(d)} ${meses[parseInt(m)-1]} ${y}`;
        };

        const renderFilas = (lista) =>
            lista
                .sort((a, b) => b.anio_convocatoria - a.anio_convocatoria)
                .map(c => {
                    const asterisco  = c.periodo_meses === 6 ? ' *' : '';
                    const fechaStr   = fmtFecha(c.fecha_convocatoria);
                    const pendiente  = c.fecha_resolucion === null && c.fecha_convocatoria !== null;
                    const accion     = pendiente
                        ? `<span class="convoc-pendiente">Pendiente de resolución</span>`
                        : `<a href="solicitudes.html?tipo=${c.tipo_convoc}&anio=${c.anio_convocatoria}" class="btn btn-secundario btn--sm">Ver →</a>`;
                    return `<tr>
                        <td>${c.anio_convocatoria}${asterisco}</td>
                        <td>${fechaStr}</td>
                        <td>${accion}</td>
                    </tr>`;
                }).join('');

        const tbodyEell = document.getElementById('convocatorias-eell');
        const tbodyEpa  = document.getElementById('convocatorias-epa');
        if (tbodyEell) tbodyEell.innerHTML = renderFilas(porTipo.eell);
        if (tbodyEpa)  tbodyEpa.innerHTML  = renderFilas(porTipo.epa);

        const haySeisMeses = convocatorias.some(c => c.periodo_meses === 6);
        const notaEl = document.getElementById('convocatorias-nota');
        if (notaEl) notaEl.style.display = haySeisMeses ? '' : 'none';

        bloque.style.display = '';

    } catch (_) {
        // Si falla, el bloque permanece oculto
    }
}


document.addEventListener('DOMContentLoaded', () => {
    cargarDatos();
    cargarAvisos();
    cargarConvocatorias();
});
