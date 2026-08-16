"""
Tests de la configuración TLS de Nginx.

Protegen el montaje que permite que el servidor sea una copia limpia del
repositorio: las rutas del certificado son lo único que difiere entre
desarrollo y producción, y viven en un fichero aparte que se sustituye por
docker-compose.override.yml.

Son comprobaciones de ficheros, no necesitan Docker.
"""
import re
from pathlib import Path

RAIZ     = Path(__file__).parent.parent
NGINX    = RAIZ / "docker/nginx/default.conf"
TLS_DEV  = RAIZ / "docker/nginx-tls/dev.conf"
COMPOSE  = RAIZ / "docker/docker-compose.yml"
EJEMPLO  = RAIZ / "docker/docker-compose.override.yml.example"
GITIGNORE = RAIZ / ".gitignore"


# ── El reto de Let's Encrypt ────────────────────────────────────────────────

def _bloque_http():
    """El server que escucha en el puerto 80."""
    t = NGINX.read_text(encoding="utf-8")
    i = t.index("listen 80;")
    return t[i:t.index("\n}", i)]


def test_la_ruta_del_reto_acme_existe():
    """Sin ella, certbot no puede validar el dominio ni renovar."""
    assert "/.well-known/acme-challenge/" in _bloque_http()


def test_el_reto_va_antes_de_la_redireccion_a_https():
    """El reto viaja por HTTP: si lo alcanza el `return 301`, la validación
    fracasa. Y fracasaría al RENOVAR, tres meses después de tocarlo."""
    bloque = _bloque_http()
    assert bloque.index("acme-challenge") < bloque.index("return 301")


def test_el_reto_se_sirve_desde_la_carpeta_de_certbot():
    bloque = _bloque_http()
    i = bloque.index("acme-challenge")
    assert "/var/www/certbot" in bloque[i:i + 200]


# ── Las rutas del certificado, fuera del fichero principal ──────────────────

def test_default_conf_no_lleva_rutas_de_certificado_escritas():
    """Si volvieran aquí, el servidor tendría que editar un fichero versionado
    y `git pull` chocaría en cada actualización."""
    t = NGINX.read_text(encoding="utf-8")
    for linea in t.splitlines():
        limpia = linea.strip()
        if limpia.startswith("#"):
            continue
        assert not limpia.startswith("ssl_certificate"), limpia


def test_default_conf_incluye_la_carpeta_tls():
    assert re.search(r'^\s*include\s+/etc/nginx/tls/\*\.conf;',
                     NGINX.read_text(encoding="utf-8"), re.M)


def test_el_repositorio_trae_el_certificado_de_desarrollo():
    """El `include` con comodín no falla si no hay ficheros, pero entonces
    Nginx arrancaría sin certificado y el bloque HTTPS no funcionaría."""
    t = TLS_DEV.read_text(encoding="utf-8")
    assert "ssl_certificate" in t and "/etc/nginx/ssl/server.crt" in t
    assert "ssl_certificate_key" in t


# ── El montaje ──────────────────────────────────────────────────────────────

def test_compose_monta_la_carpeta_tls():
    assert "./nginx-tls:/etc/nginx/tls" in COMPOSE.read_text(encoding="utf-8")


def test_la_configuracion_del_servidor_esta_ignorada_por_git():
    """Es lo que permite que el servidor haga `git pull` sin conflictos."""
    t = GITIGNORE.read_text(encoding="utf-8")
    assert "docker/docker-compose.override.yml" in t
    assert "docker/nginx-tls-prod/" in t


def test_hay_un_ejemplo_del_override_de_produccion():
    """Sin él, rehacer el servidor obliga a reconstruir esto de memoria."""
    t = EJEMPLO.read_text(encoding="utf-8")
    assert "/etc/letsencrypt:/etc/letsencrypt:ro" in t
    assert "/var/www/certbot:/var/www/certbot:ro" in t
    assert "./nginx-tls-prod:/etc/nginx/tls:ro" in t


# ─────────────────────────────────────────────────────────────────────────────
# Alias histórico solicitudes.html → buscador.html
#
# La página se llamó solicitudes.html y pasó a buscador.html. Se conservó un
# tiempo como copia del contenido: cada cambio había que aplicarlo dos veces y
# acabó divergiendo. Ahora es una redirección; estos tests evitan la recaída.
# ─────────────────────────────────────────────────────────────────────────────

def test_solicitudes_html_redirige_a_buscador():
    """El alias histórico debe ser una redirección permanente, no una copia."""
    conf = NGINX.read_text(encoding="utf-8")
    assert "location = /solicitudes.html" in conf, (
        "Falta la redirección del alias histórico solicitudes.html"
    )
    assert "return 301 /buscador.html" in conf, (
        "El alias debe redirigir con 301 (permanente) a buscador.html"
    )


def test_la_redireccion_conserva_los_parametros_de_busqueda():
    """Sin la query string, un enlace guardado con filtros llega vacío.

    Los enlaces antiguos que justifican mantener esta ruta suelen llevar
    filtros (?buscar=...&anio=...). Redirigir perdiéndolos deja al usuario en
    un buscador en blanco: la redirección funcionaría, pero no serviría.
    """
    conf = NGINX.read_text(encoding="utf-8")
    assert "return 301 /buscador.html$is_args$args;" in conf, (
        "La redirección debe arrastrar la query string con $is_args$args"
    )


def test_no_queda_una_copia_de_la_pagina():
    """solicitudes.html no debe volver a existir como archivo."""
    copia = RAIZ / "frontend" / "solicitudes.html"
    assert not copia.exists(), (
        "solicitudes.html ha vuelto como archivo. Es un duplicado de "
        "buscador.html: debe ser solo la redirección de Nginx."
    )
