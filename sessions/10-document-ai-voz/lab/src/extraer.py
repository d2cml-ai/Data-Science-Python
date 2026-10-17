"""extraer.py — de texto a datos.

Toma el texto OCR de la carátula y extrae cuatro campos a JSON y CSV.

Hay dos implementaciones, y la comparacion entre ambas ES la leccion:

    Via A, reglas.  Expresiones regulares sobre el texto OCR. Rapida, gratis, fragil
                    ante una errata del OCR.
    Via B, modelo.  Se le entrega el texto OCR y se le pide JSON. Robusta ante
                    erratas, cuesta tokens.

Regla de verificacion heredada del proyecto real, y es la parte que importa:

    Todo valor extraido debe existir LITERALMENTE en el texto OCR. Si no existe, se
    marca sin_verificar=True. Un modelo que "corrige" el numero de licitacion y
    acierta es tan peligroso como uno que lo inventa, porque la proxima vez va a
    corregir y fallar.

Hallazgos verificados sobre el documento real, que explican por que el codigo es asi:

    - El nombre de la entidad NO esta en la caratula. Vive en el encabezado de la hoja
      fisica, que pertenece a la otra pagina logica. Hay que procesar las dos mitades.
    - El encabezado esta cortado en el escaneo: donde dice PROVINCIAL el OCR lee
      ROVINCIAL. Las expresiones regulares tienen que tolerarlo o fallan.
    - El documento original contiene la errata "ASENTAMIENTO HUAMANO". Es de la
      Municipalidad, no del OCR, y el texto de referencia la conserva tal cual.

Uso:
    python -m src.extraer                 # via A y via B si hay credenciales
    python -m src.extraer reglas          # solo via A
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

from src.comun import cargar_config, configurar_logging, preparar_directorios, preparar_paddle, ruta_absoluta

log = configurar_logging("extraer")

MODELO_LLM = "claude-opus-5-5"


@dataclass
class CampoExtraido:
    """Un campo, su valor, de donde salio y si se pudo verificar."""

    campo: str
    valor: str | None
    via: str
    sin_verificar: bool = False
    nota: str = ""


@dataclass
class Extraccion:
    """El resultado completo de una via de extraccion."""

    via: str
    campos: dict[str, CampoExtraido] = field(default_factory=dict)

    def como_dict(self) -> dict[str, Any]:
        return {
            "via": self.via,
            "campos": {k: asdict(v) for k, v in self.campos.items()},
        }


# --------------------------------------------------------------------------- #
# Normalizacion para la regla de verificacion
# --------------------------------------------------------------------------- #

def normalizar(texto: str) -> str:
    """Baja a minusculas, quita acentos y colapsa espacios.

    La verificacion compara el valor extraido contra el texto OCR sobre esta forma
    normalizada. Se tolera la diferencia de acentos y de espaciado porque el OCR las
    produce sin que cambie el dato; NO se tolera un caracter distinto, que es
    justamente lo que delataria una invencion del modelo.
    """
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", sin_acentos).strip().lower()


def verificar_literal(valor: str | None, texto_ocr: str) -> bool:
    """True si el valor existe literalmente en el texto OCR."""
    if not valor:
        return False
    return normalizar(valor) in normalizar(texto_ocr)


# --------------------------------------------------------------------------- #
# Via A: reglas
# --------------------------------------------------------------------------- #

# Las expresiones toleran que el escaneo haya cortado la primera letra de PROVINCIAL
# y que el OCR confunda N° con N, No o Nro.
PATRONES = {
    "entidad_convocante": [
        # Lo que el OCR produce de verdad sobre este documento es:
        #     MUNICIPALIDAL
        #     <OVINCIALDEILO
        # El escaneo corto el encabezado y el OCR hizo el resto: la D final se leyo
        # como L, la P y la R se perdieron, y los espacios desaparecieron. El patron
        # tolera las tres cosas. Que el valor recuperado siga siendo ilegible es
        # justamente el punto de la comparacion con la via B.
        r"(MUNICIPALIDA[DL]\W*\S{0,2}OVINCIAL\W*DE\W*[A-ZÁÉÍÓÚÑ]{2,})",
        r"(MUNICIPALIDAD\s+DISTRITAL\s+DE\s+[A-ZÁÉÍÓÚÑ]+)",
        r"(GOBIERNO\s+REGIONAL\s+DE\s+[A-ZÁÉÍÓÚÑ]+)",
    ],
    "numero_procedimiento": [
        # Verificado en el encabezado real: dice "LICITACION PUBLICA OBRAS", sin el
        # "DE". Por eso el "DE" es opcional dentro del grupo, y no al reves.
        r"(LICITACI[OÓ]N\s+P[UÚ]BLICA(?:\s+(?:DE\s+)?OBRAS)?\s*"
        r"N\s*[°ºo\.]?\s*\d+\s*-\s*\d{4}\s*-?\s*[A-Z\-]*)",
        r"(ADJUDICACI[OÓ]N\s+SIMPLIFICADA\s*N\s*[°ºo\.]?\s*\d+\s*-\s*\d{4}[A-Z\-]*)",
        r"(CONCURSO\s+P[UÚ]BLICO\s*N\s*[°ºo\.]?\s*\d+\s*-\s*\d{4}[A-Z\-]*)",
    ],
    "objeto_contratacion": [
        # El objeto arranca con un sustantivo de obra y, en estas bases, termina
        # nombrando el departamento. En el documento real el OCR lo devuelve partido
        # en una palabra por linea, asi que el patron corre sobre saltos de linea.
        r"((?:AMPLIACI[OÓ]N|MEJORAMIENTO|CREACI[OÓ]N|CONSTRUCCI[OÓ]N|"
        r"REHABILITACI[OÓ]N)\s+DEL?\s+.*?DEPARTAMENTO\s+DE\s+[A-ZÁÉÍÓÚÑ]{4,})",
        # Sin el ancla del departamento: hasta el fin de parrafo.
        r"((?:AMPLIACI[OÓ]N|MEJORAMIENTO|CREACI[OÓ]N|CONSTRUCCI[OÓ]N|"
        r"REHABILITACI[OÓ]N)\s+DEL?\s+.{20,400}?)(?:\n\s*\n|$)",
    ],
    "departamento": [
        r"DEPARTAMENTO\s+DE\s+([A-ZÁÉÍÓÚÑ]{4,})",
        r"REGI[OÓ]N\s+([A-ZÁÉÍÓÚÑ]{4,})",
        # Ultimo recurso: el departamento aparece junto a la provincia en la caratula.
        r"\b(MOQUEGUA|AREQUIPA|TACNA|LIMA|CUSCO|PUNO|PIURA|ANCASH|JUN[IÍ]N)\b",
    ],
}


def _limpiar_valor(valor: str) -> str:
    """Colapsa saltos de linea y espacios dobles que el OCR mete a mitad de frase."""
    return re.sub(r"\s+", " ", valor).strip(" .,;:-")


def extraer_por_reglas(texto_ocr: str, campos: list[str]) -> Extraccion:
    """Via A. Expresiones regulares sobre el texto OCR.

    Es gratis, instantanea y frágil: una errata del OCR en la palabra que ancla el
    patron y el campo sale vacio. Esa fragilidad es el punto de la comparacion.
    """
    resultado = Extraccion(via="reglas")

    for campo in campos:
        encontrado: str | None = None
        for patron in PATRONES.get(campo, []):
            coincidencia = re.search(patron, texto_ocr, re.IGNORECASE | re.DOTALL)
            if coincidencia:
                encontrado = _limpiar_valor(coincidencia.group(1))
                log.info("Via A | %s: encontrado con el patron %r", campo, patron[:40])
                break

        if encontrado is None:
            log.warning("Via A | %s: ningun patron coincidio", campo)
            resultado.campos[campo] = CampoExtraido(
                campo=campo, valor=None, via="reglas",
                sin_verificar=True, nota="ningun patron coincidio",
            )
            continue

        # La via A saca el valor del propio texto, asi que la verificacion literal
        # casi siempre pasa. Se corre igual: si el patron reconstruyo algo, se nota.
        ok = verificar_literal(encontrado, texto_ocr)
        resultado.campos[campo] = CampoExtraido(
            campo=campo, valor=encontrado, via="reglas",
            sin_verificar=not ok,
            nota="" if ok else "el valor no aparece literal en el texto OCR",
        )

    return resultado


# --------------------------------------------------------------------------- #
# Via B: modelo de lenguaje
# --------------------------------------------------------------------------- #

ESQUEMA_SALIDA = {
    "type": "object",
    "properties": {
        "entidad_convocante": {
            "type": ["string", "null"],
            "description": "Nombre completo de la entidad que convoca, tal como aparece",
        },
        "numero_procedimiento": {
            "type": ["string", "null"],
            "description": "Tipo y numero del procedimiento de seleccion, literal",
        },
        "objeto_contratacion": {
            "type": ["string", "null"],
            "description": "Descripcion de la obra o servicio que se contrata, literal",
        },
        "departamento": {
            "type": ["string", "null"],
            "description": "Departamento del Peru donde se ejecuta",
        },
    },
    "required": [
        "entidad_convocante",
        "numero_procedimiento",
        "objeto_contratacion",
        "departamento",
    ],
    "additionalProperties": False,
}

INSTRUCCION = """Eres un asistente que lee bases de licitaciones publicas peruanas.

El texto que recibes salio de un OCR sobre un documento escaneado, asi que puede
tener erratas, palabras cortadas y lineas desordenadas.

Reglas, en orden de importancia:

1. Copia los valores TAL COMO APARECEN en el texto. No corrijas erratas, no completes
   palabras cortadas, no normalices mayusculas. Si el texto dice "ASENTAMIENTO
   HUAMANO", escribe "ASENTAMIENTO HUAMANO".
2. Si un campo no aparece en el texto, devuelve null. Nunca lo deduzcas ni lo
   inventes.
3. No agregues informacion que no este en el texto, ni siquiera si la conoces.

Devuelve los cuatro campos del esquema."""


def extraer_por_modelo(texto_ocr: str, campos: list[str]) -> Extraccion | None:
    """Via B. Se le entrega el texto OCR al modelo y se le pide JSON.

    Devuelve None si no hay credenciales: la clase tiene que poder correr sin API.
    """
    try:
        import anthropic
    except ImportError:
        log.warning(
            "Via B no disponible: falta el paquete anthropic. "
            "Instalalo con: python -m pip install anthropic==0.80.0"
        )
        return None

    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.warning(
            "Via B no disponible: no hay ANTHROPIC_API_KEY en el entorno. "
            "La via A corre igual; la comparacion queda incompleta."
        )
        return None

    cliente = anthropic.Anthropic()
    log.info("Via B | consultando %s con %d caracteres de texto OCR",
             MODELO_LLM, len(texto_ocr))

    respuesta = cliente.messages.create(
        model=MODELO_LLM,
        max_tokens=16000,
        system=INSTRUCCION,
        messages=[{"role": "user", "content": texto_ocr}],
        output_config={"format": {"type": "json_schema", "schema": ESQUEMA_SALIDA}},
    )

    # output_config.format garantiza que el primer bloque de texto es JSON valido.
    bruto = next(b.text for b in respuesta.content if b.type == "text")
    datos = json.loads(bruto)
    log.info("Via B | respuesta recibida: %s", list(datos.keys()))

    resultado = Extraccion(via="modelo")
    for campo in campos:
        valor = datos.get(campo)
        if valor is None:
            resultado.campos[campo] = CampoExtraido(
                campo=campo, valor=None, via="modelo",
                sin_verificar=True, nota="el modelo devolvio null",
            )
            continue

        # Aqui se aplica la regla de verificacion. Es el corazon del modulo.
        ok = verificar_literal(valor, texto_ocr)
        if not ok:
            log.warning(
                "Via B | %s: el valor %r NO aparece literal en el texto OCR. "
                "Se marca sin_verificar. El modelo pudo haber corregido una errata, "
                "y un modelo que corrige y acierta es tan peligroso como uno que "
                "inventa.", campo, valor[:60],
            )
        resultado.campos[campo] = CampoExtraido(
            campo=campo, valor=valor, via="modelo",
            sin_verificar=not ok,
            nota="" if ok else "no aparece literal en el texto OCR",
        )

    return resultado


# --------------------------------------------------------------------------- #
# Lectura del texto OCR
# --------------------------------------------------------------------------- #

def texto_de_hojas(config: dict[str, Any], hojas: list[int] | None = None) -> str:
    """Junta el texto OCR de las dos mitades de las hojas indicadas.

    Se procesan LAS DOS MITADES a proposito: el nombre de la entidad vive en el
    encabezado de la hoja fisica, que al partir cae en la otra pagina logica. Leer
    solo la caratula deja ese campo vacio para siempre.
    """
    hojas = hojas or config["extraccion"]["hojas_metadatos"]
    dir_ocr = ruta_absoluta(config["rutas"]["procesados"]) / "ocr"

    if not dir_ocr.exists():
        raise FileNotFoundError(
            f"No existe {dir_ocr}. Corre primero:\n"
            "    python -m src.preparar 1\n"
            "    python -m src.ocr_run"
        )

    partes: list[str] = []
    for hoja in hojas:
        archivos = sorted(dir_ocr.glob(f"h{hoja:03d}_p*.txt"))
        if not archivos:
            log.warning("Hoja %d: no hay texto OCR en %s", hoja, dir_ocr)
            continue
        for archivo in archivos:
            contenido = archivo.read_text(encoding="utf-8")
            partes.append(contenido)
            log.info("Leido %s (%d caracteres)", archivo.name, len(contenido))

    if not partes:
        raise FileNotFoundError(
            f"No se encontro texto OCR para las hojas {hojas}. "
            "Corre primero python -m src.ocr_run"
        )

    return "\n\n".join(partes)


# --------------------------------------------------------------------------- #
# Salidas
# --------------------------------------------------------------------------- #

def escribir_salidas(extracciones: list[Extraccion], destino: Path) -> tuple[Path, Path]:
    """Escribe el JSON completo y el CSV de entrega."""
    destino.mkdir(parents=True, exist_ok=True)

    ruta_json = destino / "extraccion.json"
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump([e.como_dict() for e in extracciones], f,
                  ensure_ascii=False, indent=2)
        f.flush()

    ruta_csv = destino / "extraccion.csv"
    with open(ruta_csv, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(
            f, fieldnames=["via", "campo", "valor", "sin_verificar", "nota"]
        )
        escritor.writeheader()
        for extraccion in extracciones:
            for campo in extraccion.campos.values():
                escritor.writerow({
                    "via": campo.via,
                    "campo": campo.campo,
                    "valor": campo.valor or "",
                    "sin_verificar": campo.sin_verificar,
                    "nota": campo.nota,
                })
                f.flush()

    log.info("Salidas escritas: %s y %s", ruta_json.name, ruta_csv.name)
    return ruta_json, ruta_csv


def imprimir_comparacion(extracciones: list[Extraccion], campos: list[str]) -> None:
    """Imprime la tabla que compara las dos vias. Esta tabla ES la leccion."""
    print("\n" + "=" * 100)
    print("EXTRACCION DE CAMPOS")
    print("=" * 100)

    por_via = {e.via: e for e in extracciones}

    for campo in campos:
        print(f"\n{campo}")
        for via in ("reglas", "modelo"):
            if via not in por_via:
                print(f"  {via:<8} (no se corrio)")
                continue
            extraido = por_via[via].campos.get(campo)
            if extraido is None or extraido.valor is None:
                print(f"  {via:<8} —  (no encontrado)")
                continue
            marca = "SIN VERIFICAR" if extraido.sin_verificar else "verificado"
            valor = extraido.valor if len(extraido.valor) <= 70 else extraido.valor[:67] + "..."
            print(f"  {via:<8} {valor}")
            print(f"  {'':<8} [{marca}]{(' ' + extraido.nota) if extraido.nota else ''}")

    print("\n" + "=" * 100)

    if "reglas" in por_via and "modelo" in por_via:
        aciertos_a = sum(
            1 for c in campos
            if por_via["reglas"].campos.get(c)
            and por_via["reglas"].campos[c].valor
            and not por_via["reglas"].campos[c].sin_verificar
        )
        aciertos_b = sum(
            1 for c in campos
            if por_via["modelo"].campos.get(c)
            and por_via["modelo"].campos[c].valor
            and not por_via["modelo"].campos[c].sin_verificar
        )
        print(f"Via A (reglas): {aciertos_a}/{len(campos)} campos verificados, "
              f"costo cero")
        print(f"Via B (modelo): {aciertos_b}/{len(campos)} campos verificados, "
              f"costo en tokens")
        print("  La via A falla donde el OCR dejo una errata en la palabra que ancla\n"
              "  el patron. La via B la tolera. Las dos quedan sujetas a la misma\n"
              "  regla: si el valor no esta literal en el texto, va sin verificar.",
              flush=True)
    print("=" * 100)


# --------------------------------------------------------------------------- #
# Orquestacion
# --------------------------------------------------------------------------- #

def ejecutar(config: dict[str, Any] | None = None,
             solo_reglas: bool = False) -> list[Extraccion]:
    """Corre las dos vias sobre el texto OCR y escribe las salidas."""
    config = config or cargar_config()
    preparar_directorios(config)

    campos = config["extraccion"]["campos"]
    texto = texto_de_hojas(config)

    log.info("=== extraer.py: %d campos sobre %d caracteres de texto OCR ===",
             len(campos), len(texto))

    extracciones = [extraer_por_reglas(texto, campos)]

    if not solo_reglas:
        por_modelo = extraer_por_modelo(texto, campos)
        if por_modelo is not None:
            extracciones.append(por_modelo)

    destino = ruta_absoluta(config["rutas"]["salidas"])
    ruta_json, ruta_csv = escribir_salidas(extracciones, destino)

    imprimir_comparacion(extracciones, campos)
    print(f"\nEntregable: {ruta_csv}", flush=True)
    print(f"Detalle:    {ruta_json}", flush=True)

    return extracciones


def main() -> int:
    preparar_paddle()
    solo_reglas = len(sys.argv) > 1 and sys.argv[1] == "reglas"
    ejecutar(solo_reglas=solo_reglas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
