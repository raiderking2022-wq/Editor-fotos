# Editor de fotos por lote + bot de Telegram

Edita muchas fotos de forma automática: luz, color, balance de blancos, nitidez, recorte, tamaño y marca de agua.
Se puede usar de dos formas:

- **Consola** (`editor_fotos.py`): procesa una carpeta completa en tu computadora.
- **Bot de Telegram** (`bot.py`): el cliente envía fotos, elige un estilo y las recibe editadas. Incluye fotos gratis por día, créditos de pago y un panel de administrador.

Las dos usan el mismo motor (`motor.py`).

## Qué mejora respecto a la primera versión

| Antes | Ahora |
|---|---|
| El brillo se multiplicaba y quemaba los blancos | Curva gamma más estiramiento de niveles: aclara sin quemar |
| El color se ajustaba en RGB (subir la luz lavaba los colores) | Se ajusta en LAB: la luz y el color van por separado |
| La saturación subía todo por igual (piel anaranjada) | Tipo *vibrance*: sube más los colores apagados |
| La nitidez creaba bordes de colores | Se aplica solo a la luz, con un radio según el tamaño |
| No corregía la luz amarilla de los bombillos | Balance de blancos automático que mide solo en zonas neutras |
| No recuperaba las ventanas en interiores | Detalle local (CLAHE), muy útil en inmobiliaria |
| Se perdía calidad en cada paso (8 bits) | Todo en decimales; se convierte una sola vez al final |
| `foto.png` y `foto.jpg` se sobrescribían | Nombres únicos (`foto_2.jpg`) |
| PNG transparente quedaba con fondo negro | Fondo blanco |
| Una foto a la vez | Usa todos los núcleos del procesador |
| Solo JPG/PNG/WebP | También HEIC (iPhone), TIFF y RAW (CR2, NEF, ARW, DNG…) |
| Marca de agua solo con texto | Texto con sombra (se lee sobre fondos claros) o logo PNG |
| — | Imagen **antes/después** para mostrar al cliente |
| Guardaba el GPS de las fotos | No copia EXIF: no se filtra la ubicación de los clientes |

**Estilos:** natural, calido, frio, vivido, inmobiliaria, producto, boda, blanco_negro.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso por consola

```bash
python3 editor_fotos.py ENTRADA SALIDA --estilo inmobiliaria --marca "Mi Estudio" --recorte 4:5 --ancho 2000 --comparar
python3 editor_fotos.py --estilos          # lista de estilos
```

Opciones: `--logo logo.png` (en vez de texto), `--calidad 85`, `--procesos 2`.
Con `--comparar` se crea `SALIDA/comparaciones/` con imágenes antes/después.

Para ajustar un estilo, cambia sus números en `ESTILOS` dentro de `motor.py` (cada parámetro está explicado ahí).

## Bot de Telegram

### Ponerlo en marcha (modo prueba gratis)

1. En Telegram, habla con **@BotFather**, escribe `/newbot` y copia el token. Con `/setdescription` y `/setuserpic` le pones descripción y foto.
2. Habla con **@userinfobot** para saber tu ID.
3. Copia `.env.example` como `.env` y llena `TELEGRAM_TOKEN` y `ADMIN_IDS`. Deja `MODO=gratis`.
4. `pip install -r requirements.txt`
5. `python3 bot.py`. Debe decir «Bot iniciado en modo PRUEBA GRATIS».

El bot solo funciona mientras `bot.py` esté corriendo.

### Qué ve el cliente

- Envía una o varias fotos (hasta 30). Si las manda **como archivo**, conservan la calidad completa.
- Elige un estilo y recibe primero una imagen **antes/después** y luego sus fotos editadas, como archivos.
- Al final le pregunta **👍 Me gustó / 👎 No me gustó**.
- `/saldo`, `/estilos`, `/opinion texto`, `/marca Mi Estudio`, `/recorte 4:5`, `/ancho 2000`, `/cancelar`.

### Lo que ves tú durante la prueba

- Cada voto y cada `/opinion` te llegan al instante por Telegram.
- `/stats` muestra usuarios, fotos editadas, 👍/👎 por estilo y las últimas opiniones. Así sabes qué estilos afinar.

### Cuando quieras cobrar

Cambia `MODO=pago` en el `.env` y reinicia. A partir de ahí:

- Cada persona tiene `FOTOS_GRATIS_DIA` fotos gratis al día (por ejemplo 5), con la marca `MARCA_GRATIS`.
- Con créditos, las fotos salen sin tu marca. El cliente ve precios y su ID en `/comprar`.
- Tú confirmas el pago con `/agregar ID 200` y al cliente le llega el aviso.
- Los usuarios, votos y opiniones de la prueba se conservan.

## Dónde dejarlo corriendo durante la prueba

El bot usa *polling*, así que no necesita dominio ni HTTPS, pero sí una máquina encendida.

- **Tu propia computadora** (gratis, lo más fácil para unos días): déjala encendida con `python3 bot.py` abierto. Si se apaga o se suspende, el bot se detiene hasta que lo vuelvas a abrir.
- **Oracle Cloud «Always Free»**: una máquina virtual gratis que no se apaga. Piden tarjeta para verificar la cuenta, pero no cobran.
- **Un VPS de US$4–6 al mes** (Hetzner, DigitalOcean, Contabo), cuando ya vayas en serio. Con Docker:
  ```bash
  docker build -t fotobot .
  docker run -d --restart=always --env-file .env -v fotobot-datos:/data --name fotobot fotobot
  ```

No uses servicios que «duermen» la app tras unos minutos sin visitas: el bot dejaría de responder. El archivo `bot.db` guarda usuarios, votos y opiniones, así que haz copias de seguridad.

## Pruebas

```bash
python3 -m pytest -q
```

## Siguientes pasos sugeridos

1. Probar con 20–30 fotos reales de cada tipo de cliente (bodas, casas, productos) y afinar los números de `ESTILOS`.
2. Durante la prueba, compartir el bot con 5–10 fotógrafos, inmobiliarias o tiendas y revisar `/stats` cada día. Pedirles permiso para usar sus antes/después en tu publicidad.
3. Cuando haya clientes que pagan: cobrar con enlaces de pago (PayPal o Stripe) que sumen créditos automáticamente, y después hacer la página web usando el mismo `motor.py`.
