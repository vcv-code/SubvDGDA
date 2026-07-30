/**
 * navbar.js — Navbar dinámica compartida por todas las páginas
 *
 * Cuando hay token en localStorage, sustituye el botón "Login" por
 * un enlace "Mi perfil" y un botón de cierre de sesión.
 * También gestiona el menú hamburguesa en móvil (≤900px).
 *
 * Endpoint: POST /auth/logout  (fire-and-forget al cerrar sesión)
 */
(function () {
    'use strict';

    function cerrarSesion() {
        const rt = localStorage.getItem('refresh_token');
        if (rt) {
            fetch('/auth/logout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: rt }),
            }).catch(() => {});
        }
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        window.location.href = 'index.html';
    }

    function actualizarNavbar() {
        if (!localStorage.getItem('token')) return;

        const lista = document.querySelector('.navbar__links');
        if (!lista) return;

        // Antes esto sustituía el botón "Acceder" del navbar. Al retirarse ese
        // botón (el acceso vive ahora en el pie), no había nada que sustituir y
        // quien iniciaba sesión se quedaba sin "Mi perfil" ni "Cerrar sesión".
        // Ahora los controles se añaden a la lista.
        //
        // Salvo que la página ya traiga los suyos escritos en el HTML, como
        // admin.html: ahí duplicarlos dejaría dos botones de cerrar sesión.
        if (document.getElementById('btn-cerrar-sesion')) return;
        if (lista.querySelector('.navbar__user-controls')) return;

        const li = document.createElement('li');

        const linkPerfil = document.createElement('a');
        linkPerfil.href = 'privado.html';
        linkPerfil.className = 'navbar__user-link';
        linkPerfil.textContent = 'Mi perfil';

        const linkExclusivo = document.createElement('a');
        linkExclusivo.href = 'exclusivo.html';
        linkExclusivo.className = 'navbar__user-link';
        linkExclusivo.textContent = 'Exclusivo';

        const btnCerrar = document.createElement('button');
        btnCerrar.type = 'button';
        btnCerrar.className = 'btn-login';
        btnCerrar.textContent = 'Cerrar sesión';
        btnCerrar.addEventListener('click', cerrarSesion);

        li.className = 'navbar__user-controls';
        li.replaceChildren(linkPerfil, linkExclusivo, btnCerrar);
        lista.appendChild(li);
    }

    function iniciarHamburguesa() {
        const nav = document.querySelector('nav.navbar');
        const btn = document.querySelector('.navbar__hamburger');
        if (!nav || !btn) return;

        // Elementos que pueden recibir foco dentro de la navbar (logo,
        // enlaces del menú y el propio botón hamburguesa), en orden del
        // DOM y solo los visibles. Se recalcula en cada uso porque el menú
        // de usuario se genera dinámicamente al iniciar sesión y porque en
        // móvil los enlaces solo son visibles con el menú abierto.
        const SELECTOR_FOCO =
            'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';
        function elementosFocables() {
            return Array.from(nav.querySelectorAll(SELECTOR_FOCO))
                .filter(el => el.offsetParent !== null);
        }

        function cerrarMenu() {
            nav.classList.remove('navbar--open');
            btn.setAttribute('aria-expanded', 'false');
        }

        btn.addEventListener('click', () => {
            const abierto = nav.classList.toggle('navbar--open');
            btn.setAttribute('aria-expanded', abierto);
            // Al abrir, llevamos el foco al primer enlace del menú: el botón
            // hamburguesa queda después en el DOM, así que sin esto el Tab
            // saltaría directamente al contenido de la página.
            if (abierto) {
                const primerEnlace = nav.querySelector(
                    '.navbar__links a, .navbar__links button');
                if (primerEnlace) primerEnlace.focus();
            }
        });

        // Cerrar al hacer click en un enlace
        nav.querySelectorAll('.navbar__links a, .navbar__links button').forEach(el => {
            el.addEventListener('click', cerrarMenu);
        });

        // Cerrar al hacer click fuera
        document.addEventListener('click', e => {
            if (!nav.contains(e.target)) cerrarMenu();
        });

        // Teclado: Escape cierra y devuelve el foco al botón. Mientras el
        // menú está abierto, Tab queda atrapado dentro de la navbar y cicla
        // entre sus elementos (trampa de foco, WCAG 2.4.3): así quien navega
        // con teclado no se pierde en el contenido oculto tras el panel.
        document.addEventListener('keydown', e => {
            // Solo actuamos si el menú está abierto: así Escape no roba el
            // foco (p. ej. al cerrar un modal) ni interferimos con el Tab
            // normal de la página cuando el menú está cerrado.
            if (!nav.classList.contains('navbar--open')) return;

            if (e.key === 'Escape') {
                cerrarMenu();
                btn.focus();
                return;
            }
            if (e.key !== 'Tab') return;

            const focables = elementosFocables();
            if (focables.length === 0) return;
            const primero = focables[0];
            const ultimo  = focables[focables.length - 1];

            if (e.shiftKey && document.activeElement === primero) {
                e.preventDefault();
                ultimo.focus();
            } else if (!e.shiftKey && document.activeElement === ultimo) {
                e.preventDefault();
                primero.focus();
            }
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        actualizarNavbar();
        iniciarHamburguesa();
    });
}());
