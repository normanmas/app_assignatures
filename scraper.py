# Importar llibreries
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Funcions
def obtenir_codi_assignatura(url):
    parts_url = urlparse(url)
    parametres = parse_qs(parts_url.query)
    codis =parametres.get("SignatureCode")

    if codis:
        return codis[0]
    return ""

def llegir_assignatures_grau(url_grau):
    resposta = requests.get(url_grau)
    resposta.raise_for_status()  # Comprovar si la resposta és correcta

    sopa = BeautifulSoup(resposta.text, 'html.parser')

    assignatures = []

    for vincle in sopa.find_all('a', href=True):
        url_assignatura = vincle['href']
        titol = vincle.get_text(strip = True)

        if 'PlaDocent' in url_assignatura and 'SignatureCode' in url_assignatura:
            codi = obtenir_codi_assignatura(url_assignatura)

            assignatura = {
                'codi': codi,
                'titol': titol,
                'url': url_assignatura
            }
            assignatures.append(assignatura)
    return assignatures

def llegir_pagina(url):
    resposta = requests.get(url)
    resposta.raise_for_status()  # Comprovar si la resposta és correcta

    sopa = BeautifulSoup(resposta.text, 'html.parser')

    titol = sopa.find('title')

    if titol:
        return titol.text.strip()
    return "No s'ha trobat cap títol"

def llegir_text_pla_docent(url):
    # Configurar les opcions del navegador
    opcions = Options()

    # Executar en mode headless, sense interfície gràfica
    opcions.add_argument('-headless')
    # Ruta al binari de Firefox
    opcions.binary_location = "/snap/firefox/8521/usr/lib/firefox/firefox"

    # Crear una instància del navegador
    navegador = webdriver.Firefox(options=opcions)

    try:
        navegador.get(url)
        WebDriverWait(navegador, 30).until(
            lambda pagina: "Descripció" in pagina.find_element(By.TAG_NAME, "body").text
        )

        return navegador.find_element(By.TAG_NAME, "body").text
    finally:
        navegador.quit()

def extreure_model_avaluacio(text):
    # Buscar la secció de model d'avaluació
    linies = text.split("\n")
    #marca = "Model avaluacio"
    #if marca not in text:
    #    return "Pendent."
    #tros = text.split(marca, 1)[1]
    #return tros.split("\n", 1)[0].strip()
    for linia in linies:
        if "Model avaluació" in linia:
            return linia.replace('Model avaluació:', '').strip()

    return 'Pendent'

def extreure_descripcio(text):
    # Buscar la secció de descripció
    inici = "Descripció"
    final = "L'Assignatura en el conjunt del pla d'estudis"

    if inici not in text:
        return "Pendent."

    # Trobar el final de la secció de descripció
    tros = text.split(inici, 1)[1]

    if final in tros:
        tros = tros.split(final, 1)[0]

    # Retornar la descripció
    return tros.strip()

def llegir_detall_assignatura(url):
    text = llegir_text_pla_docent(url)

    detall = {
        'model_avaluacio': extreure_model_avaluacio(text),
        'descripcio': extreure_descripcio(text)
    }
    return detall