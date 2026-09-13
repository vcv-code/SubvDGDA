#!/usr/bin/env python3
"""
health_check.py — Comprueba que el backend responde, y AVISA por correo.

Llama a GET /health y registra el resultado en logs/cron/health_check.log.

POR QUÉ AVISA Y NO SOLO REGISTRA. Este script ya existía y anotaba los fallos
correctamente. En septiembre de 2026 el backend murió y estuvo dos días caído:
durante todo ese tiempo el log fue acumulando errores cada media hora y nadie
los leyó, porque no hay motivo para abrir un fichero de log cuando no sabes que
hay un problema. La detección estaba; faltaba que alguien lo dijera.

SOLO ESCRIBE CUANDO EL ESTADO CAMBIA. Con una comprobación cada media hora, dos
días de caída son casi cien correos: al tercero se ignoran y al décimo se
archivan sin leer, con lo que el aviso deja de servir. Se manda uno al caer y
otro al recuperarse, y entre medias solo se registra en el log.

LÍMITE QUE CONVIENE CONOCER: esto corre DENTRO del servidor. Si lo que se cae es
la máquina entera, o se queda sin red, no habrá aviso porque no habrá quien lo
mande. Para eso hace falta algo externo que vigile desde fuera.
"""

import json
import logging
import os
import smtplib
import ssl
import sys
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr

import requests

# Los contenedores van en UTC y el planificador depende de ello, así que NO se
# cambia la zona del contenedor: solo se traduce la hora que sale en el correo.
# Un aviso que dice «12:00» cuando el reloj de quien lo lee marca las 14:00
# obliga a hacer cuentas justo cuando menos apetece.
try:
    from zoneinfo import ZoneInfo
    ZONA = ZoneInfo("Europe/Madrid")
except Exception:      # sin tzdata en la imagen
    ZONA = None

BACKEND_URL = os.environ.get("BACKEND_INTERNAL_URL", "http://backend:8000")
# Configurable para poder probar el script fuera del contenedor: dentro, la
# ruta por defecto es la de siempre.
LOG_DIR = os.environ.get("CRON_LOG_DIR", "/app/logs/cron")
LOG_FILE = f"{LOG_DIR}/health_check.log"

# Recuerda si el último resultado fue bueno o malo. Va en la carpeta de logs
# porque está montada desde el host: si estuviera dentro del contenedor, se
# perdería justo cuando este se reinicia, que es cuando más falta hace.
ESTADO_FILE = f"{LOG_DIR}/health_estado.json"

SMTP_HOST = os.environ.get("SMTP_HOST", "mailpit")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_TLS = os.environ.get("SMTP_TLS", "false").lower() == "true"
EMAIL_FROM = os.environ.get("EMAIL_FROM", "avisos@localhost")
EMAIL_AVISOS = os.environ.get("EMAIL_AVISOS", "")
SITE_URL = os.environ.get("SITE_URL", "")

_FORMATO = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("health_check")
log.setLevel(logging.INFO)

# Salida por pantalla siempre: es la que recoge el log del contenedor.
_consola = logging.StreamHandler(sys.stdout)
_consola.setFormatter(_FORMATO)
log.addHandler(_consola)

# Y al fichero, SI SE PUEDE. Que no se pueda no debe tumbar el script: el disco
# lleno es una causa clásica de caída, y sería absurdo que precisamente
# entonces muriera lo único que iba a avisar de ella. Antes esto reventaba con
# FileNotFoundError antes siquiera de comprobar nada.
try:
    os.makedirs(LOG_DIR, exist_ok=True)
    _fichero = logging.FileHandler(LOG_FILE, encoding="utf-8")
    _fichero.setFormatter(_FORMATO)
    log.addHandler(_fichero)
except OSError as _e:
    log.warning("No se puede escribir %s (%s); solo saldrá por pantalla", LOG_FILE, _e)


def leer_estado():
    """Último resultado conocido. Si no hay fichero, se asume que iba bien.

    Asumir «iba bien» y no «iba mal» es deliberado: en el primer arranque no
    hay nada que comparar, y suponer lo contrario mandaría un correo de
    recuperación por un incidente que nunca ocurrió.
    """
    try:
        with open(ESTADO_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        # OSError y no solo FileNotFoundError: «no es un directorio», «permiso
        # denegado» o «disco lleno» son hermanos suyos, no descendientes, y se
        # escapaban. Justo los casos en los que hay que avisar.
        return {"caido": False, "desde": None, "avisado": False}


def guardar_estado(estado):
    try:
        with open(ESTADO_FILE, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
    except OSError as e:
        # Que no se pueda guardar el estado no debe tumbar la comprobación:
        # como mucho se repetirá un aviso.
        log.error("No se pudo guardar el estado: %s", e)


def enviar_aviso(asunto, cuerpo):
    """Manda el correo. Nunca lanza: un fallo al avisar no puede romper el cron."""
    if not EMAIL_AVISOS:
        log.warning("Hay algo que avisar pero EMAIL_AVISOS está vacío: %s", asunto)
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = formataddr(("Subvenciones DGDA - avisos", EMAIL_FROM))
        msg["To"] = EMAIL_AVISOS
        msg.set_content(cuerpo)

        if SMTP_TLS:
            contexto = ssl.create_default_context()
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
                s.starttls(context=contexto)
                if SMTP_USER:
                    s.login(SMTP_USER, SMTP_PASSWORD)
                s.send_message(msg)
        else:
            # Mailpit en desarrollo: sin cifrado ni usuario.
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
                if SMTP_USER:
                    s.login(SMTP_USER, SMTP_PASSWORD)
                s.send_message(msg)
        log.info("Aviso enviado a %s: %s", EMAIL_AVISOS, asunto)
        return True
    except Exception as e:
        log.error("No se pudo enviar el aviso (%s): %s", asunto, e)
        return False


def ahora_local():
    """La hora tal como la ve quien recibe el aviso."""
    momento = datetime.now(ZONA) if ZONA else datetime.utcnow()
    sufijo = "" if ZONA else " UTC"
    return momento.strftime("%d/%m/%Y a las %H:%M") + sufijo


def _pedir(ruta, descripcion):
    """Una petición, traduciendo los fallos a un motivo legible."""
    try:
        resp = requests.get(f"{BACKEND_URL}{ruta}", timeout=10)
        if resp.status_code == 200:
            return True, None
        return False, f"{descripcion} respondió {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, f"{descripcion} no es accesible: conexión rechazada"
    except requests.exceptions.Timeout:
        return False, f"{descripcion} no respondió en 10 segundos"
    except Exception as e:
        return False, f"Error inesperado al comprobar {descripcion.lower()}: {e}"


def comprobar():
    """Devuelve (ok, motivo). El motivo se usa en el correo.

    Se comprueban DOS cosas, y la segunda es la que de verdad importa:

      /health          dice si el proceso está vivo, y nada más: devuelve
                       {"status": "ok"} sin tocar la base de datos.
      /convocatorias/  recorre el camino completo hasta MariaDB.

    Con solo la primera, una base de datos caída pasaba desapercibida: el
    backend seguía respondiendo «ok» mientras la web mostraba las páginas
    vacías, que para quien la visita es exactamente igual de inservible.
    """
    vivo, motivo = _pedir("/health", "El backend")
    if not vivo:
        return False, motivo

    datos, motivo = _pedir("/convocatorias/", "La API de datos")
    if not datos:
        return False, f"{motivo} (el proceso sí responde: falla el acceso a los datos)"

    return True, "Backend y datos OK"


def main():
    ok, motivo = comprobar()
    estado = leer_estado()
    ahora = ahora_local()

    if ok:
        log.info(motivo)
        if estado.get("caido"):
            desde = estado.get("desde") or "un momento indeterminado"
            enviar_aviso(
                "La web ha vuelto a funcionar",
                f"El backend responde otra vez, comprobado el {ahora}.\n\n"
                f"Estuvo sin responder desde el {desde}.\n\n"
                f"{SITE_URL}\n",
            )
        guardar_estado({"caido": False, "desde": None, "avisado": False})
        return

    log.error(motivo)
    if not estado.get("avisado"):
        enviar_aviso(
            "La web no responde",
            f"{motivo}\n\n"
            f"Detectado el {ahora}.\n\n"
            "Mientras el backend no responda, la web sigue mostrando las páginas\n"
            "pero sin datos: tablas, estadísticas y buscador salen vacíos. Y si\n"
            "Nginx se reinicia en ese estado, no arrancará —no puede resolver el\n"
            "nombre «backend»— y el sitio quedará inaccesible del todo.\n\n"
            "Qué mirar, entrando por SSH:\n\n"
            "    cd /opt/subvdgda/docker\n"
            "    docker compose ps\n"
            "    docker compose logs --tail=60 backend\n"
            "    df -h /\n\n"
            "Para levantarlo:\n\n"
            "    docker compose up -d backend\n"
            "    docker compose up -d nginx\n\n"
            "No se repetirá este aviso hasta que la web vuelva y se caiga otra vez.\n",
        )
        # Se marca como avisado aunque el envío falle: si el correo no sale, lo
        # que toca es mirar el log, no acumular intentos cada media hora.
        guardar_estado({"caido": True, "desde": ahora, "avisado": True})
    else:
        guardar_estado({**estado, "caido": True})


if __name__ == "__main__":
    main()
