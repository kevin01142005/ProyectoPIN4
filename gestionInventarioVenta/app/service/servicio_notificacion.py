import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.base_datos import SesionLocal
from app.config.configuracion import configuracion
from app.dto.notificacion.notificacion_response import NotificacionResponse, ResumenNotificacionesResponse
from app.model.estado_notificacion import EstadoNotificacion
from app.model.notificacion_correo import NotificacionCorreo
from app.model.rol import Rol
from app.model.rol_usuario import RolUsuario
from app.model.tipo_notificacion import TipoNotificacion
from app.model.usuario import Usuario
from app.repository.notificacion_correo_repository import NotificacionCorreoRepository
from app.service.enviador_correo import Adjunto, EnviadorCorreo

logger = logging.getLogger("app.service.servicio_notificacion")

# Los correos automáticos se envían en un hilo aparte para no demorar la respuesta de la API.
_EJECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="correo")


class ServicioNotificacion:
    def __init__(self, repository: NotificacionCorreoRepository, enviador: Optional[EnviadorCorreo] = None):
        self.repository = repository
        self.enviador = enviador or EnviadorCorreo()

    def enviar(
        self,
        tipo: TipoNotificacion,
        destinatario: str,
        asunto: str,
        html: str,
        referencia: Optional[str] = None,
        adjunto: Optional[Adjunto] = None,
    ) -> NotificacionCorreo:
        """Registra la notificación, intenta enviarla y deja guardado el resultado. Nunca lanza por fallos de SMTP."""
        notificacion = self.repository.save(
            NotificacionCorreo(
                tipo=tipo,
                destinatario=destinatario,
                asunto=asunto[:255],
                referencia=referencia,
                adjunto=adjunto.nombre if adjunto else None,
                estado_envio=EstadoNotificacion.PENDIENTE,
                intentos=0,
            )
        )

        notificacion.intentos = 1
        try:
            self.enviador.enviar(destinatario, asunto, html, adjunto)
            notificacion.estado_envio = EstadoNotificacion.ENVIADA
            notificacion.enviado = datetime.now(timezone.utc)
            notificacion.error = None
        except Exception as ex:  # SMTP caído, credenciales inválidas, correo inexistente, etc.
            logger.warning("No se pudo enviar el correo a %s: %s", destinatario, ex)
            notificacion.estado_envio = EstadoNotificacion.FALLIDA
            notificacion.error = f"{type(ex).__name__}: {ex}"[:500]

        return self.repository.save(notificacion)

    def listar(self, estado_envio: Optional[EstadoNotificacion], limite: int) -> list[NotificacionResponse]:
        return [self.a_response(n) for n in self.repository.find_recientes(estado_envio, limite)]

    def resumen(self) -> ResumenNotificacionesResponse:
        conteo = self.repository.contar_por_estado()
        pendientes = conteo.get(EstadoNotificacion.PENDIENTE, 0)
        enviadas = conteo.get(EstadoNotificacion.ENVIADA, 0)
        fallidas = conteo.get(EstadoNotificacion.FALLIDA, 0)
        return ResumenNotificacionesResponse(
            total=pendientes + enviadas + fallidas, pendientes=pendientes, enviadas=enviadas, fallidas=fallidas
        )

    @staticmethod
    def a_response(n: NotificacionCorreo) -> NotificacionResponse:
        return NotificacionResponse(
            id=n.id,
            tipo=n.tipo,
            destinatario=n.destinatario,
            asunto=n.asunto,
            referencia=n.referencia,
            adjunto=n.adjunto,
            estado_envio=n.estado_envio,
            intentos=n.intentos,
            error=n.error,
            enviado=n.enviado,
            creado=n.creado,
        )


def correos_administradores(sesion: Session) -> list[str]:
    """Destinatarios de las alertas: CORREOS_ALERTA si está definido; si no, administradores activos."""
    if configuracion.correos_alerta:
        return list(configuracion.correos_alerta)
    consulta = (
        select(Usuario.correo)
        .join(Rol, Usuario.rol_id == Rol.id)
        .where(
            Usuario.estado.is_(True),
            Rol.estado.is_(True),
            Rol.nombre.in_([RolUsuario.ADMINISTRADOR, RolUsuario.SUPER_USUARIO]),
        )
        .order_by(Usuario.id)
    )
    return list(sesion.scalars(consulta).all())


def notificar_en_segundo_plano(
    tipo: TipoNotificacion,
    asunto: str,
    html: str,
    para: Optional[Iterable[str]] = None,
    referencia: Optional[str] = None,
    minutos_entre_alertas: int = 0,
) -> None:
    """Envía una notificación sin bloquear la petición. Si 'para' es None, va a los administradores."""
    destinos = None if para is None else list(para)

    def tarea() -> None:
        try:
            with SesionLocal() as sesion:
                repositorio = NotificacionCorreoRepository(sesion)
                if minutos_entre_alertas > 0:
                    desde = datetime.now(timezone.utc) - timedelta(minutes=minutos_entre_alertas)
                    if repositorio.existe_reciente(tipo, desde, referencia):
                        return

                servicio = ServicioNotificacion(repositorio)
                lista = destinos if destinos is not None else correos_administradores(sesion)
                for destinatario in dict.fromkeys(c.strip().lower() for c in lista if c):
                    servicio.enviar(tipo, destinatario, asunto, html, referencia)
        except Exception:
            logger.exception("Falló la notificación automática de tipo %s", tipo.value)

    _EJECUTOR.submit(tarea)