"""Paso 1: texto largo -> guion del reel (guion.json) con un modelo abierto.

    python guion.py --texto informe.pdf                       # Qwen3.8-27B local en Mac (MLX, 16 GB)
    python guion.py --texto informe.pdf --motor hf            # Qwen3.8-27B en Hugging Face (requiere créditos)
    python guion.py --texto informe.pdf --solo-prompt > prompt.txt   # para pegarlo en chat.qwen.ai, DeepSeek o Claude
    python guion.py --texto informe.pdf --respuesta respuesta.txt    # verifica lo que respondió el chat

Cualquier modelo sirve si devuelve el JSON del PROMPT. Las cifras se verifican contra el texto fuente.
Va en un entorno aparte de la voz: qwen-tts fija transformers 4.57 y mlx-lm necesita transformers 5.
"""
import argparse
import json
import re
from pathlib import Path

MODELOS = {"mlx": "mlx-community/Qwen3.8-27B-4bit", "hf": "Qwen/Qwen3.8-27B"}
SISTEMA = "Eres periodista de datos. Escribes guiones de reels para leer en voz alta y nunca inventas cifras."

PROMPT = """Texto fuente:
<<<
{texto}
>>>

Escribe el guion de un reel de {segundos} segundos (unas {palabras} palabras en total) en español del Perú,
narrado en primera persona por el autor del texto.

Reglas:
- Entre 5 y 7 escenas. La primera es un gancho; la última cierra con una invitación (ver el tablero, comentar).
- Cada escena tiene una sola idea y como máximo una cifra.
- Usa solo cifras que estén en el texto fuente. No redondees, no inventes y no exageres.
- Si el texto tiene una fecha de corte de los datos, dila en la primera o segunda escena.
- "frase": lo que se dice en voz alta, de 15 a 25 palabras, y debe decir la cifra de su escena.
  No uses dígitos en las frases: escribe todos los números en palabras, también los años
  (por ejemplo "ciento veintiséis por ciento", "dos mil doce").
- "cifra": lo que se ve en pantalla, muy corto, con dígitos (por ejemplo "+126 %", "56", "12,984"). Puede ir vacío.
- "etiqueta": de 3 a 8 palabras que explican la cifra en pantalla. Es lo que lee el público, no una
  descripción de la escena: nunca escribas "gancho", "invitación" ni "cierre". En la última escena, la etiqueta
  es la llamada a la acción tal como se lee (por ejemplo, "Mira el tablero: enlace en mi perfil").

Devuelve solo JSON, sin texto antes ni después, con esta forma:
{{"titulo": "...", "escenas": [{{"frase": "...", "cifra": "...", "etiqueta": "..."}}],
  "hashtags": ["..."], "posts": {{"linkedin": "...", "x": "...", "facebook": "..."}}}}

El "titulo" tiene como máximo 5 palabras. El post de X tiene como máximo 250 caracteres. El de LinkedIn tiene 3 párrafos cortos.
Los tres posts terminan avisando que la voz del video fue generada con IA a partir de la voz del autor."""


def leer(ruta):
    ruta = Path(ruta)
    if ruta.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(ruta).pages)
    return ruta.read_text(encoding="utf-8")


def mensajes(texto, segundos=50):
    return [{"role": "system", "content": SISTEMA},
            {"role": "user", "content": PROMPT.format(texto=texto, segundos=segundos, palabras=int(segundos * 2.5))}]


def generar(msgs, motor="mlx", modelo=None):
    modelo = modelo or MODELOS[motor]
    if motor == "hf":
        from huggingface_hub import InferenceClient
        r = InferenceClient(provider="auto").chat_completion(model=modelo, messages=msgs, max_tokens=4000, temperature=0.4)
        return r.choices[0].message.content
    from mlx_lm import generate, load
    from mlx_lm.sample_utils import make_sampler
    llm, tok = load(modelo)
    prompt = tok.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False)
    return generate(llm, tok, prompt, max_tokens=4000, sampler=make_sampler(temp=0.4))


def a_guion(salida, texto):
    """Extrae el JSON de la respuesta y marca qué cifras aparecen tal cual en el texto fuente."""
    salida = re.sub(r"<think>.*?</think>", "", salida, flags=re.S)
    guion = json.loads(salida[salida.find("{"): salida.rfind("}") + 1])
    fuente = _numeros(texto)
    for e in guion["escenas"]:
        e["cifra_en_texto"] = all(n in fuente for n in _numeros(e.get("cifra", "")))
    guion["cifras_dudosas_en_posts"] = sorted(set().union(*map(_numeros, guion["posts"].values())) - fuente)
    return guion


def _numeros(s):
    """Números de un texto sin separadores de miles: '12,984' y '12984' cuentan igual."""
    return {re.sub(r"[,\s]", "", n) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", s)}


if __name__ == "__main__":
    import time

    p = argparse.ArgumentParser()
    p.add_argument("--texto", required=True)
    p.add_argument("--segundos", type=int, default=50)
    p.add_argument("--motor", default="mlx", choices=list(MODELOS))
    p.add_argument("--modelo")
    p.add_argument("--salida", default=str(Path(__file__).parent / "salidas" / "guion.json"))
    p.add_argument("--solo-prompt", action="store_true")
    p.add_argument("--respuesta", help="archivo con la respuesta que dio el chat al prompt")
    a = p.parse_args()

    texto = leer(a.texto)
    msgs = mensajes(texto, a.segundos)
    if a.solo_prompt:
        print(msgs[0]["content"] + "\n\n" + msgs[1]["content"])
        raise SystemExit
    t = time.time()
    if a.respuesta:
        a.modelo = f"la respuesta de {a.respuesta}"
        guion = a_guion(Path(a.respuesta).read_text(encoding="utf-8"), texto)
    else:
        guion = a_guion(generar(msgs, a.motor, a.modelo), texto)
    Path(a.salida).parent.mkdir(exist_ok=True)
    Path(a.salida).write_text(json.dumps(guion, ensure_ascii=False, indent=2))
    print(f"{len(texto.split()):,} palabras -> {len(guion['escenas'])} escenas en {time.time() - t:.0f} s con {a.modelo or MODELOS[a.motor]}")
    for e in guion["escenas"]:
        print(f"  {'ok' if e['cifra_en_texto'] else '¡¡'} {e['cifra'] or '-':>10} | {e['frase']}")
    if guion["cifras_dudosas_en_posts"]:
        print("  Cifras de los posts que no están en el texto:", ", ".join(guion["cifras_dudosas_en_posts"]))
