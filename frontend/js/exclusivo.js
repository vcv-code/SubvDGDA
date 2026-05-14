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

        const filasConDatos  = datos.filas.filter(f => f.total > 0);
        const totNobenef     = filasConDatos.reduce((s, f) => s + f.no_beneficiarias, 0);
        const totExcl        = filasConDatos.reduce((s, f) => s + f.excluidas, 0);
        const totDesist      = filasConDatos.reduce((s, f) => s + f.desistidas, 0);

        const filas = datos.filas.map(f => {
            if (f.total === 0) {
                return `<tr class="resumen-tabla__pendiente">
                    <td><span class="resumen-tabla__tipo resumen-tabla__tipo--${f.tipo}">${f.tipo.toUpperCase()}</span></td>
                    <td>${f.anio}</td>
                    <td colspan="6">Resolución pendiente de publicación</td>
                </tr>`;
            }
            return `<tr>
                <td><span class="resumen-tabla__tipo resumen-tabla__tipo--${f.tipo}">${f.tipo.toUpperCase()}</span></td>
                <td>${f.anio}</td>
                <td>${num(f.total)}</td>
                <td>${num(f.concedidas)}</td>
                <td>${num(f.no_beneficiarias)}</td>
                <td>${num(f.excluidas)}</td>
                <td>${num(f.desistidas)}</td>
                <td>${fmt(f.importe_total)}</td>
            </tr>`;
        }).join('');

        contenedor.innerHTML = `
            <div class="tabla-scroll">
                <table class="resumen-tabla" aria-label="Resumen de solicitudes por convocatoria">
                    <thead>
                        <tr>
                            <th>Tipo</th><th>Año</th><th>Total</th><th>Concedidas</th>
                            <th>No benef.</th><th>Excluidas</th><th>Desistidas</th><th>Importe concedido</th>
                        </tr>
                    </thead>
                    <tbody>${filas}</tbody>
                    <tfoot>
                        <tr class="resumen-tabla__totales">
                            <td colspan="2">TOTAL</td>
                            <td>${num(datos.total_global)}</td>
                            <td>${num(datos.concedidas_total)}</td>
                            <td>${num(totNobenef)}</td>
                            <td>${num(totExcl)}</td>
                            <td>${num(totDesist)}</td>
                            <td>${fmt(datos.importe_global)}</td>
                        </tr>
                    </tfoot>
                </table>
            </div>`;
    } catch {
        if (contenedor) contenedor.innerHTML = '<p class="tabla-error-msg">No se pudo cargar la tabla de resumen.</p>';
    }
}


// ─── PUNTO DE ENTRADA ─────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    const btnCerrar = document.getElementById('btn-cerrar-sesion');
    if (btnCerrar) btnCerrar.addEventListener('click', cerrarSesion);

    // Mismo patrón que privado.js: intentar renovar ANTES de hacer peticiones
    let token = localStorage.getItem('token');
    if (!token) {
        token = await intentarRenovarToken();
        if (!token) {
            sessionStorage.setItem('redirect_post_login', window.location.href);
            window.location.href = 'login.html';
            return;
        }
    }

    // Verificar que el token es válido (también redirige si está expirado)
    const perfil = await fetchAutenticado('/privado/perfil', token);
    if (!perfil) return;

    // Cargar la tabla en paralelo (no bloquea si falla)
    cargarResumenTabla(token);
});
