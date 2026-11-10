"""Arma montaje.json (tiempos, tramos de las tomas y zooms) a partir de la
narración real, y mezcla el audio: voz, música y efectos de sonido.

    uv run --no-project python docs/video/montaje/construir.py
    uv run --no-project --with numpy python docs/video/montaje/construir.py --audio

Lee docs/video/salida/voz/*.mp3 y *.alin.json (ElevenLabs, con marcas por
carácter), las tomas en docs/video/salida/intra/, los efectos en
docs/video/salida/sfx/ y la lista de efectos que escribe render.py
(docs/video/salida/sfx-eventos.json).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI.parent / "salida"
VOZ = SALIDA / "voz"
MUSICA = SALIDA / "musica-electronica.mp3"
DROP_MUSICA = 27.47  # segundo del primer drop de la música (medido con earshot)

ORDEN = ["e1", "e1b", "e2", "e3", "e4", "e5", "e6", "e6b", "e7"]
ENTRADA = 0.5  # silencio antes de la voz en cada escena
COLA = {
    "e1": 0.6,
    "e1b": 0.9,
    "e2": 0.6,
    "e3": 0.7,
    "e4": 0.7,
    "e5": 0.9,
    "e6": 0.8,
    "e6b": 1.0,
    "e7": 2.4,
}
GANANCIA_SFX = {
    "whoosh": 0.55, "swoosh": 0.45, "pop": 0.5, "impacto": 0.8, "click": 0.6, "riser": 0.45,
    "ding": 0.45, "glitch": 0.45, "tick": 0.35, "teclas": 0.5, "succion": 0.55,
}  # fmt: skip
SR = 48000
NIVEL_EFECTOS = 0.22  # el bus de efectos medía 13 dB sobre la voz


def alineacion(k: str):
    a = json.loads((VOZ / f"{k}.alin.json").read_text())
    return (
        "".join(a["characters"]),
        a["character_start_times_seconds"],
        a["character_end_times_seconds"],
    )


def construir() -> dict:
    escenas, t, voz = [], 0.0, {}
    for k in ORDEN:
        texto, ini, fin = alineacion(k)
        d = ENTRADA + fin[-1] + COLA[k]
        escenas.append({"id": k, "inicio": round(t, 3), "dur": round(d, 3)})
        voz[k] = {"texto": texto, "ini": [round(x, 3) for x in ini], "t0": round(t + ENTRADA, 3)}
        t += d
    total = round(t, 3)
    T = {e["id"]: e for e in escenas}
    fin_de = lambda k: T[k]["inicio"] + T[k]["dur"]
    rel = lambda k, x: round(x - T[k]["inicio"], 3)

    def en(k: str, frase: str) -> float:
        """Instante absoluto en que la voz empieza a decir `frase` en la escena k."""
        v = voz[k]
        i = v["texto"].lower().find(frase.lower())
        if i < 0:
            raise KeyError(f"{k}: no aparece «{frase}»")
        return round(v["t0"] + v["ini"][i], 3)

    tramos = {
        # [t0, t1, c0, c1]: instante del montaje → segundo de la toma
        "ingreso": [
            [T["e3"]["inicio"], en("e3", "Karin Triage"), 2.6, 9.9],
            [en("e3", "Karin Triage"), en("e3", "aplica"), 9.9, 15.6],
            [en("e3", "aplica"), en("e3", "En segundos"), 15.6, 20.0],
            [en("e3", "En segundos"), en("e3", "Cada afirmación"), 28.9, 33.4],
            [en("e3", "Cada afirmación"), en("e3", "verificada"), 36.6, 40.6],
            [en("e3", "verificada"), en("e3", "Y como hubo"), 42.6, 46.0],
            [en("e3", "Y como hubo"), fin_de("e3"), 30.2, 33.0],
        ],
        "sint0002": [
            [T["e4"]["inicio"], en("e4", "y la persona"), 3.2, 7.4],
            [en("e4", "y la persona"), en("e4", "Pero la ley"), 8.2, 12.0],
            [en("e4", "Pero la ley"), en("e4", "El agente"), 12.0, 14.6],
            [en("e4", "El agente"), en("e4", "Y si se"), 4.6, 6.8],
            [en("e4", "Y si se"), fin_de("e4"), 15.0, 20.5],
        ],
        "decidir": [
            [T["e5"]["inicio"], en("e5", "Un descarte"), 2.4, 9.6],
            [en("e5", "Un descarte"), en("e5", "Y lo que"), 9.6, 12.4],
            [en("e5", "Y lo que"), fin_de("e5"), 12.4, 18.4],
        ],
    }

    def inversa(clip: str, ct: float) -> float:
        """Instante del montaje en que se ve el segundo `ct` de la toma (primer tramo que lo contiene)."""
        for t0, t1, c0, c1 in tramos[clip]:
            if min(c0, c1) <= ct <= max(c0, c1):
                return round(t0 + (ct - c0) * (t1 - t0) / (c1 - c0), 3)
        raise ValueError(f"{clip}: el segundo {ct} no aparece en el montaje")

    # Sonidos de lo que ocurre dentro de las tomas grabadas.
    sfx_extra = {
        "e3": [
            {"tipo": "teclas", "t": inversa("ingreso", 4.8), "vol": 0.6},
            {"tipo": "click", "t": inversa("ingreso", 12.9), "vol": 0.7},
            {"tipo": "click", "t": inversa("ingreso", 14.4), "vol": 0.8},
        ],
        "e5": [
            {"tipo": "click", "t": inversa("decidir", 9.2), "vol": 0.8},
            {"tipo": "ding", "t": inversa("decidir", 9.5), "vol": 0.6},
        ],
    }

    # Zooms: t relativo a la escena; x, y = punto de foco en la toma (0..1).
    z = lambda t, escala, x, y, dur=1.0: {
        "t": round(t, 3),
        "escala": escala,
        "x": x,
        "y": y,
        "dur": dur,
    }
    zooms = {
        "ingreso": [
            z(0, 1.35, 0.38, 0.42),
            z(rel("e3", en("e3", "Karin Triage")) - 0.3, 1.6, 0.38, 0.62, 1.4),
            z(rel("e3", en("e3", "aplica")) - 0.2, 1.25, 0.5, 0.45),
            z(rel("e3", en("e3", "En segundos")) - 0.1, 2.1, 0.45, 0.39),
            z(rel("e3", en("e3", "Cada afirmación")) - 0.1, 2.0, 0.5, 0.28),
            z(rel("e3", en("e3", "verificada")) - 0.1, 1.9, 0.5, 0.33),
            z(rel("e3", en("e3", "Y como hubo")) - 0.1, 2.6, 0.4, 0.43),
        ],
        "sint0002": [
            z(0, 1.3, 0.5, 0.4),
            z(rel("e4", en("e4", "acoso sexual")) - 0.3, 2.2, 0.5, 0.24),
            z(rel("e4", en("e4", "y la persona")) - 0.1, 2.2, 0.48, 0.35),
            z(rel("e4", en("e4", "Pero la ley")), 1.5, 0.48, 0.4, 2.0),
            z(rel("e4", en("e4", "El agente")) - 0.1, 2.2, 0.5, 0.24, 0.9),
            z(rel("e4", en("e4", "Y si se")) - 0.1, 2.0, 0.7, 0.55, 1.1),
            z(rel("e4", en("e4", "Lo que no")), 1.4, 0.6, 0.5, 1.6),
        ],
        "decidir": [
            z(0, 1.4, 0.5, 0.5),
            z(1.0, 2.2, 0.45, 0.52, 1.2),
            z(rel("e5", en("e5", "Un descarte")) - 0.1, 2.4, 0.8, 0.9),
            z(rel("e5", en("e5", "Y lo que")) - 0.1, 1.3, 0.4, 0.5),
            z(rel("e5", en("e5", "como la denuncia")) + 0.6, 2.5, 0.17, 0.62, 1.2),
        ],
    }
    clips = {
        nombre: {"src": (SALIDA / "intra" / f"{nombre}.webm").as_uri(), "tramos": tr}
        for nombre, tr in tramos.items()
    }
    return {
        "total": total,
        "escenas": escenas,
        "clips": clips,
        "zooms": zooms,
        "sfx_extra": sfx_extra,
        "vozdet": voz,
        "voz": {k: v["t0"] for k, v in voz.items()},
        "drop": en("e1b", "NO es"),
    }


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def bus_efectos(config: dict) -> Path:
    """Suma cada efecto en su instante, con su ganancia, en una pista estéreo."""
    import numpy as np

    eventos = json.loads((SALIDA / "sfx-eventos.json").read_text())
    largo = int(config["total"] * SR) + SR
    bus = np.zeros((largo, 2), dtype=np.float32)
    cache: dict[str, np.ndarray] = {}
    for ev in eventos:
        tipo = ev["tipo"]
        if tipo not in cache:
            crudo = subprocess.run(
                ["ffmpeg", "-v", "error", "-i", str(SALIDA / "sfx" / f"{tipo}.mp3"), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                check=True, capture_output=True,
            ).stdout  # fmt: skip
            cache[tipo] = np.frombuffer(crudo, dtype=np.float32).reshape(-1, 2)
        s = cache[tipo] * GANANCIA_SFX.get(tipo, 0.5) * ev.get("vol", 1)
        i = int(ev["t"] * SR)
        if i >= largo:
            continue
        n = min(len(s), largo - i)
        bus[i : i + n] += s[:n] * NIVEL_EFECTOS
    ruta = SALIDA / "efectos.wav"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", "-c:a", "pcm_s24le", str(ruta)],
        input=np.clip(bus, -1, 1).tobytes(), check=True,
    )  # fmt: skip
    print(f"efectos: {len(eventos)} eventos")
    return ruta


def mezclar(config: dict) -> Path:
    """Voz en su lugar, música electrónica atenuada bajo la voz y efectos."""
    total = config["total"]
    entradas, filtros, etiquetas = [], [], []
    for i, k in enumerate(ORDEN):
        entradas += ["-i", str(VOZ / f"{k}.mp3")]
        ms = int(config["voz"][k] * 1000)
        filtros.append(
            f"[{i}:a]aresample={SR},aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{i}]"
        )
        etiquetas.append(f"[v{i}]")
    filtros.append(
        f"{''.join(etiquetas)}amix=inputs={len(ORDEN)}:normalize=0,apad,atrim=0:{total},volume=1.0[voz]"
    )
    n = len(ORDEN)
    # La música se corre para que su primer drop caiga en «NO es neutro».
    corrimiento = config["drop"] - DROP_MUSICA
    entradas += ["-i", str(MUSICA)]
    if corrimiento >= 0:
        ms = int(corrimiento * 1000)
        base = f"[{n}:a]aresample={SR},aformat=channel_layouts=stereo,adelay={ms}|{ms}"
    else:
        base = f"[{n}:a]aresample={SR},aformat=channel_layouts=stereo,atrim=start={-corrimiento},asetpts=PTS-STARTPTS"
    filtros.append(
        f"{base},apad,atrim=0:{total},volume=0.065,afade=t=out:st={total - 2.5}:d=2.5[mus]"
    )
    entradas += ["-i", str(bus_efectos(config))]
    filtros.append(f"[{n + 1}:a]aresample={SR},apad,atrim=0:{total}[sfx]")
    filtros.append("[voz]asplit=2[voz1][voz2]")
    filtros.append(
        "[mus][voz2]sidechaincompress=threshold=0.015:ratio=8:attack=10:release=400[musd]"
    )
    filtros.append("[voz1][musd][sfx]amix=inputs=3:normalize=0[out]")
    cruda = SALIDA / "mezcla-cruda.wav"
    ffmpeg(
        *entradas,
        "-filter_complex",
        ";".join(filtros),
        "-map",
        "[out]",
        "-ar",
        str(SR),
        "-c:a",
        "pcm_s24le",
        str(cruda),
    )
    # Normalización en dos pasadas, lineal: no comprime ni sube la música en las pausas.
    objetivo = "I=-15:TP=-1.5:LRA=11"
    medida = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(cruda), "-af", f"loudnorm={objetivo}:print_format=json", "-f", "null", "-"],
        check=True, capture_output=True, text=True,
    ).stderr  # fmt: skip
    m = json.loads(medida[medida.rindex("{") : medida.rindex("}") + 1])
    lineal = (
        f"loudnorm={objetivo}:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
        f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}"
    )
    salida = SALIDA / "mezcla.wav"
    ffmpeg(
        "-i",
        str(cruda),
        "-af",
        f"{lineal},alimiter=limit=0.84:level=false",
        "-ar",
        str(SR),
        str(salida),
    )
    return salida


if __name__ == "__main__":
    config = construir()
    (SALIDA / "montaje.json").write_text(json.dumps(config, ensure_ascii=False, indent=1))
    print(f"montaje.json · total {config['total']:.1f}s")
    for e in config["escenas"]:
        print(f"  {e['id']:4s} {e['inicio']:6.1f}s + {e['dur']:5.1f}s")
    if "--audio" in sys.argv:
        print(mezclar(config))
