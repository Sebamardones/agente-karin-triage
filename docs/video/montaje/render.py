"""Renderiza escenas.html cuadro a cuadro y produce el video.

    uv run --with playwright python docs/video/montaje/render.py montaje.json salida.mp4
    uv run --with playwright python docs/video/montaje/render.py montaje.json --cuadros 3,20.5,60

Con --cuadros guarda solo esos instantes como PNG, para revisar el diseño.
El audio se agrega después, en el paso de mezcla.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

AQUI = Path(__file__).resolve().parent


def chromium() -> str | None:
    rutas = sorted(
        glob.glob(
            os.path.expanduser(
                "~/Library/Caches/ms-playwright/chromium-*/chrome-mac*/*.app/Contents/MacOS/*"
            )
        )
    )
    return rutas[-1] if rutas else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("salida", type=Path, nargs="?")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--cuadros", help="Instantes en segundos, separados por coma")
    ap.add_argument("--desde", type=float, default=0)
    ap.add_argument("--hasta", type=float)
    args = ap.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    total = config["total"]
    with sync_playwright() as p:
        nav = p.chromium.launch(
            executable_path=chromium(), args=["--autoplay-policy=no-user-gesture-required"]
        )
        pagina = nav.new_page(viewport={"width": 1920, "height": 1080})
        pagina.add_init_script(f"window.MONTAJE = {json.dumps(config)};")
        pagina.goto((AQUI / "escenas.html").as_uri(), wait_until="networkidle")
        pagina.evaluate("window.__listo")
        errores: list[str] = []
        pagina.on("pageerror", lambda e: errores.append(str(e)))

        if args.cuadros:
            destino = args.salida or AQUI.parent / "salida" / "cuadros"
            destino.mkdir(parents=True, exist_ok=True)
            for t in [float(x) for x in args.cuadros.split(",")]:
                pagina.evaluate(f"window.__ir({t})")
                ruta = destino / f"cuadro-{t:07.2f}.png"
                pagina.screenshot(path=str(ruta))
                print(ruta)
        else:
            hasta = args.hasta or total
            n0, n1 = int(args.desde * args.fps), int(hasta * args.fps)
            ffmpeg = subprocess.Popen(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-y",
                    "-f",
                    "image2pipe",
                    "-framerate",
                    str(args.fps),
                    "-i",
                    "-",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "slow",
                    "-crf",
                    "16",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    str(args.salida),
                ],
                stdin=subprocess.PIPE,
            )
            t_inicio = time.monotonic()
            for n in range(n0, n1):
                pagina.evaluate(f"window.__ir({n / args.fps})")
                ffmpeg.stdin.write(pagina.screenshot(type="jpeg", quality=94))
                if n % (args.fps * 5) == 0:
                    hecho = (n - n0) / max(1, n1 - n0)
                    print(
                        f"  {n / args.fps:6.1f}s  {hecho:5.1%}  {time.monotonic() - t_inicio:5.0f}s transcurridos",
                        flush=True,
                    )
            ffmpeg.stdin.close()
            ffmpeg.wait()
            print(args.salida)
        if errores:
            print("Errores de la página:", *errores, sep="\n  ", file=sys.stderr)
        nav.close()


if __name__ == "__main__":
    main()
