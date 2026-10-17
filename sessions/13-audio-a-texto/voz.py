"""Herramientas de la sesión 13: de audio a texto, solo con modelos abiertos y locales.

Lo usan el notebook de la clase, la app de Gradio y el script de transcripción en vivo.
Nada de lo que hay aquí envía audio a internet: los modelos se bajan una vez de Hugging Face
y después todo corre en tu computadora (CPU, GPU NVIDIA o GPU de Mac).

    from voz import Transcriptor, cargar_audio, diarizar, a_srt
    t = Transcriptor("whisper-turbo")
    segmentos = t.segmentos(cargar_audio("entrevista.ogg"), idioma="es")
"""
from __future__ import annotations

import os
import re
import threading
import time
import unicodedata
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

SR = 16_000  # todos los modelos de voz de esta clase esperan audio mono a 16 kHz

# ───────────────────────────────────────────────────────── catálogo de modelos
MODELOS = {
    "whisper-turbo": {
        "nombre": "Whisper large-v3-turbo", "autor": "OpenAI", "pais": "EE. UU.", "licencia": "MIT",
        "idiomas": "99", "parametros": "0,8 B", "hf": "openai/whisper-large-v3-turbo",
        "nota": "El estándar. Detecta el idioma y también traduce al inglés.",
    },
    "faster-whisper": {
        "nombre": "faster-whisper (Whisper turbo en CTranslate2)", "autor": "SYSTRAN / OpenAI", "pais": "Francia / EE. UU.",
        "licencia": "MIT", "idiomas": "99", "parametros": "0,8 B",
        "hf": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
        "nota": "Los mismos pesos de Whisper, optimizados para CPU (int8). Corre en cualquier laptop.",
    },
    "qwen3-asr-0.6b": {
        "nombre": "Qwen3-ASR 0.6B", "autor": "Alibaba (Qwen)", "pais": "China", "licencia": "Apache 2.0",
        "idiomas": "30 + 22 dialectos chinos", "parametros": "0,6 B", "hf": "Qwen/Qwen3-ASR-0.6B-hf",
        "nota": "Pequeño y muy preciso. Acepta palabras clave como contexto (nombres, jerga).",
    },
    "qwen3-asr-1.7b": {
        "nombre": "Qwen3-ASR 1.7B", "autor": "Alibaba (Qwen)", "pais": "China", "licencia": "Apache 2.0",
        "idiomas": "30 + 22 dialectos chinos", "parametros": "1,7 B", "hf": "Qwen/Qwen3-ASR-1.7B-hf",
        "nota": "La versión grande de Qwen3-ASR.",
    },
    "parakeet-v3": {
        "nombre": "Parakeet TDT 0.6B v3", "autor": "NVIDIA", "pais": "EE. UU.", "licencia": "CC BY 4.0",
        "idiomas": "25 europeos", "parametros": "0,6 B", "hf": "nvidia/parakeet-tdt-0.6b-v3",
        "nota": "El más rápido. No es un modelo de lenguaje: no 'inventa' frases en el silencio.",
    },
    "voxtral-realtime": {
        "nombre": "Voxtral Mini 4B Realtime", "autor": "Mistral AI", "pais": "Francia", "licencia": "Apache 2.0",
        "idiomas": "13", "parametros": "4 B", "hf": "mistralai/Voxtral-Mini-4B-Realtime-2602",
        "nota": "Hecho para transcribir en vivo (streaming), con medio segundo de retraso. Pide GPU.",
    },
    "mms": {
        "nombre": "MMS-1b-all", "autor": "Meta", "pais": "EE. UU.", "licencia": "CC BY-NC 4.0 (no comercial)",
        "idiomas": "1162, incluye 25 variedades de quechua y el aimara", "parametros": "1 B",
        "hf": "facebook/mms-1b-all",
        "nota": "Para lenguas originarias. Sin puntuación ni mayúsculas. Hay que decirle el idioma.",
    },
}

# idioma ISO 639-1 (lo que entienden Whisper, Qwen y Voxtral) -> ISO 639-3 (lo que entiende MMS)
ISO3 = {"es": "spa", "en": "eng", "pt": "por", "fr": "fra", "qu": "quy"}


def dispositivo() -> str:
    """GPU NVIDIA ('cuda'), GPU de Mac ('mps') o CPU, en ese orden de preferencia."""
    import torch
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def cargar_audio(fuente, sr_origen: int | None = None) -> np.ndarray:
    """Cualquier audio -> arreglo float32 mono a 16 kHz.

    `fuente` puede ser una ruta (wav, mp3, ogg, m4a, opus, mp4...), un arreglo de numpy
    (con su `sr_origen`) o la tupla (sr, arreglo) que entrega Gradio.
    """
    if isinstance(fuente, (str, Path)):
        from faster_whisper import decode_audio  # usa PyAV: no hace falta instalar ffmpeg
        try:
            return decode_audio(str(fuente), sampling_rate=SR)
        except Exception:
            # algunos .ogg traen un último paquete dañado que PyAV rechaza; libsndfile sí los lee
            import soundfile as sf
            x, sr_origen = sf.read(str(fuente), dtype="float32")
            return cargar_audio(x, sr_origen)
    if isinstance(fuente, tuple):
        sr_origen, fuente = fuente
    x = np.asarray(fuente)
    if x.dtype.kind == "i":
        x = x / np.iinfo(x.dtype).max
    x = x.astype(np.float32)
    if x.ndim == 2:
        x = x.mean(axis=1 if x.shape[1] <= 2 else 0)
    if sr_origen and sr_origen != SR:
        from math import gcd

        from scipy.signal import resample_poly
        g = gcd(int(sr_origen), SR)
        x = resample_poly(x, SR // g, int(sr_origen) // g).astype(np.float32)
    return x


def tramos_de_voz(audio: np.ndarray, silencio_min=0.5, max_tramo=25.0, umbral=0.5) -> list[tuple[float, float]]:
    """Detector de voz (Silero VAD): devuelve los tramos (inicio, fin) en segundos donde alguien habla.

    Sirve para tres cosas: no mandarle silencio al modelo (evita alucinaciones), cortar audios
    largos en pedazos que el modelo acepta, y tener unidades para separar hablantes.
    """
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    opciones = VadOptions(threshold=umbral, min_silence_duration_ms=int(silencio_min * 1000),
                          max_speech_duration_s=max_tramo, speech_pad_ms=200)
    return [(t["start"] / SR, t["end"] / SR) for t in get_speech_timestamps(audio, opciones)]


@dataclass
class Segmento:
    inicio: float
    fin: float
    texto: str
    hablante: str | None = None


# ───────────────────────────────────────────────────────── transcriptor común
class Transcriptor:
    """Una misma interfaz para todos los modelos.

    - `transcribir(audio)`: texto de un audio corto (hasta ~25 s).
    - `segmentos(audio)`: audio de cualquier largo -> lista de Segmento con tiempos.
    """

    def __init__(self, clave: str, device: str | None = None, idioma_mms: str = "spa"):
        if clave not in MODELOS:
            raise ValueError(f"Modelo desconocido {clave!r}. Opciones: {', '.join(MODELOS)}")
        self.clave, self.info = clave, MODELOS[clave]
        self.device = device or ("cpu" if clave == "faster-whisper" else dispositivo())
        self.idioma_mms = idioma_mms
        t0 = time.perf_counter()
        self._cargar()
        self.segundos_carga = time.perf_counter() - t0

    def __repr__(self):
        return f"Transcriptor({self.info['nombre']} en {self.device})"

    # cada modelo se carga a su manera; todos quedan listos para recibir audio de 16 kHz
    def _cargar(self):
        import torch
        rid, dev = self.info["hf"], self.device
        media = torch.float32 if dev == "cpu" else (torch.float16 if dev == "mps" else torch.bfloat16)
        if self.clave == "faster-whisper":
            from faster_whisper import WhisperModel
            self.modelo = WhisperModel(rid, device="cuda" if dev == "cuda" else "cpu",
                                       compute_type="float16" if dev == "cuda" else "int8",
                                       cpu_threads=min(8, os.cpu_count() or 4))
        elif self.clave == "whisper-turbo":
            from transformers import pipeline
            self.modelo = pipeline("automatic-speech-recognition", model=rid, device=dev, dtype=media)
        elif self.clave.startswith("qwen3-asr"):
            from transformers import AutoProcessor, Qwen3ASRForConditionalGeneration
            self.dtype = torch.float32 if dev == "cpu" else torch.bfloat16
            self.proc = AutoProcessor.from_pretrained(rid)
            self.modelo = Qwen3ASRForConditionalGeneration.from_pretrained(rid, dtype=self.dtype).to(dev)
        elif self.clave == "parakeet-v3":
            from transformers import AutoProcessor, ParakeetForTDT
            self.proc = AutoProcessor.from_pretrained(rid)
            self.modelo = ParakeetForTDT.from_pretrained(rid, dtype=torch.float32).to(dev)
        elif self.clave == "voxtral-realtime":
            from transformers import AutoProcessor, VoxtralRealtimeForConditionalGeneration
            self.dtype = torch.float32 if dev == "cpu" else torch.bfloat16
            self.proc = AutoProcessor.from_pretrained(rid)
            self.modelo = VoxtralRealtimeForConditionalGeneration.from_pretrained(rid, dtype=self.dtype).to(dev)
        elif self.clave == "mms":
            from transformers import AutoProcessor, Wav2Vec2ForCTC
            self.proc = AutoProcessor.from_pretrained(rid, target_lang=self.idioma_mms)
            self.modelo = Wav2Vec2ForCTC.from_pretrained(rid, target_lang=self.idioma_mms,
                                                         ignore_mismatched_sizes=True).to(dev)

    def usar_idioma_mms(self, codigo: str):
        """MMS tiene un adaptador chico por idioma: cambiarlo no recarga el modelo grande."""
        if self.clave != "mms":
            raise ValueError("Solo MMS usa adaptadores por idioma")
        self.proc.tokenizer.set_target_lang(codigo)
        self.modelo.load_adapter(codigo)
        self.idioma_mms = codigo

    def transcribir(self, audio: np.ndarray, idioma: str | None = None, contexto: str | None = None) -> str:
        """Texto de un audio corto. `idioma`: 'es', 'en'... o None para detectarlo (Whisper y Qwen)."""
        import torch
        dev = self.device
        if len(audio) < SR * 0.3:
            return ""
        if self.clave == "faster-whisper":
            segs, _ = self.modelo.transcribe(audio, language=idioma, beam_size=5, initial_prompt=contexto)
            return " ".join(s.text.strip() for s in segs)
        if self.clave == "whisper-turbo":
            r = self.modelo(audio.copy(), generate_kwargs=self._kw_whisper(idioma, contexto), return_timestamps=True)
            return r["text"].strip()
        with torch.inference_mode():
            if self.clave.startswith("qwen3-asr"):
                inp = self.proc.apply_transcription_request(audio, language=idioma, prompt=contexto)
                inp = inp.to(dev, dtype=self.dtype)
                out = self.modelo.generate(**inp, max_new_tokens=448)
                return self.proc.decode(out[0, inp["input_ids"].shape[1]:], return_format="transcription_only").strip()
            if self.clave == "parakeet-v3":
                inp = self.proc(audio, sampling_rate=SR, return_tensors="pt").to(dev)
                out = self.modelo.generate(**inp)
                seq = out.sequences if hasattr(out, "sequences") else out
                return self.proc.batch_decode(seq, skip_special_tokens=True)[0].strip()
            if self.clave == "voxtral-realtime":
                inp = self.proc(audio, return_tensors="pt").to(dev, dtype=self.dtype)
                out = self.modelo.generate(**inp)
                return self.proc.batch_decode(out, skip_special_tokens=True)[0].strip()
            if self.clave == "mms":
                inp = self.proc(audio, sampling_rate=SR, return_tensors="pt").to(dev)
                ids = self.modelo(**inp).logits.argmax(-1)[0]
                return re.sub(r"\s+", " ", self.proc.decode(ids)).strip()
        raise RuntimeError(self.clave)

    def segmentos(self, audio: np.ndarray, idioma: str | None = None, contexto: str | None = None,
                  silencio_min: float = 0.3, max_tramo: float = 12.0) -> list[Segmento]:
        """Audio largo -> segmentos con tiempo. Primero el VAD corta donde hay voz; luego se
        transcribe cada tramo. Así todos los modelos dan tiempos, aunque no los traigan de fábrica.

        Tramos cortos (pausas de 0,3 s, máximo 12 s) ayudan a separar hablantes después: cada
        tramo debería tener una sola voz.
        """
        if self.clave == "faster-whisper":
            segs, _ = self.modelo.transcribe(audio, language=idioma, beam_size=5, vad_filter=True,
                                             initial_prompt=contexto,
                                             vad_parameters={"min_silence_duration_ms": int(silencio_min * 1000)})
            return [Segmento(round(s.start, 2), round(s.end, 2), s.text.strip()) for s in segs]
        salida = []
        for a, b in tramos_de_voz(audio, silencio_min=silencio_min, max_tramo=max_tramo):
            x = audio[int(a * SR):int(b * SR)]
            if self.clave == "whisper-turbo":  # Whisper además marca dónde empieza cada frase del tramo
                r = self.modelo(x.copy(), generate_kwargs=self._kw_whisper(idioma, contexto), return_timestamps=True)
                for c in r["chunks"]:
                    ini, fin = c["timestamp"]
                    fin = b - a if fin is None else min(fin, b - a)
                    if c["text"].strip():
                        salida.append(Segmento(round(a + ini, 2), round(a + fin, 2), c["text"].strip()))
                continue
            texto = self.transcribir(x, idioma, contexto)
            if texto:
                salida.append(Segmento(round(a, 2), round(b, 2), texto))
        return salida

    def _kw_whisper(self, idioma, contexto):
        import torch
        kw = {"task": "transcribe"} | ({"language": idioma} if idioma else {})
        if contexto:
            kw["prompt_ids"] = torch.tensor(self.modelo.tokenizer.get_prompt_ids(contexto)).to(self.device)
        return kw


# ───────────────────────────────────────────────────────── quién habla cuándo
@lru_cache(maxsize=1)
def _modelo_de_voces(device: str):
    """WeSpeaker ResNet34: convierte un tramo de voz en un vector de 256 números (la 'huella' de la voz)."""
    import torch
    from pyannote.audio import Inference, Model
    modelo = Model.from_pretrained("pyannote/wespeaker-voxceleb-resnet34-LM")
    return Inference(modelo, window="whole", device=torch.device(device))


def huellas_de_voz(audio: np.ndarray, tramos: list[tuple[float, float]], device: str | None = None) -> np.ndarray:
    """Un vector por tramo. Dos tramos de la misma persona dan vectores parecidos (coseno alto)."""
    import torch
    inf = _modelo_de_voces(device or dispositivo())
    filas = []
    for a, b in tramos:
        x = audio[int(a * SR):int(b * SR)]
        if len(x) < SR // 2:  # el modelo necesita al menos medio segundo
            x = np.pad(x, (0, SR // 2 - len(x)))
        filas.append(inf({"waveform": torch.from_numpy(x).unsqueeze(0), "sample_rate": SR}))
    return np.vstack(filas)


def diarizar(audio: np.ndarray, segmentos: list[Segmento], n_hablantes: int | None = None,
             umbral: float = 0.7, min_dur: float = 1.0, device: str | None = None) -> list[Segmento]:
    """Pone nombre de hablante (H1, H2...) a cada segmento.

    1. Huella de voz de cada segmento.
    2. Agrupa las huellas (clustering jerárquico con distancia coseno). Si no sabes cuántas
       personas hay, el `umbral` decide cuándo dos voces son distintas.
    3. Los segmentos muy cortos (<1 s: "sí", "ajá") dan huellas poco fiables: no votan en el
       agrupamiento y después se asignan al grupo más parecido.
    """
    from sklearn.cluster import AgglomerativeClustering
    if not segmentos:
        return []
    E = huellas_de_voz(audio, [(s.inicio, s.fin) for s in segmentos], device)
    E = E / np.linalg.norm(E, axis=1, keepdims=True)
    largos = np.array([s.fin - s.inicio >= min_dur for s in segmentos])
    if largos.sum() < 2:
        largos[:] = True
    if n_hablantes == 1 or largos.sum() < 2:
        etiquetas = np.zeros(len(segmentos), dtype=int)
    else:
        grupo = AgglomerativeClustering(n_clusters=n_hablantes, distance_threshold=None if n_hablantes else umbral,
                                        metric="cosine", linkage="average").fit(E[largos])
        centros = np.vstack([E[largos][grupo.labels_ == k].mean(axis=0) for k in range(grupo.n_clusters_)])
        etiquetas = (E @ centros.T).argmax(axis=1)
        etiquetas[largos] = grupo.labels_
    # numerar por orden de aparición: H1 es quien habla primero (en una entrevista, casi siempre quien entrevista)
    orden = {k: i + 1 for i, k in enumerate(dict.fromkeys(etiquetas))}
    return [Segmento(s.inicio, s.fin, s.texto, f"H{orden[e]}") for s, e in zip(segmentos, etiquetas)]


# ───────────────────────────────────────────────────────── salidas para el análisis
def a_tabla(segmentos: list[Segmento]) -> pd.DataFrame:
    return pd.DataFrame([asdict(s) for s in segmentos], columns=["inicio", "fin", "hablante", "texto"])


def _hhmmss(t: float, sep=",") -> str:
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}{sep}{int(round((s % 1) * 1000)):03d}"


def a_srt(segmentos: list[Segmento]) -> str:
    """Subtítulos SRT: los abren VLC, YouTube, ELAN, Atlas.ti, MAXQDA y NVivo."""
    bloques = []
    for i, s in enumerate(segmentos, 1):
        quien = f"[{s.hablante}] " if s.hablante else ""
        bloques.append(f"{i}\n{_hhmmss(s.inicio)} --> {_hhmmss(s.fin)}\n{quien}{s.texto}\n")
    return "\n".join(bloques)


def a_texto(segmentos: list[Segmento]) -> str:
    """Transcripción para leer: une segmentos seguidos del mismo hablante en un solo turno."""
    turnos = []
    for s in segmentos:
        if turnos and turnos[-1][1] == s.hablante:
            turnos[-1][2].append(s.texto)
        else:
            turnos.append([s.inicio, s.hablante, [s.texto]])
    return "\n\n".join(f"[{_hhmmss(t, '.')[:8]}] {h + ': ' if h else ''}{' '.join(x)}" for t, h, x in turnos)


def seudonimizar(texto: str, reemplazos: dict[str, str], parecido: int = 80) -> str:
    """Cambia nombres por seudónimos aunque el modelo los haya escrito mal.

    'Isabel Vásquez' también atrapa 'Isabel Vázquez' (comparación difusa con rapidfuzz).
    Revisa siempre el resultado: ningún método automático garantiza el anonimato.
    """
    from rapidfuzz import fuzz
    salida = texto
    for nombre, seudonimo in reemplazos.items():
        n = len(nombre.split())
        palabras = re.findall(r"\w+|\W+", salida)
        idx = [i for i, p in enumerate(palabras) if re.match(r"\w", p)]
        cambios = []
        for j in range(len(idx) - n + 1):
            tramo = palabras[idx[j]:idx[j + n - 1] + 1]
            if fuzz.ratio("".join(tramo).lower(), nombre.lower()) >= parecido:
                cambios.append((idx[j], idx[j + n - 1]))
        for a, b in reversed(cambios):
            palabras[a:b + 1] = [seudonimo]
        salida = "".join(palabras)
    return salida


# ───────────────────────────────────────────────────────── medir errores
def normalizar(texto: str) -> str:
    """Para comparar con justicia: minúsculas, sin puntuación ni espacios repetidos. Las tildes se quedan."""
    texto = unicodedata.normalize("NFC", texto.lower())
    texto = re.sub(r"[^\w\s']", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def wer(referencias: list[str], hipotesis: list[str]) -> float:
    """Tasa de error por palabra: (sustituciones + borradas + insertadas) / palabras de la referencia."""
    import jiwer
    return jiwer.wer([normalizar(r) for r in referencias], [normalizar(h) or "∅" for h in hipotesis])


def cer(referencias: list[str], hipotesis: list[str]) -> float:
    """Igual que el WER, pero contando caracteres. Útil para lenguas aglutinantes como el quechua."""
    import jiwer
    return jiwer.cer([normalizar(r) for r in referencias], [normalizar(h) or "∅" for h in hipotesis])


# ───────────────────────────────────────────────────────── en vivo
class VoxtralEnVivo:
    """Transcripción en vivo de verdad (streaming) con Voxtral Realtime.

    Se le va pasando audio con `agregar()` a medida que llega del micrófono y el texto aparece
    unos 0,5 s después de cada palabra. El modelo genera un token por cada 80 ms de audio,
    así que necesita una GPU que genere más de 12,5 tokens por segundo.

        vivo = VoxtralEnVivo(transcriptor)   # Transcriptor("voxtral-realtime")
        vivo.empezar()
        vivo.agregar(trozo)                  # float32, 16 kHz, cualquier tamaño
        print(vivo.texto)
        vivo.terminar()
    """

    def __init__(self, transcriptor: Transcriptor):
        if transcriptor.clave != "voxtral-realtime":
            raise ValueError("VoxtralEnVivo necesita Transcriptor('voxtral-realtime')")
        self.t = transcriptor
        self.proc = transcriptor.proc
        self._hilo = None

    def empezar(self):
        self._audio = np.zeros(0, dtype=np.float32)
        self._partes, self._fin, self.error = [], False, None
        self.eventos = []  # (segundos desde empezar, segundos de audio recibidos, texto nuevo)
        self._t0 = time.perf_counter()
        self._cond = threading.Condition()
        self._hilo = threading.Thread(target=self._generar, daemon=True)
        self._hilo.start()

    def agregar(self, trozo: np.ndarray):
        with self._cond:
            self._audio = np.concatenate([self._audio, np.asarray(trozo, dtype=np.float32)])
            self._cond.notify_all()

    @property
    def texto(self) -> str:
        return "".join(self._partes).strip()

    @property
    def segundos_recibidos(self) -> float:
        return len(self._audio) / SR

    def terminar(self, cola: float = 1.5) -> str:
        """Agrega un poco de silencio para que salgan las últimas palabras y cierra."""
        self.agregar(np.zeros(int(cola * SR), dtype=np.float32))
        with self._cond:
            self._fin = True
            self._cond.notify_all()
        if self._hilo:
            self._hilo.join(timeout=30)
        return self.texto

    def _esperar(self, n):
        with self._cond:
            while len(self._audio) < n and not self._fin:
                self._cond.wait(timeout=0.5)
            return len(self._audio) >= n

    def _bloques(self, primer):
        p, dev, dt = self.proc, self.t.device, self.t.dtype
        yield primer.input_features.to(dev, dtype=dt)
        hop, win = p.feature_extractor.hop_length, p.feature_extractor.win_length
        mel = p.num_mel_frames_first_audio_chunk
        ini = mel * hop - win // 2
        while self._esperar(fin := ini + p.num_samples_per_audio_chunk):
            x = p(self._audio[ini:fin], is_streaming=True, is_first_audio_chunk=False, return_tensors="pt")
            yield x.input_features.to(dev, dtype=dt)
            mel += p.audio_length_per_tok
            ini = mel * hop - win // 2

    def _leer(self, streamer):
        for trozo in streamer:
            if trozo:
                self._partes.append(trozo)
                self.eventos.append((time.perf_counter() - self._t0, self.segundos_recibidos, trozo))

    def _generar(self):
        from transformers import TextIteratorStreamer
        p = self.proc
        try:
            n0 = p.num_samples_first_audio_chunk
            if not self._esperar(n0):
                return
            primer = p(self._audio[:n0], is_streaming=True, is_first_audio_chunk=True, return_tensors="pt")
            streamer = TextIteratorStreamer(p.tokenizer, skip_special_tokens=True, clean_up_tokenization_spaces=True)
            lector = threading.Thread(target=self._leer, args=(streamer,), daemon=True)
            lector.start()
            self.t.modelo.generate(input_ids=primer.input_ids.to(self.t.device), input_features=self._bloques(primer),
                                   num_delay_tokens=primer.num_delay_tokens, streamer=streamer, max_new_tokens=100_000)
            lector.join(timeout=10)
        except Exception as e:  # que el error se vea en la app en lugar de morir en silencio
            self.error = f"{type(e).__name__}: {e}"


class CasiEnVivo:
    """Plan B para computadoras sin GPU: espera a que la persona haga una pausa y transcribe esa frase.

    No es streaming (el texto sale al terminar cada frase), pero con faster-whisper en CPU basta
    para tomar notas de una conversación.
    """

    def __init__(self, transcriptor: Transcriptor, idioma: str | None = "es", pausa: float = 0.6, max_frase: float = 15.0):
        self.t, self.idioma, self.pausa, self.max_frase = transcriptor, idioma, pausa, max_frase
        self.empezar()

    def empezar(self):
        self._pendiente = np.zeros(0, dtype=np.float32)
        self.frases: list[str] = []

    @property
    def texto(self) -> str:
        return " ".join(self.frases)

    def agregar(self, trozo: np.ndarray) -> str | None:
        """Devuelve la frase nueva cuando hay una lista; si no, None."""
        self._pendiente = np.concatenate([self._pendiente, np.asarray(trozo, dtype=np.float32)])
        dur = len(self._pendiente) / SR
        if dur < 1.0:
            return None
        tramos = tramos_de_voz(self._pendiente, silencio_min=self.pausa)
        if not tramos:
            self._pendiente = self._pendiente[-int(0.5 * SR):]  # solo silencio: se descarta
            return None
        fin_voz = tramos[-1][1]
        if dur - fin_voz >= self.pausa or dur >= self.max_frase:
            return self._cerrar(fin_voz if dur - fin_voz >= self.pausa else dur)
        return None

    def terminar(self) -> str:
        if len(self._pendiente) > SR // 2:
            self._cerrar(len(self._pendiente) / SR)
        return self.texto

    def _cerrar(self, hasta: float) -> str | None:
        corte = int(hasta * SR)
        frase = self.t.transcribir(self._pendiente[:corte], self.idioma)
        self._pendiente = self._pendiente[corte:]
        if frase:
            self.frases.append(frase)
            return frase
        return None
