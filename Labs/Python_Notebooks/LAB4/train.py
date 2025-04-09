#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Train_streamlist.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Cargar datos
macro = pd.read_csv("../../../data/macroeconomia.csv")
macro['YEAR'] = pd.to_datetime(macro['Fecha'])

# Título y saludo interactivo
st.title("Mi Primera Aplicación con Streamlit")
st.write("¡Hola mundo!")

nombre = st.text_input("Escribe tu nombre")
if nombre:
    st.write(f"Hola, {nombre}!")

# ---------- Gráfico 1: IPM ----------
st.subheader("Índice de precios de materias primas")

sns.set('notebook')
g = sns.relplot(x="YEAR", y="IPM", kind="line", color="red", data=macro, height=5, aspect=2)
plt.xlabel(' ')
plt.ylabel(' ')
plt.title('Índice del precio de materias primas 2013-2019')
txt = "Elaboración propia - BCRP"
plt.figtext(0.5, 0.01, txt, wrap=True, horizontalalignment='center', fontsize=12)

st.pyplot(g.fig)

# ---------- Gráfico 2: DIPM vs DRIN ----------
st.subheader("Reservas internacionales vs Índice de materias primas")

fig, ax = plt.subplots(figsize=(12, 5))
x = macro['YEAR']
y1 = macro['DIPM']
y2 = macro['DRIN']

plt.plot(x, y1, label='Indice de materias primas (Var %)', color='blue')
plt.plot(x, y2, label='Reservas internacionales (Var %)', color='red')
plt.axhline(y=0, color='black', linestyle='--', lw=0.8)
plt.legend(loc='upper right')
plt.figtext(0.2, 0.01, "Elaboración propia - BCRP", wrap=True, horizontalalignment='right', fontsize=10)

st.pyplot(fig)

# ---------- Gráfico 3: Dual lineplot ----------
st.subheader("Tipo de cambio y tasa de interés de referencia")

sns.set('notebook', style="ticks", font_scale=1.08)
fig, ax = plt.subplots(figsize=(10, 5))

sns.lineplot(x="YEAR", y="RATE", data=macro, ax=ax, color="black", label='Tasa interbancaria promedio')
ax.set_ylabel('Tasa de política monetaria')
ax.set_xlabel(' ')
ax.set_title('Exchange rate and monetary policy reaction')

# Eje secundario
ax2 = ax.twinx()
sns.lineplot(x="YEAR", y="DTC", data=macro, ax=ax2, color="red", label='Tipo de cambio (variación anual %)')
ax2.set_ylabel('Tipo de cambio')

fig.legend(loc='lower center', bbox_to_anchor=(1.1, 0.5), ncol=1)
plt.figtext(0.2, 0.01, "Elaboración propia - BCRP", wrap=True, horizontalalignment='right', fontsize=10)

st.pyplot(fig)


# In[2]:


#get_ipython().system('pip install streamlit')


# In[ ]:


#get_ipython().system('jupyter nbconvert --to script train.ipynb')

