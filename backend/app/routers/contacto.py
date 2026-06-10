import logging

from fastapi import APIRouter, HTTPException, status

from ..auth import enviar_email_contacto
from ..schemas import ContactoIn, ContactoOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contacto", tags=["contacto"])

_RESPUESTA_OK = "Mensaje recibido. ¡Gracias por escribirnos! Te responderemos lo antes posible."


@router.post("/", response_model=ContactoOut)
def contacto(datos: ContactoIn):
    # Honeypot: campo oculto que solo rellenan los bots — éxito falso sin enviar nada
    if datos.sitio_web:
        return ContactoOut(mensaje=_RESPUESTA_OK)

    try:
        enviar_email_contacto(datos.nombre, datos.email, datos.mensaje)
    except Exception as e:  # SMTP caído, conexión rechazada, etc.
        logger.error("Error enviando mensaje de contacto de %s: %s", datos.email, e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo enviar el mensaje en este momento. Inténtalo de nuevo más tarde.",
        )

    return ContactoOut(mensaje=_RESPUESTA_OK)
