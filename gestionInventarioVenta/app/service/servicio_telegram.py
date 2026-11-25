import hmac
import logging
import re
import threading
import time
from collections import OrderedDict, deque
from typing import Optional

from app.client.http_json import peticion
from app.config.configuracion import configuracion
from app.exception.api_exception import ApiException
from app.service.servicio_asistente import ServicioAsistente, obtener_servicio_asistente

logger = logging.getLogger("app.service.servicio_telegram")

MAX_CARACTERES_PREGUNTA = 500
MAX_CARACTERES_RESPUESTA = 3800  # Telegram acepta hasta 4096 por mensaje
MAX_MENSAJES_POR_MINUTO = 8
MAX_TURNOS_HISTORIAL = 6
MAX_CHATS_EN_MEMORIA = 200
MAX_ACTUALIZACIONES_VISTAS = 500
TIMEOUT_TELEGRAM = 15.0

BIENVENIDA = (
    "Hola, soy el asistente de LuxMotos.\n\n"
    "Puedo explicarte cómo funciona el sistema: el IVA, cuándo se descuenta el stock, los roles, los reportes, "
    "las notificaciones y el circuito de sensores de la bodega.\n\n"
    "No tengo acceso a los datos del negocio (stock, ventas, clientes). Esos se consultan desde la página web "
    "iniciando sesión.\n\n"
    "Escríbeme tu pregunta. Con /nuevo empiezo una conversación nueva."
)


def _quitar_markdown(texto: str) -> str:
    texto = re.sub(r"\*\*(.+?)\*\*", r"\1", texto, flags=re.S)
    texto = re.sub(r"__(.+?)__", r"\1", texto, flags=re.S)
    texto = re.sub(r"`([^`]*)`", r"\1", texto)
    texto = re.sub(r"^#{1,6}\s+", "", texto, flags=re.M)
    texto = re.sub(r"^\s*\*\s+", "- ", texto, flags=re.M)
    return texto.strip()


class ServicioTelegram:
    """Bot de Telegram por webhook. Solo responde con el conocimiento de funcionamiento del sistema (sin datos del negocio)."""

    def __init__(self, asistente: Optional[ServicioAsistente] = None, config=configuracion):
        self.asistente = asistente or obtener_servicio_asistente()
        self.config = config
        self._cerrojo = threading.Lock()
        self._historiales: "OrderedDict[int, list[dict]]" = OrderedDict()
        self._tiempos: dict[int, deque] = {}
        self._vistas: "OrderedDict[int, None]" = OrderedDict()

    @property
    def configurado(self) -> bool:
        return bool(self.config.telegram_bot_token and self.config.telegram_webhook_secreto)

    def secreto_valido(self, recibido: Optional[str]) -> bool:
        if not self.configurado or not recibido:
            return False
        return hmac.compare_digest(recibido.encode("utf-8"), self.config.telegram_webhook_secreto.encode("utf-8"))

    # ------------------------------------------------------------ webhook
    def registrar_webhook(self) -> None:
        """Le dice a Telegram a qué dirección avisar. Nunca lanza ni escribe el token en los registros."""
        if not self.configurado:
            return
        if not self.config.url_publica:
            logger.info("Telegram: sin PUBLIC_URL/RENDER_EXTERNAL_URL, no se registra el webhook (modo local).")
            return
        cuerpo = {
            "url": f"{self.config.url_publica}/telegram/webhook",
            "secret_token": self.config.telegram_webhook_secreto,
            "allowed_updates": ["message"],
        }
        try:
            estado, _, texto = peticion("POST", self._url("setWebhook"), cuerpo, None, TIMEOUT_TELEGRAM)
        except OSError as error:
            logger.warning("Telegram: no se pudo registrar el webhook (%s)", type(error).__name__)
            return
        if 200 <= estado < 300:
            logger.info("Telegram: webhook registrado en %s/telegram/webhook", self.config.url_publica)
        else:
            logger.warning("Telegram: setWebhook respondió %s: %s", estado, texto[:200])

    def registrar_webhook_en_segundo_plano(self) -> None:
        if self.configurado:
            threading.Thread(target=self.registrar_webhook, name="telegram-webhook", daemon=True).start()

    # ------------------------------------------------------------ mensajes
    def procesar_actualizacion(self, actualizacion: dict) -> None:
        """Atiende una actualización de Telegram. Nunca lanza: un fallo se registra y listo."""
        try:
            self._procesar(actualizacion)
        except Exception:  # noqa: BLE001 - el webhook no debe fallar por un mensaje raro
            logger.exception("Telegram: error atendiendo una actualización")

    def _procesar(self, actualizacion: dict) -> None:
        if not isinstance(actualizacion, dict) or self._ya_vista(actualizacion.get("update_id")):
            return
        mensaje = actualizacion.get("message")
        if not isinstance(mensaje, dict):
            return
        chat = mensaje.get("chat") or {}
        chat_id = chat.get("id")
        if not isinstance(chat_id, int) or chat.get("type") != "private":
            return  # solo conversaciones privadas

        texto = mensaje.get("text")
        if not isinstance(texto, str) or not texto.strip():
            self._enviar(chat_id, "Por ahora solo entiendo mensajes de texto.")
            return
        texto = texto.strip()

        comando = texto.split()[0].split("@")[0].lower() if texto.startswith("/") else ""
        if comando in ("/start", "/ayuda", "/help"):
            self._enviar(chat_id, BIENVENIDA)
            return
        if comando == "/nuevo":
            with self._cerrojo:
                self._historiales.pop(chat_id, None)
            self._enviar(chat_id, "Listo, empecemos de nuevo. ¿Qué quieres saber?")
            return
        if comando:
            self._enviar(chat_id, "No conozco ese comando. Escríbeme tu pregunta o usa /ayuda.")
            return

        if not self._permitido(chat_id):
            self._enviar(chat_id, "Estás escribiendo muy rápido. Espera un momento e inténtalo de nuevo.")
            return

        pregunta = texto[:MAX_CARACTERES_PREGUNTA]
        with self._cerrojo:
            historial = list(self._historiales.get(chat_id, []))
        try:
            respuesta = _quitar_markdown(self.asistente.responder_general(pregunta, historial))
        except ApiException as error:
            self._enviar(chat_id, error.message)
            return
        respuesta = respuesta[:MAX_CARACTERES_RESPUESTA] or "No obtuve respuesta, intenta de nuevo."

        with self._cerrojo:
            turnos = self._historiales.pop(chat_id, [])
            turnos += [{"role": "user", "content": pregunta}, {"role": "assistant", "content": respuesta}]
            self._historiales[chat_id] = turnos[-MAX_TURNOS_HISTORIAL:]
            while len(self._historiales) > MAX_CHATS_EN_MEMORIA:
                self._historiales.popitem(last=False)
        self._enviar(chat_id, respuesta)

    # ------------------------------------------------------------ utilidades
    def _ya_vista(self, update_id) -> bool:
        """Telegram reintenta si tarda en recibir respuesta; así no se contesta dos veces lo mismo."""
        if not isinstance(update_id, int):
            return False
        with self._cerrojo:
            if update_id in self._vistas:
                return True
            self._vistas[update_id] = None
            while len(self._vistas) > MAX_ACTUALIZACIONES_VISTAS:
                self._vistas.popitem(last=False)
        return False

    def _permitido(self, chat_id: int) -> bool:
        ahora = time.monotonic()
        with self._cerrojo:
            marcas = self._tiempos.setdefault(chat_id, deque())
            while marcas and ahora - marcas[0] > 60:
                marcas.popleft()
            if len(marcas) >= MAX_MENSAJES_POR_MINUTO:
                return False
            marcas.append(ahora)
            if len(self._tiempos) > MAX_CHATS_EN_MEMORIA * 5:
                for clave in [c for c, m in self._tiempos.items() if not m]:
                    self._tiempos.pop(clave, None)
        return True

    def _url(self, metodo: str) -> str:
        return f"{self.config.telegram_api_url}/bot{self.config.telegram_bot_token}/{metodo}"

    def _enviar(self, chat_id: int, texto: str) -> None:
        try:
            estado, _, cuerpo = peticion("POST", self._url("sendMessage"), {"chat_id": chat_id, "text": texto}, None, TIMEOUT_TELEGRAM)
            if not 200 <= estado < 300:
                logger.warning("Telegram: sendMessage respondió %s: %s", estado, cuerpo[:200])
        except OSError as error:
            logger.warning("Telegram: no se pudo enviar el mensaje (%s)", type(error).__name__)


_instancia: Optional[ServicioTelegram] = None
_cerrojo_instancia = threading.Lock()


def obtener_servicio_telegram() -> ServicioTelegram:
    global _instancia
    with _cerrojo_instancia:
        if _instancia is None:
            _instancia = ServicioTelegram()
        return _instancia