/**
 * utils.js — Utilidades compartidas del frontend
 *
 * · Toggle mostrar/ocultar contraseña para cualquier campo con `.btn-ojo`.
 * · Reglas de contraseña segura, compartidas por los formularios que la piden.
 * Usado en: login.html, privado.html, reset-password.html, admin.html
 *
 * No realiza llamadas a la API.
 */

/**
 * cumpleRequisitosPassword(password)
 * Comprueba los cuatro requisitos, uno a uno, para poder señalar cuál falla.
 * Deben coincidir con los del backend (validar_password_segura en schemas.py):
 * si divergen, la usuaria vería el formulario en verde y el servidor lo
 * rechazaría igualmente con un 422.
 *
 * @param {string} password
 * @returns {{longitud: boolean, mayuscula: boolean, minuscula: boolean, numero: boolean}}
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
 * @param {object} requisitos - Resultado de cumpleRequisitosPassword()
 * @returns {boolean}
 */
function todosRequisitosOk(requisitos) {
    return Object.values(requisitos).every(Boolean);
}
const _SVG_OJO = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
const _SVG_OJO_CERRADO = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`;

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.btn-ojo').forEach(btn => {
        btn.innerHTML = _SVG_OJO;
        btn.addEventListener('click', () => {
            const input = btn.closest('.campo-password-wrapper').querySelector('input');
            const mostrar = input.type === 'password';
            input.type = mostrar ? 'text' : 'password';
            btn.innerHTML = mostrar ? _SVG_OJO_CERRADO : _SVG_OJO;
            btn.setAttribute('aria-label', mostrar ? 'Ocultar contraseña' : 'Mostrar contraseña');
        });
    });
});
