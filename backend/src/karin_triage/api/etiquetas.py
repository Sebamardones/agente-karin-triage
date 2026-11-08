"""Etiquetas para presentar catálogos sin exponer sus identificadores internos."""

ETIQUETAS = {
    "PROCEDE_INVESTIGACION": "Procede investigación",
    "DERIVA_MEDIACION": "Deriva a mediación",
    "DESCARTADO": "No corresponde a Ley Karin · reconducir",
    "ACOSO_LABORAL": "Acoso laboral", "ACOSO_SEXUAL": "Acoso sexual",
    "VIOLENCIA_TERCEROS": "Violencia de terceros",
    "REQUIERE_ANTECEDENTES": "Requiere antecedentes",
    "DERIVAR_OTRA_INSTITUCION": "Derivar a otra institución",
    "NO_CONFIGURA_CONDUCTA": "No configura una conducta del catálogo",
    "SIN_RELACION_LABORAL": "Sin relación laboral",
    "DUPLICADA": "Duplicada", "DESISTIMIENTO": "Desistimiento",
    "PII_RESIDUAL": "Datos personales residuales · revisión manual",
    "LLM_REFUSAL": "Modelo no disponible · revisión manual",
    "PRESUPUESTO_AGOTADO": "Presupuesto agotado · revisión manual",
    "FUERA_DE_ALCANCE": "Fuera del alcance de la demo",
    "REGIMEN_ANTERIOR": "Revisar régimen anterior",
    # Revisiones guardadas antes de renombrar el perfil «analista» a «inspector».
    "analista": "inspector",
}


def etiqueta(valor):
    if not valor:
        return "Sin marcas"
    return ", ".join(ETIQUETAS.get(v.strip(), v.strip()) for v in str(valor).split(","))
