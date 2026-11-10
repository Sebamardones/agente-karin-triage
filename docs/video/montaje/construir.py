"""Arma montaje.json (tiempos, tramos de las tomas, zooms y globos) a partir de
las duraciones reales de la narración, y mezcla el audio.

    uv run --no-project python docs/video/montaje/construir.py

Lee docs/video/salida/voz/*.mp3 y *.alin.json (generados con ElevenLabs) y las
tomas convertidas a intra en docs/video/salida/intra/.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI.parent / "salida"
VOZ = SALIDA / "voz"

ORDEN = ["e1", "e1b", "e2", "e3", "e4", "e5", "e6", "e6b", "e7"]
ENTRADA = 0.6  # silencio antes de la voz en cada escena
COLA = {
    "e1": 0.9,
    "e1b": 1.0,
    "e2": 0.9,
    "e3": 1.0,
    "e4": 1.0,
    "e5": 1.0,
    "e6": 1.2,
    "e6b": 1.2,
    "e7": 2.6,
}


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
        voz[k] = {"texto": texto, "ini": ini, "t0": t + ENTRADA}
        t += d
    total = round(t, 3)

    def en(k: str, frase: str) -> float:
        """Instante absoluto en que la voz empieza a decir `frase` en la escena k."""
        v = voz[k]
        i = v["texto"].find(frase)
        if i < 0:
            raise KeyError(f"{k}: no aparece «{frase}»")
        return round(v["t0"] + v["ini"][i], 3)

    T = {e["id"]: e for e in escenas}
    rel = lambda k, x: round(x - T[k]["inicio"], 3)

    clips = {
        # [t0, t1, c0, c1]: instante del montaje → segundo de la toma
        "ingreso": [
            [T["e3"]["inicio"], en("e3", "Karin Triage"), 2.6, 9.9],
            [en("e3", "Karin Triage"), en("e3", "aplica"), 9.9, 15.6],
            [en("e3", "aplica"), en("e3", "En segundos"), 15.6, 20.0],
            [en("e3", "En segundos"), en("e3", "Cada afirmación"), 28.9, 33.4],
            [en("e3", "Cada afirmación"), en("e3", "verificada"), 36.6, 40.6],
            [en("e3", "verificada"), en("e3", "Y como hubo"), 42.6, 46.0],
            [en("e3", "Y como hubo"), T["e3"]["inicio"] + T["e3"]["dur"], 30.2, 33.0],
        ],
        "sint0002": [
            [T["e4"]["inicio"], en("e4", "y la persona"), 3.2, 7.4],
            [en("e4", "y la persona"), en("e4", "Pero la ley"), 8.2, 12.0],
            [en("e4", "Pero la ley"), en("e4", "El agente"), 12.0, 14.6],
            [en("e4", "El agente"), en("e4", "Y si se"), 4.6, 6.8],
            [en("e4", "Y si se"), T["e4"]["inicio"] + T["e4"]["dur"], 15.0, 20.5],
        ],
        "decidir": [
            [T["e5"]["inicio"], en("e5", "Un descarte"), 2.4, 9.6],
            [en("e5", "Un descarte"), en("e5", "Y lo que"), 9.6, 12.4],
            [en("e5", "Y lo que"), T["e5"]["inicio"] + T["e5"]["dur"], 12.4, 18.4],
        ],
    }
    clips = {
        nombre: {"src": (SALIDA / "intra" / f"{nombre}.webm").as_uri(), "tramos": tramos}
        for nombre, tramos in clips.items()
    }

    # Zooms: t relativo a la escena; x, y = punto de foco en la toma (0..1).
    zooms = {
        "ingreso": [
            {"t": 0, "escala": 1.35, "x": 0.38, "y": 0.42},
            {
                "t": rel("e3", en("e3", "Karin Triage")) - 0.3,
                "escala": 1.6,
                "x": 0.38,
                "y": 0.62,
                "dur": 1.4,
            },
            {
                "t": rel("e3", en("e3", "aplica")) - 0.2,
                "escala": 1.25,
                "x": 0.5,
                "y": 0.45,
                "dur": 1.0,
            },
            {
                "t": rel("e3", en("e3", "En segundos")) - 0.1,
                "escala": 2.1,
                "x": 0.45,
                "y": 0.39,
                "dur": 1.0,
            },
            {
                "t": rel("e3", en("e3", "Cada afirmación")) - 0.1,
                "escala": 2.0,
                "x": 0.5,
                "y": 0.28,
                "dur": 1.0,
            },
            {
                "t": rel("e3", en("e3", "verificada")) - 0.1,
                "escala": 1.9,
                "x": 0.5,
                "y": 0.33,
                "dur": 1.0,
            },
            {
                "t": rel("e3", en("e3", "Y como hubo")) - 0.1,
                "escala": 2.6,
                "x": 0.4,
                "y": 0.43,
                "dur": 1.0,
            },
        ],
        "sint0002": [
            {"t": 0, "escala": 1.3, "x": 0.5, "y": 0.4},
            {
                "t": rel("e4", en("e4", "acoso sexual")) - 0.3,
                "escala": 2.2,
                "x": 0.5,
                "y": 0.24,
                "dur": 1.0,
            },
            {
                "t": rel("e4", en("e4", "y la persona")) - 0.1,
                "escala": 2.2,
                "x": 0.48,
                "y": 0.35,
                "dur": 1.0,
            },
            {
                "t": rel("e4", en("e4", "Pero la ley")),
                "escala": 1.5,
                "x": 0.48,
                "y": 0.4,
                "dur": 2.0,
            },
            {
                "t": rel("e4", en("e4", "El agente")) - 0.1,
                "escala": 2.2,
                "x": 0.5,
                "y": 0.24,
                "dur": 0.9,
            },
            {
                "t": rel("e4", en("e4", "Y si se")) - 0.1,
                "escala": 2.0,
                "x": 0.7,
                "y": 0.55,
                "dur": 1.1,
            },
            {"t": rel("e4", en("e4", "Lo que no")), "escala": 1.4, "x": 0.6, "y": 0.5, "dur": 1.6},
        ],
        "decidir": [
            {"t": 0, "escala": 1.4, "x": 0.5, "y": 0.5},
            {"t": 1.0, "escala": 2.2, "x": 0.45, "y": 0.52, "dur": 1.2},
            {
                "t": rel("e5", en("e5", "Un descarte")) - 0.1,
                "escala": 2.4,
                "x": 0.8,
                "y": 0.9,
                "dur": 1.0,
            },
            {
                "t": rel("e5", en("e5", "Y lo que")) - 0.1,
                "escala": 1.3,
                "x": 0.4,
                "y": 0.5,
                "dur": 1.0,
            },
            {
                "t": rel("e5", en("e5", "como la denuncia")) + 0.6,
                "escala": 2.5,
                "x": 0.17,
                "y": 0.62,
                "dur": 1.2,
            },
        ],
    }
    fin = lambda k: T[k]["inicio"] + T[k]["dur"] - 0.5
    globos = {
        "#g-citas": {"t": en("e3", "Cada afirmación") + 0.4, "salida": en("e3", "Y como hubo")},
        "#g-urgencia": {"t": en("e3", "urgencia") - 0.2, "salida": fin("e3")},
        "#g-rd10": {"t": en("e4", "una regla escrita"), "salida": fin("e4")},
        "#g-cero": {"t": en("e5", "Costo cero") - 0.6, "salida": fin("e5")},
    }
    marcas = {
        "e1_mes": (en("e1", "Más de cuatro") - T["e1"]["inicio"]) / T["e1"]["dur"],
        "e1_mano": (en("e1", "a mano") - T["e1"]["inicio"]) / T["e1"]["dur"],
        "e1_plazos": (en("e1", "dos días") - T["e1"]["inicio"]) / T["e1"]["dur"],
    }
    return {
        "total": total,
        "escenas": escenas,
        "clips": clips,
        "zooms": zooms,
        "globos": globos,
        "marcas": marcas,
        "voz": {k: round(v["t0"], 3) for k, v in voz.items()},
    }


def mezclar(config: dict, musica: Path | None) -> Path:
    """Narración en su lugar + música de fondo con ducking bajo la voz."""
    entradas, filtros, etiquetas = [], [], []
    for i, k in enumerate(ORDEN):
        entradas += ["-i", str(VOZ / f"{k}.mp3")]
        ms = int(config["voz"][k] * 1000)
        filtros.append(
            f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{i}]"
        )
        etiquetas.append(f"[v{i}]")
    filtros.append(
        f"{''.join(etiquetas)}amix=inputs={len(ORDEN)}:normalize=0,apad,atrim=0:{config['total']}[voz]"
    )
    salida = SALIDA / "mezcla.wav"
    if musica:
        n = len(ORDEN)
        entradas += ["-stream_loop", "-1", "-i", str(musica)]
        filtros.append(
            f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{config['total']},volume=0.16,"
            f"afade=t=in:d=1.5,afade=t=out:st={config['total'] - 3}:d=3[mus]"
        )
        filtros.append("[voz]asplit=2[voz1][voz2]")
        filtros.append(
            "[mus][voz2]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[musd]"
        )
        filtros.append("[voz1][musd]amix=inputs=2:normalize=0[out]")
    else:
        filtros.append("[voz]anull[out]")
    cruda = SALIDA / "mezcla-cruda.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            *entradas,
            "-filter_complex",
            ";".join(filtros),
            "-map",
            "[out]",
            "-ar",
            "48000",
            "-c:a",
            "pcm_s24le",
            str(cruda),
        ],
        check=True,
    )
    # Normalización en dos pasadas y lineal: no comprime ni sube la música en las pausas.
    objetivo = "I=-16:TP=-1.5:LRA=11"
    medida = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(cruda),
            "-af",
            f"loudnorm={objetivo}:print_format=json",
            "-f",
            "null",
            "-",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stderr
    m = json.loads(medida[medida.rindex("{") : medida.rindex("}") + 1])
    lineal = (
        f"loudnorm={objetivo}:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
        f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(cruda),
            "-af",
            lineal,
            "-ar",
            "48000",
            str(salida),
        ],
        check=True,
    )
    return salida


if __name__ == "__main__":
    import sys

    config = construir()
    (SALIDA / "montaje.json").write_text(json.dumps(config, ensure_ascii=False, indent=1))
    print(f"montaje.json · total {config['total']:.1f}s")
    for e in config["escenas"]:
        print(f"  {e['id']:4s} {e['inicio']:6.1f}s + {e['dur']:5.1f}s")
    musica = SALIDA / "musica.mp3"
    if "--audio" in sys.argv:
        print(mezclar(config, musica if musica.exists() else None))
