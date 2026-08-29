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
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' €';
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

    // pointer:coarse = dedo es el puntero principal (móvil/tablet puro)
    // pointer:fine   = ratón o trackpad (laptop, aunque tenga pantalla táctil)
    var esTactilPrimario = window.matchMedia('(pointer: coarse)').matches;
    _mapaInstancia = L.map('mapa-ccaa', {
        center: [40.2, -3.5], zoom: 5.8,
        // minZoom se recalcula más abajo, en cuanto se sabe el tamaño real del
        // contenedor: este 2 solo vale para el instante inicial. maxZoom 8
        // porque por encima el GeoJSON ya no da más detalle.
        minZoom: 2, maxZoom: 8,
        zoomControl: true, scrollWheelZoom: true, attributionControl: true,
        doubleClickZoom: !esTactilPrimario,
    });
    // Subir el pane del tooltip por encima de los controles (zoom, leyenda)
    _mapaInstancia.getPane('tooltipPane').style.zIndex = 1050;
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

    // SIN mapa base, a propósito. Antes se cargaban las teselas de CARTO, y en
    // agosto de 2026 empezaron a exigir clave: el mapa pasó a mostrarse cubierto
    // de marcas de agua «API KEY REQUIRED» sin que aquí hubiera cambiado nada.
    //
    // No se sustituye por otro proveedor. Para un mapa de «qué comunidad recibió
    // cuánto» el fondo no aporta —solo pinta el mar y los países vecinos—, las
    // comunidades salen del GeoJSON local, y prescindir de él quita de encima
    // una dependencia externa que puede volver a cambiar de reglas. De paso
    // evita que el navegador de cada visitante se conecte a un tercero, que es
    // coherente con lo que la web declara sobre privacidad.
    //
    // El fondo del contenedor lo pone el CSS (#mapa-ccaa).

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
        // El tooltip de Leaflet SOLO en ratón. En táctil no se enlaza siquiera,
        // en lugar de enlazarlo y deshacerlo después: `unbindTooltip()` pone
        // `_tooltip` a null pero NO retira los escuchadores de foco que
        // `bindTooltip()` deja sobre el <path> del SVG. Al recibir foco una
        // comunidad, ese escuchador huérfano hace `this._tooltip._source = ...`
        // sobre null y revienta con "Cannot set properties of null".
        if (!esTactilPrimario) {
            capa.bindTooltip(html, { sticky: true, direction: 'auto', offset: [0, -4] });
        }
        capa.on({
            mouseover: onMouseOver,
            mouseout:  function() { capaGeojson.resetStyle(capa); },
            click:     function() {
                // En touch el modal lo gestiona el timer del touchstart
                if (esTactilPrimario) return;
                if (typeof onClickCCAA === 'function') onClickCCAA(nombre);
            },
        });
    }

    capaGeojson = L.geoJSON(geojsonData, {
        style: estiloFeature, onEachFeature: onEachFeature,
    }).addTo(_mapaInstancia);

    // En móvil ajustar vista para que España quepa completa
    if (window.innerWidth <= 768) {
        _mapaInstancia.fitBounds(capaGeojson.getBounds(), { padding: [8, 8] });
    }

    // Topes de alejamiento y desplazamiento.
    //
    // Desde que no hay mapa base, alejarse más allá de donde ya cabe todo no
    // enseña nada: solo el gris del contenedor, porque alrededor de las
    // comunidades no queda nada que mirar. Así que el mínimo se calcula, no se
    // fija a ojo: `getBoundsZoom` devuelve el nivel exacto al que entra la
    // extensión completa —Canarias incluida, que es la que manda porque queda
    // muy al suroeste— y se toma ése como suelo.
    //
    // Se calcula en vez de codificarlo porque depende del tamaño del
    // contenedor, y no es el mismo en escritorio (640 px de alto) que en móvil
    // (400 px). Un número fijo acertaría en uno y fallaría en el otro.
    var limitesEspana = capaGeojson.getBounds();

    // Se recalcula en CADA cambio de tamaño, no solo al cargar. El contenedor
    // mide 640, 400 o 320 px de alto según la pantalla (ver #mapa-ccaa en
    // styles.css), y a menor altura hace falta un zoom MENOR para que quepa lo
    // mismo. Con un único cálculo inicial, estrechar la ventana desde
    // escritorio dejaba un mínimo demasiado alto: España ya no cabía y encima
    // no se podía alejar para verla, que es justo lo contrario de lo que este
    // tope pretende.
    function ajustarTopes() {
        // invalidateSize primero: si el contenedor acaba de cambiar de tamaño,
        // Leaflet todavía arrastra el anterior y el cálculo saldría mal.
        _mapaInstancia.invalidateSize(false);

        var zMin = _mapaInstancia.getBoundsZoom(limitesEspana, false, [12, 12]);
        _mapaInstancia.setMinZoom(zMin);
        // Margen holgado a propósito. En una pantalla ancha, al zoom mínimo
        // el mapa abarca más longitud de la que ocupa España —la altura es lo
        // que limita, no el ancho—, y un margen ajustado quedaría más estrecho
        // que la propia vista: Leaflet entonces centra y bloquea el arrastre,
        // que se siente como si el mapa se resistiera. Con 0.5 hay sitio de
        // sobra y solo actúa cuando de verdad se está perdiendo España de vista.
        _mapaInstancia.setMaxBounds(limitesEspana.pad(0.5));

        // Si al encoger la ventana el mapa se queda por debajo del nuevo suelo,
        // se sube. Leaflet ya lo hace en `setMinZoom`, pero dejarlo explícito
        // evita depender de un detalle de su implementación.
        if (_mapaInstancia.getZoom() < zMin) _mapaInstancia.setZoom(zMin);
    }

    ajustarTopes();

    // Con retardo: al arrastrar el borde de la ventana, `resize` se dispara
    // decenas de veces por segundo, y recalcular en cada una haría dar saltos
    // al mapa. El mapa se crea una sola vez (`if (_mapaInstancia) return` al
    // principio), así que este escuchador no se duplica.
    var temporizadorTopes;
    window.addEventListener('resize', function() {
        clearTimeout(temporizadorTopes);
        temporizadorTopes = setTimeout(ajustarTopes, 200);
    });

    // Solo móvil: 1 toque = info centrada; 2 toques = modal
    if (esTactilPrimario) {
        var hintEl   = document.querySelector('.mapa-ccaa-hint');
        var hintBase = hintEl ? hintEl.textContent : '';
        var ultimoToque = { layer: null, tiempo: 0 };
        var timerInfo = null;
        // 600 ms, no 400: quien no sabe que hay que tocar dos veces lo hace
        // despacio, y con el umbral corto sus dos toques contaban como dos
        // toques sueltos. El botón de la caja es ahora la vía principal;
        // esto solo hace más tolerante el atajo.
        var DOBLE_TOQUE_MS = 600;

        // Caja de info centrada — reemplaza el tooltip de Leaflet en móvil
        var infoBox = document.createElement('div');
        infoBox.className = 'mapa-info-central';
        infoBox.style.display = 'none';
        var wrapper = document.getElementById('mapa-ccaa').parentElement;
        wrapper.appendChild(infoBox);

        function mostrarInfo(layer, datos) {
            var nombre = layer.feature.properties.name;
            infoBox.innerHTML = (datos
                ? '<strong>' + nombre + '</strong><br>'
                  + 'Importe: ' + fmtEuro(datos.importe_total) + '<br>'
                  + 'Concesiones: ' + datos.num_concesiones.toLocaleString('es-ES')
                : '<strong>' + nombre + '</strong><br>Sin subvenciones')
                // Botón explícito. El doble toque sigue funcionando, pero es un
                // gesto que nadie adivina: sin esto, en móvil la única forma de
                // llegar al detalle era una interacción oculta, y quedaba menos
                // información que en escritorio pulsando una vez.
                + '<button type="button" class="mapa-info-central__ver">'
                + 'Ver top de municipios →</button>';

            var boton = infoBox.querySelector('.mapa-info-central__ver');
            boton.addEventListener('click', function(ev) {
                ev.stopPropagation();
                clearTimeout(timerInfo);
                ocultarInfo();
                capaGeojson.resetStyle(layer);
                ultimoToque = { layer: null, tiempo: 0 };
                if (hintEl) hintEl.textContent = hintBase;
                if (typeof onClickCCAA === 'function') onClickCCAA(nombre);
            });

            infoBox.style.display = 'block';
        }

        function ocultarInfo() {
            infoBox.style.display = 'none';
        }

        capaGeojson.eachLayer(function(layer) {
            var el = layer.getElement();
            if (!el) return;
            var layerNombre = layer.feature.properties.name;
            var datosCCAA   = lookup[layerNombre];

            el.addEventListener('touchend', function() {
                var ahora   = Date.now();
                var esDoble = ultimoToque.layer === layer &&
                              (ahora - ultimoToque.tiempo) < DOBLE_TOQUE_MS;

                if (esDoble) {
                    clearTimeout(timerInfo);
                    ocultarInfo();
                    capaGeojson.resetStyle(layer);
                    ultimoToque = { layer: null, tiempo: 0 };
                    if (hintEl) hintEl.textContent = hintBase;
                    if (typeof onClickCCAA === 'function') onClickCCAA(layerNombre);
                } else {
                    if (ultimoToque.layer && ultimoToque.layer !== layer) {
                        capaGeojson.resetStyle(ultimoToque.layer);
                    }
                    clearTimeout(timerInfo);
                    onMouseOver({ target: layer });
                    mostrarInfo(layer, datosCCAA);
                    if (hintEl) hintEl.textContent = 'Pulsa «Ver top de municipios» para el detalle.';
                    ultimoToque = { layer: layer, tiempo: ahora };
                    timerInfo = setTimeout(function() {
                        ocultarInfo();
                        capaGeojson.resetStyle(layer);
                        ultimoToque = { layer: null, tiempo: 0 };
                        if (hintEl) hintEl.textContent = hintBase;
                    }, 8000);
                }
            }, { passive: true });
        });
    }


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
