# Importar llibreries

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

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

