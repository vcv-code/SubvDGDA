/**
 * reset-password.js — Restablecimiento de contraseña
 *
 * Gestiona reset-password.html. Lee el token de la URL (?token=),
 * valida que exista antes de mostrar el formulario y envía la nueva
 * contraseña al backend. El token se revoca tras el primer uso.
 *
 * Endpoint: POST /auth/reset
 */
const API_URL = '/auth';

const form      = document.getElementById('form-reset');
const alerta    = document.getElementById('reset-alerta');
const exito     = document.getElementById('reset-exito');
const btnReset  = document.getElementById('btn-reset');
const enlaceVolver = document.getElementById('reset-volver');

// Leer el token de la URL: reset-password.html?token=abc123
const token = new URLSearchParams(window.location.search).get('token');

if (!token) {
    alerta.textContent = 'Enlace inválido. Solicita uno nuevo desde la página de recuperación.';
    alerta.classList.add('visible');
    form.style.display = 'none';
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    alerta.classList.remove('visible');

    const pass1 = document.getElementById('reset-password').value;
    const pass2 = document.getElementById('reset-password2').value;

    if (pass1 !== pass2) {
        alerta.textContent = 'Las contraseñas no coinciden.';
        alerta.classList.add('visible');
        return;
    }

    btnReset.disabled = true;
    btnReset.textContent = 'Guardando...';

    try {
        const resp = await fetch(`${API_URL}/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, contrasena_nueva: pass1 }),
        });

        const datos = await resp.json();

        if (!resp.ok) {
            const msg = datos.mensaje ?? 'Enlace inválido o expirado.';
            alerta.textContent = msg;
            alerta.classList.add('visible');
            btnReset.disabled = false;
            btnReset.textContent = 'Guardar nueva contraseña';
            return;
        }

        form.style.display = 'none';
        exito.textContent = datos.mensaje + ' Ya puedes iniciar sesión con tu nueva contraseña.';
        exito.classList.add('visible');
        enlaceVolver.style.display = 'block';

    } catch {
        alerta.textContent = 'Error de conexión. Inténtalo de nuevo.';
        alerta.classList.add('visible');
        btnReset.disabled = false;
        btnReset.textContent = 'Guardar nueva contraseña';
    }
});
