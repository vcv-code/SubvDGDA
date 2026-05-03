/**
 * recursos.js — Lógica de la página de recursos
 * ─────────────────────────────────────────────────
 * Gestiona la carga y presentación del directorio de
 * organizaciones y recursos de bienestar animal.
 *
 * ESTADO: pendiente de conexión con el backend.
 * El endpoint GET /recursos/ aún no existe.
 * Cuando esté disponible, descomentar la llamada en
 * cargarRecursos() y eliminar la línea de placeholder.
 *
 * ENDPOINT PENDIENTE:
 *   GET /recursos/
 *   Respuesta esperada: [
 *     {
 *       nombre:      string,
 *       url:         string,
 *       descripcion: string,
 *       categoria:   string,
 *       logo:        string | null
 *     },
 *     ...
 *   ]
 */


// ─────────────────────────────────────────────────────────────
// CONFIGURACIÓN
// ─────────────────────────────────────────────────────────────

const API_URL = '';


// ─────────────────────────────────────────────────────────────
// REFERENCIAS AL DOM
// ─────────────────────────────────────────────────────────────

const spinner          = document.getElementById('spinner');
const errorBox         = document.getElementById('error-box');
const errorMensaje     = document.getElementById('error-mensaje');
const errorSugerencia  = document.getElementById('error-sugerencia');
const recursosContenido = document.getElementById('recursos-contenido');
const recursosPlaceholder = document.getElementById('recursos-placeholder');


// ─────────────────────────────────────────────────────────────
// FUNCIÓN PRINCIPAL: cargarRecursos
// ─────────────────────────────────────────────────────────────
/**
 * cargarRecursos()
 * Llama al endpoint GET /recursos/ y pinta las tarjetas
 * de recursos en el contenedor principal.
 *
 * Patrón idéntico al del resto de páginas del proyecto:
 *   1. Mostrar spinner
 *   2. Fetch al endpoint
 *   3. Si !ok → mostrar error-box con mensaje y sugerencia del backend
 *   4. Si ok  → pintar tarjetas en #recursos-contenido
 *   5. Ocultar spinner en finally (siempre, haya éxito o error)
 *
 * TODO: conectar con endpoint real cuando backend lo implemente.
 */
async function cargarRecursos() {
    spinner.style.display = 'block';

    try {

        // TODO: conectar con endpoint real cuando backend lo implemente
        // Descomentar las líneas siguientes cuando GET /recursos/ esté disponible:
        //
        // const respuesta = await fetch(`${API_URL}/recursos/`);
        //
        // if (!respuesta.ok) {
        //     let cuerpo = {};
        //     try { cuerpo = await respuesta.json(); } catch (_) {}
        //     errorMensaje.textContent    = cuerpo.mensaje    || `Error ${respuesta.status}`;
        //     errorSugerencia.textContent = cuerpo.sugerencia || '';
        //     errorBox.style.display      = 'block';
        //     throw new Error(`Error ${respuesta.status}`);
        // }
        //
        // const recursos = await respuesta.json();
        //
        // if (recursos.length === 0) {
        //     mostrarSinResultados();
        // } else {
        //     pintarRecursos(recursos);
        // }

        // Mientras el endpoint no exista, no hacemos nada:
        // el placeholder del HTML permanece visible.

    } catch (error) {
        console.error('Error al cargar recursos:', error);
    } finally {
        spinner.style.display = 'none';
    }
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: pintarRecursos
// Recibe el array de recursos y construye las tarjetas.
// ─────────────────────────────────────────────────────────────
/**
 * pintarRecursos(recursos)
 * Oculta el placeholder, construye una tarjeta por recurso
 * y las inserta en #recursos-contenido.
 *
 * Cada tarjeta muestra:
 *   - Nombre del recurso (enlace a su URL)
 *   - Categoría (badge)
 *   - Descripción
 *   - Logo (si existe)
 *
 * @param {Array} recursos - Array de objetos del endpoint /recursos/
 */
function pintarRecursos(recursos) {
    // Ocultar el placeholder antes de insertar datos reales
    if (recursosPlaceholder) {
        recursosPlaceholder.style.display = 'none';
    }

    // Agrupar por categoría para facilitar la lectura
    const porCategoria = {};
    recursos.forEach(r => {
        const cat = r.categoria || 'Otros';
        if (!porCategoria[cat]) porCategoria[cat] = [];
        porCategoria[cat].push(r);
    });

    // Construir una sección por categoría
    Object.entries(porCategoria).forEach(([categoria, items]) => {
        const seccion = document.createElement('div');
        seccion.className = 'recursos-categoria';

        const titulo = document.createElement('h2');
        titulo.className = 'recursos-categoria__titulo';
        titulo.textContent = categoria;
        seccion.appendChild(titulo);

        const grid = document.createElement('div');
        grid.className = 'grid-3';

        items.forEach(recurso => {
            const tarjeta = crearTarjetaRecurso(recurso);
            grid.appendChild(tarjeta);
        });

        seccion.appendChild(grid);
        recursosContenido.appendChild(seccion);
    });
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: crearTarjetaRecurso
// Construye y devuelve un <article> con los datos del recurso.
// ─────────────────────────────────────────────────────────────
/**
 * crearTarjetaRecurso(recurso)
 * Devuelve un elemento <article class="tarjeta"> con:
 *   - Logo (si existe)
 *   - Nombre como enlace externo
 *   - Descripción
 *
 * @param {Object} recurso - Objeto del endpoint /recursos/
 * @returns {HTMLElement}
 */
function crearTarjetaRecurso(recurso) {
    const article = document.createElement('article');
    article.className = 'card';

    // Logo (opcional)
    if (recurso.logo) {
        const img = document.createElement('img');
        img.src    = recurso.logo;
        img.alt    = `Logo de ${recurso.nombre}`;
        img.style.cssText = 'max-height: 48px; object-fit: contain; margin-bottom: var(--espacio-sm);';
        article.appendChild(img);
    }

    // Nombre como enlace externo
    const enlace = document.createElement('a');
    enlace.href        = recurso.url || '#';
    enlace.textContent = recurso.nombre;
    enlace.target      = '_blank';
    enlace.rel         = 'noopener noreferrer';
    enlace.style.cssText = 'font-weight: 700; color: var(--color-azul); display: block; margin-bottom: var(--espacio-xs);';
    article.appendChild(enlace);

    // Descripción
    if (recurso.descripcion) {
        const desc = document.createElement('p');
        desc.textContent  = recurso.descripcion;
        desc.style.cssText = 'font-size: 0.9rem; color: var(--color-gris-texto); margin: 0;';
        article.appendChild(desc);
    }

    return article;
}


// ─────────────────────────────────────────────────────────────
// FUNCIÓN: mostrarSinResultados
// Muestra un mensaje cuando el endpoint devuelve array vacío.
// ─────────────────────────────────────────────────────────────
function mostrarSinResultados() {
    if (recursosPlaceholder) {
        recursosPlaceholder.querySelector('p').textContent =
            'No hay recursos disponibles en este momento.';
    }
}


// ─────────────────────────────────────────────────────────────
// PUNTO DE ENTRADA
// ─────────────────────────────────────────────────────────────
/**
 * Se llama cuando el DOM está completamente construido.
 * Mismo patrón que home.js, estadisticas.js, etc.
 */
document.addEventListener('DOMContentLoaded', () => {
    cargarRecursos();
});
