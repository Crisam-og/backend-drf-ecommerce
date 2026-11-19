# ventas/comprobante_pdf.py
# Genera el PDF (A4) de una boleta o factura con ReportLab.
#   pip install reportlab
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ACCENT = colors.HexColor("#465FFF")
GRIS = colors.HexColor("#667085")
GRIS_CLARO = colors.HexColor("#F2F4F7")
TEXTO = colors.HexColor("#1D2939")


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def money(valor) -> str:
    return f"S/ {Decimal(valor):,.2f}"


_UNIDADES = [
    "cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
    "nueve", "diez", "once", "doce", "trece", "catorce", "quince", "dieciséis",
    "diecisiete", "dieciocho", "diecinueve", "veinte", "veintiuno", "veintidós",
    "veintitrés", "veinticuatro", "veinticinco", "veintiséis", "veintisiete",
    "veintiocho", "veintinueve",
]
_DECENAS = {
    3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta",
    7: "setenta", 8: "ochenta", 9: "noventa",
}
_CENTENAS = {
    1: "cien", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos",
    5: "quinientos", 6: "seiscientos", 7: "setecientos", 8: "ochocientos",
    9: "novecientos",
}


def _menor_mil(n: int) -> str:
    if n < 30:
        return _UNIDADES[n]
    if n < 100:
        d, u = divmod(n, 10)
        return _DECENAS[d] + (f" y {_UNIDADES[u]}" if u else "")
    c, r = divmod(n, 100)
    if r == 0:
        return _CENTENAS[c]
    base = "ciento" if c == 1 else _CENTENAS[c]
    return f"{base} {_menor_mil(r)}"


def _apocope(texto: str) -> str:
    # "uno" -> "un", "veintiuno" -> "veintiún" delante de "mil" / "millones"
    if texto.endswith("veintiuno"):
        return texto[: -len("veintiuno")] + "veintiún"
    if texto.endswith("uno"):
        return texto[:-3] + "un"
    return texto


def _entero_a_letras(n: int) -> str:
    if n < 1000:
        return _menor_mil(n)
    if n < 1_000_000:
        miles, resto = divmod(n, 1000)
        pref = "mil" if miles == 1 else f"{_apocope(_menor_mil(miles))} mil"
        return pref + (f" {_menor_mil(resto)}" if resto else "")
    millones, resto = divmod(n, 1_000_000)
    pref = "un millón" if millones == 1 else f"{_apocope(_entero_a_letras(millones))} millones"
    return pref + (f" {_entero_a_letras(resto)}" if resto else "")


def monto_en_letras(total) -> str:
    total = Decimal(total).quantize(Decimal("0.01"))
    entero = int(total)
    centimos = int((total - entero) * 100)
    return f"SON: {_entero_a_letras(entero).upper()} CON {centimos:02d}/100 SOLES"


# ----------------------------------------------------------------------
# Estilos
# ----------------------------------------------------------------------
def _estilos():
    base = dict(fontName="Helvetica", fontSize=9, leading=12, textColor=TEXTO)
    return {
        "normal": ParagraphStyle("normal", **base),
        "pequeno": ParagraphStyle("pequeno", **{**base, "fontSize": 8, "textColor": GRIS}),
        "empresa": ParagraphStyle(
            "empresa", **{**base, "fontName": "Helvetica-Bold", "fontSize": 14, "leading": 17}
        ),
        "caja_ruc": ParagraphStyle(
            "caja_ruc", **{**base, "fontSize": 10, "leading": 14, "alignment": TA_CENTER}
        ),
        "caja_tipo": ParagraphStyle(
            "caja_tipo",
            **{**base, "fontName": "Helvetica-Bold", "fontSize": 11, "leading": 15,
               "alignment": TA_CENTER, "textColor": ACCENT},
        ),
        "caja_num": ParagraphStyle(
            "caja_num",
            **{**base, "fontName": "Helvetica-Bold", "fontSize": 12, "leading": 16,
               "alignment": TA_CENTER},
        ),
        "th": ParagraphStyle(
            "th", **{**base, "fontName": "Helvetica-Bold", "textColor": colors.white}
        ),
        "th_der": ParagraphStyle(
            "th_der",
            **{**base, "fontName": "Helvetica-Bold", "textColor": colors.white, "alignment": TA_RIGHT},
        ),
        "der": ParagraphStyle("der", **{**base, "alignment": TA_RIGHT}),
        "centro": ParagraphStyle("centro", **{**base, "alignment": TA_CENTER}),
        "total": ParagraphStyle(
            "total", **{**base, "fontName": "Helvetica-Bold", "fontSize": 11, "alignment": TA_RIGHT}
        ),
        "total_lbl": ParagraphStyle(
            "total_lbl", **{**base, "fontName": "Helvetica-Bold", "fontSize": 11}
        ),
        "gracias": ParagraphStyle(
            "gracias", **{**base, "fontSize": 8, "textColor": GRIS, "alignment": TA_CENTER}
        ),
    }


# ----------------------------------------------------------------------
# Generador principal
# ----------------------------------------------------------------------
def descripcion_detalle(d, markup: bool = True) -> str:
    """Nombre del producto + presentación. Las ventas anteriores al cambio
    (sin presentación) conservan solo el nombre del producto."""
    nombre = d.producto.nombre or ""
    if d.presentacion_id:
        nombre = f"{nombre} ({d.nombre_presentacion})"
    return escape(nombre) if markup else nombre

def _generar_boleta_ticket_pdf(venta, empresa=None) -> bytes:
    """Genera la boleta en formato de ticket térmico de 80 mm."""
    s = _estilos()
    ancho = 80 * mm
    margen = 5 * mm
    ancho_util = ancho - 2 * margen

    # Altura estimada según la cantidad de productos y el texto que deban ocupar.
    lineas_estimadas = 0
    for d in venta.detalles.all():
        descripcion = descripcion_detalle(d, markup=False)
        lineas_estimadas += max(1, (len(descripcion) + 27) // 28) + 1
    alto = max(125 * mm, (92 + lineas_estimadas * 5) * mm)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(ancho, alto),
        leftMargin=margen,
        rightMargin=margen,
        topMargin=5 * mm,
        bottomMargin=5 * mm,
        title=f"BOLETA DE VENTA {venta.numero_comprobante}",
    )

    base = ParagraphStyle(
        "ticket_normal", fontName="Helvetica", fontSize=7.5,
        leading=9, textColor=TEXTO,
    )
    pequeno = ParagraphStyle(
        "ticket_pequeno", fontName="Helvetica", fontSize=6.5,
        leading=8, textColor=GRIS,
    )
    centro = ParagraphStyle(
        "ticket_centro", parent=base, alignment=TA_CENTER,
    )
    empresa_style = ParagraphStyle(
        "ticket_empresa", parent=centro, fontName="Helvetica-Bold",
        fontSize=10, leading=12,
    )
    titulo_style = ParagraphStyle(
        "ticket_titulo", parent=centro, fontName="Helvetica-Bold",
        fontSize=9, leading=11, textColor=ACCENT,
    )
    derecha = ParagraphStyle(
        "ticket_derecha", parent=base, alignment=TA_RIGHT,
    )
    story = []

    nombre_emp = getattr(empresa, "nombre", "") or "Mi Empresa"
    ruc_emp = getattr(empresa, "ruc", "") or "—"
    logo = getattr(empresa, "logo", None)
    if logo:
        try:
            story.append(Image(
                logo.path, width=28 * mm, height=14 * mm,
                kind="proportional", hAlign="CENTER",
            ))
        except Exception:
            pass

    story.append(Paragraph(nombre_emp, empresa_style))
    for linea in (
        getattr(empresa, "direccion", ""),
        f"Tel: {empresa.telefono}" if getattr(empresa, "telefono", "") else "",
        f"WhatsApp: {empresa.whatsapp}" if getattr(empresa, "whatsapp", "") else "",
        getattr(empresa, "correo", ""),
    ):
        if linea:
            story.append(Paragraph(str(linea), centro))

    story += [
        Spacer(1, 2 * mm),
        Paragraph(f"R.U.C. {ruc_emp}", centro),
        Paragraph("BOLETA DE VENTA", titulo_style),
        Paragraph(str(venta.numero_comprobante), centro),
        Spacer(1, 2 * mm),
    ]

    fecha = timezone.localtime(venta.fecha_venta).strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(f"<b>Cajero:</b> {venta.usuario.first_name}", base))
    story.append(Paragraph(f"<b>Cliente:</b> {venta.cliente}", base))
    story.append(Paragraph(f"<b>DNI:</b> {venta.dni_cliente or '—'}", base))
    story.append(Paragraph(f"<b>Fecha:</b> {fecha}", base))
    story.append(Paragraph("<b>Moneda:</b> SOLES (PEN)", base))
    story += [Spacer(1, 2 * mm), Paragraph("DETALLE", titulo_style)]

    datos = [[
        Paragraph("<b>Cant.</b>", pequeno),
        Paragraph("<b>Descripción</b>", pequeno),
        Paragraph("<b>Importe</b>", ParagraphStyle(
            "ticket_th_der", parent=pequeno, alignment=TA_RIGHT,
            fontName="Helvetica-Bold",
        )),
    ]]
    for d in venta.detalles.all():
        extra = ""
        if d.presentacion_id and d.unidades_por_presentacion > 1:
            extra = f" · {d.unidades_por_presentacion} und."
        descripcion = (
            f"{descripcion_detalle(d)}<br/>"
            f"<font color='#667085'>V. unit.: {money(d.precio_unitario)}{extra}</font>"
        )
        datos.append([
            Paragraph(str(d.cantidad), centro),
            Paragraph(descripcion, base),
            Paragraph(money(d.subtotal), derecha),
        ])

    detalle = Table(
        datos, colWidths=[10 * mm, 38 * mm, ancho_util - 48 * mm],
        repeatRows=1,
    )
    detalle.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLARO),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, ACCENT),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#D0D5DD")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story += [detalle, Spacer(1, 2 * mm)]

    totales = Table([
        [Paragraph("Op. Gravada", base), Paragraph(money(venta.subtotal), derecha)],
        [Paragraph("IGV (18%)", base), Paragraph(money(venta.igv), derecha)],
        [Paragraph("<b>IMPORTE TOTAL</b>", base),
         Paragraph(f"<b>{money(venta.total)}</b>", derecha)],
    ], colWidths=[ancho_util * 0.55, ancho_util * 0.45])
    totales.setStyle(TableStyle([
        ("LINEABOVE", (0, 2), (-1, 2), 0.8, ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story += [
        totales,
        Spacer(1, 2 * mm),
        Paragraph(f"<b>{monto_en_letras(venta.total)}</b>", pequeno),
        Spacer(1, 4 * mm),
        Paragraph("Gracias por su compra.", centro),
    ]

    doc.build(story)
    return buffer.getvalue()


def generar_comprobante_pdf(venta, empresa=None) -> bytes:
    """
    venta   -> instancia de VentaModel (con detalles__producto)
    empresa -> instancia del modelo de empresa (nombre, ruc, direccion, correo,
               telefono, whatsapp, logo). Puede ser None.
    """
    s = _estilos()
    es_factura = venta.tipo_comprobante == "F"
    titulo = "FACTURA" if es_factura else "BOLETA DE VENTA"

    # La factura conserva el diseño A4 original; la boleta usa ticket térmico.
    if not es_factura:
        return _generar_boleta_ticket_pdf(venta, empresa)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"{titulo} {venta.numero_comprobante}",
    )
    story = []

    # ---------------- Cabecera: empresa + caja del comprobante ----------------
    nombre_emp = getattr(empresa, "nombre", "") or "Mi Empresa"
    ruc_emp = getattr(empresa, "ruc", "") or "—"

    izquierda = []
    logo = getattr(empresa, "logo", None)
    if logo:
        try:
            izquierda.append(Image(logo.path, width=40 * mm, height=18 * mm, kind="proportional", hAlign="LEFT"))
            izquierda.append(Spacer(1, 2 * mm))
        except Exception:
            pass  # sin logo si el archivo no existe

    izquierda.append(Paragraph(nombre_emp, s["empresa"]))
    for linea in (
        getattr(empresa, "direccion", ""),
        f"Tel: {empresa.telefono}" if getattr(empresa, "telefono", "") else "",
        f"WhatsApp: {empresa.whatsapp}" if getattr(empresa, "whatsapp", "") else "",
        getattr(empresa, "correo", ""),
    ):
        if linea:
            izquierda.append(Paragraph(linea, s["pequeno"]))

    caja = Table(
        [
            [Paragraph(f"R.U.C. {ruc_emp}", s["caja_ruc"])],
            [Paragraph(titulo, s["caja_tipo"])],
            [Paragraph(venta.numero_comprobante, s["caja_num"])],
        ],
        colWidths=[70 * mm],
    )
    caja.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, ACCENT),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    cabecera = Table([[izquierda, caja]], colWidths=[110 * mm, 70 * mm])
    cabecera.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (0, 0), 0)]))
    story += [cabecera, Spacer(1, 8 * mm)]

    # ---------------- Datos del cliente ----------------
    fecha = timezone.localtime(venta.fecha_venta).strftime("%d/%m/%Y %H:%M")
    doc_label = "RUC" if es_factura else "DNI"
    doc_valor = venta.ruc_cliente if es_factura else venta.dni_cliente
    nombre_label = "Razón social" if es_factura else "Cliente"

    filas = [
        [Paragraph(f"<b>{nombre_label}:</b>", s["normal"]), Paragraph(venta.cliente, s["normal"]),
         Paragraph("<b>Fecha de emisión:</b>", s["normal"]), Paragraph(fecha, s["normal"])],
        [Paragraph(f"<b>{doc_label}:</b>", s["normal"]), Paragraph(doc_valor or "—", s["normal"]),
         Paragraph("<b>Moneda:</b>", s["normal"]), Paragraph("SOLES (PEN)", s["normal"])],
    ]
    if es_factura and venta.direccion_cliente:
        filas.append(
            [Paragraph("<b>Dirección:</b>", s["normal"]), Paragraph(venta.direccion_cliente, s["normal"]), "", ""]
        )

    cliente_tbl = Table(filas, colWidths=[28 * mm, 72 * mm, 32 * mm, 48 * mm])
    cliente_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    if es_factura and venta.direccion_cliente:
        cliente_tbl.setStyle(TableStyle([("SPAN", (1, 2), (3, 2))]))
    story += [cliente_tbl, Spacer(1, 6 * mm)]

    # ---------------- Detalle ----------------
    datos = [[
        Paragraph("Cant.", s["th"]),
        Paragraph("Descripción", s["th"]),
        Paragraph("V. Unitario", s["th_der"]),
        Paragraph("Importe", s["th_der"]),
    ]]
    for d in venta.detalles.all():
        datos.append([
            Paragraph(str(d.cantidad), s["centro"]),
            Paragraph(descripcion_detalle(d), s["normal"]),
            Paragraph(money(d.precio_unitario), s["der"]),
            Paragraph(money(d.subtotal), s["der"]),
        ])

    detalle = Table(datos, colWidths=[18 * mm, 98 * mm, 32 * mm, 32 * mm], repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#E4E7EC")),
    ]
    for i in range(2, len(datos), 2):
        estilo.append(("BACKGROUND", (0, i), (-1, i), GRIS_CLARO))
    detalle.setStyle(TableStyle(estilo))
    story += [detalle, Spacer(1, 4 * mm)]

    # ---------------- Totales ----------------
    totales = Table(
        [
            [Paragraph("Op. Gravada", s["normal"]), Paragraph(money(venta.subtotal), s["der"])],
            [Paragraph("IGV (18%)", s["normal"]), Paragraph(money(venta.igv), s["der"])],
            [Paragraph("IMPORTE TOTAL", s["total_lbl"]), Paragraph(money(venta.total), s["total"])],
        ],
        colWidths=[40 * mm, 36 * mm],
        hAlign="RIGHT",
    )
    totales.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 2), (-1, 2), 1, ACCENT),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story += [totales, Spacer(1, 6 * mm)]

    story.append(Paragraph(f"<b>{monto_en_letras(venta.total)}</b>", s["normal"]))
    story.append(Spacer(1, 12 * mm))
    story.append(Paragraph("Gracias por su compra.", s["gracias"]))

    doc.build(story)
    return buffer.getvalue()