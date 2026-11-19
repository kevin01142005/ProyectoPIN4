import shutil
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional

from app.dto.notificacion.envio_reporte_response import EnvioReporteResponse
from app.exception.api_exception import RecursoNoEncontradoException, ServicioNoDisponibleException, SolicitudInvalidaException
from app.model.estado_notificacion import EstadoNotificacion
from app.model.estado_venta import EstadoVenta
from app.model.tipo_notificacion import TipoNotificacion
from app.repository.detalle_venta_repository import DetalleVentaRepository
from app.repository.producto_repository import ProductoRepository
from app.repository.usuario_repository import UsuarioRepository
from app.repository.venta_repository import VentaRepository
from app.service.enviador_correo import Adjunto, tipo_mime_de
from app.service.servicio_notificacion import ServicioNotificacion
from app.util.anio_mes import inicio_del_dia, zona
from app.util.exportador_reporte import ENTERO, FECHA, MONEDA, Columna, DatosReporte, generar_pdf, generar_xlsx
from app.util.plantillas_correo import construir_html

TITULOS = {
    "ventas": "Reporte de ventas",
    "inventario": "Reporte de inventario",
    "productos-mas-vendidos": "Productos más vendidos",
}
FORMATOS = ("xlsx", "pdf")


@dataclass(frozen=True)
class FiltrosReporte:
    desde: Optional[date] = None
    hasta: Optional[date] = None
    estado_venta: Optional[str] = None
    solo_stock_bajo: bool = False
    categoria_id: Optional[int] = None


@dataclass
class ArchivoReporte:
    """Archivo guardado temporalmente en disco; se borra después de entregarlo o enviarlo."""

    nombre: str
    ruta: Path
    tipo_mime: str

    def leer(self) -> bytes:
        return self.ruta.read_bytes()

    def eliminar(self) -> None:
        shutil.rmtree(self.ruta.parent, ignore_errors=True)


class ServicioExportacionReporte:
    def __init__(
        self,
        venta_repository: VentaRepository,
        detalle_venta_repository: DetalleVentaRepository,
        producto_repository: ProductoRepository,
        usuario_repository: UsuarioRepository,
        servicio_notificacion: ServicioNotificacion,
    ):
        self.venta_repository = venta_repository
        self.detalle_venta_repository = detalle_venta_repository
        self.producto_repository = producto_repository
        self.usuario_repository = usuario_repository
        self.servicio_notificacion = servicio_notificacion

    def generar_archivo(self, tipo: str, formato: str, filtros: FiltrosReporte, correo: str) -> ArchivoReporte:
        self._validar(tipo, formato, filtros)
        usuario = self.usuario_repository.find_by_correo(correo)
        datos = self._armar(tipo, filtros, usuario.nombre_completo if usuario else correo)

        contenido = generar_xlsx(datos) if formato == "xlsx" else generar_pdf(datos)
        nombre = f"reporte_{tipo.replace('-', '_')}_{datetime.now(zona()):%Y%m%d_%H%M%S}.{formato}"

        carpeta = Path(tempfile.mkdtemp(prefix="luxmotos_reporte_"))
        ruta = carpeta / nombre
        ruta.write_bytes(contenido)
        return ArchivoReporte(nombre=nombre, ruta=ruta, tipo_mime=tipo_mime_de(formato))

    def enviar_por_correo(self, tipo: str, formato: str, filtros: FiltrosReporte, correo: str) -> EnvioReporteResponse:
        archivo = self.generar_archivo(tipo, formato, filtros, correo)
        try:
            usuario = self.usuario_repository.find_by_correo(correo)
            nombre = usuario.nombre_completo if usuario else correo
            titulo = TITULOS[tipo]
            asunto = f"{titulo} ({formato.upper()}) · LuxMotos"
            html = construir_html(
                "Tu reporte está listo",
                [
                    f"Hola {nombre},",
                    f"Adjuntamos el {titulo.lower()} en formato {formato.upper()}, generado el "
                    f"{datetime.now(zona()):%d/%m/%Y a las %H:%M}.",
                    "El archivo se creó solo para este envío y no se guarda en el servidor.",
                ],
            )
            notificacion = self.servicio_notificacion.enviar(
                TipoNotificacion.REPORTE_ENVIADO,
                correo,
                asunto,
                html,
                referencia=tipo,
                adjunto=Adjunto(archivo.nombre, archivo.leer(), archivo.tipo_mime),
            )
        finally:
            archivo.eliminar()

        if notificacion.estado_envio != EstadoNotificacion.ENVIADA:
            raise ServicioNoDisponibleException(
                f"No se pudo enviar el reporte a {correo}. Revisa la configuración del correo del servidor "
                f"(detalle en el módulo Notificaciones, registro #{notificacion.id})."
            )
        return EnvioReporteResponse(
            mensaje=f"El reporte se envió a {correo}",
            destinatario=correo,
            notificacion_id=notificacion.id,
            estado_envio=notificacion.estado_envio,
        )

    @staticmethod
    def _validar(tipo: str, formato: str, filtros: FiltrosReporte) -> None:
        if tipo not in TITULOS:
            raise RecursoNoEncontradoException(f"Tipo de reporte desconocido. Opciones: {', '.join(TITULOS)}")
        if formato not in FORMATOS:
            raise SolicitudInvalidaException("Formato no válido. Usa 'xlsx' o 'pdf'")
        if filtros.desde and filtros.hasta and filtros.desde > filtros.hasta:
            raise SolicitudInvalidaException("La fecha 'desde' no puede ser posterior a la fecha 'hasta'")
        if filtros.estado_venta and filtros.estado_venta not in {e.value for e in EstadoVenta}:
            raise SolicitudInvalidaException("Estado de venta no válido")

    def _armar(self, tipo: str, filtros: FiltrosReporte, generado_por: str) -> DatosReporte:
        constructor = {
            "ventas": self._ventas,
            "inventario": self._inventario,
            "productos-mas-vendidos": self._mas_vendidos,
        }[tipo]
        datos = constructor(filtros)
        return DatosReporte(
            titulo=TITULOS[tipo],
            columnas=datos.columnas,
            filas=datos.filas,
            filtros=datos.filtros,
            totales=datos.totales,
            generado_por=generado_por,
            generado_en=datetime.now(zona()).replace(tzinfo=None),
        )

    def _ventas(self, f: FiltrosReporte) -> DatosReporte:
        filas, sub, iva, total = [], Decimal(0), Decimal(0), Decimal(0)
        for v in self.venta_repository.find_all_order_by_creado_desc():
            fecha = v.creado.astimezone(zona())
            if (f.desde and fecha.date() < f.desde) or (f.hasta and fecha.date() > f.hasta):
                continue
            if f.estado_venta and v.estado_venta.value != f.estado_venta:
                continue
            filas.append(
                [f"#{v.id}", fecha.replace(tzinfo=None), v.cliente.nombre, v.vendedor.nombre_completo,
                 v.estado_venta.value, v.subtotal, v.iva, v.total]
            )
            if v.estado_venta == EstadoVenta.COMPLETADA:
                sub, iva, total = sub + v.subtotal, iva + v.iva, total + v.total

        filtros = []
        if f.desde:
            filtros.append(("Desde", f.desde.strftime("%d/%m/%Y")))
        if f.hasta:
            filtros.append(("Hasta", f.hasta.strftime("%d/%m/%Y")))
        if f.estado_venta:
            filtros.append(("Estado", f.estado_venta))

        return DatosReporte(
            titulo="",
            columnas=[Columna("N.º venta"), Columna("Fecha", FECHA), Columna("Cliente"), Columna("Vendedor"),
                      Columna("Estado"), Columna("Subtotal", MONEDA), Columna("IVA", MONEDA), Columna("Total", MONEDA)],
            filas=filas,
            filtros=filtros,
            totales=["", "", "", "TOTAL COMPLETADAS", "", sub, iva, total] if filas else None,
        )

    def _inventario(self, f: FiltrosReporte) -> DatosReporte:
        productos = self.producto_repository.find_all_by_estado_true()
        if f.categoria_id is not None:
            productos = [p for p in productos if p.categoria_id == f.categoria_id]
        if f.solo_stock_bajo:
            productos = [p for p in productos if p.stock_actual <= p.stock_minimo]

        def estado_stock(p) -> str:
            if p.stock_actual <= 0:
                return "Agotado"
            return "Stock bajo" if p.stock_actual <= p.stock_minimo else "Normal"

        filas = [
            [p.codigo, p.nombre, p.categoria.nombre, p.proveedor.nombre if p.proveedor else "-", p.precio,
             p.stock_actual, p.stock_minimo, estado_stock(p), p.precio * p.stock_actual]
            for p in productos
        ]

        filtros = []
        if f.categoria_id is not None:
            filtros.append(("Categoría", productos[0].categoria.nombre if productos else f"#{f.categoria_id}"))
        if f.solo_stock_bajo:
            filtros.append(("Solo stock bajo", "Sí"))

        return DatosReporte(
            titulo="",
            columnas=[Columna("Código"), Columna("Producto"), Columna("Categoría"), Columna("Proveedor"),
                      Columna("Precio", MONEDA), Columna("Stock actual", ENTERO), Columna("Stock mínimo", ENTERO),
                      Columna("Estado del stock"), Columna("Valor en inventario", MONEDA)],
            filas=filas,
            filtros=filtros,
            totales=["", f"{len(filas)} productos", "", "", "", sum(p.stock_actual for p in productos), "", "",
                     sum((p.precio * p.stock_actual for p in productos), Decimal(0))] if filas else None,
        )

    def _mas_vendidos(self, f: FiltrosReporte) -> DatosReporte:
        hasta = f.hasta or datetime.now(zona()).date()
        desde = f.desde or (hasta - timedelta(days=30))
        if desde > hasta:
            raise SolicitudInvalidaException("La fecha 'desde' no puede ser posterior a la fecha 'hasta'")

        resultados = self.detalle_venta_repository.buscar_productos_mas_vendidos(
            inicio_del_dia(desde), inicio_del_dia(hasta + timedelta(days=1))
        )
        filas = [[i, r.get_nombre_producto(), r.get_cantidad_total()] for i, r in enumerate(resultados, start=1)]
        return DatosReporte(
            titulo="",
            columnas=[Columna("#", ENTERO), Columna("Producto"), Columna("Unidades vendidas", ENTERO)],
            filas=filas,
            filtros=[("Desde", desde.strftime("%d/%m/%Y")), ("Hasta", hasta.strftime("%d/%m/%Y"))],
            totales=["", "TOTAL", sum(r[2] for r in filas)] if filas else None,
        )