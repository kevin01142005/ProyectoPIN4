import logging
import threading
from typing import Optional

import httpx

from app.config.configuracion import configuracion

logger = logging.getLogger(__name__)

URL_ACTUALIZAR = "https://api.thingspeak.com/update.json"


def _enviar(temperatura: float) -> None:
    datos = {"api_key": configuracion.thingspeak_write_key, "field1": temperatura}
    try:
        respuesta = httpx.post(URL_ACTUALIZAR, data=datos, timeout=8.0)
        if respuesta.status_code != 200 or respuesta.text.strip() in ("", "0"):
            logger.warning("ThingSpeak no aceptó la lectura (%s): %s", respuesta.status_code, respuesta.text[:100])
    except httpx.HTTPError as error:
        logger.warning("No se pudo enviar la lectura a ThingSpeak: %s", error)


def publicar_lectura(temperatura: float, presion: Optional[float] = None) -> None:
    """Reenvía la temperatura a ThingSpeak en segundo plano; si falla, no afecta al circuito.

    La presión se recibe pero no se envía: el canal solo grafica temperatura.
    """
    if not configuracion.thingspeak_write_key:
        return
    threading.Thread(target=_enviar, args=(temperatura,), daemon=True).start()