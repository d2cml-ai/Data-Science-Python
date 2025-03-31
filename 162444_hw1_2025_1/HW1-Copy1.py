#!/usr/bin/env python
# coding: utf-8

# # Intro

# In[1]:


# Importa el módulo webdriver, que permite controlar un navegador (como Chrome o Firefox) desde Python.
from selenium import webdriver

# Importa la clase By, que se usa para indicar cómo buscar elementos en la página (por id, class, xpath, css selector, etc.).
from selenium.webdriver.common.by import By

import time 


# In[2]:


driver = webdriver.Chrome()

url = "https://www.bumeran.com.pe/?utm_source=google&utm_medium=cpc&utm_campaign=B2C-GS-Brand&gad_source=1&gclid=Cj0KCQjwtJ6_BhDWARIsAGanmKeqqpwkfIEJv6tc6XS5tcmfwBaj4NXH3gzDtG9XVE53BRYk5VqEd0EaAv34EALw_wcB"

driver.get(url)

time.sleep(5)  

driver.maximize_window()


# In[ ]:


# <button id="buscarTrabajo" type="button" content="Buscar trabajo" class="sc-ktHwxA hEuTNc">Buscar trabajo</button>
# //*[@id="buscarTrabajo"]
# /html/body/div[1]/div/div[3]/div/div/div[1]/div/div/div/form/div[3]/button

driver.refresh()

# <button id="buscarTrabajo" type="button" content="Buscar trabajo" class="sc-ktHwxA hEuTNc">Buscar trabajo</button>
# //*[@id="buscarTrabajo"]
# /html/body/div[1]/div/div[3]/div/div/div[1]/div/div/div/form/div[3]/button

# --> Estático


# In[3]:


buscar_trabajo = driver.find_element( By.ID, 'buscarTrabajo')
buscar_trabajo.click()


# # Filtros

# ## Fecha de publicacion

# In[4]:


fecha_de_publicacion = driver.find_element(By.XPATH, '//button[contains(text(), "Fecha de publicación")]')
fecha_de_publicacion.click()


# In[7]:


menor_a_15_dias = driver.find_element(By.XPATH, '//button[contains(text(), "Menor a 15 días")]')
menor_a_15_dias.click()


# ## Departamento

# In[8]:


departamento = driver.find_element( By.XPATH, '//button[contains(text(), "Departamento")]')
departamento.click()


# In[10]:


lima = driver.find_element( By.XPATH, '//button[contains(text(), "Lima")]')
lima.click()


# ## Area

# In[11]:


area = driver.find_element( By.XPATH, '//button[contains(text(), "Área")]')
area.click()


# In[17]:


tec_sis_tel = driver.find_element( By.XPATH, '//button[contains(text(), "Tecnología, Sistemas y Telecomunicaciones")]')
tec_sis_tel.click()


# ## Subarea

# In[18]:


subarea = driver.find_element( By.XPATH, '//button[contains(text(), "Subárea")]')
subarea.click()


# In[19]:


programacion = driver.find_element( By.XPATH, '//button[contains(text(), "Programación")]')
programacion.click()


# ## Carga horaria

# In[20]:


carga_horaria = driver.find_element( By.XPATH, '//button[contains(text(), "Carga horaria")]')
carga_horaria.click()


# In[21]:


full_time = driver.find_element( By.XPATH, '//button[contains(text(), "Full-time")]')
full_time.click()


# # Scraping: Stage 1

# In[22]:


# This library is to manipulate the browser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver import ActionChains

# Standard libraries
import numpy as np
import os
import time
import re


# In[ ]:


# //*[@id="listado-avisos"]/div[2]/a


# In[23]:


job_links = []

# Loop para recorrer páginas
while True:
    # Esperar que se cargue la sección principal de resultados
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "listado-avisos"))
    )
    # Buscar enlaces dentro de ese contenedor
    listado = driver.find_element(By.ID, "listado-avisos")
    anchors = listado.find_elements(By.TAG_NAME, "a")  
    
    #  Filtrar los enlaces relevantes
    for a in anchors:
        href = a.get_attribute("href")
        if href and "/empleos/" in href and href not in job_links:
            job_links.append(href)
    
    # Mostrar cuántos enlaces se han recolectado hasta ahora
    print(f"🟢 Total acumulado: {len(job_links)}")

    # Intentar hacer clic en la flecha siguiente
    try:
        next_arrow = driver.find_element(By.XPATH, '//*[@id="listado-avisos"]/div[22]/a[2]/i')
        driver.execute_script("arguments[0].click();", next_arrow)
        time.sleep(5)  # Esperar un poco para que cargue la nueva página
    # Si no encuentra la flecha, fin
    except:
        print("🏁 No hay más páginas (flecha desapareció).")
        break

# Mostrar resultados finales
print("\n🎯 Enlaces encontrados:")
for link in job_links:
    print(link)


# # Scraping: Stage 2

# In[24]:


from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import pandas as pd
import time

titles, descriptions, districts, modalities, urls = [], [], [], [], []

sample_links = job_links[:5]

for link in sample_links:
    driver.get(link)
    print(f"🔍 Visitando: {link}")

    try:
        # Esperar que al menos el título (h1) esté presente
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'h1'))
        )
    except TimeoutException:
        print("⚠️ Página no cargó a tiempo. Saltando.")
        continue

    time.sleep(1)  # Margen adicional

    # Título
    try:
        title = driver.find_element(By.TAG_NAME, 'h1').text.strip()
    except NoSuchElementException:
        title = "NO TITLE"
    
    # Descripción
    try:
        # Extraer todo el texto dentro del contenedor principal
        contenedor = driver.find_element(By.ID, "ficha-detalle")
        description = contenedor.text.strip()

    except NoSuchElementException:
        description = "NO DESCRIPTION"

    # Distrito
    try:
        distrito = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH,
                '/html/body/div[1]/div/div[2]/div[2]/div/div[2]/div[1]/div[2]/div[1]/div[1]/div[2]/div/div[1]/div[1]/div[2]/div/div/li/a/h2'
            ))
        ).text.strip()
    except (NoSuchElementException, TimeoutException):
        distrito = "NO DISTRICT"

    # Modalidad
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "p"))
        )
        modality_tags = driver.find_elements(By.TAG_NAME, "p")
        modality = next(
            (tag.text.strip() for tag in modality_tags if tag.text.strip() in ["Remoto", "Presencial", "Híbrido"]),
            "NO MODALITY"
        )
    except:
        modality = "NO MODALITY"

    # Guardar resultados en listas
    titles.append(title)
    descriptions.append(description)
    districts.append(distrito)
    modalities.append(modality)
    urls.append(link)

    print(f"✅ Extraído: {title}")

# Crear DataFrame
df = pd.DataFrame({
    "Título": titles,
    "Descripción": descriptions,
    "Distrito": districts,
    "Modalidad": modalities,
    "URL": urls
})

# Mostrar tabla
from IPython.display import display
display(df)

# Guardar Excel
df.to_excel("ofertas_bumeran_muestra.xlsx", index=False, engine='openpyxl')
print("📁 Excel guardado como 'ofertas_bumeran.xlsx'")


# In[ ]:




