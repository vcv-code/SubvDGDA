/**
 * estadisticas-eell.js — Lógica de la página de estadísticas EELL
 * ─────────────────────────────────────────────────────────────────
 * Gestiona la carga y presentación del análisis específico de
 * Entidades de la Administración Local (EELL / ayuntamientos):
 *   · % ayuntamientos con ayuda
 *   · Importe medio EELL
 *   · Ratio de exclusión
 *   · CCAA con más concesiones
 *   · Top provincias por importe (barras horizontales)
 *   · Concentración top 10% vs resto (donut)
 *   · Ranking CCAA por importe (lista HTML)
 *   · Mapa CCAA (pendiente de decisión técnica)
 *
 * ENDPOINT:
 *   GET /estadisticas/eell
 *   Respuesta esperada: {
 *     pct_ayuntamientos_con_ayuda: number,   // 0-100
 *     importe_medio:               number,
 *     ratio_exclusion:             number,   // 0-1
 *     ccaa_top:                    string,
 *     por_ccaa: [
 *       { ccaa: string, importe_total: number, num_concesiones: number },
 *       ...
 *     ],
 *     top_provincias: [
 *       { provincia: string, importe_total: number },
 *       ...
 *     ],
 *     concentracion: {
 *       top_10_pct:  number,   // % del importe acaparado por el top 10%
 *       resto_pct:   number    // % del importe del resto (100 - top_10_pct)
 *     }
 *   }
 */


// ─────────────────────────────────────────────────────────────
// CONFIGURACIÓN
// ─────────────────────────────────────────────────────────────

const API_URL = '';

const COLORES = {
    azul:        '#1A3429',
    azulClaro:   '#2DC26C',
    verdeOscuro: '#1A3429',
    verdeMedio:  '#2DC26C',
    grisTexto:   '#616161',
    grisMedio:   '#E0E0E0',
};

const OPCIONES_BASE = {
    responsive:          true,
    maintainAspectRatio: false,
    devicePixelRatio:    window.devicePixelRatio || 2,
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
const kpiPctAyuntamientos = document.getElementById('kpi-pct-ayuntamientos');
const kpiImporteMedioEell = document.getElementById('kpi-importe-medio-eell');
const kpiRatioExclusion   = document.getElementById('kpi-ratio-exclusion');
const kpiCcaaTop          = document.getElementById('kpi-ccaa-top');

// Canvas y placeholders
const provinciasPendiente    = document.getElementById('provincias-pendiente');
const graficoTopProvincias   = document.getElementById('grafico-top-provincias');

const concentracionPendiente = document.getElementById('concentracion-pendiente');
const graficoConcentracion   = document.getElementById('grafico-concentracion');

// ranking-ccaa movido a exclusivo.html — estos elementos ya no existen en esta página


// ─────────────────────────────────────────────────────────────
// FUNCIÓN PRINCIPAL: cargarEstadisticasEell
// ─────────────────────────────────────────────────────────────
/**
 * cargarEstadisticasEell()
 * Llama al endpoint GET /estadisticas/eell y pinta KPIs y gráficos.
 *
 * Patrón idéntico al del resto de páginas del proyecto:
 *   1. Mostrar spinner
 *   2. Fetch a /estadisticas/eell
 *   3. Si !ok → mostrar error-box con mensaje y sugerencia
 *   4. Si ok  → poblar KPIs y gráficos
 *   5. Ocultar spinner en finally (siempre)
 */
async function cargarEstadisticasEell() {
    spinner.style.display = 'block';

    try {

        const respuesta = await fetch(`${API_URL}/estadisticas/eell`);

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
        poblarGraficoTopProvincias(datos.top_provincias   || []);
        poblarGraficoConcentracion(datos.concentracion    || {});
        poblarTop5Ccaa(datos.por_ccaa                     || []);
        poblarTop5Concesiones(datos.por_ccaa              || []);

    } catch (error) {
        console.error('Error al cargar estadísticas EELL:', error);
        if (!errorMensaje.textContent) {
            errorMensaje.textContent    = 'No se pudo conectar con el servidor.';
            errorSugerencia.textContent = 'Comprueba que el backend está activo.';
        }
        errorBox.style.display = 'block';
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
 * @param {Object} datos - Objeto de respuesta de /estadisticas/eell
 */
function poblarKpis(datos) {
    if (kpiPctAyuntamientos) {
        kpiPctAyuntamientos.textContent =
            datos.pct_ayuntamientos_con_ayuda != null
                ? Math.round(datos.pct_ayuntamientos_con_ayuda) + ' %'
                : '—';
    }
    if (kpiImporteMedioEell) {
        kpiImporteMedioEell.textContent =
            datos.importe_medio != null ? formatearEuros(datos.importe_medio) : '—';
    }
    if (kpiRatioExclusion) {
        kpiRatioExclusion.textContent =
            datos.ratio_exclusion != null
                ? Math.round(datos.ratio_exclusion * 100) + ' %'
                : '—';
    }
    if (kpiCcaaTop) {
        kpiCcaaTop.textContent = datos.ccaa_top || '—';
    }
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoTopProvincias
// Barras horizontales: top provincias por importe.
// ─────────────────────────────────────────────────────────────
/**
 * @param {Array} topProvincias - [{ provincia: string, importe_total: number }, ...]
 */
function poblarGraficoTopProvincias(topProvincias) {
    if (!topProvincias.length) return;

    const top = topProvincias.slice(0, 15);
    if (provinciasPendiente)  provinciasPendiente.style.display  = 'none';
    if (graficoTopProvincias) graficoTopProvincias.style.display = 'block';

    const abreviarProv = (s) => s.replace('Santa Cruz de Tenerife', 'S.C. Tenerife');

    const instancia = new Chart(graficoTopProvincias, {
        type: 'bar',
        data: {
            labels: top.map(d => abreviarProv(d.provincia)),
            datasets: [{
                label:           'Importe (€)',
                data:            top.map(d => d.importe_total),
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
    configurarDescarga(instancia, 'btn-dl-provincias', 'top-provincias-eell.png');
    configurarModal(instancia, 'Top provincias por importe EELL', `
<p>Las provincias y comunidades con mayor importe concedido concentran una parte importante de las ayudas, aunque esto no parece deberse únicamente al tamaño poblacional o a la existencia de grandes ciudades.</p>
<p>Castilla-La Mancha encabeza el importe total concedido, mientras Andalucía lidera en número de ayuntamientos beneficiados. Sin embargo, los datos muestran que muchas ayudas relevantes recaen en municipios pequeños y medianos —especialmente mediante agrupaciones— y no únicamente en grandes capitales.</p>
<p>De hecho, entre las entidades con mayores importes aparecen numerosos municipios de Tramo 1 y Tramo 2, así como agrupaciones municipales creadas para poder afrontar conjuntamente costes de gestión, esterilización o control de colonias felinas.</p>
<p>Esto sugiere que factores como la capacidad técnica para presentar proyectos, el grado de implicación institucional o la voluntad política local influyen tanto o más que la población total a la hora de acceder a estas subvenciones.</p>
<p>El buscador público permite consultar y filtrar ayudas por comunidades, provincias y municipios, y analizar agrupaciones y tramos. Además, los usuarios registrados pueden acceder a mapas interactivos, rankings y tablas avanzadas para analizar con más detalle la distribución territorial y evolución de las subvenciones.</p>
`);
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoConcentracion
// Donut: top 10% de entidades vs el resto del importe.
// ─────────────────────────────────────────────────────────────
/**
 * @param {Object} concentracion - { top_10_pct: number, resto_pct: number }
 */
function poblarGraficoConcentracion(concentracion) {
    if (concentracion.top_10_pct == null) return;

    if (concentracionPendiente) concentracionPendiente.style.display = 'none';
    if (graficoConcentracion)   graficoConcentracion.style.display   = 'block';

    const instancia = new Chart(graficoConcentracion, {
        type: 'doughnut',
        data: {
            labels: ['Top 10% de entidades', 'Resto de entidades'],
            datasets: [{
                data: [
                    Math.round(concentracion.top_10_pct),
                    Math.round(concentracion.resto_pct),
                ],
                backgroundColor: [COLORES.azul, COLORES.azulClaro],
                borderWidth:     2,
                borderColor:     '#ffffff',
                hoverOffset:     8,
            }],
        },
        options: {
            ...OPCIONES_BASE,
            cutout: '62%',
            plugins: {
                legend: {
                    display:  true,
                    position: 'bottom',
                    labels: {
                        font:            { family: 'Inter', size: 11 },
                        color:           COLORES.grisTexto,
                        boxWidth:        12,
                        boxHeight:       12,
                        borderRadius:    3,
                        useBorderRadius: true,
                        padding:         12,
                    },
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.label}: ${ctx.parsed} % del importe total`,
                    },
                },
            },
        },
    });
    configurarDescarga(instancia, 'btn-dl-concentracion', 'concentracion-eell.png');
    configurarModal(instancia, 'Concentración del importe EELL', `
<p>El 10&nbsp;% de las entidades con mayor subvención concentra una parte muy significativa del importe total concedido. Sin embargo, esta concentración no responde únicamente a grandes ciudades, sino también al funcionamiento por tramos y a la existencia de agrupaciones municipales.</p>
<p>Muchos de los importes más altos corresponden a municipios pequeños o medianos que presentan proyectos conjuntos para poder asumir costes veterinarios, campañas de esterilización o gestión de colonias felinas de forma coordinada.</p>
<p>Aun así, la distribución sigue reflejando importantes desigualdades territoriales. Mientras algunas comunidades y ayuntamientos muestran una participación activa y capacidad para acceder a ayudas, otros territorios continúan teniendo poca presencia, ya sea por falta de medios técnicos, escasa prioridad política o dificultades administrativas.</p>
<p>Los usuarios registrados pueden explorar además rankings, mapas de calor y estadísticas avanzadas que permiten identificar qué territorios concentran una mayor parte de los fondos y cómo evoluciona el reparto entre convocatorias.</p>
`);
}


// poblarRankingCcaa eliminada — el ranking CCAA se muestra en exclusivo.html


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarTop5Ccaa  (Task 2.4)
// Lista top 5 CCAA por importe con barra de proporción.
// ─────────────────────────────────────────────────────────────

/**
 * poblarTop5Ccaa(porCcaa)
 * Ordena el array por importe_total (desc), toma los 5 primeros y
 * construye una lista visual con:
 *   · Número de posición (1–5)
 *   · Nombre de la comunidad autónoma
 *   · Barra proporcional (el #1 = 100 %, los demás en proporción)
 *   · Importe formateado
 *
 * Usa por_ccaa[] que ya devuelve GET /estadisticas/eell.
 * No requiere endpoint nuevo ni cambio en backend.
 *
 * @param {Array} porCcaa - [{ ccaa: string, importe_total: number, num_concesiones: number }, ...]
 */
function poblarTop5Ccaa(porCcaa) {
    const lista     = document.getElementById('top5-ccaa-lista');
    const pendiente = document.getElementById('top5-ccaa-pendiente');

    if (!porCcaa.length || !lista) return;

    const top5 = [...porCcaa]
        .sort((a, b) => b.importe_total - a.importe_total)
        .slice(0, 5);

    if (!top5.length) return;

    if (pendiente) pendiente.style.display = 'none';
    lista.style.display = 'flex';

    const maxImporte = top5[0].importe_total;  // El #1 es el 100 %

    lista.innerHTML = top5.map((d, i) => {
        const pct = maxImporte > 0
            ? Math.round((d.importe_total / maxImporte) * 100)
            : 0;
        return `
            <li class="top5-lista__item">
                <span class="top5-lista__pos">${i + 1}</span>
                <span class="top5-lista__nombre-barra">
                    <span class="top5-lista__nombre" title="${d.ccaa}">${d.ccaa}</span>
                    <span class="top5-lista__pista">
                        <span class="top5-lista__fill" style="width:${pct}%;"></span>
                    </span>
                </span>
                <span class="top5-lista__valor">${formatearEuros(d.importe_total)}</span>
            </li>`;
    }).join('');
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarTop5Concesiones  (Task 3.2)
// Lista top 5 CCAA por número de concesiones acumuladas.
// ─────────────────────────────────────────────────────────────

/**
 * poblarTop5Concesiones(porCcaa)
 * Ordena el array por num_concesiones (desc), toma los 5 primeros y
 * construye una lista visual con:
 *   · Número de posición (1–5)
 *   · Nombre de la comunidad autónoma
 *   · Barra proporcional (el #1 = 100 %, los demás en proporción)
 *   · Número de concesiones formateado
 *
 * Complementa poblarTop5Ccaa: una CCAA puede acumular muchas concesiones
 * pequeñas sin destacar por importe total, y viceversa.
 * Reutiliza por_ccaa[] ya devuelto por GET /estadisticas/eell.
 *
 * @param {Array} porCcaa - [{ ccaa: string, importe_total: number, num_concesiones: number }, ...]
 */
function poblarTop5Concesiones(porCcaa) {
    const lista     = document.getElementById('top5-concesiones-lista');
    const pendiente = document.getElementById('top5-concesiones-pendiente');

    if (!porCcaa.length || !lista) return;

    const top5 = [...porCcaa]
        .sort((a, b) => b.num_concesiones - a.num_concesiones)
        .slice(0, 5);

    if (!top5.length) return;

    if (pendiente) pendiente.style.display = 'none';
    lista.style.display = 'flex';

    const maxConcesiones = top5[0].num_concesiones;

    lista.innerHTML = top5.map((d, i) => {
        const pct = maxConcesiones > 0
            ? Math.round((d.num_concesiones / maxConcesiones) * 100)
            : 0;
        return `
            <li class="top5-lista__item">
                <span class="top5-lista__pos">${i + 1}</span>
                <span class="top5-lista__nombre-barra">
                    <span class="top5-lista__nombre" title="${d.ccaa}">${d.ccaa}</span>
                    <span class="top5-lista__pista">
                        <span class="top5-lista__fill" style="width:${pct}%;"></span>
                    </span>
                </span>
                <span class="top5-lista__valor">${d.num_concesiones.toLocaleString('es-ES')}</span>
            </li>`;
    }).join('');
}


// ─────────────────────────────────────────────────────────────
// UTILIDADES
// ─────────────────────────────────────────────────────────────

/**
 * configurarDescarga(instanciaChart, btnId, nombreArchivo)
 * Muestra el botón de descarga y lo conecta al PNG del gráfico.
 * Idéntica a la de home.js y estadisticas-epas.js — cada JS es independiente.
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
    const num = Math.round(Number(valor));
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' €';
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
    cargarEstadisticasEell();
});
