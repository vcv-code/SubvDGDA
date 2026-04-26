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

const cargando   = document.getElementById("entidad-cargando");
const errorBox   = document.getElementById("entidad-error");
const vacia      = document.getElementById("entidad-vacia");

const tablaWrap  = document.getElementById("entidad-tabla-wrapper");
const tablaBody  = document.getElementById("entidad-tabla-body");

// Si no hay CIF → error
if (!cif) {
    cargando.style.display = "none";
    errorBox.style.display = "";
    errorBox.textContent = "No se proporcionó un CIF válido.";
} else {
    infoCif.textContent = cif;
    cargarHistorial(cif);
}

async function cargarHistorial(cif) {
    try {
        const url = `/solicitudes/?cif=${encodeURIComponent(cif)}`;
        const resp = await fetch(url);

        if (!resp.ok) {
            throw new Error("Error del servidor");
        }

        const solicitudes = await resp.json();

        cargando.style.display = "none";

        if (solicitudes.length === 0) {
            vacia.style.display = "";
            return;
        }

        // Nombre de la entidad (todas las solicitudes tienen el mismo)
        infoNombre.textContent = solicitudes[0].beneficiario.nombre;

        // Pintar tabla
        solicitudes.forEach(s => {
            const tr = document.createElement("tr");

            const anio = s.convocatoria.anio_convocatoria;
            const tipo = s.convocatoria.tipo_convoc.toUpperCase();
            const estado = s.estado;

            const importe = s.importe !== null
                ? new Intl.NumberFormat("es-ES", { maximumFractionDigits: 2 })
                    .format(parseFloat(s.importe)) + " €"
                : "—";

            const expediente = s.num_expediente || "—";

            tr.innerHTML = `
                <td>${anio}</td>
                <td>${tipo}</td>
                <td>${estado}</td>
                <td>${importe}</td>
                <td>${expediente}</td>
            `;

            tablaBody.appendChild(tr);
        });

        tablaWrap.style.display = "";

    } catch (err) {
        cargando.style.display = "none";
        errorBox.style.display = "";
        errorBox.textContent = "No se pudo cargar el historial.";
    }
}
