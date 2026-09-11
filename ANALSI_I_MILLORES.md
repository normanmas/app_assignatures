# Anàlisi i Millores per l'Aplicació d'Assignatures UOC

## 1. Resum del Projecte Actual

L'aplicació és un sistema web desenvolupat amb Flask per gestionar assignatures dels graus d'informàtica de la UOC. Permet:
- Importar assignatures mitjançant web scraping
- Consultar i filtrar assignatures per grau i model d'avaluació
- Actualitzar informació del pla docent
- Gestionar assignatures aprovades

### Tecnologies utilitzades:
- Backend: Python + Flask
- Base de dades: SQLite
- Web scraping: BeautifulSoup + Selenium
- Frontend: HTML + CSS

### Estructura actual de la base de dades:
- `assignatures`: Informació bàsica de cada assignatura
- `graus`: Llista de graus universitaris
- `graus_assignatures`: Relació many-to-many entre graus i assignatures
- `assignatures_aprovades`: Assignatures ja superades per l'usuari

---

## 2. Anàlisi de Millores

### 2.1 Millores en la Base de Dades

#### Problemes actuals:
- Falta informació important: crèdits, llengua, professor, etc.
- El camp `semestre` és text sense estructura
- No hi ha taula de semestres/acadèmics
- No hi ha índexs per millorar el rendiment
- La taula `assignatures_aprovades` no té relació amb assignatures
- Falta camp de data de creació/modificació

#### Millores proposades:

```sql
-- Taula de semestres acadèmics
CREATE TABLE semestres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codi TEXT NOT NULL UNIQUE,  -- Ex: "2026-1", "2026-2"
    nom TEXT NOT NULL,         -- Ex: "Primer semestre 2026"
    data_inici DATE,
    data_final DATE,
    ANY_ACTIU BOOLEAN DEFAULT 1
);

-- Taula de professors (opcional)
CREATE TABLE professors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    email TEXT,
    departament TEXT
);

-- Taula de llengües
CREATE TABLE llengues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codi TEXT NOT NULL UNIQUE,  -- "ca", "es", "en"
    nom TEXT NOT NULL
);

-- Taula d'assignatures (millorada)
CREATE TABLE assignatures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codi TEXT NOT NULL UNIQUE,
    titol TEXT NOT NULL,
    semestre_id INTEGER,  -- Relació amb semestres
    credits INTEGER,       -- Nombre de crèdits ECTS
    llengua_id INTEGER,    -- Relació amb llengües
    model_avaluacio TEXT,
    descripcio TEXT,
    url TEXT,
    professor_id INTEGER,  -- Relació amb professors (opcional)
    data_creacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_modificacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actiu BOOLEAN DEFAULT 1,
    FOREIGN KEY (semestre_id) REFERENCES semestres(id),
    FOREIGN KEY (llengua_id) REFERENCES llengues(id),
    FOREIGN KEY (professor_id) REFERENCES professors(id)
);

-- Taula de graus (millorada)
CREATE TABLE graus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    facultat TEXT,         -- Ex: "Estudis d'Informàtica"
    data_creacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actiu BOOLEAN DEFAULT 1
);

-- Indexos per millorar rendiment
CREATE INDEX idx_assignatures_codi ON assignatures(codi);
CREATE INDEX idx_assignatures_model_avaluacio ON assignatures(model_avaluacio);
CREATE INDEX idx_assignatures_actiu ON assignatures(actiu);
CREATE INDEX idx_graus_assignatures_grau ON graus_assignatures(grau_id);
CREATE INDEX idx_graus_assignatures_assignatura ON graus_assignatures(assignatura_codi);

-- Taula d'històric de canvis (auditoria)
CREATE TABLE assignatures_historic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignatura_id INTEGER NOT NULL,
    camp_modificat TEXT NOT NULL,
    valor_antic TEXT,
    valor_nou TEXT,
    data_modificacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuari TEXT,  -- Per futur sistema d'autenticació
    FOREIGN KEY (assignatura_id) REFERENCES assignatures(id)
);

-- Taula d'assignatures aprovades (millorada)
CREATE TABLE assignatures_aprovades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignatura_id INTEGER NOT NULL,  -- Relació amb assignatures
    semestre TEXT,  -- Semestre en què es va aprovar
    nota REAL,      -- Nota numèrica
    observacions TEXT,
    data_aprovacio DATE,
    FOREIGN KEY (assignatura_id) REFERENCES assignatures(id)
);

-- Taula de favorits (per l'usuari)
CREATE TABLE assignatures_favorites (
    assignatura_id INTEGER NOT NULL,
    usuari TEXT NOT NULL,  -- Per futur sistema d'autenticació
    data_afegit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (assignatura_id, usuari),
    FOREIGN KEY (assignatura_id) REFERENCES assignatures(id)
);
```

### 2.2 Millores en el Scraper

#### Problemes actuals:
- Només extreu informació bàsica (codi, títol, URL)
- El mètode d'extracció de model d'avaluació i descripció és fràgil
- No gestionem bé els errors
- No hi ha cache de les pàgines ja visitades
- No extreu informació addicional com crèdits, professor, etc.

#### Millores proposades:

```python
# Millores en scraper.py

# 1. Afegir cache amb decorator
import functools
import hashlib
import json
import os

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_result(timeout=3600):
    """Decorator per cachear resultats de funcions."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clau única
            key = hashlib.md5(f"{func.__name__}{args}{kwargs}".encode()).hexdigest()
            cache_file = f"{CACHE_DIR}/{key}.json"
            
            # Comprovar si existeix cache i no ha expirat
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    if time.time() - data['timestamp'] < timeout:
                        return data['result']
            
            # Executar funció
            result = func(*args, **kwargs)
            
            # Guardar a cache
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'result': result
                }, f)
            
            return result
        return wrapper
    return decorator

# 2. Millorar extreure_descripcio i extreure_model_avaluacio
# Usar expressions regulars més robustes
def extreure_model_avaluacio(text):
    """Extreure model d'avaluació amb expressions regulars."""
    import re
    
    # Buscar patrons com "Model d'avaluació: AC" o "Model avaluacio: EX"
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
    import re
    
    # Buscar la secció Descripció
    start_markers = ['Descripció', 'Descripcion', 'Description']
    end_markers = ['L\'Assignatura en el conjunt del pla', 'Assignatura en el conjunto']
    
    for start in start_markers:
        if start in text:
            parts = text.split(start, 1)
            if len(parts) > 1:
                content = parts[1]
                for end in end_markers:
                    if end in content:
                        content = content.split(end, 1)[0]
                
                # Netejar el text
                content = re.sub(r'\s+', ' ', content).strip()
                return content
    
    return 'Pendent'

def extreure_credits(text):
    """Extreure nombre de crèdits ECTS."""
    import re
    
    # Buscar patrons com "6 ECTS", "6 crèdits", "Crèdits: 6"
    patterns = [
        r'(\d+)\s*ECTS',
        r'(\d+)\s*crèdits',
        r'Crèdits:\s*(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None

def extreure_llengua(text):
    """Extreure llengua de l'assignatura."""
    import re
    
    patterns = [
        r'Llengua:\s*(\w+)',
        r'Idioma:\s*(\w+)',
        r'Language:\s*(\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            llengua = match.group(1).strip().lower()
            # Mapejar a codis estàndard
            mapping = {
                'català': 'ca', 'cat': 'ca', 'catalan': 'ca',
                'castellà': 'es', 'espanyol': 'es', 'español': 'es', 'spanish': 'es',
                'anglès': 'en', 'english': 'en',
            }
            return mapping.get(llengua, llengua)
    
    return 'ca'  # Per defecte, català

# 3. Millorar la funció llegir_assignatures_grau
@cache_result(timeout=86400)  # Cache per 24 hores
def llegir_assignatures_grau(url_grau):
    """Llegir assignatures d'un grau amb millor maneig d'errors."""
    try:
        resposta = requests.get(url_grau, timeout=30)
        resposta.raise_for_status()
        
        sopa = BeautifulSoup(resposta.text, 'html.parser')
        assignatures = []
        
        # Buscar tots els enllaços
        for vincle in sopa.find_all('a', href=True):
            url_assignatura = vincle['href']
            titol = vincle.get_text(strip=True)
            
            # Filtrar només enllaços del Pla Docent
            if 'PlaDocent' in url_assignatura and 'SignatureCode' in url_assignatura:
                codi = obtenir_codi_assignatura(url_assignatura)
                
                # Afegir més camps si són disponibles al text del vincle
                assignatura = {
                    'codi': codi,
                    'titol': titol,
                    'url': url_assignatura
                }
                assignatures.append(assignatura)
        
        return assignatures
    except Exception as e:
        print(f"Error llegint grau {url_grau}: {e}")
        return []

# 4. Afegir funció per obtenir tots els graus de manera dinàmica
def obtenir_llista_graus_uoc():
    """Obtenir llista de graus d'informàtica de la UOC."""
    # URL base dels graus
    url_base = "https://www.uoc.edu/ca/estudis/graus"
    
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
```

### 2.3 Millores en l'Aplicació Flask

#### Problemes actuals:
- No hi ha autenticació
- Les rutes no tenen protecció
- No hi ha maneig d'errors global
- Falta paginació a les llistes
- No hi ha API REST
- El codi no està ben organitzat (totes les rutes a app.py)
- No hi ha separació clara entre lògica i presentació

#### Millores proposades:

```python
# app.py millorat

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.exceptions import NotFound, InternalServerError
import logging

# Configuració
aplicacio = Flask(__name__)
aplicacio.secret_key = 'clau_secreta_molt_segura_12345'  # Canviar en producció!

# Configuració de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuració de la base de dades
aplicacio.config['DATABASE'] = 'dades/assignatures.sqlite'

# Maneig d'errors global
@aplicacio.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@aplicacio.errorhandler(500)
def internal_error(e):
    logger.error(f"Error intern: {e}")
    return render_template('500.html'), 500

# Blueprints per organitzar el codi
from routes import assignatures as assignatures_blueprint
from routes import graus as graus_blueprint
from routes import api as api_blueprint

aplicacio.register_blueprint(assignatures_blueprint)
aplicacio.register_blueprint(graus_blueprint)
aplicacio.register_blueprint(api_blueprint, url_prefix='/api')

# Filtres personalitzats per Jinja2
@aplicacio.template_filter('truncar')
def truncar_filter(s, length=100):
    if len(s) <= length:
        return s
    return s[:length] + '...'

# Nova ruta: API REST per obtenir assignatures
@aplicacio.route('/api/assignatures')
def api_assignatures():
    grau_id = request.args.get('grau_id')
    model_avaluacio = request.args.get('model_avaluacio')
    
    # Obtenir assignatures amb filters
    assignatures = obtenir_assignatures()
    
    if grau_id:
        assignatures = [a for a in assignatures if grau_id in a.get('graus', [])]
    
    if model_avaluacio:
        assignatures = [a for a in assignatures if a.get('model_avaluacio') == model_avaluacio]
    
    return jsonify({
        'success': True,
        'data': assignatures,
        'count': len(assignatures)
    })

# Nova ruta: Buscar assignatures
@aplicacio.route('/assignatures/cerca')
def cercar_assignatures():
    query = request.args.get('q', '')
    
    if not query:
        return redirect(url_for('veure_assignatures'))
    
    assignatures = obtenir_assignatures()
    
    # Filtrar per codi o títol (case insensitive)
    resultats = [
        a for a in assignatures 
        if query.lower() in a['codi'].lower() or query.lower() in a['titol'].lower()
    ]
    
    return render_template(
        'assignatures.html',
        assignatures=resultats,
        graus=obtenir_graus(),
        cercat=query
    )

# Nova ruta: Eliminar assignatura aprovada
@aplicacio.route('/aprovades/eliminar/<codi>', methods=['POST'])
def eliminar_aprovada(codi):
    eliminar_assignatura_aprovada(codi)
    flash('Assignatura eliminada de les aprovades', 'success')
    return redirect(url_for('veure_aprovades'))
```

**Estructura de directoris millorada:**
```
app_assignatures/
├── app.py                 # Configuració principal
├── config.py              # Configuració de l'aplicació
├── requirements.txt
├── base_dades.py          # Gestió de la base de dades
├── scraper/
│   ├── __init__.py
│   ├── uoc_scraper.py     # Scraper específic per UOC
│   └── cache.py           # Sistema de cache
├── models/
│   ├── __init__.py
│   ├── assignatura.py
│   ├── grau.py
│   └── usuari.py
├── routes/
│   ├── __init__.py
│   ├── assignatures.py
│   ├── graus.py
│   ├── aprovades.py
│   └── api.py
├── templates/
│   ├── base.html          # Plantilla base
│   ├── index.html
│   ├── assignatures.html
│   └── ...
├── static/
│   ├── css/
│   │   └── estil.css
│   ├── js/
│   │   └── app.js
│   └── images/
└── tests/
    ├── test_scraper.py
    └── test_base_dades.py
```

### 2.4 Millores en el Frontend

#### Problemes actuals:
- Disseny bàsic sense interacció
- No hi ha JavaScript per millorar l'experiència
- Falta responsivitat mòbil
- No hi ha sistemes de confirmació per accions importants

#### Millores proposades:

**HTML (assignatures.html millorat):**
```html
<!-- Afegir barra de cerca -->
<form method="get" action="/assignatures/cerca" class="barra-cerca">
    <input type="text" name="q" placeholder="Buscar assignatures...">
    <button type="submit">Buscar</button>
</form>

<!-- Afegir paginació -->
<div class="paginacio">
    {% if pagina > 1 %}
        <a href="?pagina={{ pagina - 1 }}" class="boto">Anterior</a>
    {% endif %}
    <span>Pàgina {{ pagina }} de {{ total_pagines }}</span>
    {% if pagina < total_pagines %}
        <a href="?pagina={{ pagina + 1 }}" class="boto">Següent</a>
    {% endif %}
</div>

<!-- Afegir confirmació per accions -->
<a href="/actualitzar-detall/{{ assignatura.codi }}" 
   onclick="return confirm('Estàs segur que vols actualitzar aquesta assignatura?')">
    Actualitzar detall
</a>
```

**CSS (estil.css millorat):**
```css
/* Reset CSS */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* Variables CSS */
:root {
    --color-primari: #2563eb;
    --color-secundari: #16a34a;
    --color-fons: #f3f6f8;
    --color-text: #1f2933;
    --color-boto: #16a34a;
    --color-boto-hover: #15803d;
}

/* Responsive */
@media (max-width: 768px) {
    .contingut {
        padding: 16px;
    }
    
    .taula-assignatures {
        overflow-x: auto;
        display: block;
    }
    
    .boto {
        padding: 8px 12px;
        font-size: 14px;
    }
}

/* Animacions */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.targeta {
    animation: fadeIn 0.3s ease-in;
}

/* Missatges flash */
.flash-message {
    padding: 12px 16px;
    margin: 16px 0;
    border-radius: 4px;
}

.flash-success {
    background-color: #d1fae5;
    color: #065f46;
}

.flash-error {
    background-color: #fee2e2;
    color: #991b1b;
}

/* Barra de cerca */
.barra-cerca {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
}

.barra-cerca input {
    flex: 1;
    padding: 8px 12px;
    border: 1px solid #d9e2ec;
    border-radius: 4px;
}
```

**JavaScript (app.js):**
```javascript
// Funcions per millorar l'experiència d'usuari

// Confirmació per eliminar
function confirmarEliminacio(codi, titol) {
    return confirm(`Estàs segur que vols eliminar "${titol}"?`);
}

// Filtrar taula sense recarregar
function filtrarTaula() {
    const input = document.getElementById('cerca-rapida');
    const filter = input.value.toLowerCase();
    const table = document.querySelector('.taula-assignatures');
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
}

// Carregar més resultats (infinite scroll)
window.addEventListener('scroll', function() {
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
    
    if (scrollTop + clientHeight >= scrollHeight - 100) {
        // Carregar següent pàgina
        const paginaActual = parseInt(document.querySelector('.paginacio span').textContent.split(' ')[1]);
        const totalPagines = parseInt(document.querySelector('.paginacio span').textContent.split(' ')[3]);
        
        if (paginaActual < totalPagines) {
            window.location.href = `?pagina=${paginaActual + 1}`;
        }
    }
});
```

### 2.5 Millores en el Sistema de Càrrega Massiva

#### Problemes actuals:
- El procés de càrrega massiva és lent
- No hi ha feedback de progrés
- No gestionem bé els errors
- No es pot reprendre des de on es va quedar

#### Millores proposades:

```python
# base_dades.py - Afegir funcions per càrrega massiva

def obtenir_estat_importacio():
    """Obtenir l'estat actual de la importació."""
    connexio = obtenir_connexio()
    
    # Comptar assignatures totals
    total_assignatures = connexio.execute("SELECT COUNT(*) FROM assignatures").fetchone()[0]
    
    # Comptar assignatures amb model_avaluacio = 'Pendent'
    pendents = connexio.execute(
        "SELECT COUNT(*) FROM assignatures WHERE model_avaluacio = 'Pendent'"
    ).fetchone()[0]
    
    # Comptar graus
    total_graus = connexio.execute("SELECT COUNT(*) FROM graus").fetchone()[0]
    
    connexio.close()
    
    return {
        'total_assignatures': total_assignatures,
        'pendents': pendents,
        'total_graus': total_graus
    }

def marcar_com_a_importat(codi):
    """Marcar una assignatura com a importada correctament."""
    connexio = obtenir_connexio()
    
    connexio.execute("""
        UPDATE assignatures 
        SET importat = 1, data_importacio = CURRENT_TIMESTAMP
        WHERE codi = ?
    """, (codi,))
    
    connexio.commit()
    connexio.close()
```

```python
# prova_scraper.py - Millorat amb progress bar

import sys
import time

def mostrar_progres(current, total, missatge=""):
    """Mostrar barra de progrés a la terminal."""
    percent = (current / total) * 100
    bar_length = 40
    filled_length = int(bar_length * current / total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    sys.stdout.write(f'\r{missatge} |{bar}| {percent:.1f}% ({current}/{total})')
    sys.stdout.flush()
    
    if current == total:
        print()

def importar_graus_massiu():
    """Importar tots els graus de manera massiva amb feedback."""
    graus = obtenir_llista_graus_uoc()
    
    print(f"\nIniciant importació de {len(graus)} graus...\n")
    
    for idx, grau in enumerate(graus, 1):
        grau_id = obtenir_o_crear_grau(grau["nom"], grau["url"])
        
        # Obtenir assignatures del grau
        assignatures = llegir_assignatures_grau(grau["url"])
        
        mostrar_progres(0, len(assignatures), f"Processant {grau['nom']}")
        
        for jdx, assignatura in enumerate(assignatures, 1):
            if not existeix_assignatura(assignatura["codi"]):
                inserir_assignatura(
                    assignatura["codi"],
                    assignatura["titol"],
                    "2026-1",  # Semestre per defecte
                    "Pendent",
                    "Pendent de llegir el pla docent",
                    assignatura["url"]
                )
            
            relacionar_grau_assignatura(grau_id, assignatura["codi"])
            
            mostrar_progres(jdx, len(assignatures), f"Processant {grau['nom']}")
        
        print()
    
    print("Importació inicial completada!")
    
    # Actualitzar assignatures pendents
    print("\nActualitzant assignatures pendents...")
    assignatures_guardades = obtenir_assignatures()
    navegador = crear_navegador()
    
    try:
        for idx, assignatura in enumerate(assignatures_guardades, 1):
            if assignatura["model_avaluacio"] == "Pendent":
                mostrar_progres(idx, len(assignatures_guardades), "Actualitzant pendents")
                
                try:
                    detall = llegir_detall_assignatura_amb_navegador(navegador, assignatura["url"])
                    
                    actualitzar_detall_assignatura(
                        assignatura["codi"],
                        detall["model_avaluacio"],
                        detall["descripcio"]
                    )
                except Exception as error:
                    print(f"\nError actualitzant {assignatura['codi']}: {error}")
        
        print("\nActualització completada!")
    finally:
        navegador.quit()
```

### 2.6 Millores en la Seguretat

#### Millores proposades:

```python
# app.py - Configuració de seguretat

from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Protecció contra atacs CSRF
aplicacio.config['WTF_CSRF_ENABLED'] = True

# Encryptar cookies
aplicacio.config['SESSION_COOKIE_SECURE'] = True
aplicacio.config['SESSION_COOKIE_HTTPONLY'] = True
aplicacio.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Talisman per HTTPS i seguretat
Talisman(
    aplicacio,
    force_https=True,  # En producció
    strict_transport_security=True,
    session_cookie_secure=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'"],
        'style-src': ["'self'", "'unsafe-inline'"],
    }
)

# Limitador de peticions per evitar abusos
limiter = Limiter(
    aplicacio,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Protegir rutes crítiques
@aplicacio.route('/importar')
@limiter.limit("5 per minute")
def importar_assignatures():
    # ... codi existent
```

### 2.7 Millores en el Despliegue

#### Dockerfile:
```dockerfile
FROM python:3.14-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instal·lar dependències
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codi
COPY . .

# Crear directori per la base de dades
RUN mkdir -p dades

# Port per defecte
EXPOSE 5000

# Comanda per executar
CMD ["python", "app.py"]
```

#### docker-compose.yml:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./dades:/app/dades
      - ./cache:/app/cache
    environment:
      - FLASK_ENV=development
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app
```

#### nginx.conf:
```nginx
worker_processes 4;

events {
    worker_connections 1024;
}

http {
    upstream flask_app {
        server app:5000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        location / {
            proxy_pass http://flask_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location /static/ {
            alias /app/static/;
            expires 30d;
        }
    }
}
```

### 2.8 Millores en els Tests

#### Estructura de tests:
```
app_assignatures/
└── tests/
    ├── __init__.py
    ├── conftest.py          # Fixtures
    ├── test_base_dades.py
    ├── test_scraper.py
    ├── test_routes.py
    └── test_models.py
```

#### Exemple de tests:

```python
# tests/conftest.py
import pytest
import sqlite3
import os

@pytest.fixture
def db():
    """Crear base de dades de prova."""
    db_path = "dades/test_assignatures.sqlite"
    
    # Crear base de dades
    conn = sqlite3.connect(db_path)
    
    # Crear taules
    from base_dades import crear_taules
    crear_taules()
    
    yield conn
    
    # Netejar
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def client(db):
    """Client Flask per tests."""
    from app import aplicacio
    aplicacio.config['TESTING'] = True
    aplicacio.config['DATABASE'] = "dades/test_assignatures.sqlite"
    
    with aplicacio.test_client() as client:
        yield client
```

```python
# tests/test_base_dades.py
from base_dades import (
    inserir_assignatura, obtenir_assignatures, existeix_assignatura,
    obtenir_o_crear_grau, relacionar_grau_assignatura
)

def test_inserir_assignatura():
    """Test inserir assignatura."""
    inserir_assignatura(
        "22.401",
        "Fonaments de programació",
        "2026-1",
        "AC",
        "Descripció de prova",
        "https://example.com"
    )
    
    assignatura = obtenir_assignatures()
    assert len(assignatura) == 1
    assert assignatura[0]['codi'] == "22.401"

def test_existeix_assignatura():
    """Test comprovació existència assignatura."""
    assert not existeix_assignatura("99.999")
    
    inserir_assignatura("99.999", "Test", "2026-1", "AC", "Test", "https://test.com")
    assert existeix_assignatura("99.999")

def test_obtenir_o_crear_grau():
    """Test obtenir o crear grau."""
    grau_id = obtenir_o_crear_grau("Test Grau", "https://test.com")
    assert grau_id > 0
    
    # Comprovar que no es crea de nou
    grau_id2 = obtenir_o_crear_grau("Test Grau", "https://test.com")
    assert grau_id == grau_id2
```

---

## 3. Implementació de les Millores

### 3.1 Pas 1: Actualitzar l'esquema de la base de dades

**Script per migrar la base de dades actual a la nova versió:**

```python
# scripts/migrar_base_dades.py
import sqlite3

def migrar_base_dades():
    """Migrar l'esquema actual al nou esquema."""
    conn = sqlite3.connect("dades/assignatures.sqlite")
    cursor = conn.cursor()
    
    # 1. Afegir nous camps a assignatures
    cursor.execute("""
        ALTER TABLE assignatures 
        ADD COLUMN credits INTEGER
    """)
    
    cursor.execute("""
        ALTER TABLE assignatures 
        ADD COLUMN data_creacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)
    
    cursor.execute("""
        ALTER TABLE assignatures 
        ADD COLUMN data_modificacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)
    
    # 2. Crear taules noves
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS semestres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codi TEXT NOT NULL UNIQUE,
            nom TEXT NOT NULL,
            data_inici DATE,
            data_final DATE,
            ANY_ACTIU BOOLEAN DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS llengues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codi TEXT NOT NULL UNIQUE,
            nom TEXT NOT NULL
        )
    """)
    
    # 3. Afegir algunes llengües per defecte
    llengues = [('ca', 'Català'), ('es', 'Castellà'), ('en', 'Anglès')]
    cursor.executemany(
        "INSERT OR IGNORE INTO llengues (codi, nom) VALUES (?, ?)",
        llengues
    )
    
    # 4. Afegir columna llengua_id a assignatures
    cursor.execute("""
        ALTER TABLE assignatures 
        ADD COLUMN llengua_id INTEGER
    """)
    
    # 5. Actualitzar llengua per defecte (Català)
    cursor.execute("""
        UPDATE assignatures 
        SET llengua_id = (SELECT id FROM llengues WHERE codi = 'ca')
        WHERE llengua_id IS NULL
    """)
    
    # 6. Afegir índexs
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignatures_codi ON assignatures(codi)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignatures_model_avaluacio ON assignatures(model_avaluacio)")
    
    # 7. Crear taula d'històric
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignatures_historic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignatura_id INTEGER NOT NULL,
            camp_modificat TEXT NOT NULL,
            valor_antic TEXT,
            valor_nou TEXT,
            data_modificacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assignatura_id) REFERENCES assignatures(id)
        )
    """)
    
    # 8. Crear taula de professors
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT,
            departament TEXT
        )
    """)
    
    # 9. Afegir camp professor_id a assignatures
    cursor.execute("""
        ALTER TABLE assignatures 
        ADD COLUMN professor_id INTEGER
    """)
    
    # 10. Afegir camp actiu a assignatures i graus
    cursor.execute("""
        ALTER TABLE assignatures 
        ADD COLUMN actiu BOOLEAN DEFAULT 1
    """)
    
    cursor.execute("""
        ALTER TABLE graus 
        ADD COLUMN actiu BOOLEAN DEFAULT 1
    """)
    
    # 11. Afegir camp data_creacio a graus
    cursor.execute("""
        ALTER TABLE graus 
        ADD COLUMN data_creacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)
    
    # 12. Crear taula de semestres acadèmics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS semestres_academics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codi TEXT NOT NULL UNIQUE,
            nom TEXT NOT NULL,
            data_inici DATE,
            data_final DATE
        )
    """)
    
    # 13. Inserir semestres coneguts
    semestres = [
        ('2025-1', 'Primer semestre 2025', '2025-02-01', '2025-06-30'),
        ('2025-2', 'Segon semestre 2025', '2025-09-01', '2026-01-31'),
        ('2026-1', 'Primer semestre 2026', '2026-02-01', '2026-06-30'),
        ('2026-2', 'Segon semestre 2026', '2026-09-01', '2027-01-31'),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO semestres_academics (codi, nom, data_inici, data_final) VALUES (?, ?, ?, ?)",
        semestres
    )
    
    # 14. Actualitzar el camp semestre de assignatures per usar el semestre_id
    cursor.execute("""
        ALTER TABLE assignatures 
        ADD COLUMN semestre_id INTEGER
    """)
    
    # Mapejar valors actuals de semestre a semestre_id
    mapping = {
        '2026-1': 3,  # Primer semestre 2026
        '2025-2': 2,  # Segon semestre 2025
    }
    
    for codi_semestre, semestre_id in mapping.items():
        cursor.execute("""
            UPDATE assignatures 
            SET semestre_id = ?
            WHERE semestre = ?
        """, (semestre_id, codi_semestre))
    
    # 15. Afegir camp facultat a graus
    cursor.execute("""
        ALTER TABLE graus 
        ADD COLUMN facultat TEXT DEFAULT 'Estudis d\'Informàtica'
    """)
    
    conn.commit()
    conn.close()
    print("Migració completada amb èxit!")

if __name__ == "__main__":
    migrar_base_dades()
```

### 3.2 Pas 2: Actualitzar les funcions de la base de dades

**Actualitzar base_dades.py amb les noves funcions:**

```python
# Afegir aquestes funcions a base_dades.py

def obtenir_semestres():
    """Obtenir tots els semestres acadèmics."""
    connexio = obtenir_connexio()
    semestres = connexio.execute("""
        SELECT id, codi, nom, data_inici, data_final
        FROM semestres_academics
        ORDER BY data_inici DESC
    """).fetchall()
    connexio.close()
    return semestres

def obtenir_llengues():
    """Obtenir totes les llengües."""
    connexio = obtenir_connexio()
    llengues = connexio.execute("""
        SELECT id, codi, nom
        FROM llengues
        ORDER BY nom
    """).fetchall()
    connexio.close()
    return llengues

def obtenir_professors():
    """Obtenir tots els professors."""
    connexio = obtenir_connexio()
    professors = connexio.execute("""
        SELECT id, nom, email, departament
        FROM professors
        ORDER BY nom
    """).fetchall()
    connexio.close()
    return professors

def obtenir_o_crear_llengua(codi, nom):
    """Obtenir o crear una llengua."""
    connexio = obtenir_connexio()
    
    llengua = connexio.execute("""
        SELECT id FROM llengues WHERE codi = ?
    """, (codi,)).fetchone()
    
    if llengua:
        connexio.close()
        return llengua['id']
    
    cursor = connexio.execute("""
        INSERT INTO llengues (codi, nom) VALUES (?, ?)
    """, (codi, nom))
    
    llengua_id = cursor.lastrowid
    connexio.commit()
    connexio.close()
    return llengua_id

def obtenir_o_crear_professor(nom, email=None, departament=None):
    """Obtenir o crear un professor."""
    connexio = obtenir_connexio()
    
    professor = connexio.execute("""
        SELECT id FROM professors WHERE nom = ? AND email = ?
    """, (nom, email)).fetchone()
    
    if professor:
        connexio.close()
        return professor['id']
    
    cursor = connexio.execute("""
        INSERT INTO professors (nom, email, departament) VALUES (?, ?, ?)
    """, (nom, email, departament))
    
    professor_id = cursor.lastrowid
    connexio.commit()
    connexio.close()
    return professor_id

def obtenir_o_crear_semestre(codi, nom, data_inici=None, data_final=None):
    """Obtenir o crear un semestre acadèmic."""
    connexio = obtenir_connexio()
    
    semestre = connexio.execute("""
        SELECT id FROM semestres_academics WHERE codi = ?
    """, (codi,)).fetchone()
    
    if semestre:
        connexio.close()
        return semestre['id']
    
    cursor = connexio.execute("""
        INSERT INTO semestres_academics (codi, nom, data_inici, data_final) VALUES (?, ?, ?, ?)
    """, (codi, nom, data_inici, data_final))
    
    semestre_id = cursor.lastrowid
    connexio.commit()
    connexio.close()
    return semestre_id

def inserir_assignatura_completa(codi, titol, semestre_codi, model_avaluacio, descripcio, url,
                                 credits=None, llengua_codi='ca', professor_nom=None):
    """Inserir una assignatura amb tots els camps."""
    connexio = obtenir_connexio()
    
    # Obtenir IDs
    semestre_id = obtenir_o_crear_semestre(
        semestre_codi, f"Semestre {semestre_codi}"
    )
    llengua_id = obtenir_o_crear_llengua(llengua_codi, llengua_codi.upper())
    professor_id = None
    
    if professor_nom:
        professor_id = obtenir_o_crear_professor(professor_nom)
    
    # Inserir assignatura
    cursor = connexio.execute("""
        INSERT INTO assignatures 
        (codi, titol, semestre, semestre_id, credits, model_avaluacio, descripcio, url, 
         llengua_id, professor_id, data_creacio, data_modificacio, actiu)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
    """, (codi, titol, semestre_codi, semestre_id, credits, model_avaluacio, descripcio, url,
          llengua_id, professor_id))
    
    assignatura_id = cursor.lastrowid
    connexio.commit()
    connexio.close()
    
    return assignatura_id
```

### 3.3 Pas 3: Actualitzar el Scraper

**Actualitzar scraper.py per extreure més informació:**

```python
# Afegir aquestes funcions a scraper.py

def extreure_credits(text):
    """Extreure nombre de crèdits ECTS del text."""
    import re
    
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
    import re
    
    patterns = [
        r'Llengua:\s*([\wÀ-Úà-ú\s]+)',
        r'Idioma:\s*([\wÀ-Úà-ú\s]+)',
        r'Language:\s*([\w\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            llengua = match.group(1).strip().lower()
            
            # Mapejar a codis estàndard
            mapping = {
                'català': 'ca', 'cat': 'ca', 'catalan': 'ca',
                'castellà': 'es', 'espanyol': 'es', 'español': 'es', 'spanish': 'es',
                'anglès': 'en', 'english': 'en', 'inglés': 'en',
            }
            
            # Buscar coincidència
            for key, value in mapping.items():
                if key in llengua:
                    return value
            
            return llengua
    
    return 'ca'  # Per defecte, català

def extreure_professor(text):
    """Extreure nom del professor de l'assignatura."""
    import re
    
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
            # Netejar el nom (treure espais múltiples, comes, etc.)
            professor = re.sub(r'\s+', ' ', professor)
            return professor
    
    return None

def llegir_detall_assignatura_complet(url):
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
```

### 3.4 Pas 4: Actualitzar les Rutes de l'Aplicació

**Afegir noves rutes a app.py:**

```python
# Afegir aquestes rutes a app.py

@aplicacio.route('/assignatures/cerca')
def cercar_assignatures():
    """Cercar assignatures per text."""
    query = request.args.get('q', '')
    
    if not query:
        return redirect(url_for('veure_assignatures'))
    
    assignatures = obtenir_assignatures()
    
    # Filtrar per codi o títol (case insensitive)
    resultats = [
        a for a in assignatures 
        if query.lower() in a['codi'].lower() or query.lower() in a['titol'].lower()
    ]
    
    graus = obtenir_graus()
    
    return render_template(
        'assignatures.html',
        assignatures=resultats,
        graus=graus,
        grau_id=None,
        cercat=query
    )

@aplicacio.route('/aprovades/eliminar/<codi>', methods=['POST'])
def eliminar_aprovada(codi):
    """Eliminar una assignatura de les aprovades."""
    eliminar_assignatura_aprovada(codi)
    flash('Assignatura eliminada de les aprovades correctament', 'success')
    return redirect(url_for('veure_aprovades'))

@aplicacio.route('/assignatures/<codi>/afegir-favorit', methods=['POST'])
def afegir_favorit(codi):
    """Afegir una assignatura a favorits."""
    # Per ara, sense autenticació, usem usuari genèric
    # En el futur, usar request.user
    usuari = "anonymous"
    
    # Implementar funció afegir_favorit a base_dades.py
    afegir_favorit(codi, usuari)
    flash('Assignatura afegida a favorits', 'success')
    return redirect(url_for('veure_assignatura', codi=codi))
```

---

## 4. Llista de Canvis a Implementar

### 4.1 Canvis Prioritaris (Alta prioritat)

1. **Base de dades:**
   - [ ] Actualitzar esquema amb nous camps (crèdits, llengua, professor, etc.)
   - [ ] Crear taules auxiliars (semestres, llengües, professors)
   - [ ] Afegir índexs per millorar rendiment
   - [ ] Crear script de migració

2. **Scraper:**
   - [ ] Millores en l'extracció de dades
   - [ ] Afegir cache per evitar peticions redundants
   - [ ] Millorar maneig d'errors
   - [ ] Extreure més camps (crèdits, llengua, professor)

3. **Aplicació:**
   - [ ] Afegir maneig d'errors global
   - [ ] Implementar barra de cerca
   - [ ] Afegir missatges flash per feedback
   - [ ] Millores en la interfície

### 4.2 Canvis Mitjans (Mitjana prioritat)

1. **Base de dades:**
   - [ ] Crear taula d'històric de canvis
   - [ ] Afegir camp actiu/eliminat
   - [ ] Millores en les relacions

2. **Aplicació:**
   - [ ] Implementar paginació
   - [ ] Afegir confirmació per accions importants
   - [ ] Millores en el disseny (CSS)
   - [ ] Afegir JavaScript per millorar UX

3. **Scraper:**
   - [ ] Implementar còpia de seguretat de dades
   - [ ] Afegir logging detallat
   - [ ] Implementar sistema de reintents

### 4.3 Canvis Futurs (Baixa prioritat)

1. **Seguretat:**
   - [ ] Implementar autenticació d'usuaris
   - [ ] Afegir HTTPS i headers de seguretat
   - [ ] Implementar limitació de peticions

2. **Despliegue:**
   - [ ] Crear Dockerfile
   - [ ] Configurar docker-compose
   - [ ] Configurar Nginx
   - [ ] Implementar CI/CD

3. **Característiques noves:**
   - [ ] API REST
   - [ ] Comparador d'assignatures
   - [ ] Sistema de recomanacions
   - [ ] Exportació de dades (CSV, JSON)
   - [ ] Notificacions per canvis al pla docent

4. **Tests:**
   - [ ] Implementar tests unitaris
   - [ ] Implementar tests d'integració
   - [ ] Configurar CI amb GitHub Actions

---

## 5. Conclusions i Recomanacions

### 5.1 Resum de l'Anàlisi

El projecte actual té una bona estructura base i funciona correctament per als requisits inicials. No obstant això, hi ha diverses àrees on es poden fer millores significatives:

1. **Base de dades:** Necessita més informació i millor estructura per donar suport a noves funcionalitats.
2. **Scraper:** Pot ser més robust i eficient.
3. **Aplicació web:** Pot millorar l'experiència d'usuari i la seguretat.
4. **Mantenibilitat:** El codi pot estar millor organitzat i documentat.

### 5.2 Recomanacions Immediates

1. **Prioritzar la migració de la base de dades** per no perdre dades existents.
2. **Millorar el maneig d'errors** en el scraper per evitar fallades silencioses.
3. **Implementar caching** per reduir el temps d'importació i l'ús de recursos.
4. **Afegir logging** per facilitar la depuració.

### 5.3 Recomanacions a Mitjà Termini

1. **Implementar autenticació** per permetre múltiples usuaris.
2. **Crear una API REST** per permetre accés des d'altres aplicacions.
3. **Millorar el disseny** per fer l'aplicació més professional.
4. **Implementar tests** per garantir la qualitat del codi.

### 5.4 Recomanacions a Llarg Termini

1. **Implementar un sistema de notificacions** per alertar sobre canvis al pla docent.
2. **Crear un sistema de recomanacions** basat en les preferències de l'usuari.
3. **Desplegar l'aplicació** en un servidor per fer-la accessible des de qualsevol lloc.
4. **Crear una aplicació mòbil** que faci servir l'API.

---

## 6. Estimació de Temps

| Tasca | Temps estimat | Prioritat |
|-------|--------------|-----------|
| Migració de la base de dades | 2-4 hores | Alta |
| Millores en el scraper | 3-5 hores | Alta |
| Millores en l'aplicació Flask | 4-6 hores | Alta |
| Millores en el frontend | 2-3 hores | Mitjana |
| Implementar autenticació | 5-8 hores | Mitjana |
| Crear API REST | 4-6 hores | Mitjana |
| Implementar tests | 3-5 hores | Mitjana |
| Docker i despliegue | 2-3 hores | Baixa |
| Notificacions | 4-6 hores | Baixa |
| **Total** | **25-40 hores** | - |

---

## 7. Recursos Addicionals

### 7.1 Documentació Recomanada

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLite Tutorial](https://www.sqlitetutorial.net/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [Bootstrap CSS](https://getbootstrap.com/) - Per millorar el disseny
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)

### 7.2 Herramientes Recomanades

- **Desenvolupament:** VS Code, PyCharm
- **Base de dades:** DB Browser for SQLite, SQLite Studio
- **Despliegue:** Docker, GitHub Actions
- **Monitorització:** Sentry (per errors), LogRocket (per analítica)
- **Testing:** pytest, Selenium Grid

### 7.3 Biblioteques Python Recomanades

- `flask-login` - Autenticació
- `flask-sqlalchemy` - ORM per SQLite
- `flask-migrate` - Migracions de base de dades
- `python-dotenv` - Gestió de variables d'entorn
- `requests-cache` - Cache per peticions HTTP
- `tenacity` - Retries amb exponential backoff
- `faker` - Generar dades de prova

---

**Data de l'Anàlisi:** 2026-09-11
**Versió del Document:** 1.0
