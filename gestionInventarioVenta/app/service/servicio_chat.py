from typing import Optional

from app.model.mensaje_chat import MensajeChat
from app.repository.mensaje_chat_repository import MensajeChatRepository
from app.repository.modulo_x_rol_repository import ModuloXRolRepository
from app.repository.usuario_repository import UsuarioRepository
from app.service.servicio_jwt import ServicioJwt

RUTA_MODULO_CHAT = "/chat"
LIMITE_HISTORIAL = 50
LARGO_MAXIMO_MENSAJE = 500


def a_diccionario(mensaje: MensajeChat) -> dict:
    return {
        "tipo": "mensaje",
        "id": mensaje.id,
        "usuarioId": mensaje.usuario_id,
        "autor": mensaje.autor,
        "texto": mensaje.texto,
        "hora": mensaje.creado.isoformat(),
    }


class ServicioChat:
    def __init__(
        self,
        mensaje_repository: MensajeChatRepository,
        usuario_repository: UsuarioRepository,
        modulo_x_rol_repository: ModuloXRolRepository,
        servicio_jwt: ServicioJwt,
    ):
        self.mensaje_repository = mensaje_repository
        self.usuario_repository = usuario_repository
        self.modulo_x_rol_repository = modulo_x_rol_repository
        self.servicio_jwt = servicio_jwt

    def autenticar(self, token: Optional[str]) -> Optional[tuple[int, str]]:
        """Valida el JWT igual que el resto de la API. Devuelve (id, nombre) o None si el token no sirve.

        Lanza PermissionError si el usuario es válido pero su rol no tiene el módulo Chat."""
        if not token or not self.servicio_jwt.es_token_valido(token):
            return None
        correo = self.servicio_jwt.extraer_correo(token)
        if correo is None:
            return None
        usuario = self.usuario_repository.find_by_correo(correo)
        if usuario is None or not usuario.estado or not usuario.rol.estado:
            return None
        if self.modulo_x_rol_repository.find_permiso_activo(usuario.rol_id, RUTA_MODULO_CHAT) is None:
            raise PermissionError("El rol no tiene acceso al chat")
        return usuario.id, usuario.nombre_completo

    def guardar(self, usuario_id: int, autor: str, texto: str) -> Optional[dict]:
        texto = texto.strip()[:LARGO_MAXIMO_MENSAJE]
        if not texto:
            return None
        mensaje = self.mensaje_repository.save(MensajeChat(usuario_id=usuario_id, autor=autor, texto=texto))
        return a_diccionario(mensaje)

    def historial(self, limite: int = LIMITE_HISTORIAL) -> list[dict]:
        return [a_diccionario(m) for m in self.mensaje_repository.find_ultimos(limite)]