from fastapi import APIRouter, Depends

from app.dto.asistente.estado_asistente_response import EstadoAsistenteResponse
from app.dto.asistente.pregunta_request import PreguntaRequest
from app.dto.asistente.respuesta_asistente_response import RespuestaAsistenteResponse
from app.service.servicio_asistente import ServicioAsistente, obtener_servicio_asistente

router = APIRouter(prefix="/asistente", tags=["Asistente de IA"])


@router.get("/estado", response_model=EstadoAsistenteResponse)
def estado(servicio: ServicioAsistente = Depends(obtener_servicio_asistente)):
    """Dice si Groq está configurado y entrega las instrucciones del asistente (las usa también el motor local Ollama)."""
    return EstadoAsistenteResponse(configurado=servicio.configurado, modelo=servicio.modelo, instruccion=servicio.instruccion)


@router.post("/chat", response_model=RespuestaAsistenteResponse)
def chat(request: PreguntaRequest, servicio: ServicioAsistente = Depends(obtener_servicio_asistente)):
    """Puente hacia Groq: guarda la clave del modelo y no toca la base de datos (los datos llegan en `contexto`)."""
    historial = [{"role": t.role, "content": t.content} for t in request.historial]
    return RespuestaAsistenteResponse(respuesta=servicio.preguntar(request.pregunta, request.contexto, historial))