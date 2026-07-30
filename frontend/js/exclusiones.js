/**
 * exclusiones.js — Buscador de exclusiones EELL (sección de buscador.html)
 * ════════════════════════════════════════════════════════════════════════
 *
 * Segundo buscador de la página, debajo del buscador general de solicitudes.
 * Solo muestra ENTIDADES LOCALES con estado "excluida" y su causa oficial.
 *
 * ¿Por qué solo EELL?
 *   Es donde la causa aporta más análisis (426 exclusiones con CCAA
 *   derivable del CIF). Los datos EPA siguen en la BD y en la API
 *   (GET /solicitudes/?estado=excluida&tipo=epa) por si se quieren
 *   mostrar más adelante.
 *
 * Convivencia con solicitudes.js en la misma página:
 *   · Todo va envuelto en una IIFE para no chocar con las variables
 *     globales del buscador principal (estado, LIMITE, formFiltros...).
 *   · Todos los IDs del DOM llevan el prefijo "exc-".
 *   · No sincroniza filtros con la URL (eso lo hace el buscador principal;
 *     dos buscadores escribiendo en la misma query se pisarían).
 *
 * Flujo de datos:
 *   Al cargar → GET /solicitudes/causas (leyenda código → motivo, caché 24 h)
 *   Buscar    → GET /solicitudes/?estado=excluida&tipo=eell&...
 *   Clic en el chip de causa → modal con el motivo completo de cada código
 *     (el nº de expediente se muestra ahí, no en la tabla).
 */
(function () {

    const API_URL = '';
    const LIMITE  = 20;   // Más corto que el buscador general: la columna causa pide una tabla ligera.
    const TIPO    = 'eell';

    const estado = {
        paginaActual:    1,
        totalResultados: 0,
    };

    // Leyenda código → { motivo, articulo } por tipo y año (GET /solicitudes/causas)
    let leyenda = {};


    // ─────────────────────────────────────────────────────────
    // REFERENCIAS AL DOM (todas con prefijo exc-)
    // ─────────────────────────────────────────────────────────
    const seccion       = document.getElementById('exclusiones');
    if (!seccion) return;   // la página no incluye la sección → no hacer nada

    const formFiltros   = document.getElementById('exc-form-filtros');
    const btnLimpiar    = document.getElementById('exc-btn-limpiar');
    const btnPrimera    = document.getElementById('exc-btn-primera');
    const btnAnterior   = document.getElementById('exc-btn-anterior');
    const btnSiguiente  = document.getElementById('exc-btn-siguiente');
    const btnUltima     = document.getElementById('exc-btn-ultima');

    const filtroNombre  = document.getElementById('exc-filtro-nombre');
    const filtroAnio    = document.getElementById('exc-filtro-anio');
    const filtroCcaa    = document.getElementById('exc-filtro-ccaa');
    const filtroCausa   = document.getElementById('exc-filtro-causa');

    const spinner       = document.getElementById('exc-spinner');
    const tablaCarga    = document.getElementById('exc-tabla-carga');
    const tablaError    = document.getElementById('exc-tabla-error');
    const tablaWrapper  = document.getElementById('exc-tabla-wrapper');
    const tablaVacia    = document.getElementById('exc-tabla-vacia');
    const tablaBody     = document.getElementById('exc-tabla-body');

    const paginacion     = document.getElementById('exc-paginacion');
    const paginaInfo     = document.getElementById('exc-pagina-info');
    const infoResultados = document.getElementById('exc-info-resultados');
    const tablaControles = document.getElementById('exc-tabla-controles');
    const resultadosCard = document.getElementById('exc-resultados-card');
    const btnDescargarCsv = document.getElementById('exc-btn-descargar-csv');

    // Modal de causas (IDs únicos en la página, sin prefijo)
    const modalCausas       = document.getElementById('modal-causas');
    const modalCausasTitulo = document.getElementById('modal-causas-titulo');
    const modalCausasConvoc = document.getElementById('modal-causas-convocatoria');
    const modalCausasLista  = document.getElementById('modal-causas-lista');
    const modalCausasCerrar = document.getElementById('modal-causas-cerrar');


    // ─────────────────────────────────────────────────────────
    // LEYENDA DE CAUSAS
    // ─────────────────────────────────────────────────────────
    async function cargarLeyenda() {
        try {
            const resp = await fetch(`${API_URL}/solicitudes/causas`);
            if (resp.ok) {
                leyenda = await resp.json();
            }
        } catch {
            // Sin leyenda, la sección sigue funcionando: se ven los códigos
            // tal cual y el modal avisa de que no hay detalle.
            leyenda = {};
        }
        actualizarFiltroCausa();
    }

    function motivoDe(anio, codigo) {
        return leyenda?.[TIPO]?.[String(anio)]?.[codigo]?.motivo ?? null;
    }

    /**
     * Rellena el desplegable de causa con la leyenda del año elegido.
     * Cada convocatoria usa su propia numeración, así que sin año
     * concreto el desplegable queda deshabilitado.
     */
    function actualizarFiltroCausa() {
        const causas = leyenda?.[TIPO]?.[filtroAnio.value];

        const seleccionPrevia = filtroCausa.value;
        filtroCausa.innerHTML = '';

        if (!causas) {
            filtroCausa.disabled = true;
            const opt = document.createElement('option');
            opt.value = '';
            // "concreto" no sobra: el desplegable de arriba permite "Todos",
            // así que sin esa palabra quien lo tiene puesto cree que ya ha
            // elegido y el mensaje parece un error.
            opt.textContent = 'Elige antes un año concreto';
            filtroCausa.appendChild(opt);
            return;
        }

        filtroCausa.disabled = false;
        const optTodas = document.createElement('option');
        optTodas.value = '';
        optTodas.textContent = 'Todas';
        filtroCausa.appendChild(optTodas);

        for (const [codigo, info] of Object.entries(causas)) {
            const opt = document.createElement('option');
            opt.value = codigo;
            // Código + motivo recortado, para que el desplegable sea legible
            const motivo = info.motivo.length > 70
                ? info.motivo.slice(0, 67) + '…'
                : info.motivo;
            opt.textContent = `${codigo} — ${motivo}`;
            filtroCausa.appendChild(opt);
        }

        if (seleccionPrevia && causas[seleccionPrevia]) {
            filtroCausa.value = seleccionPrevia;
        }
    }


    // ─────────────────────────────────────────────────────────
    // BÚSQUEDA
    // ─────────────────────────────────────────────────────────
    function leerFiltros() {
        return {
            nombre: filtroNombre.value.trim(),
            anio:   filtroAnio.value,
            ccaa:   filtroCcaa.value,
            causa:  filtroCausa.disabled ? '' : filtroCausa.value,
        };
    }

    function construirUrl(filtros, pagina) {
        const params = new URLSearchParams();
        params.set('estado', 'excluida');   // FIJO: esta sección solo lista excluidas
        params.set('tipo',   TIPO);         // FIJO: solo entidades locales
        if (filtros.nombre) params.set('buscar', filtros.nombre);
        if (filtros.anio)   params.set('anio',   filtros.anio);
        if (filtros.ccaa)   params.set('ccaa',   filtros.ccaa);
        if (filtros.causa)  params.set('causa',  filtros.causa);
        params.set('limite', LIMITE);
        params.set('pagina', pagina);
        return `${API_URL}/solicitudes/?${params.toString()}`;
    }

    async function buscarExclusiones(pagina = 1) {
        const filtros = leerFiltros();
        estado.paginaActual = pagina;

        mostrarEstadoCarga();
        spinner.style.display = 'block';

        try {
            const respuesta = await fetch(construirUrl(filtros, pagina));
            if (!respuesta.ok) {
                throw new Error(`Error del servidor: ${respuesta.status}`);
            }

            const { total, resultados } = await respuesta.json();
            estado.totalResultados = total;

            if (resultados.length === 0) {
                mostrarSinResultados();
            } else {
                pintarTabla(resultados);
                actualizarPaginacion(pagina);
                actualizarInfoResultados(resultados.length, pagina);
            }

        } catch (error) {
            console.error('Error al buscar exclusiones:', error);
            mostrarError('No se pudo conectar con el servidor. Comprueba que el backend está activo.');
        } finally {
            spinner.style.display = 'none';
        }
    }


    // ─────────────────────────────────────────────────────────
    // PINTADO DE LA TABLA
    // Columnas: Entidad | Año | CCAA | Causa
    // (el expediente solo se muestra en el modal, la tabla queda más limpia)
    // ─────────────────────────────────────────────────────────
    function pintarTabla(solicitudes) {
        tablaBody.innerHTML = '';
        solicitudes.forEach(s => tablaBody.appendChild(crearFila(s)));

        ocultarTodosEstados();
        tablaWrapper.style.display = '';
        paginacion.style.display   = '';
        if (tablaControles) tablaControles.style.display = '';
        if (resultadosCard) resultadosCard.style.display = '';
        if (infoResultados && infoResultados.textContent) infoResultados.style.display = '';
    }

    function crearFila(s) {
        const tr = document.createElement('tr');

        // dataset.label: en móvil (<600px) el CSS convierte cada fila en una
        // tarjeta y pinta este texto como etiqueta a la izquierda del valor
        // (regla `.tabla-wrapper table tbody td::before`). Sin él los valores
        // quedan solos contra el margen derecho, sin decir qué son. Deben
        // coincidir con las cabeceras <th> de la tabla.
        const tdEntidad = document.createElement('td');
        tdEntidad.dataset.label = 'Entidad';
        tdEntidad.textContent = s.beneficiario.nombre;

        const tdAnio = document.createElement('td');
        tdAnio.dataset.label = 'Año';
        tdAnio.textContent = s.convocatoria.anio_convocatoria;

        const tdCcaa = document.createElement('td');
        tdCcaa.dataset.label = 'CCAA';
        tdCcaa.textContent = s.ccaa || '—';

        // Celda de causa: botón con los códigos que abre el modal con los
        // motivos completos. Botón (no texto) por accesibilidad de teclado.
        const tdCausa = document.createElement('td');
        tdCausa.dataset.label = 'Causa';
        if (s.causa_exclusion) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'chip-causa';
            btn.textContent = s.causa_exclusion.split(';').join(' · ');
            btn.title = 'Ver el motivo completo de cada causa';
            btn.setAttribute('aria-label',
                `Ver causas de exclusión de ${s.beneficiario.nombre}`);
            btn.addEventListener('click', () => abrirModalCausas(s));
            tdCausa.appendChild(btn);
        } else {
            tdCausa.textContent = '—';
        }

        tr.append(tdEntidad, tdAnio, tdCcaa, tdCausa);
        return tr;
    }


    // ─────────────────────────────────────────────────────────
    // MODAL DE CAUSAS
    // Mismo patrón que el modal de entidad: clase .modal-abierto
    // sobre el backdrop, cierre con ×, con Escape o clic fuera.
    // ─────────────────────────────────────────────────────────
    let elementoConFocoPrevio = null;

    function abrirModalCausas(s) {
        const anio = s.convocatoria.anio_convocatoria;

        modalCausasTitulo.textContent = s.beneficiario.nombre;
        // El expediente se muestra aquí (se quitó de la tabla para aligerarla)
        modalCausasConvoc.textContent =
            `EELL ${anio}` + (s.num_expediente ? ` · ${s.num_expediente}` : '');

        modalCausasLista.innerHTML = '';
        (s.causa_exclusion || '').split(';').forEach(codigo => {
            if (!codigo) return;
            const li = document.createElement('li');

            const spanCodigo = document.createElement('span');
            spanCodigo.className = 'modal-causas-lista__codigo';
            spanCodigo.textContent = codigo;

            const spanMotivo = document.createElement('span');
            spanMotivo.textContent = motivoDe(anio, codigo)
                ?? 'Motivo no disponible (no se pudo cargar la leyenda).';

            li.append(spanCodigo, spanMotivo);
            modalCausasLista.appendChild(li);
        });

        elementoConFocoPrevio = document.activeElement;
        modalCausas.classList.add('modal-abierto');
        modalCausas.setAttribute('aria-hidden', 'false');
        modalCausasCerrar.focus();
    }

    function cerrarModalCausas() {
        modalCausas.classList.remove('modal-abierto');
        modalCausas.setAttribute('aria-hidden', 'true');
        // Devolver el foco al botón que abrió el modal (WCAG 2.4.3)
        if (elementoConFocoPrevio) elementoConFocoPrevio.focus();
    }

    modalCausasCerrar.addEventListener('click', cerrarModalCausas);

    modalCausas.addEventListener('click', (e) => {
        if (e.target === modalCausas) cerrarModalCausas();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modalCausas.classList.contains('modal-abierto')) {
            cerrarModalCausas();
        }
    });


    // ─────────────────────────────────────────────────────────
    // PAGINACIÓN E INFO (mismo patrón que solicitudes.js)
    // ─────────────────────────────────────────────────────────
    function actualizarPaginacion(pagina) {
        const totalPaginas = Math.ceil(estado.totalResultados / LIMITE);
        paginaInfo.textContent = `Página ${pagina} de ${totalPaginas}`;
        btnAnterior.disabled  = pagina === 1;
        btnSiguiente.disabled = pagina >= totalPaginas;
        btnPrimera.hidden = pagina === 1;
        btnUltima.hidden  = pagina >= totalPaginas;
    }

    function actualizarInfoResultados(cantidad, pagina) {
        if (!infoResultados) return;
        const inicio = (pagina - 1) * LIMITE + 1;
        const fin    = inicio + cantidad - 1;
        infoResultados.style.display = '';
        infoResultados.textContent =
            `${estado.totalResultados} exclusiones · Mostrando de la ${inicio} a la ${fin}`;
    }

    /** Scroll al inicio de la sección de exclusiones (no de la página,
     *  que dejaría al usuario en el buscador general). */
    function scrollASeccion() {
        seccion.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }


    // ─────────────────────────────────────────────────────────
    // ESTADOS VISUALES
    // ─────────────────────────────────────────────────────────
    function ocultarTodosEstados() {
        tablaCarga.style.display   = 'none';
        tablaError.style.display   = 'none';
        tablaVacia.style.display   = 'none';
        tablaWrapper.style.display = 'none';
        paginacion.style.display   = 'none';
        if (tablaControles) tablaControles.style.display = 'none';
        if (resultadosCard) resultadosCard.style.display = 'none';
        if (infoResultados) infoResultados.style.display = 'none';
    }

    function mostrarEstadoCarga() {
        ocultarTodosEstados();
        tablaCarga.style.display = '';
        tablaCarga.textContent   = 'Buscando…';
    }

    function mostrarSinResultados() {
        ocultarTodosEstados();
        if (resultadosCard) resultadosCard.style.display = '';
        tablaVacia.style.display = '';
    }

    function mostrarError(mensaje) {
        ocultarTodosEstados();
        tablaError.style.display = '';
        tablaError.textContent   = mensaje;
    }


    // ─────────────────────────────────────────────────────────
    // DESCARGA CSV (los mismos filtros, sin paginar)
    // ─────────────────────────────────────────────────────────
    function _slugify(texto) {
        return texto
            .toLowerCase()
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .replace(/\s+/g, '_')
            .replace(/[^a-z0-9_]/g, '');
    }

    function _nombreCSV(filtros) {
        const partes = ['exclusiones_eell'];
        if (filtros.anio)  partes.push(filtros.anio);
        if (filtros.causa) partes.push('causa_' + _slugify(filtros.causa));
        if (filtros.ccaa)  partes.push(_slugify(filtros.ccaa));
        return partes.join('_') + '.csv';
    }

    async function descargarCSV() {
        const filtros = leerFiltros();
        const params  = new URLSearchParams();
        params.set('estado', 'excluida');
        params.set('tipo',   TIPO);
        if (filtros.nombre) params.set('buscar', filtros.nombre);
        if (filtros.anio)   params.set('anio',   filtros.anio);
        if (filtros.ccaa)   params.set('ccaa',   filtros.ccaa);
        if (filtros.causa)  params.set('causa',  filtros.causa);

        try {
            const resp = await fetch(`${API_URL}/solicitudes/export?${params.toString()}`);
            if (!resp.ok) {
                const cuerpo = await resp.json().catch(() => ({}));
                mostrarError(cuerpo.mensaje ?? 'No se pudo generar el CSV.');
                return;
            }
            const blob   = await resp.blob();
            const enlace = document.createElement('a');
            enlace.href     = URL.createObjectURL(blob);
            enlace.download = _nombreCSV(filtros);
            enlace.click();
            URL.revokeObjectURL(enlace.href);
        } catch {
            mostrarError('No se pudo conectar con el servidor. Comprueba que el backend está activo.');
        }
    }


    // ─────────────────────────────────────────────────────────
    // LIMPIAR FILTROS
    // ─────────────────────────────────────────────────────────
    function limpiarFiltros() {
        formFiltros.reset();
        actualizarFiltroCausa();

        ocultarTodosEstados();
        tablaCarga.style.display = '';
        tablaCarga.textContent   = 'Usa los filtros y pulsa "Buscar" para ver las entidades locales excluidas.';

        estado.paginaActual = 1;
    }


    // ─────────────────────────────────────────────────────────
    // EVENTOS
    // ─────────────────────────────────────────────────────────
    formFiltros.addEventListener('submit', () => {
        estado.paginaActual = 1;
        buscarExclusiones(1);
    });

    btnLimpiar.addEventListener('click', limpiarFiltros);

    const btnLimpiarVacio = document.getElementById('exc-btn-limpiar-vacio');
    if (btnLimpiarVacio) {
        btnLimpiarVacio.addEventListener('click', limpiarFiltros);
    }

    filtroAnio.addEventListener('change', actualizarFiltroCausa);

    btnAnterior.addEventListener('click', () => {
        if (estado.paginaActual > 1) {
            buscarExclusiones(estado.paginaActual - 1);
            scrollASeccion();
        }
    });

    btnSiguiente.addEventListener('click', () => {
        if (estado.paginaActual < Math.ceil(estado.totalResultados / LIMITE)) {
            buscarExclusiones(estado.paginaActual + 1);
            scrollASeccion();
        }
    });

    btnPrimera.addEventListener('click', () => {
        if (estado.paginaActual !== 1) {
            buscarExclusiones(1);
            scrollASeccion();
        }
    });

    btnUltima.addEventListener('click', () => {
        const totalPaginas = Math.ceil(estado.totalResultados / LIMITE);
        if (estado.paginaActual < totalPaginas) {
            buscarExclusiones(totalPaginas);
            scrollASeccion();
        }
    });

    btnDescargarCsv.addEventListener('click', descargarCSV);


    // ─────────────────────────────────────────────────────────
    // ARRANQUE: solo se descarga la leyenda (búsqueda bajo demanda)
    // ─────────────────────────────────────────────────────────
    cargarLeyenda();

})();
