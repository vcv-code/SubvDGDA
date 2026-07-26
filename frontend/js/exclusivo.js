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
        // Render compartido con la home (js/resumen-tabla.js)
        window.renderResumenTabla(datos, contenedor);
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


// El modal "Top municipios" (abrirModalCCAA / cerrarModalCCAA) vive en el
// módulo compartido js/modal-ccaa.js — se usa igual desde estadisticas-eell.html.


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

    // Solo admin: el contenido (resumen + mapa) ya es público en el inicio y en
    // estadísticas EELL, así que esta página queda reservada para la usuaria
    // (admin) de cara a futuro contenido exclusivo. Los registrados normales se
    // redirigen a su perfil.
    if (perfil.rol !== 'admin') {
        window.location.href = 'privado.html';
        return;
    }

    await cargarResumenTabla(token);
    cargarMapaCCAA();

    // El cierre del modal CCAA (×, clic fuera, Escape) lo auto-conecta modal-ccaa.js
});
