import json
import urllib.error
import urllib.request
from typing import Optional

# Algunos servicios (por ejemplo los que están detrás de Cloudflare) rechazan el agente por defecto de Python.
AGENTE_USUARIO = "LuxMotos-API/1.0"


def peticion(
    metodo: str,
    url: str,
    cuerpo: Optional[dict] = None,
    cabeceras: Optional[dict] = None,
    timeout: float = 60.0,
) -> tuple[int, dict, str]:
    """Hace una petición HTTP con cuerpo JSON y devuelve (estado, cabeceras en minúscula, texto).

    Un estado 4xx/5xx NO lanza excepción: se devuelve para que quien llama decida.
    Los fallos de red o el tiempo agotado sí lanzan OSError (URLError, TimeoutError...).
    """
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    solicitud = urllib.request.Request(url, data=datos, method=metodo)
    solicitud.add_header("User-Agent", AGENTE_USUARIO)
    if datos is not None:
        solicitud.add_header("Content-Type", "application/json")
    for nombre, valor in (cabeceras or {}).items():
        solicitud.add_header(nombre, valor)

    try:
        with urllib.request.urlopen(solicitud, timeout=timeout) as respuesta:
            texto = respuesta.read().decode("utf-8", "replace")
            return respuesta.status, {k.lower(): v for k, v in respuesta.headers.items()}, texto
    except urllib.error.HTTPError as error:
        texto = error.read().decode("utf-8", "replace")
        return error.code, {k.lower(): v for k, v in error.headers.items()}, texto