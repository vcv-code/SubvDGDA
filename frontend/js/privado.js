/**
 * privado.js — Lógica de la zona exclusiva (privado.html)
 * ──────────────────────────────────────────────────────
 * Este archivo gestiona el control de acceso y la carga de contenido
 * de la página privada. Es el único script que trabaja con el token JWT.
 *
 * FLUJO COMPLETO:
 *   1. Comprueba si hay token en localStorage
 *   2. Si no hay → redirige a login.html inmediatamente
 *   3. Si hay token → llama a GET /privado/perfil y GET /privado/resumen-exclusivo
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
 * obtenerToken()
 * Lee el token JWT de localStorage.
 * Si no existe, redirige al login y devuelve null para detener la ejecución.
 *
 * ¿Por qué comprobar el token en el cliente si el servidor ya lo comprueba?
 * La comprobación del servidor es la que cuenta (seguridad real). La comprobación
 * del cliente es solo para mejorar la experiencia de usuario: evitar la petición
 * al servidor si sabemos de antemano que no hay token, y redirigir de forma
 * instantánea sin esperar la respuesta de red.
 *
 * @returns {string|null} El token JWT o null si no existe
 */
function obtenerToken() {
    const token = localStorage.getItem('token');
    if (!token) {
        // Sin token → no hay sesión iniciada → al login
        window.location.href = 'login.html';
        return null;
    }
    return token;
}

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
function cerrarSesion() {
    localStorage.removeItem('token');
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
        // Token expirado o inválido → limpiar y redirigir
        localStorage.removeItem('token');
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
 * ICONOS_CONTENIDO
 * Mapa de palabras clave → icono SVG para cada tipo de contenido exclusivo.
 * Se usa para añadir un icono visual a cada tarjeta.
 * Los SVG son de Material Icons (camino de diseño simplificado).
 */
const ICONOS_CONTENIDO = {
    'historial':    '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
    'análisis':     '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>',
    'comparativa':  '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg>',
    'puntuación':   '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
};

/**
 * obtenerIcono(texto)
 * Devuelve el SVG correspondiente al contenido, buscando por palabras clave.
 * Si no encuentra ninguna coincidencia, devuelve un icono genérico.
 *
 * @param {string} texto - Descripción del contenido exclusivo
 * @returns {string} HTML del SVG
 */
function obtenerIcono(texto) {
    const textoMin = texto.toLowerCase();
    for (const [clave, svg] of Object.entries(ICONOS_CONTENIDO)) {
        if (textoMin.includes(clave)) return svg;
    }
    // Icono genérico: documento
    return '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>';
}

/**
 * renderizarContenido(items)
 * Genera las tarjetas de contenido exclusivo y las inserta en el DOM.
 * Cada item del array es una string que describe el contenido.
 * Usa las clases .privado-item definidas en styles.css sección 23.
 *
 * @param {string[]} items - Array de strings con el contenido exclusivo
 */
function renderizarContenido(items) {
    const contenedor = document.getElementById('privado-contenido');
    if (!contenedor) return;

    // Vaciamos los skeleton loaders de carga
    contenedor.innerHTML = '';

    items.forEach(item => {
        const tarjeta = document.createElement('div');
        tarjeta.className = 'privado-item';

        tarjeta.innerHTML = `
            <div class="privado-item__icono-svg" aria-hidden="true">
                ${obtenerIcono(item)}
            </div>
            <div>
                <p class="privado-item__nombre">${item}</p>
                <p class="privado-item__desc">Disponible para usuarios registrados</p>
            </div>
        `;

        contenedor.appendChild(tarjeta);
    });
}

/**
 * mostrarErrorPrivado()
 * Muestra la alerta de error y limpia los skeleton loaders.
 */
function mostrarErrorPrivado() {
    const alerta = document.getElementById('privado-alerta');
    if (alerta) alerta.classList.add('visible');

    // Limpiamos los skeletons para no mostrar contenido de carga falso
    const contenedor = document.getElementById('privado-contenido');
    if (contenedor) contenedor.innerHTML = '';

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
 * /privado/resumen-exclusivo devuelve el contenido exclusivo (lista de items).
 * Son responsabilidades diferentes y el backend las tiene separadas.
 * Usamos Promise.all() para hacerlas en paralelo y no esperar una antes
 * de lanzar la otra.
 */
async function cargarZonaPrivada() {

    // ── Paso 1: Comprobar token ───────────────────────────────────────────
    const token = obtenerToken();
    if (!token) return;   // obtenerToken() ya redirigió si no había token

    try {
        // ── Paso 2: Peticiones en paralelo ───────────────────────────────
        /**
         * Promise.all() lanza las dos peticiones simultáneamente.
         * Espera a que AMBAS terminen antes de continuar.
         * Es más eficiente que esperar la primera y luego lanzar la segunda.
         *
         * Si cualquiera de las dos falla (401, error de red...) el catch
         * lo captura.
         */
        const [perfil, resumen] = await Promise.all([
            fetchAutenticado('/privado/perfil', token),
            fetchAutenticado('/privado/resumen-exclusivo', token),
        ]);

        // fetchAutenticado() devuelve null si hubo 401 (y ya redirigió)
        if (!perfil || !resumen) return;

        // ── Paso 3: Renderizar los datos ─────────────────────────────────
        mostrarSaludo(resumen.mensaje);
        mostrarPerfil(perfil);
        renderizarContenido(resumen.contenido);

    } catch (error) {
        console.error('Error al cargar zona privada:', error);
        mostrarErrorPrivado();
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
});
