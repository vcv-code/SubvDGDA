/**
 * estadisticas-epas.js — Lógica de la página de estadísticas EPAs
 * ─────────────────────────────────────────────────────────────────
 * Gestiona la carga y presentación del análisis específico de
 * Entidades Protectoras de Animales (EPAs):
 *   · Importe medio y mediana
 *   · Beneficiarios únicos y nuevas entidades
 *   · Distribución de importes por rangos
 *   · Comparativa media vs mediana por año
 *   · Nuevos vs recurrentes por año
 *   · Top beneficiarios por importe
 *
 * ENDPOINT:
 *   GET /estadisticas/epas
 *   Respuesta esperada: {
 *     importe_medio:         number,
 *     mediana:               number,
 *     beneficiarios_unicos:  number,
 *     nuevas_entidades:      number,
 *     distribucion_importes: [{ rango: string, cantidad: number }, ...],
 *     por_anio: [
 *       {
 *         anio:              number,
 *         media:             number,
 *         mediana:           number,
 *         nuevos:            number,
 *         recurrentes:       number,
 *         top_beneficiarios: [{ nombre: string, importe: number }, ...]
 *       }, ...
 *     ]
 *   }
 */


// ─────────────────────────────────────────────────────────────
// CONFIGURACIÓN
// ─────────────────────────────────────────────────────────────

const API_URL = '';

const ANIOS = [2021, 2022, 2023, 2024, 2025];

const COLORES = {
    verdeOscuro:  '#2E7D32',
    verdeMedio:   '#66BB6A',
    verdeClaro:   '#A5D6A7',
    azul:         '#1565C0',
    grisTexto:    '#616161',
    grisMedio:    '#E0E0E0',
};

const OPCIONES_BASE = {
    responsive:          true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
};


// ─────────────────────────────────────────────────────────────
// REFERENCIAS AL DOM
// ─────────────────────────────────────────────────────────────

const spinner         = document.getElementById('spinner');
const errorBox        = document.getElementById('error-box');
const errorMensaje    = document.getElementById('error-mensaje');
const errorSugerencia = document.getElementById('error-sugerencia');

// KPIs
const kpiImporteMedio      = document.getElementById('kpi-importe-medio');
const kpiMediana           = document.getElementById('kpi-mediana');
const kpiBeneficiariosUnicos = document.getElementById('kpi-beneficiarios-unicos');
const kpiNuevasEntidades   = document.getElementById('kpi-nuevas-entidades');

// Canvas y placeholders
const distribucionPendiente = document.getElementById('distribucion-pendiente');
const graficoDistribucion   = document.getElementById('grafico-distribucion-importes');

const mediaMedianaPendiente = document.getElementById('media-mediana-pendiente');
const graficoMediaMediana   = document.getElementById('grafico-media-mediana');

const nuevosPendiente       = document.getElementById('nuevos-pendiente');
const graficoNuevos         = document.getElementById('grafico-nuevos-recurrentes');

const topPendiente          = document.getElementById('top-pendiente');
const graficoTop            = document.getElementById('grafico-top-beneficiarios');


// ─────────────────────────────────────────────────────────────
// FUNCIÓN PRINCIPAL: cargarEstadisticasEpas
// ─────────────────────────────────────────────────────────────
/**
 * cargarEstadisticasEpas()
 * Llama al endpoint GET /estadisticas/epas y pinta KPIs y gráficos.
 *
 * Patrón idéntico al del resto de páginas del proyecto:
 *   1. Mostrar spinner
 *   2. Fetch al endpoint (comentado — pendiente de backend)
 *   3. Si !ok → mostrar error-box con mensaje y sugerencia
 *   4. Si ok  → poblar KPIs y gráficos
 *   5. Ocultar spinner en finally (siempre)
 *
 * TODO: conectar con endpoint real cuando backend lo implemente.
 */
async function cargarEstadisticasEpas() {
    spinner.style.display = 'block';

    try {

        const respuesta = await fetch(`${API_URL}/estadisticas/epas`);

        if (!respuesta.ok) {
            let cuerpo = {};
            try { cuerpo = await respuesta.json(); } catch (_) {}
            errorMensaje.textContent    = cuerpo.mensaje    || `Error ${respuesta.status}`;
            errorSugerencia.textContent = cuerpo.sugerencia || '';
            errorBox.style.display      = 'block';
            throw new Error(`Error ${respuesta.status}`);
        }

        const datos = await respuesta.json();
        poblarKpis(datos);
        poblarGraficoDistribucion(datos.distribucion_importes || []);
        poblarGraficoMediaMediana(datos.por_anio || []);
        poblarGraficoNuevosRecurrentes(datos.por_anio || []);
        poblarGraficoTopBeneficiarios(datos.por_anio || []);

    } catch (error) {
        console.error('Error al cargar estadísticas EPAs:', error);
    } finally {
        spinner.style.display = 'none';
    }
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarKpis
// ─────────────────────────────────────────────────────────────
/**
 * poblarKpis(datos)
 * Rellena las 4 tarjetas KPI con los datos del endpoint.
 *
 * @param {Object} datos - Objeto de respuesta de /estadisticas/epas
 */
function poblarKpis(datos) {
    if (kpiImporteMedio) {
        kpiImporteMedio.textContent =
            datos.importe_medio != null ? formatearEuros(datos.importe_medio) : '—';
    }
    if (kpiMediana) {
        kpiMediana.textContent =
            datos.mediana != null ? formatearEuros(datos.mediana) : '—';
    }
    if (kpiBeneficiariosUnicos) {
        kpiBeneficiariosUnicos.textContent =
            datos.beneficiarios_unicos != null
                ? datos.beneficiarios_unicos.toLocaleString('es-ES')
                : '—';
    }
    if (kpiNuevasEntidades) {
        kpiNuevasEntidades.textContent =
            datos.nuevas_entidades != null
                ? datos.nuevas_entidades.toLocaleString('es-ES')
                : '—';
    }
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoDistribucion
// Barras verticales: nº concesiones por rango de importe.
// ─────────────────────────────────────────────────────────────
/**
 * @param {Array} distribucion - [{ rango: string, cantidad: number }, ...]
 */
function poblarGraficoDistribucion(distribucion) {
    if (!distribucion.length) return;
    if (distribucionPendiente) distribucionPendiente.style.display = 'none';
    if (graficoDistribucion)   graficoDistribucion.style.display   = 'block';

    const instancia = new Chart(graficoDistribucion, {
        type: 'bar',
        data: {
            labels: distribucion.map(d => d.rango),
            datasets: [{
                label:           'Nº de concesiones',
                data:            distribucion.map(d => d.cantidad),
                backgroundColor: COLORES.verdeOscuro,
                borderRadius:    4,
                borderSkipped:   false,
            }],
        },
        options: {
            ...OPCIONES_BASE,
            plugins: {
                ...OPCIONES_BASE.plugins,
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.parsed.y.toLocaleString('es-ES')} concesiones`,
                    },
                },
            },
            scales: {
                x: {
                    grid:  { display: false },
                    ticks: { font: { family: 'Inter', size: 10 }, color: COLORES.grisTexto },
                },
                y: {
                    beginAtZero: true,
                    grid:  { color: COLORES.grisMedio },
                    ticks: { font: { family: 'Inter', size: 11 }, color: COLORES.grisTexto },
                },
            },
        },
    });
    configurarDescarga(instancia, 'btn-dl-distribucion', 'distribucion-importes-epa.png');
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoMediaMediana
// Barras agrupadas: media vs mediana por año.
// ─────────────────────────────────────────────────────────────
/**
 * @param {Array} porAnio - [{ anio, media, mediana, ... }, ...]
 */
function poblarGraficoMediaMediana(porAnio) {
    if (!porAnio.length) return;
    if (mediaMedianaPendiente) mediaMedianaPendiente.style.display = 'none';
    if (graficoMediaMediana)   graficoMediaMediana.style.display   = 'block';

    const instancia = new Chart(graficoMediaMediana, {
        type: 'bar',
        data: {
            labels: porAnio.map(d => d.anio),
            datasets: [
                {
                    label:           'Media (€)',
                    data:            porAnio.map(d => d.media),
                    backgroundColor: COLORES.verdeOscuro,
                    borderRadius:    4,
                    borderSkipped:   false,
                },
                {
                    label:           'Mediana (€)',
                    data:            porAnio.map(d => d.mediana),
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
                        font:            { family: 'Inter', size: 11 },
                        color:           COLORES.grisTexto,
                        boxWidth:        12,
                        boxHeight:       12,
                        borderRadius:    3,
                        useBorderRadius: true,
                        padding:         16,
                    },
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.dataset.label}: ${formatearEuros(ctx.raw)}`,
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
                        callback: v => formatearEjeY(v),
                    },
                },
            },
        },
    });
    configurarDescarga(instancia, 'btn-dl-media-mediana', 'media-mediana-epa.png');
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoNuevosRecurrentes
// Barras apiladas: nuevas entidades vs recurrentes por año.
// ─────────────────────────────────────────────────────────────
/**
 * @param {Array} porAnio - [{ anio, nuevos, recurrentes, ... }, ...]
 */
function poblarGraficoNuevosRecurrentes(porAnio) {
    if (!porAnio.length) return;
    if (nuevosPendiente) nuevosPendiente.style.display = 'none';
    if (graficoNuevos)   graficoNuevos.style.display   = 'block';

    const instancia = new Chart(graficoNuevos, {
        type: 'bar',
        data: {
            labels: porAnio.map(d => d.anio),
            datasets: [
                {
                    label:           'Nuevas',
                    data:            porAnio.map(d => d.nuevos),
                    backgroundColor: COLORES.verdeClaro,
                    borderRadius:    4,
                    borderSkipped:   false,
                    stack:           'entidades',
                },
                {
                    label:           'Recurrentes',
                    data:            porAnio.map(d => d.recurrentes),
                    backgroundColor: COLORES.verdeOscuro,
                    borderRadius:    4,
                    borderSkipped:   false,
                    stack:           'entidades',
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
                        font:            { family: 'Inter', size: 11 },
                        color:           COLORES.grisTexto,
                        boxWidth:        12,
                        boxHeight:       12,
                        borderRadius:    3,
                        useBorderRadius: true,
                        padding:         16,
                    },
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString('es-ES')}`,
                    },
                },
            },
            scales: {
                x: {
                    grid:    { display: false },
                    ticks:   { font: { family: 'Inter', size: 11 }, color: COLORES.grisTexto },
                    stacked: true,
                },
                y: {
                    beginAtZero: true,
                    stacked:     true,
                    grid:        { color: COLORES.grisMedio },
                    ticks:       { font: { family: 'Inter', size: 11 }, color: COLORES.grisTexto },
                },
            },
        },
    });
    configurarDescarga(instancia, 'btn-dl-nuevos', 'nuevos-recurrentes-epa.png');
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoTopBeneficiarios
// Barras horizontales: top beneficiarios por importe acumulado.
// ─────────────────────────────────────────────────────────────
/**
 * @param {Array} porAnio - Se usa el campo top_beneficiarios del último año disponible,
 *                          o un campo top_beneficiarios a nivel raíz del objeto datos.
 *
 * NOTA: La estructura exacta de este campo depende del diseño final del endpoint.
 * Cuando el backend lo implemente, ajustar para leer desde el lugar correcto.
 */
function poblarGraficoTopBeneficiarios(porAnio) {
    // Tomar el top del último año disponible con datos
    const ultimo = [...porAnio].reverse().find(d => d.top_beneficiarios?.length > 0);
    if (!ultimo) return;

    const top = ultimo.top_beneficiarios.slice(0, 10);
    if (topPendiente) topPendiente.style.display = 'none';
    if (graficoTop)   graficoTop.style.display   = 'block';

    const instancia = new Chart(graficoTop, {
        type: 'bar',
        data: {
            labels: top.map(d => d.nombre),
            datasets: [{
                label:           'Importe (€)',
                data:            top.map(d => d.importe),
                backgroundColor: COLORES.azul,
                borderRadius:    4,
                borderSkipped:   false,
            }],
        },
        options: {
            ...OPCIONES_BASE,
            indexAxis: 'y',
            plugins: {
                ...OPCIONES_BASE.plugins,
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${formatearEuros(ctx.parsed.x)}`,
                    },
                },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid:  { color: COLORES.grisMedio },
                    ticks: {
                        font:     { family: 'Inter', size: 11 },
                        color:    COLORES.grisTexto,
                        callback: v => formatearEjeY(v),
                    },
                },
                y: {
                    grid:  { display: false },
                    ticks: { font: { family: 'Inter', size: 10 }, color: COLORES.grisTexto },
                },
            },
        },
    });
    configurarDescarga(instancia, 'btn-dl-top', 'top-beneficiarios-epa.png');
}


// ─────────────────────────────────────────────────────────────
// UTILIDADES
// ─────────────────────────────────────────────────────────────

/**
 * configurarDescarga(instanciaChart, btnId, nombreArchivo)
 * Muestra el botón de descarga y lo conecta al PNG del gráfico.
 * Idéntica a la de home.js — cada JS es independiente.
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

function formatearEuros(valor) {
    return Number(valor).toLocaleString('es-ES', {
        style:                'currency',
        currency:             'EUR',
        maximumFractionDigits: 0,
    });
}

function formatearEjeY(n) {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + ' M';
    if (n >= 1_000)     return (n / 1_000).toFixed(0) + ' K';
    return n;
}


// ─────────────────────────────────────────────────────────────
// PUNTO DE ENTRADA
// ─────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    cargarEstadisticasEpas();
});
