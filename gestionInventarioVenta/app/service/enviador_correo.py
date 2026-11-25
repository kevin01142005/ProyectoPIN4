import base64
import json
import logging
import re
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional

from app.client.http_json import peticion
from app.config.configuracion import configuracion

logger = logging.getLogger("app.service.enviador_correo")


class CorreoNoConfiguradoError(Exception):
    pass


class CorreoNoEnviadoError(Exception):
    pass


@dataclass(frozen=True)
class Adjunto:
    nombre: str
    contenido: bytes
    tipo_mime: str


class EnviadorCorreo:
    """Envía correos por la API web de Brevo (si hay BREVO_API_KEY) o por SMTP (por defecto Gmail con STARTTLS, puerto 587)."""

    def __init__(self, config=configuracion):
        self.config = config

    def configurado(self) -> bool:
        return bool(self.config.correo_activo and (self.config.brevo_api_key or (self.config.smtp_usuario and self.config.smtp_contrasena)))

    def enviar(self, destinatario: str, asunto: str, html: str, adjunto: Optional[Adjunto] = None) -> None:
        if not self.config.correo_activo:
            raise CorreoNoConfiguradoError("El envío de correos está desactivado (CORREO_ACTIVO=false)")
        if self.config.brevo_api_key:
            self._enviar_brevo(destinatario, asunto, html, adjunto)
            return
        if not (self.config.smtp_usuario and self.config.smtp_contrasena):
            raise CorreoNoConfiguradoError("Faltan BREVO_API_KEY, o bien SMTP_USER y SMTP_PASSWORD, en la configuración del servidor")

        mensaje = self._construir(destinatario, asunto, html, adjunto)
        contexto = ssl.create_default_context()

        if self.config.smtp_puerto == 465:
            with smtplib.SMTP_SSL(
                self.config.smtp_host, self.config.smtp_puerto, timeout=self.config.smtp_timeout, context=contexto
            ) as servidor:
                servidor.login(self.config.smtp_usuario, self.config.smtp_contrasena)
                servidor.send_message(mensaje)
            return

        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_puerto, timeout=self.config.smtp_timeout) as servidor:
            servidor.starttls(context=contexto)
            servidor.login(self.config.smtp_usuario, self.config.smtp_contrasena)
            servidor.send_message(mensaje)

    def _enviar_brevo(self, destinatario: str, asunto: str, html: str, adjunto: Optional[Adjunto]) -> None:
        """API de correo transaccional de Brevo (HTTPS, no usa puertos SMTP). El remitente debe estar verificado en Brevo."""
        remitente = self.config.correo_remitente or self.config.smtp_usuario
        if not remitente:
            raise CorreoNoConfiguradoError("Falta CORREO_REMITENTE (el correo remitente verificado en Brevo)")
        cuerpo: dict = {
            "sender": {"name": self.config.nombre_remitente, "email": remitente},
            "to": [{"email": destinatario}],
            "subject": asunto,
            "htmlContent": html,
            "textContent": _a_texto_plano(html),
        }
        if adjunto is not None:
            cuerpo["attachment"] = [{"name": adjunto.nombre, "content": base64.b64encode(adjunto.contenido).decode("ascii")}]

        try:
            estado, _, texto = peticion(
                "POST",
                f"{self.config.brevo_url}/smtp/email",
                cuerpo,
                {"api-key": self.config.brevo_api_key, "accept": "application/json"},
                self.config.smtp_timeout,
            )
        except OSError as error:
            raise CorreoNoEnviadoError(f"No se pudo conectar con Brevo: {error}") from error

        if 200 <= estado < 300:
            return
        detalle = _detalle_error(texto)
        logger.warning("Brevo respondió %s: %s", estado, detalle)
        if estado in (401, 403):
            raise CorreoNoEnviadoError(f"Brevo rechazó la clave o la cuenta no está activada ({estado}): {detalle}")
        raise CorreoNoEnviadoError(f"Brevo no pudo enviar el correo (error {estado}): {detalle}")

    def _construir(self, destinatario: str, asunto: str, html: str, adjunto: Optional[Adjunto]) -> EmailMessage:
        remitente = self.config.correo_remitente or self.config.smtp_usuario
        mensaje = EmailMessage()
        mensaje["From"] = formataddr((self.config.nombre_remitente, remitente))
        mensaje["To"] = destinatario
        mensaje["Subject"] = asunto
        mensaje.set_content(_a_texto_plano(html))
        mensaje.add_alternative(html, subtype="html")

        if adjunto is not None:
            tipo, _, subtipo = adjunto.tipo_mime.partition("/")
            mensaje.add_attachment(adjunto.contenido, maintype=tipo, subtype=subtipo, filename=adjunto.nombre)
        return mensaje


def _detalle_error(texto: str) -> str:
    try:
        datos = json.loads(texto)
        if isinstance(datos, dict) and datos.get("message"):
            return str(datos["message"])[:300]
    except (json.JSONDecodeError, TypeError):
        pass
    return texto[:300]


def _a_texto_plano(html: str) -> str:
    sin_estilos = re.sub(r"(?is)<(style|head)[^>]*>.*?</\1>", " ", html)
    con_saltos = re.sub(r"(?i)</(p|div|tr|h[1-6]|li)>|<br\s*/?>", "\n", sin_estilos)
    texto = re.sub(r"<[^>]+>", " ", con_saltos)
    texto = re.sub(r"[ \t]+", " ", texto)
    return re.sub(r"\n\s*\n+", "\n\n", texto).strip()


def tipo_mime_de(formato: str) -> str:
    return {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf",
    }[formato]