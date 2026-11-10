"""Seudonimización local, sin E/S ni registro de los valores originales.

El mapa es sensible y queda exclusivamente en manos del llamador. La detección
heurística no constituye una garantía general de ausencia de datos personales.

Tres capas, en este orden: (1) nombres conocidos que llegan en los campos
estructurados del caso, por coincidencia exacta; (2) patrones estructurados
—RUT, correo, teléfono, dirección, URL—; (3) heurística de nombres propios.
La capa 1 gana sobre la 3, y la lista `EXCLUSIONES` gana sobre la 3 para que los
nombres institucionales y normativos sobrevivan intactos.

Limitación conocida y aceptada
------------------------------
La capa 3 exige *Title Case* —inicial mayúscula y resto en minúscula— y limita
la coincidencia a `_MAX_PALABRAS_NOMBRE` palabras candidatas. En consecuencia,
un nombre que aparece **únicamente** en mayúsculas completas, sin ninguna
aparición en *Title Case* en el mismo texto, no lo detecta la heurística.

Se eligió así a propósito. La versión anterior aceptaba mayúsculas completas y
no limitaba el largo, de modo que un relato escrito íntegro en mayúsculas
—algo que una persona alterada escribe de verdad— se sustituía por un solo
token, llegaba vacío al modelo y la denuncia terminaba en la cola de
antecedentes incompletos sin que nadie supiera por qué. Perder un nombre en
mayúsculas es malo; destruir el relato completo es peor, y es además un fallo
silencioso.

Esa fuga queda cubierta por la capa 1 cuando el nombre llega en los campos
estructurados, que es la vía normal para la persona denunciante y el empleador.
También queda cubierta si el nombre aparece al menos una vez en *Title Case* en
el texto: la sustitución se propaga entonces a todas sus grafías.

Las pruebas que fijan este comportamiento están en
`tests/test_seudonimizador.py`, bajo el encabezado de regresiones de la capa 3.
"""

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoSeudonimizacion:
    texto: str
    mapa: dict[str, str]
    hallazgos: list[str]


EXCLUSIONES = (
    "Direccion del Trabajo", "Dirección del Trabajo", "Inspeccion del Trabajo",
    "Inspección del Trabajo", "Codigo del Trabajo", "Código del Trabajo", "Ley Karin",
    "Ministerio del Trabajo", "Contraloria General de la Republica",
    "Contraloría General de la República", "Estatuto Administrativo",
    "Superintendencia de Seguridad Social",
    "lunes", "martes", "miercoles", "miércoles", "jueves", "viernes", "sabado", "sábado",
    "domingo", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
    "septiembre", "setiembre", "octubre", "noviembre", "diciembre",
)

_TOKEN = r"\[(?:PERSONA|EMPRESA|RUT|EMAIL|TELEFONO|DIRECCION|URL)_\d+\]"
_LETRAS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"
_MAYUSCULA = "A-ZÁÉÍÓÚÜÑ"
_MINUSCULA = "a-záéíóúüñ"
# Artículos, pronombres y posesivos no forman parte de un nombre. El filtro
# se aplica a cada componente para conservar el contexto antes y después de él.
_CONTEXTO = r"(?:el|la|los|las|un|una|unos|unas|yo|mi|mis|tu|tus|su|sus|me|nos)"
# Se exige Title Case: inicial mayúscula y el resto en minúscula. Una palabra en
# mayúsculas completas (GRITO, SISTEMA) deja de ser candidata a nombre propio.
# Ver la limitación conocida en el docstring del módulo.
_PALABRA = (
    rf"(?!(?i:{_CONTEXTO})(?!\w))[{_MAYUSCULA}][{_MINUSCULA}]+"
)
_ESPACIO = r"[^\S\r\n]+"
_PARTICULA = r"(?:de|del|la|las|los|y)"
_SUFIJO = r"(?:Limitada|Ltda\.?|SpA|S\.A\.|SA|EIRL|E\.I\.R\.L\.|y Compa[nñ][ií]a)"
# Salvaguarda estructural: como maximo 4 palabras candidatas. La primera va
# fuera del grupo repetido, de modo que el grupo admite 1 a 3 repeticiones.
# Sin este limite, un cambio futuro en la expresion puede volver a tragarse un
# relato completo, que es el fallo silencioso que esta regla evita.
_MAX_PALABRAS_NOMBRE = 4
_NOMBRE = re.compile(
    rf"(?<!\w){_PALABRA}(?:{_ESPACIO}(?:{_PARTICULA}{_ESPACIO})*"
    rf"(?:{_SUFIJO}|{_PALABRA}))"
    rf"{{1,{_MAX_PALABRAS_NOMBRE - 1}}}"
    rf"(?:{_ESPACIO}{_SUFIJO}(?!\w))?(?!\w)"
)
_GIRO = re.compile(
    r"^(?:Comercial|Industrias|Servicios|Transportes|Minimarket|Panader[ií]a|"
    r"Constructora|Sociedad|Empresa|Cl[ií]nica|Colegio|Supermercado)\b", re.IGNORECASE
)
_SOCIEDAD = re.compile(rf"(?<!\w){_SUFIJO}(?!\w)", re.IGNORECASE)
_PATRONES = (
    ("RUT", re.compile(r"(?<!\w)(?:\d{1,2}\.\d{3}\.\d{3}|\d{7,8})-[\dKk](?!\w)")),
    ("EMAIL", re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.IGNORECASE)),
    ("TELEFONO", re.compile(
        r"(?<![\w$\d])(?<!\$ )(?<!CLP )(?:\+56[ -]?)?[29](?:[ -]?\d){8}(?![\w\d])"
    )),
    ("DIRECCION", re.compile(
        rf"(?<!\w)(?:Avenida|Av\.|Calle|Pasaje|Psje\.|Camino)\s+"
        rf"(?:[{_LETRAS}]+\s+){{1,10}}(?:[Nn]°?\s*)?\d+\b", re.IGNORECASE
    )),
    ("URL", re.compile(r"(?<!\w)(?:https?://|www\.)[^\s<>\[\]]+", re.IGNORECASE)),
)
_PROTEGIDO = re.compile(_TOKEN)
_EXCLUIDO = re.compile(
    rf"{_TOKEN}|(?<!\w)(?:"
    + "|".join(re.escape(valor) for valor in sorted(EXCLUSIONES, key=len, reverse=True))
    + r")(?!\w)", re.IGNORECASE
)


def _segmentos(texto: str, protegido: re.Pattern[str]) -> Iterator[tuple[str, bool]]:
    """Separa zonas protegidas para que ninguna coincidencia las atraviese."""
    inicio = 0
    for match in protegido.finditer(texto):
        yield texto[inicio:match.start()], False
        yield match.group(), True
        inicio = match.end()
    yield texto[inicio:], False


def _sustituir(
    texto: str, patron: re.Pattern[str], reemplazo: Callable[[re.Match[str]], str],
    protegido: re.Pattern[str] = _PROTEGIDO,
) -> str:
    return "".join(
        segmento if reservado else patron.sub(reemplazo, segmento)
        for segmento, reservado in _segmentos(texto, protegido)
    )


def _categoria_nombre(valor: str) -> str:
    return "EMPRESA" if _GIRO.search(valor) or _SOCIEDAD.search(valor) else "PERSONA"


def seudonimizar(
    texto: str, nombres_conocidos: list[str] | None = None,
    empresas_conocidas: list[str] | None = None,
) -> ResultadoSeudonimizacion:
    """Aplica nombres conocidos, patrones y heurística, en ese orden.

    `empresas_conocidas` son nombres que vienen del campo estructurado del
    empleador: se tokenizan siempre como EMPRESA, aunque no lleven giro ni
    tipo societario («Municipalidad de …» no los lleva).

    Las variantes de mayúsculas comparten token y conservan en el mapa la
    primera grafía encontrada. Su capitalización individual no es reversible.
    """
    mapa: dict[str, str] = {}
    indices: dict[tuple[str, str], str] = {}
    conteos: dict[str, int] = {}
    hallazgos: list[str] = []
    # Evita colisiones con tokens que ya vinieran en el texto de entrada.
    reservados = set(_PROTEGIDO.findall(texto))

    def token(categoria: str, valor: str) -> str:
        clave = categoria, valor.casefold()
        if clave not in indices:
            numero = conteos.get(categoria, 0) + 1
            while f"[{categoria}_{numero}]" in reservados:
                numero += 1
            conteos[categoria] = numero
            nuevo = f"[{categoria}_{numero}]"
            indices[clave] = nuevo
            mapa[nuevo] = valor
            if categoria not in hallazgos:
                hallazgos.append(categoria)
        return indices[clave]

    empresas = {n.strip().casefold() for n in empresas_conocidas or [] if n.strip()}

    def categoria_conocida(valor: str) -> str:
        return "EMPRESA" if valor.strip().casefold() in empresas else _categoria_nombre(valor)

    conocidos = sorted(
        {n for n in [*(nombres_conocidos or []), *(empresas_conocidas or [])] if n.strip()},
        key=lambda n: (-len(n), n.casefold(), n),
    )
    if conocidos:
        patron = re.compile(
            r"(?<!\w)(?:" + "|".join(re.escape(n) for n in conocidos) + r")(?!\w)", re.IGNORECASE
        )
        texto = _sustituir(texto, patron, lambda m: token(categoria_conocida(m.group()), m.group()))
    for categoria, patron in _PATRONES:
        texto = _sustituir(texto, patron, lambda m, cat=categoria: token(cat, m.group()))
    # Descubre primero las grafías capitalizadas; sustituye también sus otras
    # apariciones sin distinguir mayúsculas, incluso si estaban antes en el relato.
    nombres = {
        m.group() for segmento, reservado in _segmentos(texto, _EXCLUIDO) if not reservado
        for m in _NOMBRE.finditer(segmento)
    }
    if nombres:
        patron = re.compile(
            r"(?<!\w)(?:"
            + "|".join(re.escape(n) for n in sorted(nombres, key=lambda n: (-len(n), n)))
            + r")(?!\w)", re.IGNORECASE,
        )
        texto = _sustituir(
            texto, patron, lambda m: token(_categoria_nombre(m.group()), m.group()), _EXCLUIDO
        )
    return ResultadoSeudonimizacion(texto, mapa, hallazgos)


def detectar_pii_residual(texto: str) -> list[str]:
    """Reescanea sin modificar el texto ni considerar los tokens como PII."""
    categorias: list[str] = []
    for categoria, patron in _PATRONES:
        if any(patron.search(s) for s, reservado in _segmentos(texto, _PROTEGIDO) if not reservado):
            categorias.append(categoria)
    for segmento, reservado in _segmentos(texto, _EXCLUIDO):
        if not reservado:
            for match in _NOMBRE.finditer(segmento):
                categoria = _categoria_nombre(match.group())
                if categoria not in categorias:
                    categorias.append(categoria)
    return categorias
