from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from app.config.base_datos import obtener_sesion
from app.config.seguridad import correo_autenticado
from app.dto.notificacion.envio_reporte_response import EnvioReporteResponse
from app.repository.detalle_venta_repository import DetalleVentaRepository
from app.repository.notificacion_correo_repository import NotificacionCorreoRepository
from app.repository.producto_repository import ProductoRepository
from app.repository.usuario_repository import UsuarioRepository
from app.repository.venta_repository import VentaRepository
from app.service.servicio_exportacion_reporte import FiltrosReporte, ServicioExportacionReporte
from app.service.servicio_notificacion import ServicioNotificacion

router = APIRouter(prefix="/reportes", tags=["Reportes (descarga y envío por correo)"])


def obtener_servicio_exportacion_reporte(db: Session = Depends(obtener_sesion)) -> ServicioExportacionReporte:
    return ServicioExportacionReporte(
        VentaRepository(db),
        DetalleVentaRepository(db),
        ProductoRepository(db),
        UsuarioRepository(db),
        ServicioNotificacion(NotificacionCorreoRepository(db)),
    )


def filtros_reporte(
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    estado_venta: Optional[str] = None,
    solo_stock_bajo: bool = False,
    categoria_id: Optional[int] = None,
) -> FiltrosReporte:
    return FiltrosReporte(desde, hasta, estado_venta or None, solo_stock_bajo, categoria_id)


@router.get("/exportar/{tipo}")
def exportar(
    tipo: str,
    formato: str = "xlsx",
    filtros: FiltrosReporte = Depends(filtros_reporte),
    correo: str = Depends(correo_autenticado),
    servicio: ServicioExportacionReporte = Depends(obtener_servicio_exportacion_reporte),
):
    """Descarga el reporte (tipo: ventas, inventario, productos-mas-vendidos; formato: xlsx o pdf)."""
    archivo = servicio.generar_archivo(tipo, formato, filtros, correo)
    return FileResponse(
        archivo.ruta,
        media_type=archivo.tipo_mime,
        filename=archivo.nombre,
        background=BackgroundTask(archivo.eliminar),
    )


@router.post("/enviar/{tipo}", response_model=EnvioReporteResponse)
def enviar_por_correo(
    tipo: str,
    formato: str = "xlsx",
    filtros: FiltrosReporte = Depends(filtros_reporte),
    correo: str = Depends(correo_autenticado),
    servicio: ServicioExportacionReporte = Depends(obtener_servicio_exportacion_reporte),
):
    """Envía el reporte, como adjunto, al correo del usuario que hace la solicitud."""
    return servicio.enviar_por_correo(tipo, formato, filtros, correo)