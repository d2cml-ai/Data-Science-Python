import streamlit as st

st.title("Mi Primera Aplicación con Streamlit")
st.write("¡Hola mundo!")

# Widget interactivo
nombre = st.text_input("Escribe tu nombre")
if nombre:
    st.write(f"Hola, {nombre}!")
