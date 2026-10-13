"""Dashboard: clasifica un titular peruano en cuatro categorías.

Correr con:  streamlit run app.py
"""
import streamlit as st
from transformers import pipeline

st.title("Clasificador de titulares peruanos")
st.write("Escribe un titular y el modelo dirá a qué sección pertenece.")


# Cargar el modelo toma segundos; con cache solo se hace una vez
@st.cache_resource
def cargar_modelo():
    return pipeline("text-classification", model="modelo", top_k=None)


clasificador = cargar_modelo()

titular = st.text_input("Titular")

if titular:
    resultados = clasificador(titular)[0]
    st.subheader("Probabilidad por categoría")
    for resultado in resultados:
        st.write(resultado["label"], round(resultado["score"], 3))
        st.progress(resultado["score"])
