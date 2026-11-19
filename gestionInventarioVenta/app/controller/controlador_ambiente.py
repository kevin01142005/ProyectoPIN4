import hmac
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query

from app.config.configuracion import configuracion
from app.config.inyeccion import obtener_servicio_lectura_ambiente
from app.dto.ambiente.lectura_ambiente_request import LecturaAmbienteRequest
from app.dto.ambiente.lectura_ambiente_response import LecturaAmbienteResponse, ResumenAmbienteResponse
from app.exception.api_exception import AccesoDenegadoException
from app.service.servicio_lectura_ambiente import ServicioLecturaAmbiente

router = APIRouter(prefix="/ambiente", tags=["Ambiente (circuito de sensores)"])


def validar_clave_dispositivo(x_api_key: Optional[str] = Header(default=None)) -> None:
    """El circuito no inicia sesión como usuario: se identifica con una clave propia."""
    esperada = configuracion.dispositivo_api_key
    if not esperada or x_api_key is None or not hmac.compare_digest(x_api_key, esperada):
        raise AccesoDenegadoException()


@router.post("/lecturas", response_model=LecturaAmbienteResponse, status_code=201)
def registrar(
    request: LecturaAmbienteRequest,
    _clave: None = Depends(validar_clave_dispositivo),
    servicio: ServicioLecturaAmbiente = Depends(obtener_servicio_lectura_ambiente),
):
    return servicio.registrar(request)


@router.get("/lecturas", response_model=list[LecturaAmbienteResponse])
def listar(
    horas: int = Query(24, ge=1, le=720),
    limite: int = Query(500, ge=1, le=5000),
    servicio: ServicioLecturaAmbiente = Depends(obtener_servicio_lectura_ambiente),
):
    return servicio.listar(horas, limite)


@router.get("/ultima", response_model=Optional[LecturaAmbienteResponse])
def ultima(servicio: ServicioLecturaAmbiente = Depends(obtener_servicio_lectura_ambiente)):
    return servicio.ultima()


@router.get("/resumen", response_model=ResumenAmbienteResponse)
def resumen(
    horas: int = Query(24, ge=1, le=720),
    servicio: ServicioLecturaAmbiente = Depends(obtener_servicio_lectura_ambiente),
):
    return servicio.resumen(horas)
