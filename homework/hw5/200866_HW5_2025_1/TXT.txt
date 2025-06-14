# -*- coding: utf-8 -*-
"""
Created on Mon Jun 9 19:21:52 2025

@author: Estefanía Chávez
"""

#Tarea 5

# Parte 1: Análisis de Sentimiento con FinBERT

# PASO 1: Importar librerías necesarias
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from datasets import load_dataset

# PASO 2: Cargar el modelo FinBERT
model_name = "ProsusAI/finbert"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Creamos un pipeline para clasificación de sentimiento
nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

# PASO 3: Cargar el dataset financiero
# -> Agregamos el parámetro trust_remote_code=True como indica el error
dataset = load_dataset("financial_phrasebank", "sentences_allagree", trust_remote_code=True)

# Extraemos las frases de prueba
phrases = dataset["train"]["sentence"]

# PASO 4: Aplicamos el modelo a una muestra de frases
sample_phrases = phrases[:10]  # Puedes cambiar a [:50] si quieres más resultados
results = nlp(sample_phrases)

# PASO 5: Mostrar resultados
print("=== Resultados del análisis de sentimiento ===")
for phrase, res in zip(sample_phrases, results):
    print(f"{phrase} => {res['label']} ({res['score']:.2f})")

# Parte 2:
    
import fitz  # PyMuPDF
from transformers import pipeline
import textwrap

# Paso 1: Ruta al archivo PDF
pdf_path = "Contrato_ejercicio (1).pdf"

# Paso 2: Extraer texto del PDF
def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

full_text = extract_text_from_pdf(pdf_path)

# Paso 3: Crear el modelo de resumen
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Paso 4: Dividir en partes si el texto es largo
chunks = textwrap.wrap(full_text, 1024)

# Paso 5: Generar el resumen
summary = ""
for chunk in chunks:
    result = summarizer(chunk, max_length=150, min_length=50, do_sample=False)
    summary += result[0]['summary_text'] + "\n"

# Paso 6: Mostrar el resumen
print("\n=== RESUMEN DEL CONTRATO ===\n")
print(summary)


# BONUS

from transformers import pipeline
import fitz

# Paso 1: Extraer texto del contrato
def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

pdf_path = "Contrato_ejercicio (1).pdf"
full_text = extract_text_from_pdf(pdf_path)

# Paso 2: Usar solo una parte del texto
text_fragment = full_text[:1000]

# Paso 3: Definir etiquetas legales comunes
labels = [
    "penalty clause", "guarantee", "duration", "exclusive use",
    "inspection rights", "termination clause", "early termination",
    "payment terms"
]

# Paso 4: Cargar el modelo de clasificación zero-shot
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Paso 5: Aplicar clasificación
results = classifier(text_fragment, candidate_labels=labels)

# Paso 6: Mostrar resultados
print("=== Clasificación de cláusulas en el contrato ===\n")
for label, score in zip(results["labels"], results["scores"]):
    print(f"{label}: {score:.2%}")


#Bonus 2: Modelo 

from transformers import pipeline
import fitz

# Paso 1: Extraer texto del contrato
def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Ruta del PDF
pdf_path = "Contrato_ejercicio (1).pdf"
full_text = extract_text_from_pdf(pdf_path)
text_fragment = full_text[:1000]

# Paso 2: Definir etiquetas
labels = [
    "penalty clause", "guarantee", "duration", "exclusive use",
    "inspection rights", "termination clause", "early termination",
    "payment terms"
]

# Paso 3: Pipeline con modelo multilingüe
classifier_alt = pipeline("zero-shot-classification", model="joeddav/xlm-roberta-large-xnli")

# Paso 4: Clasificar
results = classifier_alt(text_fragment, candidate_labels=labels)

# Paso 5: Mostrar resultados
print("=== Resultados con XLM-RoBERTa ===\n")
for label, score in zip(results["labels"], results["scores"]):
    print(f"{label}: {score:.2%}")
