Homework 5 – NLP con Modelos de Hugging Face

sentiment_analysis_finbert.py
- Aplica el modelo `ProsusAI/finbert` para clasificar el sentimiento (positivo, negativo, neutral) de frases del dataset `financial_phrasebank` (versión `sentences_allagree`).
- Herramientas: `datasets`, `transformers`

`resumen_contrato.py`
* Extrae texto desde un archivo PDF usando `PyMuPDF` (`fitz`) y genera un resumen con el modelo `facebook/bart-large-cnn`.
* El archivo PDF esperado es `Contrato_ejercicio (1).pdf` (debe estar en la misma carpeta).
* Herramientas: `fitz`, `transformers`

`bonus_zero_shot_contract.py`
- Utilizo el modelo multilingüe `joeddav/xlm-roberta-large-xnli` para identificar cláusulas legales comunes dentro del contrato usando clasificación zero-shot.
- Candidatas: "penalty clause", "duration", "payment terms", etc.

---

## 🧠 Modelos de Hugging Face utilizados

1. [`ProsusAI/finbert`](https://huggingface.co/ProsusAI/finbert) – Clasificación de sentimiento financiero
2. [`facebook/bart-large-cnn`](https://huggingface.co/facebook/bart-large-cnn) – Resumen de textos largos
3. [`joeddav/xlm-roberta-large-xnli`](https://huggingface.co/joeddav/xlm-roberta-large-xnli) – Clasificación zero-shot multilingüe

---

PAQUETES A INSTALAR: 


```Anaconda prompt
pip install transformers datasets pymupdf
```


```bash
python sentiment_analysis_finbert.py
python resumen_contrato.py
python bonus_zero_shot_contract.py
```


