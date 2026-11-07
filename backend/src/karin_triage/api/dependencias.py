"""Sesiones web y transacciones por solicitud."""

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session


def usuario_actual(request: Request):
    usuario = request.session.get("usuario")
    if usuario not in {"analista_demo", "supervisor_demo"}:
        raise HTTPException(303, headers={"Location": "/entrar"})
    return {"nombre": usuario, "rol": usuario.removesuffix("_demo")}


def obtener_sesion(request: Request):
    with Session(request.app.state.motor) as sesion:
        yield sesion
