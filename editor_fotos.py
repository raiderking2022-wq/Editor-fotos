#!/usr/bin/env python3
"""Editor de fotos por lote.

Uso:
    python3 editor_fotos.py CARPETA_ENTRADA CARPETA_SALIDA [--estilo calido] [--marca "Mi Estudio"]

Estilos: natural, calido, frio, vivido, inmobiliaria
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp"}

# exposicion: multiplicador de brillo | contraste: 1.0 = igual | saturacion: 1.0 = igual
# calidez: >0 mas calido (rojo/amarillo), <0 mas frio (azul) | nitidez: 0 a 1
ESTILOS = {
    "natural":      dict(exposicion=1.00, contraste=1.05, saturacion=1.05, calidez=0,   nitidez=0.4),
    "calido":       dict(exposicion=1.05, contraste=1.08, saturacion=1.10, calidez=12,  nitidez=0.4),
    "frio":         dict(exposicion=1.00, contraste=1.10, saturacion=0.95, calidez=-12, nitidez=0.4),
    "vivido":       dict(exposicion=1.03, contraste=1.15, saturacion=1.30, calidez=4,   nitidez=0.6),
    "inmobiliaria": dict(exposicion=1.15, contraste=1.10, saturacion=1.10, calidez=0,   nitidez=0.7),
}


def autocorregir_exposicion(img):
    """Ajusta el brillo para acercar el promedio a un valor medio agradable."""
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    promedio = float(gris.mean()) or 1.0
    factor = np.clip(120.0 / promedio, 0.8, 1.4)
    return cv2.convertScaleAbs(img, alpha=factor, beta=0)


def ajustar(img, exposicion, contraste, saturacion, calidez, nitidez):
    img = autocorregir_exposicion(img)
    f = img.astype(np.float32)

    f *= exposicion
    f = (f - 128.0) * contraste + 128.0

    # calidez: sube rojo y baja azul (BGR)
    f[:, :, 2] += calidez
    f[:, :, 0] -= calidez
    f = np.clip(f, 0, 255).astype(np.uint8)

    # saturacion
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturacion, 0, 255)
    f = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # nitidez (unsharp mask)
    if nitidez > 0:
        suave = cv2.GaussianBlur(f, (0, 0), 2.0)
        f = cv2.addWeighted(f, 1 + nitidez, suave, -nitidez, 0)
    return f


def recortar(img, ratio):
    """Recorta al centro a una relacion de aspecto (ancho/alto)."""
    h, w = img.shape[:2]
    actual = w / h
    if actual > ratio:
        nw = int(h * ratio)
        x = (w - nw) // 2
        return img[:, x:x + nw]
    nh = int(w / ratio)
    y = (h - nh) // 2
    return img[y:y + nh, :]


def marca_de_agua(pil_img, texto):
    img = pil_img.convert("RGBA")
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(capa)
    tam = max(16, img.width // 25)
    try:
        fuente = ImageFont.truetype("DejaVuSans.ttf", tam)
    except OSError:
        fuente = ImageFont.load_default()
    caja = draw.textbbox((0, 0), texto, font=fuente)
    tw, th = caja[2] - caja[0], caja[3] - caja[1]
    margen = tam // 2
    pos = (img.width - tw - margen, img.height - th - margen * 2)
    draw.text(pos, texto, font=fuente, fill=(255, 255, 255, 170))
    return Image.alpha_composite(img, capa).convert("RGB")


def procesar(ruta, destino, args):
    # ImageOps.exif_transpose respeta la rotacion de fotos de celular
    pil = ImageOps.exif_transpose(Image.open(ruta)).convert("RGB")
    img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    img = ajustar(img, **ESTILOS[args.estilo])

    if args.recorte:
        a, b = args.recorte.split(":")
        img = recortar(img, float(a) / float(b))

    if args.ancho and img.shape[1] > args.ancho:
        escala = args.ancho / img.shape[1]
        img = cv2.resize(img, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA)

    salida = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    if args.marca:
        salida = marca_de_agua(salida, args.marca)

    salida.save(destino / (ruta.stem + ".jpg"), quality=92, optimize=True)


def main():
    p = argparse.ArgumentParser(description="Editor de fotos por lote")
    p.add_argument("entrada")
    p.add_argument("salida")
    p.add_argument("--estilo", choices=ESTILOS, default="natural")
    p.add_argument("--marca", help="Texto de marca de agua")
    p.add_argument("--recorte", help="Relacion de aspecto, ej. 4:5 o 16:9")
    p.add_argument("--ancho", type=int, help="Ancho maximo en pixeles")
    args = p.parse_args()

    entrada, salida = Path(args.entrada), Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    fotos = sorted(f for f in entrada.iterdir() if f.suffix.lower() in EXTENSIONES)
    if not fotos:
        sys.exit("No encontre fotos en la carpeta de entrada.")

    errores = 0
    for i, foto in enumerate(fotos, 1):
        try:
            procesar(foto, salida, args)
            print(f"[{i}/{len(fotos)}] {foto.name} OK")
        except Exception as e:
            errores += 1
            print(f"[{i}/{len(fotos)}] {foto.name} ERROR: {e}")
    print(f"Listo: {len(fotos) - errores} editadas, {errores} con error.")


if __name__ == "__main__":
    main()
