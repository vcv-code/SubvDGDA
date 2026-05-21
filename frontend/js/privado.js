/**
 * privado.js — Lógica de la zona exclusiva (privado.html)
 * ──────────────────────────────────────────────────────
 * Este archivo gestiona el control de acceso y la carga de contenido
 * de la página privada. Es el único script que trabaja con el token JWT.
 *
 * FLUJO COMPLETO:
 *   1. Comprueba si hay token en localStorage
 *   2. Si no hay → redirige a login.html inmediatamente
 *   3. Si hay token → llama a GET /privado/perfil
 *      con el header Authorization: Bearer <token>
 *   4. Muestra el saludo personalizado y las tarjetas de contenido
 *   5. Si el servidor responde 401 (token expirado o inválido) → redirige a login.html
 *
 * CONCEPTOS CLAVE USADOS:
 *   · localStorage.getItem()     → leer el token guardado por auth.js
 *   · localStorage.removeItem()  → borrar el token al cerrar sesión
 *   · fetch() con headers        → enviar el token al servidor
 *   · Bearer token               → estándar de autenticación HTTP con JWT
 *   · Redirect programático      → window.location.href para cambiar de página
 */


// ─────────────────────────────────────────────────────────────
// CONFIGURACIÓN
// ─────────────────────────────────────────────────────────────

const API_URL = '';


// ─────────────────────────────────────────────────────────────
// CONTROL DE ACCESO
// ─────────────────────────────────────────────────────────────

/**
 * cerrarSesion()
 * Elimina el token de localStorage y redirige al login.
 * Se llama al hacer clic en cualquiera de los botones de cerrar sesión.
 *
 * ¿Por qué no invalidamos el token en el servidor?
 * Los JWT son stateless (sin estado en el servidor). Una vez emitido,
 * el servidor no puede "invalidarlo" directamente. La forma correcta de
 * manejar esto en producción sería una lista negra de tokens o usar
 * tokens de corta duración con refresh tokens. Para el nivel de este
 * proyecto, borrar el token del cliente es suficiente.
 */
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

async function cerrarSesion() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
        // Revocamos el token en el servidor (fire-and-forget, no bloqueamos)
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


// ─────────────────────────────────────────────────────────────
// UTILIDADES DE FETCH CON AUTENTICACIÓN
// ─────────────────────────────────────────────────────────────

/**
 * fetchAutenticado(ruta, token)
 * Hace una petición GET a la API incluyendo el token JWT en la cabecera.
 *
 * ¿Qué es el header Authorization: Bearer?
 * Es el estándar HTTP para enviar tokens de autenticación.
 * "Bearer" significa "portador" — quien tenga este token tiene acceso.
 * El servidor lo valida con la clave secreta con la que fue firmado.
 *
 * Si el servidor responde 401 (Unauthorized), el token ha expirado
 * o es inválido → borramos el token y redirigimos al login.
 *
 * @param {string} ruta  - Ruta de la API (sin el API_URL base)
 * @param {string} token - El JWT guardado en localStorage
 * @returns {Promise<Object>} Los datos JSON de la respuesta
 */
async function fetchAutenticado(ruta, token) {
    const respuesta = await fetch(`${API_URL}${ruta}`, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
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

    if (!respuesta.ok) {
        throw new Error(`Error ${respuesta.status} en ${ruta}`);
    }

    return respuesta.json();
}


// ─────────────────────────────────────────────────────────────
// RENDERIZADO DE CONTENIDO
// ─────────────────────────────────────────────────────────────

/**
 * mostrarSaludo(mensaje)
 * Actualiza el título H1 con el mensaje de bienvenida del servidor.
 * Ejemplo del backend: "Bienvenida, usuario@email.com"
 *
 * @param {string} mensaje
 */
function mostrarSaludo(mensaje) {
    const el = document.getElementById('privado-saludo');
    if (el) el.textContent = mensaje;
}

/**
 * mostrarPerfil(perfil)
 * Muestra el rol y fecha de registro debajo del saludo.
 *
 * @param {{ email: string, rol: string, miembro_desde: string }} perfil
 */
function mostrarPerfil(perfil) {
    const el = document.getElementById('privado-perfil');
    if (!el) return;

    // Formateamos la fecha de registro con Intl.DateTimeFormat
    // para que aparezca en español (ej: "15 de enero de 2026")
    const fecha = new Date(perfil.miembro_desde);
    const fechaFormateada = new Intl.DateTimeFormat('es-ES', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
    }).format(fecha);

    el.textContent = `Cuenta activa desde el ${fechaFormateada} · Rol: ${perfil.rol}`;
}


/**
 * mostrarErrorPrivado()
 * Muestra la alerta de error y limpia los skeleton loaders.
 */
function mostrarErrorPrivado() {
    const alerta = document.getElementById('privado-alerta');
    if (alerta) alerta.classList.add('visible');

    const saludo = document.getElementById('privado-saludo');
    if (saludo) saludo.textContent = 'No se pudo cargar la página';
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN PRINCIPAL
// ─────────────────────────────────────────────────────────────

/**
 * cargarZonaPrivada()
 * Función principal: comprueba el token, hace las dos peticiones
 * al backend y rellena la página con los datos recibidos.
 *
 * ¿Por qué dos peticiones y no una?
 * /privado/perfil devuelve los datos del usuario (email, rol, fecha).
 * El contenido exclusivo (resumen-tabla y resoluciones) está en exclusivo.html.
 */
async function cargarZonaPrivada() {

    // ── Paso 1: Comprobar token (con renovación automática si hay refresh_token)
    let token = localStorage.getItem('token');
    if (!token) {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            try {
                const r = await fetch(`${API_URL}/auth/refresh`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh_token: refreshToken }),
                });
                if (r.ok) {
                    const datos = await r.json();
                    localStorage.setItem('token', datos.access_token);
                    localStorage.setItem('refresh_token', datos.refresh_token);
                    token = datos.access_token;
                } else {
                    localStorage.removeItem('refresh_token');
                    sessionStorage.setItem('redirect_post_login', window.location.href);
                    window.location.href = 'login.html';
                    return;
                }
            } catch {
                sessionStorage.setItem('redirect_post_login', window.location.href);
                window.location.href = 'login.html';
                return;
            }
        } else {
            sessionStorage.setItem('redirect_post_login', window.location.href);
            window.location.href = 'login.html';
            return;
        }
    }

    try {
        // ── Paso 2: Cargar perfil ─────────────────────────────────────────
        const perfil = await fetchAutenticado('/privado/perfil', token);
        if (!perfil) return;

        // ── Paso 3: Renderizar ────────────────────────────────────────────
        mostrarSaludo(`Bienvenida, ${perfil.nombre ?? perfil.email}`);
        mostrarPerfil(perfil);

        const campoNombre = document.getElementById('nombre-nuevo');
        if (campoNombre && perfil.nombre) campoNombre.value = perfil.nombre;

        if (perfil.rol === 'admin') {
            document.getElementById('btn-panel-admin').classList.add('privado-banner__btn-admin--visible');
        }

    } catch (error) {
        console.error('Error al cargar zona privada:', error);
        mostrarErrorPrivado();
    }
}


// ─────────────────────────────────────────────────────────────
// CAMBIAR NOMBRE
// ─────────────────────────────────────────────────────────────

async function manejarCambiarNombre(evento) {
    evento.preventDefault();

    const token = localStorage.getItem('token');
    if (!token) { window.location.href = 'login.html'; return; }

    const nombre = document.getElementById('nombre-nuevo').value.trim();
    const alerta = document.getElementById('cambiar-nombre-error');
    const ok     = document.getElementById('cambiar-nombre-ok');

    alerta.classList.remove('visible');
    ok.style.display = 'none';

    try {
        const respuesta = await fetch(`${API_URL}/privado/cambiar-nombre`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({ nombre }),
        });

        if (respuesta.status === 422) {
            const datos = await respuesta.json();
            const raw = datos.detail?.[0]?.msg ?? 'Nombre no válido.';
            alerta.textContent = raw.replace(/^Value error,\s*/i, '');
            alerta.classList.add('visible');
            return;
        }
        if (!respuesta.ok) {
            alerta.textContent = 'Error inesperado. Inténtalo de nuevo.';
            alerta.classList.add('visible');
            return;
        }

        const datos = await respuesta.json();
        mostrarSaludo(`Bienvenida, ${datos.nombre}`);
        ok.style.display = 'block';

    } catch {
        alerta.textContent = 'No se pudo conectar con el servidor.';
        alerta.classList.add('visible');
    }
}


// ─────────────────────────────────────────────────────────────
// CAMBIAR CONTRASEÑA
// ─────────────────────────────────────────────────────────────

async function manejarCambiarPassword(evento) {
    evento.preventDefault();

    const token = localStorage.getItem('token');
    if (!token) {
        sessionStorage.setItem('redirect_post_login', window.location.href);
        window.location.href = 'login.html';
        return;
    }

    const actual        = document.getElementById('password-actual').value;
    const nueva         = document.getElementById('password-nueva').value;
    const nuevaConfirm  = document.getElementById('password-nueva-confirm')?.value ?? '';
    const errorConfirm  = document.getElementById('error-password-nueva-confirm');
    const alerta        = document.getElementById('cambiar-password-error');
    const ok            = document.getElementById('cambiar-password-ok');

    alerta.classList.remove('visible');
    ok.style.display = 'none';

    // Validación confirmar contraseña (solo frontend, antes de enviar al servidor)
    if (nueva !== nuevaConfirm) {
        if (errorConfirm) errorConfirm.classList.add('visible');
        return;
    }
    if (errorConfirm) errorConfirm.classList.remove('visible');

    try {
        const respuesta = await fetch(`${API_URL}/privado/cambiar-contrasena`, {
            method: 'PUT',
            headers: {
                'Content-Type':  'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ contrasena_actual: actual, contrasena_nueva: nueva }),
        });

        if (respuesta.status === 401) {
            alerta.textContent = 'Contraseña actual incorrecta.';
            alerta.classList.add('visible');
            return;
        }
        if (respuesta.status === 422) {
            const datos = await respuesta.json();
            const raw = datos.detail?.[0]?.msg ?? 'La nueva contraseña no cumple los requisitos.';
            // Pydantic v2 prefija los errores custom con "Value error, "
            alerta.textContent = raw.replace(/^Value error,\s*/i, '');
            alerta.classList.add('visible');
            return;
        }
        if (!respuesta.ok) {
            alerta.textContent = 'Error inesperado. Inténtalo de nuevo.';
            alerta.classList.add('visible');
            return;
        }

        document.getElementById('password-actual').value = '';
        document.getElementById('password-nueva').value  = '';
        const confirmField = document.getElementById('password-nueva-confirm');
        if (confirmField) confirmField.value = '';
        ok.style.display = 'block';

    } catch {
        alerta.textContent = 'No se pudo conectar con el servidor.';
        alerta.classList.add('visible');
    }
}


// ─────────────────────────────────────────────────────────────
// BOTONES DE CERRAR SESIÓN
// ─────────────────────────────────────────────────────────────

/**
 * Conecta los dos botones de cerrar sesión (navbar y cuerpo de página)
 * con la función cerrarSesion(). Se hace aquí y no con onclick en el HTML
 * para separar la lógica del marcado (principio de separación de capas).
 */
function iniciarBotonesCerrarSesion() {
    const btnNavbar = document.getElementById('btn-cerrar-sesion');
    if (btnNavbar) btnNavbar.addEventListener('click', cerrarSesion);

    const btnPrincipal = document.getElementById('btn-cerrar-sesion-principal');
    if (btnPrincipal) btnPrincipal.addEventListener('click', cerrarSesion);
}


// ─────────────────────────────────────────────────────────────
// PUNTO DE ENTRADA
// ─────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    iniciarBotonesCerrarSesion();
    cargarZonaPrivada();

    const formNombre = document.getElementById('form-cambiar-nombre');
    if (formNombre) formNombre.addEventListener('submit', manejarCambiarNombre);

    const formPassword = document.getElementById('form-cambiar-password');
    if (formPassword) formPassword.addEventListener('submit', manejarCambiarPassword);
});
