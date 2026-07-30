/**
 * modal-grafica.js — Modal de conclusiones por gráfica
 * Compartido por index.html, estadisticas-epas.html y estadisticas-eell.html.
 *
 * API pública:
 *   configurarModal(instanciaChart, titulo, conclusion)
 *     - instanciaChart : instancia Chart.js ya creada
 *     - titulo         : título de la gráfica (cabecera del modal)
 *     - conclusion     : texto interpretativo que se muestra en el modal
 *
 * Añade un botón "¿Qué conclusiones se sacan?" al pie de la tarjeta.
 * Al hacer clic se abre un modal con la gráfica como fondo tenue
 * y el texto de conclusiones encima.
 * Se cierra con el botón ✕, clic en el backdrop o tecla Escape.
 */
(function () {

    function _crearModal() {
        if (document.getElementById('modal-grafica')) return;

        const modal = document.createElement('div');
        modal.id = 'modal-grafica';
        modal.className = 'modal-grafica';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-labelledby', 'modal-grafica-titulo');
        modal.setAttribute('aria-hidden', 'true');
        modal.innerHTML = `
            <div class="modal-grafica__backdrop"></div>
            <div class="modal-grafica__panel">
                <img class="modal-grafica__fondo" id="modal-grafica-fondo" src="" alt="">
                <div class="modal-grafica__contenido">
                    <div class="modal-grafica__cabecera">
                        <h3 class="modal-grafica__titulo" id="modal-grafica-titulo"></h3>
                        <button class="modal-grafica__cerrar" aria-label="Cerrar">&#x2715;</button>
                    </div>
                    <div class="modal-grafica__cuerpo">
                        <div class="modal-grafica__texto" id="modal-grafica-texto"></div>
                    </div>
                </div>
            </div>`;
        document.body.appendChild(modal);

        const cerrar = () => {
            modal.classList.remove('modal-grafica--visible');
            modal.setAttribute('aria-hidden', 'true');
            // Devuelve el foco al botón que abrió el modal (WCAG 2.4.3).
            // Sin esto, al cerrar con teclado el foco vuelve al principio del
            // documento y hay que tabular otra vez hasta donde se estaba.
            if (modal._openerEl) {
                modal._openerEl.focus();
                modal._openerEl = null;
            }
        };

        modal.querySelector('.modal-grafica__backdrop').addEventListener('click', cerrar);
        modal.querySelector('.modal-grafica__cerrar').addEventListener('click', cerrar);
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('modal-grafica--visible')) cerrar();
        });
    }

    window.configurarModal = function (instanciaChart, titulo, conclusion) {
        _crearModal();

        const canvas = instanciaChart.canvas;
        const card   = canvas.closest('.card-grafico');
        if (!card) return;

        const trigger = document.createElement('button');
        trigger.className   = 'card-grafico__trigger';
        trigger.textContent = '¿Qué conclusiones se sacan?';
        card.appendChild(trigger);

        trigger.addEventListener('click', () => {
            const modal = document.getElementById('modal-grafica');
            const fondo = document.getElementById('modal-grafica-fondo');
            const titEl = document.getElementById('modal-grafica-titulo');
            const texEl = document.getElementById('modal-grafica-texto');

            fondo.src        = instanciaChart.toBase64Image('image/png', 1);
            fondo.alt        = titulo;
            titEl.textContent = titulo;
            const tag = document.createElement('span');
            tag.className = 'modal-grafica__titulo-tag';
            tag.textContent = ' — Conclusiones';
            titEl.appendChild(tag);
            texEl.innerHTML  = conclusion;

            modal._openerEl = trigger;
            modal.classList.add('modal-grafica--visible');
            modal.setAttribute('aria-hidden', 'false');
            modal.querySelector('.modal-grafica__cerrar').focus();
        });
    };

}());
