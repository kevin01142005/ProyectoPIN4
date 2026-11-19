import re
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional

from app.config.configuracion import configuracion


class CorreoNoConfiguradoError(Exception):
    pass


@dataclass(frozen=True)
class Adjunto:
    nombre: str
    contenido: bytes
    tipo_mime: str


class EnviadorCorreo:
    """Envía correos por SMTP (por defecto Gmail con STARTTLS en el puerto 587)."""

    def __init__(self, config=configuracion):
        self.config = config

    def configurado(self) -> bool:
        return bool(self.config.correo_activo and self.config.smtp_usuario and self.config.smtp_contrasena)

    def enviar(self, destinatario: str, asunto: str, html: str, adjunto: Optional[Adjunto] = None) -> None:
        if not self.config.correo_activo:
            raise CorreoNoConfiguradoError("El envío de correos está desactivado (CORREO_ACTIVO=false)")
        if not (self.config.smtp_usuario and self.config.smtp_contrasena):
            raise CorreoNoConfiguradoError("Faltan SMTP_USER y SMTP_PASSWORD en la configuración del servidor")

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