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
    verdeOscuro:  '#1A3429',
    verdeMedio:   '#2DC26C',
    verdeClaro:   '#A5D6A7',
    azul:         '#1A3429',
    grisTexto:    '#616161',
    grisMedio:    '#E0E0E0',
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

const exclusionesAnioPendiente  = document.getElementById('exclusiones-anio-pendiente');
const graficoExclusionesAnio    = document.getElementById('grafico-exclusiones-anio');
const causasFrecuentesPendiente = document.getElementById('causas-frecuentes-pendiente');
const graficoCausasFrecuentes   = document.getElementById('grafico-causas-frecuentes');
const causasFrecuentesSub       = document.getElementById('causas-frecuentes-sub');

// Rojo del estado "excluida" (mismo que los badges y chips del buscador)
const COLOR_EXCLUIDA = '#C62828';
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
 *   2. Fetch a /estadisticas/epas
 *   3. Si !ok → mostrar error-box con mensaje y sugerencia
 *   4. Si ok  → poblar KPIs y gráficos
 *   5. Ocultar spinner en finally (siempre)
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
        poblarGraficoExclusionesAnio(datos.exclusiones || {});
        poblarGraficoCausasFrecuentes(datos.exclusiones || {});

    } catch (error) {
        console.error('Error al cargar estadísticas EPAs:', error);
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
        const tag = document.getElementById('kpi-nuevas-entidades-tag');
        if (tag && datos.por_anio?.length) {
            const ultimoAnio = Math.max(...datos.por_anio.map(d => d.anio));
            tag.textContent = `Primera vez concedida en ${ultimoAnio}`;
        }
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
    configurarModal(instancia, 'Distribución de importes EPA', `
<p>La mayoría de las protectoras reciben importes relativamente modestos, concentrados principalmente entre 2.000&nbsp;€ y 6.000&nbsp;€. Las ayudas superiores a 8.000&nbsp;€ son claramente minoritarias y muy pocas entidades llegaron a los 10.000&nbsp;€, algo que únicamente ocurrió en 2024.</p>
<p>En convocatorias anteriores los límites habituales eran menores (máximo 5.000&nbsp;€, aunque en 2023 y 2024 las convocatorias fueron semestrales en lugar de anuales). En 2025, aunque el máximo seguía fijado en 10.000&nbsp;€, las ayudas más altas apenas superaron los 8.000&nbsp;€.</p>
<p>Los datos muestran un reparto relativamente equilibrado y sin grandes concentraciones de fondos. Sin embargo, también reflejan la escasa magnitud económica real de estas subvenciones frente al volumen de gasto que asumen muchas asociaciones. En numerosos casos, estas ayudas apenas cubren una cuarta parte —o menos— del coste total de los proyectos.</p>
<p>Además, como el trabajo necesario para sostener estas actividades se realiza de forma voluntaria y no remunerada, supone un importante ahorro indirecto para la administración que, de ser asumidas mediante personal contratado, implicarían costes salariales, cotizaciones e impuestos muy superiores.</p>
<p>Las protectoras deben además adelantar grandes cantidades de dinero para ejecutar y justificar proyectos completos, aunque finalmente la subvención cubra solo una parte reducida del coste total. Esto genera incertidumbre económica y dificulta especialmente la participación de entidades pequeñas sostenidas únicamente por voluntariado, hasta el punto de que muchas veces les resulta inviable presentarse a la convocatoria.</p>
`);
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
    configurarModal(instancia, 'Media vs mediana por año', `
<p>La mediana se mantiene sistemáticamente por debajo de la media en todos los años analizados. Esto indica que unas pocas entidades con importes más altos elevan el promedio general, mientras que la mayoría de las protectoras reciben realmente cantidades inferiores a la media.</p>
<p>Por ello, la mediana refleja mejor la realidad habitual de la convocatoria: la protectora «tipo» recibe ayudas relativamente modestas frente al volumen real de gastos que debe asumir.</p>
<p>Además, la diferencia entre media y mediana también evidencia que pequeñas variaciones en puntuación pueden traducirse en diferencias económicas relevantes dentro de una convocatoria ya de por sí limitada presupuestariamente.</p>
`);
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
    configurarModal(instancia, 'Entidades nuevas y recurrentes', `
<p>La mayor parte de las entidades beneficiarias ya habían participado en convocatorias anteriores. Las nuevas incorporaciones se mantienen relativamente estables, lo que indica la existencia de un núcleo consolidado de protectoras con experiencia previa en este tipo de subvenciones.</p>
<p>Esto puede interpretarse de dos formas: por un lado, demuestra continuidad y especialización; pero también refleja las dificultades de acceso para entidades pequeñas o con menos recursos administrativos, especialmente teniendo en cuenta la carga burocrática, la necesidad de adelantar gastos y la complejidad de las justificaciones económicas.</p>
<p>Muchas asociaciones funcionan únicamente con voluntariado y sin apoyo profesional externo, por lo que afrontar facturas, memorias, presupuestos y documentación técnica supone un esfuerzo añadido muy importante que no todas pueden permitirse.</p>
`);
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

    const abreviar = (s) => s
        .replace(/^ASOCIACI[ÓO]N\b/i, 'A.')
        .replace(/^ASSOCIACIÓ\b/i,     'A.')
        .replace(/^ASOC\b/i,           'A.')
        .replace(/PROTECTORA\b/gi,     'P.');

    const instancia = new Chart(graficoTop, {
        type: 'bar',
        data: {
            labels: top.map((d, i) => `${i + 1}ª - ${abreviar(d.nombre)}`),
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
            layout: { padding: { left: 0 } },
            plugins: {
                ...OPCIONES_BASE.plugins,
                tooltip: {
                    callbacks: {
                        title: ctx => top[ctx[0].dataIndex].nombre,
                        label: ctx => ` ${formatearEuros(ctx.parsed.x)}`,
                    },
                },
            },
            scales: {
                x: {
                    min:  7000,
                    max:  8500,
                    grid:  { color: COLORES.grisMedio },
                    ticks: {
                        font:      { family: 'Inter', size: 11 },
                        color:     COLORES.grisTexto,
                        stepSize:  500,
                        callback:  v => {
                            const k = v / 1000;
                            return (k % 1 === 0 ? k : k.toFixed(1).replace('.', ',')) + ' K';
                        },
                    },
                },
                y: {
                    grid:  { display: false },
                    ticks: {
                        font:       { family: 'Inter', size: 10 },
                        color:      COLORES.grisTexto,
                        crossAlign: 'far',
                    },
                    afterFit: (axis) => { axis.width = 290; },
                },
            },
        },
    });
    configurarDescarga(instancia, 'btn-dl-top', 'top-beneficiarios-epa.png');
    configurarModal(instancia, 'Top beneficiarios EPA', `
<p>Las entidades con mayor importe acumulado suelen ser protectoras que han obtenido buenas puntuaciones de forma continuada en varias convocatorias. El sistema tiende a premiar la trayectoria, la capacidad de gestión y la consolidación de proyectos a largo plazo.</p>
<p>Sin embargo, incluso entre las entidades mejor posicionadas, los importes concedidos siguen siendo relativamente reducidos si se comparan con los costes reales que asumen las protectoras: atención veterinaria, alimentación, esterilizaciones, rescates, transporte o mantenimiento de instalaciones.</p>
<p>Además, el modelo actual genera cierta incertidumbre económica, ya que las asociaciones deben ejecutar y justificar proyectos completos antes de conocer con exactitud qué importe recibirán o incluso si finalmente obtendrán subvención.</p>
`);

    const tituloEl = graficoTop.closest('.card-grafico')?.querySelector('.card-grafico__titulo');
    if (tituloEl) tituloEl.textContent = `Top beneficiarios ${ultimo.anio}`;
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoExclusionesAnio
// Barras: nº de solicitudes EPA excluidas por convocatoria.
// Datos: exclusiones.por_anio[{ anio, total }]
// ─────────────────────────────────────────────────────────────
function poblarGraficoExclusionesAnio(exclusiones) {
    const porAnio = exclusiones.por_anio || [];
    if (!porAnio.length) return;
    if (exclusionesAnioPendiente) exclusionesAnioPendiente.style.display = 'none';
    if (graficoExclusionesAnio)   graficoExclusionesAnio.style.display   = 'block';

    const instancia = new Chart(graficoExclusionesAnio, {
        type: 'bar',
        data: {
            labels: porAnio.map(d => d.anio),
            datasets: [{
                label:           'Solicitudes excluidas',
                data:            porAnio.map(d => d.total),
                backgroundColor: COLOR_EXCLUIDA,
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
                        label: ctx => ` ${ctx.parsed.y.toLocaleString('es-ES')} excluidas`,
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
                    ticks: { font: { family: 'Inter', size: 11 }, color: COLORES.grisTexto },
                },
            },
        },
    });
    configurarDescarga(instancia, 'btn-dl-exclusiones-anio', 'exclusiones-por-anio-epa.png');
    configurarModal(instancia, 'Exclusiones EPA por año', `
<p>Las exclusiones de protectoras han sido muy variables: 21 en 2021, 59 en 2022 (el año con más tropiezos documentales de la primera etapa), solo 13 y 14 en 2023 y 2024, y un salto hasta 110 en 2025. Ese repunte acompaña al crecimiento de la convocatoria —cada año se presentan más asociaciones— y a un control formal más minucioso: la resolución de 2025 detalla 27 causas distintas de exclusión.</p>
<p>Un matiz de lectura: en 2021–2023 el BOE llama a estas solicitudes "desestimadas", pero todas llevan una causa formal de exclusión (documentación que falta, plazos, requisitos de registro), así que se contabilizan igual en toda la serie.</p>
<p>Quedar excluida no significa no necesitar la ayuda: son requisitos administrativos que muchas asociaciones pequeñas, gestionadas por voluntariado, no siempre pueden cubrir sin apoyo técnico.</p>
`);
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoCausasFrecuentes
// Barras horizontales: top de causas del ÚLTIMO año con exclusiones.
// Solo un año porque cada convocatoria usa su propia numeración de
// causas (el "5" de 2022 no es el "5" de 2023).
// Datos: exclusiones.{ causas_anio, causas_frecuentes[{ codigo, motivo, total }] }
// ─────────────────────────────────────────────────────────────
function poblarGraficoCausasFrecuentes(exclusiones) {
    const causas = exclusiones.causas_frecuentes || [];
    if (!causas.length) return;
    if (causasFrecuentesPendiente) causasFrecuentesPendiente.style.display = 'none';
    if (graficoCausasFrecuentes)   graficoCausasFrecuentes.style.display   = 'block';

    if (causasFrecuentesSub && exclusiones.causas_anio) {
        causasFrecuentesSub.textContent =
            `Top de causas de la convocatoria ${exclusiones.causas_anio} (código oficial)`;
    }

    // Partir el motivo en líneas de ~55 caracteres para el tooltip
    const partirMotivo = (texto) => {
        const palabras = (texto || '').split(' ');
        const lineas = [];
        let linea = '';
        for (const p of palabras) {
            if ((linea + ' ' + p).trim().length > 55) {
                lineas.push(linea.trim());
                linea = p;
            } else {
                linea += ' ' + p;
            }
        }
        if (linea.trim()) lineas.push(linea.trim());
        return lineas;
    };

    const instancia = new Chart(graficoCausasFrecuentes, {
        type: 'bar',
        data: {
            labels: causas.map(c => c.codigo),
            datasets: [{
                label:           'Solicitudes con esta causa',
                data:            causas.map(c => c.total),
                backgroundColor: COLOR_EXCLUIDA,
                borderRadius:    4,
                borderSkipped:   false,
            }],
        },
        options: {
            ...OPCIONES_BASE,
            indexAxis: 'y',   // barras horizontales: los códigos caben mejor en el eje Y
            plugins: {
                ...OPCIONES_BASE.plugins,
                tooltip: {
                    callbacks: {
                        title: (items) => `Causa ${items[0].label}`,
                        label: ctx => ` ${ctx.parsed.x.toLocaleString('es-ES')} solicitudes`,
                        afterBody: (items) => partirMotivo(causas[items[0].dataIndex]?.motivo),
                    },
                },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid:  { color: COLORES.grisMedio },
                    ticks: { font: { family: 'Inter', size: 11 }, color: COLORES.grisTexto },
                },
                y: {
                    grid:  { display: false },
                    ticks: { font: { family: 'Inter', size: 11 }, color: COLORES.grisTexto },
                },
            },
        },
    });
    configurarDescarga(instancia, 'btn-dl-causas-frecuentes', 'causas-exclusion-epa.png');
    configurarModal(instancia, 'Causas de exclusión más frecuentes (EPA)', `
<p>En 2025 casi todo el top es documentación registral básica: no presentar la inscripción de la entidad (44 solicitudes), la copia de la tarjeta de identificación fiscal definitiva (43, más otras 21 por presentarla provisional), los estatutos (38) o incurrir en alguna de las prohibiciones del artículo 13.2 de la Ley General de Subvenciones (37). Una misma solicitud puede acumular varias causas, por eso la suma supera el total de excluidas.</p>
<p>El patrón apunta a asociaciones pequeñas, a menudo recién constituidas o gestionadas íntegramente por voluntariado, que se quedan fuera por papeles que no dependen del proyecto en sí sino de su situación administrativa. Un acompañamiento técnico previo (o una fase de subsanación más accesible) reduciría buena parte de estas exclusiones.</p>
<p>La gráfica muestra solo la última convocatoria porque cada año usa su propia numeración de causas y no son mezclables entre sí. Pasa el cursor por cada barra para ver el motivo oficial completo.</p>
`);
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
    const num = Math.round(Number(valor));
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' €';
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
