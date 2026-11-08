"""Cómo se presenta un caso al funcionario. Solo lectura de datos ya guardados.

Nada de este módulo decide: traduce la propuesta, las reglas aplicadas y las
revisiones humanas a lo que la persona necesita ver para decidir. Si un dato no
existe, no se inventa.
"""

import re
from datetime import datetime

from markupsafe import Markup, escape

from karin_triage.models.tablas import ahora

BANDEJAS = ("por-revisar", "esperando", "revisados", "cerrados", "anteriores")

NOMBRES_BANDEJA = {
    "analista": {"por-revisar": "Por revisar", "esperando": "Esperando supervisor",
                 "revisados": "Revisados", "cerrados": "Cerrados",
                 "anteriores": "Tandas anteriores"},
    "supervisor": {"por-revisar": "Sin revisar", "esperando": "Por validar",
                   "revisados": "Revisados", "cerrados": "Cerrados",
                   "anteriores": "Tandas anteriores"},
}

# Etiqueta corta de la propuesta para las tarjetas de la cola.
CHIP_DECISION = {
    "PROCEDE_INVESTIGACION": ("Investigar", "chip-investigar"),
    "DERIVA_MEDIACION": ("Mediación", "chip-mediacion"),
    "DESCARTADO": ("Reconducir", "chip-reconducir"),
    "REQUIERE_ANTECEDENTES": ("Pedir antecedentes", "chip-neutro"),
    "DERIVAR_OTRA_INSTITUCION": ("Otra institución", "chip-neutro"),
}

# Qué hace cada regla dura, en lenguaje del funcionario.
REGLAS = {
    "RD-01": "Faltan datos obligatorios: el caso se detuvo antes de la IA",
    "RD-02": "Empleador del sector público: se deriva sin llamar a la IA",
    "RD-03": "Informe interno del empleador: alerta de plazo de 30 días",
    "RD-04": "Relato posiblemente duplicado: nunca se descarta solo",
    "RD-05": "Hechos anteriores a la ley: revisión humana",
    "RD-06": "Quedaron datos personales tras seudonimizar: se cortó el flujo",
    "RD-10": "Acoso sexual no va a mediación: la regla corrigió la propuesta",
    "RD-11": "Descarte sin motivo válido: revisión prioritaria",
    "RD-12": "Señales de riesgo: se elevó la urgencia de resguardo",
    "RD-13": "Confianza bajo el umbral: revisión prioritaria",
    "RD-14": "Descarte propuesto: requiere segunda firma de un supervisor",
    "RD-15": "Una cita no era literal: se pidió al modelo corregirla",
    "RD-16": "El modelo no respondió: el caso pasó a revisión manual",
}
PREVIAS = {"RD-01", "RD-02", "RD-03", "RD-04", "RD-05"}


def lista_reglas(reglas_aplicadas):
    if not reglas_aplicadas:
        return []
    valores = reglas_aplicadas.split(",") if isinstance(reglas_aplicadas, str) else reglas_aplicadas
    return [r.strip() for r in valores if r and r.strip()]


def categoria(historial, estado_revision):
    """Bandeja en la que está el caso, derivada de sus revisiones humanas."""
    if not historial:
        return "por-revisar"
    if len(historial) >= 2 or estado_revision.startswith("Revisión de una versión anterior"):
        return "cerrados"
    if estado_revision.startswith("Pendiente de validación"):
        return "esperando"
    return "revisados"


def tiempo_relativo(momento):
    if not isinstance(momento, datetime):
        return ""
    segundos = max(0, int((ahora() - momento).total_seconds()))
    if segundos < 60:
        return "recién"
    if segundos < 3600:
        return f"hace {segundos // 60} min"
    if segundos < 86400:
        return f"hace {segundos // 3600} h"
    dias = segundos // 86400
    return f"hace {dias} día" if dias == 1 else f"hace {dias} días"


def _compactar(texto):
    return " ".join((texto or "").split())


def citas_de(propuesta):
    relato, normativas = [], []
    for bloque in propuesta.justificacion_y_citas or []:
        for cita in bloque.get("citas", []):
            (normativas if cita.get("fuente") == "normativa" else relato).append(cita)
    return relato, normativas


def uso_ia(propuesta):
    """True si la propuesta salió del modelo; False si una regla o un fallo lo evitó."""
    return bool(propuesta.justificacion_y_citas)


def resaltar(texto, citas):
    """Relato escapado con cada cita literal marcada y numerada en su lugar.

    Devuelve (Markup, encontradas). Una cita que no aparece tal cual en el texto
    no se marca y no cuenta como verificada.
    """
    texto = texto or ""
    tramos = []
    for numero, cita in enumerate(citas, start=1):
        literal = (cita.get("texto_literal") or "").strip()
        if not literal:
            continue
        inicio = texto.find(literal)
        if inicio < 0:
            # Igual que RD-15: se tolera solo la diferencia de espacios.
            patron = r"\s+".join(re.escape(p) for p in literal.split())
            hallazgo = re.search(patron, texto)
            if not hallazgo:
                continue
            inicio, fin = hallazgo.span()
        else:
            fin = inicio + len(literal)
        if any(inicio < f and fin > i for i, f, _ in tramos):
            continue
        tramos.append((inicio, fin, numero))
    tramos.sort()
    partes, cursor = [], 0
    for inicio, fin, numero in tramos:
        partes.append(escape(texto[cursor:inicio]))
        # El número va en CSS (::after) para que no entre en la selección de una cita.
        partes.append(Markup('<mark id="cita-{n}" class="cita-marca" data-cita="{n}">{t}</mark>'
                          ).format(n=numero, t=texto[inicio:fin]))
        cursor = fin
    partes.append(escape(texto[cursor:]))
    return Markup("").join(partes), {n for _, _, n in tramos}


def extracto(propuesta, largo=110):
    relato, _ = citas_de(propuesta)
    if relato:
        texto = _compactar(relato[0].get("texto_literal"))
        return texto if len(texto) <= largo else texto[: largo - 1].rstrip() + "…"
    return ""


def recorrido(propuesta):
    """Pasos que siguió el caso, armados desde reglas y marcas guardadas."""
    reglas = lista_reglas(propuesta.reglas_aplicadas)
    marcas = propuesta.marcas_pipeline or ""
    previas = [r for r in reglas if r in PREVIAS]
    pasos = []
    detenido_antes = bool(previas) and not uso_ia(propuesta)
    pasos.append({"nombre": "Reglas previas",
                  "estado": "detenido" if detenido_antes else "ok",
                  "detalle": "; ".join(REGLAS[r] for r in previas) if previas
                  else "Datos completos y dentro del alcance"})
    if detenido_antes:
        pasos.append({"nombre": "IA", "estado": "omitido",
                      "detalle": "No se llamó al modelo: este caso costó cero en inferencia"})
        return pasos
    pii = "PII_RESIDUAL" in marcas or "RD-06" in reglas
    pasos.append({"nombre": "Seudonimización", "estado": "detenido" if pii else "ok",
                  "detalle": REGLAS["RD-06"] if pii else "Nombres, RUT y contactos reemplazados por tokens"})
    if pii:
        return pasos
    if not uso_ia(propuesta):
        motivo = ("Presupuesto diario agotado" if "PRESUPUESTO_AGOTADO" in marcas
                  else REGLAS["RD-16"])
        pasos.append({"nombre": "IA", "estado": "detenido", "detalle": motivo})
        return pasos
    pasos.append({"nombre": "IA", "estado": "ok",
                  "detalle": "Extrajo los hechos y propuso una tipificación"})
    pasos.append({"nombre": "Citas", "estado": "aviso" if "RD-15" in reglas else "ok",
                  "detalle": REGLAS["RD-15"] if "RD-15" in reglas
                  else "Cada cita se comparó con su fuente, carácter por carácter"})
    posteriores = [r for r in reglas if r not in PREVIAS and r not in {"RD-06", "RD-15", "RD-16"}]
    pasos.append({"nombre": "Reglas posteriores",
                  "estado": "aviso" if "RD-10" in posteriores else "ok",
                  "detalle": "; ".join(REGLAS.get(r, r) for r in posteriores) if posteriores
                  else "Ninguna regla tuvo que intervenir"})
    return pasos


def decision_modelo_corregida(propuesta):
    for bloque in propuesta.justificacion_y_citas or []:
        original = bloque.get("decision_modelo")
        if original and original != propuesta.decision:
            return original
    return None
