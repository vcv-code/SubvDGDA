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

        const enlace = document.querySelector('a.btn-login[href="login.html"]');
        if (!enlace) return;
        const li = enlace.closest('li');
        if (!li) return;

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
    }

    function iniciarHamburguesa() {
        const nav = document.querySelector('nav.navbar');
        const btn = document.querySelector('.navbar__hamburger');
        if (!nav || !btn) return;

        btn.addEventListener('click', () => {
            const abierto = nav.classList.toggle('navbar--open');
            btn.setAttribute('aria-expanded', abierto);
        });

        // Cerrar al hacer click en un enlace
        nav.querySelectorAll('.navbar__links a, .navbar__links button').forEach(el => {
            el.addEventListener('click', () => {
                nav.classList.remove('navbar--open');
                btn.setAttribute('aria-expanded', 'false');
            });
        });

        // Cerrar al hacer click fuera
        document.addEventListener('click', e => {
            if (!nav.contains(e.target)) {
                nav.classList.remove('navbar--open');
                btn.setAttribute('aria-expanded', 'false');
            }
        });

        // Cerrar con Escape
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') {
                nav.classList.remove('navbar--open');
                btn.setAttribute('aria-expanded', 'false');
                btn.focus();
            }
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        actualizarNavbar();
        iniciarHamburguesa();
    });
}());
