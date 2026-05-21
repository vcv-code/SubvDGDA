/**
 * exclusivo.js — Lógica del área de contenido exclusivo (exclusivo.html)
 *
 * Comprueba el token, carga la tabla resumen de solicitudes y gestiona
 * el cierre de sesión. Mismo patrón que privado.js pero sin el formulario
 * de cambio de contraseña.
 *
 * Endpoints:
 *   GET /privado/perfil         → verificar acceso (401 si token inválido)
 *   GET /privado/resumen-tabla  → datos de la tabla por convocatoria
 */

const API_URL = '';


// ─── CONTROL DE ACCESO ────────────────────────────────────────────────────────

function obtenerToken() {
    const token = localStorage.getItem('token');
    if (!token) { window.location.href = 'login.html'; return null; }
    return token;
}

async function intentarRenovarToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return null;
    const r = await fetch(`${API_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!r.ok) { localStorage.removeItem('refresh_token'); return null; }
    const datos = await r.json();
    localStorage.setItem('token', datos.access_token);
    localStorage.setItem('refresh_token', datos.refresh_token);
    return datos.access_token;
}

async function cerrarSesion() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
        fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
        }).catch(() => {});
    }
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    window.location.href = 'login.html';
}


// ─── FETCH AUTENTICADO ────────────────────────────────────────────────────────

async function fetchAutenticado(ruta, token) {
    const respuesta = await fetch(`${API_URL}${ruta}`, {
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    });
    if (respuesta.status === 401) {
        // Token expirado — intentar renovar antes de ir al login
        const nuevoToken = await intentarRenovarToken();
        if (nuevoToken) {
            const reintento = await fetch(`${API_URL}${ruta}`, {
                headers: { 'Authorization': `Bearer ${nuevoToken}`, 'Content-Type': 'application/json' },
            });
            if (reintento.ok) return reintento.json();
        }
        localStorage.removeItem('token');
        sessionStorage.setItem('redirect_post_login', window.location.href);
        window.location.href = 'login.html';
        return null;
    }
    if (!respuesta.ok) throw new Error(`Error ${respuesta.status} en ${ruta}`);
    return respuesta.json();
}


// ─── TABLA RESUMEN ────────────────────────────────────────────────────────────

async function cargarResumenTabla(token) {
    const contenedor = document.getElementById('resumen-tabla-contenedor');
    if (!contenedor) return;

    try {
        const datos = await fetchAutenticado('/privado/resumen-tabla', token);
        if (!datos) return;

        const fmt = (n) => new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n);
        const num = (n) => n.toLocaleString('es-ES');

        const colgroup = `<colgroup>
            <col style="width:10%"><col style="width:7%"><col style="width:9%">
            <col style="width:13%"><col style="width:12%"><col style="width:12%">
            <col style="width:12%"><col style="width:15%">
        </colgroup>`;

        const cabecera = `<tr>
            <th>Tipo</th><th>Año</th><th>Total</th>
            <th class="col-sep">Concedidas</th>
            <th>No benef.</th><th>Excluidas</th><th>Desistidas</th>
            <th class="col-sep">Importe concedido</th>
        </tr>`;

        const renderFila = (f) => {
            if (f.total === 0) {
                return `<tr class="resumen-tabla__pendiente">
                    <td><span class="resumen-tabla__tipo resumen-tabla__tipo--${f.tipo}">${f.tipo.toUpperCase()}</span></td>
                    <td>${f.anio}</td>
                    <td colspan="6" style="text-align:center;">Resolución pendiente de publicación</td>
                </tr>`;
            }
            return `<tr>
                <td><span class="resumen-tabla__tipo resumen-tabla__tipo--${f.tipo}">${f.tipo.toUpperCase()}</span></td>
                <td>${f.anio}</td>
                <td>${num(f.total)}</td>
                <td class="col-sep">${num(f.concedidas)}</td>
                <td>${num(f.no_beneficiarias)}</td>
                <td>${num(f.excluidas)}</td>
                <td>${num(f.desistidas)}</td>
                <td class="col-sep">${fmt(f.importe_total)}</td>
            </tr>`;
        };

        const renderBloque = (tipo, filasTipo) => {
            const cd = filasTipo.filter(f => f.total > 0);
            const s  = (campo) => cd.reduce((a, f) => a + f[campo], 0);
            const subtotal = cd.length ? `
                <tfoot>
                    <tr class="resumen-tabla__subtotal">
                        <td colspan="2">Subtotal ${tipo.toUpperCase()}</td>
                        <td>${num(s('total'))}</td>
                        <td class="col-sep">${num(s('concedidas'))}</td>
                        <td>${num(s('no_beneficiarias'))}</td>
                        <td>${num(s('excluidas'))}</td>
                        <td>${num(s('desistidas'))}</td>
                        <td class="col-sep">${fmt(s('importe_total'))}</td>
                    </tr>
                </tfoot>` : '';
            return `
                <div class="resumen-tabla-card">
                <div class="resumen-bloque tabla-scroll">
                    <table class="resumen-tabla" aria-label="Solicitudes ${tipo.toUpperCase()}" style="table-layout:fixed;">
                        ${colgroup}<thead>${cabecera}</thead>
                        <tbody>${filasTipo.map(renderFila).join('')}</tbody>
                        ${subtotal}
                    </table>
                </div>
                </div>`;
        };

        const filasEpa  = datos.filas.filter(f => f.tipo === 'epa').sort((a, b) => b.anio - a.anio);
        const filasEell = datos.filas.filter(f => f.tipo === 'eell').sort((a, b) => b.anio - a.anio);

        const todosConDatos = datos.filas.filter(f => f.total > 0);
        const totNobenef = todosConDatos.reduce((s, f) => s + f.no_beneficiarias, 0);
        const totExcl    = todosConDatos.reduce((s, f) => s + f.excluidas, 0);
        const totDesist  = todosConDatos.reduce((s, f) => s + f.desistidas, 0);

        contenedor.innerHTML = `
            <div class="resumen-grupos">
                ${renderBloque('epa', filasEpa)}
                ${renderBloque('eell', filasEell)}
                <div class="resumen-tabla-card">
                <div class="resumen-bloque resumen-bloque--total tabla-scroll">
                    <table class="resumen-tabla" aria-label="Total global" style="table-layout:fixed;">
                        ${colgroup}
                        <thead>${cabecera}</thead>
                        <tbody>
                            <tr class="resumen-tabla__totales">
                                <td colspan="2">TOTAL GLOBAL</td>
                                <td>${num(datos.total_global)}</td>
                                <td class="col-sep">${num(datos.concedidas_total)}</td>
                                <td>${num(totNobenef)}</td>
                                <td>${num(totExcl)}</td>
                                <td>${num(totDesist)}</td>
                                <td class="col-sep">${fmt(datos.importe_global)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                </div>
            </div>`;
    } catch {
        if (contenedor) contenedor.innerHTML = '<p class="tabla-error-msg">No se pudo cargar la tabla de resumen.</p>';
    }
}


// ─── MAPA CCAA ────────────────────────────────────────────────────────────────

async function cargarMapaCCAA() {
    try {
        const [respEell, respStats] = await Promise.all([
            fetch(`${API_URL}/estadisticas/eell`),
            fetch(`${API_URL}/estadisticas/`),
        ]);
        if (!respEell.ok) return;
        const datos = await respEell.json();

        // Calcular rango de años EELL dinámicamente
        if (respStats.ok) {
            const stats   = await respStats.json();
            const aniosEell = (stats.por_anio || [])
                .filter(x => x.tipo === 'eell' && x.total > 0)
                .map(x => x.anio);
            if (aniosEell.length) {
                const minA = Math.min(...aniosEell);
                const maxA = Math.max(...aniosEell);
                const subtitulo = document.getElementById('subtitulo-mapa-ccaa');
                if (subtitulo) {
                    subtitulo.textContent = `Importes concedidos por comunidades autónomas (${minA}–${maxA}). Pasa el cursor por las comunidades para ver el importe total y número de concesiones, y haz clic en ellas para ver el top 10 de municipios (salvo que tengan menos).`;
                }
            }
        }

        if (typeof pintarMapaCCAA === 'function') {
            setTimeout(() => pintarMapaCCAA(datos.por_ccaa || [], abrirModalCCAA), 150);
        }
    } catch (e) {
        console.error('cargarMapaCCAA:', e);
    }
}


// ─── MODAL TOP 10 MUNICIPIOS ──────────────────────────────────────────────────

function fmtEur(v) {
    return Math.round(Number(v)).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' €';
}

async function abrirModalCCAA(nombre) {
    const modal = document.getElementById('modal-ccaa');
    if (!modal) return;

    document.getElementById('modal-ccaa-titulo').textContent = 'Top municipios — ' + nombre;
    document.getElementById('modal-lista-acum').innerHTML = '<li style="color:#999;padding:.5rem 0">Cargando...</li>';
    document.getElementById('modal-lista-anio').innerHTML  = '';
    modal.style.display = 'flex';

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

    } catch(e) {
        const err = '<li style="color:#c00">Error al cargar datos</li>';
        document.getElementById('modal-lista-acum').innerHTML = err;
        document.getElementById('modal-lista-anio').innerHTML = err;
    }
}

function cerrarModalCCAA() {
    const modal = document.getElementById('modal-ccaa');
    if (modal) modal.style.display = 'none';
}


// ─── PUNTO DE ENTRADA ─────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    const btnCerrar = document.getElementById('btn-cerrar-sesion');
    if (btnCerrar) btnCerrar.addEventListener('click', cerrarSesion);

    let token = localStorage.getItem('token');
    if (!token) {
        token = await intentarRenovarToken();
        if (!token) {
            sessionStorage.setItem('redirect_post_login', window.location.href);
            window.location.href = 'login.html';
            return;
        }
    }

    const perfil = await fetchAutenticado('/privado/perfil', token);
    if (!perfil) return;

    await cargarResumenTabla(token);
    cargarMapaCCAA();

    const btnCerrarModal = document.querySelector('.modal-ccaa__cerrar');
    if (btnCerrarModal) btnCerrarModal.addEventListener('click', cerrarModalCCAA);
    const modalOverlay = document.getElementById('modal-ccaa');
    if (modalOverlay) modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) cerrarModalCCAA(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') cerrarModalCCAA(); });
});
