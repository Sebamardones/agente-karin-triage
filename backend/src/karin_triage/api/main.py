"""API y vistas renderizadas: toda propuesta permanece bajo revisión humana."""

import json
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from starlette.middleware.sessions import SessionMiddleware

from karin_triage.agent.grafo import procesar_caso
from karin_triage.agent.nodos import Contexto
from karin_triage.api.dependencias import obtener_sesion, usuario_actual
from karin_triage.config import Ajustes
from karin_triage.core.taxonomia import Decision
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


def datos_fila(sesion, denuncia, propuesta):
    historial = revisiones(sesion, propuesta)
    return {"denuncia": denuncia, "p": propuesta, "historial": historial,
            "version": historial[0].version if historial else 0}


def motivo_bloqueo(historial, propuesta, usuario):
    """Por qué este usuario no puede registrar una revisión ahora; None si puede.

    Flujo de un descarte: el analista hace la primera revisión y un supervisor
    distinto la valida. Si el supervisor firmara primero, la demo (un solo
    supervisor) no tendría quién hiciera la segunda y el caso quedaría trabado.
    """
    if len(historial) >= 2:
        return 409, "El caso ya tiene dos revisiones humanas"
    if not historial and propuesta.decision == "DESCARTADO" and usuario["rol"] != "analista":
        return 403, "La primera revisión de un descarte la hace el analista"
    descarte = propuesta.decision == "DESCARTADO" or (
        historial and historial[0].decision_final == "DESCARTADO"
    )
    if historial and descarte:
        if historial[0].funcionario == usuario["nombre"]:
            return 403, "La segunda revisión exige un funcionario distinto"
        if usuario["rol"] != "supervisor":
            return 403, "La segunda revisión de un descarte exige supervisor"
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
    carga_estado = {"en_curso": False, "procesados": 0, "saltados": 0, "fallidos": 0}

    def cargar_en_segundo_plano():
        try:
            with Session(motor) as sesion:
                for linea in resolver_golden_set().read_text(encoding="utf-8").splitlines():
                    if not linea.strip():
                        continue
                    try:
                        registro = json.loads(linea)["entrada"]
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
                and request.session.get("usuario") not in {"analista_demo", "supervisor_demo"}):
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
        cuentas = {"analista_demo": ajustes.demo_password_analista,
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

    @app.get("/")
    def bandeja(request: Request, usuario: Usuario, sesion: Sesion):
        with carga_lock:
            estado_carga = dict(carga_estado)
        filas = sesion.execute(select(Denuncia, Preclasificacion).join(
            Preclasificacion, Preclasificacion.denuncia_id == Denuncia.id
        ).order_by(Preclasificacion.prioridad, Preclasificacion.creado_en)).all()
        return vista(request, "bandeja.html", usuario,
                     filas=[datos_fila(sesion, d, p) for d, p in filas],
                     mensaje=request.session.pop("mensaje", None), carga=estado_carga)

    @app.post("/cargar-golden-set")
    def cargar(request: Request, usuario: Usuario, background_tasks: BackgroundTasks):
        if usuario["rol"] != "analista":
            raise HTTPException(403, "Solo el analista puede cargar casos sintéticos")
        with carga_lock:
            if not carga_estado["en_curso"]:
                carga_estado.update(en_curso=True, procesados=0, saltados=0, fallidos=0)
                background_tasks.add_task(cargar_en_segundo_plano)
        request.session["mensaje"] = "Carga solicitada. Los casos aparecerán en la bandeja."
        return RedirectResponse("/", 303)

    @app.get("/casos/{identificador}")
    def caso(identificador: str, request: Request, usuario: Usuario,
             sesion: Sesion):
        d, p = buscar(sesion, identificador)
        fila = datos_fila(sesion, d, p)
        bloqueo = motivo_bloqueo(fila["historial"], p, usuario)
        decisiones = list(Decision)
        if not fila["historial"] and usuario["rol"] != "analista":
            decisiones.remove(Decision.DESCARTADO)
        return vista(request, "caso.html", usuario, **fila, decisiones=decisiones,
                     bloqueo=bloqueo[1] if bloqueo else None)

    @app.post("/casos/{identificador}/revision")
    def revisar(identificador: str, request: Request, decision_final: Annotated[Decision, Form()],
                version: Annotated[int, Form()], usuario: Usuario, sesion: Sesion,
                comentario: Annotated[str, Form()] = ""):
        d, p = buscar(sesion, identificador)
        historial = revisiones(sesion, p)
        actual = historial[0].version if historial else 0
        if version != actual:
            raise HTTPException(409, "Otro funcionario revisó el caso mientras tanto; recarga.")
        bloqueo = motivo_bloqueo(historial, p, usuario)
        if bloqueo:
            raise HTTPException(*bloqueo)
        nivel = 2 if historial else 1
        if nivel == 1 and decision_final == Decision.DESCARTADO and usuario["rol"] != "analista":
            # Un descarte iniciado por el supervisor no tendría quién lo validara.
            raise HTTPException(403, "La primera revisión de un descarte la hace el analista")
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
                coincide_con_agente=coincide,
            ))
            registrar_evento(sesion, d.id, usuario["nombre"], "revision", {
                "nivel": nivel, "rol": usuario["rol"], "decision_final": decision_final.value,
                "coincide_con_agente": coincide,
            })
            sesion.commit()
        except (StaleDataError, IntegrityError):
            sesion.rollback()
            raise HTTPException(409, "Otro funcionario revisó el caso mientras tanto") from None
        if request.headers.get("HX-Request") == "true":
            # Recarga completa: el historial y el formulario también deben reflejar la firma.
            respuesta = vista(request, "_fila.html", usuario, **datos_fila(sesion, d, p))
            respuesta.headers["HX-Refresh"] = "true"
            return respuesta
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
