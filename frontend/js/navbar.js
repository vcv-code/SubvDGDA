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

        const btnCerrar = document.createElement('button');
        btnCerrar.type = 'button';
        btnCerrar.className = 'btn-login';
        btnCerrar.textContent = 'Cerrar sesión';
        btnCerrar.addEventListener('click', cerrarSesion);

        li.className = 'navbar__user-controls';
        li.replaceChildren(linkPerfil, btnCerrar);
    }

    document.addEventListener('DOMContentLoaded', actualizarNavbar);
}());
