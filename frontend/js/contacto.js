/**
 * contacto.js — Envío del formulario de contacto (POST /contacto/)
 *
 * Valida en cliente (nombre, email, mensaje y consentimiento), envía el
 * mensaje al backend y muestra feedback. Incluye el campo honeypot
 * `sitio_web` (oculto) que el backend usa para descartar bots.
 *
 * Autocontenido: contacto.html no carga auth.js, así que los pequeños
 * helpers de alerta/error se definen aquí.
 */
(function () {
    'use strict';

    const API_URL = '';

    // Mismo criterio de email que auth.js (validación ligera de cliente; la
    // de verdad la hace EmailStr de Pydantic en el backend).
    function esEmailValido(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function mostrarError(idElemento, visible) {
        const el = document.getElementById(idElemento);
        if (el) el.classList.toggle('visible', visible);
    }

    function mostrarAlerta(idElemento, visible, mensaje) {
        const el = document.getElementById(idElemento);
        if (!el) return;
        if (mensaje) el.textContent = mensaje;
        el.classList.toggle('visible', visible);
    }

    function setBtnCargando(btn, cargando) {
        if (!btn) return;
        btn.disabled = cargando;
        btn.textContent = cargando ? 'Enviando…' : 'Enviar mensaje';
    }

    function iniciar() {
        const form = document.getElementById('form-contacto');
        if (!form) return;
        const btn = document.getElementById('btn-submit-contacto');

        form.addEventListener('submit', async (evento) => {
            evento.preventDefault();

            // ── Leer valores ──────────────────────────────────────────────
            const nombre  = document.getElementById('contacto-nombre').value.trim();
            const email   = document.getElementById('contacto-email').value.trim();
            const mensaje = document.getElementById('contacto-mensaje').value.trim();
            const consent = document.getElementById('contacto-consent').checked;

            // ── Validación client-side (nombre es opcional) ───────────────
            let hayErrores = false;

            const emailOk = esEmailValido(email);
            mostrarError('error-email-contacto', !emailOk);
            if (!emailOk) hayErrores = true;

            const mensajeOk = mensaje.length >= 10;
            mostrarError('error-mensaje-contacto', !mensajeOk);
            if (!mensajeOk) hayErrores = true;

            if (hayErrores) return;

            if (!consent) {
                mostrarAlerta('contacto-alerta', true,
                    'Para enviar el mensaje debes aceptar la política de privacidad.');
                return;
            }

            // ── Ocultar alertas previas y deshabilitar botón ──────────────
            mostrarAlerta('contacto-alerta', false);
            mostrarAlerta('contacto-ok', false);
            setBtnCargando(btn, true);

            try {
                const sitio_web = document.getElementById('hp-sitio-web')?.value ?? '';
                const respuesta = await fetch(`${API_URL}/contacto/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nombre, email, mensaje, sitio_web }),
                });

                if (!respuesta.ok) {
                    const errorData = await respuesta.json().catch(() => ({}));
                    const msg = errorData.mensaje
                        || 'No se pudo enviar el mensaje. Inténtalo de nuevo.';
                    mostrarAlerta('contacto-alerta', true, msg);
                    return;
                }

                const datos = await respuesta.json().catch(() => ({}));
                mostrarAlerta('contacto-ok', true,
                    datos.mensaje || 'Mensaje enviado. ¡Gracias por escribirnos!');
                form.reset();

            } catch (error) {
                console.error('Error en contacto:', error);
                mostrarAlerta('contacto-alerta', true,
                    'No se pudo conectar con el servidor. Inténtalo de nuevo más tarde.');
            } finally {
                setBtnCargando(btn, false);
            }
        });
    }

    document.addEventListener('DOMContentLoaded', iniciar);
}());
