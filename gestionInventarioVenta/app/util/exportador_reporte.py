"""Genera archivos XLSX y PDF a partir de un reporte ya armado (sin tocar la base de datos)."""
import io
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from xml.sax.saxutils import escape

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

COLOR_MARCA = "B71C1C"

TEXTO, ENTERO, MONEDA, FECHA = "texto", "entero", "moneda", "fecha"


@dataclass(frozen=True)
class Columna:
    titulo: str
    tipo: str = TEXTO


@dataclass(frozen=True)
class DatosReporte:
    titulo: str
    columnas: list[Columna]
    filas: list[list[Any]]
    filtros: list[tuple[str, str]] = field(default_factory=list)
    totales: Optional[list[Any]] = None
    generado_por: str = ""
    generado_en: Optional[datetime] = None


def _fecha_generacion(datos: DatosReporte) -> str:
    momento = datos.generado_en or datetime.now()
    return momento.strftime("%d/%m/%Y %H:%M")


def _texto_filtros(datos: DatosReporte) -> str:
    if not datos.filtros:
        return "Filtros: ninguno (todos los registros)"
    return "Filtros: " + " · ".join(f"{k}: {v}" for k, v in datos.filtros)


def _sin_zona(valor: datetime) -> datetime:
    return valor.replace(tzinfo=None) if valor.tzinfo else valor


def _formatear(valor: Any, tipo: str) -> str:
    """Texto para el PDF (formato colombiano: punto para miles)."""
    if valor is None or valor == "":
        return ""
    if tipo == MONEDA:
        return "$ " + f"{Decimal(str(valor)):,.0f}".replace(",", ".")
    if tipo == ENTERO:
        return f"{int(valor):,}".replace(",", ".")
    if tipo == FECHA and isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    return str(valor)


def _repartir_anchos(naturales: list[float], total: float) -> list[float]:
    """Si todo cabe, se reparte el sobrante; si no, las columnas cortas conservan su ancho y las largas se reducen."""
    if sum(naturales) <= total:
        factor = total / sum(naturales)
        return [n * factor for n in naturales]

    anchos = [0.0] * len(naturales)
    pendientes = list(range(len(naturales)))
    restante = total
    while pendientes:
        cuota = restante / len(pendientes)
        fijas = [i for i in pendientes if naturales[i] <= cuota]
        if not fijas:
            for i in pendientes:
                anchos[i] = cuota
            break
        for i in fijas:
            anchos[i] = naturales[i]
            restante -= naturales[i]
            pendientes.remove(i)
    return anchos


def generar_xlsx(datos: DatosReporte) -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Reporte"
    ncols = len(datos.columnas)

    hoja.cell(row=1, column=1, value=datos.titulo).font = Font(bold=True, size=14, color=COLOR_MARCA)
    hoja.cell(row=2, column=1, value=f"Generado el {_fecha_generacion(datos)}" + (f" por {datos.generado_por}" if datos.generado_por else ""))
    hoja.cell(row=3, column=1, value=_texto_filtros(datos))
    for n_fila in (1, 2, 3):
        hoja.merge_cells(start_row=n_fila, start_column=1, end_row=n_fila, end_column=max(ncols, 2))

    fila_encabezado = 5
    borde = Border(*(Side(style="thin", color="DDDDDD"),) * 4)
    for i, columna in enumerate(datos.columnas, start=1):
        celda = hoja.cell(row=fila_encabezado, column=i, value=columna.titulo)
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor=COLOR_MARCA)
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celda.border = borde

    formatos = {MONEDA: '"$"#,##0', ENTERO: "#,##0", FECHA: "dd/mm/yyyy hh:mm"}

    def escribir(fila_excel: int, valores: list[Any], negrita: bool = False) -> None:
        for i, (columna, valor) in enumerate(zip(datos.columnas, valores), start=1):
            if isinstance(valor, Decimal):
                valor = float(valor)
            if isinstance(valor, datetime):
                valor = _sin_zona(valor)
            celda = hoja.cell(row=fila_excel, column=i, value=valor)
            celda.border = borde
            if columna.tipo in formatos:
                celda.number_format = formatos[columna.tipo]
            if columna.tipo in (ENTERO, MONEDA):
                celda.alignment = Alignment(horizontal="right")
            if negrita:
                celda.font = Font(bold=True)
                celda.fill = PatternFill("solid", fgColor="F1F1F1")

    for numero, fila in enumerate(datos.filas, start=fila_encabezado + 1):
        escribir(numero, fila)
    ultima = fila_encabezado + len(datos.filas)
    if datos.totales is not None:
        ultima += 1
        escribir(ultima, datos.totales, negrita=True)

    if not datos.filas:
        hoja.cell(row=fila_encabezado + 1, column=1, value="Sin datos para los filtros seleccionados")

    for i, columna in enumerate(datos.columnas, start=1):
        largo = max(
            [len(columna.titulo)] + [len(_formatear(f[i - 1], columna.tipo)) for f in datos.filas] +
            ([len(_formatear(datos.totales[i - 1], columna.tipo))] if datos.totales else [0])
        )
        hoja.column_dimensions[get_column_letter(i)].width = min(max(largo + 3, 12), 50)

    hoja.freeze_panes = hoja.cell(row=fila_encabezado + 1, column=1)
    if datos.filas:
        hoja.auto_filter.ref = f"A{fila_encabezado}:{get_column_letter(ncols)}{fila_encabezado + len(datos.filas)}"

    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


def generar_pdf(datos: DatosReporte) -> bytes:
    ncols = len(datos.columnas)
    pagina = landscape(A4) if ncols > 5 else A4
    ancho_util = pagina[0] - 3 * cm

    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("titulo", parent=estilos["Title"], textColor=colors.HexColor("#" + COLOR_MARCA), fontSize=17, alignment=0)
    meta = ParagraphStyle("meta", parent=estilos["Normal"], fontSize=9, textColor=colors.HexColor("#555555"), leading=12)
    celda = ParagraphStyle("celda", parent=estilos["Normal"], fontSize=8, leading=10)
    celda_der = ParagraphStyle("celda_der", parent=celda, alignment=2)
    cabecera = ParagraphStyle("cabecera", parent=celda, textColor=colors.white, fontName="Helvetica-Bold", alignment=1)
    total = ParagraphStyle("total", parent=celda, fontName="Helvetica-Bold")
    total_der = ParagraphStyle("total_der", parent=total, alignment=2)

    def parrafo(valor: Any, columna: Columna, es_total: bool = False) -> Paragraph:
        numerica = columna.tipo in (ENTERO, MONEDA)
        estilo = (total_der if numerica else total) if es_total else (celda_der if numerica else celda)
        return Paragraph(escape(_formatear(valor, columna.tipo)), estilo)

    elementos: list[Any] = [
        Paragraph(escape(datos.titulo), titulo),
        Paragraph(
            escape(f"Generado el {_fecha_generacion(datos)}" + (f" por {datos.generado_por}" if datos.generado_por else "")),
            meta,
        ),
        Paragraph(escape(_texto_filtros(datos)), meta),
        Spacer(1, 12),
    ]

    if not datos.filas:
        elementos.append(Paragraph("Sin datos para los filtros seleccionados.", estilos["Normal"]))
    else:
        tabla = [[Paragraph(escape(c.titulo), cabecera) for c in datos.columnas]]
        for fila in datos.filas:
            tabla.append([parrafo(v, c) for c, v in zip(datos.columnas, fila)])
        if datos.totales is not None:
            tabla.append([parrafo(v, c, True) for c, v in zip(datos.columnas, datos.totales)])

        # Ancho natural de cada columna: lo que mide su texto más largo (cabecera en negrita incluida) más el relleno.
        naturales = []
        for i, c in enumerate(datos.columnas):
            textos = [_formatear(f[i], c.tipo) for f in datos.filas[:200]]
            if datos.totales is not None:
                textos.append(_formatear(datos.totales[i], c.tipo))
            ancho_texto = max(
                [stringWidth(t, "Helvetica", 8) for t in textos]
                + [max(stringWidth(p, "Helvetica-Bold", 8) for p in c.titulo.split()) if c.titulo.split() else 0]
            )
            naturales.append(min(ancho_texto + 16, ancho_util * 0.4))
        anchos = _repartir_anchos(naturales, ancho_util)

        estilo_tabla = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#" + COLOR_MARCA)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7F7")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        if datos.totales is not None:
            estilo_tabla.append(("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E9E9E9")))
        elementos.append(Table(tabla, colWidths=anchos, repeatRows=1, style=TableStyle(estilo_tabla)))

    def pie(canvas, documento) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawString(1.5 * cm, 1 * cm, "LuxMotos · Gestión de inventario")
        canvas.drawRightString(pagina[0] - 1.5 * cm, 1 * cm, f"Página {documento.page}")
        canvas.restoreState()

    salida = io.BytesIO()
    SimpleDocTemplate(
        salida, pagesize=pagina, leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.8 * cm,
        title=datos.titulo, author="LuxMotos",
    ).build(elementos, onFirstPage=pie, onLaterPages=pie)
    return salida.getvalue()