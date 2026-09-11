# Importar llibreries
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import functools
import hashlib
import json
import os
import re
import time

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Configuració del cache
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Temps de cache per defecte (24 hores en segons)
CACHE_TIMEOUT = 86400


def cache_result(timeout=CACHE_TIMEOUT):
    """Decorator per cachear resultats de funcions."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clau única
            key = hashlib.md5(f"{func.__name__}{args}{kwargs}".encode()).hexdigest()
            cache_file = f"{CACHE_DIR}/{key}.json"
            
            # Comprovar si existeix cache i no ha expirat
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        if time.time() - data['timestamp'] < timeout:
                            return data['result']
                except (json.JSONDecodeError, KeyError):
                    # Si el cache està corrupte, eliminar-lo
                    os.remove(cache_file)
            
            # Executar funció
            result = func(*args, **kwargs)
            
            # Guardar a cache
            try:
                with open(cache_file, 'w') as f:
                    json.dump({
                        'timestamp': time.time(),
                        'result': result
                    }, f)
            except (TypeError, ValueError):
                # Si el resultat no és serialitzable, no cachear
                pass
            
            return result
        return wrapper
    return decorator


def esborrar_cache():
    """Esborrar tot el cache."""
    for file in os.listdir(CACHE_DIR):
        if file.endswith('.json'):
            os.remove(os.path.join(CACHE_DIR, file))
    print(f"Cache esborrat: {CACHE_DIR}")


# Funcions d'extracció
def obtenir_codi_assignatura(url):
    """Obtenir el codi d'una assignatura des de l'URL."""
    parts_url = urlparse(url)
    parametres = parse_qs(parts_url.query)
    codis = parametres.get("SignatureCode")

    if codis:
        return codis[0]
    return ""


def extreure_model_avaluacio(text):
    """Extreure model d'avaluació amb expressions regulars."""
    patterns = [
        r'Model [d\' ]?avaluació:\s*(\w+)',
        r'Model avaluacio:\s*(\w+)',
        r'Model:\s*(\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return 'Pendent'


def extreure_descripcio(text):
    """Extreure descripció de manera més robusta."""
    start_markers = ['Descripció', 'Descripcion', 'Description']
    end_markers = ["L'Assignatura en el conjunt del pla", 'Assignatura en el conjunto']
    
    for start in start_markers:
        if start in text:
            parts = text.split(start, 1)
            if len(parts) > 1:
                content = parts[1]
                for end in end_markers:
                    if end in content:
                        content = content.split(end, 1)[0]
                
                content = re.sub(r'\s+', ' ', content).strip()
                return content
    
    return 'Pendent'


def extreure_credits(text):
    """Extreure nombre de crèdits ECTS."""
    patterns = [
        r'(\d+)\s*crèdits?\s*(?:ECTS)?',
        r'(\d+)\s*credits?\s*(?:ECTS)?',
        r'Crèdits:\s*(\d+)',
        r'Credits:\s*(\d+)',
        r'(\d+)\s*ECTS',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None


def extreure_llengua(text):
    """Extreure llengua de l'assignatura."""
    patterns = [
        r'Llengua:\s*([\wÀ-Úà-ú\s]+)',
        r'Idioma:\s*([\wÀ-Úà-ú\s]+)',
        r'Language:\s*([\w\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            llengua = match.group(1).strip().lower()
            
            mapping = {
                'català': 'ca', 'cat': 'ca', 'catalan': 'ca',
                'castellà': 'es', 'espanyol': 'es', 'español': 'es', 'spanish': 'es',
                'anglès': 'en', 'english': 'en', 'inglés': 'en',
            }
            
            for key, value in mapping.items():
                if key in llengua:
                    return value
            
            return llengua
    
    return 'ca'


def extreure_professor(text):
    """Extreure nom del professor de l'assignatura."""
    patterns = [
        r'Professor:\s*([\wÀ-Úà-ú\s.,-]+)',
        r'Profesor:\s*([\wÀ-Úà-ú\s.,-]+)',
        r'Professorat:\s*([\wÀ-Úà-ú\s.,-]+)',
        r'Tutor:\s*([\wÀ-Úà-ú\s.,-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            professor = match.group(1).strip()
            professor = re.sub(r'\s+', ' ', professor)
            return professor
    
    return None


# Funcions de scraping
@cache_result(timeout=CACHE_TIMEOUT)
def llegir_assignatures_grau(url_grau):
    """Llegir assignatures d'un grau amb millor maneig d'errors."""
    try:
        resposta = requests.get(url_grau, timeout=30)
        resposta.raise_for_status()
        
        sopa = BeautifulSoup(resposta.text, 'html.parser')
        assignatures = []
        
        for vincle in sopa.find_all('a', href=True):
            url_assignatura = vincle['href']
            titol = vincle.get_text(strip=True)
            
            if 'PlaDocent' in url_assignatura and 'SignatureCode' in url_assignatura:
                codi = obtenir_codi_assignatura(url_assignatura)
                
                assignatura = {
                    'codi': codi,
                    'titol': titol,
                    'url': url_assignatura
                }
                assignatures.append(assignatura)
        
        return assignatures
    except requests.exceptions.RequestException as e:
        print(f"Error llegint grau {url_grau}: {e}")
        return []
    except Exception as e:
        print(f"Error inesperat llegint grau {url_grau}: {e}")
        return []


def llegir_pagina(url):
    """Llegir el títol d'una pàgina."""
    try:
        resposta = requests.get(url, timeout=30)
        resposta.raise_for_status()
        
        sopa = BeautifulSoup(resposta.text, 'html.parser')
        titol = sopa.find('title')
        
        if titol:
            return titol.text.strip()
        return "No s'ha trobat cap títol"
    except Exception as e:
        print(f"Error llegint pàgina {url}: {e}")
        return "Error al llegir la pàgina"


def crear_navegador():
    """Crear un navegador Firefox en mode headless."""
    opcions = Options()
    opcions.add_argument('-headless')
    opcions.binary_location = "/snap/firefox/8521/usr/lib/firefox/firefox"
    return webdriver.Firefox(options=opcions)


def llegir_text_pla_docent_amb_navegador(navegador, url):
    """Llegir el text del pla docent utilitzant un navegador."""
    try:
        navegador.get(url)
        WebDriverWait(navegador, 30).until(
            lambda pagina: "Descripció" in pagina.find_element(By.TAG_NAME, "body").text
        )
        return navegador.find_element(By.TAG_NAME, "body").text
    except Exception as e:
        print(f"Error llegint pla docent amb navegador: {e}")
        return ""


def llegir_text_pla_docent(url):
    """Llegir el text del pla docent."""
    navegador = crear_navegador()
    try:
        return llegir_text_pla_docent_amb_navegador(navegador, url)
    finally:
        navegador.quit()


def llegir_detall_assignatura(url):
    """Llegir tots els detalls d'una assignatura."""
    text = llegir_text_pla_docent(url)

    detall = {
        'model_avaluacio': extreure_model_avaluacio(text),
        'descripcio': extreure_descripcio(text),
        'credits': extreure_credits(text),
        'llengua': extreure_llengua(text),
        'professor': extreure_professor(text)
    }
    return detall


def llegir_detall_assignatura_amb_navegador(navegador, url):
    """Llegir tots els detalls d'una assignatura utilitzant un navegador existent."""
    text = llegir_text_pla_docent_amb_navegador(navegador, url)

    detall = {
        'model_avaluacio': extreure_model_avaluacio(text),
        'descripcio': extreure_descripcio(text),
        'credits': extreure_credits(text),
        'llengua': extreure_llengua(text),
        'professor': extreure_professor(text)
    }
    return detall


def obtenir_llista_graus_uoc():
    """Obtenir llista de graus d'informàtica de la UOC."""
    graus_coneguts = [
        {"nom": "Grau de Ciència de Dades Aplicada", 
         "url": "https://www.uoc.edu/ca/estudis/graus/grau-data-science"},
        {"nom": "Grau d'Enginyeria Biomèdica",
         "url": "https://www.uoc.edu/ca/estudis/graus/grau-enginyeria-biomedica"},
        {"nom": "Grau d'Enginyeria i Telecomunicació",
         "url": "https://www.uoc.edu/ca/estudis/graus/grau-tecnologies-telecomunicacio"},
        {"nom": "Grau d'Enginyeria Informàtica",
         "url": "https://www.uoc.edu/ca/estudis/graus/grau-enginyeria-informatica"},
        {"nom": "Grau de Multimèdia",
         "url": "https://www.uoc.edu/ca/estudis/graus/grau-multimedia"},
        {"nom": "Grau de Desenvolupament i Proves de Software",
         "url": "https://www.uoc.edu/ca/estudis/graus/grau-desenvolupament-proves-software"},
        {"nom": "Doble grau d'Informàtica i ADE",
         "url": "https://www.uoc.edu/ca/estudis/graus/grau-informatica-ade-doble-titulacio"},
    ]
    
    return graus_coneguts
