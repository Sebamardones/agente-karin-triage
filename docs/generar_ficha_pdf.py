"""Genera docs/FICHA_NEGOCIO.pdf, la ficha de negocio de una página.

El texto resume docs/FICHA_NEGOCIO.md; si cambia una cifra allá, se cambia
aquí y se regenera. Uso, desde la raíz del repositorio:

    uv run --with reportlab python docs/generar_ficha_pdf.py

reportlab no es dependencia del proyecto: solo se usa para este archivo.
"""

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

SALIDA = Path(__file__).with_name("FICHA_NEGOCIO.pdf")
AZUL = HexColor("#0a3d7a")
ROJO = HexColor("#c8102e")

titulo = ParagraphStyle(
    "titulo", fontName="Helvetica-Bold", fontSize=17, leading=20, textColor=AZUL
)
bajada = ParagraphStyle(
    "bajada", fontName="Helvetica", fontSize=8.6, leading=11, textColor=HexColor("#555555")
)
seccion = ParagraphStyle(
    "seccion",
    fontName="Helvetica-Bold",
    fontSize=9.4,
    leading=11.5,
    textColor=ROJO,
    spaceBefore=6.5,
    spaceAfter=1.5,
)
cuerpo = ParagraphStyle(
    "cuerpo", fontName="Helvetica", fontSize=9.2, leading=11.9, alignment=TA_JUSTIFY
)
fuente = ParagraphStyle(
    "fuente", fontName="Helvetica", fontSize=7.4, leading=9.2, textColor=HexColor("#444444")
)

SECCIONES = [
    (
        "CLIENTE Y PROBLEMA",
        (
            "Dirección del Trabajo: inspectores y supervisores de recepción. El informe semestral DT con corte al "
            "30/06/2026 registra <b>92.643 ingresos</b> entre agosto de 2024 y junio de 2026; el primer semestre de 2026 "
            "sumó 25.830 (<b>4.305/mes</b>). 32.565 (35%) se clasificaron para continuar como Ley Karin, 48.505 (52%) se "
            "derivaron o cerraron y 11.573 (12%) seguían pendientes. Usuarios proyectados: <b>400</b>, es decir, 200 "
            "inspectores dedicados en exclusiva a recepción Ley Karin y 200 con dedicación no exclusiva, supervisores "
            "incluidos. El ahorro de tiempo debe medirse en un piloto."
        ),
    ),
    (
        "PROPUESTA DE VALOR E IA",
        (
            "Dos funciones de IA extraen hechos y proponen tipificación con citas verificables. Reglas deterministas, "
            "seudonimización previa y revisión humana controlan el flujo. Un descarte exige motivo, comentario, cita y "
            "doble revisión. <b>El agente propone; una persona decide.</b> La aplicación pública solo usa casos "
            "sintéticos; admite relatos ficticios nuevos."
        ),
    ),
    (
        "POR QUÉ IMPORTA EL TIEMPO",
        (
            "La pre-clasificación corre contra plazos legales: <b>2 días hábiles</b> para pedir medidas de resguardo "
            "(art. 211-B bis del Código del Trabajo) y <b>30 días</b> para concluir la investigación (art. 211-C). Si la "
            "Inspección no se pronuncia en 30 días sobre un informe interno, se tienen por válidas las conclusiones del "
            "empleador. La propuesta llega ordenada por urgencia, con sus citas, para decidir antes del vencimiento."
        ),
    ),
    (
        "INGRESOS Y PRECIO PROPUESTO",
        (
            "Piloto B2G anual por unidad de recepción (10 analistas y 5 supervisores): <b>CLP 5.400.000 + IVA</b> "
            "(CLP 450.000/mes), hasta 1.600 casos mensuales, unos CLP 285 por caso; cada caso adicional, CLP 150. "
            "Volumen de referencia: 1.581 casos/mes, cerca del 37% del ritmo nacional. Incluye operación, 10 h de "
            "soporte y seguimiento de calidad. Es una hipótesis comercial pendiente de validación. Entrada por Compra "
            "Ágil si el total con IVA cumple el límite de 100 UTM; no garantiza adjudicación."
        ),
    ),
    (
        "MARGEN ESTIMADO DEL PILOTO (1.581 CASOS/MES)",
        (
            "Ingreso CLP 450.000/mes menos inferencia (CLP 158.100 con la reserva de USD 0,10/caso), infraestructura "
            "CLP 12.000, soporte 10 h a CLP 15.000 (CLP 150.000) y calidad CLP 40.000: <b>margen bruto CLP 89.900 "
            "(20%)</b>. A la tasa observada en v3 (USD 0,0178/caso), la inferencia baja a CLP 28.110 y el margen sube "
            "a <b>CLP 219.890 (49%)</b>. CLP 1.000 por USD como supuesto; antes de desarrollo, adquisición e impuestos."
        ),
    ),
    (
        "VALOR PARA LA DT",
        (
            "A CLP 9.000 por hora de funcionario (supuesto), el precio más la adopción equivale a unos <b>2 minutos "
            "por caso</b>. Si el sistema libera más tiempo neto por caso, el piloto se paga en capacidad. Es la "
            "hipótesis que mide el piloto; no está demostrada."
        ),
    ),
    (
        "COSTO MENSUAL: DEMOSTRACIÓN Y PILOTO",
        (
            "Demo: Heroku Basic USD 7 + Postgres Essential-0 USD 5 + inferencia USD 3 = <b>USD 15/mes</b>. "
            "Piloto: la corrida v3 estima USD 0,0178/caso; para planificar se reservan USD 0,10/caso (unas cinco "
            "veces lo observado). A 1.581 casos/mes: <b>USD 40 observado y USD 170 presupuestado</b>, con USD 12 de "
            "infraestructura, antes de soporte. Las tarifas deben conciliarse con la factura vigente."
        ),
    ),
    (
        "COSTO PROYECTADO DEL DESPLIEGUE NACIONAL",
        (
            "400 usuarios y 4.305 casos/mes (CLP 1.000 por USD como supuesto): 2 dynos web + 1 worker Standard-2X USD 150 "
            "+ Postgres Standard-0 USD 50 (precios a verificar al cotizar) + inferencia USD 431 + soporte 40 h "
            "CLP 600.000 + calidad CLP 160.000 = <b>unos CLP 1.391.000/mes</b> (CLP 16,7 M/año), unos CLP 3.478 por "
            "usuario y CLP 323 por caso. Adopción: CLP 7,2 M una vez (2 h por usuario). Excluye integración con Mi DT, "
            "ClaveÚnica y desarrollo institucional."
        ),
    ),
    (
        "ADOPCIÓN Y RIESGOS",
        (
            "Piloto acotado con medición de calidad, tiempo de revisión y falsos descartes. No se aceptan denuncias "
            "reales en esta demo. El uso institucional requiere validación jurídica y de privacidad. La seudonimización "
            "heurística no garantiza anonimato."
        ),
    ),
]

FUENTES = [
    (
        "Fuentes: informe estadístico semestral DT Ley N.° 21.643, corte 30/06/2026 (agosto 2026); informe DT "
        "ago. 2024-jun. 2025; Código del Trabajo, arts. 211-B bis y 211-C."
    ),
    "Informe 2026: dt.gob.cl/portal/1626/articles-129626_archivo_01.pdf",
    "Compra Ágil: chilecompra.cl/compraagil/ | Infraestructura: heroku.com/pricing/",
    "Demo: karin-triage-grupo7-c7c6a3fb2988.herokuapp.com",
]


def construir() -> None:
    doc = SimpleDocTemplate(
        str(SALIDA),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=13 * mm,
        bottomMargin=11 * mm,
        title="KARIN triage · Ficha de negocio",
        author="Grupo 7 · UAI",
    )
    flujo = [
        Paragraph("KARIN triage", titulo),
        Paragraph("Pre-clasificación asistida | Grupo 7 - UAI | Noviembre 2026", bajada),
        Spacer(1, 3),
    ]
    for nombre, texto in SECCIONES:
        flujo += [Paragraph(nombre, seccion), Paragraph(texto, cuerpo)]
    flujo.append(Spacer(1, 6))
    flujo += [Paragraph(linea, fuente) for linea in FUENTES]

    paginas = []
    doc.build(
        flujo,
        onFirstPage=lambda c, d: paginas.append(1),
        onLaterPages=lambda c, d: paginas.append(1),
    )
    if len(paginas) != 1:
        raise SystemExit(f"La ficha ocupa {len(paginas)} páginas; debe ocupar una.")
    print(f"{SALIDA} · 1 página")


if __name__ == "__main__":
    construir()
