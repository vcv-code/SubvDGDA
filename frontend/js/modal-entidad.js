/**
 * modal-entidad.js — Modal de ficha de entidad
 * ─────────────────────────────────────────────
 * Se invoca desde solicitudes.js cuando el usuario hace clic en una fila.
 * Abre un modal con la ficha resumida de la entidad (nombre, CIF, CCAA,
 * importes totales e histórico de solicitudes) sin navegar fuera del buscador.
 * El pie del modal incluye el enlace "Ver página completa →" que abre
 * entidad.html?cif=... en una pestaña nueva para compartir o guardar la URL.
 *
 * API que expone al resto del código:
 *   abrirModalEntidad(cif, nombre)  → abre el modal y carga los datos
 */

(function () {
    'use strict';

    // ── Constantes ────────────────────────────────────────────────────────────

    const ENDPOINT = '/solicitudes/';

    // ── Referencias al DOM ───────────────────────────────────────────────────

    const backdrop = document.getElementById('modal-entidad');

    if (!backdrop) {
        console.warn('[modal-entidad] No se encontró #modal-entidad en el DOM.');
        return;
    }

    const btnCerrar      = backdrop.querySelector('#modal-cerrar');
    const elNombre       = backdrop.querySelector('#modal-nombre');
    const elCif          = backdrop.querySelector('#modal-cif');
    const elCcaa         = backdrop.querySelector('#modal-ccaa');
    const elTotalImporte = backdrop.querySelector('#modal-total-importe');
    const elTotalSols    = backdrop.querySelector('#modal-total-sols');
    const elEstado       = backdrop.querySelector('#modal-estado');
    const elHistorico    = backdrop.querySelector('#modal-historico');
    const elTablaBody    = backdrop.querySelector('#modal-tabla-body');
    const elEnlacePagina = backdrop.querySelector('#modal-enlace-pagina');

    // ── Helpers ───────────────────────────────────────────────────────────────

    function fmtImporte(valor) {
        if (valor === null || valor === undefined) return '—';
        const [ent, dec] = parseFloat(valor).toFixed(2).split('.');
        return ent.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + dec + ' €';
    }

    function badgeEstado(estado) {
        const mapa = {
            'concedida':       { texto: 'Concedida',       clase: 'badge-concedida' },
            'no_beneficiaria': { texto: 'No beneficiaria', clase: 'badge-no-beneficiaria' },
            'excluida':        { texto: 'Excluida',         clase: 'badge-excluida' },
            'desistida':       { texto: 'Desistida',        clase: 'badge-desistida' },
        };
        const info = mapa[estado] || { texto: estado, clase: '' };
        return `<span class="badge ${info.clase}">${info.texto}</span>`;
    }

    // ── Abrir / Cerrar ────────────────────────────────────────────────────────

    function abrirModal() {
        backdrop.classList.add('modal-abierto');
        backdrop.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        // Foco al botón de cierre para accesibilidad por teclado
        setTimeout(() => btnCerrar && btnCerrar.focus(), 50);
    }

    function cerrarModal() {
        backdrop.classList.remove('modal-abierto');
        backdrop.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        // Devuelve el foco al elemento que abrió el modal
        if (backdrop._openerEl) {
            backdrop._openerEl.focus();
            backdrop._openerEl = null;
        }
    }

    // ── Rellenar datos ────────────────────────────────────────────────────────

    function limpiarModal() {
        if (elNombre)      elNombre.textContent       = '—';
        if (elCif)         elCif.textContent           = '—';
        if (elCcaa) {
            elCcaa.textContent = '—';
            const bloque = elCcaa.closest('.modal-dato');
            if (bloque) bloque.style.display = '';
        }
        if (elTotalImporte) elTotalImporte.textContent = '—';
        if (elTotalSols)   elTotalSols.textContent     = '—';
        if (elEstado) {
            elEstado.className = 'modal-estado';
            elEstado.textContent = 'Cargando datos…';
            elEstado.style.display = '';
        }
        if (elHistorico)   elHistorico.style.display  = 'none';
        if (elTablaBody)   elTablaBody.innerHTML       = '';
    }

    function rellenarModal(solicitudes, cif) {
        if (!solicitudes || solicitudes.length === 0) {
            if (elEstado) {
                elEstado.textContent = 'No se encontraron solicitudes para esta entidad.';
                elEstado.style.display = '';
            }
            return;
        }

        const primera = solicitudes[0];

        // Datos de cabecera
        if (elNombre) elNombre.textContent = primera.beneficiario.nombre || cif;
        if (elCif)    elCif.textContent    = primera.beneficiario.cif   || cif;

        // CCAA — solo disponible en EELL; se oculta si está vacía
        const ccaa = primera.beneficiario.ccaa || primera.ccaa || '—';
        if (elCcaa) {
            elCcaa.textContent = ccaa;
            const bloque = elCcaa.closest('.modal-dato');
            if (bloque) bloque.style.display = ccaa === '—' ? 'none' : '';
        }

        // Totales
        const concedidas = solicitudes.filter(s => s.estado === 'concedida');
        const totalImporte = concedidas.reduce((acc, s) => {
            return acc + (s.importe !== null ? parseFloat(s.importe) : 0);
        }, 0);

        if (elTotalImporte) {
            elTotalImporte.textContent = concedidas.length > 0
                ? fmtImporte(totalImporte)
                : '—';
        }
        if (elTotalSols) {
            elTotalSols.textContent = solicitudes.length;
        }

        // Histórico
        if (elTablaBody) {
            const ordenadas = [...solicitudes].sort((a, b) =>
                b.convocatoria.anio_convocatoria - a.convocatoria.anio_convocatoria
            );
            elTablaBody.innerHTML = ordenadas.map(s => {
                const anio       = s.convocatoria.anio_convocatoria;
                const expediente = s.num_expediente || '—';
                const tipo       = s.convocatoria.tipo_convoc
                    ? s.convocatoria.tipo_convoc.toUpperCase()
                    : '—';
                const importe    = s.estado === 'concedida' ? fmtImporte(s.importe) : '—';
                const tramo      = s.tramo !== null && s.tramo !== undefined
                    ? `<span class="badge-tramo">T${s.tramo}</span>`
                    : '';

                return `<tr>
                    <td style="text-align:center;">${anio}</td>
                    <td class="modal-tabla__expediente">${expediente}</td>
                    <td style="text-align:center;">${tipo}</td>
                    <td>${badgeEstado(s.estado)} ${tramo}</td>
                    <td style="text-align:center; font-variant-numeric:tabular-nums;">${importe}</td>
                </tr>`;
            }).join('');
        }

        // Mostrar histórico, ocultar estado
        if (elEstado)   elEstado.style.display   = 'none';
        if (elHistorico) elHistorico.style.display = '';
    }

    // ── Carga de datos ────────────────────────────────────────────────────────

    async function cargarEntidad(cif) {
        try {
            const resp = await fetch(`${ENDPOINT}?cif=${encodeURIComponent(cif)}`);
            if (!resp.ok) {
                throw new Error(`HTTP ${resp.status}`);
            }
            const data = await resp.json();
            const solicitudes = data.resultados || data;
            rellenarModal(solicitudes, cif);
        } catch (err) {
            console.error('[modal-entidad] Error al cargar entidad:', err);
            if (elEstado) {
                elEstado.className = 'modal-estado modal-estado--error';
                elEstado.textContent = 'No se pudieron cargar los datos. Inténtalo de nuevo.';
                elEstado.style.display = '';
            }
            if (elHistorico) elHistorico.style.display = 'none';
        }
    }

    // ── API pública ───────────────────────────────────────────────────────────

    /**
     * Abre el modal y carga la ficha de la entidad con el CIF indicado.
     * @param {string} cif    — CIF de la entidad
     * @param {string} nombre — Nombre provisional (se muestra mientras carga)
     * @param {Element} [openerEl] — Elemento que abrió el modal (para devolver foco)
     */
    window.abrirModalEntidad = function (cif, nombre, openerEl) {
        if (!cif) return;
        backdrop._openerEl = openerEl || null;
        limpiarModal();
        if (elNombre) elNombre.textContent = nombre || cif;
        if (elCif)    elCif.textContent    = cif;
        if (elEnlacePagina) elEnlacePagina.href = `entidad.html?cif=${encodeURIComponent(cif)}`;
        abrirModal();
        cargarEntidad(cif);
    };

    // ── Eventos de cierre ─────────────────────────────────────────────────────

    // Botón X
    if (btnCerrar) {
        btnCerrar.addEventListener('click', cerrarModal);
    }

    // Clic en el backdrop (fuera de la card)
    backdrop.addEventListener('click', function (e) {
        if (e.target === backdrop) {
            cerrarModal();
        }
    });

    // Tecla ESC
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && backdrop.classList.contains('modal-abierto')) {
            cerrarModal();
        }
    });

    // Trampa de foco dentro del modal
    backdrop.addEventListener('keydown', function (e) {
        if (e.key !== 'Tab') return;
        const focusables = Array.from(
            backdrop.querySelectorAll(
                'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
            )
        ).filter(el => el.offsetParent !== null);

        if (focusables.length === 0) return;
        const first = focusables[0];
        const last  = focusables[focusables.length - 1];

        if (e.shiftKey) {
            if (document.activeElement === first) {
                e.preventDefault();
                last.focus();
            }
        } else {
            if (document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        }
    });

})();
