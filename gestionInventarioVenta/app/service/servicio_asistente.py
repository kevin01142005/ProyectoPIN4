import json
import logging
import threading
from pathlib import Path
from typing import Optional

from app.client.http_json import peticion
from app.config.configuracion import configuracion
from app.exception.api_exception import ServicioNoDisponibleException, SolicitudInvalidaException

logger = logging.getLogger("app.service.servicio_asistente")

MAX_TURNOS_HISTORIAL = 6
MAX_CARACTERES_TURNO = 1500
MAX_TOKENS_RESPUESTA = 1500  # los modelos que razonan gastan parte de este límite pensando
MAX_CARACTERES_CONTEXTO = 12000

# Documento opcional con información extra (garantías, horarios, catálogo...). Si existe, se agrega al contexto.
ARCHIVO_CONOCIMIENTO = Path(__file__).resolve().parents[2] / "conocimiento_asistente.txt"

CONOCIMIENTO_BASE = """\
SISTEMA LUXMOTOS (inventario y ventas de accesorios para moto). Los valores están en pesos colombianos (COP).

IVA y totales: el IVA es del 19 %. El subtotal es la suma de precio x cantidad de cada producto; el IVA es el subtotal x 0,19 \
(redondeado a 2 decimales); el total es subtotal + IVA. Ejemplo: subtotal 100.000, IVA 19.000, total 119.000.

Ventas: una venta nueva queda en estado Pendiente y todavía no mueve el inventario. Al completarla se descuenta el stock \
(se registra una salida de inventario con el motivo "Venta #número") y se genera la factura. Solo una venta Pendiente puede \
completarse o anularse; anularla no cambia el stock porque aún no se había descontado.

Stock bajo: cuando, al completar una venta, un producto queda con stock actual menor o igual a su stock mínimo, el sistema \
envía un correo de alerta a los administradores.

Roles: Empleado: opera el día a día; ve y registra productos y puede editarlos (no eliminarlos), consulta categorías y \
proveedores, gestiona clientes, consulta el inventario, registra ventas y usa el asistente y el chat; no ve reportes, \
notificaciones, auditoría, usuarios ni seguridad. Administrador: además elimina productos, categorías y proveedores y ve el \
Panel, los reportes, las notificaciones, la auditoría y los usuarios. Super usuario: todo lo anterior más el módulo de \
Seguridad (roles, módulos y permisos).

Reportes: de ventas, de inventario y de productos más vendidos, con filtros. Se pueden descargar en Excel (XLSX) o PDF, o \
enviar al correo del usuario registrado. Los usan el Administrador y el Super usuario.

Notificaciones por correo: el sistema envía correos automáticos por registro de usuario, venta, stock bajo, alerta de \
condiciones de la bodega y envío de reportes. La página Notificaciones muestra el estado de cada envío (pendiente, enviada o \
fallida).

Circuito de sensores: mide la temperatura y la presión de la bodega cada 30 segundos y las envía al sistema. Si una lectura \
sale de los límites configurados se genera una alerta, suena el buzzer y se envía un correo a los administradores (con una \
pausa entre alertas). La gráfica de temperatura se ve en el Panel.

Auditoría: registra las acciones de los usuarios (por ejemplo crear o actualizar una venta) y quién las hizo.

Chat: los usuarios conectados pueden chatear en tiempo real dentro del sistema.
"""

INSTRUCCION = """\
Eres el asistente de LuxMotos, una tienda de accesorios para moto. Responde siempre en español, de forma breve y clara.

Recibirás la pregunta junto con un bloque "DATOS ACTUALES DEL SISTEMA" que arma el sistema con lo que ese usuario tiene \
permitido ver. Responde usando SOLO esos datos y la información de funcionamiento de abajo. Nunca inventes cifras, nombres \
ni productos: si lo que se pregunta no está en los datos, dilo (puede que ese rol no tenga acceso a ello). Los nombres de \
clientes aparecen como códigos (por ejemplo CLI-12); úsalos tal cual. Muestra el dinero en pesos colombianos (COP).

{conocimiento}

Escribe texto sencillo, sin tablas; para varias filas usa viñetas cortas.
"""

INSTRUCCION_GENERAL = """\
Eres el asistente de LuxMotos, una tienda de accesorios para moto, y atiendes por Telegram. Responde siempre en español, \
de forma breve y clara, en texto plano (sin Markdown, sin asteriscos y sin tablas; para varias cosas usa líneas cortas con guion).

Solo puedes responder con la información de funcionamiento del sistema que aparece abajo. NO tienes acceso a los datos \
del negocio en tiempo real (stock, ventas, clientes, precios, proveedores): si te los piden, explica que esos datos se \
consultan desde la página web de LuxMotos iniciando sesión (cada rol ve solo lo que tiene permitido). Nunca inventes cifras, \
nombres, productos, horarios ni políticas: si algo no está en la información de abajo, dilo y sugiere preguntar en la tienda.

{conocimiento}
"""


def _cargar_conocimiento() -> str:
    texto = CONOCIMIENTO_BASE
    try:
        if ARCHIVO_CONOCIMIENTO.is_file():
            extra = ARCHIVO_CONOCIMIENTO.read_text(encoding="utf-8").strip()
            if extra:
                texto += "\nINFORMACIÓN ADICIONAL\n" + extra
    except OSError as error:
        logger.warning("No se pudo leer %s: %s", ARCHIVO_CONOCIMIENTO, error)
    return texto


def _historial_valido(historial: Optional[list[dict]]) -> list[dict]:
    limpio = []
    for turno in historial or []:
        rol = turno.get("role")
        contenido = turno.get("content")
        if rol in ("user", "assistant") and isinstance(contenido, str) and contenido.strip():
            limpio.append({"role": rol, "content": contenido.strip()[:MAX_CARACTERES_TURNO]})
    return limpio[-MAX_TURNOS_HISTORIAL:]


class ServicioAsistente:
    def __init__(self):
        conocimiento = _cargar_conocimiento()
        self._instruccion = INSTRUCCION.format(conocimiento=conocimiento)
        self._instruccion_general = INSTRUCCION_GENERAL.format(conocimiento=conocimiento)

    @property
    def instruccion(self) -> str:
        return self._instruccion

    @property
    def configurado(self) -> bool:
        return bool(configuracion.groq_api_key)

    @property
    def modelo(self) -> str:
        return configuracion.groq_modelo

    # ------------------------------------------------------------ Groq
    @staticmethod
    def _groq(mensajes: list[dict]) -> dict:
        cuerpo = {
            "model": configuracion.groq_modelo,
            "messages": mensajes,
            "temperature": 0.1,
            "max_tokens": MAX_TOKENS_RESPUESTA,
        }
        if configuracion.groq_modelo.startswith("openai/gpt-oss"):
            cuerpo["reasoning_effort"] = "low"  # respuestas rápidas; no hace falta razonar a fondo para leer un resumen
        cabeceras = {"Authorization": f"Bearer {configuracion.groq_api_key}"}
        url = f"{configuracion.groq_url}/chat/completions"

        try:
            estado, _, texto = peticion("POST", url, cuerpo, cabeceras, configuracion.asistente_timeout)
        except OSError as error:
            logger.warning("No se pudo conectar con Groq: %s", error)
            raise ServicioNoDisponibleException("No se pudo conectar con el modelo de IA. Intenta de nuevo.") from error

        if estado == 200:
            try:
                return json.loads(texto)
            except json.JSONDecodeError as error:
                raise ServicioNoDisponibleException("El modelo devolvió una respuesta no válida.") from error
        if estado in (401, 403):
            logger.warning("Groq rechazó la clave (%s)", estado)
            raise ServicioNoDisponibleException("La clave del modelo de IA no es válida o fue revocada.")
        if estado == 413 or (estado == 400 and "too large" in texto.lower()):
            raise ServicioNoDisponibleException("La consulta es demasiado grande para el modelo. Haz una pregunta más concreta.")
        if estado == 429:
            raise ServicioNoDisponibleException(
                "Se alcanzó el límite de uso del modelo de IA. Espera unos segundos e inténtalo de nuevo."
            )
        logger.warning("Groq respondió %s: %s", estado, texto[:300])
        raise ServicioNoDisponibleException(f"El modelo de IA no pudo responder (error {estado}). Intenta reformular la pregunta.")

    # ------------------------------------------------------------ pregunta
    def preguntar(self, pregunta: str, contexto: str, historial: Optional[list[dict]] = None) -> str:
        if not self.configurado:
            raise ServicioNoDisponibleException("El asistente en la nube no está configurado en el servidor.")
        pregunta = (pregunta or "").strip()
        if not pregunta:
            raise SolicitudInvalidaException("Escribe una pregunta")

        contexto = (contexto or "").strip()[:MAX_CARACTERES_CONTEXTO]
        if contexto:
            usuario = f"DATOS ACTUALES DEL SISTEMA:\n{contexto}\n\nPREGUNTA: {pregunta}"
        else:
            usuario = f"(No se enviaron datos del sistema para esta pregunta.)\n\nPREGUNTA: {pregunta}"

        mensajes = [{"role": "system", "content": self._instruccion}]
        mensajes += _historial_valido(historial)
        mensajes.append({"role": "user", "content": usuario})

        return self._texto_de(self._groq(mensajes))

    def responder_general(self, pregunta: str, historial: Optional[list[dict]] = None) -> str:
        """Respuesta sin datos del negocio (la usa el bot de Telegram): solo el conocimiento de funcionamiento del sistema."""
        if not self.configurado:
            raise ServicioNoDisponibleException("El asistente en la nube no está configurado en el servidor.")
        pregunta = (pregunta or "").strip()
        if not pregunta:
            raise SolicitudInvalidaException("Escribe una pregunta")

        mensajes = [{"role": "system", "content": self._instruccion_general}]
        mensajes += _historial_valido(historial)
        mensajes.append({"role": "user", "content": pregunta})
        return self._texto_de(self._groq(mensajes))

    @staticmethod
    def _texto_de(datos: dict) -> str:
        try:
            texto = (datos["choices"][0]["message"].get("content") or "").strip()
        except (KeyError, IndexError, TypeError, AttributeError) as error:
            raise ServicioNoDisponibleException("El modelo devolvió una respuesta inesperada.") from error
        return texto or "No obtuve respuesta, intenta de nuevo."


_instancia: Optional[ServicioAsistente] = None
_cerrojo = threading.Lock()


def obtener_servicio_asistente() -> ServicioAsistente:
    """Una sola instancia para todo el servidor (el texto de conocimiento se arma una vez)."""
    global _instancia
    with _cerrojo:
        if _instancia is None:
            _instancia = ServicioAsistente()
        return _instancia