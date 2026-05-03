/**
 * estadisticas-avanzadas.js — Lógica de la página de estadísticas avanzadas
 * ─────────────────────────────────────────────────────────────────────────
 * Gestiona la carga y presentación de los análisis avanzados:
 * distribución geográfica (CCAA), comparativa EPA vs EELL,
 * líneas de actuación EPA 2025 y ranking por importe.
 *
 * ESTADO: pendiente de conexión con el backend.
 * Los endpoints GET /estadisticas/avanzadas/ y GET /estadisticas/por-ccaa/
 * aún no existen. Cuando estén disponibles, descomentar las llamadas
 * en cargarEstadisticasAvanzadas() y poblar los gráficos con datos reales.
 *
 * ENDPOINTS PENDIENTES:
 *   GET /estadisticas/avanzadas/
 *   Respuesta esperada: {
 *     importe_medio_epa:    number,
 *     importe_medio_eell:   number,
 *     ccaa_top:             string,
 *     num_agrupaciones:     number,
 *     tasa_concesion:       [{ anio, tasa_epa, tasa_eell }, ...]
 *     lineas_epa_2025:      { abandonados: number, colonias: number }
 *   }
 *
 *   GET /estadisticas/por-ccaa/
 *   Respuesta esperada: [
 *     { ccaa: string, importe_total: number, num_concesiones: number },
 *     ...
 *   ]
 */


// ─────────────────────────────────────────────────────────────
// CONFIGURACIÓN
// ─────────────────────────────────────────────────────────────

const API_URL = '';


// ─────────────────────────────────────────────────────────────
// REFERENCIAS AL DOM
// ─────────────────────────────────────────────────────────────

const spinner         = document.getElementById('spinner');
const errorBox        = document.getElementById('error-box');
const errorMensaje    = document.getElementById('error-mensaje');
const errorSugerencia = document.getElementById('error-sugerencia');

// KPIs
const kpiImporteMedioEpa  = document.getElementById('kpi-importe-medio-epa');
const kpiImporteMedioEell = document.getElementById('kpi-importe-medio-eell');
const kpiCcaaTop          = document.getElementById('kpi-ccaa-top');
const kpiAgrupaciones     = document.getElementById('kpi-agrupaciones');

// Contenedores de gráficos (placeholder / canvas)
const ccaaPendiente    = document.getElementById('ccaa-pendiente');
const graficoCcaa      = document.getElementById('grafico-ccaa');

const tasaPendiente    = document.getElementById('tasa-pendiente');
const graficoTasa      = document.getElementById('grafico-tasa');

const lineasPendiente  = document.getElementById('lineas-pendiente');
const graficoLineas    = document.getElementById('grafico-lineas');

const rankingCcaa      = document.getElementById('ranking-ccaa');
const rankingPendiente = document.getElementById('ranking-ccaa-pendiente');


// ─────────────────────────────────────────────────────────────
// FUNCIÓN PRINCIPAL: cargarEstadisticasAvanzadas
// ─────────────────────────────────────────────────────────────
/**
 * cargarEstadisticasAvanzadas()
 * Llama a los endpoints de estadísticas avanzadas y pinta
 * los KPIs y gráficos de la página.
 *
 * Patrón idéntico al del resto de páginas del proyecto:
 *   1. Mostrar spinner
 *   2. Fetch al endpoint
 *   3. Si !ok → mostrar error-box con mensaje y sugerencia del backend
 *   4. Si ok  → poblar KPIs y gráficos
 *   5. Ocultar spinner en finally (siempre, haya éxito o error)
 *
 * TODO: conectar con endpoint real cuando backend lo implemente.
 */
async function cargarEstadisticasAvanzadas() {
    spinner.style.display = 'block';

    try {

        // TODO: conectar con endpoint real cuando backend lo implemente.
        // Descomentar las líneas siguientes cuando GET /estadisticas/avanzadas/ esté disponible:
        //
        // const respuesta = await fetch(`${API_URL}/estadisticas/avanzadas/`);
        //
        // if (!respuesta.ok) {
        //     let cuerpo = {};
        //     try { cuerpo = await respuesta.json(); } catch (_) {}
        //     errorMensaje.textContent    = cuerpo.mensaje    || `Error ${respuesta.status}`;
        //     errorSugerencia.textContent = cuerpo.sugerencia || '';
        //     errorBox.style.display      = 'block';
        //     throw new Error(`Error ${respuesta.status}`);
        // }
        //
        // const datos = await respuesta.json();
        // poblarKpis(datos);
        // poblarGraficoTasa(datos.tasa_concesion   || []);
        // poblarGraficoLineas(datos.lineas_epa_2025 || {});

        // TODO: conectar con endpoint real cuando backend lo implemente.
        // Descomentar las líneas siguientes cuando GET /estadisticas/por-ccaa/ esté disponible:
        //
        // const respuestaCcaa = await fetch(`${API_URL}/estadisticas/por-ccaa/`);
        //
        // if (!respuestaCcaa.ok) {
        //     let cuerpo = {};
        //     try { cuerpo = await respuestaCcaa.json(); } catch (_) {}
        //     errorMensaje.textContent    = cuerpo.mensaje    || `Error ${respuestaCcaa.status}`;
        //     errorSugerencia.textContent = cuerpo.sugerencia || '';
        //     errorBox.style.display      = 'block';
        //     throw new Error(`Error ${respuestaCcaa.status}`);
        // }
        //
        // const datosCcaa = await respuestaCcaa.json();
        // poblarGraficoCcaa(datosCcaa);
        // poblarRankingCcaa(datosCcaa);

        // Mientras los endpoints no existan, no hacemos nada:
        // los placeholders del HTML permanecen visibles.

    } catch (error) {
        console.error('Error al cargar estadísticas avanzadas:', error);
    } finally {
        spinner.style.display = 'none';
    }
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarKpis
// Rellena los 4 KPIs de la fila superior.
// ─────────────────────────────────────────────────────────────
/**
 * poblarKpis(datos)
 * Recibe el objeto del endpoint /estadisticas/avanzadas/ y
 * actualiza el texto de cada tarjeta KPI.
 *
 * @param {Object} datos - Objeto de respuesta del endpoint
 */
function poblarKpis(datos) {
    if (kpiImporteMedioEpa) {
        kpiImporteMedioEpa.textContent =
            datos.importe_medio_epa != null
                ? formatearEuros(datos.importe_medio_epa)
                : '—';
    }
    if (kpiImporteMedioEell) {
        kpiImporteMedioEell.textContent =
            datos.importe_medio_eell != null
                ? formatearEuros(datos.importe_medio_eell)
                : '—';
    }
    if (kpiCcaaTop) {
        kpiCcaaTop.textContent = datos.ccaa_top || '—';
    }
    if (kpiAgrupaciones) {
        kpiAgrupaciones.textContent =
            datos.num_agrupaciones != null
                ? datos.num_agrupaciones.toLocaleString('es-ES')
                : '—';
    }
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoCcaa
// Crea un gráfico de barras horizontales con Chart.js.
// ─────────────────────────────────────────────────────────────
/**
 * poblarGraficoCcaa(datosCcaa)
 * Recibe el array del endpoint /estadisticas/por-ccaa/ y
 * crea un gráfico de barras horizontales en #grafico-ccaa.
 *
 * @param {Array} datosCcaa - Array [{ ccaa, importe_total, num_concesiones }]
 */
function poblarGraficoCcaa(datosCcaa) {
    if (!datosCcaa.length) return;

    // Ordenar de mayor a menor importe
    const ordenados = [...datosCcaa].sort((a, b) => b.importe_total - a.importe_total);

    if (ccaaPendiente) ccaaPendiente.style.display  = 'none';
    if (graficoCcaa)   graficoCcaa.style.display    = 'block';

    new Chart(graficoCcaa, {
        type: 'bar',
        data: {
            labels:   ordenados.map(d => d.ccaa),
            datasets: [{
                label:           'Importe concedido (€)',
                data:            ordenados.map(d => d.importe_total),
                backgroundColor: 'rgba(37, 99, 235, 0.7)',
                borderColor:     'rgba(37, 99, 235, 1)',
                borderWidth:     1,
            }],
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => formatearEuros(ctx.parsed.x),
                    },
                },
            },
            scales: {
                x: {
                    ticks: {
                        callback: val => formatearEuros(val),
                    },
                },
            },
        },
    });
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoTasa
// Crea un gráfico de líneas comparativo EPA vs EELL.
// ─────────────────────────────────────────────────────────────
/**
 * poblarGraficoTasa(tasas)
 * Recibe el array tasa_concesion del endpoint /estadisticas/avanzadas/
 * y crea un gráfico de líneas en #grafico-tasa.
 *
 * @param {Array} tasas - Array [{ anio, tasa_epa, tasa_eell }]
 */
function poblarGraficoTasa(tasas) {
    if (!tasas.length) return;

    if (tasaPendiente) tasaPendiente.style.display = 'none';
    if (graficoTasa)   graficoTasa.style.display   = 'block';

    new Chart(graficoTasa, {
        type: 'line',
        data: {
            labels: tasas.map(d => d.anio),
            datasets: [
                {
                    label:       'EPA (%)',
                    data:        tasas.map(d => d.tasa_epa),
                    borderColor: 'rgba(37, 99, 235, 1)',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension:     0.3,
                    fill:        true,
                },
                {
                    label:       'EELL (%)',
                    data:        tasas.map(d => d.tasa_eell),
                    borderColor: 'rgba(16, 185, 129, 1)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension:     0.3,
                    fill:        true,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)} %`,
                    },
                },
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: { callback: val => `${val} %` },
                },
            },
        },
    });
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoLineas
// Crea un donut comparativo de líneas EPA 2025.
// ─────────────────────────────────────────────────────────────
/**
 * poblarGraficoLineas(lineas)
 * Recibe el objeto lineas_epa_2025 y crea un donut en #grafico-lineas.
 *
 * @param {Object} lineas - { abandonados: number, colonias: number }
 */
function poblarGraficoLineas(lineas) {
    if (!lineas.abandonados && !lineas.colonias) return;

    if (lineasPendiente) lineasPendiente.style.display = 'none';
    if (graficoLineas)   graficoLineas.style.display   = 'block';

    new Chart(graficoLineas, {
        type: 'doughnut',
        data: {
            labels: ['Animales abandonados', 'Colonias felinas'],
            datasets: [{
                data:            [lineas.abandonados || 0, lineas.colonias || 0],
                backgroundColor: ['rgba(37, 99, 235, 0.8)', 'rgba(16, 185, 129, 0.8)'],
                borderWidth:     2,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: ctx => formatearEuros(ctx.parsed),
                    },
                },
            },
        },
    });
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarRankingCcaa
// Inserta los elementos del ranking en la lista #ranking-ccaa.
// ─────────────────────────────────────────────────────────────
/**
 * poblarRankingCcaa(datosCcaa)
 * Ordena el array por importe_total y construye un <li> por CCAA.
 *
 * @param {Array} datosCcaa - Array [{ ccaa, importe_total, num_concesiones }]
 */
function poblarRankingCcaa(datosCcaa) {
    if (!datosCcaa.length || !rankingCcaa) return;

    if (rankingPendiente) rankingPendiente.style.display = 'none';

    const ordenados = [...datosCcaa]
        .sort((a, b) => b.importe_total - a.importe_total)
        .slice(0, 10);

    rankingCcaa.innerHTML = '';

    ordenados.forEach((d, i) => {
        const li = document.createElement('li');
        li.className = 'ranking-lista__item';

        const posicion = document.createElement('span');
        posicion.className   = 'ranking-lista__posicion';
        posicion.textContent = `${i + 1}`;

        const nombre = document.createElement('span');
        nombre.className   = 'ranking-lista__nombre';
        nombre.textContent = d.ccaa;

        const importe = document.createElement('span');
        importe.className   = 'ranking-lista__valor';
        importe.textContent = formatearEuros(d.importe_total);

        li.appendChild(posicion);
        li.appendChild(nombre);
        li.appendChild(importe);
        rankingCcaa.appendChild(li);
    });
}


// ─────────────────────────────────────────────────────────────
// UTILIDAD: formatearEuros
// ─────────────────────────────────────────────────────────────
/**
 * formatearEuros(valor)
 * Devuelve el número formateado como moneda EUR con separadores
 * de miles y dos decimales (ej: "1.234.567,89 €").
 *
 * @param  {number} valor
 * @returns {string}
 */
function formatearEuros(valor) {
    return Number(valor).toLocaleString('es-ES', {
        style:    'currency',
        currency: 'EUR',
        maximumFractionDigits: 0,
    });
}


// ─────────────────────────────────────────────────────────────
// PUNTO DE ENTRADA
// ─────────────────────────────────────────────────────────────
/**
 * Se llama cuando el DOM está completamente construido.
 * Mismo patrón que home.js, estadisticas.js, recursos.js, etc.
 */
document.addEventListener('DOMContentLoaded', () => {
    cargarEstadisticasAvanzadas();
});
