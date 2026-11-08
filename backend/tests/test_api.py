"""Contrato de la bandeja con SQLite temporal, sin modelo ni red."""

import json
import re
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
    monkeypatch.setenv("KARIN_DEMO_PASSWORD_ANALISTA", "inspector-sintetico")
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


def login(cliente, rol="inspector"):
    return cliente.post("/entrar", data={"usuario": f"{rol}_demo", "password": f"{rol}-sintetico"})


def revision(cliente, identificador, version=0, decision="DESCARTADO", **kw):
    return cliente.post(f"/casos/{identificador}/revision", data={
        "version": version, "decision_final": decision, "comentario": "Comentario sintético",
        "motivo_descarte": "NO_CONFIGURA_CONDUCTA",
        "cita_respaldo": "Relato sintético para revisión.",
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
    r = cliente.post("/entrar", data={"usuario": "inspector_demo", "password": secreto})
    assert "Usuario o contraseña incorrectos" in r.text
    assert secreto not in r.text
    assert cliente.get("/", follow_redirects=False).status_code == 303


def test_04_login_correcto(entorno):
    cliente, _ = entorno
    assert login(cliente).status_code == 200
    assert cliente.get("/").status_code == 200
    assert "httponly" in cliente.post("/entrar", data={
        "usuario": "inspector_demo", "password": "inspector-sintetico"
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
    assert "11 casos nuevos" in cliente.post("/cargar-golden-set").text
    assert "11 ya estaban en la bandeja" in cliente.post("/cargar-golden-set").text
    with Session(motor) as s:
        assert len(list(s.scalars(select(Denuncia)))) == 11


def test_07_detalle_propuesta(entorno):
    identificador = caso(entorno)
    login(entorno[0])
    html = entorno[0].get(f"/casos/{identificador}").text
    for texto in ("PROCEDE_INVESTIGACION", "Relato sintético", "RD-12", "Cita del relato · Relato sintético"):
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


def test_descarte_lo_inicia_el_inspector(entorno):
    cliente, _ = entorno
    propuesto = caso(entorno, externo="PROPUESTO", decision="DESCARTADO")
    otro = caso(entorno, externo="OTRO")
    login(cliente, "supervisor")
    # El supervisor no abre un descarte: ni el propuesto por el agente ni uno propio.
    r = revision(cliente, propuesto, decision="DERIVA_MEDIACION")
    assert r.status_code == 403 and "inspector" in r.text
    r = revision(cliente, otro, decision="DESCARTADO")
    assert r.status_code == 403 and "inspector" in r.text
    assert 'value="DESCARTADO"' not in cliente.get(f"/casos/{otro}").text
    assert revision(cliente, otro, decision="PROCEDE_INVESTIGACION").status_code == 200
    # Flujo completo: inspector primero, supervisor valida.
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
        assert set(evento.detalle) == {"nivel", "rol", "decision_final", "coincide_con_agente",
                                      "motivo_descarte", "excepcion_rd10"}
        assert verificar_cadena(s, identificador)


def test_sin_propuesta_y_sin_javascript(entorno):
    identificador = caso(entorno, decision=None)
    cliente, _ = entorno
    login(cliente)
    html = cliente.get(f"/casos/{identificador}").text
    assert "Sin propuesta: Modelo no disponible · revisión manual" in html
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
    assert "10 casos nuevos" in html and "1 con error" in html


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
    assert "0 de 11 casos procesados" in respuesta.text
    cliente.post("/cargar-golden-set")
    assert len(pendientes) == 1
    funcion, args, kwargs = pendientes.pop()
    funcion(*args, **kwargs)
    html = cliente.get("/").text
    assert "11 casos nuevos" in html and "Carga en curso" not in html


def test_exito_htmx_recarga_la_pagina(entorno):
    identificador = caso(entorno)
    login(entorno[0])
    r = revision(entorno[0], identificador)
    evento = json.loads(r.headers["HX-Trigger"])["revisionRegistrada"]
    # Sin recarga: la interfaz recibe a qué bandeja pasó el caso y cuál sigue.
    assert r.status_code == 200 and evento["caso"] == identificador
    assert evento["bandeja"] == "por-revisar" and evento["siguiente"] is None
    assert evento["mensaje"] == "Enviado a un supervisor para su validación"


def test_formulario_oculto_si_el_usuario_no_puede_revisar(entorno):
    identificador = caso(entorno, decision="DESCARTADO")
    cliente, _ = entorno
    login(cliente, "supervisor")
    html = cliente.get(f"/casos/{identificador}").text
    assert 'name="decision_final"' not in html and "la hace el inspector" in html
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
    html = cliente.get("/bandeja/contenido?bandeja=revisados").text
    assert 'id="bandeja-viva"' in html and "every 5s" in html
    assert "Revisado · segunda revisión disponible: Deriva a mediación (inspector_demo)" in html
    html = cliente.get("/bandeja/contenido?bandeja=esperando").text
    assert "Pendiente de validación por un supervisor · nivel 1: No corresponde a Ley Karin" in html
    login(cliente, "supervisor")
    assert revision(cliente, descarte, version=1).status_code == 200
    assert "Validación humana completada: No corresponde a Ley Karin · reconducir (supervisor_demo)" in cliente.get("/?bandeja=cerrados").text
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
    assert "Validación humana completada: No corresponde a Ley Karin · reconducir (supervisor_demo)" in cliente.get("/?bandeja=cerrados").text


@pytest.mark.parametrize("datos", [
    {}, {"motivo_descarte": "INVENTADO", "comentario": "Fundamento"},
    {"motivo_descarte": "NO_CONFIGURA_CONDUCTA", "comentario": "Sin pruebas"},
    {"motivo_descarte": "NO_CONFIGURA_CONDUCTA", "comentario": "Fundamento", "cita_respaldo": "Inventada"},
])
def test_descarte_humano_exige_fundamento_y_cita(entorno, datos):
    identificador = caso(entorno)
    login(entorno[0])
    r = entorno[0].post(f"/casos/{identificador}/revision", data={
        "decision_final": "DESCARTADO", "version": 0, **datos})
    assert r.status_code == 422
    with Session(entorno[1]) as sesion:
        assert not list(sesion.scalars(select(RevisionHumana)))


def test_descarte_persiste_fundamento(entorno):
    identificador = caso(entorno)
    login(entorno[0])
    assert revision(entorno[0], identificador).status_code == 200
    with Session(entorno[1]) as sesion:
        fila = sesion.scalar(select(RevisionHumana))
        assert fila.motivo_descarte == "NO_CONFIGURA_CONDUCTA"
        assert fila.cita_respaldo == "Relato sintético para revisión."


def test_excepcion_rd10_exige_comentario_y_supervisor(entorno):
    identificador = caso(entorno)
    with Session(entorno[1]) as sesion:
        sesion.scalar(select(Preclasificacion)).tipo_conducta = "ACOSO_SEXUAL"
        sesion.commit()
    cliente = entorno[0]
    login(cliente)
    assert "Advertencia RD-10" in cliente.get(f"/casos/{identificador}").text
    assert revision(cliente, identificador, decision="DERIVA_MEDIACION", comentario="").status_code == 422
    assert revision(cliente, identificador, decision="DERIVA_MEDIACION").status_code == 200
    assert "Pendiente de validación" in cliente.get("/?bandeja=esperando").text
    assert revision(cliente, identificador, version=1, decision="DERIVA_MEDIACION").status_code == 403
    login(cliente, "supervisor")
    assert revision(cliente, identificador, version=1, decision="DERIVA_MEDIACION").status_code == 200
    with Session(entorno[1]) as sesion:
        assert all(r.excepcion_rd10 for r in sesion.scalars(select(RevisionHumana)))


def test_demo_nueva_exige_confirmacion_y_no_borra_historial(entorno):
    cliente, motor = entorno
    identificador = caso(entorno)
    login(cliente)
    revision(cliente, identificador)
    relato = "Este es un relato completamente inventado de hostigamiento en una empresa ficticia."
    assert cliente.post("/demo/nuevo", data={"relato": relato}).status_code == 422
    assert cliente.post("/demo/nuevo", data={"relato": relato, "confirmar_sintetico": True}).status_code == 200
    with Session(motor) as sesion:
        assert len(list(sesion.scalars(select(Denuncia)))) == 2
        assert len(list(sesion.scalars(select(RevisionHumana)))) == 1
    login(cliente, "supervisor")
    assert cliente.post("/demo/nueva-tanda").status_code == 403


def test_tandas_generan_casos_nuevos_sin_borrar(entorno):
    cliente, motor = entorno
    login(cliente)
    cliente.post("/demo/nueva-tanda")
    cliente.post("/demo/nueva-tanda")
    with Session(motor) as sesion:
        assert len(list(sesion.scalars(select(Denuncia)))) == 22


def test_bandeja_sin_contadores_de_carga_vacios(entorno):
    login(entorno[0])
    html = entorno[0].get("/").text
    assert "Total de casos guardados: 0" in html
    assert "Carga terminada" not in html and "Datos sintéticos" in html


# --- Rediseño con identidad DT (docs/plan-diseno.md) ---------------------------


def test_franja_de_prototipo_y_accesibilidad_en_todas_las_paginas(entorno):
    cliente, _ = entorno
    publica = cliente.get("/entrar").text
    login(cliente)
    for html in (publica, cliente.get("/").text, cliente.get("/demo/nuevo").text):
        assert "no es un servicio de la Dirección del Trabajo" in html
        assert 'href="#contenido"' in html and 'id="contenido"' in html
        assert "/estaticos/logo-dt.svg" in html
    assert "plataforma del curso" in publica
    for archivo in ("logo-dt.svg", "cinta-contingencia-dark.svg"):
        assert cliente.get(f"/estaticos/{archivo}").status_code == 200


def test_bandeja_muestra_la_tanda_vigente_y_guarda_las_anteriores(entorno):
    cliente, motor = entorno
    login(cliente)
    cliente.post("/demo/nueva-tanda")
    cliente.post("/demo/nueva-tanda")
    caso(entorno, externo="DEMO-0123456789ab")  # relato nuevo: siempre vigente
    with Session(motor) as sesion:
        externos = [d.id_externo_dt for d in sesion.scalars(
            select(Denuncia).order_by(Denuncia.id_externo_dt))]
    tandas = sorted({e.split("-")[1] for e in externos if e.count("-") >= 2})
    assert len(tandas) == 2
    principal = cliente.get("/bandeja/contenido").text
    historial = cliente.get("/bandeja/contenido?bandeja=anteriores").text
    assert 'Tandas anteriores <span class="contador">11</span>' in principal
    assert "DEMO-0123456789ab" in principal and "DEMO-0123456789ab" not in historial
    # Cada tanda queda completa de un solo lado: nada se borra ni se mezcla.
    vigente = [t for t in tandas if f"DEMO-{t}-" in principal]
    anterior = [t for t in tandas if f"DEMO-{t}-" in historial]
    assert len(vigente) == 1 and len(anterior) == 1 and vigente != anterior
    assert f"DEMO-{vigente[0]}-" not in historial
    assert "Total de casos guardados: 23" in principal


def test_bandeja_sin_tandas_muestra_todo(entorno):
    caso(entorno, externo="SINT-0001")
    login(entorno[0])
    html = entorno[0].get("/").text
    assert "SINT-0001" in html and "Tandas anteriores" not in html


def test_motivo_de_descarte_solo_en_descartes(entorno):
    cliente, _ = entorno
    investigar = caso(entorno, externo="CASO-INVESTIGA")
    descartar = caso(entorno, externo="CASO-DESCARTE", decision="DESCARTADO")
    login(cliente)
    assert 'chip-reconducir">Motivo:' not in cliente.get(f"/casos/{investigar}").text
    assert 'chip-reconducir">Motivo:' in cliente.get(f"/casos/{descartar}").text


def test_revision_registrada_confirma_en_la_ficha(entorno):
    identificador = caso(entorno)
    cliente, _ = entorno
    login(cliente)
    # Sin JavaScript: redirección al caso con el aviso de a qué bandeja pasó.
    r = cliente.post(f"/casos/{identificador}/revision", data={
        "version": 0, "decision_final": "PROCEDE_INVESTIGACION", "comentario": ""})
    assert r.status_code == 200
    assert 'class="confirmacion">Propuesta confirmada · pasó a Revisados' in r.text
    assert "Propuesta confirmada" not in cliente.get(f"/casos/{identificador}").text


def test_css_versionado_por_contenido(entorno):
    cliente, _ = entorno
    huella = main.plantillas.env.globals["version_css"]
    assert len(huella) == 12
    assert f'/estaticos/estilo.css?v={huella}"' in cliente.get("/entrar").text
    assert cliente.get(f"/estaticos/estilo.css?v={huella}").status_code == 200


# --- Puesto de trabajo (docs/plan-interaccion.md) -------------------------------


def test_bandejas_por_rol_llevan_el_descarte_al_supervisor(entorno):
    cliente, _ = entorno
    descarte = caso(entorno, externo="DESCARTE-ROL", decision="DESCARTADO")
    login(cliente)
    assert "DESCARTE-ROL" in cliente.get("/").text
    assert revision(cliente, descarte).status_code == 200
    assert "DESCARTE-ROL" not in cliente.get("/").text
    login(cliente, "supervisor")
    html = cliente.get("/").text  # el supervisor entra directo a lo que debe validar
    activa = re.search(r'aria-current="page">(.*?)</a>', html, re.DOTALL).group(1)
    assert "Por validar" in activa and '<span class="contador">1</span>' in activa
    assert "DESCARTE-ROL" in html


def test_panel_parcial_muestra_veredicto_y_citas_marcadas(entorno):
    identificador = caso(entorno, texto="Inicio. Relato sintético para revisión. Fin.")
    with Session(entorno[1]) as sesion:
        p = sesion.scalar(select(Preclasificacion))
        p.justificacion_y_citas = [{"justificacion": "Sintética", "citas": [
            {"texto_literal": "Relato sintético para revisión.", "fuente": "denuncia"},
            {"texto_literal": "Cita inventada que no está", "fuente": "denuncia"}]}]
        sesion.commit()
    login(entorno[0])
    html = entorno[0].get(f"/casos/{identificador}/panel").text
    assert "<html" not in html and 'id="panel-caso"' in html
    assert "El agente propone" in html and "Procede investigación" in html
    assert '<mark id="cita-1" class="cita-marca" data-cita="1">Relato sintético para revisión.</mark>' in html
    assert 'id="cita-2"' not in html and "Citas del relato verificadas: 1 de 2" in html
    assert "no aparece tal cual en el texto" in html


def test_revision_abre_el_siguiente_caso_de_la_misma_bandeja(entorno):
    primero = caso(entorno, externo="PRIMERO", prioridad=0)
    segundo = caso(entorno, externo="SEGUNDO", prioridad=1)
    login(entorno[0])
    r = revision(entorno[0], primero, decision="PROCEDE_INVESTIGACION")
    evento = json.loads(r.headers["HX-Trigger"])["revisionRegistrada"]
    assert evento["siguiente"] == segundo
    assert evento["mensaje"] == "Propuesta confirmada · pasó a Revisados"


def test_seguimiento_del_relato_nuevo_lleva_a_la_propuesta(entorno):
    cliente, motor = entorno
    login(cliente)
    relato = "Relato completamente inventado sobre hostigamiento en una empresa ficticia."
    r = cliente.post("/demo/nuevo", data={"relato": relato, "confirmar_sintetico": True},
                     follow_redirects=False)
    destino = r.headers["location"]
    assert r.status_code == 303 and destino.startswith("/demo/seguimiento/DEMO-")
    externo = destino.rsplit("/", 1)[1]
    with Session(motor) as sesion:
        listo = sesion.scalar(select(Denuncia.id).where(Denuncia.id_externo_dt == externo))
    assert cliente.get(destino, follow_redirects=False).headers["location"] == f"/casos/{listo}"
    assert cliente.get(destino + "/estado").headers["HX-Redirect"] == f"/casos/{listo}"
    assert cliente.get("/demo/seguimiento/SINT-0001/estado").status_code == 404


def test_resaltar_escapa_el_relato_y_respeta_espacios():
    from karin_triage.api.presentacion import resaltar
    html, encontradas = resaltar("<b>x</b> la jefatura   grita", [
        {"texto_literal": "la jefatura grita"}])
    assert "<b>" not in html and "&lt;b&gt;" in html
    assert encontradas == {1} and 'data-cita="1">la jefatura   grita</mark>' in html


def test_recorrido_de_un_caso_sin_ia(entorno):
    identificador = caso(entorno, decision=None)
    with Session(entorno[1]) as sesion:
        p = sesion.scalar(select(Preclasificacion))
        p.justificacion_y_citas, p.reglas_aplicadas = [], "RD-02"
        p.estado_auxiliar, p.marcas_pipeline = "DERIVAR_OTRA_INSTITUCION", ""
        sesion.commit()
    login(entorno[0])
    html = entorno[0].get(f"/casos/{identificador}").text
    assert "Sin IA · RD-02" in html and "costó cero" in html
