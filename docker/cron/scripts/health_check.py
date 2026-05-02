#!/usr/bin/env python3
"""
health_check.py — Comprueba que el backend responde correctamente.

Llama a GET /health y registra el resultado en logs/cron/health_check.log.
Si el backend no responde o devuelve un error, lo registra como ERROR
para que quede constancia en el log del incidente.
"""

import logging
import os
import sys

import requests

BACKEND_URL = os.environ.get("BACKEND_INTERNAL_URL", "http://backend:8000")
LOG_DIR = "/app/logs/cron"
LOG_FILE = f"{LOG_DIR}/health_check.log"

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger()
log.addHandler(logging.StreamHandler(sys.stdout))


def main():
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if resp.status_code == 200:
            log.info("Backend OK — %s", resp.json())
        else:
            log.error("Backend respondió %d", resp.status_code)
    except requests.exceptions.ConnectionError:
        log.error("Backend no accesible — conexión rechazada")
    except requests.exceptions.Timeout:
        log.error("Backend no respondió en 10s — timeout")
    except Exception as e:
        log.error("Error inesperado: %s", e)


if __name__ == "__main__":
    main()
