import logging
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from app.config.base_datos import SesionLocal
from app.repository.mensaje_chat_repository import MensajeChatRepository
from app.repository.modulo_x_rol_repository import ModuloXRolRepository
from app.repository.usuario_repository import UsuarioRepository
from app.service.gestor_conexiones_chat import gestor_conexiones_chat as gestor
from app.service.servicio_chat import ServicioChat
from app.service.servicio_jwt import obtener_servicio_jwt

log = logging.getLogger(__name__)

CODIGO_NO_AUTORIZADO = 4401
CODIGO_SIN_PERMISO = 4403


def _con_servicio(accion):
    """Abre una sesión de base de datos corta, ejecuta la acción y la cierra."""
    with SesionLocal() as db:
        servicio = ServicioChat(
            MensajeChatRepository(db),
            UsuarioRepository(db),
            ModuloXRolRepository(db),
            obtener_servicio_jwt(),
        )
        return accion(servicio)


async def chat_websocket(ws: WebSocket) -> None:
    """Sala de chat en tiempo real. El token JWT llega en la URL: /ws/chat?token=..."""
    await ws.accept()

    try:
        persona: Optional[tuple[int, str]] = await run_in_threadpool(
            _con_servicio, lambda s: s.autenticar(ws.query_params.get("token"))
        )
    except PermissionError:
        await ws.close(code=CODIGO_SIN_PERMISO)
        return
    if persona is None:
        await ws.close(code=CODIGO_NO_AUTORIZADO)
        return
    usuario_id, nombre = persona

    try:
        historial = await run_in_threadpool(_con_servicio, lambda s: s.historial())
    except Exception:
        log.exception("No se pudo leer el historial del chat")
        historial = []

    await gestor.enviar_a(ws, {"tipo": "bienvenida", "usuarioId": usuario_id, "nombre": nombre})
    await gestor.enviar_a(ws, {"tipo": "historial", "mensajes": historial})
    gestor.registrar(ws, usuario_id, nombre)
    await gestor.difundir_aviso(f"{nombre} se conectó")
    await gestor.difundir_conectados()

    try:
        while True:
            datos = await ws.receive_json()
            if not isinstance(datos, dict) or datos.get("tipo") != "mensaje":
                continue  # "ping" de la interfaz para mantener viva la conexión
            texto = str(datos.get("texto", ""))
            try:
                mensaje = await run_in_threadpool(_con_servicio, lambda s: s.guardar(usuario_id, nombre, texto))
            except Exception:
                log.exception("No se pudo guardar el mensaje del chat")
                await gestor.enviar_a(ws, {"tipo": "error", "texto": "No se pudo guardar el mensaje"})
                continue
            if mensaje is not None:
                await gestor.difundir(mensaje)
    except WebSocketDisconnect:
        pass
    finally:
        if gestor.quitar(ws) is not None:
            await gestor.difundir_aviso(f"{nombre} se desconectó")
            await gestor.difundir_conectados()


def registrar_chat(app: FastAPI) -> None:
    """Se registra como ruta WebSocket simple: el chequeo de permisos de las rutas HTTP
    (autorizar_solicitud) espera una petición HTTP, así que aquí el JWT se valida a mano."""
    app.router.add_websocket_route("/ws/chat", chat_websocket, name="chat")