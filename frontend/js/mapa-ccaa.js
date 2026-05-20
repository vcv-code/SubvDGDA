/*
 * mapa-ccaa.js — Choropleth Leaflet de CCAA por importe concedido
 *
 * Uso: llamar a pintarMapaCCAA(porCcaa) pasando el array
 *      por_ccaa de GET /estadisticas/eell.
 *
 * Requiere:
 *   · Leaflet 1.9.4 cargado antes que este script
 *   · /assets/geojson/ccaa.geojson con propiedad "name" alineada con la API
 *   · Un div #mapa-ccaa en el HTML
 */

'use strict';

let _mapaInstancia = null;


/**
 * pintarMapaCCAA(porCcaa)
 * Choropleth Leaflet en #mapa-ccaa coloreado por importe_total.
 * Escala de quintiles reales del dataset (p20/p40/p60/p80).
 * Paleta de tonos tierra. Hover oscurece el color propio. Clic abre modal top municipios.
 *
 * @param {Array} porCcaa - [{ ccaa, importe_total, num_concesiones }, ...]
 */
async function pintarMapaCCAA(porCcaa, onClickCCAA) {
    if (_mapaInstancia) return;

    const contenedor = document.getElementById('mapa-ccaa');
    if (!contenedor || typeof L === 'undefined') return;
    if (!porCcaa || !porCcaa.length) return;

    const lookup = {};
    porCcaa.forEach(d => { lookup[d.ccaa] = d; });

    const importes = porCcaa.map(d => d.importe_total).filter(v => v > 0);
    const sorted   = [...importes].sort((a, b) => a - b);
    const n        = sorted.length;
    const cuartil  = p => sorted[Math.min(Math.floor(p * n), n - 1)];

    // Redondear a número "bonito" según magnitud
    function redondear(v) {
        if (v >= 1000000) return Math.round(v / 100000) * 100000;
        if (v >= 500000)  return Math.round(v / 50000)  * 50000;
        if (v >= 100000)  return Math.round(v / 25000)  * 25000;
        return Math.round(v / 5000) * 5000;
    }

    // 4 bandas: 3 umbrales en p25, p50, p75
    const umbrales = [
        redondear(cuartil(0.25)),
        redondear(cuartil(0.50)),
        redondear(cuartil(0.75)),
    ];

    // Paleta tierra: beige → caramelo → marrón
    function getColor(valor) {
        if (!valor || valor <= 0) return '#CC0000';
        if (valor > umbrales[2])  return '#5C2C0A';
        if (valor > umbrales[1])  return '#8B5216';
        if (valor > umbrales[0])  return '#C8924A';
        return '#E8D5B4';
    }

    // Oscurece un color hex entre 0 (negro) y 1 (original)
    function oscurecer(hex, factor) {
        var r = Math.round(parseInt(hex.slice(1,3), 16) * factor);
        var g = Math.round(parseInt(hex.slice(3,5), 16) * factor);
        var b = Math.round(parseInt(hex.slice(5,7), 16) * factor);
        return '#' + [r, g, b].map(function(v) {
            return Math.min(255, v).toString(16).padStart(2, '0');
        }).join('');
    }

    function fmtEuro(valor) {
        const num = Math.round(Number(valor));
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' €';
    }

    function fmtK(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + ' M';
        if (num >= 1000)    return (num / 1000).toFixed(0) + ' K';
        return num;
    }

    let geojsonData;
    try {
        const resp = await fetch('/assets/geojson/ccaa.geojson');
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        geojsonData = await resp.json();
    } catch (e) {
        console.error('pintarMapaCCAA: error al cargar GeoJSON:', e);
        contenedor.innerHTML =
            '<p class="estado-error" style="padding:1rem;text-align:center;">Mapa no disponible.</p>';
        return;
    }

    _mapaInstancia = L.map('mapa-ccaa', {
        center: [40.2, -3.5], zoom: 5.8,
        zoomControl: true, scrollWheelZoom: true, attributionControl: true,
    });
    setTimeout(function() { _mapaInstancia.invalidateSize(true); }, 400);

    // Indicador de nivel de zoom
    var ctrlZoom = L.control({ position: 'topright' });
    ctrlZoom.onAdd = function() {
        var div = L.DomUtil.create('div', 'mapa-zoom-indicator');
        div.textContent = 'Zoom: ' + Math.round(_mapaInstancia.getZoom() * 10) / 10;
        return div;
    };
    ctrlZoom.addTo(_mapaInstancia);
    _mapaInstancia.on('zoom', function() {
        var el = document.querySelector('.mapa-zoom-indicator');
        if (el) el.textContent = 'Zoom: ' + Math.round(_mapaInstancia.getZoom() * 10) / 10;
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
        attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>' +
            ' contributors &copy; <a href="https://carto.com/attributions" target="_blank" rel="noopener">CARTO</a>',
        subdomains: 'abcd', maxZoom: 19,
    }).addTo(_mapaInstancia);

    var capaGeojson;

    function estiloFeature(feature) {
        var datos = lookup[feature.properties.name];
        return {
            fillColor:   getColor(datos ? datos.importe_total : 0),
            fillOpacity: 1,
            color:       '#FFFFFF',
            weight:      1.5,
            opacity:     1,
        };
    }

    function onMouseOver(e) {
        var colorActual = e.target.options.fillColor;
        e.target.setStyle({
            weight:    3,
            color:     '#1A1A1A',
            fillColor: oscurecer(colorActual, 0.72),
        });
        e.target.bringToFront();
    }

    function onEachFeature(feature, capa) {
        var nombre = feature.properties.name;
        var datos  = lookup[nombre];
        var html   = datos
            ? '<strong>' + nombre + '</strong><br>Importe: ' + fmtEuro(datos.importe_total) + '<br>Concesiones: ' + datos.num_concesiones.toLocaleString('es-ES')
            : '<strong>' + nombre + '</strong><br>Sin subvenciones';
        capa.bindTooltip(html, { sticky: true, direction: 'top', offset: [0, -4] });
        capa.on({
            mouseover: onMouseOver,
            mouseout:  function() { capaGeojson.resetStyle(capa); },
            click:     function()  { if (typeof onClickCCAA === 'function') onClickCCAA(nombre); },
        });
    }

    capaGeojson = L.geoJSON(geojsonData, {
        style: estiloFeature, onEachFeature: onEachFeature,
    }).addTo(_mapaInstancia);


    // Leyenda
    var leyenda = L.control({ position: 'bottomright' });
    leyenda.onAdd = function() {
        var div   = L.DomUtil.create('div', 'mapa-leyenda');
        var items = [
            { color: '#E8D5B4', label: '≤ ' + fmtK(umbrales[0]) },
            { color: '#C8924A', label: fmtK(umbrales[0]) + ' – ' + fmtK(umbrales[1]) },
            { color: '#8B5216', label: fmtK(umbrales[1]) + ' – ' + fmtK(umbrales[2]) },
            { color: '#5C2C0A', label: '> ' + fmtK(umbrales[2]) },
            { color: '#CC0000', label: 'Sin subvenciones' },
        ];
        div.innerHTML = '<p class="mapa-leyenda__titulo">Importe (€)</p>' +
            items.map(function(i) {
                return '<div class="mapa-leyenda__fila"><span class="mapa-leyenda__color" style="background:' + i.color + '"></span>' + i.label + '</div>';
            }).join('');
        return div;
    };
    leyenda.addTo(_mapaInstancia);
}
