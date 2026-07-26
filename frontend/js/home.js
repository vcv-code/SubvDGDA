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
    verdeOscuro:    '#1A3429',
    verdeMedio:     '#2DC26C',
    verdeClaro:     '#A5D6A7',
    verdeFondo:     'rgba(26, 52, 41, 0.10)',
    azul:           '#1565C0',
    concedida:      '#2E7D32',
    noBeneficiaria: '#D97706',
    excluida:       '#C62828',
    desistida:      '#6B7280',
    grisTexto:      '#616161',
    grisMedio:      '#E0E0E0',
};

const OPCIONES_BASE = {
    responsive:          true,
    maintainAspectRatio: false,
    devicePixelRatio:    window.devicePixelRatio || 2,
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
        poblarUmbrales(datos.umbrales);

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

    // Badges de tendencia año-sobre-año (no toca el backend)
    mostrarTendencias(datos);
}


// ─────────────────────────────────────────────────────────────
// BADGES DE TENDENCIA AÑO-SOBRE-AÑO (Task 2.3)
// ─────────────────────────────────────────────────────────────

/**
 * mostrarTendencias(datos)
 * Calcula la variación % entre el último año y el penúltimo disponibles
 * en datos.por_anio y actualiza los badges de los KPIs "Registros totales"
 * e "Importe Concedido".
 *
 * No toca el backend: todos los cálculos se hacen sobre los datos que
 * ya devuelve GET /estadisticas/.
 *
 * ¿Por qué solo esos dos KPIs?
 *   · Registros totales → suma d.total de todos los tipos por año.
 *   · Importe Concedido → suma d.importe_total de todos los tipos por año.
 *   · Entidades únicas → es un escalar global (datos.entidades_unicas),
 *     sin desglose anual en el schema; no se puede calcular tendencia.
 *
 * @param {Object} datos - Objeto completo de /estadisticas/
 */
function mostrarTendencias(datos) {
    const porAnio = datos.por_anio || [];
    if (!porAnio.length) return;

    // Obtener años únicos ordenados ascendentemente
    const anios = [...new Set(porAnio.map(d => d.anio))].sort((a, b) => a - b);
    if (anios.length < 2) return;   // Necesitamos al menos 2 años para comparar

    const anioActual   = anios[anios.length - 1];
    const anioAnterior = anios[anios.length - 2];

    // Suma de un campo numérico para todos los tipos de un año dado
    const sumar = (anio, campo) =>
        porAnio
            .filter(d => d.anio === anio)
            .reduce((suma, d) => suma + (d[campo] || 0), 0);

    mostrarTendencia(
        'tendencia-registros',
        sumar(anioActual,   'total'),
        sumar(anioAnterior, 'total'),
        anioAnterior
    );

    mostrarTendencia(
        'tendencia-importe',
        sumar(anioActual,   'importe_total'),
        sumar(anioAnterior, 'importe_total'),
        anioAnterior
    );
}

/**
 * mostrarTendencia(id, actual, anterior, anioAnterior)
 * Rellena un badge <span> con la variación % y aplica la clase
 * de color correcta (verde sube, rojo baja).
 *
 * @param {string} id           - ID del <span> en el HTML.
 * @param {number} actual       - Valor del año más reciente.
 * @param {number} anterior     - Valor del año de comparación.
 * @param {number} anioAnterior - Año de comparación (para el texto del badge).
 */
function mostrarTendencia(id, actual, anterior, anioAnterior) {
    const el = document.getElementById(id);
    if (!el || !anterior) return;

    const pct  = ((actual - anterior) / anterior) * 100;
    const sube = pct >= 0;

    el.className   = `tendencia-badge ${sube ? 'tendencia-badge--sube' : 'tendencia-badge--baja'}`;
    el.textContent = `${sube ? '↑' : '↓'} ${Math.abs(pct).toFixed(1)} % vs ${anioAnterior}`;
    el.style.display = 'inline-flex';
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
    const epaByAnio  = ANIOS.map(anio => porAnio.filter(d => d.anio === anio && d.tipo === 'epa').reduce((s, d) => s + d.importe_total, 0));
    const eellByAnio = ANIOS.map(anio => porAnio.filter(d => d.anio === anio && d.tipo === 'eell').reduce((s, d) => s + d.importe_total, 0));

    const instancia = new Chart(document.getElementById('home-grafico-linea'), {
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
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const lines = [' Total: ' + formatearMillones(ctx.raw)];
                            if (epaByAnio[ctx.dataIndex]  > 0) lines.push('  EPA:  ' + formatearMillones(epaByAnio[ctx.dataIndex]));
                            if (eellByAnio[ctx.dataIndex] > 0) lines.push('  EELL: ' + formatearMillones(eellByAnio[ctx.dataIndex]));
                            return lines;
                        },
                    },
                },
            },
        },
    });
    configurarDescarga(instancia, 'btn-dl-linea', 'evolucion-importe.png');
    configurarModal(instancia, 'Evolución del importe por año', `
<p>4 millones para protección animal en toda España (2 millones para protectoras y 2 millones para administraciones), pueden parecer mucho… hasta que los comparas.</p>
<p>El gasto público estatal supera actualmente los 200.000 millones de euros anuales. Eso significa que esta partida representa aprox. un 0,0019&nbsp;% del gasto: unos 0,08&nbsp;€ por habitante al año.</p>
<p>Solo la Comunidad de Madrid ha destinado 7,2 millones de dinero público a tauromaquia en 2026. En 2025 aprobó además 1,7 millones para la «Fiesta del Toro». Un tribunal anuló posteriormente un convenio previo de 1,4 millones al considerarlo una subvención concedida «a dedo».</p>
<p>4 millones es:</p>
<ul>
<li>menos que el caché anual de algunos futbolistas de primera,</li>
<li>menos que muchas campañas institucionales de publicidad,</li>
<li>menos que el coste de algunas rotondas o reformas urbanas concretas,</li>
<li>menos que el presupuesto anual de fiestas de bastantes ciudades medianas,</li>
<li>menos que algunos rescates a empresas privadas o sobrecostes públicos aislados.</li>
</ul>
<p>Mientras tanto, protectoras saturadas, colonias felinas sin recursos y miles de animales abandonados dependen de donaciones y de voluntariado agotado física, psicológica y económicamente.</p>
<p>Es positivo que exista financiación estatal. Pero sigue siendo insuficiente para un problema estructural que afecta al bienestar animal, la salud pública y la convivencia.</p>
<p>Invertir en protección animal no es gasto simbólico: es prevención social, sanitaria y administrativa.</p>
<p class="modal-grafica__fuentes"><strong>Fuentes:</strong> <a href="https://www.lamoncloa.gob.es/consejodeministros/resumenes/paginas/2025/181125-rueda-de-prensa-ministros.aspx" target="_blank" rel="noopener noreferrer">Consejo de Ministros (nov. 2025)</a> · <a href="https://www.animanaturalis.org/n/47065/andalucia-aumenta-al-80-las-subvenciones-publicas-a-municipios-taurinos-y-el-dinero-publico-a-la-tauromaquia-bate-records-en-toda-espana" target="_blank" rel="noopener noreferrer">Animanaturalis: subvenciones a tauromaquia</a> · <a href="https://www.comunidad.madrid/noticias/2025/03/26/comunidad-madrid-aprueba-17-millones-euros-fiesta-toro-2025" target="_blank" rel="noopener noreferrer">Comunidad de Madrid: 1,7&nbsp;M€ Fiesta del Toro (2025)</a></p>
`);
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

    const instancia = new Chart(document.getElementById('home-grafico-donut'), {
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
    configurarDescarga(instancia, 'btn-dl-donut', 'distribucion-estados.png');
    configurarModal(instancia, 'Distribución por estado', `
<p>Algo más del 40&nbsp;% de las solicitudes terminan concedidas. Sin embargo, un porcentaje muy similar corresponde a entidades «No beneficiarias»: protectoras y ayuntamientos que cumplen los requisitos y obtienen puntuación válida, pero quedan fuera únicamente por falta de presupuesto.</p>
<p>Esto refleja que la demanda real de recursos para protección animal es estructuralmente muy superior a los fondos disponibles cada año.</p>
<p>La gráfica también muestra otro problema importante: una parte de las solicitudes queda excluida o desistida por cuestiones burocráticas, documentación o plazos. Muchas protectoras y pequeños ayuntamientos funcionan con voluntariado, escasos recursos administrativos y una carga de trabajo enorme, por lo que afrontar procedimientos complejos y cambiantes resulta especialmente difícil.</p>
<p>Aunque desde la administración se ofrecen charlas y apoyo técnico —algo positivo y necesario—, los requisitos y criterios suelen modificarse con frecuencia y no siempre simplifican el proceso.</p>
<p>En la práctica, la protección animal sigue dependiendo en gran medida del esfuerzo económico y humano de asociaciones, ayuntamientos y voluntariado que sostienen servicios de interés público con recursos muy limitados.</p>
`);
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

    const instancia = new Chart(document.getElementById('home-grafico-barras'), {
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
    configurarDescarga(instancia, 'btn-dl-barras', 'epa-vs-eell.png');
    configurarModal(instancia, 'EPA vs EELL por año (M€)', `
<p>La evolución del presupuesto muestra un avance importante respecto a 2021: las ayudas casi se cuadruplicaron hasta alcanzar cerca de 4 millones de euros anuales desde 2023.</p>
<p>Sin embargo, también se observa que el crecimiento se ha estancado. Desde entonces, la financiación permanece prácticamente congelada pese al aumento de solicitudes, las nuevas obligaciones legales y la creciente presión sobre protectoras y ayuntamientos.</p>
<p>Las protectoras continúan sosteniendo una parte esencial del sistema mediante rescates, acogidas, atención veterinaria y trabajo voluntario. Al mismo tiempo, muchas administraciones pequeñas y medianas se encuentran sobrepasadas por el volumen de trabajo y las exigencias burocráticas asociadas a la nueva normativa estatal.</p>
<p>No obstante, parte del problema no parece deberse únicamente a falta de medios. En muchos casos también existe escasa implicación institucional y poco interés real en aplicar las obligaciones de bienestar animal vigentes desde hace más de 3 años y medio, lo que provoca grandes diferencias entre territorios: mientras algunos ayuntamientos intentan adaptarse, otros continúan incumpliendo o retrasando medidas básicas sin apenas consecuencias ni mecanismos efectivos de control.</p>
<p>En cualquier caso, el principal problema de estas subvenciones sigue siendo su escasa magnitud. Aunque el presupuesto actual supone un avance, continúa siendo insuficiente para cubrir de forma estructural las necesidades existentes de protección animal en todo el territorio.</p>
`);
}


// ─────────────────────────────────────────────────────────────
// KPI: TASA DE ÉXITO GLOBAL
// Datos: GET /estadisticas/ → total_concedidas / total_registros
// ─────────────────────────────────────────────────────────────

function mostrarTasaExito(datos) {
    const elExito   = document.getElementById('home-tasa-exito');
    const elFracaso = document.getElementById('home-tasa-fracaso');
    if (!elExito) return;
    if (datos.total_registros > 0) {
        const pct = Math.round((datos.total_concedidas / datos.total_registros) * 100);
        elExito.textContent   = pct + ' %';
        if (elFracaso) elFracaso.textContent = (100 - pct) + ' %';
    } else {
        elExito.textContent = '—';
        if (elFracaso) elFracaso.textContent = '—';
    }
}


// ─────────────────────────────────────────────────────────────
// UMBRAL DE PUNTUACIÓN (corte de concesión por año)
// Datos: GET /estadisticas/ → datos.umbrales
// ─────────────────────────────────────────────────────────────

const _ORDEN_LINEA    = ['colonias_felinas', 'animales_abandonados'];
const _ETIQUETA_LINEA = { colonias_felinas: 'Colonias', animales_abandonados: 'Abandonados' };

/** Formatea una puntuación: entero sin decimales, coma decimal, sin ceros sobrantes. */
function formatearUmbral(n) {
    const txt = Number.isInteger(n) ? String(n) : n.toFixed(2).replace(/0+$/, '');
    return txt.replace('.', ',');
}

/** Construye el contenido de una celda (EPA o EELL) para un año. */
function celdaUmbral(item) {
    if (!item) return '—';
    if (!item.hubo_corte) return '<span class="umbral-sin-corte">Sin corte</span>';

    if (item.por_linea && item.por_linea.length) {
        const iguales = item.por_linea.every(v => v.umbral === item.por_linea[0].umbral);
        if (iguales) {
            return `${formatearUmbral(item.por_linea[0].umbral)} <span class="umbral-detalle">(ambas líneas)</span>`;
        }
        return [...item.por_linea]
            .sort((a, b) => _ORDEN_LINEA.indexOf(a.linea) - _ORDEN_LINEA.indexOf(b.linea))
            .map(v => `${_ETIQUETA_LINEA[v.linea]} ${formatearUmbral(v.umbral)}`)
            .join(' · ');
    }
    return formatearUmbral(item.umbral);
}

/** Rellena la tabla de umbrales en horizontal: una fila por tipo de entidad
 *  (EPA / EELL) y una columna por año (más recientes a la izquierda). */
function poblarUmbrales(umbrales) {
    const thead = document.getElementById('umbral-thead');
    const tbody = document.getElementById('umbral-tbody');
    if (!tbody || !umbrales || !umbrales.length) return;

    // Años como columnas, más recientes a la izquierda
    const anios = [...new Set(umbrales.map(u => u.anio))].sort((a, b) => b - a);
    const porClave = {};
    umbrales.forEach(u => { porClave[`${u.tipo}-${u.anio}`] = u; });

    if (thead) {
        thead.innerHTML = `<tr>
            <th scope="col">Tipo de entidad</th>
            ${anios.map(a => `<th scope="col">${a}</th>`).join('')}
        </tr>`;
    }

    const fila = (tipo, etiqueta) => `
        <tr>
            <th scope="row">${etiqueta}</th>
            ${anios.map(a => `<td>${celdaUmbral(porClave[`${tipo}-${a}`])}</td>`).join('')}
        </tr>`;

    tbody.innerHTML = fila('epa', 'EPA (protectoras)')
                    + fila('eell', 'EELL (entidades locales)');

    const seccion = document.getElementById('seccion-umbral');
    if (seccion) seccion.style.display = '';
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
        // Etiqueta del estado del plazo de solicitud (lo calcula el backend en estado_plazo).
        const etiquetasPlazo = { abierto: ' (plazo abierto)', cerrado: ' (plazo cerrado)', sin_fecha: '' };

        contenedor.innerHTML = avisos.map(aviso => {
            const tipo  = etiquetas[aviso.tipo_convoc] || aviso.tipo_convoc.toUpperCase();
            const plazo = etiquetasPlazo[aviso.estado_plazo] ?? '';
            const fecha = aviso.fecha_convocatoria
                ? new Date(aviso.fecha_convocatoria).toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })
                : 'fecha pendiente';
            return `
                <div class="aviso-banner">
                    <span class="aviso-banner__icono" aria-hidden="true">📢</span>
                    <div class="aviso-banner__texto">
                        <strong>Convocatoria ${aviso.anio_convocatoria}${plazo} — ${tipo}</strong>
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
        // Si la fecha es del mismo año que la fila, se omite el año (redundante con
        // la columna Año). Se conserva si difiere (p. ej. resolución en enero del año siguiente).
        const fmtFecha = (iso, anioFila) => {
            if (!iso) return '—';
            const [y, m, d] = iso.split('-');
            const base = `${parseInt(d)} ${meses[parseInt(m) - 1]}`;
            return (anioFila && parseInt(y) === anioFila) ? base : `${base} ${y}`;
        };

        // URLs del BOE de las resoluciones (no las da la API; se mantienen aquí).
        const RESOL_BOE = {
            'epa-2025':  'https://www.boe.es/buscar/doc.php?id=BOE-A-2025-27109',
            'epa-2024':  'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-23749',
            'epa-2023':  'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2023-23529',
            'epa-2022':  'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2022-22122',
            'epa-2021':  'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2022-602',
            'eell-2025': 'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-27204',
            'eell-2024': 'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-24205',
            'eell-2023': 'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-662',
        };
        const BDNS_CONVOC = 'https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/';

        // Una fila por convocatoria con todo: la fecha de convocatoria enlaza a la
        // ficha BDNS (PDFs + BOE), la de resolución al BOE, y el botón "Ver solicitudes"
        // (búsqueda filtrada) solo aparece cuando ya hay resolución (antes no hay datos).
        const renderFila = (lista) =>
            [...lista]
                .sort((a, b) => b.anio_convocatoria - a.anio_convocatoria)
                .map(c => {
                    const asterisco = c.periodo_meses === 6 ? '&nbsp;*' : '';

                    const convocTxt  = fmtFecha(c.fecha_convocatoria, c.anio_convocatoria);
                    const convocCell = c.num_convoc
                        ? `<a href="${BDNS_CONVOC}${c.num_convoc}" target="_blank" rel="noopener noreferrer" title="Ver la convocatoria ${c.anio_convocatoria} en BDNS (se abre en una pestaña nueva)">${convocTxt}</a>`
                        : convocTxt;

                    let resolCell, accesoCell;
                    if (c.fecha_resolucion === null) {
                        resolCell  = '<span class="convoc-pendiente">Pendiente</span>';
                        accesoCell = '<span class="convoc-pendiente">—</span>';
                    } else {
                        const boe = RESOL_BOE[`${c.tipo_convoc}-${c.anio_convocatoria}`];
                        const resolTxt = fmtFecha(c.fecha_resolucion, c.anio_convocatoria);
                        resolCell = boe
                            ? `<a href="${boe}" target="_blank" rel="noopener noreferrer" title="Resolución ${c.anio_convocatoria} en el BOE (se abre en una pestaña nueva)">${resolTxt}</a>`
                            : resolTxt;
                        accesoCell = `<a href="buscador.html?tipo=${c.tipo_convoc}&anio=${c.anio_convocatoria}" class="btn btn-secundario btn--sm" title="Ver las solicitudes y concesiones de esta convocatoria">Ver →</a>`;
                    }

                    return `<tr>
                        <td>${c.anio_convocatoria}${asterisco}</td>
                        <td>${convocCell}</td>
                        <td>${resolCell}</td>
                        <td>${accesoCell}</td>
                    </tr>`;
                }).join('');

        const tbodyEell = document.getElementById('convocatorias-eell');
        const tbodyEpa  = document.getElementById('convocatorias-epa');
        if (tbodyEell) tbodyEell.innerHTML = renderFila(porTipo.eell);
        if (tbodyEpa)  tbodyEpa.innerHTML  = renderFila(porTipo.epa);

        const haySeisMeses = convocatorias.some(c => c.periodo_meses === 6);
        const notaEl = document.getElementById('convocatorias-nota');
        if (notaEl) notaEl.style.display = haySeisMeses ? '' : 'none';

        bloque.style.display = '';
        const seccion = document.getElementById('seccion-convocatorias');
        if (seccion) seccion.style.display = '';

    } catch (_) {
        // Si falla, el bloque permanece oculto
    }
}


// ─────────────────────────────────────────────────────────────
// RESUMEN POR CONVOCATORIA (tabla al final, banda crema)
// Endpoint público propio; render compartido con exclusivo.html
// (js/resumen-tabla.js → window.renderResumenTabla).
// ─────────────────────────────────────────────────────────────
async function cargarResumenTabla() {
    const contenedor = document.getElementById('resumen-tabla-contenedor');
    if (!contenedor) return;
    try {
        const respuesta = await fetch(`${API_URL}/estadisticas/resumen-convocatorias`);
        if (!respuesta.ok) throw new Error(`Error ${respuesta.status}`);
        const datos = await respuesta.json();
        window.renderResumenTabla(datos, contenedor);
    } catch (error) {
        console.error('Error al cargar el resumen por convocatoria:', error);
        contenedor.innerHTML = '<p class="tabla-error-msg">No se pudo cargar el resumen por convocatoria.</p>';
    }
}


document.addEventListener('DOMContentLoaded', () => {
    cargarDatos();
    cargarAvisos();
    cargarConvocatorias();
    cargarResumenTabla();
});
