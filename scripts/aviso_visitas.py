#!/usr/bin/env python3
"""
aviso_visitas.py — Correo mensual con la evolución de las visitas.

POR QUÉ EXISTE. El histórico se alimenta de los informes, y los informes se
generan en el servidor por tarea programada. Sin un aviso, uno se entera de
cómo va la web solo cuando se acuerda de mirar — y de acordarse ya sabemos lo
que pasa: la última copia de seguridad descargada antes de automatizarlo era de
mes y medio antes.

QUÉ MANDA Y QUÉ NO. El cuerpo lleva las cifras por mes y la tendencia, en texto
plano. **No adjunta el resumen de visitas**, que lleva direcciones IP de los
visitantes: sacarlas del servidor por correo sería dejarlas en un buzón sin
necesidad. El histórico del que salen estas cifras ya viene filtrado.

DÓNDE CORRE. En el HOST del servidor, por el `crontab` del sistema, igual que
la copia de seguridad — no dentro del contenedor de cron, que no ve la carpeta
de informes. Por eso tiene su propio envío de correo en vez de reutilizar el de
health_check.py: son dos contextos de ejecución distintos y el del contenedor
recibe la configuración por variables de entorno que aquí no están puestas.

Uso:
    python3 scripts/aviso_visitas.py           → actualiza el histórico y avisa
    python3 scripts/aviso_visitas.py --seco    → enseña el correo, sin enviarlo
"""
import importlib.util
import os
import smtplib
import ssl
import sys
from datetime import date
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

RAIZ = Path(__file__).parent.parent
ENV_FILE = RAIZ / "docker/.env"
INFORMES = RAIZ / "informes/servidor"
INFORMES_LOCAL = RAIZ / "informes"


def cargar_env():
    """Lee docker/.env sin dependencias, igual que hace backup_db.sh."""
    if not ENV_FILE.exists():
        return
    for linea in ENV_FILE.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def _modulo(nombre):
    """Carga un script hermano como módulo, sin que scripts/ sea un paquete."""
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / f"scripts/{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def flecha(pct):
    return "▲" if pct > 0 else ("▼" if pct < 0 else "=")


def componer(hist, evo, informes):
    dias = hist.get("dias", {})
    if not dias:
        return None, None

    meses = evo.por_meses(dias)
    ultimo = meses[-1]
    previo = meses[-2] if len(meses) > 1 else None

    if previo and previo["media"]:
        pct = (ultimo["media"] - previo["media"]) / previo["media"] * 100
        titular = f"{flecha(pct)} {pct:+.0f} % frente a {previo['nombre']}"
    else:
        titular = "primer mes con datos"

    asunto = f"Visitas de {ultimo['nombre']} — {titular}"

    lineas = [
        f"Evolución de subvencionesdgda.org a {date.today():%d/%m/%Y}.",
        "",
        "Mes             Visitas   Media/día   Días",
        "-" * 46,
    ]
    for m in meses[-6:]:
        marca = ""
        if m["en_curso"]:
            marca = f'  (en curso, {m["dias"]}/{m["del_mes"]})'
        elif not m["completo"]:
            marca = f'  (parcial, {m["dias"]}/{m["del_mes"]})'
        lineas.append(
            f'{m["nombre"]:<15} {m["total"]:>7}   {m["media"]:>9}   {m["dias"]:>4}{marca}')

    lineas += [
        "",
        "Compara la MEDIA DIARIA y no el total: un mes con menos días medidos",
        "sale más bajo sin que haya ido peor.",
        "",
    ]

    # No se dice «sin descargar»: el servidor no sabe qué se ha bajado nadie.
    # Solo puede contar lo que tiene guardado, y esa cifra ya es útil.
    if informes:
        ultimo = max(informes, key=lambda r: r.name).name
        lineas += [
            f"El servidor guarda {len(informes)} informe(s); el más reciente es",
            f"{ultimo}. Para traértelos y ver el detalle:",
            "",
            "    make informes",
            "    make evolucion",
            "",
        ]
    else:
        lineas += [
            "AVISO: no hay ningún informe guardado en el servidor.",
            "Comprueba que la tarea semanal sigue corriendo:",
            "",
            "    ssh servidor 'crontab -l'",
            "",
        ]

    lineas += [
        "Este correo no adjunta el resumen de visitas porque lleva direcciones",
        "IP de los visitantes. Las cifras de arriba salen del histórico, que va",
        "filtrado.",
    ]
    return asunto, "\n".join(lineas)


def enviar(asunto, cuerpo):
    """Manda el correo. Nunca lanza: un fallo al avisar no rompe el cron."""
    destino = os.environ.get("EMAIL_AVISOS", "")
    if not destino:
        print("EMAIL_AVISOS está vacío: no hay a quién avisar.", file=sys.stderr)
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = formataddr(
            ("Subvenciones DGDA - visitas", os.environ.get("EMAIL_FROM", "avisos@localhost")))
        msg["To"] = destino
        msg.set_content(cuerpo)

        host = os.environ.get("SMTP_HOST", "localhost")
        puerto = int(os.environ.get("SMTP_PORT", "1025"))
        usuario = os.environ.get("SMTP_USER", "")
        clave = os.environ.get("SMTP_PASSWORD", "")

        with smtplib.SMTP(host, puerto, timeout=20) as s:
            if os.environ.get("SMTP_TLS", "false").lower() == "true":
                s.starttls(context=ssl.create_default_context())
            if usuario:
                s.login(usuario, clave)
            s.send_message(msg)
        print(f"Aviso enviado a {destino}")
        return True
    except Exception as e:
        print(f"No se pudo enviar el aviso: {e}", file=sys.stderr)
        return False


def main(argv):
    seco = "--seco" in argv
    cargar_env()

    historico = _modulo("historico_visitas")
    evo = _modulo("evolucion_visitas")

    # Incorporar al histórico lo que haya generado la tarea semanal, por si
    # este aviso corre antes de que nadie se haya descargado nada.
    rutas = sorted(INFORMES.glob("resumen-*.html")) if INFORMES.exists() else []
    rutas += sorted(INFORMES_LOCAL.glob("resumen-*.html"))
    hist = historico.cargar()
    for r in rutas:
        info = historico.leer_informe(r)
        if info:
            historico.fusionar(hist, info)
    historico.guardar(hist)

    asunto, cuerpo = componer(hist, evo, rutas)
    if not asunto:
        print("El histórico está vacío: no hay nada que contar.")
        return 0

    if seco:
        print(f"Asunto: {asunto}\n")
        print(cuerpo)
        return 0
    return 0 if enviar(asunto, cuerpo) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
