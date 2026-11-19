# Proyecto: Editor de fotos para excursiones (web + script + bot)

## Contexto del usuario
- Habla español (República Dominicana). Responder siempre en español, claro y práctico.
- Quiere generar ingresos con una herramienta que edite fotos por lote.
- Presupuesto: lo más barato posible, idealmente gratis.
- Usa el móvil y una PC. Quiere probar en ambos.

## Nicho y estilo de las fotos
- Fotos de excursiones: buggy, naturaleza, cenotes, cuevas, santuario de monos y similares.
- Look deseado: **colores vivos** que resalten la naturaleza (verdes, azules/turquesa del agua, tierra), sin verse artificial.
- Retos: cuevas/cenotes (poca luz, rayos de luz), agua turquesa (sin saturar la piel), buggy (polvo y sol), selva (verdes densos).

## Decisiones tomadas
1. Python (Pillow, OpenCV, numpy) en vez de Lightroom: sin licencias.
2. Prioridad: **1) Web estática en el navegador** (en vez del bot de Telegram), 2) Bot de Telegram (opcional), 3) Escritorio.
3. La web edita las fotos en el navegador del cliente (Canvas + JavaScript). Sin servidor, sin subir fotos, costo $0.
   La lógica del script de Python se reescribió en JavaScript (una web estática no puede ejecutar Python).
4. Una sola web sirve para móvil y PC.
5. Para RAW o miles de fotos, el script de Python en la PC sigue siendo la opción potente.
6. Pagos al inicio manuales (transferencia o PayPal).

## Estado actual
- `index.html` **construida y probada** en Chromium (vista móvil 390px y PC) con imágenes sintéticas:
  - Subida múltiple + arrastrar y soltar, miniaturas, comparador antes/después deslizable.
  - Estilos: Vívido excursión (principal), Cenote/Cueva, Selva/Monos, Buggy/Sol, Natural + "Personalizado".
  - Sliders: exposición (EV), contraste, vibrance (protege piel), saturación, calidez, sombras, luces altas,
    agua turquesa, verdes, nitidez (unsharp sobre luminancia). Auto exposición igual que en Python.
  - Recorte (original, 4:5, 1:1, 16:9, 9:16, 3:2), ancho máximo, JPG/WebP, calidad.
  - Marca de agua con texto y/o logo (posición, tamaño, opacidad).
  - ZIP con JSZip (cdnjs, partes de 40 fotos), descarga individual, botón Compartir (galería del móvil).
  - Respeta EXIF (carga con `<img>`), límite de 16 MP por canvas (iPhone), libera memoria entre fotos.
  - Guarda el último estilo y opciones en `localStorage` (con try/catch).
- `editor_fotos.py` funciona (probado solo con imágenes sintéticas). Estilos: natural, calido, frio, vivido, inmobiliaria.
  Todavía NO tiene los estilos nuevos de la web (vibrance, sombras/luces, agua, verdes).

## Pendiente (en orden)
1. Probar la web con fotos reales de excursiones y afinar "Vívido excursión".
2. Activar GitHub Pages (Settings → Pages → rama `main`) y probar en móvil y PC (incluido iPhone/Safari).
3. Pasar los estilos de la web al script de Python para que ambos se vean parecidos.
4. Soporte RAW en el script (`rawpy`).
5. Monetización en la web: plan gratis (p. ej. marca "Editado con..." o límite de fotos) vs. de pago; vender presets (exportar/importar estilos en JSON).
6. Opcional: bot de Telegram, ventana de escritorio (tkinter) o `.exe` (PyInstaller).
7. Definir precios y conseguir clientes (operadores de excursiones, fotógrafos de tours, agencias, hoteles).

## Notas técnicas
- Código simple y comentado en español.
- No subir tokens ni claves al repo: usar variables de entorno.
- Al avanzar, actualizar "Estado actual" y "Pendiente".
