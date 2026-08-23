/**
 * entidad.js — Historial de solicitudes por CIF
 * ------------------------------------------------
 * Lee el parámetro ?cif= de la URL, llama al backend
 * y pinta todas las solicitudes de esa entidad.
 */

const params = new URLSearchParams(window.location.search);
const cif = params.get("cif");

// Referencias al DOM
const infoNombre = document.getElementById("entidad-nombre");
const infoCif    = document.getElementById("entidad-cif");
const infoUbic   = document.getElementById("entidad-ubicacion");
const infoProv   = document.getElementById("entidad-provincia");

const cargando   = document.getElementById("entidad-cargando");
const errorBox   = document.getElementById("entidad-error");
const vacia      = document.getElementById("entidad-vacia");

const tablaWrap  = document.getElementById("entidad-tabla-wrapper");
const tablaBody  = document.getElementById("entidad-tabla-body");

// Referencias al bloque de agrupación (Paso 16)
const agrupacionDetalle      = document.getElementById("agrupacion-detalle");
const agrupacionRepresentante = document.getElementById("agrupacion-representante");
const agrupacionNumMunicipios = document.getElementById("agrupacion-num-municipios");
const agrupacionMiembros     = document.getElementById("agrupacion-miembros");

// Si no hay CIF → error
if (!cif) {
    cargando.style.display = "none";
    errorBox.style.display = "";
    errorBox.textContent = "No se proporcionó un CIF válido.";
} else {
    infoCif.textContent = cif;
    cargarHistorial(cif);
}

function badgeEstadoHtml(estado) {
    const mapa = {
        'concedida':       { texto: 'Concedida',       clase: 'badge-concedida' },
        'no_beneficiaria': { texto: 'No beneficiaria', clase: 'badge-no-beneficiaria' },
        'excluida':        { texto: 'Excluida',         clase: 'badge-excluida' },
        'desistida':       { texto: 'Desistida',        clase: 'badge-desistida' },
    };
    const info = mapa[estado] || { texto: estado, clase: '' };
    return `<span class="badge ${info.clase}">${info.texto}</span>`;
}

async function cargarHistorial(cif) {
    document.getElementById('spinner').style.display = 'block';
    try {
        const url = `/solicitudes/?cif=${encodeURIComponent(cif)}`;
        const resp = await fetch(url);

        if (!resp.ok) {
            let cuerpo = {};
            try { cuerpo = await resp.json(); } catch (_) {}
            const errorBox        = document.getElementById('error-box');
            const errorMensaje    = document.getElementById('error-mensaje');
            const errorSugerencia = document.getElementById('error-sugerencia');
            if (errorBox) {
                errorMensaje.textContent    = cuerpo.mensaje    || `Error ${resp.status}`;
                errorSugerencia.textContent = cuerpo.sugerencia || '';
                cargando.style.display      = 'none';
                errorBox.style.display      = 'block';
            }
            throw new Error("Error del servidor");
        }

        const { resultados: solicitudes } = await resp.json();

        cargando.style.display = "none";

        if (solicitudes.length === 0) {
            vacia.style.display = "";
            return;
        }

        // Nombre de la entidad (todas las solicitudes tienen el mismo)
        infoNombre.textContent = solicitudes[0].beneficiario.nombre;

        // Ubicación: solo la traen las EELL, donde se deriva del CIF. Sirve para
        // desambiguar los municipios que el BOE nombra abreviados —«El Cuervo»,
        // «La Mata», «Burguillos», «La Frontera»—, que existen en más de una
        // provincia. Se busca en todas las solicitudes porque una entidad puede
        // tener años EPA (sin provincia) y años EELL (con ella).
        const conUbicacion = solicitudes.find(s => s.provincia);
        if (conUbicacion && infoUbic) {
            infoProv.textContent = conUbicacion.ccaa
                ? `${conUbicacion.provincia} (${conUbicacion.ccaa})`
                : conUbicacion.provincia;
            infoUbic.hidden = false;
        }

        // Pintar tabla
        solicitudes.forEach(s => {
            const tr = document.createElement("tr");

            const anio = s.convocatoria.anio_convocatoria;
            const tipo = s.convocatoria.tipo_convoc.toUpperCase();
            const estado = s.estado;

            const importe = s.importe !== null
                ? new Intl.NumberFormat("es-ES", { maximumFractionDigits: 2 })
                    .format(parseFloat(s.importe)) + " €"
                : "—";

            const tramoBadge = s.tramo !== null && s.tramo !== undefined
                ? `<span class="badge-tramo">T${s.tramo}</span>`
                : "";

            const expediente = s.num_expediente || "—";

            // `data-label` no es decorativo: en móvil la tabla se convierte en
            // tarjetas y el CSS pinta ese atributo como etiqueta a la izquierda
            // de cada valor. Sin él queda un hueco vacío y el dato suelto a la
            // derecha, que es como se veía antes.
            tr.innerHTML = `
                <td data-label="Año">${anio}</td>
                <td data-label="Tipo">${tipo}</td>
                <td data-label="Estado">${badgeEstadoHtml(estado)}</td>
                <td data-label="Importe">${importe}${tramoBadge}</td>
                <td data-label="Expediente">${expediente}</td>
            `;

            tablaBody.appendChild(tr);

            // Si la solicitud pertenece a una agrupación, cargamos el desglose
            if (s.es_agrupacion === true) {
                cargarAgrupacion(s.id_solic);
            }
        });

        tablaWrap.style.display = "";

        // Leyenda de tramos: solo si alguna solicitud tiene tramo
        const leyenda = document.getElementById('leyenda-tramos');
        if (leyenda && solicitudes.some(s => s.tramo !== null && s.tramo !== undefined)) {
            leyenda.style.display = '';
        }

    } catch (err) {
        cargando.style.display = "none";
        errorBox.style.display = "";
        errorBox.textContent = "No se pudo cargar el historial.";
    } finally {
        document.getElementById('spinner').style.display = 'none';
    }
}


/**
 * cargarAgrupacion(idSolic)
 * Llama a GET /agrupaciones/{id_solic} y muestra el desglose
 * de municipios miembro de la agrupación EELL.
 *
 * Respuesta esperada del backend:
 *   {
 *     representante: string,
 *     num_municipios: number,
 *     miembros: [{ nombre, cif, importe }, ...]
 *   }
 */
async function cargarAgrupacion(idSolic) {
    try {
        const resp = await fetch(`/agrupaciones/${idSolic}`);
        if (!resp.ok) return;  // Si el backend aún no tiene el endpoint, no rompemos la página

        const datos = await resp.json();

        // Rellenar datos del bloque
        agrupacionRepresentante.textContent =
            `Entidad representante: ${datos.representante?.nombre || '—'}`;
        agrupacionNumMunicipios.textContent =
            `Número de municipios: ${datos.num_municipios ?? '—'}`;

        // Pintar filas de miembros
        const tbody = agrupacionMiembros.querySelector("tbody");
        tbody.innerHTML = "";
        (datos.miembros || []).forEach(m => {
            const importe = m.importe_asignado !== null && m.importe_asignado !== undefined
                ? new Intl.NumberFormat("es-ES", { maximumFractionDigits: 2 })
                    .format(parseFloat(m.importe_asignado)) + " €"
                : "—";
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${m.nombre || '—'}</td>
                <td>${m.cif    || '—'}</td>
                <td>${importe}</td>
            `;
            tbody.appendChild(tr);
        });

        // Mostrar el bloque
        agrupacionDetalle.style.display = "block";

    } catch (err) {
        // Error silencioso: el bloque queda oculto si el endpoint falla
        agrupacionDetalle.style.display = "none";
    }
}
