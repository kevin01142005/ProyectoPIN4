from html import escape
from typing import Optional, Sequence

COLOR_MARCA = "#B71C1C"


def construir_html(
    titulo: str,
    parrafos: Sequence[str],
    tabla: Optional[tuple[Sequence[str], Sequence[Sequence[object]]]] = None,
    pie: str = "Este es un mensaje automático del sistema de gestión de inventario de LuxMotos. No respondas a este correo.",
) -> str:
    """Correo con el estilo de LuxMotos. Todo el texto se escapa para evitar inyección de HTML."""
    cuerpo = "".join(f'<p style="margin:0 0 12px;line-height:1.5">{escape(p)}</p>' for p in parrafos)

    if tabla is not None:
        encabezados, filas = tabla
        ths = "".join(
            f'<th style="background:#f1f1f1;text-align:left;padding:8px;border:1px solid #ddd">{escape(str(h))}</th>'
            for h in encabezados
        )
        trs = "".join(
            "<tr>" + "".join(f'<td style="padding:8px;border:1px solid #ddd">{escape(str(c))}</td>' for c in fila) + "</tr>"
            for fila in filas
        )
        cuerpo += (
            '<table style="border-collapse:collapse;width:100%;font-size:14px;margin:8px 0 16px">'
            f"<tr>{ths}</tr>{trs}</table>"
        )

    return (
        '<div style="font-family:Arial,Helvetica,sans-serif;background:#f6f6f6;padding:24px">'
        '<div style="max-width:620px;margin:auto;background:#fff;border-radius:8px;overflow:hidden;'
        'border:1px solid #e5e5e5">'
        f'<div style="background:{COLOR_MARCA};color:#fff;padding:16px 24px;font-size:18px;font-weight:bold">'
        "LuxMotos · Gestión de inventario</div>"
        '<div style="padding:24px;color:#222;font-size:15px">'
        f'<h2 style="margin:0 0 16px;font-size:19px;color:{COLOR_MARCA}">{escape(titulo)}</h2>'
        f"{cuerpo}"
        "</div>"
        f'<div style="padding:12px 24px;background:#fafafa;color:#777;font-size:12px">{escape(pie)}</div>'
        "</div></div>"
    )