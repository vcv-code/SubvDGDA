"""
test_scheduler.py — Tests del scheduler del cron BDNS/DGDA.

Comprueba que `_jobs_for(dt)` devuelve los scripts correctos según fecha/hora UTC:
  · health_check.py corre cada 6h (00:00, 06:00, 12:00, 18:00).
  · check_bdns.py corre en temporada convocatorias (marzo–junio) y resoluciones
    (noviembre–enero), siempre a las 08:00 UTC, con frecuencia variable.
  · Fuera de calendario no se ejecuta nada.

El módulo no es un paquete (docker/cron/ no tiene __init__.py), así que se carga
con importlib.util a partir del path del archivo.
"""
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest

_SCHEDULER_PATH = Path(__file__).resolve().parents[1] / "docker" / "cron" / "scheduler.py"
_spec = importlib.util.spec_from_file_location("scheduler", _SCHEDULER_PATH)
scheduler = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scheduler)
_jobs_for = scheduler._jobs_for


def _dt(year, month, day, hour, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


# ──────────────────────────────────────────────
# health_check.py — cada 6 horas
# ──────────────────────────────────────────────

@pytest.mark.parametrize("hour", [0, 6, 12, 18])
def test_health_check_corre_cada_6h(hour):
    assert "health_check.py" in _jobs_for(_dt(2026, 7, 15, hour, 0))


@pytest.mark.parametrize("hour", [1, 3, 5, 7, 11, 13, 17, 19, 23])
def test_health_check_no_corre_fuera_de_horario(hour):
    assert "health_check.py" not in _jobs_for(_dt(2026, 7, 15, hour, 0))


def test_health_check_solo_en_minuto_0():
    assert "health_check.py" not in _jobs_for(_dt(2026, 7, 15, 6, 30))


# ──────────────────────────────────────────────
# check_bdns.py — temporada convocatorias (marzo–junio)
# ──────────────────────────────────────────────

@pytest.mark.parametrize("day", [1, 5, 9, 13, 17, 21, 25, 29])
def test_check_bdns_corre_en_marzo_cada_4_dias(day):
    assert "check_bdns.py" in _jobs_for(_dt(2026, 3, day, 8, 0))


@pytest.mark.parametrize("day", [2, 3, 4, 6, 7, 8])
def test_check_bdns_no_corre_dias_intermedios_marzo(day):
    assert "check_bdns.py" not in _jobs_for(_dt(2026, 3, day, 8, 0))


@pytest.mark.parametrize("day", [1, 3, 5, 7, 15, 21, 29])
def test_check_bdns_corre_en_abril_cada_2_dias(day):
    assert "check_bdns.py" in _jobs_for(_dt(2026, 4, day, 8, 0))


@pytest.mark.parametrize("day", [1, 3, 5, 15, 25, 31])
def test_check_bdns_corre_en_mayo_cada_2_dias(day):
    assert "check_bdns.py" in _jobs_for(_dt(2026, 5, day, 8, 0))


@pytest.mark.parametrize("day", [2, 4, 6, 10, 16, 30])
def test_check_bdns_no_corre_dias_pares_en_mayo(day):
    assert "check_bdns.py" not in _jobs_for(_dt(2026, 5, day, 8, 0))


@pytest.mark.parametrize("day", [1, 5, 9, 13, 17, 21, 25, 29])
def test_check_bdns_corre_en_junio_cada_4_dias(day):
    assert "check_bdns.py" in _jobs_for(_dt(2026, 6, day, 8, 0))


# ──────────────────────────────────────────────
# check_bdns.py — temporada resoluciones (noviembre–enero)
# ──────────────────────────────────────────────

@pytest.mark.parametrize("day", [1, 3, 5, 7, 15, 21, 29])
def test_check_bdns_corre_en_noviembre_cada_2_dias(day):
    assert "check_bdns.py" in _jobs_for(_dt(2026, 11, day, 8, 0))


@pytest.mark.parametrize("day", [2, 4, 6, 10, 16, 30])
def test_check_bdns_no_corre_dias_pares_en_noviembre(day):
    assert "check_bdns.py" not in _jobs_for(_dt(2026, 11, day, 8, 0))


@pytest.mark.parametrize("day", [1, 3, 5, 15, 25, 31])
def test_check_bdns_corre_en_diciembre_cada_2_dias(day):
    assert "check_bdns.py" in _jobs_for(_dt(2026, 12, day, 8, 0))


@pytest.mark.parametrize("day", [1, 5, 9, 13, 17, 21, 25, 29])
def test_check_bdns_corre_en_enero_cada_4_dias(day):
    assert "check_bdns.py" in _jobs_for(_dt(2026, 1, day, 8, 0))


@pytest.mark.parametrize("day", [2, 3, 4, 6, 7, 8])
def test_check_bdns_no_corre_dias_intermedios_enero(day):
    assert "check_bdns.py" not in _jobs_for(_dt(2026, 1, day, 8, 0))


# ──────────────────────────────────────────────
# check_bdns.py — fuera de calendario (julio–octubre, febrero)
# ──────────────────────────────────────────────

@pytest.mark.parametrize("month", [2, 7, 8, 9, 10])
@pytest.mark.parametrize("day", [1, 5, 15, 25])
def test_check_bdns_no_corre_fuera_de_temporada(month, day):
    assert "check_bdns.py" not in _jobs_for(_dt(2026, month, day, 8, 0))


# ──────────────────────────────────────────────
# check_bdns.py — solo a las 08:00 UTC, no a otras horas
# ──────────────────────────────────────────────

@pytest.mark.parametrize("hour", [0, 7, 9, 12, 18, 23])
def test_check_bdns_solo_a_las_8_utc(hour):
    """Aunque el día sea válido, fuera de las 08:00 UTC no se ejecuta."""
    assert "check_bdns.py" not in _jobs_for(_dt(2026, 4, 1, hour, 0))


def test_check_bdns_solo_en_minuto_0():
    assert "check_bdns.py" not in _jobs_for(_dt(2026, 4, 1, 8, 30))


# ──────────────────────────────────────────────
# Combinaciones — ambos jobs pueden coincidir
# ──────────────────────────────────────────────

def test_solo_health_check_en_dia_valido_a_medianoche():
    """1 de abril (día válido check_bdns) pero a las 00:00 → solo health_check."""
    jobs = _jobs_for(_dt(2026, 4, 1, 0, 0))
    assert jobs == ["health_check.py"]


def test_solo_check_bdns_a_las_8_dia_valido():
    """1 de abril a las 08:00 → solo check_bdns (las 8 no son múltiplo de 6)."""
    jobs = _jobs_for(_dt(2026, 4, 1, 8, 0))
    assert jobs == ["check_bdns.py"]


def test_dia_no_valido_check_bdns_a_las_8():
    """4 de abril (día par no válido) a las 08:00 → ningún job."""
    assert _jobs_for(_dt(2026, 4, 4, 8, 0)) == []


def test_julio_a_medianoche_solo_health():
    """En julio el cron de BDNS no corre nunca; el health sí cada 6h."""
    assert _jobs_for(_dt(2026, 7, 15, 0, 0)) == ["health_check.py"]
    assert _jobs_for(_dt(2026, 7, 15, 8, 0)) == []
