from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config.base_datos import obtener_sesion
from app.dto.notificacion.notificacion_response import NotificacionResponse, ResumenNotificacionesResponse
from app.exception.api_exception import SolicitudInvalidaException
from app.model.estado_notificacion import EstadoNotificacion
from app.repository.notificacion_correo_repository import NotificacionCorreoRepository
from app.service.servicio_notificacion import ServicioNotificacion

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones por correo"])


def obtener_servicio_notificacion(db: Session = Depends(obtener_sesion)) -> ServicioNotificacion:
    return ServicioNotificacion(NotificacionCorreoRepository(db))


@router.get("", response_model=list[NotificacionResponse])
def listar(
    estado: Optional[str] = None,
    limite: int = Query(200, ge=1, le=1000),
    servicio: ServicioNotificacion = Depends(obtener_servicio_notificacion),
):
    estado_envio = None
    if estado:
        try:
            estado_envio = EstadoNotificacion(estado.upper())
        except ValueError:
            raise SolicitudInvalidaException("Estado no válido. Usa PENDIENTE, ENVIADA o FALLIDA") from None
    return servicio.listar(estado_envio, limite)


@router.get("/resumen", response_model=ResumenNotificacionesResponse)
def resumen(servicio: ServicioNotificacion = Depends(obtener_servicio_notificacion)):
    return servicio.resumen()