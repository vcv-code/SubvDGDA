/**
 * scroll-arriba.js — Botón flotante "volver arriba" compartido
 *
 * Inyecta un botón fijo en la esquina inferior derecha que solo aparece
 * cuando la persona ha bajado lo suficiente (UMBRAL px). Al pulsarlo,
 * vuelve al principio de la página. El desplazamiento suave lo aporta
 * `scroll-behavior: smooth` definido en el <html> (styles.css).
 *
 * Como se auto-oculta hasta que hay scroll, es inofensivo en páginas
 * cortas: simplemente nunca llega a mostrarse.
 */
(function () {
    'use strict';

    // Píxeles de scroll vertical a partir de los cuales mostramos el botón.
    const UMBRAL = 600;

    function crearBoton() {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn-subir';
        btn.setAttribute('aria-label', 'Volver al principio de la página');
        // Flecha hacia arriba (decorativa: el texto accesible va en aria-label).
        btn.innerHTML = '<span class="btn-subir__icono" aria-hidden="true">↑</span>';

        btn.addEventListener('click', () => {
            window.scrollTo({ top: 0, left: 0 });
        });

        return btn;
    }

    function iniciar() {
        const btn = crearBoton();
        document.body.appendChild(btn);

        let pendiente = false;
        function actualizarVisibilidad() {
            pendiente = false;
            const visible = window.scrollY > UMBRAL;
            btn.classList.toggle('btn-subir--visible', visible);
        }

        window.addEventListener('scroll', () => {
            // Agrupamos en un rAF para no recalcular en cada evento de scroll.
            if (!pendiente) {
                pendiente = true;
                window.requestAnimationFrame(actualizarVisibilidad);
            }
        }, { passive: true });

        actualizarVisibilidad();
    }

    document.addEventListener('DOMContentLoaded', iniciar);
}());
