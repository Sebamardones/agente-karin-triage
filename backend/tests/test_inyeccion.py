"""La instrucción inyectada permanece como dato dentro de sus delimitadores."""

import test_grafo
from test_grafo import CASOS, ejecutar

sesion = test_grafo.sesion


def test_inyeccion_detectada_y_registrada(sesion):
    estado, fila, _ = ejecutar(sesion, "G-06")
    assert estado["inyeccion_detectada"] is True
    assert "DET-INY" in fila.reglas_aplicadas
    assert any(r["id"] == "DET-INY" and r["efecto"] == "INYECCION_REGISTRADA"
               for r in estado["reglas"])


def test_inyeccion_no_cambia_decision(sesion):
    _, fila, modelo = ejecutar(sesion, "G-06")
    assert fila.decision == "PROCEDE_INVESTIGACION"
    assert modelo.tipificaciones == 1


def test_instruccion_conservada_dentro_de_denuncia(sesion):
    estado, _, modelo = ejecutar(sesion, "G-06")
    instruccion = CASOS["G-06"]["entrada"]["relato"].split("###")[1]
    for llamada in modelo.llamadas:
        contenido = llamada["contenido_usuario"]
        assert contenido.startswith("<denuncia>\n")
        denuncia = contenido.split("<denuncia>\n")[1].split("\n</denuncia>")[0]
        assert instruccion in denuncia
        assert denuncia == estado["texto_seudonimizado"]


def test_etiquetas_apertura_y_cierre(sesion):
    _, _, modelo = ejecutar(sesion, "G-06")
    for llamada in modelo.llamadas:
        assert "<denuncia>" in llamada["contenido_usuario"]
        assert "</denuncia>" in llamada["contenido_usuario"]
