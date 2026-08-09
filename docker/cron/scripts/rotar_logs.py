#!/usr/bin/env python3
"""
rotar_logs.py — Rotación diaria de los ficheros de log del proyecto.

Por qué un script y no la rotación de Docker
────────────────────────────────────────────
El `max-size` / `max-file` del logging de Docker solo rota lo que un
contenedor escribe por salida estándar. Aquí tanto Nginx como el backend
escriben DIRECTAMENTE a ficheros dentro de carpetas montadas, así que Docker
ni los ve. Tampoco vale `logrotate` del sistema: viviría fuera del
repositorio y habría que instalarlo a mano en cada servidor.

Este script corre en el contenedor de cron, que ya existe, y va versionado
con el proyecto: se comporta igual en local que en el VPS.

Por qué "copiar y vaciar" y no renombrar
────────────────────────────────────────
Nginx mantiene el fichero abierto. Si se renombra, sigue escribiendo en el
fichero renombrado (el mismo inodo) y el nuevo `access.log` se queda vacío
para siempre; lo normal sería avisarle con `nginx -s reopen`, pero desde
otro contenedor no se le puede mandar la señal con comodidad.

Copiando el contenido a un fichero con fecha y VACIANDO el original se
conserva el inodo, así que Nginx sigue escribiendo sin enterarse. Es la
misma estrategia que `logrotate` llama `copytruncate`. Tiene una pega
conocida: las líneas escritas entre la copia y el vaciado se pierden. Para
un registro de accesos es asumible.

Qué NO hace
───────────
No toca `estado_2026.json` ni ningún fichero que no acabe en `.log`: el
estado del cron es un espejo de la base de datos, no un registro.
"""
import logging
import os
import shutil
from datetime import datetime, timedelta

LOG_ROOT = "/app/logs"

# Deja su propio registro, como health_check.py y check_bdns.py. No se añade
# al panel admin: allí cada log del cron tiene su sección con selector y
# botón, y para una tarea que o funciona o deja crecer los ficheros no
# compensa. Se consulta desde el servidor si hace falta.
LOG_FILE = f"{LOG_ROOT}/cron/rotar_logs.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# Días que se conservan los registros. Es el número que debe aparecer en la
# sección "Registros del servidor" de privacidad.html: si se cambia aquí,
# hay que cambiarlo allí. Treinta días equilibra dos cosas en tensión —
# menos tiempo es mejor para la privacidad, más tiempo permite investigar un
# problema o sacar estadísticas de uso del último mes.
DIAS_RETENCION = 30

# Un fichero vacío no se rota: evita generar copias de cero bytes cada día
# en instalaciones con poco tráfico.
MIN_BYTES = 1


def _hoy():
    return datetime.now().strftime("%Y-%m-%d")


def rotar(ruta):
    """Copia el contenido a un fichero con fecha y vacía el original."""
    if os.path.getsize(ruta) < MIN_BYTES:
        return None

    destino = f"{ruta}.{_hoy()}"
    if os.path.exists(destino):
        return None            # ya se rotó hoy

    shutil.copy2(ruta, destino)
    with open(ruta, "w"):      # vacía sin cambiar el inodo
        pass
    return destino


def limpiar_antiguos(directorio, base):
    """Borra las copias con fecha anteriores al periodo de retención."""
    limite = datetime.now() - timedelta(days=DIAS_RETENCION)
    borrados = 0
    for nombre in os.listdir(directorio):
        if not nombre.startswith(base + "."):
            continue
        sufijo = nombre[len(base) + 1:]
        try:
            fecha = datetime.strptime(sufijo, "%Y-%m-%d")
        except ValueError:
            continue           # no es una copia con fecha nuestra
        if fecha < limite:
            os.remove(os.path.join(directorio, nombre))
            borrados += 1
    return borrados


def main():
    if not os.path.isdir(LOG_ROOT):
        log.warning("No existe %s; nada que rotar.", LOG_ROOT)
        return

    rotados = borrados = 0
    for directorio, _, ficheros in os.walk(LOG_ROOT):
        for nombre in ficheros:
            if not nombre.endswith(".log"):
                continue
            ruta = os.path.join(directorio, nombre)
            # Su propio log no se rota aquí: al vaciarlo a mitad de ejecución
            # se perderían las líneas ya escritas de esta misma pasada. Se
            # rota en la ejecución siguiente, cuando ya está cerrado.
            if os.path.abspath(ruta) == os.path.abspath(LOG_FILE):
                borrados += limpiar_antiguos(directorio, nombre)
                continue
            if rotar(ruta):
                rotados += 1
                log.info("Rotado: %s", ruta)
            borrados += limpiar_antiguos(directorio, nombre)

    log.info("Fin: %d rotados, %d copias borradas (retención %d días)",
             rotados, borrados, DIAS_RETENCION)


if __name__ == "__main__":
    main()
