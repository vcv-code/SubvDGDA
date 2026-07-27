/**
 * estadisticas-eell.js — Lógica de la página de estadísticas EELL
 * ─────────────────────────────────────────────────────────────────
 * Gestiona la carga y presentación del análisis específico de
 * Entidades de la Administración Local (EELL / ayuntamientos):
 *   · % ayuntamientos con ayuda
 *   · Importe medio EELL
 *   · Ratio de exclusión
 *   · Entidades que repiten (KPI con asterisco → nota fija bajo los KPIs)
 *   · Top provincias por importe (barras horizontales)
 *   · Tramos de importe concedido (barras verticales)
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
 *     },
 *     distribucion_importes: [
 *       { rango: string, cantidad: number },   // tramos de importe
 *       ...
 *     ],
 *     recurrencia_por_anio: [
 *       { anio: number, nuevas: number, recurrentes: number },
 *       ...
 *     ],
 *     entidades_repiten: number,   // beneficiarias con ayuda en >1 año
 *     total_entidades:   number    // beneficiarias únicas (concedidas)
 *   }
 *   Nota: ccaa_top y concentracion se siguen devolviendo pero ya no se
 *   pintan en esta página (el donut se sustituyó por los tramos de importe).
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
const kpiEellRepiten      = document.getElementById('kpi-eell-repiten');
const kpiEellRepitenTag   = document.getElementById('kpi-eell-repiten-tag');

// Canvas y placeholders
const provinciasPendiente    = document.getElementById('provincias-pendiente');
const graficoTopProvincias   = document.getElementById('grafico-top-provincias');

const tramosPendiente        = document.getElementById('tramos-pendiente');
const graficoTramos          = document.getElementById('grafico-tramos');

const exclusionesAnioPendiente  = document.getElementById('exclusiones-anio-pendiente');
const graficoExclusionesAnio    = document.getElementById('grafico-exclusiones-anio');
const causasFrecuentesPendiente = document.getElementById('causas-frecuentes-pendiente');
const graficoCausasFrecuentes   = document.getElementById('grafico-causas-frecuentes');
const causasFrecuentesSub       = document.getElementById('causas-frecuentes-sub');

// Rojo del estado "excluida" (mismo que los badges y chips del buscador)
const COLOR_EXCLUIDA = '#C62828';

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
        poblarGraficoTramos(datos.distribucion_importes   || []);
        poblarTop5Ccaa(datos.por_ccaa                     || []);
        poblarTop5Concesiones(datos.por_ccaa              || []);
        poblarRecurrencia(datos);
        poblarGraficoExclusionesAnio(datos.exclusiones    || {});
        poblarGraficoCausasFrecuentes(datos.exclusiones   || {});

        // Mapa CCAA (Leaflet). El modal de top municipios al hacer
        // clic vive en js/modal-ccaa.js (window.abrirModalCCAA). Se retrasa un
        // pelín para asegurar que Leaflet (defer) ya ha cargado.
        if (typeof pintarMapaCCAA === 'function') {
            setTimeout(() => pintarMapaCCAA(datos.por_ccaa || [], window.abrirModalCCAA), 150);
        }

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
    // El KPI de recurrencia (entidades que repiten) se rellena en
    // poblarRecurrencia, junto a su tabla por año.
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
<p><strong>Evolución 2023–2025.</strong> El reparto territorial ha cambiado mucho entre convocatorias. En 2023 las ayudas estaban muy repartidas (15 comunidades, con Castilla-La Mancha, Comunidad Valenciana, Región de Murcia y Canarias entre el 12&nbsp;% y el 18&nbsp;% cada una). En 2024 se concentraron drásticamente: solo 8 comunidades recibieron ayuda y dos —Castilla-La Mancha (41&nbsp;%) y Andalucía (32&nbsp;%)— acapararon casi tres cuartas partes del importe. En 2025 el reparto se reabre (de nuevo 15 comunidades), pero con Castilla-La Mancha (39&nbsp;%) y Andalucía (23&nbsp;%) consolidadas como líderes. En conjunto, las que más peso ganan son Castilla-La Mancha (+21 puntos) y Andalucía (+14), mientras que Región de Murcia (−13) y Canarias (−12), protagonistas en 2023, casi desaparecen.</p>
<p>Puedes explorar esta distribución en el <strong>mapa por comunidad autónoma</strong> de esta misma página (con el top de municipios de cada una al hacer clic) y filtrar las ayudas por comunidad, provincia y municipio en el buscador.</p>
`);
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoTramos
// Barras verticales: nº de concesiones por tramo de importe.
// ─────────────────────────────────────────────────────────────
/**
 * @param {Array} distribucion - [{ rango: string, cantidad: number }, ...]
 */
function poblarGraficoTramos(distribucion) {
    if (!distribucion.length) return;
    if (tramosPendiente) tramosPendiente.style.display = 'none';
    if (graficoTramos)   graficoTramos.style.display   = 'block';

    const instancia = new Chart(graficoTramos, {
        type: 'bar',
        data: {
            labels: distribucion.map(d => d.rango),
            datasets: [{
                label:           'Nº de concesiones',
                data:            distribucion.map(d => d.cantidad),
                backgroundColor: COLORES.azul,
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
    configurarDescarga(instancia, 'btn-dl-tramos', 'tramos-importe-eell.png');
    configurarModal(instancia, 'Tramos de importe concedido EELL', `
<p>Las EELL manejan importes mucho mayores y más dispersos que las protectoras: van desde poco más de 3.000&nbsp;€ hasta cerca de 100.000&nbsp;€, con una media en torno a los 37.500&nbsp;€. La mayoría de las concesiones se concentra en los tramos intermedios (10.000–50.000&nbsp;€), mientras que los importes muy bajos y los muy altos son minoritarios.</p>
<p>Esa dispersión no responde únicamente al tamaño de los municipios: buena parte de los importes más altos corresponde a municipios pequeños o medianos que se presentan en agrupación para asumir de forma conjunta costes veterinarios, campañas de esterilización o la gestión de colonias felinas.</p>
<p>Aun así, un grupo reducido de entidades concentra una parte muy significativa del importe total concedido, lo que refleja desigualdades territoriales: mientras algunas comunidades y ayuntamientos participan activamente y tienen capacidad para acceder a las ayudas, otros territorios apenas aparecen, ya sea por falta de medios técnicos, escasa prioridad política o dificultades administrativas.</p>
<p><strong>Evolución 2023–2025.</strong> El importe medio por concesión ha crecido de forma sostenida: unos 32.200&nbsp;€ en 2023, 35.200&nbsp;€ en 2024 y 48.800&nbsp;€ en 2025. A la vez baja el número de concesiones (60&nbsp;→&nbsp;55&nbsp;→&nbsp;40): cada año hay menos beneficiarias pero de mayor cuantía. El grueso, que en 2023–2024 estaba en los tramos de 10.000–50.000&nbsp;€, se desplaza en 2025 hacia importes más altos (el tramo de 50.000–75.000&nbsp;€ pasa a ser el más frecuente), en buena parte por el peso creciente de las agrupaciones de municipios, que concentran ayudas más grandes.</p>
<p>El buscador público permite filtrar las ayudas por importe, comunidad, provincia y municipio, y el <strong>mapa por comunidad</strong> de esta página muestra cómo se reparten los fondos por territorio.</p>
`);
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoExclusionesAnio
// Barras: nº de solicitudes EELL excluidas por convocatoria.
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
    configurarDescarga(instancia, 'btn-dl-exclusiones-anio', 'exclusiones-por-anio-eell.png');
    configurarModal(instancia, 'Exclusiones EELL por año', `
<p>Las exclusiones de entidades locales se han disparado: 39 en 2023, 84 en 2024 y 303 en 2025. El salto de 2025 va de la mano del crecimiento de la propia convocatoria (se presentaron muchos más ayuntamientos que nunca), pero también de un control documental más estricto: la resolución de 2025 detalla 41 causas distintas de exclusión, frente a las 18 de 2023.</p>
<p>Conviene leer el dato con perspectiva: quedar excluido no significa no necesitar la ayuda, sino no haber superado los requisitos formales (documentación incompleta, fuera de plazo, sin firmar…). Buena parte de los ayuntamientos excluidos son municipios pequeños con poca capacidad administrativa, lo que apunta a que el procedimiento resulta exigente precisamente para quienes menos medios tienen.</p>
<p>En el buscador de exclusiones (bajo el buscador general) puede consultarse cada entidad excluida con su causa oficial completa.</p>
`);
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarGraficoCausasFrecuentes
// Barras horizontales: top de causas del ÚLTIMO año con exclusiones.
// Solo un año porque cada convocatoria usa su propia numeración de
// causas (el "5" de 2023 no es el "5" de 2025).
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
    configurarDescarga(instancia, 'btn-dl-causas-frecuentes', 'causas-exclusion-eell.png');
    configurarModal(instancia, 'Causas de exclusión más frecuentes (EELL)', `
<p>En 2025 la causa dominante fue el <strong>Programa municipal de gestión ética de colonias felinas</strong>: no presentarlo (88 solicitudes) o tenerlo sin vigencia (79) suma más de la mitad de las exclusiones. Es el requisito estrella de la convocatoria —lo exige la Ley 7/2023 de bienestar animal— y donde más ayuntamientos tropiezan.</p>
<p>El resto del top son defectos documentales: la memoria técnica del Anexo III (68), la acreditación del poder de la persona firmante (65) y el cronograma de actuaciones del Anexo II en sus tres variantes (incorrecto, incompleto o fuera de modelo: 145 en conjunto). Una misma solicitud puede acumular varias causas, por eso la suma supera el total de excluidas.</p>
<p>La gráfica muestra solo la última convocatoria porque cada año usa su propia numeración de causas y no son mezclables entre sí. Pasa el cursor por cada barra para ver el motivo oficial completo, o consulta cualquier entidad concreta en el buscador de exclusiones.</p>
`);
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: poblarRecurrencia
// KPI "entidades que repiten" con asterisco → nota fija bajo los KPIs.
// ─────────────────────────────────────────────────────────────
/**
 * @param {Object} datos - respuesta de /estadisticas/eell:
 *   { entidades_repiten, total_entidades, ... }
 */
function poblarRecurrencia(datos) {
    const repiten = datos.entidades_repiten || 0;
    const total   = datos.total_entidades   || 0;

    // KPI "Entidades que repiten": el número lleva un asterisco (superíndice)
    // que remite a la nota fija bajo los KPIs, con los ayuntamientos concretos.
    if (kpiEellRepiten) {
        kpiEellRepiten.innerHTML = repiten.toLocaleString('es-ES') + '<sup>*</sup>';
    }
    if (kpiEellRepitenTag && total) {
        kpiEellRepitenTag.textContent = `de ${total} beneficiarias`;
    }
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
    cargarEstadisticasEell();
});
