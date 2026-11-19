"""Importa todas las entidades para registrarlas en Base.metadata."""
from app.model.accion_auditoria import AccionAuditoria
from app.model.categoria import Categoria
from app.model.cliente import Cliente
from app.model.detalle_venta import DetalleVenta
from app.model.estado_notificacion import EstadoNotificacion
from app.model.estado_venta import EstadoVenta
from app.model.factura import Factura
from app.model.lectura_ambiente import LecturaAmbiente
from app.model.mensaje_chat import MensajeChat
from app.model.modulo import Modulo
from app.model.modulo_x_rol import ModuloXRol
from app.model.movimiento_inventario import MovimientoInventario
from app.model.notificacion_correo import NotificacionCorreo
from app.model.producto import Producto
from app.model.producto_compatibilidad import ProductoCompatibilidad
from app.model.proveedor import Proveedor
from app.model.registro_auditoria import RegistroAuditoria
from app.model.rol import Rol
from app.model.rol_usuario import RolUsuario
from app.model.tipo_movimiento_inventario import TipoMovimientoInventario
from app.model.tipo_notificacion import TipoNotificacion
from app.model.usuario import Usuario
from app.model.venta import Venta

__all__ = [
    "AccionAuditoria", "Categoria", "Cliente", "DetalleVenta", "EstadoNotificacion", "EstadoVenta", "Factura", "LecturaAmbiente", "MensajeChat", "Modulo",
    "ModuloXRol", "MovimientoInventario", "NotificacionCorreo", "Producto", "ProductoCompatibilidad", "Proveedor", "RegistroAuditoria", "Rol",
    "RolUsuario", "TipoMovimientoInventario", "TipoNotificacion", "Usuario", "Venta",
]