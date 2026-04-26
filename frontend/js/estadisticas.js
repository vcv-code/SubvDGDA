/**
 * estadisticas.js — Lógica del dashboard de estadísticas
 * ────────────────────────────────────────────────────────
 * Este archivo carga los datos de la API y construye los 3
 * gráficos Chart.js más el panel de KPIs y el ranking.
 *
 * FUENTE DE DATOS:
 *   GET /estadisticas/
 *   → { total_registros, total_concedidas, importe_global, por_anio[] }
 *
 * ESTRUCTURA DE por_anio[]:
 *   { anio, tipo, total, concedidas, no_beneficiarias,
 *     excluidas, desistidas, importe_total }
 *   · tipo puede ser "epa" o "eell"
 *   · EELL solo existe desde 2023
 *
 * GRÁFICOS QUE SE CREAN:
 *   1. grafico-linea  → Línea: importe total por año (EPA + EELL sumados)
 *   2. grafico-donut  → Donut: distribución de solicitudes por estado
 *   3. grafico-barras → Barras agrupadas: EPA vs EELL por año
 *
 * LIBRERÍAS USADAS:
 *   Chart.js v4 (cargada en el HTML antes que este script)
 *
 * CONCEPTOS CLAVE:
 *   · new Chart(canvas, config) → crea un gráfico en el canvas indicado
 *   · type: 'line' | 'doughnut' | 'bar' → tipo de gráfico
 *   · data.labels → etiquetas del eje X (o leyenda)
 *   · data.datasets → series de datos a dibujar
 *   · options → configuración visual (ejes, leyenda, tooltips...)
 */


// ─────────────────────────────────────────────────────────────
// CONFIGURACIÓN
// ─────────────────────────────────────────────────────────────

const API_URL = '';

/** Años del sistema, usados como etiquetas en los gráficos */
const ANIOS = [2021, 2022, 2023, 2024, 2025];

/**
 * Paleta de colores para los gráficos.
 * Usamos las mismas variables que en CSS para mantener coherencia,
 * pero en Chart.js debemos poner los valores literales (no var(--...)).
 */
const COLORES = {
    verdePrimario:  '#47C079',
    verdeOscuro:    '#2E7D32',
    verdeMedio:     '#66BB6A',
    verdeClaro:     '#A5D6A7',
    verdeFondo:     'rgba(71, 192, 121, 0.15)',  /* Con transparencia para el área */
    concedida:      '#2E7D32',
    noBeneficiaria: '#A5D6A7',
    excluida:       '#EF6C00',
    desistida:      '#C62828',
    grisTexto:      '#616161',
    grisMedio:      '#E0E0E0',
};

/**
 * Opciones base compartidas por todos los gráficos.
 * Evita repetir la misma configuración en cada Chart.
 * ¿Por qué responsive: true + maintainAspectRatio: false?
 * responsive: true → el gráfico se redimensiona con la ventana.
 * maintainAspectRatio: false → respeta la altura del .chart-container
 *   en lugar de usar la proporción ancho/alto automática.
 */
const OPCIONES_BASE = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },  /* Ocultamos la leyenda de Chart.js */
    },
};


// ─────────────────────────────────────────────────────────────
// UTILIDADES
// ─────────────────────────────────────────────────────────────

function formatearMiles(n) {
    return new Intl.NumberFormat('es-ES', { maximumFractionDigits: 0 }).format(n);
}

function formatearMillones(n) {
    const m = n / 1_000_000;
    return new Intl.NumberFormat('es-ES', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
    }).format(m) + ' M€';
}

/** Convierte 14800000 → "14.8M€" (compacto para eje Y de gráficos) */
function formatearEjeY(n) {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + ' M';
    if (n >= 1_000)     return (n / 1_000).toFixed(0) + ' K';
    return n;
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN PRINCIPAL
// ─────────────────────────────────────────────────────────────

async function cargarEstadisticas() {
    try {
        // ── Petición a la API ──────────────────────────────────────
        const respuesta = await fetch(`${API_URL}/estadisticas/`);
        if (!respuesta.ok) throw new Error(`Error ${respuesta.status}`);
        const datos = await respuesta.json();

        // ── Actualizar cada bloque de la página ────────────────────
        actualizarKPIs(datos);
        crearGraficoLinea(datos.por_anio);
        crearGraficoDonut(datos);
        crearGraficoBarras(datos.por_anio);
        // El ranking queda pendiente hasta que el backend lo implemente.
        // Cuando esté disponible, descomentar:
        // await cargarRanking();

    } catch (error) {
        console.error('Error al cargar estadísticas:', error);
        mostrarErrorGlobal();
    }
}


// ─────────────────────────────────────────────────────────────
// BLOQUE 1: TARJETAS KPI
// ─────────────────────────────────────────────────────────────

function actualizarKPIs(datos) {
    // KPI 1: total de registros
    document.getElementById('kpi-total').textContent =
        formatearMiles(datos.total_registros);

    // KPI 2: entidades únicas — pendiente de backend
    // Cuando el backend exponga el dato, cambiar por:
    // document.getElementById('kpi-entidades').textContent = formatearMiles(datos.total_entidades);
    document.getElementById('kpi-entidades').textContent = '—';

    // KPI 3: importe total concedido en millones
    document.getElementById('kpi-importe').textContent =
        formatearMillones(datos.importe_global);

    // KPI 4: porcentaje de solicitudes concedidas
    const porcentaje = Math.round(
        (datos.total_concedidas / datos.total_registros) * 100
    );
    document.getElementById('kpi-porcentaje').textContent = porcentaje + ' %';

    // El tag de tendencia lo dejamos estático para este sprint
    document.getElementById('kpi-tendencia').textContent = '+ tendencia';
}


// ─────────────────────────────────────────────────────────────
// BLOQUE 2: GRÁFICO DE LÍNEA — Evolución del importe por año
// ─────────────────────────────────────────────────────────────

/**
 * crearGraficoLinea(porAnio)
 * Suma el importe de EPA + EELL por cada año y lo muestra
 * como un gráfico de línea con área rellena.
 *
 * ¿Por qué línea con área?
 * El área rellena hace visualmente evidente que el importe
 * va creciendo con los años. Es más expresivo que una línea sola.
 *
 * @param {Array} porAnio - Array de objetos por año y tipo
 */
function crearGraficoLinea(porAnio) {
    // Calculamos el importe total por año (EPA + EELL sumados)
    const importesPorAnio = ANIOS.map(anio => {
        // .filter() devuelve todos los registros de ese año (puede ser 1 ó 2: EPA y EELL)
        // .reduce() los suma todos
        return porAnio
            .filter(d => d.anio === anio)
            .reduce((suma, d) => suma + d.importe_total, 0);
    });

    const canvas = document.getElementById('grafico-linea');

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: ANIOS,
            datasets: [{
                label: 'Importe total',
                data: importesPorAnio,

                /* Línea verde */
                borderColor:     COLORES.verdeOscuro,
                borderWidth:     2.5,

                /* Área rellena bajo la línea */
                fill:            true,
                backgroundColor: COLORES.verdeFondo,

                /* Puntos en la línea */
                pointBackgroundColor: COLORES.verdeOscuro,
                pointRadius:     5,
                pointHoverRadius: 7,

                /* Curvatura de la línea (0 = recta, 0.4 = suave) */
                tension: 0.4,
            }],
        },
        options: {
            ...OPCIONES_BASE,
            scales: {
                x: {
                    grid: { color: COLORES.grisMedio },
                    ticks: {
                        font: { family: 'Inter', size: 11 },
                        color: COLORES.grisTexto,
                    },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: COLORES.grisMedio },
                    ticks: {
                        font: { family: 'Inter', size: 11 },
                        color: COLORES.grisTexto,
                        /* Formateamos las etiquetas del eje Y en millones */
                        callback: (valor) => formatearEjeY(valor),
                    },
                },
            },
            plugins: {
                ...OPCIONES_BASE.plugins,
                tooltip: {
                    callbacks: {
                        /* Formateamos el valor del tooltip */
                        label: (ctx) => ' ' + formatearMillones(ctx.raw),
                    },
                },
            },
        },
    });
}


// ─────────────────────────────────────────────────────────────
// BLOQUE 3: GRÁFICO DE DONUT — Distribución por estado
// ─────────────────────────────────────────────────────────────

/**
 * crearGraficoDonut(datos)
 * Muestra la proporción de cada estado (concedida, no_beneficiaria,
 * excluida, desistida) sobre el total de solicitudes.
 *
 * ¿Por qué donut y no tarta?
 * El hueco central del donut permite añadir texto central en el
 * futuro (ej: porcentaje concedido) sin necesidad de modificar
 * el layout. Visualmente también es más moderno.
 *
 * @param {Object} datos - Objeto completo de /estadisticas/
 */
function crearGraficoDonut(datos) {
    // Calculamos los totales de cada estado sumando todos los años
    const totales = datos.por_anio.reduce(
        (acc, d) => {
            acc.concedidas       += d.concedidas;
            acc.noBeneficiarias  += d.no_beneficiarias;
            acc.excluidas        += d.excluidas;
            acc.desistidas       += d.desistidas;
            return acc;
        },
        { concedidas: 0, noBeneficiarias: 0, excluidas: 0, desistidas: 0 }
    );

    const canvas = document.getElementById('grafico-donut');

    new Chart(canvas, {
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
                borderColor: '#ffffff',   /* Separación blanca entre sectores */
                hoverOffset: 8,           /* El sector crece al hacer hover */
            }],
        },
        options: {
            ...OPCIONES_BASE,
            cutout: '62%',   /* Porcentaje del hueco central del donut */
            plugins: {
                ...OPCIONES_BASE.plugins,
                tooltip: {
                    callbacks: {
                        /* Mostramos número y porcentaje en el tooltip */
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
// BLOQUE 4: GRÁFICO DE BARRAS — EPA vs EELL por año
// ─────────────────────────────────────────────────────────────

/**
 * crearGraficoBarras(porAnio)
 * Muestra dos barras por año: una para EPA y otra para EELL.
 * Los años sin EELL (2021, 2022) solo tienen barra EPA.
 *
 * ¿Por qué barras agrupadas y no apiladas?
 * Las barras agrupadas permiten comparar fácilmente los valores
 * absolutos de EPA y EELL. Las apiladas serían mejores para
 * mostrar el total, pero en este caso la comparación importa más.
 *
 * @param {Array} porAnio - Array de objetos por año y tipo
 */
function crearGraficoBarras(porAnio) {
    // Importe EPA por año (0 si no existe ese año, aunque siempre existe)
    const importeEPA = ANIOS.map(anio => {
        const d = porAnio.find(x => x.anio === anio && x.tipo === 'epa');
        return d ? d.importe_total : 0;
    });

    // Importe EELL por año (0 para 2021 y 2022 porque no hay datos)
    const importeEELL = ANIOS.map(anio => {
        const d = porAnio.find(x => x.anio === anio && x.tipo === 'eell');
        return d ? d.importe_total : 0;
    });

    const canvas = document.getElementById('grafico-barras');

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: ANIOS,
            datasets: [
                {
                    label: 'EPA',
                    data: importeEPA,
                    backgroundColor: COLORES.verdeOscuro,
                    borderRadius: 4,    /* Bordes redondeados de la barra */
                    borderSkipped: false,
                },
                {
                    label: 'EELL',
                    data: importeEELL,
                    backgroundColor: COLORES.verdeMedio,
                    borderRadius: 4,
                    borderSkipped: false,
                },
            ],
        },
        options: {
            ...OPCIONES_BASE,
            plugins: {
                ...OPCIONES_BASE.plugins,
                /* Para este gráfico SÍ mostramos la leyenda (EPA / EELL) */
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: { family: 'Inter', size: 11 },
                        color: COLORES.grisTexto,
                        boxWidth: 12,
                        boxHeight: 12,
                        borderRadius: 3,
                        useBorderRadius: true,
                        padding: 16,
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
                    grid: { display: false },
                    ticks: {
                        font: { family: 'Inter', size: 11 },
                        color: COLORES.grisTexto,
                    },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: COLORES.grisMedio },
                    ticks: {
                        font: { family: 'Inter', size: 11 },
                        color: COLORES.grisTexto,
                        callback: (valor) => formatearEjeY(valor),
                    },
                },
            },
        },
    });
}


// ─────────────────────────────────────────────────────────────
// BLOQUE 5: RANKING TOP 5
// Pendiente de endpoint /estadisticas/ranking en el backend.
// Esta función se activará cuando esté disponible.
// ─────────────────────────────────────────────────────────────

/**
 * cargarRanking()
 * Llamará a GET /estadisticas/ranking cuando el backend lo implemente.
 * Por ahora se deja como función documentada pero no llamada.
 *
 * PENDIENTE DE BACKEND: El endpoint debe devolver una lista como:
 * [
 *   { nombre: "Ayuntamiento de Madrid", cif: "P2800100E", importe: 980000 },
 *   ...
 * ]
 */
async function cargarRanking() {
    try {
        const respuesta = await fetch(`${API_URL}/estadisticas/ranking`);
        if (!respuesta.ok) throw new Error('Ranking no disponible');

        const ranking = await respuesta.json();
        const maxImporte = ranking[0]?.importe || 1;  // Para calcular % de barra

        const lista = document.getElementById('ranking-lista');
        document.getElementById('ranking-pendiente').style.display = 'none';

        ranking.forEach((entidad, i) => {
            const pct = Math.round((entidad.importe / maxImporte) * 100);
            const li  = document.createElement('li');
            li.className = 'ranking-item';

            li.innerHTML = `
                <span class="ranking-item__pos">#${i + 1}</span>
                <div class="ranking-item__info">
                    <span class="ranking-item__nombre"
                          title="${entidad.nombre}">
                        ${entidad.nombre}
                    </span>
                    <div class="ranking-item__barra-wrapper">
                        <div class="ranking-item__barra"
                             style="width: ${pct}%;"
                             role="progressbar"
                             aria-valuenow="${pct}"
                             aria-valuemin="0"
                             aria-valuemax="100">
                        </div>
                    </div>
                </div>
                <span class="ranking-item__importe">
                    ${formatearMiles(Math.round(entidad.importe / 1000))} K€
                </span>
            `;

            lista.appendChild(li);
        });

    } catch (error) {
        // Si falla, el aviso de "pendiente" ya está visible en el HTML
        console.warn('Ranking no disponible aún:', error.message);
    }
}


// ─────────────────────────────────────────────────────────────
// MANEJO DE ERROR GLOBAL
// ─────────────────────────────────────────────────────────────

function mostrarErrorGlobal() {
    const mensaje = `
        <div class="estado-error" style="margin-bottom: var(--espacio-md);">
            No se pudo conectar con el servidor.
            Comprueba que el backend está activo (Docker o uvicorn)
        </div>
    `;
    document.querySelector('.contenedor').insertAdjacentHTML('afterbegin', mensaje);
}


// ─────────────────────────────────────────────────────────────
// PUNTO DE ENTRADA
// ─────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    cargarEstadisticas();
});
