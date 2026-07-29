/**
 * admin.js — Panel de administración
 *
 * Flujo de carga:
 *   1. Verifica token + rol admin; redirige si no procede.
 *   2. Carga en paralelo: estado, usuarios, avisos, logs.
 *   3. Conecta eventos: cambio de rol, activar/desactivar, logs, cerrar sesión.
 */

'use strict';

const API_URL = '';

// ── Utilidades ────────────────────────────────────────────────────────────────

function token() {
    return localStorage.getItem('token');
}

function authHeaders() {
    return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token()}` };
}

function mostrarToast(mensaje) {
    const toast = document.getElementById('admin-toast');
    toast.textContent = mensaje;
    toast.classList.add('visible');
    setTimeout(() => toast.classList.remove('visible'), 2500);
}

function mostrarAlerta(mensaje) {
    const alerta = document.getElementById('admin-alerta');
    alerta.textContent = mensaje;
    alerta.classList.add('visible');
}

function formatearFecha(isoStr) {
    if (!isoStr) return '—';
    const d = new Date(isoStr);
    return d.toLocaleDateString('es-ES', { year: 'numeric', month: '2-digit', day: '2-digit' });
}


// ── Verificación de acceso ────────────────────────────────────────────────────

async function intentarRenovarToken() {
    const rt = localStorage.getItem('refresh_token');
    if (!rt) return null;
    try {
        const r = await fetch(`${API_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: rt }),
        });
        if (!r.ok) { localStorage.removeItem('refresh_token'); return null; }
        const d = await r.json();
        localStorage.setItem('token', d.access_token);
        localStorage.setItem('refresh_token', d.refresh_token);
        return d.access_token;
    } catch { return null; }
}

async function verificarAcceso() {
    let t = token();
    if (!t) {
        t = await intentarRenovarToken();
        if (!t) {
            sessionStorage.setItem('redirect_post_login', window.location.href);
            window.location.href = 'login.html';
            return false;
        }
    }

    try {
        const r = await fetch(`${API_URL}/privado/perfil`, {
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${t}` },
        });
        if (r.status === 401) {
            // Token expirado — intentar renovar y reintentar una sola vez
            const nuevoToken = await intentarRenovarToken();
            if (!nuevoToken) {
                localStorage.removeItem('token');
                localStorage.removeItem('refresh_token');
                sessionStorage.setItem('redirect_post_login', window.location.href);
                window.location.href = 'login.html';
                return false;
            }
            const r2 = await fetch(`${API_URL}/privado/perfil`, {
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${nuevoToken}` },
            });
            if (!r2.ok) {
                localStorage.removeItem('token');
                localStorage.removeItem('refresh_token');
                sessionStorage.setItem('redirect_post_login', window.location.href);
                window.location.href = 'login.html';
                return false;
            }
            const p2 = await r2.json();
            if (p2.rol !== 'admin') { window.location.href = 'privado.html'; return false; }
            document.getElementById('admin-meta').textContent = `Sesión: ${p2.email}`;
            return true;
        }
        const perfil = await r.json();
        if (perfil.rol !== 'admin') {
            window.location.href = 'privado.html';
            return false;
        }
        document.getElementById('admin-meta').textContent =
            `Sesión: ${perfil.email}`;
        return true;
    } catch {
        mostrarAlerta('No se puede conectar con el servidor.');
        return false;
    }
}


// ── 1. Estado general ─────────────────────────────────────────────────────────

async function cargarEstado() {
    try {
        const r = await fetch(`${API_URL}/admin/estado`, { headers: authHeaders() });
        if (!r.ok) { document.getElementById('stat-health').textContent = '✗ Error'; return; }
        const d = await r.json();

        document.getElementById('stat-health').textContent        = d.health === 'ok' ? '✓ OK' : '✗';
        document.getElementById('stat-convocatorias').textContent = d.total_convocatorias;
        document.getElementById('stat-solicitudes').textContent   = d.total_solicitudes;
        document.getElementById('stat-usuarios').textContent      = d.total_usuarios;

    } catch {
        document.getElementById('stat-health').textContent = '✗ Error';
    }
}


// ── 2. Usuarios ───────────────────────────────────────────────────────────────

let miId = null;  // id del admin en sesión, para proteger autoedición
let usuariosPagina = 1;             // página actual de la tabla de usuarios
const USUARIOS_LIMITE = 20;         // usuarios por página

async function cargarUsuarios() {
    const contenedor = document.getElementById('admin-usuarios-contenido');
    try {
        const [rPerfil, rUsuarios] = await Promise.all([
            fetch(`${API_URL}/privado/perfil`, { headers: authHeaders() }),
            fetch(`${API_URL}/admin/usuarios?pagina=${usuariosPagina}&limite=${USUARIOS_LIMITE}`, { headers: authHeaders() }),
        ]);
        if (!rUsuarios.ok) {
            contenedor.innerHTML = '<p class="admin-vacio">Error al cargar usuarios.</p>';
            return;
        }
        const perfil   = await rPerfil.json();
        const data     = await rUsuarios.json();
        const usuarios = data.usuarios;

        miId = perfil.id_usuario ?? null;

        if (!data.total) {
            contenedor.innerHTML = '<p class="admin-vacio">No hay usuarios registrados.</p>';
            return;
        }

        const filas = usuarios.map(u => {
            const esSelf = u.id_usuario === miId;
            const badgeRol    = `<span class="badge-rol badge-rol--${u.rol}">${u.rol}</span>`;
            const badgeActivo = u.activo
                ? '<span class="badge-activo badge-activo--si">Activo</span>'
                : '<span class="badge-activo badge-activo--no">Inactivo</span>';
            const badgeVerif  = u.email_verificado
                ? '<span class="badge-activo badge-activo--si">✓ Verificado</span>'
                : '<span class="badge-activo badge-activo--no">✗ Sin verificar</span>';

            const btnToggleActivo = esSelf ? '' :
                `<button class="btn-accion ${u.activo ? 'btn-accion--rojo' : 'btn-accion--verde'}"
                         data-id="${u.id_usuario}" data-accion="activo" data-valor="${!u.activo}">
                     ${u.activo ? 'Desactivar' : 'Activar'}
                 </button>`;

            const btnToggleRol = esSelf ? '' :
                `<button class="btn-accion btn-accion--gris"
                         data-id="${u.id_usuario}" data-accion="rol"
                         data-valor="${u.rol === 'admin' ? 'registrado' : 'admin'}">
                     ${u.rol === 'admin' ? 'Quitar admin' : 'Hacer admin'}
                 </button>`;

            const btnEliminar = esSelf ? '' :
                `<button class="btn-accion btn-accion--rojo"
                         data-id="${u.id_usuario}" data-accion="eliminar">
                     Eliminar
                 </button>`;

            const nombreMostrado = u.nombre
                ? `<span>${u.nombre}</span><br><small class="admin-usuario__email">${u.email}</small>`
                : u.email;

            return `<tr>
                <td>${nombreMostrado}${esSelf ? ' <em style="font-size:.75rem;color:#888">(tú)</em>' : ''}</td>
                <td>${badgeRol}</td>
                <td>${badgeActivo}</td>
                <td>${badgeVerif}</td>
                <td>${formatearFecha(u.created_at)}</td>
                <td><div class="admin-acciones-td">${btnToggleActivo}${btnToggleRol}${btnEliminar}</div></td>
            </tr>`;
        }).join('');

        const totalPaginas = Math.ceil(data.total / USUARIOS_LIMITE);
        const totalTxt = `${data.total} ${data.total === 1 ? 'usuario' : 'usuarios'}`;
        const controles = totalPaginas > 1
            ? `<button class="btn btn-secundario btn--sm" id="usuarios-anterior" ${usuariosPagina <= 1 ? 'disabled' : ''}>Anterior</button>
                <span>Página ${usuariosPagina} de ${totalPaginas} · ${totalTxt}</span>
                <button class="btn btn-secundario btn--sm" id="usuarios-siguiente" ${usuariosPagina >= totalPaginas ? 'disabled' : ''}>Siguiente</button>`
            : `<span>${totalTxt}</span>`;
        const paginacion = `<div class="paginacion admin-usuarios-paginacion">${controles}</div>`;

        contenedor.innerHTML = `
            <table class="admin-tabla">
                <thead>
                    <tr>
                        <th>Usuario</th>
                        <th>Rol</th>
                        <th>Cuenta</th>
                        <th>Email verif.</th>
                        <th>Alta</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>${filas}</tbody>
            </table>
            ${paginacion}`;

        contenedor.querySelectorAll('[data-accion]').forEach(btn =>
            btn.addEventListener('click', accionUsuario)
        );

        const btnAnt = document.getElementById('usuarios-anterior');
        const btnSig = document.getElementById('usuarios-siguiente');
        if (btnAnt) btnAnt.addEventListener('click', () => { usuariosPagina--; cargarUsuarios(); });
        if (btnSig) btnSig.addEventListener('click', () => { usuariosPagina++; cargarUsuarios(); });
    } catch {
        contenedor.innerHTML = '<p class="admin-vacio">Error al cargar usuarios.</p>';
    }
}

/**
 * iniciarAltaUsuario()
 * Alta de cuentas desde el panel. Es la única vía que queda desde que se
 * retiró el registro público, así que también es la única forma de dar
 * acceso a alguien sin tocar la base de datos a mano.
 *
 * POST /admin/usuarios → 201 { id_usuario, email, rol... }
 *                        409 si el email ya existe
 *                        422 si la contraseña o el email no son válidos
 */
function iniciarAltaUsuario() {
    const form = document.getElementById('form-alta-usuario');
    if (!form) return;

    const requisitos = form.querySelector('.admin-alta__requisitos');
    const TEXTO_REQUISITOS = 'Mínimo 8 caracteres, con mayúscula, minúscula y número.';

    function marcarRequisitos(ok) {
        requisitos.classList.toggle('admin-alta__requisitos--error', !ok);
        requisitos.textContent = ok
            ? TEXTO_REQUISITOS
            : 'La contraseña no cumple: mínimo 8 caracteres, con mayúscula, minúscula y número.';
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email    = document.getElementById('alta-email').value.trim();
        const nombre   = document.getElementById('alta-nombre').value.trim();
        const password = document.getElementById('alta-password').value;
        const rol      = document.getElementById('alta-rol').value;

        // Validación en cliente para no gastar una ida y vuelta en lo evidente.
        // Las reglas viven en utils.js y son las mismas que aplica el backend.
        if (!todosRequisitosOk(cumpleRequisitosPassword(password))) {
            marcarRequisitos(false);
            return;
        }
        marcarRequisitos(true);

        const btn = document.getElementById('btn-alta-usuario');
        btn.disabled = true;

        try {
            const r = await fetch(`${API_URL}/admin/usuarios`, {
                method:  'POST',
                headers: { ...authHeaders(), 'Content-Type': 'application/json' },
                body:    JSON.stringify({ email, nombre, password, rol }),
            });

            if (r.ok) {
                form.reset();
                mostrarToast('Usuario creado. Se le ha enviado el email de verificación.');
                usuariosPagina = 1;
                await cargarUsuarios();
            } else if (r.status === 409) {
                mostrarAlerta('Ya existe un usuario con ese email.');
            } else {
                mostrarAlerta('No se ha podido crear el usuario. Revisa el email y la contraseña.');
            }
        } catch {
            mostrarAlerta('Error de conexión.');
        } finally {
            btn.disabled = false;
        }
    });
}

async function accionUsuario(e) {
    const btn    = e.currentTarget;
    const id     = btn.dataset.id;
    const accion = btn.dataset.accion;
    const valor  = btn.dataset.valor;

    if (accion === 'eliminar') {
        if (!confirm('¿Eliminar este usuario permanentemente? Esta acción no se puede deshacer.')) return;
    }

    btn.disabled = true;
    try {
        let r;
        if (accion === 'activo') {
            r = await fetch(`${API_URL}/admin/usuarios/${id}/activo`,
                { method: 'PATCH', headers: authHeaders(), body: JSON.stringify({ activo: valor === 'true' }) });
        } else if (accion === 'rol') {
            r = await fetch(`${API_URL}/admin/usuarios/${id}/rol`,
                { method: 'PATCH', headers: authHeaders(), body: JSON.stringify({ rol: valor }) });
        } else {
            r = await fetch(`${API_URL}/admin/usuarios/${id}`,
                { method: 'DELETE', headers: authHeaders() });
        }
        if (r.ok) {
            const mensajes = { activo: 'Estado actualizado', rol: 'Rol actualizado', eliminar: 'Usuario eliminado' };
            mostrarToast(mensajes[accion]);
            await cargarUsuarios();
        } else {
            const err = await r.json();
            mostrarAlerta(err.detail ?? err.mensaje ?? 'Error al actualizar usuario.');
            btn.disabled = false;
        }
    } catch {
        mostrarAlerta('Error de conexión.');
        btn.disabled = false;
    }
}


// ── 3. Avisos ─────────────────────────────────────────────────────────────────

async function cargarAvisos() {
    const contenedor = document.getElementById('admin-avisos-contenido');
    try {
        const r = await fetch(`${API_URL}/admin/avisos?incluir_resueltas=true`, { headers: authHeaders() });
        if (!r.ok) { contenedor.innerHTML = '<p class="admin-vacio">Error al cargar avisos.</p>'; return; }
        const avisos = await r.json();

        const activas   = avisos.filter(a => !a.fecha_resolucion);
        const resueltas = avisos.filter(a =>  a.fecha_resolucion);

        let html = '';

        if (!activas.length) {
            html += '<p class="admin-vacio">No hay avisos activos. El banner de inicio no se mostrará.</p>';
        } else {
            const badgePlazo = {
                abierto:   '<span class="admin-plazo-badge admin-plazo-badge--abierto">Plazo abierto</span>',
                cerrado:   '<span class="admin-plazo-badge admin-plazo-badge--cerrado">Plazo cerrado</span>',
                sin_fecha: '<span class="admin-plazo-badge admin-plazo-badge--falta">⚠ Falta fecha de plazo</span>',
            };
            html += activas.map(a => `
                <div class="admin-aviso" data-id="${a.id_convoc}">
                    <div class="admin-aviso__info">
                        <div class="admin-aviso__titulo">${a.titulo_convoc}</div>
                        <div class="admin-aviso__meta">
                            ${a.tipo_convoc.toUpperCase()} · ${a.anio_convocatoria}
                            ${a.fecha_convocatoria ? ' · BOE: ' + formatearFecha(a.fecha_convocatoria) : ''}
                        </div>
                        <div class="admin-aviso__plazo">
                            ${badgePlazo[a.estado_plazo] || ''}
                            <label class="admin-plazo-label">Fin de plazo:
                                <input type="date" class="admin-plazo-input" value="${a.fecha_fin_plazo ?? ''}">
                            </label>
                            <button class="btn-accion btn-accion--gris" data-accion="guardar-plazo" data-id="${a.id_convoc}"
                                    title="Guarda la fecha de fin de plazo de solicitud">
                                Guardar plazo
                            </button>
                        </div>
                    </div>
                    <div class="admin-aviso__acciones">
                        <button class="btn-accion btn-accion--gris" data-accion="desactivar" data-id="${a.id_convoc}"
                                title="Marca la convocatoria como resuelta (desaparece del banner)">
                            Marcar resuelta
                        </button>
                        <button class="btn-accion btn-accion--rojo" data-accion="eliminar" data-id="${a.id_convoc}"
                                title="Elimina la convocatoria (solo si no tiene solicitudes)">
                            Eliminar
                        </button>
                    </div>
                </div>`).join('');
        }

        if (resueltas.length) {
            const itemsResueltas = resueltas.map(a => `
                <div class="admin-aviso admin-aviso--resuelta" data-id="${a.id_convoc}">
                    <div class="admin-aviso__info">
                        <div class="admin-aviso__titulo">${a.titulo_convoc}</div>
                        <div class="admin-aviso__meta">
                            ${a.tipo_convoc.toUpperCase()} · ${a.anio_convocatoria}
                            · resuelta ${formatearFecha(a.fecha_resolucion)}
                        </div>
                    </div>
                    <div class="admin-aviso__acciones">
                        <button class="btn-accion btn-accion--verde" data-accion="reactivar" data-id="${a.id_convoc}"
                                title="Vuelve a mostrarla como aviso activo en el banner">
                            Reactivar
                        </button>
                        <button class="btn-accion btn-accion--rojo" data-accion="eliminar" data-id="${a.id_convoc}"
                                title="Elimina la convocatoria (solo si no tiene solicitudes)">
                            Eliminar
                        </button>
                    </div>
                </div>`).join('');
            html += `
                <details class="admin-resueltas">
                    <summary class="admin-resueltas__summary">
                        Historial de resueltas (${resueltas.length})
                    </summary>
                    <div class="admin-resueltas__lista">${itemsResueltas}</div>
                </details>`;
        }

        contenedor.innerHTML = html;
        contenedor.querySelectorAll('[data-accion]').forEach(btn =>
            btn.addEventListener('click', accionAviso)
        );
    } catch {
        contenedor.innerHTML = '<p class="admin-vacio">Error al cargar avisos.</p>';
    }
}

async function accionAviso(e) {
    const btn    = e.currentTarget;
    const id     = btn.dataset.id;
    const accion = btn.dataset.accion;

    if (accion === 'eliminar') {
        if (!confirm('¿Eliminar esta convocatoria? Esta acción no se puede deshacer.')) return;
    }

    btn.disabled = true;
    try {
        let r;
        if (accion === 'guardar-plazo') {
            const card  = btn.closest('.admin-aviso');
            const fecha = card.querySelector('.admin-plazo-input').value || null;  // vacío → borra el plazo
            r = await fetch(`${API_URL}/admin/avisos/${id}/fin-plazo`, {
                method: 'PATCH',
                headers: { ...authHeaders(), 'Content-Type': 'application/json' },
                body: JSON.stringify({ fecha_fin_plazo: fecha }),
            });
        } else if (accion === 'desactivar') {
            r = await fetch(`${API_URL}/admin/avisos/${id}/desactivar`,
                { method: 'PATCH', headers: authHeaders() });
        } else if (accion === 'reactivar') {
            r = await fetch(`${API_URL}/admin/avisos/${id}/reactivar`,
                { method: 'PATCH', headers: authHeaders() });
        } else {
            r = await fetch(`${API_URL}/admin/avisos/${id}`,
                { method: 'DELETE', headers: authHeaders() });
        }
        if (r.ok) {
            const mensajes = { 'guardar-plazo': 'Fecha de plazo guardada', desactivar: 'Convocatoria marcada como resuelta', reactivar: 'Aviso reactivado', eliminar: 'Convocatoria eliminada' };
            mostrarToast(mensajes[accion]);
            await cargarAvisos();
            if (accion === 'eliminar') await cargarEstado();
        } else {
            const err = await r.json();
            mostrarAlerta(err.detail ?? err.mensaje ?? 'Error al procesar la acción.');
            btn.disabled = false;
        }
    } catch {
        mostrarAlerta('Error de conexión.');
        btn.disabled = false;
    }
}


// ── 4. Logs ───────────────────────────────────────────────────────────────────

async function cargarLogs() {
    const pre = document.getElementById('admin-logs-pre');
    const n   = document.getElementById('logs-n').value;
    pre.textContent = 'Cargando...';
    pre.className   = 'admin-logs-pre';
    try {
        const r = await fetch(`${API_URL}/admin/logs?n=${n}`, { headers: authHeaders() });
        if (!r.ok) {
            pre.textContent = 'Error al cargar logs.';
            pre.classList.add('admin-logs-pre--vacio');
            return;
        }
        const data = await r.json();
        if (!data.lineas.length) {
            pre.textContent = '(sin registros)';
            pre.classList.add('admin-logs-pre--vacio');
        } else {
            pre.textContent = data.lineas.join('\n');
            pre.scrollTop   = pre.scrollHeight;
        }
    } catch {
        pre.textContent = 'Error al cargar logs.';
        pre.classList.add('admin-logs-pre--vacio');
    }
}


// ── 5. Logs de error ──────────────────────────────────────────────────────────

async function cargarLogsErrores() {
    const pre = document.getElementById('admin-logs-errores-pre');
    const n   = document.getElementById('logs-errores-n').value;
    pre.textContent = 'Cargando...';
    pre.className   = 'admin-logs-pre admin-logs-pre--error';
    try {
        const r = await fetch(`${API_URL}/admin/logs/errores?n=${n}`, { headers: authHeaders() });
        if (!r.ok) {
            pre.textContent = 'Error al cargar logs.';
            pre.classList.add('admin-logs-pre--vacio');
            return;
        }
        const data = await r.json();
        if (!data.lineas.length) {
            pre.textContent = '(sin registros)';
            pre.classList.add('admin-logs-pre--vacio');
        } else {
            pre.textContent = data.lineas.join('\n');
            pre.scrollTop   = pre.scrollHeight;
        }
    } catch {
        pre.textContent = 'Error al cargar logs.';
        pre.classList.add('admin-logs-pre--vacio');
    }
}


// ── 6. Logs del cron ──────────────────────────────────────────────────────────

async function cargarLogsCron(fichero, preId, selectId) {
    const pre = document.getElementById(preId);
    const n   = document.getElementById(selectId).value;
    pre.textContent = 'Cargando...';
    pre.className   = 'admin-logs-pre';
    try {
        const r = await fetch(`${API_URL}/admin/logs/cron?fichero=${fichero}&n=${n}`, { headers: authHeaders() });
        if (!r.ok) {
            pre.textContent = 'Error al cargar logs.';
            pre.classList.add('admin-logs-pre--vacio');
            return;
        }
        const data = await r.json();
        if (!data.lineas.length) {
            pre.textContent = '(sin registros)';
            pre.classList.add('admin-logs-pre--vacio');
        } else {
            pre.textContent = data.lineas.join('\n');
            pre.scrollTop   = pre.scrollHeight;
        }
    } catch {
        pre.textContent = 'Error al cargar logs.';
        pre.classList.add('admin-logs-pre--vacio');
    }
}

const cargarLogsCronBdns   = () => cargarLogsCron('bdns',   'admin-logs-cron-bdns-pre',   'logs-cron-bdns-n');
const cargarLogsCronHealth = () => cargarLogsCron('health', 'admin-logs-cron-health-pre', 'logs-cron-health-n');


// ── Cerrar sesión ─────────────────────────────────────────────────────────────

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


// ── Inicialización ────────────────────────────────────────────────────────────

async function init() {
    const acceso = await verificarAcceso();
    if (!acceso) return;

    // Carga en paralelo todas las secciones
    await Promise.all([
        cargarEstado(),
        cargarUsuarios(),
        cargarAvisos(),
        cargarLogs(),
        cargarLogsErrores(),
        cargarLogsCronBdns(),
        cargarLogsCronHealth(),
    ]);

    iniciarAltaUsuario();

    document.getElementById('btn-cerrar-sesion')
        .addEventListener('click', cerrarSesion);
    document.getElementById('btn-recargar-logs')
        .addEventListener('click', cargarLogs);
    document.getElementById('logs-n')
        .addEventListener('change', cargarLogs);
    document.getElementById('btn-recargar-logs-errores')
        .addEventListener('click', cargarLogsErrores);
    document.getElementById('logs-errores-n')
        .addEventListener('change', cargarLogsErrores);
    document.getElementById('btn-recargar-logs-cron-bdns')
        .addEventListener('click', cargarLogsCronBdns);
    document.getElementById('logs-cron-bdns-n')
        .addEventListener('change', cargarLogsCronBdns);
    document.getElementById('btn-recargar-logs-cron-health')
        .addEventListener('click', cargarLogsCronHealth);
    document.getElementById('logs-cron-health-n')
        .addEventListener('change', cargarLogsCronHealth);
}

init();
