"""
test_scheduler.py — Tests del scheduler del cron BDNS/DGDA.

Comprueba que `_jobs_for(dt)` devuelve los scripts correctos según fecha/hora UTC:
  · health_check.py corre cada media hora (minutos 0 y 30).
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
# health_check.py — cada media hora
# ──────────────────────────────────────────────

@pytest.mark.parametrize("hour", range(24))
@pytest.mark.parametrize("minute", [0, 30])
def test_health_check_corre_cada_media_hora(hour, minute):
    """Antes iba cada 6 horas: bastaba para dejar constancia en el log, pero no
    para enterarse de una caída. Desde que avisa por correo, la frecuencia es lo
    que separa saberlo en media hora de saberlo en dos días."""
    assert "health_check.py" in _jobs_for(_dt(2026, 7, 15, hour, minute))


@pytest.mark.parametrize("minute", [1, 15, 29, 31, 45, 59])
def test_health_check_no_corre_en_otros_minutos(minute):
    assert "health_check.py" not in _jobs_for(_dt(2026, 7, 15, 6, minute))


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


def test_check_bdns_a_las_8_dia_valido():
    """1 de abril a las 08:00 → check_bdns, junto al health check.

    Antes este test comprobaba que a esa hora corriera «solo» check_bdns,
    porque el health iba cada 6 horas y las 8 no son múltiplo de 6. Al pasar a
    cada media hora se cruzan, y no pasa nada: son tareas independientes.
    """
    jobs = _jobs_for(_dt(2026, 4, 1, 8, 0))
    assert "check_bdns.py" in jobs
    assert set(jobs) == {"check_bdns.py", "health_check.py"}


def test_dia_no_valido_check_bdns_a_las_8():
    """4 de abril (día par no válido) a las 08:00 → ningún job."""
    # A las 08:00 en punto también corre el health check, que va cada media hora.
    assert _jobs_for(_dt(2026, 4, 4, 8, 0)) == ["health_check.py"]


def test_julio_solo_corre_el_health():
    """En julio el cron de BDNS no corre nunca; el health sí, cada media hora."""
    assert _jobs_for(_dt(2026, 7, 15, 0, 0)) == ["health_check.py"]
    assert _jobs_for(_dt(2026, 7, 15, 8, 0)) == ["health_check.py"]
    assert _jobs_for(_dt(2026, 7, 15, 8, 15)) == []


# ──────────────────────────────────────────────
# rotar_logs.py — diario a las 04:15 UTC
# ──────────────────────────────────────────────

@pytest.mark.parametrize("mes", [1, 3, 4, 6, 7, 11, 12])
def test_rotar_logs_corre_todos_los_dias(mes):
    """A diferencia de check_bdns, no depende de la temporada: corre siempre."""
    assert _jobs_for(_dt(2026, mes, 15, 4, 15)) == ["rotar_logs.py"]


def test_rotar_logs_solo_a_las_4_15():
    """Un minuto antes o después no dispara nada."""
    assert _jobs_for(_dt(2026, 7, 15, 4, 14)) == []
    assert _jobs_for(_dt(2026, 7, 15, 4, 16)) == []
    assert _jobs_for(_dt(2026, 7, 15, 5, 15)) == []


def test_rotar_logs_no_choca_con_los_demas():
    """Las 04:15 no son minuto 0 ni 30, así que no coinciden con el health
    check; ni son las 08:00, así que tampoco con check_bdns."""
    assert _jobs_for(_dt(2026, 4, 1, 4, 15)) == ["rotar_logs.py"]


def test_el_health_check_convive_con_las_demas_tareas():
    """Corriendo cada media hora se cruza con las otras, y eso es correcto:
    son tareas independientes y ninguna bloquea a la otra."""
    assert _jobs_for(_dt(2026, 4, 1, 0, 0)) == ["health_check.py"]
    assert set(_jobs_for(_dt(2026, 4, 1, 8, 0))) == {"health_check.py", "check_bdns.py"}
