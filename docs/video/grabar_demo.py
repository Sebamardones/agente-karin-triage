"""Graba las tomas del video de demostración (docs/GUION_VIDEO.md).

Cada toma es un clip .webm aparte, a 1920×1080, con un cursor visible. El
montaje con la narración se hace después con ffmpeg.

Uso, desde la raíz del repositorio:

    uv run --with playwright python docs/video/grabar_demo.py sesion
    uv run --with playwright python docs/video/grabar_demo.py preparar
    uv run --with playwright python docs/video/grabar_demo.py grabar [toma ...]

- `sesion` abre una ventana en /entrar. La persona inicia sesión como
  inspector_demo; el script guarda la cookie de sesión fuera del repositorio
  (~/.cache/karin-video/). El script nunca escribe contraseñas.
- `preparar` crea una tanda nueva y espera a que termine de procesarse.
  Gasta API (unos USD 0,2).
- `grabar` graba todas las tomas o solo las indicadas. La toma `ingreso`
  registra un caso nuevo (gasta API, unos USD 0,02) y la toma `decidir`
  confirma ese caso.

Opciones: --base URL (por defecto, la aplicación pública), --salida DIR.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, sync_playwright

BASE_PUBLICA = "https://karin-triage-grupo7-c7c6a3fb2988.herokuapp.com"
REPO = "https://github.com/Sebamardones/agente-karin-triage/blob/entrega/codex-revision/README.md"
RAIZ = Path(__file__).resolve().parent
SESION = Path(
    os.environ.get(
        "KARIN_VIDEO_SESION", Path.home() / ".cache" / "karin-video" / "sesion-inspector.json"
    )
)

# Playwright graba en píxeles CSS: el viewport mide lo mismo que el video. El
# zoom de 125 % del guion se aplica con CSS (`zoom`) sobre la página.
VIEWPORT = {"width": 1920, "height": 1080}
VIDEO = {"width": 1920, "height": 1080}
ZOOM = 1.25

EMPLEADOR = "Comercial Los Aromos Limitada"
MESES = ["marzo", "abril", "mayo", "junio", "febrero", "enero", "julio", "agosto"]
RELATO = (
    "Trabajo como administrativa en la oficina de una empresa ficticia desde {mes}. "
    "Desde hace dos meses, mi jefatura me excluye de las reuniones del equipo, revisa "
    "en voz alta mis errores frente a todos y me dijo que si sigo reclamando me va a "
    "dejar sin contrato en diciembre. Ayer me tomó del brazo con fuerza en el pasillo "
    "para que no me fuera de la oficina. Tengo miedo de volver mañana."
)

ZOOM_JS = """
(() => {
  const aplicar = () => { document.documentElement.style.zoom = '%s'; };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', aplicar); else aplicar();
})();
"""

# Cursor dibujado en la página: Playwright no graba el puntero del sistema.
CURSOR_JS = """
(() => {
  const poner = () => {
    if (document.getElementById('cursor-demo')) return;
    const c = document.createElement('div');
    c.id = 'cursor-demo';
    c.style.cssText = 'position:fixed;left:0;top:0;width:22px;height:22px;z-index:2147483647;' +
      'pointer-events:none;transform:translate(-3px,-2px);transition:transform .08s;';
    c.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M3 2l7.5 19 2.6-7.6L21 10.9z" ' +
      'fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    document.documentElement.appendChild(c);
    const xy = JSON.parse(sessionStorage.getItem('cursor-demo') || '[-50,-50]');
    c.style.left = xy[0] + 'px'; c.style.top = xy[1] + 'px';
    addEventListener('mousemove', e => {
      c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px';
      try { sessionStorage.setItem('cursor-demo', JSON.stringify([e.clientX, e.clientY])); } catch (_) {}
    }, true);
    addEventListener('mousedown', () => c.style.transform = 'translate(-3px,-2px) scale(.8)', true);
    addEventListener('mouseup', () => c.style.transform = 'translate(-3px,-2px)', true);
  };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', poner); else poner();
})();
"""


def chromium_local() -> str | None:
    """Usa el Chromium ya descargado por Playwright, si existe."""
    cache = Path.home() / "Library" / "Caches" / "ms-playwright"
    for app in sorted(cache.glob("chromium-*/chrome-mac*/Chromium.app"), reverse=True):
        binario = app / "Contents" / "MacOS" / "Chromium"
        if binario.exists():
            return str(binario)
    for app in sorted(
        cache.glob("chromium-*/chrome-mac*/Google Chrome for Testing.app"), reverse=True
    ):
        binario = app / "Contents" / "MacOS" / "Google Chrome for Testing"
        if binario.exists():
            return str(binario)
    return None


class Toma:
    """Contexto de navegador que graba un clip y anota marcas de tiempo."""

    def __init__(self, navegador, nombre: str, salida: Path, con_sesion: bool, zoom: bool = True):
        self.nombre = nombre
        self.salida = salida
        self.dir_tmp = salida / f".tmp-{nombre}"
        shutil.rmtree(self.dir_tmp, ignore_errors=True)
        opciones = {
            "viewport": VIEWPORT,
            "record_video_dir": str(self.dir_tmp),
            "record_video_size": VIDEO,
            "locale": "es-CL",
            "color_scheme": "light",
            "reduced_motion": "no-preference",
        }
        if con_sesion:
            opciones["storage_state"] = str(SESION)
        self.ctx: BrowserContext = navegador.new_context(**opciones)
        self.ctx.add_init_script(CURSOR_JS)
        if zoom:
            self.ctx.add_init_script(ZOOM_JS % ZOOM)
        self.page: Page = self.ctx.new_page()
        self.t0 = time.monotonic()
        self.marcas: list[tuple[float, str]] = []
        self.x, self.y = VIEWPORT["width"] / 2, VIEWPORT["height"] / 2

    def marca(self, texto: str) -> None:
        self.marcas.append((round(time.monotonic() - self.t0, 2), texto))
        print(f"  [{self.nombre} {self.marcas[-1][0]:6.1f}s] {texto}")

    def pausa(self, segundos: float) -> None:
        self.page.wait_for_timeout(int(segundos * 1000))

    def mover(self, selector_o_locator, *, pasos: int = 28) -> None:
        loc = (
            self.page.locator(selector_o_locator)
            if isinstance(selector_o_locator, str)
            else selector_o_locator
        )
        if not loc.count():
            self.marca(f"AVISO: no aparece {selector_o_locator}; se omite")
            return
        loc.first.scroll_into_view_if_needed()
        caja = loc.first.bounding_box()
        if not caja:
            return
        x, y = caja["x"] + caja["width"] / 2, caja["y"] + caja["height"] / 2
        self.page.mouse.move(x, y, steps=pasos)
        self.x, self.y = x, y

    def clic(self, selector_o_locator, *, espera: float = 0.35) -> None:
        loc = (
            self.page.locator(selector_o_locator)
            if isinstance(selector_o_locator, str)
            else selector_o_locator
        )
        if not loc.count():
            raise RuntimeError(f"No aparece el elemento para hacer clic: {selector_o_locator}")
        self.mover(selector_o_locator)
        self.pausa(espera)
        self.page.mouse.down()
        self.page.mouse.up()

    def desplazar(self, dy: float, *, duracion: float = 1.6) -> None:
        """Desplazamiento suave de la ventana, en píxeles CSS."""
        self.page.evaluate(
            """([dy, ms]) => new Promise(ok => {
                const y0 = scrollY, t0 = performance.now();
                const paso = t => {
                  const k = Math.min(1, (t - t0) / ms), e = k < .5 ? 2*k*k : 1 - (-2*k + 2)**2 / 2;
                  scrollTo(0, y0 + dy * e);
                  k < 1 ? requestAnimationFrame(paso) : ok();
                };
                requestAnimationFrame(paso);
            })""",
            [dy, int(duracion * 1000)],
        )

    def desplazar_a(self, selector: str, *, margen: float = 120, duracion: float = 1.6) -> None:
        loc = self.page.locator(selector).first
        if not loc.count():
            self.marca(f"AVISO: no aparece {selector}; se omite el desplazamiento")
            return
        y = loc.evaluate("e => e.getBoundingClientRect().top")
        self.desplazar(y - margen, duracion=duracion)

    def cerrar(self) -> Path:
        video = self.page.video
        self.ctx.close()
        destino = self.salida / f"{self.nombre}.webm"
        if video:
            Path(video.path()).replace(destino)
        shutil.rmtree(self.dir_tmp, ignore_errors=True)
        (self.salida / f"{self.nombre}.marcas.json").write_text(
            json.dumps(self.marcas, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"  → {destino}")
        return destino


# --- Tomas -------------------------------------------------------------------


def toma_landing(t: Toma, base: str, estado: dict) -> None:
    t.page.goto(f"{base}/entrar", wait_until="networkidle")
    t.marca("landing visible")
    t.pausa(4)
    t.desplazar_a(".landing-cifras", margen=260, duracion=3.5)
    t.marca("cifras en pantalla")
    t.pausa(6)
    t.desplazar_a(".landing-fuente", margen=420, duracion=2)
    t.marca("fuente visible")
    t.pausa(5)


def toma_entrar(t: Toma, base: str, estado: dict) -> None:
    t.page.goto(f"{base}/", wait_until="networkidle")
    if "/entrar" in t.page.url:
        sys.exit("La sesión guardada expiró. Ejecuta de nuevo el paso `sesion`.")
    t.marca("bandeja con guía")
    t.pausa(3.5)
    boton = t.page.locator("#guia button")
    if boton.is_visible():
        t.clic(boton)
        t.marca("guía cerrada")
    t.pausa(1.5)
    t.mover(".tarjetas .tarjeta-caso", pasos=40)
    t.pausa(3)


def toma_ingreso(t: Toma, base: str, estado: dict) -> None:
    t.page.goto(f"{base}/", wait_until="networkidle")
    cerrar_guia(t)
    t.pausa(1)
    t.clic("a[href='/ingresos/nuevo']")
    t.page.wait_for_url("**/ingresos/nuevo")
    t.marca("formulario")
    t.pausa(1.2)
    t.clic("input[name=tipo_ingreso][value=DIRECTA] + span")
    t.clic("input[name=empleador]")
    t.page.keyboard.type(EMPLEADOR, delay=45)
    t.clic("input[name=sector_empleador][value=PRIVADO] + span")
    t.clic("#relato-ingreso")
    # Se pega el relato de una vez, como lo haría la persona desde un editor.
    # Cada intento cambia el mes: un relato idéntico activaría RD-04 (duplicado)
    # y el caso no pasaría por la IA.
    intento = estado.get("ingresos", 0)
    estado["ingresos"] = intento + 1
    t.page.locator("#relato-ingreso").fill(RELATO.format(mes=MESES[intento % len(MESES)]))
    t.page.locator("#relato-ingreso").dispatch_event("input")
    t.marca("relato pegado")
    t.pausa(2.5)
    t.clic("input[name=confirmar_sintetico]")
    t.pausa(0.8)
    t.clic(".formulario-ingreso .acciones button")
    t.page.wait_for_url(re.compile(r".*/ingresos/seguimiento/.*"), timeout=60_000)
    estado["folio"] = t.page.url.rsplit("/", 1)[-1]
    t.marca(f"procesando · folio {estado['folio']}")
    t.page.wait_for_url(re.compile(r".*/casos/[^/?]+.*"), timeout=240_000)
    t.page.wait_for_load_state("networkidle")
    estado["caso_nuevo"] = t.page.url.split("/casos/")[1].split("?")[0].split("/")[0]
    t.marca(f"propuesta lista · caso {estado['caso_nuevo']}")
    t.pausa(3)
    t.mover("#titulo-caso")
    t.pausa(2.5)
    t.desplazar_a("#relato", margen=140)
    t.marca("relato con citas")
    marcada = t.page.locator("#relato mark").first
    if marcada.count():
        t.mover(marcada)
    t.pausa(4)
    t.desplazar_a(".citas", margen=140)
    t.marca("lista de citas")
    t.pausa(4)
    t.desplazar_a("#titulo-recorrido", margen=140)
    t.marca("recorrido")
    t.pausa(4)


def toma_sint0002(t: Toma, base: str, estado: dict) -> None:
    t.page.goto(f"{base}/", wait_until="networkidle")
    cerrar_guia(t)
    tarjeta = t.page.locator(
        ".tarjeta-caso", has=t.page.locator(".tarjeta-id", has_text="SINT-0002")
    ).first
    if not tarjeta.count():
        sys.exit("No hay SINT-0002 en la bandeja «Por revisar». Ejecuta `preparar`.")
    t.pausa(1.5)
    t.clic(tarjeta)
    t.page.wait_for_selector("#panel-caso")
    t.page.wait_for_load_state("networkidle")
    estado["sint0002_corregido"] = t.page.locator(".correccion").count() > 0
    t.marca(
        "SINT-0002 abierto"
        + (" · RD-10 corrigió al modelo" if estado["sint0002_corregido"] else "")
    )
    t.pausa(2)
    if estado["sint0002_corregido"]:
        t.mover(".correccion")
        t.pausa(4)
    t.desplazar_a("#relato", margen=140)
    frase = (
        t.page.locator("#relato")
        .get_by_text(re.compile(r"acuerdo|conversar|mediaci", re.IGNORECASE))
        .first
    )
    if frase.count():
        t.mover(frase)
    t.marca("frase de la mediación")
    t.pausa(5)
    t.desplazar_a("#titulo-recorrido", margen=140)
    t.marca("recorrido")
    t.pausa(5)


def toma_decidir(t: Toma, base: str, estado: dict) -> None:
    caso = estado.get("caso_nuevo")
    if not caso:
        sys.exit("Falta el caso nuevo: graba antes la toma `ingreso`.")
    t.page.goto(f"{base}/casos/{caso}?bandeja=por-revisar", wait_until="networkidle")
    cerrar_guia(t)
    t.pausa(1.5)
    t.desplazar_a("#decision", margen=200)
    t.pausa(1.5)
    t.mover("#accion-descartar")
    t.marca("muestra descartar")
    t.pausa(2)
    t.clic("#accion-confirmar")
    t.marca("confirmado")
    t.page.wait_for_load_state("networkidle")
    t.pausa(3.5)
    tarjeta = t.page.locator(
        ".tarjeta-caso", has=t.page.locator(".tarjeta-id", has_text="SINT-0004")
    ).first
    if tarjeta.count():
        t.mover(
            tarjeta.locator(".chip-neutro").first
            if tarjeta.locator(".chip-neutro").count()
            else tarjeta
        )
        t.marca("SINT-0004 sin IA")
    t.pausa(5)


def toma_github(t: Toma, base: str, estado: dict) -> None:
    t.page.goto(REPO, wait_until="networkidle")
    t.marca("README")
    t.pausa(2)
    t.desplazar_a(
        "h3:has-text('El flujo de un caso'), h3 >> text=El flujo de un caso",
        margen=80,
        duracion=2.5,
    )
    t.marca("diagrama")
    t.pausa(7)
    t.desplazar_a("h4:has-text('Mejora medida de los prompts')", margen=80, duracion=2.5)
    t.marca("tabla de mejora")
    t.pausa(8)


def toma_cierre(t: Toma, base: str, estado: dict) -> None:
    t.page.goto((RAIZ / "cierre.html").as_uri(), wait_until="networkidle")
    t.marca("cierre")
    t.pausa(10)


TOMAS = {
    "landing": (toma_landing, False),
    "entrar": (toma_entrar, True),
    "ingreso": (toma_ingreso, True),
    "sint0002": (toma_sint0002, True),
    "decidir": (toma_decidir, True),
    "github": (toma_github, False),
    "cierre": (toma_cierre, False),
}
SIN_ZOOM = {"cierre"}


def cerrar_guia(t: Toma) -> None:
    boton = t.page.locator("#guia button")
    if boton.count() and boton.is_visible():
        boton.click()


# --- Comandos ------------------------------------------------------------------


def lanzar(p, *, visible: bool):
    return p.chromium.launch(headless=not visible, executable_path=chromium_local())


def cmd_sesion(base: str) -> None:
    SESION.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        nav = lanzar(p, visible=True)
        ctx = nav.new_context(viewport=VIEWPORT, locale="es-CL")
        page = ctx.new_page()
        page.goto(f"{base}/entrar")
        print("Inicia sesión como inspector_demo en la ventana abierta (tienes 5 minutos).")
        page.wait_for_url(
            lambda url: not url.rstrip("/").endswith("/entrar") and "/entrar?" not in url,
            timeout=300_000,
        )
        ctx.storage_state(path=str(SESION))
        os.chmod(SESION, 0o600)
        nav.close()
    print(f"Sesión guardada en {SESION}")


def cmd_preparar(base: str) -> None:
    with sync_playwright() as p:
        nav = lanzar(p, visible=False)
        ctx = nav.new_context(viewport=VIEWPORT, storage_state=str(SESION), locale="es-CL")
        page = ctx.new_page()
        page.goto(f"{base}/", wait_until="networkidle")
        if "/entrar" in page.url:
            sys.exit("La sesión guardada expiró. Ejecuta de nuevo el paso `sesion`.")
        cerrar_guia_page(page)
        page.locator("details.mas-acciones summary").click()
        page.locator("form[action='/demo/nueva-tanda'] button").click()
        page.wait_for_load_state("networkidle")
        print("Tanda nueva solicitada. Esperando el procesamiento…")
        limite = time.monotonic() + 600
        while time.monotonic() < limite:
            page.wait_for_timeout(8000)
            page.goto(f"{base}/", wait_until="networkidle")
            estado = (
                page.locator(".estado-carga").inner_text()
                if page.locator(".estado-carga").count()
                else ""
            )
            print(
                "  ", estado.strip().splitlines()[0] if estado.strip() else "(sin estado de carga)"
            )
            if "Carga terminada" in estado:
                break
        ids = page.locator(".tarjeta-id").all_inner_texts()
        print(f"Casos en «Por revisar»: {len(ids)}")
        for i in ids:
            print("   ", i)
        nav.close()


def cerrar_guia_page(page: Page) -> None:
    boton = page.locator("#guia button")
    if boton.count() and boton.is_visible():
        boton.click()


def cmd_grabar(base: str, salida: Path, nombres: list[str]) -> None:
    salida.mkdir(parents=True, exist_ok=True)
    archivo_estado = salida / "estado.json"
    estado = json.loads(archivo_estado.read_text()) if archivo_estado.exists() else {}
    if any(TOMAS[n][1] for n in nombres) and not SESION.exists():
        sys.exit("No hay sesión guardada. Ejecuta primero el paso `sesion`.")
    with sync_playwright() as p:
        nav = lanzar(p, visible=False)
        for nombre in nombres:
            funcion, con_sesion = TOMAS[nombre]
            print(f"Toma «{nombre}»")
            t = Toma(nav, nombre, salida, con_sesion, zoom=nombre not in SIN_ZOOM)
            try:
                funcion(t, base, estado)
            finally:
                t.cerrar()
                archivo_estado.write_text(json.dumps(estado, indent=1), encoding="utf-8")
        nav.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("comando", choices=["sesion", "preparar", "grabar"])
    parser.add_argument("tomas", nargs="*", help=f"Tomas a grabar: {', '.join(TOMAS)}")
    parser.add_argument("--base", default=BASE_PUBLICA)
    parser.add_argument("--salida", type=Path, default=RAIZ / "salida")
    args = parser.parse_args()
    base = args.base.rstrip("/")
    if args.comando == "sesion":
        cmd_sesion(base)
    elif args.comando == "preparar":
        cmd_preparar(base)
    else:
        desconocidas = [n for n in args.tomas if n not in TOMAS]
        if desconocidas:
            sys.exit(f"Tomas desconocidas: {desconocidas}")
        cmd_grabar(base, args.salida, args.tomas or list(TOMAS))


if __name__ == "__main__":
    main()
