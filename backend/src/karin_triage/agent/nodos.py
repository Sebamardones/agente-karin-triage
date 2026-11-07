"""Nodos con dependencias inyectadas y auditoría limitada a metadatos."""

import json
import unicodedata
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import date
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from karin_triage.agent.estado import EstadoTriage
from karin_triage.config.ajustes import AjustesNucleo
from karin_triage.core.reglas import (
    EntradaDenuncia,
    ResultadoRegla,
    aplicar_reglas_post,
    aplicar_reglas_previas,
    rd_06,
    rd_15,
    rd_16,
)
from karin_triage.core.taxonomia import EstadoAuxiliar, SectorEmpleador, TipoIngreso
from karin_triage.models.salidas_llm import HechosExtraidos, PropuestaClasificacion
from karin_triage.models.tablas import Denuncia, Preclasificacion, registrar_evento
from karin_triage.services.llm import PresupuestoAgotado, llamar, resolver_prefijo
from karin_triage.services.seudonimizador import detectar_pii_residual
from karin_triage.services.seudonimizador import seudonimizar as seudonimizar_texto

SENALES_INYECCION = (
    "ignora tus instrucciones", "ignora las instrucciones anteriores",
    "nueva instruccion", "instruccion del sistema", "system:", "assistant:",
    "olvida lo anterior", "eres un asistente", "responde solo",
)
MARCAS_CORTE = {"PII_RESIDUAL", "LLM_REFUSAL", "PRESUPUESTO_AGOTADO"}


@dataclass
class Contexto:
    sesion: Session
    llamar_llm: Callable = llamar
    prompt_tipificacion: str = "tipificar_v3.md"


def fabricar_nodos(contexto: Contexto) -> dict[str, Callable[[EstadoTriage], dict]]:
    """Cada cierre recibe estado y devuelve únicamente las claves modificadas."""
    sesion = contexto.sesion

    def agregar(estado, resultados):
        return estado.get("reglas", []) + [asdict(r) for r in resultados]

    def entrada_reglas(estado):
        e = estado["entrada"]
        return EntradaDenuncia(
            relato=e["relato"], empleador=e["empleador"], fecha_denuncia=e["fecha_denuncia"],
            tipo_ingreso=TipoIngreso(e["tipo_ingreso"]),
            sector_empleador=SectorEmpleador(e["sector_empleador"]),
            hash_contenido=e["hash_contenido"], hashes_previos=e["hashes_previos"],
        )

    def ingestar_y_validar(estado):
        e = {k: v.strip() if isinstance(v, str) else v for k, v in estado["entrada"].items()}
        e["relato"] = e.get("relato") or ""
        e["empleador"] = e.get("empleador") or ""
        fecha = e.get("fecha_denuncia")
        e["fecha_denuncia"] = date.fromisoformat(fecha) if isinstance(fecha, str) else fecha
        e["tipo_ingreso"] = TipoIngreso(e.get("tipo_ingreso", "DIRECTA")).value
        e["sector_empleador"] = SectorEmpleador(
            e.get("sector_empleador", "NO_DETERMINADO")
        ).value
        fecha_iso = e["fecha_denuncia"].isoformat() if e["fecha_denuncia"] else ""
        e["hash_contenido"] = sha256(
            (e["relato"] + "|" + e["empleador"] + "|" + fecha_iso).encode("utf-8")
        ).hexdigest()
        e["hashes_previos"] = list(sesion.scalars(select(Denuncia.hash_contenido)))
        normalizado = "".join(c for c in unicodedata.normalize("NFD", e["relato"].lower())
                              if unicodedata.category(c) != "Mn")
        inyeccion = any(s in normalizado for s in SENALES_INYECCION)
        # El modelo existente exige fecha no nula: no inventar una fecha ausente.
        if e["fecha_denuncia"] is None:
            raise ValueError("fecha_denuncia obligatoria para persistir; no se inventa una fecha")
        fila = Denuncia(
            id_externo_dt=e.get("id_externo_dt") or str(uuid4()),
            tipo_ingreso=e["tipo_ingreso"], fecha_denuncia=e["fecha_denuncia"],
            empleador=seudonimizar_texto(e["empleador"], [e["empleador"]]).texto,
            sector_empleador=e["sector_empleador"], texto_seudonimizado="",
            hash_contenido=e["hash_contenido"], estado="PENDIENTE_REVISION_HUMANA",
        )
        sesion.add(fila)
        sesion.flush()
        registrar_evento(sesion, fila.id, "pipeline", "ingesta", {
            k: e[k] for k in ("tipo_ingreso", "sector_empleador", "hash_contenido")
        })
        resultados = [ResultadoRegla("DET-INY", True, "INYECCION_REGISTRADA",
                                     "Se detectó una instrucción dentro del dato.")] if inyeccion else []
        return {"entrada": e, "denuncia_id": fila.id, "inyeccion_detectada": inyeccion,
                "reglas": agregar(estado, resultados), "marcas": [], "estado_auxiliar": None,
                "hechos": None, "propuesta": None, "intentos_validacion": 0,
                "llamadas_llm": 0, "costo_usd": 0.0, "tokens_entrada": 0, "tokens_salida": 0,
                "cache_read_tokens": 0}

    def reglas_previas(estado):
        # RD-02/RD-03 cortan aquí. RD-06 recibe [] deliberadamente y se evalúa
        # después de seudonimizar, siempre antes del LLM: no alterar esta precedencia.
        efecto, resultados = aplicar_reglas_previas(entrada_reglas(estado), hallazgos_pii=[])
        cambios = {"reglas": agregar(estado, resultados)}
        if isinstance(efecto, EstadoAuxiliar):
            cambios["estado_auxiliar"] = efecto.value
        elif efecto:
            cambios["marcas"] = estado["marcas"] + [efecto.value]
        return cambios

    def seudonimizar(estado):
        e = estado["entrada"]
        resultado = seudonimizar_texto(e["relato"], nombres_conocidos=[e["empleador"]])
        sesion.get(Denuncia, estado["denuncia_id"]).texto_seudonimizado = resultado.texto
        return {"texto_seudonimizado": resultado.texto, "mapa_seudonimos": resultado.mapa}

    def control_pii_residual(estado):
        hallazgos = detectar_pii_residual(estado["texto_seudonimizado"])
        cambios = {"hallazgos_pii": hallazgos}
        if hallazgos:
            cambios.update(reglas=agregar(estado, [rd_06(hallazgos)]),
                           marcas=estado["marcas"] + ["PII_RESIDUAL"])
        return cambios

    def ejecutar_llm(estado, nombre, formato, effort, contenido, clave):
        prompt = (resolver_prefijo().parent / nombre).read_bytes().decode("utf-8")
        try:
            respuesta = contexto.llamar_llm(
                prompt_nodo=prompt, contenido_usuario=contenido, formato=formato,
                effort=effort, sesion=sesion,
            )
        except PresupuestoAgotado:
            return {"marcas": estado["marcas"] + ["PRESUPUESTO_AGOTADO"], "propuesta": None}
        cambios = {k: estado.get(k, 0) + getattr(respuesta, k) for k in
                   ("tokens_entrada", "tokens_salida", "cache_read_tokens", "costo_usd")}
        cambios["llamadas_llm"] = estado["llamadas_llm"] + 1
        if respuesta.refusal:
            cambios.update(reglas=agregar(estado, [rd_16(stop_reason="refusal")]),
                           marcas=estado["marcas"] + ["LLM_REFUSAL"], propuesta=None)
        else:
            cambios[clave] = formato.model_validate(respuesta.datos).model_dump(mode="json")
        return cambios

    def contenido_denuncia(estado):
        return f"<denuncia>\n{estado['texto_seudonimizado']}\n</denuncia>"

    def extraer_hechos(estado):
        return ejecutar_llm(estado, "extraer_hechos_v1.md", HechosExtraidos, "low",
                            contenido_denuncia(estado), "hechos")

    def tipificar_y_proponer(estado):
        contenido = (contenido_denuncia(estado) + "\n<hechos>\n"
                     + json.dumps(estado["hechos"], ensure_ascii=False)
                     + "\n</hechos>\n<dictamenes>\n</dictamenes>")
        return ejecutar_llm(estado, contexto.prompt_tipificacion, PropuestaClasificacion,
                            "medium", contenido, "propuesta")

    def validar_salida(estado):
        resultado = rd_15(PropuestaClasificacion.model_validate(estado["propuesta"]),
                          estado["texto_seudonimizado"], estado["intentos_validacion"],
                          resolver_prefijo().read_text(encoding="utf-8"))
        cambios = {"reglas": agregar(estado, [resultado])}
        if resultado.aplico and estado["intentos_validacion"] == 0:
            cambios["intentos_validacion"] = 1
        return cambios

    def reglas_duras_post(estado):
        # Se guarda lo que propuso el modelo ANTES de corregirlo. Sin esto, una
        # propuesta corregida por RD-10 llega al funcionario con la decisión ya
        # arreglada y la justificación original argumentando lo contrario, sin
        # que nada indique que una regla intervino. Eso no es auditable: el
        # funcionario ve una contradicción y no sabe de dónde viene.
        decision_modelo = (estado.get("propuesta") or {}).get("decision")
        propuesta, resultados = aplicar_reglas_post(
            PropuestaClasificacion.model_validate(estado["propuesta"]),
            estado["texto_seudonimizado"], HechosExtraidos.model_validate(estado["hechos"]),
            prefijo_normativo=resolver_prefijo().read_text(encoding="utf-8"),
        )
        return {"decision_modelo": decision_modelo,
                "propuesta": propuesta.model_dump(mode="json"),
                "reglas": agregar(estado, resultados)}

    def calcular_ruta(estado):
        p = estado.get("propuesta") or {}
        if p.get("urgencia_resguardo") or MARCAS_CORTE.intersection(estado["marcas"]):
            prioridad = 0
        elif any(r["aplico"] and r["id"] in {"RD-11", "RD-13", "RD-15"}
                 and r["efecto"] != "REINTENTO" for r in estado["reglas"]):
            prioridad = 1
        else:
            prioridad = 2 if p.get("decision") == "DESCARTADO" else 3
        return {"prioridad": prioridad}

    def persistir(estado):
        p = estado.get("propuesta") or {}
        ids = list(dict.fromkeys(r["id"] for r in estado["reglas"] if r["aplico"]))
        version = Path(contexto.prompt_tipificacion).stem
        fila = Preclasificacion(
            denuncia_id=estado["denuncia_id"],
            version_pipeline=f"{version}+reglas2+{AjustesNucleo().modelo}",
            decision=p.get("decision"), estado_auxiliar=estado["estado_auxiliar"],
            marcas_pipeline=",".join(estado["marcas"]), tipo_conducta=",".join(
                p.get("tipo_conducta", [])), reglas_aplicadas=",".join(ids),
            justificacion_y_citas=[{
                "decision_modelo": estado.get("decision_modelo"),
                **{k: p[k] for k in ("justificacion", "citas", "supuestos") if k in p},
            }] if p else [],
            prioridad=estado["prioridad"],
            **{k: p[k] for k in ("vulneracion_ddff", "urgencia_resguardo",
                                 "motivo_descarte", "confianza") if k in p},
            **{k: estado[k] for k in ("tokens_entrada", "tokens_salida", "cache_read_tokens",
                                      "costo_usd")},
        )
        sesion.add(fila)
        registrar_evento(sesion, estado["denuncia_id"], "pipeline", "preclasificacion", {
            "decision": p.get("decision"), "prioridad": estado["prioridad"],
            "reglas": ids, "confianza": p.get("confianza"), "costo_usd": estado["costo_usd"],
        })
        sesion.flush()
        return {}

    return {f.__name__: f for f in (
        ingestar_y_validar, reglas_previas, seudonimizar, control_pii_residual,
        extraer_hechos, tipificar_y_proponer, validar_salida, reglas_duras_post,
        calcular_ruta, persistir,
    )}
