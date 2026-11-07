"""Mide una versión del prompt de tipificación contra el golden set.

Uso:

    cd backend
    uv run --python 3.12 python ../evals/runner.py --prompt tipificar_v1.md
    uv run --python 3.12 python ../evals/runner.py --prompt tipificar_v2.md

Cada corrida escribe `evals/salidas/<prompt>-<marca>.json` con el detalle por
caso y un resumen de las métricas. `evals/salidas/` está en `.gitignore`: se
versiona el informe (`docs/MEJORA_PROMPTS.md`), no las corridas crudas.

**Esto gasta dinero real.** Son hasta 16 llamadas al modelo por corrida, dos por
cada uno de los 8 casos, salvo los que las reglas duras cortan antes. El tope
diario del código y el límite de la consola siguen aplicando.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend" / "src"))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from karin_triage.agent.grafo import construir_grafo
from karin_triage.agent.nodos import Contexto
from karin_triage.models.tablas import Base, Preclasificacion
from karin_triage.services import llm

GOLDEN = RAIZ / "golden_set" / "denuncias.jsonl"
SALIDAS = RAIZ / "evals" / "salidas"


def cargar_casos() -> list[dict]:
    return [json.loads(l) for l in GOLDEN.read_text(encoding="utf-8").splitlines() if l.strip()]


def literal(cita: dict, texto: str, prefijo: str | None = None) -> bool:
    """Misma normalización que RD-15: solo espacios en blanco consecutivos."""
    if cita.get("fuente") == "normativa":
        texto = llm.leer_prefijo() if prefijo is None else prefijo
    fragmento = " ".join(cita.get("texto_literal", "").split())
    return bool(fragmento) and fragmento in " ".join(texto.split())


def evaluar(nombre_prompt: str) -> dict:
    casos = cargar_casos()
    motor = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(motor)

    detalle: list[dict] = []
    with Session(motor) as sesion:
        contexto = Contexto(sesion, llm.llamar, prompt_tipificacion=nombre_prompt)
        grafo = construir_grafo(contexto)
        for caso in casos:
            esperado = caso["esperado"]
            llamadas = []

            def contabilizar(**kwargs):
                llamadas.append(1)
                return llm.llamar(**kwargs)

            contexto = Contexto(sesion, contabilizar, prompt_tipificacion=nombre_prompt)
            grafo = construir_grafo(contexto)
            base = {"id": caso["id"], "decision_esperada": esperado.get("decision"),
                    "estado_auxiliar_esperado": esperado.get("estado_auxiliar"),
                    "urgencia_esperada": esperado.get("urgencia_resguardo"),
                    "tipos_esperados": esperado.get("tipo_conducta", [])}
            try:
                estado = grafo.invoke({"entrada": caso["entrada"]})
                error = None
            except Exception as exc:                      # noqa: BLE001
                sesion.rollback()
                detalle.append({**base, "error": type(exc).__name__, "hubo_llm": bool(llamadas),
                                "llamadas_llm": len(llamadas)})
                continue
            sesion.commit()
            fila = sesion.scalar(
                select(Preclasificacion).where(Preclasificacion.denuncia_id == estado["denuncia_id"]))
            bloque = (fila.justificacion_y_citas or [{}])[0]
            citas = bloque.get("citas", [])
            texto = estado.get("texto_seudonimizado", "")

            detalle.append({
                **base,
                "id": caso["id"],
                "titulo": caso["titulo"],
                "error": error,
                "decision_esperada": esperado.get("decision"),
                "decision_obtenida": fila.decision,
                "decision_del_modelo": bloque.get("decision_modelo"),
                "tipos_modelo": (estado.get("propuesta") or {}).get("tipo_conducta", []),
                "decision_correcta": fila.decision == esperado.get("decision"),
                "estado_auxiliar_esperado": esperado.get("estado_auxiliar"),
                "estado_auxiliar_obtenido": fila.estado_auxiliar,
                "estado_auxiliar_correcto":
                    fila.estado_auxiliar == esperado.get("estado_auxiliar"),
                "urgencia_esperada": esperado.get("urgencia_resguardo"),
                "urgencia_obtenida": fila.urgencia_resguardo,
                "citas_totales": len(citas),
                "citas_literales": sum(1 for c in citas if literal(c, texto)),
                "reglas_aplicadas": fila.reglas_aplicadas,
                "llamadas_llm": estado.get("llamadas_llm", 0),
                "reintento_de_validacion": estado.get("intentos_validacion", 0) > 0,
                "hubo_llm": estado.get("llamadas_llm", 0) > 0,
                "propuesta_valida": bool(citas) and all(literal(c, texto) for c in citas),
                "costo_usd": fila.costo_usd or 0.0,
            })

    return {"prompt": nombre_prompt,
            "modelo": llm.AjustesNucleo().modelo,
            "golden_sha256": hashlib.sha256(GOLDEN.read_bytes()).hexdigest(),
            "prompt_sha256": hashlib.sha256((RAIZ / "prompts" / nombre_prompt).read_bytes()).hexdigest(),
            "marca": datetime.now(UTC).isoformat(timespec="seconds"),
            "detalle": detalle,
            "metricas": metricas(detalle)}


def metricas(detalle: list[dict]) -> dict:
    con_propuesta = [d for d in detalle if d.get("decision_esperada")]
    citas_totales = sum(d.get("citas_totales", 0) for d in detalle)
    citas_ok = sum(d.get("citas_literales", 0) for d in detalle)

    # Las dos primeras NO se compensan con el resto. Si fallan, la version del
    # prompt no se publica, aunque las demas metricas esten perfectas.
    sexual_a_mediacion = sum(
        d.get("decision_del_modelo") == "DERIVA_MEDIACION"
        and "ACOSO_SEXUAL" in (d.get("tipos_esperados", []) + d.get("tipos_modelo", []))
        for d in detalle)
    falsos_descartes = sum(
        1 for d in con_propuesta
        if d.get("decision_obtenida") == "DESCARTADO"
        and d["decision_esperada"] in ("PROCEDE_INVESTIGACION", "DERIVA_MEDIACION"))

    urgencia_esperada = [d for d in detalle if d.get("urgencia_esperada") is not None]
    positivos = [d for d in urgencia_esperada if d["urgencia_esperada"] is True]
    con_llm = [d for d in detalle if d.get("hubo_llm", d.get("llamadas_llm", 0) > 0)]
    return {
        "acoso_sexual_a_mediacion_por_el_modelo": sexual_a_mediacion,
        "falsos_descartes": falsos_descartes,
        "decision_correcta": f"{sum(1 for d in con_propuesta if d.get('decision_correcta'))}"
                             f"/{len(con_propuesta)}",
        "estado_auxiliar_correcto":
            f"{sum(1 for d in detalle if d.get('estado_auxiliar_esperado') and d.get('estado_auxiliar_correcto'))}"
            f"/{sum(1 for d in detalle if d.get('estado_auxiliar_esperado'))}",
        "citas_literales_validas":
            f"{citas_ok}/{citas_totales}" + (f" ({100 * citas_ok // citas_totales}%)"
                                             if citas_totales else ""),
        "json_valido_al_primer_intento": None,
        "nota_json": "No se captura JSON crudo: el SDK entrega objetos parseados. Se mide esquema+citas sin reintento.",
        "salida_validada_sin_reintento":
            f"{sum(1 for d in con_llm if not d.get('error') and d.get('propuesta_valida') and not d.get('reintento_de_validacion'))}/{len(con_llm)}",
        "urgencia_correcta":
            f"{sum(1 for d in urgencia_esperada if not d.get('error') and d.get('urgencia_obtenida') == d['urgencia_esperada'])}/{len(urgencia_esperada)}",
        "urgencia_positiva_detectada":
            f"{sum(1 for d in positivos if d.get('urgencia_obtenida') is True)}/{len(positivos)}",
        "urgencia_falsos_positivos": sum(d.get("urgencia_obtenida") is True
                                         and d["urgencia_esperada"] is False for d in urgencia_esperada),
        "errores": sum(1 for d in detalle if d.get("error")),
        "llamadas_llm": sum(d.get("llamadas_llm", 0) for d in detalle),
        "costo_usd_total": round(sum(d.get("costo_usd", 0.0) for d in detalle), 4),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prompt", default="tipificar_v2.md",
                    help="nombre del archivo en prompts/, por ejemplo tipificar_v1.md")
    args = ap.parse_args()

    if not (RAIZ / "prompts" / args.prompt).is_file():
        print(f"No existe prompts/{args.prompt}", file=sys.stderr)
        return 2

    print(f"Evaluando prompts/{args.prompt} sobre {GOLDEN.name}.")
    print("Esto hace llamadas reales al modelo y cuesta dinero.\n")

    resultado = evaluar(args.prompt)

    print(f"{'caso':6} {'esperado':24} {'obtenido':24} {'citas':>7}  reglas")
    for d in resultado["detalle"]:
        if d.get("error"):
            print(f"{d['id']:6} ERROR: {d['error']}")
            continue
        esp = d["decision_esperada"] or d["estado_auxiliar_esperado"] or "-"
        obt = d["decision_obtenida"] or d["estado_auxiliar_obtenido"] or "-"
        marca = "  " if (d["decision_correcta"] or d["estado_auxiliar_correcto"]) else "<-"
        print(f"{d['id']:6} {esp:24} {obt:24} "
              f"{d['citas_literales']}/{d['citas_totales']:<5} {d['reglas_aplicadas'] or ''} {marca}")

    print("\nMetricas:")
    for k, v in resultado["metricas"].items():
        print(f"  {k:42} {v}")

    SALIDAS.mkdir(parents=True, exist_ok=True)
    destino = SALIDAS / f"{Path(args.prompt).stem}-{resultado['marca'].replace(':', '')}.json"
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDetalle en {destino.relative_to(RAIZ)}")
    return int(bool(resultado["metricas"]["errores"]))


if __name__ == "__main__":
    raise SystemExit(main())
