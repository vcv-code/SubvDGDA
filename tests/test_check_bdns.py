"""
test_check_bdns.py — Tests del helper de reintentos `_get_bdns_con_retry`.

Cubre el comportamiento del retry con backoff exponencial implementado en
`docker/cron/scripts/check_bdns.py`:
  · Primer intento OK → devuelve la respuesta sin sleeps.
  · Fallo y luego OK → reintenta con backoff inicial.
  · Todos los intentos fallan (error de red) → devuelve None.
  · Todos los intentos devuelven status != 200 → devuelve None.
  · Los tiempos de espera siguen el patrón 2s → 4s → 8s.

El módulo `check_bdns.py` se carga con importlib.util porque:
  · `docker/cron/scripts/` no es un paquete Python (sin __init__.py).
  · Ejecuta side effects al importarse (os.makedirs sobre /app/logs/cron
    y logging.basicConfig contra archivo), que mockeamos antes de cargar.
  · Importa `pymysql`, que no está instalado en el venv local, así que
    se sustituye por un módulo falso en sys.modules.
"""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

_CHECK_BDNS_PATH = (
    Path(__file__).resolve().parents[1]
    / "docker" / "cron" / "scripts" / "check_bdns.py"
)


def _cargar_modulo():
    """Carga check_bdns.py con todas las dependencias problemáticas mockeadas."""
    # pymysql no está en el venv local — sustituirlo por un mock en sys.modules
    sys.modules.setdefault("pymysql", MagicMock())

    with patch("os.makedirs"), patch("logging.basicConfig"):
        spec = importlib.util.spec_from_file_location("check_bdns", _CHECK_BDNS_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod


check_bdns = _cargar_modulo()


def _resp(status):
    """Fabrica un objeto Response simulado con el código indicado."""
    r = MagicMock()
    r.status_code = status
    r.json.return_value = {"ok": True}
    return r


# ──────────────────────────────────────────────
# Camino feliz
# ──────────────────────────────────────────────

def test_get_bdns_devuelve_respuesta_si_primer_intento_ok():
    """Si BDNS responde 200 a la primera, no hay reintentos ni sleeps."""
    with patch.object(check_bdns.requests, "get", return_value=_resp(200)) as g, \
         patch.object(check_bdns.time, "sleep") as s:
        resp = check_bdns._get_bdns_con_retry("http://x/test")

    assert resp is not None
    assert resp.status_code == 200
    assert g.call_count == 1
    assert s.call_count == 0


# ──────────────────────────────────────────────
# Recuperación tras un fallo
# ──────────────────────────────────────────────

def test_get_bdns_reintenta_y_devuelve_si_segundo_intento_ok():
    """Un timeout puntual no debe rendirse: en el 2º intento BDNS responde 200."""
    respuestas = [requests.Timeout("blip"), _resp(200)]

    def lado_efecto(*args, **kwargs):
        valor = respuestas.pop(0)
        if isinstance(valor, Exception):
            raise valor
        return valor

    with patch.object(check_bdns.requests, "get", side_effect=lado_efecto) as g, \
         patch.object(check_bdns.time, "sleep") as s:
        resp = check_bdns._get_bdns_con_retry("http://x/test")

    assert resp is not None
    assert g.call_count == 2
    assert s.call_count == 1
    assert s.call_args_list[0].args[0] == 2  # backoff inicial de 2s


# ──────────────────────────────────────────────
# Todos los intentos fallan
# ──────────────────────────────────────────────

def test_get_bdns_devuelve_none_si_todos_intentos_fallan_red():
    """3 errores de red consecutivos → la función se rinde con None."""
    with patch.object(
        check_bdns.requests, "get",
        side_effect=requests.ConnectionError("BDNS caído")
    ) as g, patch.object(check_bdns.time, "sleep") as s:
        resp = check_bdns._get_bdns_con_retry("http://x/test")

    assert resp is None
    assert g.call_count == 3              # 3 intentos completos
    assert s.call_count == 2              # se duerme entre 1-2 y 2-3, no después del 3


def test_get_bdns_devuelve_none_si_status_500_tres_veces():
    """BDNS responde 500 las 3 veces → la función se rinde con None."""
    with patch.object(check_bdns.requests, "get", return_value=_resp(500)) as g, \
         patch.object(check_bdns.time, "sleep") as s:
        resp = check_bdns._get_bdns_con_retry("http://x/test")

    assert resp is None
    assert g.call_count == 3
    assert s.call_count == 2


# ──────────────────────────────────────────────
# Backoff exponencial
# ──────────────────────────────────────────────

def test_get_bdns_backoff_exponencial_2_4_segundos():
    """
    Si fallan los 3 intentos, los sleeps deben ser exponenciales (2s y 4s).
    No se duerme tras el 3º intento porque no hay un 4º.
    """
    with patch.object(
        check_bdns.requests, "get",
        side_effect=requests.ConnectionError("BDNS caído")
    ), patch.object(check_bdns.time, "sleep") as s:
        check_bdns._get_bdns_con_retry("http://x/test")

    sleeps = [c.args[0] for c in s.call_args_list]
    assert sleeps == [2, 4]
