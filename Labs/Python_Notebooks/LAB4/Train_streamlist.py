#!/usr/bin/env python
# coding: utf-8

# ## Macroeconomics 
# IMP: log-Commodity price index, TC: log-exchange rate, RIN: log-international reserves, IPC: log-price consumption index, RATE: central bank rate reference
# 
# D: Annual difference

# In[19]:


get_ipython().system('pip install streamlit')


# In[20]:


import streamlit as st

st.title("Mi Primera Aplicación con Streamlit")
st.write("¡Hola mundo!")

# Agregar un widget interactivo
nombre = st.text_input("Escribe tu nombre")
if nombre:
    st.write(f"Hola, {nombre}!")


# In[21]:


import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

# Configura el estilo de seaborn
sns.set('notebook')

# Crea el gráfico y guarda la referencia
g = sns.relplot(x="YEAR", y="IPM", kind="line", color="red", data=macro, height=5, aspect=2)

# Añade etiquetas y título
plt.xlabel(' ')
plt.ylabel(' ')
plt.title('Índice del precio de materias primas 2013-2019')

# Añade el texto al pie del gráfico
txt="Elboración propia - BCRP"  
plt.figtext(0.5, 0.01, txt, wrap=True, horizontalalignment='center', fontsize=12)

# Muestra el gráfico en Streamlit
st.pyplot(g.fig)


# In[5]:


import numpy as np
import pandas as pd
from pandas import Series, DataFrame
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt


# In[3]:


macro = pd.read_csv("../../../data/macroeconomia.csv")
macro['YEAR']  = pd.to_datetime(macro['Fecha'])
macro


# In[6]:


sns.set('notebook')

sns.relplot(x="YEAR", y="IPM", kind="line", color="red", data=macro, height=5, aspect=2)
plt.xlabel(' ')
plt.ylabel(' ')
plt.title('Índice del precio de materias primas 2013-2019')

txt="Elboración propia - BCRP"  
plt.figtext(0.5, 0.01, txt, wrap=True, horizontalalignment='center', fontsize=12)


# #### Series in a single image
# 
# This graph shows a positive relationship between the change in international reserves and the commodity index.

# In[7]:


sns.set('notebook')


fig, ax = plt.subplots(figsize=(12,5))

x = macro['YEAR']
y1 = macro['DIPM']
y2 = macro['DRIN']

plt.plot(x, y1, label ='Indice de materias primas (Var %)', color='blue')
plt.plot(x, y2, label ='Reservas internacionales (Var %)', color='red')
plt.axhline(y=0, color='black', linestyle='--', lw=0.8)

plt.legend(loc='upper right')

txt="Elaboración propia - BCRP"  
plt.figtext(0.2, 0.01, txt, wrap=True, horizontalalignment='right', fontsize=10)


# ### Dual-line Plots
# 
# #### Exchange rate and monetary policy reaction

# In[8]:


sns.set('notebook', style = "ticks", font_scale= 1.08)

fig, ax = plt.subplots(figsize=(10,5))
lineplot = sns.lineplot(x= "YEAR" , y= "RATE", data=macro, 
                        label = 'Tasa interbancaria promedio ', color="k", legend=False)

#sns.despine()
plt.ylabel('Tasa de política monetaria')
plt.xlabel(' ')
plt.title('Exchange rate and monetary policy reaction');

ax2 = ax.twinx()
lineplot2 = sns.lineplot(x= "YEAR", y= "DTC", data=macro, ax=ax2, color = "red", 
                         label ='Tipo de cambio (variación anual %)', legend=False) 
sns.despine(right=False)
plt.ylabel('Tipo de cambio')
ax.figure.legend(loc='lower center', bbox_to_anchor=(1.1, 0.5), ncol=1);


txt="Elboración propia - BCRP"  
plt.figtext(0.2, 0.01, txt, wrap=True, horizontalalignment='right', fontsize=10)


# In[14]:


get_ipython().system('pip install streamlit')


# In[15]:


get_ipython().system('jupyter nbconvert --to script Train_streamlist.ipynb')


# In[12]:


import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

# Configura el estilo de seaborn
sns.set('notebook')

# Crea el gráfico y guarda la referencia
g = sns.relplot(x="YEAR", y="IPM", kind="line", color="red", data=macro, height=5, aspect=2)

# Añade etiquetas y título
plt.xlabel(' ')
plt.ylabel(' ')
plt.title('Índice del precio de materias primas 2013-2019')

# Añade el texto al pie del gráfico
txt="Elboración propia - BCRP"  
plt.figtext(0.5, 0.01, txt, wrap=True, horizontalalignment='center', fontsize=12)

# Muestra el gráfico en Streamlit
st.pyplot(g.fig)


# In[ ]:





# In[ ]:





# #### Reference:
# 
# #### Library of plots 
# 
# https://www.python-graph-gallery.com/stacked-and-percent-stacked-barplot
# 
# #### Seaborn package:
# 
# https://seaborn.pydata.org/generated/seaborn.catplot.html
# 
# https://programmerclick.com/article/54791895404/
