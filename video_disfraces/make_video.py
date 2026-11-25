"""Genera el video "¿Quién está detrás del disfraz?" (1:20, 1080x1920, 30 fps).

Uso: python3 make_video.py   ->  crea quien_esta_detras.mp4 en esta carpeta.
Requiere: Pillow, numpy, ffmpeg.
"""
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
DUR = 80.0
INTRO, SEG, OUTRO = 5.0, 14.0, 5.0
REVEAL = 4.0  # segundo dentro de cada segmento en que se revela el actor

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FS = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
_fc = {}


def font(path, size):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]


# personaje, película, actor, dato, color principal
ITEMS = [
    ("EL FAUNO", "El laberinto del fauno (2006)", "DOUG JONES",
     "Especialista en criaturas fantásticas, pasó horas en maquillaje y prótesis "
     "faciales para dar vida al Fauno y al Hombre Pálido.", (150, 120, 70)),
    ("PENNYWISE", "It (2017)", "BILL SKARSGÅRD",
     "Combinó maquillaje blanco, prótesis en frente y nariz, lentes de contacto "
     "y su propio control muscular para crear una versión irreconocible del payaso.", (210, 40, 40)),
    ("GOLLUM", "El Señor de los Anillos", "ANDY SERKIS",
     "Pionero de la captura de movimiento, utilizó trajes con marcadores digitales "
     "para trasladar sus gestos, voz y postura al personaje.", (150, 160, 110)),
    ("CHEWBACCA", "Star Wars", "PETER MAYHEW",
     "Con 2,21 metros de estatura, interpretó al wookiee durante décadas dentro de "
     "un pesado traje peludo y máscara de látex con visibilidad reducida.", (170, 110, 60)),
    ("HELLBOY", "Hellboy (2004 y 2008)", "RON PERLMAN",
     "Soportó entre tres y cuatro horas diarias de maquillaje y prótesis para lucir "
     "la piel roja, cuernos limados, colmillos y el brazo derecho gigante.", (220, 50, 30)),
]
assert INTRO + SEG * len(ITEMS) + OUTRO == DUR


# ---------------------------------------------------------------- utilidades
def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_out_back(t):
    t = max(0.0, min(1.0, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def text_c(d, y, txt, f, fill, stroke=0, sfill=(0, 0, 0), spacing=10, x=W / 2):
    d.multiline_text((x, y), txt, font=f, fill=fill, anchor="ma", align="center",
                     stroke_width=stroke, stroke_fill=sfill, spacing=spacing)


def wrap(txt, f, maxw):
    lines, cur = [], ""
    for w in txt.split():
        t = (cur + " " + w).strip()
        if f.getlength(t) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return "\n".join(lines)


def fit_font(path, txt, maxw, start):
    s = start
    while s > 30:
        f = font(path, s)
        if f.getlength(txt) <= maxw:
            return f
        s -= 4
    return font(path, s)


def gradient_bg(c1, c2):
    y = np.linspace(0, 1, H)[:, None, None]
    a = np.array(c1, float)[None, None, :]
    b = np.array(c2, float)[None, None, :]
    img = a * (1 - y) + b * y
    img = np.repeat(img, W, axis=1)
    # viñeta
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2)
    img *= np.clip(1.15 - 0.55 * r, 0.25, 1)[:, :, None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def darker(c, k):
    return tuple(int(v * k) for v in c)


# ------------------------------------------------------- máscara de teatro
def make_mask(color, size=620):
    """Máscara estilizada (rostro misterioso) en RGBA."""
    S = size * 2  # supersampling
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = S * 0.08
    face = [pad, pad * 0.6, S - pad, S - pad * 0.2]
    # sombra/borde
    d.ellipse([face[0] - 14, face[1] - 14, face[2] + 14, face[3] + 14], fill=(255, 255, 255, 255))
    d.ellipse(face, fill=darker(color, 0.55) + (255,))
    d.ellipse([face[0] + 40, face[1] + 40, face[2] - 40, face[3] - 140], fill=darker(color, 0.75) + (255,))
    # ojos
    ew, eh = S * 0.2, S * 0.11
    for cx in (S * 0.33, S * 0.67):
        cy = S * 0.42
        d.ellipse([cx - ew / 2, cy - eh / 2, cx + ew / 2, cy + eh / 2], fill=(10, 10, 15, 255))
        d.ellipse([cx - ew / 2 - 8, cy - eh / 2 - 30, cx + ew / 2 + 8, cy - eh / 2 + 6],
                  outline=(255, 255, 255, 200), width=10)
    # boca
    d.arc([S * 0.3, S * 0.58, S * 0.7, S * 0.8], 20, 160, fill=(10, 10, 15, 255), width=26)
    # signo de interrogación
    f = font(FB, int(S * 0.22))
    d.text((S / 2, S * 0.0), "?", font=f, fill=(255, 255, 255, 235), anchor="mt",
           stroke_width=10, stroke_fill=(0, 0, 0, 255))
    return im.resize((size, size), Image.LANCZOS)


# ------------------------------------------------------------ fotos reales
IMG_DIR = os.path.join(HERE, "imagenes")


def find_img(name):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        q = os.path.join(IMG_DIR, name + ext)
        if os.path.exists(q):
            return q
    return None


def photo_card(path, w, h, color, label=None):
    """Recorta la foto tipo 'cover', esquinas redondeadas, borde y etiqueta."""
    src = Image.open(path).convert("RGB")
    sc = max(w / src.width, h / src.height)
    src = src.resize((int(src.width * sc) + 1, int(src.height * sc) + 1), Image.LANCZOS)
    left = (src.width - w) // 2
    top = int((src.height - h) * 0.08)  # prioriza la parte superior (rostros)
    src = src.crop((left, top, left + w, top + h)).convert("RGBA")
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 40, fill=255)
    card = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([0, 0, w + 15, h + 15], 48, fill=color + (255,))
    src.putalpha(m)
    card.alpha_composite(src, (8, 8))
    if label:
        d = ImageDraw.Draw(card)
        f = font(FB, 38)
        tw = f.getlength(label)
        d.rounded_rectangle([(w + 16 - tw) / 2 - 24, h - 60, (w + 16 + tw) / 2 + 24, h + 2], 25,
                            fill=(0, 0, 0, 210))
        d.text(((w + 16) / 2, h - 29), label, font=f, fill=(255, 255, 255), anchor="mm")
    return card


# ------------------------------------------------------------- partículas
rng = np.random.default_rng(7)
PARTS = rng.random((70, 4))  # x, y, velocidad, tamaño


def draw_particles(d, t, color):
    for x, y, v, s in PARTS:
        py = (y * H - t * (40 + v * 120)) % H
        px = x * W + math.sin(t * (0.5 + v) + x * 10) * 30
        r = 2 + s * 5
        a = int(60 + 120 * s)
        c = tuple(min(255, int(cc * 0.5 + 128)) for cc in color)
        d.ellipse([px - r, py - r, px + r, py + r], fill=c + (a,))


# ----------------------------------------------------------- precálculos
print("Preparando recursos...")
BGS = [gradient_bg(darker(c, 0.45), (8, 8, 14)) for *_, c in ITEMS]
BG_INTRO = gradient_bg((60, 20, 80), (5, 5, 12))
MASKS = [make_mask(c) for *_, c in ITEMS]
CHAR_BIG, CHAR_SM, ACT_SM = [], [], []
for _n, it in enumerate(ITEMS, 1):
    pc, pa = find_img(f"{_n}_personaje"), find_img(f"{_n}_actor")
    CHAR_BIG.append(photo_card(pc, 820, 640, it[4]) if pc else None)
    CHAR_SM.append(photo_card(pc, 460, 500, it[4], "PERSONAJE") if pc else None)
    ACT_SM.append(photo_card(pa, 460, 500, it[4], "ACTOR") if pa else None)
    print(f"  #{_n}: personaje={'sí' if pc else 'NO'}  actor={'sí' if pa else 'NO'}")
MASK_INTRO = make_mask((180, 140, 40), 700)


def seg_header(d, idx, color, t):
    # barra superior
    d.rounded_rectangle([60, 90, W - 60, 230], 40, fill=(0, 0, 0, 150), outline=color + (255,), width=5)
    text_c(d, 112, "¿QUIÉN ESTÁ DETRÁS?", font(FB, 74), (255, 255, 255), 3)
    # número
    k = ease_out_back(t / 0.5)
    sz = int(150 * max(0.01, k))
    if sz > 4:
        text_c(d, 270, f"#{idx + 1}", font(FB, sz), color, 6, (0, 0, 0))


def render_segment(i, t):
    name, movie, actor, fact, color = ITEMS[i]
    img = BGS[i].copy().convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    draw_particles(d, t + i * 3, color)
    seg_header(d, i, color, t)

    # nombre del personaje + película
    k = ease_out(t / 0.6)
    yname = 470 + (1 - k) * 80
    fn = fit_font(FB, name, W - 120, 110)
    text_c(d, yname, name, fn, (255, 255, 255), 6, darker(color, 0.3))
    text_c(d, yname + fn.size + 25, movie, font(FR, 50), (220, 220, 230), 2)
    img = Image.alpha_composite(img, ov)

    mask = MASKS[i]
    mx, my = (W - mask.width) // 2, 760
    if t < REVEAL:
        # máscara que flota y tiembla al acercarse la revelación
        bob = math.sin(t * 3) * 14
        shake = 0
        if t > REVEAL - 1.0:
            shake = math.sin(t * 70) * 12 * (t - (REVEAL - 1.0))
        a = ease_out(t / 0.5)
        m = CHAR_BIG[i].copy() if CHAR_BIG[i] else mask.copy()
        if CHAR_BIG[i]:
            mx, my = (W - m.width) // 2, 700
            bob = bob * 0.4
        if a < 1:
            m.putalpha(m.getchannel("A").point(lambda p: int(p * a)))
        img.alpha_composite(m, (int(mx + shake), int(my + bob)))
        # cuenta regresiva
        d2 = ImageDraw.Draw(img)
        rem = REVEAL - t
        cnt = str(int(math.ceil(rem))) if rem > 0.05 else ""
        frac = rem - math.floor(rem)
        if cnt and t > 0.4:
            s = int(120 + 50 * frac)
            text_c(d2, 1440, cnt, font(FB, s), (255, 230, 90), 6)
        # barra de progreso
        p = min(1, t / REVEAL)
        bar = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(bar).rounded_rectangle([140, 1680, W - 140, 1710], 15, fill=(255, 255, 255, 50))
        img = Image.alpha_composite(img, bar)
        d2 = ImageDraw.Draw(img)
        d2.rounded_rectangle([140, 1680, 140 + (W - 280) * p, 1710], 15, fill=color + (255,))
    else:
        tr = t - REVEAL
        # mitades de la máscara saliendo hacia los lados
        if tr < 0.8:
            sp = ease_out(tr / 0.8)
            half = mask.width // 2
            L = mask.crop((0, 0, half, mask.height)).rotate(sp * 25, expand=False)
            R = mask.crop((half, 0, mask.width, mask.height)).rotate(-sp * 25, expand=False)
            fade = 1 - sp
            for part in (L, R):
                part.putalpha(part.getchannel("A").point(lambda p: int(p * fade)))
            img.alpha_composite(L, (int(mx - sp * 600), my + int(sp * 120)))
            img.alpha_composite(R, (int(mx + half + sp * 600), my + int(sp * 120)))
        # destello
        if tr < 0.35:
            fl = Image.new("RGBA", (W, H), (255, 255, 255, int(230 * (1 - tr / 0.35))))
            img = Image.alpha_composite(img, fl)
        d3 = ImageDraw.Draw(img)
        has_ph = CHAR_SM[i] is not None and ACT_SM[i] is not None
        if has_ph:
            # personaje (izq.) y actor (der.) lado a lado
            kc = ease_out(tr / 0.5)
            ka = ease_out_back((tr - 0.1) / 0.6)
            img.alpha_composite(CHAR_SM[i], (int(52 - (1 - kc) * 300), 690))
            if tr > 0.1:
                img.alpha_composite(ACT_SM[i], (int(552 + (1 - min(1, ka)) * 600), 690))
            cy, fy = 1255, 1495
        else:
            cy, fy = 900, 1330
        d3 = ImageDraw.Draw(img)
        k = ease_out_back(tr / 0.6)
        cw = int((W - 120) * max(0.02, min(1.1, k)))
        ch = 210 if has_ph else 330
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(card).rounded_rectangle([W / 2 - cw / 2, cy - 30, W / 2 + cw / 2, cy - 30 + ch], 50,
                                               fill=(0, 0, 0, 200), outline=color + (255,), width=8)
        img = Image.alpha_composite(img, card)
        d3 = ImageDraw.Draw(img)
        if tr > 0.15:
            text_c(d3, cy - 10, "ES...", font(FB, 46), color, 3)
            fa = fit_font(FB, actor, W - 200, 110 if has_ph else 120)
            ka2 = ease_out_back((tr - 0.15) / 0.5)
            fa2 = font(FB, max(10, int(fa.size * min(1.2, ka2))))
            text_c(d3, cy + 50, actor, fa2, (255, 255, 255), 7, darker(color, 0.4))
        if tr > 0.6:
            k2 = ease_out((tr - 0.6) / 0.6)
            yf = fy + (1 - k2) * 60
            text_c(d3, yf, wrap(fact, font(FB, 46), W - 120), font(FB, 46), (255, 240, 200), 4, spacing=18)
    # transición de salida
    if t > SEG - 0.25:
        a = int(255 * (t - (SEG - 0.25)) / 0.25)
        img = Image.alpha_composite(img, Image.new("RGBA", (W, H), (0, 0, 0, a)))
    if t < 0.2:
        a = int(255 * (1 - t / 0.2))
        img = Image.alpha_composite(img, Image.new("RGBA", (W, H), (0, 0, 0, a)))
    return img


def star(d, cx, cy, r, color):
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=color, outline=(0, 0, 0))


def render_intro(t):
    img = BG_INTRO.copy().convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    draw_particles(d, t, (200, 150, 60))
    img = Image.alpha_composite(img, ov)
    k = ease_out_back(t / 0.8)
    s = max(10, int(700 * k))
    m = MASK_INTRO.resize((s, s), Image.LANCZOS).rotate(math.sin(t * 2) * 6)
    img.alpha_composite(m, ((W - s) // 2, 700 + (700 - s) // 2))
    d = ImageDraw.Draw(img)
    l1 = ease_out((t - 0.3) / 0.6)
    if l1 > 0:
        text_c(d, 200 - (1 - l1) * 100, "¿QUIÉN ESTÁ", font(FB, 130), (255, 255, 255), 8, (60, 0, 80))
    l2 = ease_out((t - 0.6) / 0.6)
    if l2 > 0:
        text_c(d, 350 - (1 - l2) * 100, "DETRÁS DEL", font(FB, 130), (255, 255, 255), 8, (60, 0, 80))
    l3 = ease_out_back((t - 0.9) / 0.6)
    if l3 > 0:
        text_c(d, 500, "DISFRAZ?", font(FB, max(10, int(160 * min(1.1, l3)))), (255, 205, 50), 9, (60, 0, 80))
    if t > 1.8:
        a = ease_out((t - 1.8) / 0.6)
        d.rounded_rectangle([60, 1460, W - 60, 1600], 50, fill=(200, 30, 60))
        d.text((W / 2, 1530 + (1 - a) * 20), "5 ACTORES IRRECONOCIBLES", font=font(FB, 54),
               fill=(255, 255, 255), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0))
    if t > 2.6:
        text_c(d, 1680, "¿Cuántos adivinas?", font(FR, 64), (240, 240, 240), 2)
    if t > DUR:  # nunca
        pass
    if t > INTRO - 0.25:
        a = int(255 * (t - (INTRO - 0.25)) / 0.25)
        img = Image.alpha_composite(img, Image.new("RGBA", (W, H), (0, 0, 0, a)))
    return img


def render_outro(t):
    img = BG_INTRO.copy().convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    draw_particles(d, t + 50, (200, 150, 60))
    img = Image.alpha_composite(img, ov)
    d = ImageDraw.Draw(img)
    k = ease_out_back(t / 0.6)
    text_c(d, 260, "¿CUÁL TE", font(FB, max(10, int(140 * min(1.1, k)))), (255, 255, 255), 8, (60, 0, 80))
    text_c(d, 420, "SORPRENDIÓ", font(FB, max(10, int(140 * min(1.1, k)))), (255, 205, 50), 8, (60, 0, 80))
    text_c(d, 580, "MÁS?", font(FB, max(10, int(140 * min(1.1, k)))), (255, 255, 255), 8, (60, 0, 80))
    if t > 0.6:
        a = ease_out((t - 0.6) / 0.5)
        d.rounded_rectangle([140, 860 + (1 - a) * 40, W - 140, 1020 + (1 - a) * 40], 50, fill=(255, 255, 255))
        d.text((W / 2, 940 + (1 - a) * 40), "DÉJALO EN COMENTARIOS", font=font(FB, 50), fill=(30, 10, 40), anchor="mm")
    # mini lista de actores
    if t > 1.0:
        for j, it in enumerate(ITEMS):
            if t > 1.0 + j * 0.15:
                text_c(d, 1110 + j * 82, f"{it[2]}  ·  {it[0]}", font(FB, 44), (255, 255, 255), 3, darker(it[4], 0.5))
    if t > 2.5:
        pulse = 1 + 0.06 * math.sin((t - 2.5) * 8)
        f = font(FB, int(70 * pulse))
        d.rounded_rectangle([170, 1610, W - 170, 1760], 70, fill=(200, 30, 60))
        text_c(d, 1685 - f.size / 2 - 8, "SÍGUEME PARA MÁS", f, (255, 255, 255), 2)
    text_c(d, 1830, "Fotos: Wikimedia Commons (Gage Skidmore y otros, CC BY-SA) y Wikipedia",
           font(FR, 24), (170, 170, 180))
    if t > OUTRO - 0.5:
        a = int(255 * (t - (OUTRO - 0.5)) / 0.5)
        img = Image.alpha_composite(img, Image.new("RGBA", (W, H), (0, 0, 0, a)))
    return img


def frame_at(t):
    if t < INTRO:
        return render_intro(t)
    if t >= DUR - OUTRO:
        return render_outro(t - (DUR - OUTRO))
    i = int((t - INTRO) // SEG)
    return render_segment(i, t - INTRO - i * SEG)


# ------------------------------------------------------------------ audio
SR = 44100


def synth_audio(path):
    n = int(DUR * SR)
    out = np.zeros(n)
    tt = np.arange(n) / SR
    bpm = 120
    beat = 60 / bpm

    def add(sig, start):
        s = int(start * SR)
        e = min(n, s + len(sig))
        if s < n:
            out[s:e] += sig[: e - s]

    # bombo
    kl = int(0.35 * SR)
    kt = np.arange(kl) / SR
    kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 9)
    # hi-hat
    hl = int(0.06 * SR)
    hat = rng.standard_normal(hl) * np.exp(-np.arange(hl) / SR * 70)
    hat = np.diff(hat, prepend=0)
    # bajo misterioso (La menor - Fa - Do - Mi)
    roots = [55.0, 43.65, 65.41, 41.2]
    b = 0.0
    while b < DUR - 1:
        bar = int(b // (beat * 4))
        add(kick * 0.9, b)
        add(hat * 0.18, b + beat / 2)
        f = roots[bar % 4]
        L = int(beat * SR)
        lt = np.arange(L) / SR
        bass = np.tanh(2 * np.sin(2 * np.pi * f * lt)) * np.exp(-lt * 3) * 0.28
        add(bass, b)
        b += beat
    # pad
    for bar in range(int(DUR / (beat * 4)) + 1):
        f = roots[bar % 4] * 4
        L = int(beat * 4 * SR)
        lt = np.arange(L) / SR
        env = np.minimum(1, lt / 0.5) * np.minimum(1, (beat * 4 - lt) / 0.5)
        pad = sum(np.sin(2 * np.pi * f * m * lt + m) for m in (1, 1.5, 2.0)) * env * 0.035
        add(pad, bar * beat * 4)

    # efectos por segmento
    def whoosh(dur=0.7):
        L = int(dur * SR)
        noise = rng.standard_normal(L)
        lt = np.arange(L) / SR
        env = np.sin(np.pi * lt / dur) ** 2
        # filtro paso-bajo variable simple
        y = np.zeros(L)
        acc = 0
        for k in range(L):
            a = 0.02 + 0.5 * (k / L)
            acc += a * (noise[k] - acc)
            y[k] = acc
        return y * env * 0.9

    def ding():
        L = int(1.2 * SR)
        lt = np.arange(L) / SR
        return sum(np.sin(2 * np.pi * f * lt) * np.exp(-lt * d) for f, d in
                   ((880, 4), (1320, 5), (1760, 7))) * 0.22

    def tick():
        L = int(0.05 * SR)
        lt = np.arange(L) / SR
        return np.sin(2 * np.pi * 1500 * lt) * np.exp(-lt * 80) * 0.35

    W1 = whoosh()
    D1 = ding()
    T1 = tick()
    add(W1, 0.2)
    add(D1, 1.0)
    for i in range(len(ITEMS)):
        s0 = INTRO + i * SEG
        add(W1 * 0.6, s0)
        for c in (1, 2, 3):
            add(T1, s0 + REVEAL - c)
        add(W1, s0 + REVEAL - 0.35)
        add(D1, s0 + REVEAL)
    add(D1, DUR - OUTRO)

    # ducking ligero + fade final
    out *= np.minimum(1, (DUR - tt) / 1.5)
    out = np.tanh(out * 1.2) * 0.8
    pcm = (out * 32767).astype(np.int16)
    st = np.repeat(pcm[:, None], 2, axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


def main():
    wav = os.path.join(HERE, "audio.wav")
    print("Sintetizando audio...")
    synth_audio(wav)
    outp = os.path.join(HERE, "quien_esta_detras.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", outp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = int(DUR * FPS)
    for f in range(total):
        im = frame_at(f / FPS).convert("RGB")
        p.stdin.write(im.tobytes())
        if f % 150 == 0:
            print(f"  frame {f}/{total}")
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print("Listo:", outp)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        for t in [float(x) for x in sys.argv[2:]]:
            frame_at(t).convert("RGB").save(os.path.join(HERE, f"prev_{t:.1f}.png"))
    else:
        main()
