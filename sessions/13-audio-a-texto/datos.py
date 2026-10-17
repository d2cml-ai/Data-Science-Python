"""Descarga los audios de la sesión 13. Todos tienen licencia libre y se citan abajo.

    uv run python sessions/13-audio-a-texto/datos.py

Qué baja (unos 60 MB en total) a sessions/13-audio-a-texto/data/:

- Español peruano leído, con transcripción: OpenSLR 73, "Crowdsourced high-quality Peruvian
  Spanish speech data set" (Google, CC BY-SA 4.0). Solo se bajan las frases elegidas, no los
  900 MB de cada zip: se leen por partes con peticiones HTTP Range.
- Inglés leído, con transcripción: FLEURS (Google, CC BY 4.0), también leído por partes.
- Entrevistas reales de Wikimedia Commons (CC BY-SA 4.0): calle en El Agustino (Lima), una
  dirigente de Fenmucarinap, saberes de plantas medicinales en quechua de Huaylas (Shansha,
  Áncash) y una historia oral en inglés (Minnesota State University, Mankato).
"""
import io
import math
import random
import tarfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf
from scipy.signal import resample_poly

CARPETA = Path(__file__).resolve().parent / "data"
SR = 16_000
UA = {"User-Agent": "ds-python-up/2026 (https://github.com/d2cml-ai/Data-Science-Python)"}

# nombre local: (archivo en Commons, autor, idioma, descripción corta)
COMMONS = {
    "agustino_1.ogg": ("Entrevista 1 en la Av. Rivagüero - El Agustino.ogg",
                       "JorgeFlores-pe (Wikimedia Perú)", "es",
                       "Entrevista en la calle a una vendedora de frutas, previa del repechaje Perú-Australia (2022)"),
    "agustino_2.ogg": ("Entrevista 2 en la Av. Rivagüero - El Agustino.ogg",
                       "JorgeFlores-pe (Wikimedia Perú)", "es",
                       "Entrevista en la calle a dos vendedoras de dulces, mismo día"),
    "aurora_coronado.ogg": ("Entrevista-Aurora Coronado-organización de mujeres indígenas-fiestas patrias.ogg",
                            "QM Keen", "es",
                            "Dirigente de Fenmucarinap (sierra central) durante una conferencia de prensa (2022)"),
    "shansha_elena.ogg": ("Elena Figueroa - Entrevista sobre Españolada, Shansha, Áncash, Perú.ogg",
                          "Figuemijun (proyecto Voces y plantas – Qurakuna Rimaykuy)", "qwh",
                          "Entrevista en quechua de Huaylas sobre una planta medicinal (2026)"),
    "shansha_maricela.ogg": ("Maricela Figueroa - Entrevista sobre Aurinsha, Shansha, Áncash, Perú.ogg",
                             "Figuemijun (proyecto Voces y plantas – Qurakuna Rimaykuy)", "qwh",
                             "Entrevista en quechua de Huaylas sobre una planta medicinal (2026)"),
    "historia_oral_glines.ogg": ("Dr. Don E. Glines 2012 Oral History Interview Part Two.ogg",
                                 "Don E. Glines, Heather Harren (Minnesota State University, Mankato)", "en",
                                 "Historia oral de un docente de la Wilson Campus School (2012)"),
}

OPENSLR73 = "https://www.openslr.org/resources/73/es_pe_{sexo}.zip"
FLEURS = "https://huggingface.co/datasets/google/fleurs/resolve/main/data/"


def _get(url, rango=None):
    cab = dict(UA)
    if rango:
        cab["Range"] = f"bytes={rango[0]}-{rango[1]}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=cab), timeout=120) as r:
        return r.read()


class ZipRemoto(io.RawIOBase):
    """Archivo remoto que se lee por partes (HTTP Range): zipfile solo pide los bytes que necesita."""

    BLOQUE = 1 << 20  # zipfile hace muchas lecturas chicas: pedimos de a 1 MB y guardamos lo leído

    def __init__(self, url):
        self.url, self.pos, self.buf_ini, self.buf = url, 0, 0, b""
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA, method="HEAD"), timeout=60) as r:
            self.size = int(r.headers["Content-Length"])

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = {0: offset, 1: self.pos + offset, 2: self.size + offset}[whence]
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = min(n, self.size - self.pos)
        if n <= 0:
            return b""
        fin = self.pos + n
        if not (self.buf_ini <= self.pos and fin <= self.buf_ini + len(self.buf)):
            self.buf_ini = self.pos
            self.buf = _get(self.url, (self.pos, min(self.pos + max(n, self.BLOQUE), self.size) - 1))
        datos = self.buf[self.pos - self.buf_ini:fin - self.buf_ini]
        self.pos += len(datos)
        return datos


def _guardar_16k(contenido, ruta):
    """WAV en bytes -> WAV mono de 16 kHz (la frecuencia que esperan los modelos de voz)."""
    x, sr = sf.read(io.BytesIO(contenido), dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    if sr != SR:
        g = math.gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g).astype("float32")
    sf.write(ruta, x, SR)


def bajar_commons():
    """Entrevistas de Wikimedia Commons. Devuelve una tabla con la atribución de cada audio."""
    destino = CARPETA / "entrevistas"
    destino.mkdir(parents=True, exist_ok=True)
    filas = []
    for local, (titulo, autor, idioma, desc) in COMMONS.items():
        ruta = destino / local
        url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(titulo)
        if not ruta.exists():
            ruta.write_bytes(_get(url))
        filas.append({"archivo": local, "idioma": idioma, "descripcion": desc, "autor": autor,
                      "licencia": "CC BY-SA 4.0",
                      "fuente": "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(titulo.replace(" ", "_"))})
    tabla = pd.DataFrame(filas)
    tabla.to_csv(destino / "atribucion.csv", index=False)
    return tabla


def bajar_openslr73(n_por_sexo=12, semilla=7):
    """Frases de español peruano leído, una por hablante, con su transcripción oficial."""
    destino = CARPETA / "es_peru"
    destino.mkdir(parents=True, exist_ok=True)
    indice = destino / "transcripciones.csv"
    if indice.exists():
        return pd.read_csv(indice)
    filas = []
    for sexo in ["female", "male"]:
        z = zipfile.ZipFile(ZipRemoto(OPENSLR73.format(sexo=sexo)))
        lineas = z.read("line_index.tsv").decode("utf-8").strip().splitlines()
        tabla = pd.DataFrame([l.split("\t") for l in lineas], columns=["id", "texto"])
        tabla["hablante"] = tabla["id"].str.rsplit("_", n=1).str[0]
        # una frase por hablante, de entre 6 y 20 palabras, elegida al azar con semilla fija
        tabla = tabla[tabla["texto"].str.split().str.len().between(6, 20)]
        rng = random.Random(semilla)
        hablantes = sorted(tabla["hablante"].unique())
        rng.shuffle(hablantes)
        for h in hablantes[:n_por_sexo]:
            fila = tabla[tabla["hablante"] == h].sample(1, random_state=semilla).iloc[0]
            _guardar_16k(z.read(f"{fila['id']}.wav"), destino / f"{fila['id']}.wav")
            filas.append({"archivo": f"{fila['id']}.wav", "texto": fila["texto"].strip(),
                          "hablante": h, "sexo": "mujer" if sexo == "female" else "hombre"})
        # para la entrevista simulada: varias frases de un hablante de cada sexo
        h = hablantes[n_por_sexo]
        for _, fila in tabla[tabla["hablante"] == h].head(8).iterrows():
            _guardar_16k(z.read(f"{fila['id']}.wav"), destino / f"{fila['id']}.wav")
            filas.append({"archivo": f"{fila['id']}.wav", "texto": fila["texto"].strip(),
                          "hablante": h, "sexo": "mujer" if sexo == "female" else "hombre", "rol": "entrevista"})
    tabla = pd.DataFrame(filas)
    tabla["rol"] = tabla.get("rol", pd.Series(dtype=str)).fillna("evaluacion")
    tabla.to_csv(indice, index=False)
    return tabla


def bajar_fleurs_en(n=12):
    """Frases de inglés leído (FLEURS, Google, CC BY 4.0), con transcripción oficial.

    El audio viene en un .tar.gz de 289 MB, pero se lee como flujo y se corta apenas
    tenemos n frases distintas: solo se bajan unos pocos MB.
    """
    destino = CARPETA / "en_fleurs"
    destino.mkdir(parents=True, exist_ok=True)
    indice = destino / "transcripciones.csv"
    if indice.exists():
        return pd.read_csv(indice)
    tsv = _get(FLEURS + "en_us/test.tsv").decode("utf-8").strip().splitlines()
    meta = {c[1]: (c[0], c[2], c[6] if len(c) > 6 else "") for c in (l.split("\t") for l in tsv)}
    filas, frases = [], set()
    pedido = urllib.request.Request(FLEURS + "en_us/audio/test.tar.gz", headers=UA)
    with urllib.request.urlopen(pedido, timeout=120) as r, tarfile.open(fileobj=r, mode="r|gz") as tar:
        for m in tar:
            nombre = Path(m.name).name
            if not m.isfile() or nombre not in meta or meta[nombre][0] in frases:
                continue
            frase, texto, genero = meta[nombre]
            _guardar_16k(tar.extractfile(m).read(), destino / nombre)
            frases.add(frase)
            filas.append({"archivo": nombre, "texto": texto, "sexo": {"MALE": "hombre", "FEMALE": "mujer"}.get(genero, genero)})
            if len(filas) == n:
                break
    tabla = pd.DataFrame(filas)
    tabla.to_csv(indice, index=False)
    return tabla


def entrevista_simulada(pausa=0.7):
    """Une frases reales de dos hablantes peruanos, alternando turnos, y guarda quién habla cuándo.

    Como sabemos la verdad (texto y hablante de cada tramo), sirve para medir la diarización.
    """
    destino = CARPETA / "es_peru"
    wav, verdad = destino / "entrevista_simulada.wav", destino / "entrevista_simulada.csv"
    if wav.exists() and verdad.exists():
        return wav, pd.read_csv(verdad)
    tabla = bajar_openslr73()
    turnos = tabla[tabla["rol"] == "entrevista"]
    a, b = [g for _, g in turnos.groupby("sexo")]
    orden = [f for par in zip(a.itertuples(), b.itertuples()) for f in par]
    audio, filas, t = [], [], 0.0
    silencio = np.zeros(int(pausa * SR), dtype=np.float32)
    for f in orden:
        x, sr = sf.read(destino / f.archivo, dtype="float32")
        if sr != SR:
            raise ValueError(f"{f.archivo}: se esperaba 16 kHz y vino {sr}")
        filas.append({"inicio": round(t, 2), "fin": round(t + len(x) / SR, 2),
                      "hablante": "Entrevistadora" if f.sexo == "mujer" else "Entrevistado", "texto": f.texto})
        audio += [x, silencio]
        t += (len(x) + len(silencio)) / SR
    sf.write(wav, np.concatenate(audio), SR)
    pd.DataFrame(filas).to_csv(verdad, index=False)
    return wav, pd.DataFrame(filas)


if __name__ == "__main__":
    print(bajar_commons()[["archivo", "idioma", "descripcion"]].to_string(index=False))
    es = bajar_openslr73()
    print(f"\nEspañol peruano: {len(es)} frases de {es['hablante'].nunique()} hablantes")
    en = bajar_fleurs_en()
    print(f"Inglés: {len(en)} frases distintas")
    wav, verdad = entrevista_simulada()
    print(f"Entrevista simulada: {verdad['fin'].max():.0f} s, {len(verdad)} turnos -> {wav}")
    total = sum(p.stat().st_size for p in CARPETA.rglob("*") if p.is_file())
    print(f"\nTotal en {CARPETA}: {total / 1e6:.0f} MB")
