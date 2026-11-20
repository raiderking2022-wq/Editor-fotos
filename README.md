# Editor-fotos

**Estudio de Imágenes**: una página web (un solo archivo, `index.html`) que, a partir de una foto de tu modelo, genera una serie de escenas manteniendo su rostro y su cuerpo. Solo cambian la ropa y el lugar, y la modelo queda a un lado para dejar espacio libre para texto.

## Cómo usarla
1. Abre `index.html` en el navegador (o publícala en GitHub Pages / Vercel).
2. Sube la foto de la modelo.
3. Elige el motor (los tres primeros son gratis):
   - **Hugging Face (recomendado)**: usa FLUX Kontext o Qwen Image Edit, que respetan el rostro. Tiene una cuota gratis diaria; con un token gratis de [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) tienes más.
   - **Copiar prompts**: prepara un prompt por escena para pegarlo con tu foto en la app de Gemini o en Dreamina (uso gratis diario).
   - **AI Horde**: gratis e ilimitado, pero no conserva bien la cara.
   - **Gemini API**: de pago, la mejor calidad.
4. Marca o edita las escenas (Navidad, lluvia con sombrilla, playa, París, otoño, nieve, gala, oficina, jardín, ciudad de noche, o tus propias escenas).
5. Elige el lado donde va la modelo (izquierda, derecha o alternar), el formato (16:9, 4:5, 9:16, 1:1) y el estilo, y pulsa **Generar**.

La clave se guarda solo en tu navegador.
