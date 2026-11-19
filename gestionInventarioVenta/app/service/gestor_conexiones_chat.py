from datetime import datetime, timezone
from typing import Any


class GestorConexionesChat:
    """Lleva las conexiones WebSocket abiertas y reparte los mensajes a todas.

    Vive en memoria del proceso: por eso la API debe correr con un solo worker.
    No usa base de datos; guardar los mensajes es trabajo de ServicioChat.
    """

    def __init__(self) -> None:
        # conexión -> (id del usuario, nombre)
        self._conexiones: dict[Any, tuple[int, str]] = {}

    def registrar(self, ws: Any, usuario_id: int, nombre: str) -> None:
        self._conexiones[ws] = (usuario_id, nombre)

    def quitar(self, ws: Any) -> tuple[int, str] | None:
        return self._conexiones.pop(ws, None)

    def conectados(self) -> list[dict]:
        """Una entrada por usuario (aunque tenga varias pestañas abiertas)."""
        unicos = {uid: nombre for uid, nombre in self._conexiones.values()}
        return [{"id": uid, "nombre": nombre} for uid, nombre in sorted(unicos.items(), key=lambda p: p[1].lower())]

    async def enviar_a(self, ws: Any, datos: dict) -> None:
        await ws.send_json(datos)

    async def difundir(self, datos: dict) -> None:
        caidas = []
        for ws in list(self._conexiones):
            try:
                await ws.send_json(datos)
            except Exception:
                caidas.append(ws)
        for ws in caidas:
            self._conexiones.pop(ws, None)

    async def difundir_conectados(self) -> None:
        await self.difundir({"tipo": "usuarios", "usuarios": self.conectados()})

    async def difundir_aviso(self, texto: str) -> None:
        await self.difundir({"tipo": "sistema", "texto": texto, "hora": datetime.now(timezone.utc).isoformat()})


gestor_conexiones_chat = GestorConexionesChat()