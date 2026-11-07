"""Genera docs/FICHA_NEGOCIO.pdf (una página A4). Uso: python scripts/generar_ficha_pdf.py docs/FICHA_NEGOCIO.pdf"""

import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

NAVY = colors.HexColor("#0f2a3f")
TEAL = colors.HexColor("#1b6e8a")
TEXTO = colors.HexColor("#222222")
GRIS = colors.HexColor("#555555")
ANCHO, ALTO = A4
MARGEN = 40
UTIL = ANCHO - 2 * MARGEN

cuerpo = ParagraphStyle("c", fontName="Helvetica", fontSize=8.6, leading=11.4, textColor=TEXTO)
titulo = ParagraphStyle("t", fontName="Helvetica", fontSize=10.5, leading=13, textColor=TEAL)
celda = ParagraphStyle("x", parent=cuerpo, fontSize=8.2, leading=10)
celda_b = ParagraphStyle("xb", parent=celda, fontName="Helvetica-Bold")
pie = ParagraphStyle("p", fontName="Helvetica", fontSize=7, leading=10, textColor=GRIS)

SECCIONES = [
    ("CLIENTE Y PROBLEMA",
     "Dirección del Trabajo: analistas y supervisores de recepción. El balance oficial registra "
     "44.212 denuncias entre agosto de 2024 y junio de 2025 (4.019/mes). De ellas, 17.980 (40%) "
     "se preclasificaron como no Ley Karin y se cerraron. La propuesta busca reducir el esfuerzo "
     "de clasificación con revisión trazable; el ahorro de tiempo debe medirse en un piloto."),
    ("PROPUESTA DE VALOR E IA",
     "Dos funciones de IA extraen hechos y proponen tipificación con citas verificables. Reglas "
     "deterministas, seudonimización previa y revisión humana controlan el flujo. Un descarte exige "
     "motivo, comentario, cita y doble revisión. El agente propone; una persona decide. La "
     "aplicación pública solo usa casos sintéticos; admite relatos ficticios nuevos."),
    ("INGRESOS Y PRECIO PROPUESTO",
     "Servicio B2G anual por inspección: CLP 3.600.000 + IVA (CLP 300.000/mes), hasta 1.000 casos "
     "mensuales. Incluye operación y soporte básico. Excedentes, desarrollo e integraciones se "
     "cotizan aparte. Es una hipótesis comercial, pendiente de validación con el cliente. Entrada "
     "propuesta por Compra Ágil si el total cumple el límite de 100 UTM y los requisitos del "
     "procedimiento; no garantiza adjudicación."),
]

CONSUMO_INTRO = (
    "Escenario: <b>10 analistas, 5 supervisores y 1.581 casos al mes</b> (unos 75 por día hábil, "
    "con 21 días hábiles).")
TABLA = [
    ["Concepto", "Observado", "Presupuesto"],
    ["Inferencia por caso", "USD 0,0178", "USD 0,10"],
    ["Inferencia, 1.581 casos", "USD 28,11", "USD 158,10"],
    ["Heroku Basic + Postgres Essential-0", "USD 12", "USD 12"],
    ["Total mensual", "USD 40,11", "USD 170,10"],
]
CONSUMO_NOTA = (
    "Observado: corrida v3, USD 0,16 para nueve casos con IA; se supone que todo caso usa IA, "
    "aunque los que resuelven las reglas cuestan cero. USD 0,10/caso es el presupuesto de "
    "planificación, unas cinco veces lo observado. Cada analista revisa unos 158 casos al mes; "
    "con 40,7% de descartes, cada supervisor firma unos 129 al mes. El número de usuarios no "
    "cambia el costo de IA. Postgres de 1 GB alcanza para cerca de un año. Para operar, los topes "
    "pasan a 400 llamadas y USD 8 al día, y a USD 170 al mes en la consola. El escenario supera "
    "en 581 casos el plan base: se cotizan como volumen adicional. Tarifas de IA pendientes de "
    "conciliar con la factura.")

RIESGOS = ("ADOPCIÓN Y RIESGOS",
           "Piloto acotado con medición de calidad, tiempo de revisión y falsos descartes. No se "
           "aceptan denuncias reales en esta demo. El uso institucional requiere validación jurídica "
           "y de privacidad. La seudonimización heurística no garantiza anonimato. La contratación, "
           "el precio y la capacidad deben validarse antes de ofrecer el servicio institucional.")


def bloque(c, y, cabecera, texto):
    y -= 20
    p = Paragraph(cabecera, titulo)
    _, h = p.wrap(UTIL, 100)
    p.drawOn(c, MARGEN, y - h)
    y -= h + 6
    p = Paragraph(texto, cuerpo)
    _, h = p.wrap(UTIL, 400)
    p.drawOn(c, MARGEN, y - h)
    return y - h


def main(salida):
    from reportlab.pdfgen.canvas import Canvas

    c = Canvas(salida, pagesize=A4)
    c.setTitle("KARIN triage · Ficha de negocio")
    c.setAuthor("Grupo 7 · UAI")
    c.setFillColor(NAVY)
    c.rect(0, ALTO - 120, ANCHO, 120, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 24)
    c.drawString(MARGEN, ALTO - 58, "KARIN triage")
    c.setFont("Helvetica", 9.5)
    c.drawString(MARGEN, ALTO - 88, "Pre-clasificación asistida | Grupo 7 - UAI | Noviembre 2026")

    y = ALTO - 128
    for cab, txt in SECCIONES:
        y = bloque(c, y, cab, txt)

    y = bloque(c, y, "CONSUMO MENSUAL ESTIMADO DE OPERACIÓN", CONSUMO_INTRO)
    filas = [[Paragraph(v, celda_b if i in (0, len(TABLA) - 1) else celda) for v in fila]
             for i, fila in enumerate(TABLA)]
    t = Table(filas, colWidths=[UTIL * 0.5, UTIL * 0.25, UTIL * 0.25])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, TEAL),
        ("LINEABOVE", (0, -1), (-1, -1), 0.6, TEAL),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    _, h = t.wrap(UTIL, 200)
    t.drawOn(c, MARGEN, y - 4 - h)
    y -= h + 10
    p = Paragraph(CONSUMO_NOTA, cuerpo)
    _, h = p.wrap(UTIL, 400)
    p.drawOn(c, MARGEN, y - h)
    y -= h

    y = bloque(c, y, *RIESGOS)
    if y < 90:
        sys.exit(f"El contenido no cabe en una página (y={y:.0f})")

    lineas = ["Fuentes: balance Mintrab 01/08/2025; informe DT agosto 2024-junio 2025.",
              "Compra Ágil: chilecompra.cl/compraagil/ | Infraestructura: heroku.com/pricing/",
              "Demo: karin-triage-grupo7-c7c6a3fb2988.herokuapp.com"]
    for i, linea in enumerate(lineas):
        par = Paragraph(linea, pie)
        par.wrapOn(c, UTIL, 20)
        par.drawOn(c, MARGEN, 62 - i * 13 - (4 if i == 2 else 0))
    c.showPage()
    c.save()
    print(f"OK, margen inferior libre: y={y:.0f}")


if __name__ == "__main__":
    main(sys.argv[1])
