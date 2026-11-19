# Editor de Fotos Excursión

Editor de fotos por lote para excursiones (buggy, cenotes, cuevas, selva, santuario de monos).

- **`index.html`**: la web. Edita las fotos dentro del navegador (móvil o PC). No sube nada a ningún servidor y su costo es $0.
- **`editor_fotos.py`**: el script de Python para la PC (lotes enormes y, más adelante, RAW).

## Web: qué hace
- Sube varias fotos (botón o arrastrar y soltar).
- Vista previa con comparador antes/después deslizable.
- Estilos: **Vívido excursión**, Cenote/Cueva, Selva/Monos, Buggy/Sol y Natural.
- Ajustes: exposición, contraste, intensidad (vibrance, cuida la piel), saturación, calidez, sombras, luces altas, agua turquesa, verdes y nitidez.
- Recorte (4:5, 1:1, 16:9, 9:16, 3:2), ancho máximo, JPG o WebP y calidad.
- Marca de agua con texto o logo.
- Descarga en ZIP (en partes de 40 si son muchas), una por una o "Compartir" para guardar en la galería del móvil.
- Respeta la rotación de las fotos de celular y recuerda tu último estilo.

## Probar en la PC
Abre `index.html` con doble clic en Chrome, Edge o Firefox.

## Publicar gratis con GitHub Pages
1. Junta (merge) el `index.html` a la rama `main`.
2. En GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: `main` / `(root)` → Save**.
3. En 1-2 minutos queda en `https://TU-USUARIO.github.io/Editor-fotos/`. Abre ese enlace en el móvil y en la PC.

## Script de Python
```bash
pip install pillow opencv-python numpy
python3 editor_fotos.py ENTRADA SALIDA --estilo vivido --marca "Mi Estudio" --recorte 4:5 --ancho 2000
```
