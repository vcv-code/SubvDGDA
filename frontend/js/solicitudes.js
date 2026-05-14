/**
 * solicitudes.js — Lógica del buscador de solicitudes
 * ─────────────────────────────────────────────────────
 * Este archivo gestiona toda la interacción de solicitudes.html.
 *
 * RESPONSABILIDADES:
 *   1. Leer los valores del panel de filtros.
 *   2. Construir la URL con los parámetros correctos.
 *   3. Llamar al endpoint GET /solicitudes/ con fetch().
 *   4. Pintar los resultados en la tabla.
 *   5. Gestionar la paginación (botones Anterior / Siguiente).
 *   6. Mostrar / ocultar filtros condicionales (CCAA, Provincia, Línea).
 *   7. Enviar búsqueda por nombre al backend mediante el parámetro ?buscar=
 *      (filtrado server-side; el backend ignora stopwords comunes).
 *
 * ENDPOINT PRINCIPAL:
 *   GET /solicitudes/?anio=&tipo=&estado=&limite=&pagina=
 *
 * ESTRUCTURA DE CADA SOLICITUD (SolicitudOut del backend):
 *   {
 *     id_solic:       number,
 *     num_expediente: string | null,
 *     puntuacion:     number | null,
 *     estado:         "concedida" | "no_beneficiaria" | "excluida" | "desistida",
 *     convocatoria: {
 *       id_convoc, titulo_convoc, tipo_convoc,
 *       anio_convocatoria, periodo_meses,
 *       fecha_convocatoria, fecha_resolucion
 *     },
 *     beneficiario: {
 *       id_benef, nombre, cif, tipo_benef
 *     },
 *     importe:        number | null,  (null si la solicitud no fue concedida)
 *     es_agrupacion:  boolean          // true si pertenece a una agrupación EELL
 *   }
 */


// ─────────────────────────────────────────────────────────────
// CONFIGURACIÓN
// ─────────────────────────────────────────────────────────────

const API_URL   = '';
const LIMITE    = 50;   // Resultados por página. 50 es un buen equilibrio entre velocidad y usabilidad.

// ─────────────────────────────────────────────────────────────
// ESTADO GLOBAL DE LA PÁGINA
// ─────────────────────────────────────────────────────────────
/**
 * Usamos un objeto "estado" para guardar la página actual y los
 * filtros activos. Así, los botones de paginación pueden saber
 * en qué página están sin tener que leer el DOM.
 *
 * ¿Por qué un objeto y no variables sueltas?
 * Agrupar el estado en un objeto facilita su lectura y depuración
 * desde la consola del navegador (F12 → Console → estado).
 */
const estado = {
    paginaActual: 1,
    totalResultados: 0,
};

// Último array de solicitudes recibidas de la API.
// Se guarda para poder re-ordenar sin hacer una nueva petición.
let ultimasSolicitudes = [];


// ─────────────────────────────────────────────────────────────
// REFERENCIAS A ELEMENTOS DEL DOM
// ─────────────────────────────────────────────────────────────
/**
 * Guardamos las referencias en constantes para no tener que
 * llamar a document.getElementById() cada vez que las necesitemos.
 * Es más eficiente y el código queda más limpio.
 */
const formFiltros    = document.getElementById('form-filtros');
const btnBuscar      = document.getElementById('btn-buscar');
const btnLimpiar     = document.getElementById('btn-limpiar');
const btnAnterior    = document.getElementById('btn-anterior');
const btnSiguiente   = document.getElementById('btn-siguiente');

const filtraNombre   = document.getElementById('filtro-nombre');
const filtroAnio     = document.getElementById('filtro-anio');
const filtroTipo     = document.getElementById('filtro-tipo');
const filtroEstado   = document.getElementById('filtro-estado');
const filtroCcaa     = document.getElementById('filtro-ccaa');
const filtroLinea    = document.getElementById('filtro-linea');

const grupoCcaa      = document.getElementById('grupo-ccaa');
const grupoProvicia  = document.getElementById('grupo-provincia');
const grupoLinea     = document.getElementById('grupo-linea');

const tablaCarga     = document.getElementById('tabla-carga');
const tablaError     = document.getElementById('tabla-error');
const tablaWrapper   = document.getElementById('tabla-wrapper');
const tablaVacia     = document.getElementById('tabla-vacia');
const tablaBody      = document.getElementById('tabla-body');

const paginacion     = document.getElementById('paginacion');
const paginaInfo     = document.getElementById('pagina-info');
const infoResultados = document.getElementById('info-resultados');
const tablaControles = document.getElementById('tabla-controles');
const ordenSelect    = document.getElementById('orden-select');
const btnDescargarCsv = document.getElementById('btn-descargar-csv');


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: leerFiltros
// Lee los valores actuales del formulario y los devuelve
// como un objeto limpio.
// ─────────────────────────────────────────────────────────────
function leerFiltros() {
    return {
        nombre:   filtraNombre.value.trim().toLowerCase(),
        anio:     filtroAnio.value,
        tipo:     filtroTipo.value,
        estado:   filtroEstado.value,
        ccaa:       filtroCcaa.value,
        provincia:  document.getElementById('filtro-provincia').value,
        linea:      filtroLinea.value,
    };
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: construirUrl
// Recibe los filtros y la página y devuelve la URL completa
// para llamar al endpoint.
// ─────────────────────────────────────────────────────────────
/**
 * URLSearchParams: clase nativa de JS para construir cadenas de
 * parámetros query de forma segura (escapa caracteres especiales).
 * Es más robusto que concatenar strings a mano.
 *
 * Ejemplo de resultado:
 *   /solicitudes/?tipo=epa&estado=concedida&limite=50&pagina=2
 */
function construirUrl(filtros, pagina) {
    const params = new URLSearchParams();

    // Solo añadimos el parámetro si tiene valor (no está vacío)
    if (filtros.anio)   params.set('anio',   filtros.anio);
    if (filtros.tipo)   params.set('tipo',   filtros.tipo);
    if (filtros.estado) params.set('estado', filtros.estado);
    // búsqueda por nombre (server-side) - modificación
    if (filtros.nombre) params.set('buscar', filtros.nombre);
    // NUEVO
    if (filtros.ccaa)      params.set('ccaa', filtros.ccaa);
    if (filtros.provincia) params.set('provincia', filtros.provincia);
    if (filtros.linea)     params.set('linea', filtros.linea);

    // Paginación: siempre se envían
    params.set('limite', LIMITE);
    params.set('pagina', pagina);

    return `${API_URL}/solicitudes/?${params.toString()}`;
}


// ─────────────────────────────────────────────────────────────
// PERSISTENCIA DE FILTROS EN LA URL
// Permite que al volver con el botón Atrás los filtros se
// restauren automáticamente sin perder la búsqueda anterior.
// ─────────────────────────────────────────────────────────────
function sincronizarUrl(filtros, pagina) {
    const params = new URLSearchParams();
    if (filtros.nombre)    params.set('nombre',    filtros.nombre);
    if (filtros.anio)      params.set('anio',      filtros.anio);
    if (filtros.tipo)      params.set('tipo',      filtros.tipo);
    if (filtros.estado)    params.set('estado',    filtros.estado);
    if (filtros.ccaa)      params.set('ccaa',      filtros.ccaa);
    if (filtros.provincia) params.set('provincia', filtros.provincia);
    if (filtros.linea)     params.set('linea',     filtros.linea);
    if (pagina > 1)        params.set('pagina',    pagina);
    const qs = params.toString();
    history.pushState({}, '', qs ? `?${qs}` : window.location.pathname);
}

function cargarFiltrosDesdeUrl() {
    const params = new URLSearchParams(window.location.search);
    if (!params.toString()) return 0;
    if (params.get('nombre'))    filtraNombre.value    = params.get('nombre');
    if (params.get('anio'))      filtroAnio.value      = params.get('anio');
    if (params.get('tipo'))      filtroTipo.value      = params.get('tipo');
    if (params.get('estado'))    filtroEstado.value    = params.get('estado');
    if (params.get('ccaa'))      filtroCcaa.value      = params.get('ccaa');
    if (params.get('provincia'))
        document.getElementById('filtro-provincia').value = params.get('provincia');
    if (params.get('linea'))     filtroLinea.value     = params.get('linea');
    actualizarFiltrosCondicionales();
    return parseInt(params.get('pagina')) || 1;
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN PRINCIPAL: buscarSolicitudes
// Orquesta la búsqueda completa: lee filtros → llama a la API
// → actualiza la tabla y la paginación.
// ─────────────────────────────────────────────────────────────
async function buscarSolicitudes(pagina = 1) {
    const filtros = leerFiltros();
    estado.paginaActual = pagina;
    sincronizarUrl(filtros, pagina);

    // Mostramos el estado de carga y ocultamos el resto
    mostrarEstadoCarga();
    document.getElementById('spinner').style.display = 'block';

    try {
        // ── Construir URL y hacer fetch ───────────────────────────────
        const url = construirUrl(filtros, pagina);
        const respuesta = await fetch(url);

        if (!respuesta.ok) {
            // Intentamos leer el JSON de error estructurado del backend
            let cuerpo = {};
            try { cuerpo = await respuesta.json(); } catch (_) {}
            const errorBox      = document.getElementById('error-box');
            const errorMensaje  = document.getElementById('error-mensaje');
            const errorSugerencia = document.getElementById('error-sugerencia');
            if (errorBox) {
                errorMensaje.textContent    = cuerpo.mensaje    || `Error ${respuesta.status}`;
                errorSugerencia.textContent = cuerpo.sugerencia || '';
                ocultarTodosEstados();
                errorBox.style.display = 'block';
            }
            throw new Error(`Error del servidor: ${respuesta.status}`);
        }

        // ── Parsear JSON ──────────────────────────────────────────────
        const { total, resultados: solicitudes } = await respuesta.json();
        estado.totalResultados = total;

        // ── Pintar resultados ─────────────────────────────────────────
        if (solicitudes.length === 0) {
            mostrarSinResultados();
        } else {
            pintarTabla(solicitudes);
            actualizarPaginacion(pagina);
            actualizarInfoResultados(solicitudes.length, pagina);
        }

    } catch (error) {
        console.error('Error al buscar solicitudes:', error);
        mostrarError('No se pudo conectar con el servidor. Comprueba que el backend está activo.');
    } finally {
        document.getElementById('spinner').style.display = 'none';
    }
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: ordenarSolicitudes
// Ordena el array según el select de orden antes de pintarlo.
// ─────────────────────────────────────────────────────────────
function ordenarSolicitudes(solicitudes) {
    const criterio = ordenSelect ? ordenSelect.value : '';

    // Clonamos para no mutar el array original recibido de la API
    const copia = [...solicitudes];

    switch (criterio) {
        case 'importe-desc':
            return copia.sort((a, b) => (b.importe ?? -1) - (a.importe ?? -1));
        case 'importe-asc':
            return copia.sort((a, b) => (a.importe ?? Infinity) - (b.importe ?? Infinity));
        case 'entidad-az':
            return copia.sort((a, b) =>
                (a.beneficiario.nombre || '').localeCompare(b.beneficiario.nombre || '', 'es'));
        default:
            // Por defecto: orden alfabético A→Z
            return copia.sort((a, b) =>
                (a.beneficiario.nombre || '').localeCompare(b.beneficiario.nombre || '', 'es'));
    }
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: pintarTabla
// Borra las filas anteriores y pinta las nuevas.
// ─────────────────────────────────────────────────────────────
function pintarTabla(solicitudes) {
    // Guardamos la referencia para poder re-ordenar sin nueva petición
    ultimasSolicitudes = solicitudes;

    // Aplicamos el orden seleccionado antes de pintar
    const ordenadas = ordenarSolicitudes(solicitudes);

    // Limpiamos el <tbody> antes de añadir nuevas filas
    tablaBody.innerHTML = '';

    // Por cada solicitud creamos una <tr> y la añadimos al <tbody>
    ordenadas.forEach(s => {
        const fila = crearFila(s);
        tablaBody.appendChild(fila);
    });

    // Mostramos la tabla, controles y paginación
    ocultarTodosEstados();
    tablaWrapper.style.display   = '';
    paginacion.style.display     = '';
    if (tablaControles) tablaControles.style.display = '';
    if (infoResultados && infoResultados.textContent) infoResultados.style.display = '';

    // Leyenda de tramos: solo si algún resultado tiene tramo
    const leyenda = document.getElementById('leyenda-tramos');
    if (leyenda) {
        leyenda.style.display = ordenadas.some(s => s.tramo !== null && s.tramo !== undefined)
            ? '' : 'none';
    }
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: crearFila
// Recibe una solicitud y devuelve un elemento <tr> listo para
// insertar en la tabla.
// ─────────────────────────────────────────────────────────────
function crearFila(s) {
    const tr = document.createElement('tr');

    // El cursor pointer indica que la fila es clickable
    tr.style.cursor = 'pointer';

    /**
     * Al hacer clic navegamos a entidad.html pasando el CIF en la URL.
     * entidad.html lo leerá con URLSearchParams para mostrar el historial.
     */
    tr.addEventListener('click', () => {
        const cif = s.beneficiario.cif || '';
        if (cif) {
            window.location.href = `entidad.html?cif=${encodeURIComponent(cif)}`;
        }
    });

    // ── Valores de cada celda (5 columnas según wireframe) ─────────
    const nombre      = s.beneficiario.nombre || '—';
    const anio        = s.convocatoria.anio_convocatoria;
    const tipo        = s.convocatoria.tipo_convoc.toUpperCase(); // "epa" → "EPA"
    const badgeEstado = crearBadge(s.estado);

    // Importe: null si la solicitud no fue concedida
    const importe = s.importe !== null
    ? new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 })
        .format(parseFloat(s.importe)) + ' €'
    : '—';

    // ── Construir HTML de la fila ──────────────────────────────────
    // data-label: atributo leído por el CSS en móvil (<600px)
    // para mostrar el nombre de columna como prefijo en la tarjeta.
    tr.innerHTML = `
        <td data-label="Entidad"></td>
        <td data-label="Año">${anio}</td>
        <td data-label="Tipo">${tipo}</td>
        <td data-label="Estado"></td>
        <td data-label="Importe">${importe}</td>
    `;

    // Celda 0: nombre de la entidad + badges si aplican
    const tdNombre = tr.cells[0];
    tdNombre.appendChild(document.createTextNode(nombre));
    if (s.es_agrupacion === true) {
        const badgeAgrupacion = document.createElement('span');
        badgeAgrupacion.className   = 'badge-agrupacion';
        badgeAgrupacion.textContent = 'Agrupación';
        tdNombre.appendChild(badgeAgrupacion);
    }
    if (s.tramo !== null && s.tramo !== undefined) {
        const badgeTramo = document.createElement('span');
        badgeTramo.className   = 'badge-tramo';
        badgeTramo.textContent = `T${s.tramo}`;
        tdNombre.appendChild(badgeTramo);
    }

    // Badge de estado: se inserta en la celda vacía (índice 3)
    // usando appendChild() para no mezclar HTML con innerHTML
    tr.cells[3].appendChild(badgeEstado);

    return tr;
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: crearBadge
// Devuelve un <span> con la clase CSS correcta según el estado.
// ─────────────────────────────────────────────────────────────
/**
 * Los badges de estado están definidos en styles.css:
 *   .badge-concedida       → verde
 *   .badge-no-beneficiaria → rojo
 *   .badge-excluida        → naranja
 *   .badge-desistida       → morado
 */
function crearBadge(estado) {
    const span = document.createElement('span');
    span.classList.add('badge');

    // Mapeamos el valor de la API al texto y clase CSS correspondiente
    const mapaEstados = {
        'concedida':       { texto: 'Concedida',       clase: 'badge-concedida' },
        'no_beneficiaria': { texto: 'No beneficiaria', clase: 'badge-no-beneficiaria' },
        'excluida':        { texto: 'Excluida',         clase: 'badge-excluida' },
        'desistida':       { texto: 'Desistida',        clase: 'badge-desistida' },
    };

    const info = mapaEstados[estado] || { texto: estado, clase: '' };
    span.classList.add(info.clase);
    span.textContent = info.texto;

    return span;
}


// ─────────────────────────────────────────────────────────────
// FILTROS CONDICIONALES
// Muestra u oculta filtros según los valores de Tipo y Año.
// ─────────────────────────────────────────────────────────────
/**
 * actualizarFiltrosCondicionales()
 * Se llama cada vez que el usuario cambia el select de Tipo o Año.
 *
 * Reglas:
 *   · Si Tipo = "eell" → mostrar CCAA y Provincia
 *   · Si Tipo ≠ "eell" → ocultar CCAA y Provincia
 *   · Si Tipo = "epa" Y Año = "2025" → mostrar Línea
 *   · En cualquier otro caso → ocultar Línea
 */
function actualizarFiltrosCondicionales() {
    const tipo = filtroTipo.value;

    const esEell    = tipo === 'eell';
    const esEpa     = tipo === 'epa';
    const todosTipos = tipo === '';

    // Años disponibles según tipo
    const aniosEell = ['2023', '2024', '2025'];
    const aniosEpa  = ['2021', '2022', '2023', '2024', '2025'];
    const aniosPermitidos = esEell ? aniosEell : aniosEpa;

    // Actualizar visibilidad de cada <option> del selector de año
    Array.from(filtroAnio.options).forEach(opt => {
        if (opt.value === '') return; // "Todos" siempre visible
        opt.hidden = esEell && !aniosEell.includes(opt.value);
    });

    // Si el año seleccionado ya no está permitido, resetearlo
    if (filtroAnio.value && !todosTipos && !aniosPermitidos.includes(filtroAnio.value)) {
        filtroAnio.value = '';
    }

    const esEpa2025 = esEpa && filtroAnio.value === '2025';

    // CCAA y Provincia: visibles solo para EELL
    grupoCcaa.style.display     = esEell ? '' : 'none';
    grupoProvicia.style.display = esEell ? '' : 'none';

    // Línea de actuación: visible solo para EPA 2025
    grupoLinea.style.display    = esEpa2025 ? '' : 'none';

    if (!esEell) {
        filtroCcaa.value = '';
        document.getElementById('filtro-provincia').value = '';
    }
    if (!esEpa2025) {
        filtroLinea.value = '';
    }
}


// ─────────────────────────────────────────────────────────────
// PAGINACIÓN
// ─────────────────────────────────────────────────────────────
function actualizarPaginacion(pagina) {
    const totalPaginas = Math.ceil(estado.totalResultados / LIMITE);
    paginaInfo.textContent = `Página ${pagina} de ${totalPaginas}`;
    btnAnterior.disabled  = pagina === 1;
    btnSiguiente.disabled = pagina >= totalPaginas;
}

function actualizarInfoResultados(cantidad, pagina) {
    if (!infoResultados) return;
    const inicio = (pagina - 1) * LIMITE + 1;
    const fin    = inicio + cantidad - 1;
    infoResultados.style.display = '';
    infoResultados.textContent =
        `${estado.totalResultados} resultados · Mostrando del ${inicio} al ${fin}`;
}


// ─────────────────────────────────────────────────────────────
// GESTIÓN DE ESTADOS VISUALES (carga, error, sin resultados)
// ─────────────────────────────────────────────────────────────
function ocultarTodosEstados() {
    tablaCarga.style.display   = 'none';
    tablaError.style.display   = 'none';
    tablaVacia.style.display   = 'none';
    tablaWrapper.style.display = 'none';
    paginacion.style.display   = 'none';
    if (tablaControles)  tablaControles.style.display  = 'none';
    if (infoResultados)  infoResultados.style.display  = 'none';
}

function mostrarEstadoCarga() {
    ocultarTodosEstados();
    tablaCarga.style.display = '';
    tablaCarga.textContent   = 'Buscando…';
}

function mostrarSinResultados() {
    ocultarTodosEstados();
    tablaVacia.style.display = '';
}

function mostrarError(mensaje) {
    ocultarTodosEstados();
    tablaError.style.display = '';
    tablaError.textContent   = mensaje;
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: descargarCSV
// Redirige al endpoint de exportación del backend con los
// filtros activos. El backend genera y sirve el archivo CSV.
// ─────────────────────────────────────────────────────────────
/**
 * Construye la URL de /solicitudes/export con los mismos filtros
 * que la búsqueda activa, excluyendo pagina y orden (el backend
 * exporta todos los resultados que coinciden con los filtros).
 *
 * Filtros incluidos: buscar, tipo, ccaa, anio, estado.
 * Filtros excluidos: pagina, limite, orden.
 *
 * La descarga se dispara con window.location.href, lo que hace
 * que el navegador reciba el fichero CSV directamente del servidor.
 */
function descargarCSV() {
    const filtros = leerFiltros();
    const params  = new URLSearchParams();

    if (filtros.nombre)    params.set('buscar',    filtros.nombre);
    if (filtros.tipo)      params.set('tipo',      filtros.tipo);
    if (filtros.anio)      params.set('anio',      filtros.anio);
    if (filtros.estado)    params.set('estado',    filtros.estado);
    if (filtros.ccaa)      params.set('ccaa',      filtros.ccaa);
    if (filtros.provincia) params.set('provincia', filtros.provincia);
    if (filtros.linea)     params.set('linea',     filtros.linea);

    const url = `${API_URL}/solicitudes/export?${params.toString()}`;
    window.location.href = url;
}


// ─────────────────────────────────────────────────────────────
// LIMPIAR FILTROS
// Resetea el formulario y vuelve al estado inicial.
// ─────────────────────────────────────────────────────────────
function limpiarFiltros() {
    // form.reset() devuelve todos los <input> y <select> a su valor inicial
    formFiltros.reset();

    // Actualizamos los filtros condicionales (que quedan ocultos)
    actualizarFiltrosCondicionales();

    // Volvemos al estado inicial de la tabla
    ocultarTodosEstados();
    tablaCarga.style.display = '';
    tablaCarga.textContent   = 'Usa los filtros y pulsa "Buscar" para ver resultados.';

    // Reseteamos la paginación y la URL
    estado.paginaActual = 1;
    history.pushState({}, '', window.location.pathname);
}


// ─────────────────────────────────────────────────────────────
// EVENTOS
// Conectamos las funciones con las acciones del usuario.
// ─────────────────────────────────────────────────────────────

// Buscar al enviar el formulario (botón Buscar o pulsar Enter)
formFiltros.addEventListener('submit', () => {
    estado.paginaActual = 1; // Resetear a página 1 en cada nueva búsqueda
    buscarSolicitudes(1);
});

// Limpiar filtros
btnLimpiar.addEventListener('click', limpiarFiltros);

// Paginación: página anterior
btnAnterior.addEventListener('click', () => {
    if (estado.paginaActual > 1) {
        buscarSolicitudes(estado.paginaActual - 1);
        // Hacemos scroll suave hacia arriba para que el usuario
        // vea la nueva tabla desde el principio
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
});

// Paginación: página siguiente
btnSiguiente.addEventListener('click', () => {
    if (estado.paginaActual < Math.ceil(estado.totalResultados / LIMITE)) {
        buscarSolicitudes(estado.paginaActual + 1);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
});

/**
 * Filtros condicionales: se actualizan cada vez que cambia
 * el select de Tipo o el select de Año.
 * El evento "change" se dispara cuando el valor del <select>
 * cambia (el usuario elige una opción diferente).
 */
filtroTipo.addEventListener('change', actualizarFiltrosCondicionales);
filtroAnio.addEventListener('change', actualizarFiltrosCondicionales);

/**
 * Orden: cuando cambia el select de orden, re-pintamos la tabla
 * con los mismos resultados ya descargados (sin nueva petición).
 * Para ello guardamos el último array de solicitudes en una variable
 * de módulo que pintarTabla() actualiza.
 */
if (ordenSelect) {
    ordenSelect.addEventListener('change', () => {
        if (ultimasSolicitudes.length > 0) {
            pintarTabla(ultimasSolicitudes);
        }
    });
}

// Descargar CSV: redirige al endpoint de exportación del backend
if (btnDescargarCsv) {
    btnDescargarCsv.addEventListener('click', descargarCSV);
}


// ─────────────────────────────────────────────────────────────
// INICIALIZACIÓN: restaurar filtros desde la URL al cargar
// ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const pagina = cargarFiltrosDesdeUrl();
    if (pagina) buscarSolicitudes(pagina);
});

// Botón Atrás / Adelante del navegador: restaurar filtros
window.addEventListener('popstate', () => {
    const pagina = cargarFiltrosDesdeUrl();
    if (pagina) {
        buscarSolicitudes(pagina);
    } else {
        limpiarFiltros();
    }
});
