/**
 * auth.js — Lógica de login y registro
 * ──────────────────────────────────────────────────────
 * Este archivo gestiona los formularios de login.html y registro.html.
 * Es el único script que se encarga de toda la autenticación del frontend.
 *
 * ¿Cómo sabe este script en qué página está?
 * No necesita saberlo. Cada función busca un elemento del DOM por su id.
 * Si el elemento no existe (porque estamos en otra página), el código
 * simplemente no hace nada. Así funciona en ambas páginas con un solo archivo.
 *
 * PETICIONES A LA API:
 *   · POST /auth/login    → { email, password } → { access_token, token_type }
 *   · POST /auth/registro → { email, password } → 201 { id_usuario, email, rol... }
 *
 * ALMACENAMIENTO DEL TOKEN:
 *   · localStorage.setItem('token', access_token)
 *   · El token se lee después en privado.html y en futuras peticiones protegidas
 *
 * CONCEPTOS CLAVE USADOS:
 *   · fetch() con método POST y body JSON
 *   · async / await para código asíncrono
 *   · localStorage para persistir el token entre páginas
 *   · Validación client-side antes de enviar al servidor
 *   · Feedback visual: errores debajo del campo, alerta general, botón deshabilitado
 */


// ─────────────────────────────────────────────────────────────
// CONFIGURACIÓN
// ─────────────────────────────────────────────────────────────

/**
 * URL base de la API.
 * Mismo valor que en home.js, solicitudes.js y estadisticas.js.
 * Si el backend cambia de puerto, se cambia aquí una sola vez.
 */
const API_URL = '';


// ─────────────────────────────────────────────────────────────
// UTILIDADES DE VALIDACIÓN
// ─────────────────────────────────────────────────────────────

/**
 * esEmailValido(email)
 * Comprueba que el string tiene el formato básico de un email.
 * Usamos una expresión regular (regex) estándar para esto.
 *
 * ¿Por qué no confiamos solo en type="email" del HTML?
 * Los navegadores tienen comportamientos distintos con la validación
 * nativa. Al usar novalidate en el formulario y validar en JS,
 * tenemos control total sobre los mensajes de error.
 *
 * @param {string} email
 * @returns {boolean}
 */
function esEmailValido(email) {
    // Regex básica de email: algo@algo.algo
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * cumpleRequisitosPassword(password)
 * Comprueba los cuatro requisitos del backend (definidos en schemas.py).
 * Devuelve un objeto con el resultado de cada requisito individualmente
 * para poder actualizar los indicadores visuales uno a uno.
 *
 * @param {string} password
 * @returns {{ longitud: boolean, mayuscula: boolean, minuscula: boolean, numero: boolean }}
 */
function cumpleRequisitosPassword(password) {
    return {
        longitud:  password.length >= 8,
        mayuscula: /[A-Z]/.test(password),
        minuscula: /[a-z]/.test(password),
        numero:    /[0-9]/.test(password),
    };
}

/**
 * todosRequisitosOk(requisitos)
 * Devuelve true si todos los requisitos son true.
 * Usamos Object.values() para obtener el array de booleanos
 * y .every() para comprobar que todos sean true.
 *
 * @param {object} requisitos - Resultado de cumpleRequisitosPassword()
 * @returns {boolean}
 */
function todosRequisitosOk(requisitos) {
    return Object.values(requisitos).every(Boolean);
}


// ─────────────────────────────────────────────────────────────
// UTILIDADES DE UI (interfaz de usuario)
// ─────────────────────────────────────────────────────────────

/**
 * mostrarError(idElemento, visible)
 * Muestra u oculta un mensaje de error debajo de un campo.
 * Añade o quita la clase "visible" (definida en styles.css sección 22).
 *
 * @param {string} idElemento - id del <span class="campo-error">
 * @param {boolean} visible   - true = mostrar, false = ocultar
 */
function mostrarError(idElemento, visible) {
    const el = document.getElementById(idElemento);
    if (!el) return;
    el.classList.toggle('visible', visible);
}

/**
 * mostrarAlerta(idElemento, visible, mensaje)
 * Muestra u oculta la alerta general del formulario.
 * Si se pasa un mensaje, lo actualiza.
 *
 * @param {string} idElemento
 * @param {boolean} visible
 * @param {string} [mensaje] - Texto a mostrar en la alerta (opcional)
 */
function mostrarAlerta(idElemento, visible, mensaje) {
    const el = document.getElementById(idElemento);
    if (!el) return;
    if (mensaje) el.textContent = mensaje;
    el.classList.toggle('visible', visible);
}

/**
 * setBtnCargando(idBtn, cargando)
 * Deshabilita el botón de submit mientras espera la respuesta del servidor.
 * Esto evita que el usuario haga clic varias veces y envíe la petición
 * dos veces (double submit).
 *
 * @param {string} idBtn
 * @param {boolean} cargando
 */
function setBtnCargando(idBtn, cargando) {
    const btn = document.getElementById(idBtn);
    if (!btn) return;
    btn.disabled = cargando;
    btn.textContent = cargando ? 'Espera...' : btn.dataset.textoOriginal;
}


// ─────────────────────────────────────────────────────────────
// MÓDULO DE LOGIN
// ─────────────────────────────────────────────────────────────

/**
 * iniciarLogin()
 * Busca el formulario de login en el DOM y le añade el event listener.
 * Si el formulario no existe (estamos en registro.html), no hace nada.
 * Se llama desde DOMContentLoaded.
 */
function iniciarLogin() {
    const form = document.getElementById('form-login');
    if (!form) return;   // No estamos en login.html, salimos

    // Guardamos el texto original del botón para restaurarlo después de la carga
    const btn = document.getElementById('btn-submit-login');
    if (btn) btn.dataset.textoOriginal = btn.textContent;

    // Escuchamos el evento 'submit' del formulario
    form.addEventListener('submit', async (evento) => {
        // preventDefault() evita que el navegador recargue la página al enviar
        // (comportamiento por defecto de los formularios HTML)
        evento.preventDefault();

        // ── Paso 1: Leer los valores del formulario ───────────────────────
        const email    = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;

        // ── Paso 2: Validación client-side ────────────────────────────────
        // Validamos antes de hacer la petición al servidor para dar feedback
        // inmediato sin necesidad de esperar la respuesta de red.
        let hayErrores = false;

        if (!esEmailValido(email)) {
            mostrarError('error-email', true);
            hayErrores = true;
        } else {
            mostrarError('error-email', false);
        }

        if (password.length === 0) {
            mostrarError('error-password', true);
            hayErrores = true;
        } else {
            mostrarError('error-password', false);
        }

        if (hayErrores) return;   // No enviamos si hay errores de validación

        // ── Paso 3: Ocultar alerta previa y deshabilitar botón ───────────
        mostrarAlerta('login-alerta', false);
        setBtnCargando('btn-submit-login', true);

        try {
            // ── Paso 4: Petición POST /auth/login ─────────────────────────
            /**
             * El backend espera un JSON con { email, password }.
             * A diferencia de un formulario tradicional (form-urlencoded),
             * usamos JSON porque el endpoint del backend usa LoginIn (Pydantic).
             *
             * Headers:
             *   'Content-Type': 'application/json' — indica al servidor
             *   que el body es JSON, no datos de formulario.
             *
             * Body:
             *   JSON.stringify() convierte el objeto JS a texto JSON.
             *   Ejemplo: { email: "a@b.com", password: "Test1234" }
             *         → '{"email":"a@b.com","password":"Test1234"}'
             */
            const respuesta = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            if (!respuesta.ok) {
                // El servidor devolvió un error (401 credenciales incorrectas,
                // 403 cuenta desactivada, etc.)
                const errorData = await respuesta.json().catch(() => ({}));
                const mensaje = errorData.mensaje || 'Email o contraseña incorrectos.';
                mostrarAlerta('login-alerta', true, mensaje);
                return; // cambio de detail por mensaje
            }

            // ── Paso 5: Guardar el token ──────────────────────────────────
            /**
             * La respuesta tiene la forma: { access_token: "...", token_type: "bearer" }
             *
             * Guardamos access_token en localStorage con la clave "token".
             * localStorage persiste aunque el usuario cierre la pestaña.
             * Solo se borra si el usuario cierra sesión o limpia el navegador.
             *
             * ¿Por qué localStorage y no sessionStorage?
             * sessionStorage se borra al cerrar la pestaña. Para una app que
             * el usuario puede usar en varias sesiones, localStorage es más cómodo.
             * En una app bancaria usaríamos sessionStorage por seguridad.
             */
            const datos = await respuesta.json();
            localStorage.setItem('token', datos.access_token);

            // Si "Recuérdame" está marcado, guardamos el refresh token
            // para que la sesión se pueda renovar automáticamente al volver
            const recordarme = document.getElementById('recordarme');
            if (recordarme?.checked) {
                localStorage.setItem('refresh_token', datos.refresh_token);
            } else {
                localStorage.removeItem('refresh_token');
            }

            // ── Paso 6: Redirigir a la zona privada ───────────────────────
            window.location.href = 'privado.html';

        } catch (error) {
            // Error de red (backend apagado, sin conexión, etc.)
            console.error('Error en login:', error);
            mostrarAlerta('login-alerta', true, 'No se pudo conectar con el servidor. Comprueba que el backend está activo.');

        } finally {
            // finally siempre se ejecuta, haya error o no.
            // Restauramos el botón para que el usuario pueda volver a intentarlo.
            setBtnCargando('btn-submit-login', false);
        }
    });
}


// ─────────────────────────────────────────────────────────────
// MÓDULO DE REGISTRO
// ─────────────────────────────────────────────────────────────

/**
 * actualizarIndicadoresPassword(password)
 * Actualiza los 4 indicadores de requisitos en tiempo real.
 * Se llama en cada pulsación de tecla en el campo de contraseña.
 *
 * ¿Cómo funciona visualmente?
 * Cada .password-req tiene un ::before con "·" por defecto.
 * Al añadir la clase "ok", el CSS cambia el "·" por "✓" verde.
 * Ver styles.css sección 22 (.password-req.ok).
 *
 * @param {string} password
 */
function actualizarIndicadoresPassword(password) {
    const req = cumpleRequisitosPassword(password);

    // Para cada requisito: añadir/quitar clase "ok" según si se cumple
    document.getElementById('req-longitud') ?.classList.toggle('ok', req.longitud);
    document.getElementById('req-mayuscula')?.classList.toggle('ok', req.mayuscula);
    document.getElementById('req-minuscula')?.classList.toggle('ok', req.minuscula);
    document.getElementById('req-numero')   ?.classList.toggle('ok', req.numero);
}

/**
 * iniciarRegistro()
 * Busca el formulario de registro en el DOM y le añade los listeners.
 * Si el formulario no existe (estamos en login.html), no hace nada.
 */
function iniciarRegistro() {
    const form = document.getElementById('form-registro');
    if (!form) return;   // No estamos en registro.html, salimos

    const btn = document.getElementById('btn-submit-registro');
    if (btn) btn.dataset.textoOriginal = btn.textContent;

    // ── Listener de contraseña en tiempo real ────────────────────────────
    // El evento 'input' se dispara con cada pulsación de tecla.
    // Actualiza los indicadores visuales sin esperar al submit.
    const inputPassword = document.getElementById('registro-password');
    if (inputPassword) {
        inputPassword.addEventListener('input', () => {
            actualizarIndicadoresPassword(inputPassword.value);
        });
    }

    // ── Listener del formulario ──────────────────────────────────────────
    form.addEventListener('submit', async (evento) => {
        evento.preventDefault();

        // ── Paso 1: Leer valores ──────────────────────────────────────────
        const email    = document.getElementById('registro-email').value.trim();
        const password = document.getElementById('registro-password').value;
        // El campo nombre es solo visual, no se envía al backend

        // ── Paso 2: Validación client-side ────────────────────────────────
        let hayErrores = false;

        if (!esEmailValido(email)) {
            mostrarError('error-email-reg', true);
            hayErrores = true;
        } else {
            mostrarError('error-email-reg', false);
        }

        const requisitos = cumpleRequisitosPassword(password);
        if (!todosRequisitosOk(requisitos)) {
            mostrarError('error-password-reg', true);
            hayErrores = true;
        } else {
            mostrarError('error-password-reg', false);
        }

        if (hayErrores) return;

        // ── Paso 3: Ocultar alertas previas y deshabilitar botón ─────────
        mostrarAlerta('registro-alerta', false);
        mostrarAlerta('registro-ok', false);
        setBtnCargando('btn-submit-registro', true);

        try {
            // ── Paso 4: Petición POST /auth/registro ──────────────────────
            /**
             * El backend espera { email, password }.
             * Respuesta correcta: 201 Created con { id_usuario, email, rol, ... }
             * Respuesta de error: 400 Bad Request si el email ya existe.
             *
             * NOTA: El campo "nombre" del formulario NO se envía porque
             * el schema RegistroIn del backend solo tiene email y password.
             * Si en el futuro el backend añade el campo nombre, bastará
             * con incluirlo en el objeto del body.
             */
            const respuesta = await fetch(`${API_URL}/auth/registro`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            if (!respuesta.ok) {
                const errorData = await respuesta.json().catch(() => ({}));
                const mensaje = errorData.mensaje || 'No se pudo crear la cuenta. Inténtalo de nuevo.';
                mostrarAlerta('registro-alerta', true, mensaje);
                return; // detail por mensaje
            }

            // ── Paso 5: Mostrar éxito y redirigir ─────────────────────────
            /**
             * No guardamos el token aquí. El registro solo CREA la cuenta.
             * El usuario debe hacer login a continuación para obtener su token.
             * Esto es el flujo estándar: Registro → Login → Token.
             */
            mostrarAlerta('registro-ok', true, 'Cuenta creada correctamente. Redirigiendo al login...');

            // Esperamos 2 segundos para que el usuario pueda leer el mensaje
            // y luego redirigimos a login.html
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);

        } catch (error) {
            console.error('Error en registro:', error);
            mostrarAlerta('registro-alerta', true, 'No se pudo conectar con el servidor. Comprueba que el backend está activo.');

        } finally {
            setBtnCargando('btn-submit-registro', false);
        }
    });
}


// ─────────────────────────────────────────────────────────────
// PUNTO DE ENTRADA
// ─────────────────────────────────────────────────────────────

/**
 * DOMContentLoaded: esperamos a que el DOM esté listo y luego
 * intentamos inicializar ambos módulos.
 * Cada módulo se inicia solo si encuentra su formulario en el DOM.
 * En login.html se activa iniciarLogin().
 * En registro.html se activa iniciarRegistro().
 */
document.addEventListener('DOMContentLoaded', () => {
    iniciarLogin();
    iniciarRegistro();
});
