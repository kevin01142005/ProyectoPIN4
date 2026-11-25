from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Header

from app.exception.api_exception import AccesoDenegadoException
from app.service.servicio_telegram import ServicioTelegram, obtener_servicio_telegram

router = APIRouter(prefix="/telegram", tags=["Telegram"])


@router.post("/webhook", include_in_schema=False)
def webhook(
    tareas: BackgroundTasks,
    actualizacion: dict = Body(...),
    secreto: Optional[str] = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
    servicio: ServicioTelegram = Depends(obtener_servicio_telegram),
):
    """Telegram avisa aquí de cada mensaje. No usa JWT: se valida el secreto que se dio al registrar el webhook.
    Se responde 200 enseguida y la respuesta al usuario se envía en segundo plano."""
    if not servicio.secreto_valido(secreto):
        raise AccesoDenegadoException()
    tareas.add_task(servicio.procesar_actualizacion, actualizacion)
    return {"ok": True}