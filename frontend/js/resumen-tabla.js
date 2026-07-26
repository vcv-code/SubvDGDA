/**
 * resumen-tabla.js — Render compartido de la tabla "Resumen por convocatoria"
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * La misma tabla se muestra en dos sitios con datos de idéntica forma
 * (ResumenTablaOut):
 *   · Home (pública)      → GET /estadisticas/resumen-convocatorias  (home.js)
 *   · Exclusivo (login)   → GET /privado/resumen-tabla               (exclusivo.js)
 *
 * Para no duplicar el HTML, ambos llaman a window.renderResumenTabla(datos, cont).
 * Solo pinta; cada página se encarga de su propio fetch.
 *
 * @param {Object} datos       - { filas:[{tipo,anio,total,concedidas,no_beneficiarias,
 *                                 excluidas,desistidas,importe_total}], total_global,
 *                                 concedidas_total, importe_global }
 * @param {HTMLElement} contenedor - dónde inyectar la tabla
 */
window.renderResumenTabla = function (datos, contenedor) {
    if (!contenedor || !datos) return;

    const fmt = (n) => new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n);
    const num = (n) => n.toLocaleString('es-ES');

    const colgroup = `<colgroup>
        <col style="width:10%"><col style="width:7%"><col style="width:9%">
        <col style="width:13%"><col style="width:12%"><col style="width:12%">
        <col style="width:12%"><col style="width:15%">
    </colgroup>`;

    const cabecera = `<tr>
        <th scope="col">Tipo</th><th scope="col">Año</th><th scope="col">Total</th>
        <th scope="col" class="col-sep">Concedidas</th>
        <th scope="col">No benef.</th><th scope="col">Excluidas</th><th scope="col">Desistidas</th>
        <th scope="col" class="col-sep">Importe concedido</th>
    </tr>`;

    const renderFila = (f) => {
        if (f.total === 0) {
            return `<tr class="resumen-tabla__pendiente">
                <td><span class="resumen-tabla__tipo resumen-tabla__tipo--${f.tipo}">${f.tipo.toUpperCase()}</span></td>
                <td>${f.anio}</td>
                <td colspan="6" style="text-align:center;">Resolución pendiente de publicación</td>
            </tr>`;
        }
        return `<tr>
            <td><span class="resumen-tabla__tipo resumen-tabla__tipo--${f.tipo}">${f.tipo.toUpperCase()}</span></td>
            <td>${f.anio}</td>
            <td>${num(f.total)}</td>
            <td class="col-sep">${num(f.concedidas)}</td>
            <td>${num(f.no_beneficiarias)}</td>
            <td>${num(f.excluidas)}</td>
            <td>${num(f.desistidas)}</td>
            <td class="col-sep">${fmt(f.importe_total)}${f.tipo === 'epa' && f.anio === 2021 ? '<sup>*</sup>' : ''}</td>
        </tr>`;
    };

    const renderBloque = (tipo, filasTipo) => {
        const cd = filasTipo.filter(f => f.total > 0);
        const s  = (campo) => cd.reduce((a, f) => a + f[campo], 0);
        const subtotal = cd.length ? `
            <tfoot>
                <tr class="resumen-tabla__subtotal">
                    <td colspan="2">Subtotal ${tipo.toUpperCase()}</td>
                    <td>${num(s('total'))}</td>
                    <td class="col-sep">${num(s('concedidas'))}</td>
                    <td>${num(s('no_beneficiarias'))}</td>
                    <td>${num(s('excluidas'))}</td>
                    <td>${num(s('desistidas'))}</td>
                    <td class="col-sep">${fmt(s('importe_total'))}</td>
                </tr>
            </tfoot>` : '';
        return `
            <div class="resumen-tabla-card">
            <div class="resumen-bloque tabla-scroll">
                <table class="resumen-tabla" aria-label="Solicitudes ${tipo.toUpperCase()}" style="table-layout:fixed;">
                    ${colgroup}<thead>${cabecera}</thead>
                    <tbody>${filasTipo.map(renderFila).join('')}</tbody>
                    ${subtotal}
                </table>
            </div>
            </div>`;
    };

    const filasEpa  = datos.filas.filter(f => f.tipo === 'epa').sort((a, b) => b.anio - a.anio);
    const filasEell = datos.filas.filter(f => f.tipo === 'eell').sort((a, b) => b.anio - a.anio);

    const todosConDatos = datos.filas.filter(f => f.total > 0);
    const totNobenef = todosConDatos.reduce((s, f) => s + f.no_beneficiarias, 0);
    const totExcl    = todosConDatos.reduce((s, f) => s + f.excluidas, 0);
    const totDesist  = todosConDatos.reduce((s, f) => s + f.desistidas, 0);

    contenedor.innerHTML = `
        <div class="resumen-grupos">
            ${renderBloque('epa', filasEpa)}
            <!-- Nota del asterisco del importe de 2021 (EPA), justo bajo su tabla.
                 Texto editorial FIJO; revisar si cambian los presupuestos. -->
            <p class="nota-asterisco">
                <span aria-hidden="true">*</span> En 2021, primer año de la convocatoria, el presupuesto ascendía a 3 millones de euros; sin embargo, la escasa difusión y la complejidad del procedimiento provocaron un número reducido de solicitudes, por lo que gran parte de los fondos quedó sin adjudicar. Al año siguiente el presupuesto se redujo en un millón y, pese al posterior aumento de solicitudes, no ha vuelto a ampliarse. Sería deseable que se incremente en próximas convocatorias.
            </p>
            ${renderBloque('eell', filasEell)}
            <div class="resumen-tabla-card">
            <div class="resumen-bloque resumen-bloque--total tabla-scroll">
                <table class="resumen-tabla" aria-label="Total global" style="table-layout:fixed;">
                    ${colgroup}
                    <thead>${cabecera}</thead>
                    <tbody>
                        <tr class="resumen-tabla__totales">
                            <td colspan="2">TOTAL GLOBAL</td>
                            <td>${num(datos.total_global)}</td>
                            <td class="col-sep">${num(datos.concedidas_total)}</td>
                            <td>${num(totNobenef)}</td>
                            <td>${num(totExcl)}</td>
                            <td>${num(totDesist)}</td>
                            <td class="col-sep">${fmt(datos.importe_global)}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            </div>
        </div>`;
};
