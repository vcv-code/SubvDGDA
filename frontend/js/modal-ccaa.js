/**
 * modal-ccaa.js — Modal "Top municipios" del mapa CCAA (compartido)
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Se abre al hacer clic en una comunidad del mapa (js/mapa-ccaa.js). Muestra el
 * top 10 de municipios por importe (acumulado y del último año), expandiendo las
 * agrupaciones de ayuntamientos en sus miembros individuales.
 *
 * Usa solo endpoints PÚBLICOS:
 *   GET /solicitudes/?ccaa=…&estado=concedida   y   GET /agrupaciones/{id_solic}
 *
 * Lo comparten exclusivo.html (registrados) y estadisticas-eell.html (público).
 * Expone window.abrirModalCCAA(nombre) — que se pasa a pintarMapaCCAA — y
 * window.cerrarModalCCAA(). El cierre (botón ×, clic fuera, Escape) se auto-
 * conecta al cargar, si la página incluye el markup #modal-ccaa. Va en IIFE
 * para no chocar con las variables globales de la página que lo incluya.
 */
(function () {

    const API_URL = '';

    function fmtEur(v) {
        return Math.round(Number(v)).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' €';
    }

    // Elemento que abrió el modal, para devolverle el foco al cerrar.
    // Se toma de document.activeElement porque el disparador es una región
    // del mapa de Leaflet, no un botón propio al que podamos referirnos.
    let elementoConFocoPrevio = null;

    async function abrirModalCCAA(nombre) {
        const modal = document.getElementById('modal-ccaa');
        if (!modal) return;

        elementoConFocoPrevio = document.activeElement;

        document.getElementById('modal-ccaa-titulo').textContent = 'Top municipios — ' + nombre;
        document.getElementById('modal-lista-acum').innerHTML = '<li style="color:#999;padding:.5rem 0">Cargando...</li>';
        document.getElementById('modal-lista-anio').innerHTML  = '';
        modal.style.display = 'flex';

        // Llevar el foco dentro del diálogo (WCAG 2.4.3). Sin esto, quien usa
        // teclado o lector de pantalla no se entera de que se ha abierto: el
        // foco se queda detrás, sobre el mapa.
        const btnCerrar = modal.querySelector('.modal-ccaa__cerrar');
        if (btnCerrar) setTimeout(() => btnCerrar.focus(), 50);

        try {
            const resp = await fetch(`${API_URL}/solicitudes/?ccaa=${encodeURIComponent(nombre)}&estado=concedida&limite=500`);
            if (!resp.ok) throw new Error();
            const datos = await resp.json();
            const rows  = datos.resultados || [];

            // Expandir agrupaciones: obtener miembros individuales con importe_asignado
            const agrupaciones = rows.filter(r => r.es_agrupacion);
            const miembrosMap  = {};
            if (agrupaciones.length) {
                const detalles = await Promise.all(
                    agrupaciones.map(r => fetch(`${API_URL}/agrupaciones/${r.id_solic}`).then(res => res.ok ? res.json() : null))
                );
                detalles.forEach((det, i) => {
                    if (det && det.miembros) {
                        miembrosMap[agrupaciones[i].id_solic] = {
                            anio:     agrupaciones[i].convocatoria.anio_convocatoria,
                            miembros: det.miembros,
                        };
                    }
                });
            }

            const acum = {}, porAnio = {};
            rows.forEach(function(r) {
                const anio = r.convocatoria.anio_convocatoria;
                if (r.es_agrupacion && miembrosMap[r.id_solic]) {
                    // Distribuir entre municipios miembro
                    miembrosMap[r.id_solic].miembros.forEach(function(m) {
                        const key = m.nombre;
                        const imp = Number(m.importe_asignado) || 0;
                        acum[key] = (acum[key] || 0) + imp;
                        if (!porAnio[anio]) porAnio[anio] = {};
                        porAnio[anio][key] = (porAnio[anio][key] || 0) + imp;
                    });
                } else {
                    const key = r.beneficiario.nombre;
                    const imp = Number(r.importe) || 0;
                    acum[key] = (acum[key] || 0) + imp;
                    if (!porAnio[anio]) porAnio[anio] = {};
                    porAnio[anio][key] = (porAnio[anio][key] || 0) + imp;
                }
            });

            const anios   = rows.map(r => r.convocatoria.anio_convocatoria);
            const minAnio = anios.length ? String(Math.min(...anios)) : '—';
            const maxAnio = anios.length ? String(Math.max(...anios)) : '—';
            document.getElementById('modal-anio-min').textContent = minAnio;
            document.getElementById('modal-anio-max').textContent = maxAnio;
            document.getElementById('modal-anio-ult').textContent = maxAnio;

            function top10html(obj) {
                return Object.entries(obj)
                    .sort((a, b) => b[1] - a[1]).slice(0, 10)
                    .map(([nom, imp], i) => {
                        const n = nom.replace(/^AYUNTAMIENTO\s+(DE\s+|DEL?\s+)?/i, '');
                        return `<li><span class="modal-ccaa__pos">${i+1}</span>` +
                               `<span class="modal-ccaa__nombre">${n}</span>` +
                               `<span class="modal-ccaa__importe">${fmtEur(imp)}</span></li>`;
                    }).join('') || '<li style="color:#999">Sin datos</li>';
            }

            const listaAcum = Object.entries(acum).sort((a,b) => b[1]-a[1]);
            const listaAnio = Object.entries(porAnio[maxAnio] || {}).sort((a,b) => b[1]-a[1]);

            const notaFmt = n => `Top ${Math.min(10, n)} de ${n} municipio${n !== 1 ? 's' : ''}.`;
            document.getElementById('modal-nota-acum').textContent = notaFmt(listaAcum.length);
            document.getElementById('modal-nota-anio').textContent = notaFmt(listaAnio.length);

            document.getElementById('modal-lista-acum').innerHTML = top10html(acum);
            document.getElementById('modal-lista-anio').innerHTML  = top10html(porAnio[maxAnio] || {});

        } catch (e) {
            const err = '<li style="color:#c00">Error al cargar datos</li>';
            document.getElementById('modal-lista-acum').innerHTML = err;
            document.getElementById('modal-lista-anio').innerHTML = err;
        }
    }

    function cerrarModalCCAA() {
        const modal = document.getElementById('modal-ccaa');
        if (modal) modal.style.display = 'none';

        // Devolver el foco a donde estaba antes de abrirlo
        if (elementoConFocoPrevio) {
            elementoConFocoPrevio.focus();
            elementoConFocoPrevio = null;
        }
    }

    window.abrirModalCCAA  = abrirModalCCAA;
    window.cerrarModalCCAA = cerrarModalCCAA;

    // Auto-conexión del cierre (botón ×, clic fuera, Escape)
    document.addEventListener('DOMContentLoaded', () => {
        const btnCerrar = document.querySelector('.modal-ccaa__cerrar');
        if (btnCerrar) btnCerrar.addEventListener('click', cerrarModalCCAA);
        const overlay = document.getElementById('modal-ccaa');
        if (overlay) overlay.addEventListener('click', e => { if (e.target === overlay) cerrarModalCCAA(); });
        document.addEventListener('keydown', e => { if (e.key === 'Escape') cerrarModalCCAA(); });
    });

})();
