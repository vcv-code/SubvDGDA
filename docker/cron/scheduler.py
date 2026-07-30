#!/usr/bin/env python3
"""
scheduler.py — Scheduler de tareas cron para el servicio BDNS/DGDA.

Implementa la misma lógica que el crontab original:
  · health_check.py — 0 */6 * * *    (00:00, 06:00, 12:00, 18:00 UTC)
  · check_bdns.py   — Temporada convocatorias (marzo–junio):
                      0 8 */4 3 *    (marzo:   días 1,5,9,…)
                      0 8 */2 4 *    (abril:   días 1,3,5,…)
                      0 8 */2 5 *    (mayo:    días 1,3,5,…)
                      0 8 */4 6 *    (junio:   días 1,5,9,…)
                      Temporada resoluciones (noviembre–enero):
                      0 8 */2 11 *   (noviembre: días 1,3,5,…)
                      0 8 */2 12 *   (diciembre: días 1,3,5,…)
                      0 8 */4 1 *    (enero:     días 1,5,9,…)
  · rotar_logs.py   — 15 4 * * *     (04:15 UTC a diario)
"""
import logging
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [cron] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger(__name__)


def _jobs_for(dt: datetime) -> list[str]:
    """Devuelve los scripts que deben ejecutarse en el minuto indicado (UTC)."""
    jobs: list[str] = []
    h, m, d, mo = dt.hour, dt.minute, dt.day, dt.month

    # 0 */6 * * *  →  00:00, 06:00, 12:00, 18:00 UTC
    if m == 0 and h % 6 == 0:
        jobs.append("health_check.py")

    # 0 8 */N M *  →  08:00 UTC en días (d-1)%N==0 del mes M
    if m == 0 and h == 8:
        # Temporada convocatorias (marzo–junio): pico en abril–mayo
        if mo == 3 and (d - 1) % 4 == 0:
            jobs.append("check_bdns.py")
        elif mo in (4, 5) and (d - 1) % 2 == 0:
            jobs.append("check_bdns.py")
        elif mo == 6 and (d - 1) % 4 == 0:
            jobs.append("check_bdns.py")
        # Temporada resoluciones (noviembre–enero): pico en noviembre–diciembre
        elif mo in (11, 12) and (d - 1) % 2 == 0:
            jobs.append("check_bdns.py")
        elif mo == 1 and (d - 1) % 4 == 0:
            jobs.append("check_bdns.py")

    # 15 4 * * *  →  04:15 UTC a diario.
    # A esa hora no hay tráfico, así que la ventana entre copiar y vaciar el
    # log (donde se pierde alguna línea) cae en el momento de menos actividad.
    if h == 4 and m == 15:
        jobs.append("rotar_logs.py")

    return jobs


def _run(script: str) -> None:
    log.info("Iniciando %s", script)
    result = subprocess.run(["python3", f"/app/scripts/{script}"])
    if result.returncode == 0:
        log.info("%s completado OK", script)
    else:
        log.error("%s terminó con código %d", script, result.returncode)


def _handle_stop(sig, _frame):
    log.info("Señal %d recibida, deteniendo servicio cron", sig)
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    log.info("Servicio cron BDNS/DGDA iniciado")
    while True:
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        for script in _jobs_for(now):
            _run(script)

        # Esperar hasta el siguiente minuto exacto
        elapsed_secs = datetime.now(timezone.utc).second
        time.sleep(60 - elapsed_secs + 0.05)


if __name__ == "__main__":
    main()
