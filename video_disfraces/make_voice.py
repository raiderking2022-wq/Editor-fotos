"""Genera la narración (voz neural en español) en voz/*.wav con edge-tts.
Uso: python3 make_voice.py   (requiere: pip install edge-tts, ffmpeg)"""
import os, subprocess, json
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "voz")
VOICE = "es-MX-JorgeNeural"
# (nombre, inicio en segundos, duración máxima, texto)
INTRO, SEG, REVEAL = 5.0, 14.0, 4.0
ITEMS = [
    ("el Fauno", "Doug Jones",
     "Especialista en criaturas fantásticas, pasó horas en maquillaje y prótesis faciales para dar vida al Fauno y al Hombre Pálido."),
    ("Pennywise", "Bill Skarsgård",
     "Combinó maquillaje blanco, prótesis en frente y nariz, lentes de contacto y su propio control muscular para crear una versión irreconocible del payaso."),
    ("Gollum", "Andy Serkis",
     "Pionero de la captura de movimiento, utilizó trajes con marcadores digitales para trasladar sus gestos, voz y postura al personaje."),
    ("Chewbacca", "Peter Mayhew",
     "Con dos metros veintiún de estatura, interpretó al wookiee durante décadas dentro de un pesado traje peludo y máscara de látex con visibilidad reducida."),
    ("Hellboy", "Ron Perlman",
     "Soportó entre tres y cuatro horas diarias de maquillaje y prótesis para lucir la piel roja, cuernos limados, colmillos y el brazo derecho gigante."),
]
NUM = ["uno", "dos", "tres", "cuatro", "cinco"]
LINES = [("intro", 0.3, 4.4, "¿Quién está detrás del disfraz? Cinco actores irreconocibles.")]
for i, (ch, actor, fact) in enumerate(ITEMS):
    s0 = INTRO + i * SEG
    LINES.append((f"{i+1}a", s0 + 0.3, REVEAL - 0.5, f"Número {NUM[i]}: {ch}. ¿Quién es?"))
    LINES.append((f"{i+1}b", s0 + REVEAL + 0.25, SEG - REVEAL - 0.6, f"¡Es {actor}! {fact}"))
LINES.append(("outro", 75.3, 4.4, "¿Cuál te sorprendió más? Déjalo en comentarios, y sígueme para más."))


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", p]).decode())


def tts(text, rate, mp3):
    env = dict(os.environ)
    env.setdefault("SSL_CERT_FILE", "/root/.ccr/ca-bundle.crt") if os.path.exists("/root/.ccr/ca-bundle.crt") else None
    cmd = ["edge-tts", "--voice", VOICE, f"--rate={rate:+d}%", "--text", text, "--write-media", mp3]
    if os.environ.get("HTTPS_PROXY"):
        cmd += ["--proxy", os.environ["HTTPS_PROXY"]]
    subprocess.run(cmd, check=True, env=env, capture_output=True)


os.makedirs(OUT, exist_ok=True)
plan = []
for name, start, maxd, text in LINES:
    mp3 = os.path.join(OUT, name + ".mp3")
    rate = 0
    tts(text, rate, mp3)
    d = dur(mp3)
    while d > maxd and rate < 45:
        rate = min(45, rate + max(4, int((d / maxd - 1) * 100) + 2))
        tts(text, rate, mp3)
        d = dur(mp3)
    wav = os.path.join(OUT, name + ".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                    "-ar", "44100", "-ac", "1", wav], check=True)
    os.remove(mp3)
    print(f"{name}: {d:.2f}s (máx {maxd:.1f}) rate {rate:+d}%")
    plan.append({"file": name + ".wav", "start": start})
json.dump(plan, open(os.path.join(OUT, "plan.json"), "w"), indent=1)
