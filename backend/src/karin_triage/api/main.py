"""API y vistas renderizadas: toda propuesta permanece bajo revisión humana."""

import hashlib
import json
import os
import re
import secrets
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from pathlib import Path
from threading import Lock
from typing import Annotated
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from starlette.middleware.sessions import SessionMiddleware

from karin_triage.agent.grafo import procesar_caso
from karin_triage.agent.nodos import Contexto
from karin_triage.api import presentacion
from karin_triage.api.dependencias import obtener_sesion, usuario_actual
from karin_triage.api.etiquetas import etiqueta
from karin_triage.config import Ajustes
from karin_triage.core.reglas import EXPRESIONES_FALTA_PRUEBA, _normalizar
from karin_triage.core.taxonomia import Decision, MotivoDescarte
from karin_triage.models.tablas import (
    Denuncia,
    Preclasificacion,
    RevisionHumana,
    registrar_evento,
)

Usuario = Annotated[dict, Depends(usuario_actual)]
Sesion = Annotated[Session, Depends(obtener_sesion)]

DIRECTORIO = Path(__file__).resolve().parent
plantillas = Jinja2Templates(directory=DIRECTORIO / "plantillas")
plantillas.env.filters["etiqueta"] = etiqueta
# Huella del CSS en su URL: sin esto, un navegador que ya visitó el sitio sigue
# usando la hoja anterior tras un despliegue (StaticFiles no envía Cache-Control).
plantillas.env.globals["version_css"] = hashlib.sha256(
    (DIRECTORIO / "estaticos" / "estilo.css").read_bytes()).hexdigest()[:12]
plantillas.env.globals["version_js"] = hashlib.sha256(
    (DIRECTORIO / "estaticos" / "interaccion.js").read_bytes()).hexdigest()[:12]


def contradice_rd10(propuesta, decision):
    return "ACOSO_SEXUAL" in propuesta.tipo_conducta and decision == "DERIVA_MEDIACION"


def resolver_golden_set():
    directorio = os.getenv("KARIN_GOLDEN_SET_DIR")
    if directorio:
        ruta = Path(directorio) / "denuncias.jsonl"
        if ruta.is_file():
            return ruta
        raise FileNotFoundError("KARIN_GOLDEN_SET_DIR no contiene denuncias.jsonl")
    for padre in Path(__file__).resolve().parents:
        ruta = padre / "golden_set" / "denuncias.jsonl"
        if ruta.is_file():
            return ruta
    raise FileNotFoundError("Define KARIN_GOLDEN_SET_DIR")


def revisiones(sesion, propuesta):
    return list(sesion.scalars(select(RevisionHumana).where(
        RevisionHumana.preclasificacion_id == propuesta.id
    ).order_by(RevisionHumana.nivel, RevisionHumana.creado_en)))


def estado_revision(historial, propuesta):
    """Estado humano del caso para la bandeja: lo decide la última firma, no el agente."""
    if not historial:
        return "Pendiente de revisión humana"
    if any(r.decision_final == "DESCARTADO" and not r.motivo_descarte for r in historial):
        return "Revisión de una versión anterior (sin fundamento registrado)"
    ultima = historial[-1]
    firma = f"{etiqueta(ultima.decision_final)} ({ultima.funcionario})"
    if len(historial) == 1:
        if (propuesta.decision == "DESCARTADO" or ultima.decision_final == "DESCARTADO"
                or contradice_rd10(propuesta, ultima.decision_final)):
            return f"Pendiente de validación por un supervisor · nivel 1: {firma}"
        return f"Revisado · segunda revisión disponible: {firma}"
    return f"Validación humana completada: {firma}"


def datos_fila(sesion, denuncia, propuesta):
    historial = revisiones(sesion, propuesta)
    estado = estado_revision(historial, propuesta)
    clave = propuesta.decision or propuesta.estado_auxiliar
    return {"denuncia": denuncia, "p": propuesta, "historial": historial,
            "version": historial[0].version if historial else 0,
            "estado_revision": estado,
            "categoria": presentacion.categoria(historial, estado),
            "chip": presentacion.CHIP_DECISION.get(clave, ("Sin propuesta", "chip-neutro")),
            "uso_ia": presentacion.uso_ia(propuesta),
            "reglas": presentacion.lista_reglas(propuesta.reglas_aplicadas),
            "extracto": presentacion.extracto(propuesta),
            "tiempo": presentacion.tiempo_relativo(denuncia.fecha_ingesta)}


def bandeja_por_defecto(usuario):
    return "esperando" if usuario["rol"] == "supervisor" else "por-revisar"


def ordenar_cola(filas):
    """Urgentes primero; dentro de cada grupo se respeta el orden de prioridad."""
    return ([f for f in filas if f["p"].urgencia_resguardo]
            + [f for f in filas if not f["p"].urgencia_resguardo])


TANDA = re.compile(r"^DEMO-([0-9a-f]{8})-")
RELATO_NUEVO = re.compile(r"^DEMO-[0-9a-f]{12}$")


def separar_tanda_vigente(filas):
    """Divide la bandeja en casos vigentes y casos de tandas anteriores.

    Vigentes: la tanda más reciente y los relatos nuevos. Si no hay tandas, todos
    los casos son vigentes. Solo cambia lo que se muestra: no borra ni modifica
    ningún caso ni revisión.
    """
    tandas = [(f["p"].creado_en, m.group(1)) for f in filas
              if (m := TANDA.match(f["denuncia"].id_externo_dt))]
    if not tandas:
        return filas, []
    vigente = max(tandas)[1]
    vigentes, anteriores = [], []
    for f in filas:
        externo = f["denuncia"].id_externo_dt
        es_vigente = externo.startswith(f"DEMO-{vigente}-") or RELATO_NUEVO.match(externo)
        (vigentes if es_vigente else anteriores).append(f)
    return vigentes, anteriores


def motivo_bloqueo(historial, propuesta, usuario):
    """Por qué este usuario no puede registrar una revisión ahora; None si puede.

    El nivel 2 es siempre la validación de un supervisor distinto de quien
    firmó el nivel 1. Flujo de un descarte: el inspector hace la primera revisión
    y un supervisor la valida. Si el supervisor firmara primero, la demo (un solo
    supervisor) no tendría quién hiciera la segunda y el caso quedaría trabado.
    """
    if len(historial) >= 2:
        return 409, "El caso ya tiene dos revisiones humanas"
    if not historial and propuesta.decision == "DESCARTADO" and usuario["rol"] != "inspector":
        return 403, "La primera revisión de un descarte la hace el inspector"
    if historial:
        # El nivel 2 es siempre una validación: supervisor y persona distinta.
        # Si dependiera de que el descarte viniera de antes, un descarte firmado
        # recién en el nivel 2 quedaría sin validar (ocurrió con SINT-0001).
        if historial[0].funcionario == usuario["nombre"]:
            return 403, "La segunda revisión exige un funcionario distinto"
        if usuario["rol"] != "supervisor":
            return 403, "La segunda revisión exige supervisor"
    return None


def buscar(sesion, identificador):
    denuncia = sesion.get(Denuncia, identificador)
    propuesta = sesion.scalar(select(Preclasificacion).where(
        Preclasificacion.denuncia_id == identificador
    ).order_by(Preclasificacion.creado_en.desc(), Preclasificacion.id.desc()))
    if denuncia is None or propuesta is None:
        raise HTTPException(404, "Caso no encontrado")
    return denuncia, propuesta


def crear_app(ajustes=None, motor=None):
    ajustes = ajustes or Ajustes()
    propio = motor is None
    motor = motor or create_engine(ajustes.database_url)

    @asynccontextmanager
    async def lifespan(app):
        yield
        if propio:
            motor.dispose()

    app = FastAPI(title="Karin Triage", lifespan=lifespan)
    app.state.motor = motor
    carga_lock = Lock()
    carga_estado = {"en_curso": False, "procesados": 0, "saltados": 0, "fallidos": 0,
                    "total": 0}

    def cargar_en_segundo_plano(registros=None):
        try:
            with Session(motor) as sesion:
                entradas = registros if registros is not None else [
                    json.loads(linea)["entrada"] for linea in
                    resolver_golden_set().read_text(encoding="utf-8").splitlines() if linea.strip()]
                with carga_lock:
                    carga_estado["total"] = len(entradas)
                for registro in entradas:
                    try:
                        if sesion.scalar(select(Denuncia.id).where(
                            Denuncia.id_externo_dt == registro["id_externo_dt"]
                        )):
                            resultado = "saltados"
                        else:
                            procesar_caso(registro, Contexto(sesion))
                            sesion.commit()
                            resultado = "procesados"
                    except Exception:  # noqa: BLE001 - no exponer datos del proveedor
                        sesion.rollback()
                        resultado = "fallidos"
                    with carga_lock:
                        carga_estado[resultado] += 1
        except Exception:  # noqa: BLE001 - archivo o infraestructura no disponibles
            with carga_lock:
                carga_estado["fallidos"] += 1
        finally:
            with carga_lock:
                carga_estado["en_curso"] = False

    app.mount("/estaticos", StaticFiles(directory=DIRECTORIO / "estaticos"), name="estaticos")

    @app.middleware("http")
    async def proteger_rutas(request, call_next):
        publicas = {"/entrar", "/salir", "/salud"}
        if (request.url.path not in publicas
                and not request.url.path.startswith("/estaticos/")
                and request.session.get("usuario") not in {"inspector_demo", "supervisor_demo"}):
            if request.headers.get("HX-Request") == "true":
                # Un refresco periódico con la sesión vencida no debe pintar el login en la tabla.
                return Response(headers={"HX-Redirect": "/entrar"})
            return RedirectResponse("/entrar", 303)
        return await call_next(request)

    def vista(request, nombre, usuario=None, **datos):
        return plantillas.TemplateResponse(request=request, name=nombre,
                                          context={"usuario": usuario, **datos})

    @app.get("/salud")
    def salud():
        return {"estado": "ok"}

    @app.get("/entrar")
    def entrar(request: Request):
        return vista(request, "login.html")

    @app.post("/entrar")
    def autenticar(request: Request, usuario: str = Form(""), password: str = Form("")):
        cuentas = {"inspector_demo": ajustes.demo_password_analista,
                   "supervisor_demo": ajustes.demo_password_supervisor}
        secreto = cuentas.get(usuario)
        valido = secrets.compare_digest(password.encode(), (
            secreto.get_secret_value() if secreto else "credencial-inexistente"
        ).encode())
        request.session.clear()
        if secreto is None or not valido:
            return vista(request, "login.html", error="Usuario o contraseña incorrectos")
        request.session["usuario"] = usuario
        return RedirectResponse("/", 303)

    @app.get("/salir")
    def salir(request: Request):
        request.session.clear()
        return RedirectResponse("/entrar", 303)

    def clasificar(sesion):
        filas = sesion.execute(select(Denuncia, Preclasificacion).join(
            Preclasificacion, Preclasificacion.denuncia_id == Denuncia.id
        ).order_by(Preclasificacion.prioridad, Preclasificacion.creado_en)).all()
        vigentes, anteriores = separar_tanda_vigente(
            [datos_fila(sesion, d, p) for d, p in filas])
        grupos = {b: [] for b in presentacion.BANDEJAS}
        for f in vigentes:
            grupos[f["categoria"]].append(f)
        grupos["anteriores"] = anteriores
        return grupos, vigentes, len(filas)

    def metricas(sesion, vigentes):
        hoy = datetime.now(UTC).replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
        primeras = list(sesion.scalars(select(RevisionHumana).where(RevisionHumana.nivel == 1)))
        coinciden = sum(1 for r in primeras if r.coincide_con_agente)
        return {
            "revisadas_hoy": sesion.scalar(select(func.count(RevisionHumana.id)).where(
                RevisionHumana.creado_en >= hoy)) or 0,
            "coincidencia": round(100 * coinciden / len(primeras)) if primeras else None,
            "primeras": len(primeras),
            "sin_ia": sum(1 for f in vigentes if not f["uso_ia"]),
        }

    def datos_bandeja(sesion, usuario, bandeja=None):
        if bandeja not in presentacion.BANDEJAS:
            bandeja = bandeja_por_defecto(usuario)
        with carga_lock:
            estado_carga = dict(carga_estado)
        grupos, vigentes, total = clasificar(sesion)
        cola = ordenar_cola(grupos[bandeja])
        return {"bandeja": bandeja, "cola": cola,
                "urgentes": [f for f in cola if f["p"].urgencia_resguardo],
                "resto": [f for f in cola if not f["p"].urgencia_resguardo],
                "conteos": {b: len(v) for b, v in grupos.items()},
                "nombres": presentacion.NOMBRES_BANDEJA[usuario["rol"]],
                "carga": estado_carga, "total_casos": total,
                "pendientes": len(grupos["por-revisar"]),
                "metricas": metricas(sesion, vigentes)}

    def siguiente_en(sesion, usuario, bandeja, excluir):
        if bandeja not in presentacion.BANDEJAS:
            return None
        grupos, _, _ = clasificar(sesion)
        for f in ordenar_cola(grupos[bandeja]):
            if f["denuncia"].id != excluir:
                return f["denuncia"].id
        return None

    def datos_panel(request, sesion, usuario, denuncia, propuesta):
        fila = datos_fila(sesion, denuncia, propuesta)
        bloqueo = motivo_bloqueo(fila["historial"], propuesta, usuario)
        decisiones = list(Decision)
        if not fila["historial"] and usuario["rol"] != "inspector":
            decisiones.remove(Decision.DESCARTADO)
        citas_relato, citas_normativas = presentacion.citas_de(propuesta)
        relato, encontradas = presentacion.resaltar(denuncia.texto_seudonimizado, citas_relato)
        return {**fila, "decisiones": decisiones, "motivos": list(MotivoDescarte),
                "bloqueo": bloqueo[1] if bloqueo else None,
                "relato_marcado": relato, "encontradas": encontradas,
                "citas_relato": citas_relato, "citas_normativas": citas_normativas,
                "recorrido": presentacion.recorrido(propuesta),
                "decision_corregida": presentacion.decision_modelo_corregida(propuesta),
                "primera": fila["historial"][0] if fila["historial"] else None,
                "puede_descartar": Decision.DESCARTADO in decisiones,
                "mensaje": request.session.pop("mensaje", None)}

    @app.get("/")
    def bandeja(request: Request, usuario: Usuario, sesion: Sesion, bandeja: str | None = None):
        return vista(request, "bandeja.html", usuario, **datos_bandeja(sesion, usuario, bandeja),
                     mensaje_bandeja=request.session.pop("mensaje", None))

    @app.get("/bandeja/contenido")
    def bandeja_contenido(request: Request, usuario: Usuario, sesion: Sesion,
                          bandeja: str | None = None):
        # Refresco periódico: lo firmado por otro funcionario aparece sin recargar.
        return vista(request, "_bandeja.html", usuario, **datos_bandeja(sesion, usuario, bandeja))

    @app.post("/cargar-golden-set")
    def cargar(request: Request, usuario: Usuario, background_tasks: BackgroundTasks):
        if usuario["rol"] != "inspector":
            raise HTTPException(403, "Solo el inspector puede cargar casos sintéticos")
        try:
            # El total se conoce antes de empezar: la barra de progreso es determinada.
            total = sum(1 for linea in resolver_golden_set().read_text(
                encoding="utf-8").splitlines() if linea.strip())
        except FileNotFoundError:
            total = 0
        with carga_lock:
            if not carga_estado["en_curso"]:
                carga_estado.update(en_curso=True, procesados=0, saltados=0, fallidos=0,
                                    total=total)
                background_tasks.add_task(cargar_en_segundo_plano)
        request.session["mensaje"] = "Carga solicitada. Los casos aparecerán en la bandeja."
        return RedirectResponse("/", 303)

    def programar_demo(registros, background_tasks):
        with carga_lock:
            if carga_estado["en_curso"]:
                raise HTTPException(409, "Hay una carga en curso; espera antes de crear otra.")
            carga_estado.update(en_curso=True, procesados=0, saltados=0, fallidos=0,
                                total=len(registros))
            background_tasks.add_task(cargar_en_segundo_plano, registros)

    @app.get("/demo/nuevo")
    def formulario_demo(request: Request, usuario: Usuario):
        if usuario["rol"] != "inspector":
            raise HTTPException(403, "Solo el inspector puede crear casos sintéticos")
        return vista(request, "nuevo.html", usuario)

    @app.post("/demo/nuevo")
    def nuevo_demo(request: Request, usuario: Usuario, background_tasks: BackgroundTasks,
                   relato: Annotated[str, Form(min_length=40, max_length=6000)],
                   confirmar_sintetico: Annotated[bool, Form()] = False):
        if usuario["rol"] != "inspector":
            raise HTTPException(403, "Solo el inspector puede crear casos sintéticos")
        if not confirmar_sintetico:
            raise HTTPException(422, "Debes confirmar que el relato es ficticio y sin datos reales")
        registro = {"id_externo_dt": f"DEMO-{uuid4().hex[:12]}", "relato": relato,
                    "tipo_ingreso": "DIRECTA", "fecha_denuncia": date.today().isoformat(),
                    "empleador": "EMPRESA_SINTETICA", "sector_empleador": "PRIVADO"}
        programar_demo([registro], background_tasks)
        return RedirectResponse(f"/demo/seguimiento/{registro['id_externo_dt']}", 303)

    def estado_seguimiento(sesion, externo):
        if not RELATO_NUEVO.match(externo):
            raise HTTPException(404, "Seguimiento no encontrado")
        listo = sesion.scalar(select(Denuncia.id).where(Denuncia.id_externo_dt == externo))
        with carga_lock:
            en_curso = carga_estado["en_curso"]
        return listo, en_curso

    @app.get("/demo/seguimiento/{externo}")
    def seguimiento(externo: str, request: Request, usuario: Usuario, sesion: Sesion):
        listo, en_curso = estado_seguimiento(sesion, externo)
        if listo:
            return RedirectResponse(f"/casos/{listo}", 303)
        return vista(request, "seguimiento.html", usuario, externo=externo, en_curso=en_curso)

    @app.get("/demo/seguimiento/{externo}/estado")
    def seguimiento_estado(externo: str, request: Request, usuario: Usuario, sesion: Sesion):
        listo, en_curso = estado_seguimiento(sesion, externo)
        if listo:
            # htmx sigue el encabezado: la persona llega sola a la propuesta.
            return Response(headers={"HX-Redirect": f"/casos/{listo}"})
        return vista(request, "_seguimiento_estado.html", usuario, externo=externo,
                     en_curso=en_curso)

    @app.post("/demo/nueva-tanda")
    def nueva_tanda(request: Request, usuario: Usuario, background_tasks: BackgroundTasks):
        if usuario["rol"] != "inspector":
            raise HTTPException(403, "Solo el inspector puede crear una tanda de demo")
        tanda = uuid4().hex[:8]
        registros = []
        for linea in resolver_golden_set().read_text(encoding="utf-8").splitlines():
            if linea.strip():
                registro = dict(json.loads(linea)["entrada"])
                registro["id_externo_dt"] = f"DEMO-{tanda}-{registro['id_externo_dt']}"
                registros.append(registro)
        programar_demo(registros, background_tasks)
        request.session["mensaje"] = "Nueva tanda en proceso. Se conservaron los casos y revisiones anteriores."
        return RedirectResponse("/", 303)

    @app.get("/casos/{identificador}")
    def caso(identificador: str, request: Request, usuario: Usuario,
             sesion: Sesion, bandeja: str | None = None):
        d, p = buscar(sesion, identificador)
        panel = datos_panel(request, sesion, usuario, d, p)
        cola = datos_bandeja(sesion, usuario, bandeja or panel["categoria"])
        return vista(request, "bandeja.html", usuario, **cola, panel=panel,
                     seleccionado=d.id)

    @app.get("/casos/{identificador}/panel")
    def caso_panel(identificador: str, request: Request, usuario: Usuario, sesion: Sesion,
                   bandeja: str | None = None):
        d, p = buscar(sesion, identificador)
        return vista(request, "caso.html", usuario,
                     panel=datos_panel(request, sesion, usuario, d, p),
                     bandeja=bandeja if bandeja in presentacion.BANDEJAS else None)

    @app.get("/casos/{identificador}/estado")
    def caso_estado(identificador: str, request: Request, usuario: Usuario, sesion: Sesion):
        d, p = buscar(sesion, identificador)
        return vista(request, "_estado_caso.html", usuario, **datos_fila(sesion, d, p))

    @app.post("/casos/{identificador}/revision")
    def revisar(identificador: str, request: Request, decision_final: Annotated[Decision, Form()],
                version: Annotated[int, Form()], usuario: Usuario, sesion: Sesion,
                comentario: Annotated[str, Form()] = "",
                motivo_descarte: Annotated[str, Form()] = "",
                cita_respaldo: Annotated[str, Form()] = ""):
        d, p = buscar(sesion, identificador)
        historial = revisiones(sesion, p)
        bandeja_origen = presentacion.categoria(historial, estado_revision(historial, p))
        actual = historial[0].version if historial else 0
        if version != actual:
            raise HTTPException(409, "Otro funcionario revisó el caso mientras tanto; recarga.")
        bloqueo = motivo_bloqueo(historial, p, usuario)
        if bloqueo:
            raise HTTPException(*bloqueo)
        nivel = 2 if historial else 1
        if nivel == 1 and decision_final == Decision.DESCARTADO and usuario["rol"] != "inspector":
            # Un descarte iniciado por el supervisor no tendría quién lo validara.
            raise HTTPException(403, "La primera revisión de un descarte la hace el inspector")
        excepcion = contradice_rd10(p, decision_final.value)
        if excepcion:
            if not comentario.strip():
                raise HTTPException(422, "RD-10: la excepción requiere fundamento y validación de supervisor")
            if nivel == 1 and usuario["rol"] != "inspector":
                raise HTTPException(403, "La excepción RD-10 debe iniciarla el inspector y validarla otro supervisor")
        if decision_final == Decision.DESCARTADO:
            if motivo_descarte not in {m.value for m in MotivoDescarte} or not comentario.strip():
                raise HTTPException(422, "El descarte requiere un motivo del catálogo y un comentario")
            cita = " ".join(cita_respaldo.split())
            if not cita or cita not in " ".join(d.texto_seudonimizado.split()):
                raise HTTPException(422, "El descarte requiere una cita literal del relato seudonimizado")
            if any(t in _normalizar(comentario) for t in EXPRESIONES_FALTA_PRUEBA):
                raise HTTPException(422, "No se permite descartar por falta de prueba")
        else:
            motivo_descarte, cita_respaldo = "", ""
        try:
            if historial:
                # CAS atómico y versionado ORM: dos solicitudes no pueden firmar a la vez.
                historial[0].version += 1
                sesion.flush()
            else:
                # Reclama la primera revisión sin añadir columnas al modelo existente.
                reclamado = sesion.execute(update(Denuncia).where(
                    Denuncia.id == d.id, Denuncia.estado == "PENDIENTE_REVISION_HUMANA"
                ).values(estado="EN_REVISION_HUMANA"))
                if reclamado.rowcount != 1:
                    raise HTTPException(409, "Otro funcionario revisó el caso mientras tanto")
            coincide = decision_final.value == p.decision
            sesion.add(RevisionHumana(
                preclasificacion_id=p.id, funcionario=usuario["nombre"], rol=usuario["rol"],
                nivel=nivel, decision_final=decision_final.value, comentario=comentario,
                motivo_descarte=motivo_descarte or None, cita_respaldo=cita_respaldo or None,
                excepcion_rd10=excepcion,
                coincide_con_agente=coincide,
            ))
            registrar_evento(sesion, d.id, usuario["nombre"], "revision", {
                "nivel": nivel, "rol": usuario["rol"], "decision_final": decision_final.value,
                "coincide_con_agente": coincide,
                "motivo_descarte": motivo_descarte or None, "excepcion_rd10": excepcion,
            })
            sesion.commit()
        except (StaleDataError, IntegrityError):
            sesion.rollback()
            raise HTTPException(409, "Otro funcionario revisó el caso mientras tanto") from None
        destino = datos_fila(sesion, d, p)["categoria"]
        nombres = presentacion.NOMBRES_BANDEJA[usuario["rol"]]
        if destino == "esperando":
            aviso = "Enviado a un supervisor para su validación"
        elif nivel == 2:
            aviso = "Validación registrada · caso cerrado"
        elif decision_final.value == p.decision:
            aviso = f"Propuesta confirmada · pasó a {nombres[destino]}"
        else:
            aviso = f"Corrección registrada · pasó a {nombres[destino]}"
        if request.headers.get("HX-Request") == "true":
            # La interfaz saca la tarjeta de la cola, muestra el aviso y abre el siguiente caso.
            siguiente = siguiente_en(sesion, usuario, bandeja_origen, d.id)
            return Response(headers={"HX-Trigger": json.dumps({"revisionRegistrada": {
                "caso": d.id, "mensaje": aviso, "siguiente": siguiente,
                "bandeja": bandeja_origen}}, ensure_ascii=True)})
        request.session["mensaje"] = aviso
        return RedirectResponse(f"/casos/{d.id}", 303)

    app.add_middleware(
        SessionMiddleware, secret_key=ajustes.session_secret.get_secret_value(),
        same_site="lax", https_only=os.getenv("KARIN_HTTPS_ONLY") == "1",
    )
    return app


def __getattr__(nombre):
    # Uvicorn puede importar `main:app`; los tests crean aplicaciones aisladas.
    if nombre == "app":
        return crear_app()
    raise AttributeError(nombre)
