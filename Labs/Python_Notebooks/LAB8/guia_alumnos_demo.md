# 📘 Guía paso a paso para correr el proyecto desde CMD (Windows)

- ✅ Sistema operativo: **Windows 10 / 11**
- ✅ Terminal: **Símbolo del sistema (CMD)**
- ✅ Python: **3.10 o superior**
- ✅ Editor del notebook: **Jupyter Notebook en el navegador**
- ✅ Sin Docker · Sin claves embebidas · Sin servicios extra

---

## 📋 Checklist de prerrequisitos

Antes de empezar, verifica que tienes:

- [ ] **Python 3.10+** instalado (más abajo se valida)
- [ ] **Conexión estable a internet** (Gemini + traductor lo necesitan)
- [ ] **API Key de Gemini** lista o cuenta de Google para crearla
- [ ] **Un documento PDF corto** para usar en la demo (5–30 páginas)

---

## 🪟 PARTE 1 — Abrir CMD y verificar Python

### 1.1 — Abrir CMD

Hay tres formas, usa la que prefieras:

- Pulsa `Win + R`, escribe `cmd` y presiona **Enter**.
- Pulsa la tecla **Windows**, escribe `cmd` y haz clic en **Símbolo del sistema**.
- Pulsa `Win + X` y elige **Terminal** (en Windows 11 abre por defecto PowerShell; arriba a la derecha cambia a *Símbolo del sistema*).

### 1.2 — Verificar la versión de Python

En la ventana de CMD escribe:

```cmd
python --version
```

Resultado esperado:

```
Python 3.10.x
```

> 🚨 **Si dice `'python' no se reconoce como un comando…`** → instala Python desde <https://www.python.org/downloads/> y, **muy importante**, marca la casilla **“Add python.exe to PATH”** durante la instalación. Cierra y abre CMD de nuevo después de instalarlo.

### 1.3 — Verificar pip

```cmd
pip --version
```

Debe responder con la versión de pip y la ruta donde está instalado. Si falla, vuelve al paso anterior.

---

## 📂 PARTE 2 — Preparar la carpeta del proyecto

### 2.1 — Crear una carpeta de trabajo

Vamos a usar `C:\Users\TU_USUARIO\Documents\rag-demo`. Si tu usuario es distinto, ajusta el nombre.

En CMD ejecuta (una línea a la vez):

```cmd
cd %USERPROFILE%\Documents
mkdir rag-demo
cd rag-demo
```

> 💡 `%USERPROFILE%` es una variable que apunta a tu carpeta de usuario, sea cual sea (`C:\Users\Juan`, `C:\Users\Maria`, etc.). **No hace falta cambiarla.**

### 2.2 — Copiar los archivos del proyecto

Copia dentro de `C:\Users\TU_USUARIO\Documents\rag-demo` los archivos que te entregó el profesor:

```
📁 rag-demo
└── 📔 RAG_documento_demo.ipynb
```

(Si recibiste un `.zip`, click derecho → **Extraer todo…** → selecciona la carpeta `rag-demo`.)

### 2.3 — Verificar que el notebook está ahí

```cmd
dir
```

Debe aparecer en el listado el archivo `RAG_documento_demo.ipynb`.

---

## 🐍 PARTE 3 — Crear y activar el entorno virtual

> 💡 **¿Qué es un entorno virtual?** Es un Python aislado solo para este proyecto. Las librerías que instales aquí no afectan a otros proyectos de tu PC.

### 3.1 — Crear el venv

Asegúrate de que el prompt está en la carpeta correcta (debe terminar en `…\rag-demo>`). Ejecuta:

```cmd
python -m venv venv
```

Esto tarda unos 10–15 segundos y crea una carpeta nueva llamada `venv\` dentro del proyecto.

### 3.2 — Activar el venv

```cmd
venv\Scripts\activate
```

Si todo va bien, el prompt cambia a:

```
(venv) C:\Users\TU_USUARIO\Documents\rag-demo>
```

> 🟢 **Mientras veas `(venv)` al principio, estás dentro del entorno virtual.**

> 🚨 **Si ves un error de “execution policy”** → eso solo pasa en PowerShell. En **CMD** no debería ocurrir. Verifica que estás efectivamente en el *Símbolo del sistema* y no en PowerShell.

### 3.3 — Desactivar el venv (cuando termines)

Cuando ya no quieras usar el proyecto, basta con:

```cmd
deactivate
```

---

## 📦 PARTE 4 — Instalar las dependencias

Con el `(venv)` activo, instala todas las librerías necesarias:

```cmd
pip install pypdf tiktoken langchain-text-splitters deep-translator google-genai chromadb ipywidgets tqdm python-dotenv notebook
```

⏱️ Tarda **3–5 minutos** dependiendo de tu conexión. Verás muchas líneas de descarga.

Al final debe aparecer un mensaje similar a:

```
Successfully installed chromadb-... deep-translator-... google-genai-... notebook-...
```

### 4.1 — Verificar la instalación

```cmd
pip list | findstr /I "chromadb google-genai deep-translator pypdf notebook"
```

Debes ver las cinco librerías listadas con sus versiones. Si falta alguna, repite el `pip install` correspondiente.

---

## 🔑 PARTE 5 — Obtener tu API Key de Gemini

### 5.1 — Generar la clave

1. Abre el navegador y ve a 👉 <https://aistudio.google.com/app/apikey>
2. Inicia sesión con tu cuenta de Google.
3. Haz clic en **“Create API key”** (botón azul).
4. Selecciona o crea un proyecto.
5. Copia la cadena que empieza con `AIzaSy…` (39 caracteres aprox.).

> 🔒 **Guárdala en un lugar seguro** (un bloc de notas, gestor de contraseñas…). **No la subas a GitHub** y **no la compartas** con nadie.

### 5.2 — ¿Dónde se ingresa la clave?

En este proyecto la clave se pega **directamente al ejecutar la celda del Paso 1 del notebook**. Cuando hagas `Ctrl + Enter` en esa celda, aparecerá un campo donde tendrás que pegar la API Key. **No se guarda en ningún archivo, no queda escrita en pantalla.**

> 💡 **Opcional (avanzado):** si no quieres pegarla cada vez, puedes crear un archivo llamado `.env` dentro de la carpeta `rag-demo` con la línea:
>
> ```
> GEMINI_API_KEY=AIzaSy_tu_clave_real_aqui
> ```
>
> El notebook lo detectará y no te pedirá la clave. **Pero esto es opcional**. Para la clase, lo más sencillo es pegarla cuando aparezca el prompt.

---

## 📄 PARTE 6 — Preparar el documento PDF de la demostración

### 6.1 — Elegir un PDF corto

Para esta demo conviene un PDF de **entre 5 y 30 páginas**: un artículo, un capítulo, un manual, una nota técnica… Si es muy largo, la indexación tarda más.

### 6.2 — Copiar el PDF a la carpeta del proyecto

Lo más sencillo es **dejar el PDF dentro de la propia carpeta `rag-demo`** y renombrarlo a `documento_demo.pdf`. Así el notebook lo encuentra sin tener que tocar rutas.

Desde CMD puedes copiarlo con:

```cmd
copy "C:\Users\TU_USUARIO\Downloads\mi_archivo.pdf" "%CD%\documento_demo.pdf"
```

> 💡 `%CD%` es la carpeta actual. Asegúrate de estar en `…\rag-demo>` antes de ejecutar el `copy`.

Verifica que se copió:

```cmd
dir documento_demo.pdf
```

---

## 📔 PARTE 7 — Abrir el notebook desde CMD

Con el `(venv)` activo y dentro de la carpeta del proyecto, lanza Jupyter:

```cmd
jupyter notebook
```

Sucederán dos cosas:

1. En la propia consola CMD verás logs del servidor.
2. **Tu navegador se abrirá automáticamente** mostrando la lista de archivos de la carpeta.

> 🚨 **Si el navegador no se abre solo**, busca en la consola una línea parecida a:
> ```
> http://localhost:8888/tree?token=…
> ```
> Cópiala y pégala manualmente en tu navegador.

### 7.1 — Abrir el notebook

En la página del navegador:

1. Haz clic sobre `RAG_documento_demo.ipynb`.
2. El notebook se abrirá en una pestaña nueva.

### 7.2 — Verificar el kernel

En la esquina superior derecha del notebook debería aparecer **“Python 3 (ipykernel)”** o similar. Si dice **“No Kernel”**, haz clic ahí y selecciona **Python 3**.

> ⚠️ **Importante:** No cierres la ventana de CMD mientras uses el notebook. Si la cierras, el servidor de Jupyter se detiene y el notebook deja de funcionar. Para **detener el servidor** (cuando termines), vuelve a CMD y presiona `Ctrl + C` dos veces.

---

## ▶️ PARTE 8 — Ejecutar el notebook celda por celda

> 🎯 **Atajo clave:** `Shift + Enter` ejecuta la celda actual y avanza a la siguiente. `Ctrl + Enter` la ejecuta sin avanzar.

Vas a recorrer los **11 pasos en orden**, de arriba hacia abajo. Esto es lo que esperar en cada uno:

### Paso 0 — Preparación del entorno
Solo es una celda con un `pip install` comentado. **No la ejecutes** si ya hiciste el `pip install` de la Parte 4.

### Paso 1 — Carga segura de la API Key
**Lo que vas a ver al ejecutar la celda con `Ctrl + Enter`:**

```
🔑 Pega tu API Key de Gemini y presiona Enter (no se mostrará por seguridad):
   GEMINI_API_KEY ➜ █
```

Pega aquí tu clave (no se mostrará en pantalla — es normal). Presiona **Enter**. Resultado:

```
✅ Clave cargada correctamente — longitud: 39 caracteres.
```

> 🚨 Si dejas el campo vacío y das Enter, te dará `AssertionError`. Vuelve a ejecutar la celda y pega bien la clave.

### Paso 2 — Verificación del traductor
**Lo que ves:**

```
✅ Traductor operativo.
   Entrada : Knowledge is power.
   Salida  : El conocimiento es poder.
```

> 🚨 Si falla con error de conexión: revisa tu internet. Algunas redes corporativas o universitarias **bloquean Google Translate**; en ese caso, prueba con otra red (móvil, casa).

### Paso 3 — Lectura del documento PDF
⏱️ ~5 segundos para un PDF corto.

**Lo que ves:**

```
📄 Páginas detectadas: 18
📊 Caracteres totales : 42,150
📊 Palabras aprox.    : 6,820
🔍 Vista previa (primeros 400 caracteres):
------------------------------------------------------------
[texto del documento]
------------------------------------------------------------
```

> 🚨 Si da `FileNotFoundError`: la ruta del PDF está mal. Revisa la línea `DOCUMENT_PATH = r"./documento_demo.pdf"` y comprueba que el archivo existe con ese nombre exacto en la carpeta del proyecto.

### Paso 4 — Conteo de tokens
**Lo que ves:**

```
🔢 Tokens del documento : 9,420
📏 Límite por petición  : 8 192 tokens (gemini-embedding-001)
➡️  Por eso lo dividiremos en fragmentos en el siguiente paso.
```

### Paso 5 — Segmentación en fragmentos
⏱️ ~2 segundos.

**Lo que ves:**

```
✂️  Fragmentos generados : 48
📐 Tamaño objetivo       : 200 tokens (con 25 de solapamiento)

🔍 Ejemplo — fragmento #3 (texto original):
------------------------------------------------------------
[fragmento de texto en inglés u original]
------------------------------------------------------------
```

### Paso 6 — Traducción al español 🌍
⏱️ Para un documento corto: **30 segundos – 2 minutos**.

**Lo que ves:** una barra de progreso `tqdm`:

```
🌍 Traduciendo EN→ES: 100%|████████| 48/48 [00:45<00:00]
💾 48 traducciones guardadas en 'segments_cache.pkl'.
```

> 💾 Se guarda automáticamente en `segments_cache.pkl`. **Si repites la demo después, este paso será instantáneo** (la próxima vez detecta la caché y no traduce de nuevo).
>
> 🚨 Si Google Translate frena con muchos errores: detén la celda con el botón cuadrado ⏹️, espera 2–3 minutos y vuelve a ejecutar. Continuará desde donde se quedó.

### Paso 7 — Configuración de embeddings
⏱️ Inmediato.

**Lo que ves:**

```
✅ Embeddings listos.
   • Modelo       : gemini-embedding-001
   • Dimensiones  : 768
   • Throttling   : 1 petición cada 1.1s (~54 por minuto)
```

### Paso 8 — Base vectorial ChromaDB
⏱️ ~2 segundos.

**Lo que ves:**

```
📦 Colección activa : 'rag_demo_collection'
📍 Persistencia en  : ./chroma_storage
🔢 Documentos hoy   : 0
```

### Paso 9 — Indexación con embeddings 📥
⏱️ Para un documento corto: **1–2 minutos** (depende del número de fragmentos).

**Lo que ves:**

```
📥 Se indexarán 48 fragmentos nuevos.
   Tiempo estimado: ~0.9 minutos.

📥 Indexando: 100%|████████| 5/5 [00:53<00:00]

✅ Indexado completo. Total en colección: 48
```

> 💡 **Si vuelves a ejecutar esta celda después**, detectará que ya están indexados y no repetirá el trabajo: `♻️  La colección ya contiene 48 fragmentos. No se reindexa.`
>
> 🚨 Si te da error `RESOURCE_EXHAUSTED` o `429`: llegaste al rate limit del free tier. El código tiene reintentos automáticos. Si insiste, espera 1 minuto y vuelve a ejecutar la celda — continuará desde donde quedó.

### Paso 10 — Prueba del pipeline RAG
⏱️ ~5 segundos.

**Lo que ves:**

```
🧪 Prueba rápida del pipeline RAG

📝 RESPUESTA:
[respuesta generada por Gemini sobre el contenido del documento]

📚 FUENTES (top 3):
   1. distancia=0.3520 → [fragmento del documento]…
   2. distancia=0.4108 → [fragmento del documento]…
   3. distancia=0.4633 → [fragmento del documento]…
```

### Paso 11 — Interfaz interactiva 🎨
**Lo que ves:** una caja morada con el título *“Asistente RAG sobre tu documento”*, un campo de texto, un slider de fragmentos, y dos botones (🚀 Preguntar y 🧹 Limpiar).

> 🚨 **Si NO aparece la interfaz** y solo ves `VBox(children=…)`: presiona en el menú del notebook **Kernel → Restart Kernel**, y luego haz **Cell → Run All**. Como hay caché, se llega rápido al Paso 11 otra vez.

---

## 💬 PARTE 9 — Hacer preguntas al documento

Una vez veas la caja morada del Paso 11:

1. **Click** dentro del campo de texto.
2. **Escribe** tu pregunta. Algunas ideas:
   - *¿De qué trata este documento?*
   - *¿Cuáles son las ideas principales?*
   - *Resume el apartado sobre [tema X].*
   - *¿Qué conclusiones plantea el autor?*
3. **Ajusta el slider** “Fragmentos a recuperar” (4 está bien para empezar).
4. Haz click en **🚀 Preguntar**.
5. Espera 2–3 segundos.
6. Verás:
   - Tu pregunta
   - La respuesta generada por Gemini, basada solo en el documento
   - Los fragmentos que se consultaron (haz click en cada uno para expandirlo)

> 💡 **Las preguntas son ilimitadas** una vez indexado el documento. Cada pregunta cuesta ~2 peticiones de Gemini (búsqueda + generación), bien dentro del free tier.

---

## 🔄 PARTE 10 — Cómo retomar el trabajo otro día

Cuando vuelvas mañana o más tarde:

1. **Abre CMD.**
2. Ve a la carpeta del proyecto:
   ```cmd
   cd %USERPROFILE%\Documents\rag-demo
   ```
3. Activa el venv:
   ```cmd
   venv\Scripts\activate
   ```
4. Lanza Jupyter:
   ```cmd
   jupyter notebook
   ```
5. Abre `RAG_documento_demo.ipynb` desde el navegador.
6. Menú **Cell → Run All**.
   - Pasos 0-5: ~10 segundos
   - Paso 6 detecta `segments_cache.pkl` → instantáneo
   - Paso 9 detecta que ChromaDB ya está poblado → instantáneo
   - Llegas al Paso 11 en ~30 segundos y ya puedes preguntar.

> 🔑 Solo deberás volver a pegar la API Key en el Paso 1 (no se guarda).

---

## 🩺 PARTE 11 — Troubleshooting (errores comunes)

### ❌ `'python' no se reconoce como un comando interno…`
Python no está en el PATH. Reinstálalo desde <https://www.python.org/downloads/> marcando **“Add python.exe to PATH”**. Cierra y abre CMD.

### ❌ `'pip' no se reconoce como un comando…`
Lo mismo de arriba. Si Python sí responde pero pip no, prueba:
```cmd
python -m pip install --upgrade pip
```

### ❌ `'jupyter' no se reconoce como un comando…`
Te falta instalarlo o no activaste el venv. Verifica que tu prompt comienza con `(venv)` y luego ejecuta:
```cmd
pip install notebook
```

### ❌ El navegador no se abre al ejecutar `jupyter notebook`
Busca en la consola una línea con `http://localhost:8888/tree?token=…` y pégala manualmente en tu navegador.

### ❌ `ModuleNotFoundError: No module named 'google.genai'` (u otra librería)
No estás dentro del venv o no instalaste las dependencias. Verifica que el prompt empieza con `(venv)` y vuelve a ejecutar el `pip install` de la Parte 4.

### ❌ Paso 1: `AssertionError` o el campo de la clave queda vacío
Diste Enter sin pegar la clave. Vuelve a ejecutar la celda y esta vez pégala antes de presionar Enter.

### ❌ Paso 3: `FileNotFoundError`
La ruta del PDF está mal. Asegúrate de que el PDF se llama `documento_demo.pdf` y está en la misma carpeta que el notebook. Si quieres usar otra ruta, edita la variable `DOCUMENT_PATH` del Paso 3.

### ❌ Paso 6: el traductor falla constantemente
- Tu IP puede estar temporalmente limitada por hacer demasiadas peticiones. Espera 10–15 minutos.
- O aumenta el `DELAY_BETWEEN_CALLS` del Paso 6 de `0.25` a `1.0` (más lento, más estable).
- Verifica que la red no bloquea Google Translate.

### ❌ Paso 9: `RESOURCE_EXHAUSTED` o `429 Too Many Requests`
Excediste el rate limit de Gemini. El código reintenta solo. Si insiste, espera 1 minuto y vuelve a ejecutar la celda — retomará el indexado donde se quedó.

### ❌ Paso 9: `Quota exceeded for the day`
Llegaste al límite diario del free tier. Espera 24 h o usa otra cuenta. **Lo que ya se indexó queda guardado** en `chroma_storage`.

### ❌ Paso 11: La UI aparece como `VBox(children=…)` o no se renderiza
1. En el menú del notebook → **Kernel → Restart Kernel**.
2. Luego → **Cell → Run All**.
3. Como hay caché, llegas rápido al Paso 11 con la UI bien renderizada.

### ❌ `Permission denied` al instalar paquetes
Probablemente no activaste el venv. Verifica el `(venv)` en el prompt. Si no está:
```cmd
venv\Scripts\activate
```

### ❌ Detener el servidor de Jupyter
Vuelve a la ventana de CMD donde lanzaste `jupyter notebook` y presiona `Ctrl + C` dos veces.

---

## ✅ Checklist final antes de empezar

Antes de ejecutar el notebook por primera vez, confirma:

- [ ] Estás en CMD, dentro de `…\rag-demo>` y ves `(venv)` al inicio del prompt
- [ ] `pip list` muestra `google-genai`, `chromadb`, `deep-translator`, `pypdf`, `notebook`
- [ ] El archivo `documento_demo.pdf` existe dentro de la carpeta del proyecto
- [ ] Tienes a mano tu API Key de Gemini (39 caracteres)
- [ ] Tu conexión a internet es estable
- [ ] El navegador abrió correctamente el notebook

Si todos están marcados → **dale `Cell → Run All`** y a disfrutar 🚀.

---

## 📊 Tiempo total estimado (primera vez)

| Etapa | Tiempo |
|---|---|
| Setup (Partes 1–7) | ~10 minutos |
| Pasos 0–5 del notebook | ~30 segundos |
| Paso 6 (traducción) | ~30 s – 2 min |
| Pasos 7–8 | ~5 segundos |
| Paso 9 (indexado con embeddings) | ~1–2 minutos |
| Pasos 10–11 + primera pregunta | ~10 segundos |
| **TOTAL primera vez** | **~15–18 minutos** |
| **Veces siguientes** | **~1 minuto** (todo cacheado) |

---

## 🆘 ¿Algo no funcionó?

Copia el **mensaje de error completo** (incluyendo el trace de arriba abajo) y compártelo con el profesor o el compañero que te apoya. Con el error a la vista se resuelve mucho más rápido.

¡Mucho éxito con la demostración! 🎓
