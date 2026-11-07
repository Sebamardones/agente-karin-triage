"""Ejecución finita sin checkpointer: la fila persistida es la cola humana."""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from karin_triage.agent.estado import EstadoTriage
from karin_triage.agent.nodos import Contexto, fabricar_nodos


def construir_grafo(contexto: Contexto) -> CompiledStateGraph:
    grafo = StateGraph(EstadoTriage)
    for nombre, nodo in fabricar_nodos(contexto).items():
        grafo.add_node(nombre, nodo)
    grafo.add_edge(START, "ingestar_y_validar")
    grafo.add_edge("ingestar_y_validar", "reglas_previas")
    grafo.add_conditional_edges("reglas_previas", lambda e: "calcular_ruta" if
                               e["estado_auxiliar"] or e["marcas"] else "seudonimizar")
    grafo.add_edge("seudonimizar", "control_pii_residual")
    grafo.add_conditional_edges("control_pii_residual", lambda e: "calcular_ruta" if
                               "PII_RESIDUAL" in e["marcas"] else "extraer_hechos")
    for origen, destino in (("extraer_hechos", "tipificar_y_proponer"),
                            ("tipificar_y_proponer", "validar_salida")):
        grafo.add_conditional_edges(origen, lambda e, destino=destino: "calcular_ruta" if
                                   {"LLM_REFUSAL", "PRESUPUESTO_AGOTADO"}.intersection(
                                       e["marcas"]) else destino)
    grafo.add_conditional_edges("validar_salida", lambda e: "tipificar_y_proponer" if
                               e["reglas"][-1]["efecto"] == "REINTENTO"
                               else "reglas_duras_post")
    grafo.add_edge("reglas_duras_post", "calcular_ruta")
    grafo.add_edge("calcular_ruta", "persistir")
    grafo.add_edge("persistir", END)
    return grafo.compile()


def procesar_caso(registro: dict, contexto: Contexto) -> str:
    """El llamador controla commit/rollback de su transacción."""
    return construir_grafo(contexto).invoke({"entrada": registro})["denuncia_id"]
