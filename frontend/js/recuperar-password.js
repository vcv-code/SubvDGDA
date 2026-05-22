/**
 * recuperar-password.js — Solicitud de recuperación de contraseña
 *
 * Gestiona el formulario de recuperar-password.html.
 * Envía el email al backend; la respuesta es siempre positiva
 * para no revelar si el email está registrado (anti-enumeración).
 *
 * Endpoint: POST /auth/recuperar
 */
const API_URL = '/auth';

const form    = document.getElementById('form-recuperar');
const alerta  = document.getElementById('recuperar-alerta');
const exito   = document.getElementById('recuperar-exito');
const btnEnviar = document.getElementById('btn-recuperar');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    alerta.classList.remove('visible');
    exito.classList.remove('visible');

    const email = document.getElementById('recuperar-email').value.trim();
    if (!email) {
        alerta.textContent = 'Introduce tu correo electrónico.';
        alerta.classList.add('visible');
        return;
    }

    btnEnviar.disabled = true;
    btnEnviar.textContent = 'Enviando...';

    try {
        const resp = await fetch(`${API_URL}/recuperar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email }),
        });

        const datos = await resp.json();

        // Siempre mostramos el mensaje de éxito — el backend no revela
        // si el email existe o no (medida de seguridad)
        form.style.display = 'none';
        exito.textContent = datos.mensaje;
        exito.classList.add('visible');

    } catch {
        alerta.textContent = 'Error de conexión. Inténtalo de nuevo.';
        alerta.classList.add('visible');
        btnEnviar.disabled = false;
        btnEnviar.textContent = 'Enviar enlace';
    }
});
