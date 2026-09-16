"""
El favicon de la raíz.

Existe por un fallo real: el informe de visitas de septiembre de 2026 registró
**224 peticiones a `/favicon.ico` devolviendo 404** en treinta días. Las páginas
declaran `<link rel="icon" href="assets/img/logo.png">`, pero navegadores,
lectores de RSS y buscadores piden `/favicon.ico` a la raíz de todas formas, y
allí no había nada.

No rompe nada visible —de ahí que llevara meses pasando—: solo ensucia el log y
deja la pestaña sin icono en los clientes que no leen el `<link>`.
"""
import re
import struct
from pathlib import Path

FAVICON = Path("frontend/favicon.ico")


def test_el_favicon_existe_en_la_raiz():
    """En la RAÍZ, no en assets/: es la ruta fija que piden los clientes."""
    assert FAVICON.exists(), "falta frontend/favicon.ico"


def test_es_un_ico_de_verdad():
    """Renombrar un PNG a .ico no vale: parte de los clientes que piden esta
    ruta son justamente los que no interpretan PNG."""
    cabecera = FAVICON.read_bytes()[:4]
    # Cabecera ICO: reservado (0), tipo 1 = icono.
    reservado, tipo = struct.unpack("<HH", cabecera)
    assert reservado == 0 and tipo == 1, "no tiene cabecera de ICO"


def test_lleva_los_tamanos_que_hacen_falta():
    """16 y 32 px son los de la pestaña; sin ellos el navegador reescala uno
    grande y se ve sucio."""
    datos = FAVICON.read_bytes()
    n = struct.unpack("<H", datos[4:6])[0]
    # En el directorio de un ICO, 0 significa 256.
    lados = {datos[6 + i * 16] or 256 for i in range(n)}
    assert {16, 32} <= lados, f"faltan tamaños: hay {sorted(lados)}"


def test_nginx_le_pone_cache_larga():
    """Un icono no cambia nunca. La regla de imágenes ya lo cubre, pero si
    alguien toca la lista de extensiones y quita `ico`, cada visita volvería a
    pedirlo."""
    conf = Path("docker/nginx/default.conf").read_text(encoding="utf-8")
    bloques = re.findall(r"location\s+([^{]+)\{([^}]*)\}", conf)
    con_cache_larga = [sel for sel, cuerpo in bloques if "expires 1y" in cuerpo]
    assert any("ico" in sel for sel in con_cache_larga), \
        "ninguna regla con `expires 1y` incluye ya la extensión .ico"
