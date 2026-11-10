> **Guía personal de uso diario.** Es la guía que el autor usa a diario; las rutas de ejemplo (`C:\dev-n8n\n8n-personal`)
> son las de su PC: ajústalas si clonas el repositorio en otra carpeta.
> Presentación del proyecto: [`README.md`](../README.md) · Documentación técnica: [`DOCUMENTACION.md`](DOCUMENTACION.md)

# Anki Immersion Pipeline — versión personal

Convierte **un video, un audio o un texto en inglés** en un **mazo de Anki** con tarjetas de oración + voz natural.
Todo corre en tu computadora (GPU RTX 4060), sin pagar APIs.

```
 enlace / video / audio                                          oraciones (.txt)
        │                                                              ▲
        ▼                                                              │
  [00] descargar ──► [01] transcribir ──► mensaje listo ──► chat (Claude / DeepSeek)
      yt-dlp            Whisper large-v3     (portapapeles)         │
                                                                    ▼
                                         [02] voz (Kokoro) ──► [03] mazo .apkg ──► Anki
```

Hay **dos comandos** que usas todos los días: `transcribir` (antes del chat) y `armar` (después del chat).

---

## 1. TU RUTINA DIARIA (empieza aquí)

### 1.1 Abrir el proyecto y revisar el entorno

1. Abre VS Code → **File → Open Folder** → `C:\dev-n8n\n8n-personal`.
2. Abre la terminal (**Ctrl + ñ**) y mira el inicio de la línea:

| Lo que ves                                        | Qué hacer                                                                            |
| ------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `(anki-immersion-pipeline) PS C:\dev-n8n\...>`    | Perfecto, el entorno ya está activo. Sigue al paso 1.2.                              |
| `(base) PS ...` (Anaconda activo)                 | `conda deactivate` (si sigue `(base)`, repítelo) y luego activa el entorno de abajo. |
| `PS ...` sin ningún paréntesis                    | Activa el entorno: `.\.venv\Scripts\Activate.ps1`                                    |
| `(base)` **y** `(anki-immersion-pipeline)` juntos | `conda deactivate` y comprueba que quede solo `(anki-immersion-pipeline)`.           |

```powershell
# Desactivar Anaconda si aparece (base):
conda deactivate

# Activar el entorno del proyecto (si no se activó solo):
.\.venv\Scripts\Activate.ps1

# Desactivar el entorno del proyecto (cuando termines, opcional):
deactivate

# Comprobar que todo está bien (GPU, Whisper, Kokoro, ffmpeg...):
python scripts/check_env.py
```

> Si PowerShell dice que "la ejecución de scripts está deshabilitada" al activar: una sola vez, `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### 1.2 PASO A — Transcribir y preparar el mensaje para el chat

Un comando por mazo. **Pon siempre el enlace entre comillas.** Cada comando: descarga el audio (si es enlace), lo transcribe con Whisper, arma el mensaje completo para la IA y **lo copia al portapapeles**.

**Mazo `aula` — "Inglés Inmersión"** (lo que enseñan en el aula)

```powershell
# Si tienes la grabación de la clase (archivo en tu PC):
python scripts/run.py transcribir "data\input\clase.mp4" --deck aula --n 10

# Si la clase está en un enlace:
python scripts/run.py transcribir "https://www.youtube.com/watch?v=XXXXXXXXXXX" --deck aula --n 10
```

> Si el material del aula es **texto o una foto**: sácale el texto con Google Lens, pégalo en el chat junto con las instrucciones de `prompts\generar_oraciones.md` (mazo: `aula`, 10 oraciones) y sigue en el Paso B. No necesitas Whisper para eso.

**Mazo `blogs` — "Sergii Speaks"**

```powershell
python scripts/run.py transcribir "https://www.youtube.com/watch?v=XXXXXXXXXXX" --deck blogs --n 10
```

**Mazo `podcast` — "TED"**

```powershell
python scripts/run.py transcribir "https://www.youtube.com/watch?v=XXXXXXXXXXX" --deck podcast --n 10
```

Cuando termine verás `COPIADO al portapapeles`. Entonces:

1. Abre el chat (Claude / DeepSeek) y pega con **Ctrl + V**. Envía.
2. La IA te devuelve **un bloque de código** con las oraciones. Cópialo.
3. Pégalo en un archivo nuevo dentro de `data\input\` con un nombre descriptivo, por ejemplo `data\input\blogs_uruguay.txt`.
   La primera línea debe ser `@deck: blogs` (o `aula` / `podcast`); la IA ya la trae. Si faltara, escríbela tú arriba.

> Si el portapapeles falla, el mensaje también queda guardado en `data\transcripts\<nombre>.prompt.txt`: ábrelo, copia todo y pégalo en el chat.

### 1.3 PASO B — Generar audios y el mazo (después de que la IA te entregue las oraciones)

```powershell
python scripts/run.py armar data\input\blogs_uruguay.txt
```

(Cambia el nombre del archivo por el tuyo. El mazo sale de la línea `@deck:` del archivo, no tienes que repetirlo.)

Genera los audios con Kokoro y crea `data\decks\<alias>__<nombre>.apkg`, por ejemplo `data\decks\blogs__blogs_uruguay.apkg`.

### 1.4 PASO C — Importar a Anki

1. Haz **doble clic** en el `.apkg` (o en Anki: **Archivo → Importar**).
2. Las tarjetas se **suman** al mazo existente del mismo nombre; las que ya estaban **no se duplican**.

Eso es todo: **A → chat → B → C**.

### 1.5 Resumen de una línea por mazo

| Mazo (alias) | Nombre en Anki   | Comando del Paso A                                                          |
| ------------ | ---------------- | --------------------------------------------------------------------------- |
| `aula`       | Inglés Inmersión | `python scripts/run.py transcribir "<archivo o enlace>" --deck aula --n 10` |
| `blogs`      | Sergii Speaks    | `python scripts/run.py transcribir "<enlace>" --deck blogs --n 10`          |
| `podcast`    | TED              | `python scripts/run.py transcribir "<enlace>" --deck podcast --n 10`        |

Siempre después: `python scripts/run.py armar data\input\<tu_archivo>.txt` y se importa el `.apkg`.

**`--n`**: cuántas oraciones le pides a la IA. Con 10 tienes el mínimo cómodo; para videos largos (20 min o más) puedes subir a 15–20.

#### Palabras nuevas (opcional)

Si viste en el video una palabra que no conoces y quieres practicarla, **después de pegar el mensaje** (al final, tras la transcripción) escribe una línea así antes de enviar:

```
Palabras: hefty, waive, hang out
```

- **Con esa línea**: la IA mantiene oraciones del video, pero a las que correspondan les suma tus palabras y hasta **3 palabras más** para que suenen naturales. Esas oraciones **cuentan dentro del mínimo** (`--n`). Al final te dice cuáles extendió, cuál era la oración original y qué agregó.
- **Sin esa línea**: todas las oraciones son **fieles al video**, sin agregar nada.
- Si una palabra no encaja de forma natural, la IA no la fuerza y te avisa.
- Tus palabras cambian cada vez; la IA nunca las supone. Funciona igual con el Skill `oraciones-anki-inmersion` y con el mensaje del lanzador.

---

## 2. Cómo funciona por dentro

### 2.1 Las etapas (cada una es un proceso aparte)

Cada etapa carga su modelo, trabaja y **termina**, así Windows libera toda la VRAM antes de la siguiente. El lanzador `run.py` solo las encadena; también puedes correr cada una por separado.

| Etapa | Script                       | Entrada                       | Salida                                                  | Modelo / herramienta             |
| ----- | ---------------------------- | ----------------------------- | ------------------------------------------------------- | -------------------------------- |
| 0     | `scripts/00_download.py`     | enlace                        | `data/input/downloads/<título>_<id>.mp3`                | yt-dlp (+ Deno + ffmpeg)         |
| 1     | `scripts/01_transcribe.py`   | audio / video                 | `data/transcripts/<nombre>.txt` y `.timestamps.txt`     | faster-whisper large-v3, GPU     |
| —     | `scripts/run.py transcribir` | enlace o archivo              | todo lo anterior + `<nombre>.prompt.txt` + portapapeles | `prompts/plantilla_prompt.txt`   |
| 2     | `scripts/02_tts.py`          | archivo de oraciones          | `data/audio/<alias>/<hash>.mp3`                         | Kokoro-82M, GPU                  |
| 3     | `scripts/03_build_deck.py`   | archivo de oraciones + audios | `data/decks/<alias>__<nombre>.apkg`                     | genanki                          |
| —     | `scripts/run.py armar`       | archivo de oraciones          | etapas 2 y 3 seguidas                                   |                                  |
| (1b)  | `scripts/01b_ocr.py`         | fotos                         | `data/transcripts/<nombre>.txt`                         | EasyOCR — **fuera de tu rutina** |

Para correr una etapa suelta, por ejemplo:

```powershell
python scripts/00_download.py "https://www.youtube.com/watch?v=XXXXXXXXXXX"
python scripts/01_transcribe.py "data\input\downloads\archivo.mp3"
python scripts/02_tts.py data\input\blogs_uruguay.txt
python scripts/03_build_deck.py data\input\blogs_uruguay.txt
```

### 2.2 Carpetas

```
C:\dev-n8n\n8n-personal\
├── .venv\                 entorno (lo crea uv; no se toca ni se sube a git)
├── pyproject.toml / uv.lock   dependencias y versiones exactas congeladas
├── vendor\                modelo spaCy guardado localmente (para no depender de GitHub)
├── prompts\
│   ├── plantilla_prompt.txt   mensaje que se pega en el chat (con marcadores {{DECK}} {{N}} {{TEXT}})
│   └── generar_oraciones.md   versión legible + instrucciones (para el caso texto/foto)
├── scripts\               los comandos que ejecutas
├── src\anki_pipeline\     el código reutilizable (config, transcribe, tts, anki_deck, decks, ...)
├── tests\                 27 pruebas automáticas
└── data\                  (ignorado por git)
    ├── input\             tus archivos de oraciones y medios de entrada
    │   └── downloads\     audios descargados de YouTube
    ├── transcripts\       transcripciones y mensajes para el chat
    ├── audio\<alias>\     audios mp3 por mazo (caché: si ya existe, no se regenera)
    ├── decks\             los .apkg finales
    └── tmp\               temporales de prueba
```

**Qué puedes borrar sin problema** cuando quieras liberar espacio: `data\input\downloads\` (los mp3 descargados), `data\transcripts\` y `data\tmp\`.
`data\audio\` también se puede borrar: si vuelves a armar, los audios se regeneran **con los mismos nombres**, así que Anki los reconoce (solo cuesta tiempo).

### 2.3 Formato del archivo de oraciones

```
@deck: blogs
I get lots of newspapers delivered to my house. | Me entregan muchos periódicos en mi casa.
That fee has gone up dramatically. | Esa tarifa ha subido muchísimo.
# esto es un comentario (se ignora)
```

- Una oración por línea: `Inglés | Español`.
- `@deck: <alias>` indica a qué mazo van. Si el alias no existe, da error con la lista de alias válidos.
- Líneas vacías y las que empiezan con `#` se ignoran.
- Si una oración está repetida, se avisa y se usa una sola vez.
- No uses el símbolo `|` dentro de una oración o traducción.
- Cada oración en inglés debe terminar con su puntuación (`.` `?` `!`); si falta, se agrega al generar el audio.

### 2.4 Cómo Anki evita duplicados (importante)

Anki identifica cada tarjeta por un **GUID**. El proyecto lo fabrica siempre igual:

- **Mazo**: su ID sale del nombre del mazo (`config.DECKS`).
- **Tipo de nota** ("Inglés Inmersión (Audio)"): su ID sale de su nombre.
- **Tarjeta**: su GUID sale de _nombre del mazo + oración en inglés normalizada_ (sin importar mayúsculas ni espacios extra).
- **Audio**: el nombre del archivo sale de la oración + voz + velocidad.

Resultado: importar el mismo `.apkg` dos veces no duplica; importar un lote nuevo se suma al mismo mazo (verificado con tus pruebas reales).

Reglas para no romperlo:

1. **No cambies los nombres de los mazos** en `config.DECKS` después de importar (cambiaría los IDs y Anki crearía un mazo nuevo).
2. **No cambies `MODEL_NAME`**, ni los campos o plantillas de la tarjeta. Si algún día los cambias, sube `MODEL_VERSION` en `config.py`.
3. Una misma oración en dos mazos distintos son dos tarjetas distintas (a propósito).

### 2.5 La tarjeta

- **Frente**: la oración en inglés + el audio.
- **Reverso**: la traducción al español.
- Sin colores fijos en el estilo: se ve bien en modo claro y oscuro.

---

## 3. Configuración (`src/anki_pipeline/config.py`)

| Qué             | Valor actual                                          | Nota                                                             |
| --------------- | ----------------------------------------------------- | ---------------------------------------------------------------- |
| Modelo Whisper  | `large-v3`, `float16`                                 | Medido en tu RTX 4060.                                           |
| Lote de Whisper | `WHISPER_BATCH_SIZE = 4`                              | Pico 4.85 GB de VRAM y ~33x tiempo real (batch 1: 5.24 GB y 7x). |
| Beam / idioma   | `5` / `"en"`                                          |                                                                  |
| Voz Kokoro      | `af_heart,af_bella` (mezcla), velocidad `1.0`         | Elegida por tu oído entre varias pruebas.                        |
| Mazos           | `DECKS = {"aula": ..., "blogs": ..., "podcast": ...}` | Ver sección 4.                                                   |
| OCR             | solo inglés, preproceso gris + CLAHE                  | Sin usar en tu rutina personal.                                  |

No cambies la voz ni la velocidad sin necesidad: forman parte del nombre de los audios.

---

## 4. Agregar un mazo nuevo (por ejemplo, otro canal)

1. Abre `src/anki_pipeline/config.py` y agrega una línea en `DECKS`:

```python
DECKS: dict[str, str] = {
    "aula": "Inglés Inmersión",
    "blogs": "Sergii Speaks",
    "podcast": "TED",
    "nuevo": "Nombre del canal",   # alias: minúsculas, sin espacios | nombre: como se verá en Anki
}
```

2. Úsalo: `python scripts/run.py transcribir "<enlace>" --deck nuevo --n 10`
3. Elige el nombre definitivo **antes** del primer import (ver regla 1 de la sección 2.4).

---

## 5. Decisiones técnicas (y por qué)

| Decisión                   | Valor                                         | Razón                                                                                                       |
| -------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Python                     | **3.12** (fijado en `.python-version`)        | Kokoro exige `<3.13`; torch, ctranslate2, easyocr y spaCy tienen versiones maduras. No usar 3.13 ni 3.14.   |
| Gestor                     | **uv** + `uv.lock`                            | El lock congela las versiones exactas: lo que hoy funciona, funciona mañana.                                |
| PyTorch                    | build **CUDA 12.6** (`2.14.1+cu126`)          | Tu RTX 4060 la soporta y CTranslate2 (faster-whisper) necesita CUDA **12**. Driver mínimo: 560.             |
| Whisper                    | `faster-whisper` + `large-v3`, `float16`      | Mismo modelo de OpenAI, ~2x más rápido y menos VRAM (~5 GB de pico; tu GPU tiene ~6.9 GB libres en reposo). |
| Voz                        | Kokoro-82M (licencia Apache-2.0)              | Ligero, rápido y determinista (misma oración = mismo audio).                                                |
| Audio                      | mp3 vía ffmpeg empaquetado (`imageio-ffmpeg`) | No hay que instalar nada en Windows.                                                                        |
| Descarga                   | `yt-dlp[default,deno]`                        | Incluye el runtime JavaScript que YouTube exige hoy.                                                        |
| Etapas separadas           | un proceso por etapa                          | La VRAM se libera entre etapas; un fallo en una no tumba las demás.                                         |
| Proyecto fuera de OneDrive | `C:\dev-n8n\n8n-personal`                     | OneDrive intentaría sincronizar varios GB de librerías.                                                     |
| Topes de versión           | `av<17`, `opencv<5`, `numpy<2.4`              | Evitan que librerías recién salidas rompan otras (ver `pyproject.toml`).                                    |
| Modelo spaCy               | guardado en `vendor/`                         | Kokoro lo necesita y no está en PyPI; así `uv sync` ya no depende de que GitHub responda.                   |

---

## 6. Instalar desde cero (otra PC, o si algo se rompe)

```powershell
# 0) Diagnóstico
nvidia-smi                 # driver >= 560
uv --version               # si no existe:  winget install --id=astral-sh.uv -e   (y abrir terminal nueva)

# 1) Desde la carpeta del proyecto
uv python install 3.12
uv sync                    # crea .venv y descarga todo (varios GB)

# 2) Verificar
python scripts/check_env.py
python scripts/check_env.py --full     # prueba real de Whisper y Kokoro (descarga modelos la primera vez)
```

Notas:

- El proyecto y `.venv` van **fuera de OneDrive**.
- En VS Code el intérprete es `.venv\Scripts\python.exe` (ya configurado en `.vscode/settings.json`).
- `uv sync --group business` agrega psycopg, FastAPI, uvicorn y httpx (dependencias opcionales para exponer el núcleo como servicio; no se usan en el flujo normal).

---

## 7. Pruebas

```powershell
python -m pytest -q
```

Hay 27 pruebas que cubren: formato de la transcripción, lectura de oraciones, nombres de audio, IDs estables de Anki, registro de mazos, validación de enlaces, OCR, el armado del mensaje y las validaciones del lanzador.

---

## 8. Problemas conocidos

| Síntoma                                                     | Causa y solución                                                                                                                                              |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| El enlace da error o dice "URL inválida"                    | Ponlo **entre comillas** y pega **un solo** enlace (no uno dentro de otro).                                                                                   |
| Falla la descarga de YouTube                                | Video privado, borrado, con restricción de país/edad, o yt-dlp desactualizado (YouTube cambia seguido): `uv lock --upgrade-package yt-dlp` y luego `uv sync`. |
| `Library cublas64_12.dll is not found`                      | ctranslate2 no encuentra CUDA 12. Ya se resuelve en el código con `cuda_setup.ensure_cuda_dlls()`; usa siempre los scripts del proyecto.                      |
| `torch ... NO es una build CUDA`                            | uv bajó el torch de CPU. Revisa `[tool.uv.sources]` y corre `uv sync --reinstall-package torch --reinstall-package torchvision`.                              |
| Aviso "unauthenticated requests to the HF Hub"              | Inofensivo: Hugging Face avisa que no usas token. Solo afecta la velocidad de la primera descarga de modelos.                                                 |
| `uv run` falla por un error de red (504) al bajar un modelo | Era el modelo spaCy en GitHub; ahora está en `vendor/`. Si vuelve a pasar, usa `python scripts/...` con el entorno activo (no necesita red).                  |
| Falta de memoria de GPU (CUDA out of memory)                | Cierra programas que usen la GPU (navegador con aceleración, juegos). Si persiste, baja `WHISPER_BATCH_SIZE` a 2 en `config.py`.                              |
| La IA devuelve oraciones sin la línea `@deck:`              | Escríbela tú al inicio del archivo: `@deck: blogs`.                                                                                                           |
| "Alias de mazo desconocido"                                 | El alias no está en `config.DECKS` (¿error de tipeo?). El mensaje de error lista los válidos.                                                                 |
| La tarjeta se ve borrosa en Anki                            | Ya corregido (sin colores fijos). Si importaste una versión vieja, elimina el mazo y el tipo de nota y vuelve a importar.                                     |

---

## 9. Mantenimiento

```powershell
# Actualizar yt-dlp (si YouTube deja de funcionar)
uv lock --upgrade-package yt-dlp
uv sync

# Ver qué ocupa espacio en data\
Get-ChildItem data -Recurse | Measure-Object Length -Sum
```

---

## 10. OCR (queda fuera de tu rutina)

El código de OCR (`scripts/01b_ocr.py`, `src/anki_pipeline/ocr.py`) está guardado y probado, pero para uso personal es mejor **Google Lens** (copia el texto exacto, sin errores de lectura). Se conserva en el código por si se necesita más adelante.
Notas de lo aprendido: solo inglés; la mejor configuración fue gris + CLAHE; binarizar destruía el texto; las imágenes pequeñas dan más errores (el script avisa).

---

## 11. Uso y licencias

- **Kokoro-82M**: pesos con licencia Apache-2.0 (uso comercial permitido).
- **Descargar de YouTube** va contra sus condiciones de servicio: úsalo solo con material que puedes ver legalmente y para tu estudio personal. Para un uso comercial habría que revisar esto aparte.

---

## 12. Ideas a futuro

- Exponer el núcleo (`src/anki_pipeline`) como un servicio HTTP local, para poder llamarlo desde otras herramientas.
- Más de un idioma de estudio (Kokoro y Whisper lo permiten; hoy el proyecto está configurado para inglés).
