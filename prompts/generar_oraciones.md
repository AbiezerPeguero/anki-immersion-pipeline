# Prompt: de transcripcion a oraciones listas para el pipeline

Cambia solo 3 cosas antes de enviarlo: el alias del mazo (2 veces), la cantidad de oraciones y la transcripcion.
Opcional: al final del mensaje, una linea `Palabras: hefty, waive, hang out` (ver mas abajo). Sin esa linea, todo es fiel al video.

```
Voy a pegarte la transcripción de un video en inglés. Quiero que me prepares oraciones para tarjetas de Anki.

Mazo: blogs
Cantidad: 10 oraciones (mínimo; las oraciones con mis palabras nuevas, si las hay, cuentan dentro de este número)

Reglas:
1. Elige oraciones ÚTILES para aprender inglés real: expresiones naturales, phrasal verbs, conectores, contracciones y estructuras que se repiten en conversaciones. Evita datos que solo tienen sentido dentro del video (nombres propios, cifras sueltas).
2. Cada oración debe entenderse sola, sin el contexto del video, y tener entre 6 y 20 palabras. Si el hablante la dijo incompleta, redáctala completa conservando sus palabras y su tono. Quita muletillas (um, uh, you know).
3. Sé fiel al contenido: no cambies lo que el hablante afirma (cifras, quién hizo qué, cuándo) y no inventes hechos, temas ni nombres que la transcripción no menciona. Limpiar y completar la redacción está permitido; cambiar el significado no. No repitas oraciones. La única excepción para añadir palabras que no están en el video es la sección "Palabras nuevas", y SOLO aplica si yo escribo esas palabras.
4. Traducción al español natural latinoamericano, no literal.
5. Ordénalas de la más útil a la menos útil.
6. No uses el símbolo | dentro de ninguna oración o traducción.
7. Termina cada oración en inglés con su puntuación final (. ? !).
8. (Solo si el texto viene de una foto/OCR) Puede tener errores de lectura: letras cambiadas, 0 en vez de o, signos mal puestos, palabras cortadas. Corrígelos con el contexto antes de crear las oraciones.

Palabras nuevas (OPCIONAL: solo si, después de la transcripción, escribo una línea que empieza con "Palabras:"):
- Si NO escribo esa línea, ignora por completo esta sección: todas las oraciones son fieles al video, como indica la regla 3.
- Si la escribo, cada palabra o expresión de esa línea debe aparecer al menos una vez, en la oración del video donde mejor encaje.
- Parte siempre de una oración real del video y puedes sumarle hasta 3 palabras ADEMÁS de mi palabra (mi palabra no cuenta; si es una expresión como "hang out", tampoco). Se permiten los ajustes gramaticales mínimos (conjugar mi palabra, ponerla en plural, mover el orden).
- Mantén la situación del video (mismos hechos, cifras, personas y tono) y que la oración suene natural, como se diría en la vida real. Sigue cumpliendo las reglas 1 a 8.
- Si una palabra no encaja de forma natural con ese límite, no la fuerces: no la incluyas y dímelo en la nota.
- Después del bloque, en una nota breve, indica para cada oración extendida la oración original del video y qué palabras se le agregaron.

Formato de salida (EXACTO, dentro de UN solo bloque de código, sin nada más dentro del bloque):
@deck: blogs
English sentence | Traducción al español
English sentence | Traducción al español

Una oración por línea, separadas por " | ". Sin numeración, sin viñetas, sin comillas.
Fuera del bloque no agregues nada, salvo una nota breve si alguna parte de la transcripción no se entendía y, si usé "Palabras:", la nota de oraciones extendidas.

Transcripción:
PEGA AQUÍ EL TEXTO
```

## Que hacer con la respuesta

1. Copia SOLO el contenido del bloque de codigo que te devuelva Claude.
2. En VS Code: File -> New Text File, pega, y guardalo en `data/input/` con extension `.txt` (por ejemplo `blogs_2026-11-09.txt`). VS Code guarda en UTF-8, que es lo que necesita el pipeline.
3. Corre las etapas 2 y 3 con ese archivo.
