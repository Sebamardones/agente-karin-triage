"""Contrato de la bandeja con SQLite temporal, sin modelo ni red."""

import json
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from karin_triage.api import main
from karin_triage.models.tablas import (
    Base,
    Denuncia,
    EventoAuditoria,
    Preclasificacion,
    RevisionHumana,
    verificar_cadena,
)


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("KARIN_SESSION_SECRET", "secreto-sintetico-exclusivo-tests")
    monkeypatch.setenv("KARIN_DEMO_PASSWORD_ANALISTA", "analista-sintetico")
    monkeypatch.setenv("KARIN_DEMO_PASSWORD_SUPERVISOR", "supervisor-sintetico")
    monkeypatch.setenv("KARIN_HTTPS_ONLY", "0")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    motor = create_engine(f"sqlite:///{tmp_path / 'api.db'}")
    Base.metadata.create_all(motor)

    def falso(registro, contexto):
        return insertar(contexto.sesion, registro["id_externo_dt"])

    monkeypatch.setattr(main, "procesar_caso", falso)
    with TestClient(main.crear_app(motor=motor)) as cliente:
        yield cliente, motor
    motor.dispose()


def insertar(sesion, externo="SINTETICO-1", prioridad=3, decision="PROCEDE_INVESTIGACION",
             texto="Relato sintético para revisión."):
    d = Denuncia(id_externo_dt=externo, tipo_ingreso="DIRECTA", fecha_denuncia=date(2026, 11, 1),
                 empleador="EMPRESA_SINTETICA", sector_empleador="PRIVADO",
                 texto_seudonimizado=texto, hash_contenido="0" * 64,
                 estado="PENDIENTE_REVISION_HUMANA")
    sesion.add(d)
    sesion.flush()
    sesion.add(Preclasificacion(
        denuncia_id=d.id, version_pipeline="prueba", decision=decision,
        prioridad=prioridad, confianza=0.9, reglas_aplicadas="RD-12,RD-14",
        justificacion_y_citas=[{"justificacion": "Revisión requerida", "citas": [
            {"texto_literal": texto, "fuente": "denuncia", "referencia": "Relato sintético"}
        ]}], marcas_pipeline="LLM_REFUSAL" if decision is None else "",
    ))
    sesion.flush()
    return d.id


def caso(entorno, **kw):
    with Session(entorno[1]) as sesion:
        identificador = insertar(sesion, **kw)
        sesion.commit()
        return identificador


def login(cliente, rol="analista"):
    return cliente.post("/entrar", data={"usuario": f"{rol}_demo", "password": f"{rol}-sintetico"})


def revision(cliente, identificador, version=0, decision="DESCARTADO", **kw):
    return cliente.post(f"/casos/{identificador}/revision", data={
        "version": version, "decision_final": decision, "comentario": "Comentario sintético",
        **kw,
    }, headers={"HX-Request": "true"})


def test_01_salud_publica(entorno):
    r = entorno[0].get("/salud")
    assert r.status_code == 200 and r.json() == {"estado": "ok"}


def test_02_sin_sesion(entorno):
    r = entorno[0].get("/", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/entrar"


def test_03_password_incorrecta(entorno):
    cliente, _ = entorno
    secreto = "password-sintetica-incorrecta"
    r = cliente.post("/entrar", data={"usuario": "analista_demo", "password": secreto})
    assert "Usuario o contraseña incorrectos" in r.text
    assert secreto not in r.text
    assert cliente.get("/", follow_redirects=False).status_code == 303


def test_04_login_correcto(entorno):
    cliente, _ = entorno
    assert login(cliente).status_code == 200
    assert cliente.get("/").status_code == 200
    assert "httponly" in cliente.post("/entrar", data={
        "usuario": "analista_demo", "password": "analista-sintetico"
    }, follow_redirects=False).headers["set-cookie"].lower()


def test_05_orden_prioridad(entorno):
    for prioridad in (3, 0, 1):
        caso(entorno, externo=f"CASO-PRIORIDAD-{prioridad}", prioridad=prioridad)
    login(entorno[0])
    html = entorno[0].get("/").text
    assert html.index("CASO-PRIORIDAD-0") < html.index("CASO-PRIORIDAD-1")
    assert html.index("CASO-PRIORIDAD-1") < html.index("CASO-PRIORIDAD-3")


def test_06_carga_idempotente(entorno):
    cliente, motor = entorno
    login(cliente)
    assert "procesados: 8" in cliente.post("/cargar-golden-set").text
    assert "saltados: 8" in cliente.post("/cargar-golden-set").text
    with Session(motor) as s:
        assert len(list(s.scalars(select(Denuncia)))) == 8


def test_07_detalle_propuesta(entorno):
    identificador = caso(entorno)
    login(entorno[0])
    html = entorno[0].get(f"/casos/{identificador}").text
    for texto in ("PROCEDE_INVESTIGACION", "Relato sintético", "RD-12", "Fuente: denuncia"):
        assert texto in html


def test_08_version_vieja(entorno):
    identificador = caso(entorno)
    login(entorno[0])
    assert revision(entorno[0], identificador).status_code == 200
    r = revision(entorno[0], identificador)
    assert r.status_code == 409 and "Otro funcionario" in r.text


def test_09_descarte_misma_persona(entorno):
    identificador = caso(entorno, decision="DESCARTADO")
    login(entorno[0])
    assert revision(entorno[0], identificador).status_code == 200
    r = revision(entorno[0], identificador, version=1)
    assert r.status_code == 403 and "distinto" in r.text


def test_descarte_lo_inicia_el_analista(entorno):
    cliente, _ = entorno
    propuesto = caso(entorno, externo="PROPUESTO", decision="DESCARTADO")
    otro = caso(entorno, externo="OTRO")
    login(cliente, "supervisor")
    # El supervisor no abre un descarte: ni el propuesto por el agente ni uno propio.
    r = revision(cliente, propuesto, decision="DERIVA_MEDIACION")
    assert r.status_code == 403 and "analista" in r.text
    r = revision(cliente, otro, decision="DESCARTADO")
    assert r.status_code == 403 and "analista" in r.text
    assert 'value="DESCARTADO"' not in cliente.get(f"/casos/{otro}").text
    assert revision(cliente, otro, decision="PROCEDE_INVESTIGACION").status_code == 200
    # Flujo completo: analista primero, supervisor valida.
    login(cliente)
    assert revision(cliente, propuesto).status_code == 200
    login(cliente, "supervisor")
    assert revision(cliente, propuesto, version=1).status_code == 200


def test_10_descarte_rol_y_supervisor(entorno):
    identificador = caso(entorno, decision="DESCARTADO")
    cliente, _ = entorno
    login(cliente)
    assert revision(cliente, identificador).status_code == 200
    assert revision(cliente, identificador, version=1).status_code == 403
    # Usuario diferente con rol incorrecto: se verifica sin depender de la UI.
    with Session(entorno[1]) as s:
        primera = s.scalar(select(RevisionHumana))
        primera.funcionario = "funcionario_sintetico_distinto"
        s.commit()
        version = primera.version
    r = revision(cliente, identificador, version=version)
    assert r.status_code == 403 and "supervisor" in r.text
    login(cliente, "supervisor")
    assert revision(cliente, identificador, version=version).status_code == 200


def test_11_coincidencia(entorno):
    cliente, motor = entorno
    login(cliente)
    a = caso(entorno, externo="CORRECCION")
    b = caso(entorno, externo="CONFIRMACION")
    assert revision(cliente, a).status_code == 200
    assert revision(cliente, b, decision="PROCEDE_INVESTIGACION").status_code == 200
    with Session(motor) as s:
        filas = list(s.scalars(select(RevisionHumana).order_by(RevisionHumana.creado_en)))
        assert [r.coincide_con_agente for r in filas] == [False, True]


def test_12_html_escapado(entorno):
    identificador = caso(entorno, texto="<script>alert(1)</script>")
    login(entorno[0])
    html = entorno[0].get(f"/casos/{identificador}").text
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_13_auditoria_sin_comentario(entorno):
    identificador = caso(entorno)
    login(entorno[0])
    assert revision(entorno[0], identificador).status_code == 200
    with Session(entorno[1]) as s:
        evento = s.scalar(select(EventoAuditoria))
        assert evento.accion == "revision"
        assert "Comentario sintético" not in json.dumps(evento.detalle, ensure_ascii=False)
        assert set(evento.detalle) == {"nivel", "rol", "decision_final", "coincide_con_agente"}
        assert verificar_cadena(s, identificador)


def test_sin_propuesta_y_sin_javascript(entorno):
    identificador = caso(entorno, decision=None)
    cliente, _ = entorno
    login(cliente)
    html = cliente.get(f"/casos/{identificador}").text
    assert "Sin propuesta: LLM_REFUSAL" in html
    assert 'name="decision_final"' in html
    r = cliente.post(f"/casos/{identificador}/revision", data={
        "version": 0, "decision_final": "PROCEDE_INVESTIGACION", "comentario": "Sintético",
    }, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == f"/casos/{identificador}"


def test_carga_continua_tras_fallo(entorno, monkeypatch):
    original = main.procesar_caso
    llamadas = []

    def fallar_primero(registro, contexto):
        llamadas.append(registro)
        if len(llamadas) == 1:
            original(registro, contexto)
            raise ValueError("Fallo sintético")
        return original(registro, contexto)

    monkeypatch.setattr(main, "procesar_caso", fallar_primero)
    login(entorno[0])
    html = entorno[0].post("/cargar-golden-set").text
    assert "procesados: 7" in html and "fallidos: 1" in html


def test_logout_roles_y_rutas_protegidas(entorno):
    cliente, _ = entorno
    login(cliente, "supervisor")
    assert cliente.post("/cargar-golden-set").status_code == 403
    cliente.get("/salir")
    for ruta in ("/", "/docs", "/openapi.json", "/casos/inexistente"):
        assert cliente.get(ruta, follow_redirects=False).headers["location"] == "/entrar"
    assert cliente.get("/estaticos/estilo.css").status_code == 200


def test_resolver_directorio_entorno(entorno, monkeypatch, tmp_path):
    monkeypatch.setenv("KARIN_GOLDEN_SET_DIR", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        main.resolver_golden_set()
    ruta = tmp_path / "denuncias.jsonl"
    ruta.write_text("", encoding="utf-8")
    assert main.resolver_golden_set() == ruta


def test_carga_programada_responde_sin_esperar_y_no_duplica(entorno, monkeypatch):
    pendientes = []

    def programar(self, funcion, *args, **kwargs):
        pendientes.append((funcion, args, kwargs))

    monkeypatch.setattr(main.BackgroundTasks, "add_task", programar)
    cliente, _ = entorno
    login(cliente)
    respuesta = cliente.post("/cargar-golden-set")
    assert respuesta.status_code == 200 and "Carga en curso" in respuesta.text
    assert "procesados: 0" in respuesta.text
    cliente.post("/cargar-golden-set")
    assert len(pendientes) == 1
    funcion, args, kwargs = pendientes.pop()
    funcion(*args, **kwargs)
    html = cliente.get("/").text
    assert "procesados: 8" in html and "Carga en curso" not in html


def test_exito_htmx_recarga_la_pagina(entorno):
    identificador = caso(entorno)
    login(entorno[0])
    r = revision(entorno[0], identificador)
    assert r.status_code == 200 and r.headers["HX-Refresh"] == "true"


def test_formulario_oculto_si_el_usuario_no_puede_revisar(entorno):
    identificador = caso(entorno, decision="DESCARTADO")
    cliente, _ = entorno
    login(cliente, "supervisor")
    html = cliente.get(f"/casos/{identificador}").text
    assert 'name="decision_final"' not in html and "la hace el analista" in html
    login(cliente)
    assert 'name="decision_final"' in cliente.get(f"/casos/{identificador}").text
    assert revision(cliente, identificador).status_code == 200
    html = cliente.get(f"/casos/{identificador}").text
    assert 'name="decision_final"' not in html and "funcionario distinto" in html
    login(cliente, "supervisor")
    assert 'name="decision_final"' in cliente.get(f"/casos/{identificador}").text


def test_bandeja_muestra_el_estado_humano_y_se_refresca(entorno):
    cliente, _ = entorno
    descarte = caso(entorno, externo="DESCARTE", decision="DESCARTADO")
    simple = caso(entorno, externo="SIMPLE")
    login(cliente)
    assert "Pendiente de revisión humana" in cliente.get("/bandeja/contenido").text
    assert revision(cliente, simple, decision="DERIVA_MEDIACION").status_code == 200
    assert revision(cliente, descarte).status_code == 200
    html = cliente.get("/bandeja/contenido").text
    assert 'id="bandeja-viva"' in html and "every 5s" in html
    assert "Revisado: DERIVA_MEDIACION (analista_demo)" in html
    assert "Pendiente de validación por un supervisor · nivel 1: DESCARTADO" in html
    login(cliente, "supervisor")
    assert revision(cliente, descarte, version=1).status_code == 200
    assert "Validado: DESCARTADO (supervisor_demo)" in cliente.get("/").text
    estado = cliente.get(f"/casos/{descarte}/estado").text
    assert 'id="estado-caso"' in estado and "Nivel 2 · supervisor_demo" in estado


def test_refresco_con_sesion_vencida_redirige_sin_pintar_login(entorno):
    r = entorno[0].get("/bandeja/contenido", headers={"HX-Request": "true"},
                       follow_redirects=False)
    assert r.status_code == 200 and r.headers["HX-Redirect"] == "/entrar" and r.text == ""


def test_nivel_dos_siempre_supervisor_distinto(entorno):
    # Caso SINT-0001: propuesta sin descarte, y el descarte llega recién en el nivel 2.
    cliente, _ = entorno
    identificador = caso(entorno)
    login(cliente)
    assert revision(cliente, identificador, decision="DERIVA_MEDIACION").status_code == 200
    r = revision(cliente, identificador, version=1, decision="DESCARTADO")
    assert r.status_code == 403 and "distinto" in r.text
    html = cliente.get(f"/casos/{identificador}").text
    assert 'name="decision_final"' not in html
    login(cliente, "supervisor")
    assert revision(cliente, identificador, version=1, decision="DESCARTADO").status_code == 200
    assert "Validado: DESCARTADO (supervisor_demo)" in cliente.get("/").text
