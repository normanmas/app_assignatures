# Resum de Millores Implementades al Projecte d'Assignatures UOC

## Data: 2026-09-11

---

## 1. Millores a la Base de Dades

### 1.1 Nou esquema de la base de dades

S'han afegit els següents elements a la base de dades SQLite (`dades/assignatures.sqlite`):

#### Nous camps a la taula `assignatures`:
- `credits INTEGER` - Nombre de crèdits ECTS
- `data_creacio TIMESTAMP` - Data de creació de l'assignatura
- `data_modificacio TIMESTAMP` - Data de la darrera modificació
- `llengua_id INTEGER` - Relació amb la taula de llengües
- `semestre_id INTEGER` - Relació amb la taula de semestres acadèmics
- `professor_id INTEGER` - Relació amb la taula de professors
- `actiu BOOLEAN DEFAULT 1` - Indica si l'assignatura està activa

#### Noves taules creades:
- **`llengues`**: Emmagatzema les llengües disponibles (ca, es, en)
  - `id INTEGER PRIMARY KEY`
  - `codi TEXT NOT NULL UNIQUE` (ex: 'ca', 'es', 'en')
  - `nom TEXT NOT NULL` (ex: 'Català', 'Castellà', 'Anglès')

- **`semestres_academics`**: Emmagatzema informació dels semestres acadèmics
  - `id INTEGER PRIMARY KEY`
  - `codi TEXT NOT NULL UNIQUE` (ex: '2026-1', '2026-2')
  - `nom TEXT NOT NULL`
  - `data_inici DATE`
  - `data_final DATE`

- **`professors`**: Emmagatzema informació dels professors
  - `id INTEGER PRIMARY KEY`
  - `nom TEXT NOT NULL`
  - `email TEXT`
  - `departament TEXT`

- **`assignatures_historic`**: Taula d'auditoria per registrar canvis
  - `id INTEGER PRIMARY KEY`
  - `assignatura_id INTEGER NOT NULL`
  - `camp_modificat TEXT NOT NULL`
  - `valor_antic TEXT`
  - `valor_nou TEXT`
  - `data_modificacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
  - `usuari TEXT`

- **`assignatures_favorites`**: Taula per emmagatzemar assignatures favorites per usuari
  - `assignatura_id INTEGER NOT NULL`
  - `usuari TEXT NOT NULL`
  - `data_afegit TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

#### Nous camps a la taula `assignatures_aprovades`:
- `data_aprovacio DATE` - Data en què es va aprovar l'assignatura
- `assignatura_id INTEGER` - Relació amb la taula assignatures

#### Nous camps a la taula `graus`:
- `actiu BOOLEAN DEFAULT 1` - Indica si el grau està actiu
- `data_creacio TIMESTAMP` - Data de creació
- `facultat TEXT` - Facultat a la qual pertany el grau

#### Índexs creats per millorar el rendiment:
- `idx_assignatures_codi` - Índex pel camp codi
- `idx_assignatures_model_avaluacio` - Índex pel camp model_avaluacio
- `idx_assignatures_actiu` - Índex pel camp actiu
- `idx_graus_assignatures_grau` - Índex pel camp grau_id
- `idx_graus_assignatures_assignatura` - Índex pel camp assignatura_codi

---

## 2. Millores al Scraper (`scraper.py`)

### 2.1 Sistema de Cache
- **Decorator `@cache_result`**: Cachea els resultats de les funcions durant 24 hores per defecte
- **Directori de cache**: `cache/` - Emmagatzema els resultats en fitxers JSON
- **Funció `esborrar_cache()`**: Permet esborrar manualment tot el cache
- **Maneig d'errors**: Gestió de caches corruptes i errors de serialització

### 2.2 Funcions d'Extracció Millorades
Totes les funcions d'extracció ara utilitzen expressions regulars més robustes:

- **`extreure_model_avaluacio(text)`**: 
  - Cerca patrons com "Model d'avaluació: AC", "Model avaluacio: EX", "Model: AC"
  - Retorna 'Pendent' si no troba res

- **`extreure_descripcio(text)`**:
  - Cerca la secció Descripció en diferents idiomes
  - Talla el text a la secció següent ("L'Assignatura en el conjunt del pla")
  - Neteja el text (espais múltiples, etc.)

- **`extreure_credits(text)`**: 
  - Extreu el nombre de crèdits ECTS
  - Reconeix patrons com "6 ECTS", "6 crèdits", "Crèdits: 6"

- **`extreure_llengua(text)`**:
  - Extreu la llengua de l'assignatura
  - Mapeja a codis estàndard (ca, es, en)
  - Reconeix diferents formats (Català, Castellà, Anglès, etc.)

- **`extreure_professor(text)`**:
  - Extreu el nom del professor
  - Neteja el nom (espais múltiples, comes, etc.)

### 2.3 Funcions Actualitzades
- **`llegir_assignatures_grau(url_grau)`**: 
  - Ara usa el decorator `@cache_result` per cachear els resultats
  - Millor maneig d'errors amb try/except
  - Timeout de 30 segons per les peticions

- **`llegir_detall_assignatura(url)`**:
  - Retorna tots els camps: model_avaluacio, descripcio, credits, llengua, professor

- **`llegir_detall_assignatura_amb_navegador(navegador, url)`**:
  - Versió que usa un navegador existent per a múltiples peticions
  - Retorna tots els camps com la funció anterior

### 2.4 Nova funció
- **`obtenir_llista_graus_uoc()`**: Retorna la llista de graus coneguts de la UOC

---

## 3. Millores a la Base de Dades (`base_dades.py`)

### 3.1 Noves Funcions

#### Funcions per obtenir dades:
- **`obtenir_semestres()`**: Obté tots els semestres acadèmics
- **`obtenir_llengues()`**: Obté totes les llengües
- **`obtenir_professors()`**: Obté tots els professors

#### Funcions "obtenir o crear":
- **`obtenir_o_crear_llengua(codi, nom)`**: Obté o crea una llengua, retorna l'ID
- **`obtenir_o_crear_professor(nom, email, departament)`**: Obté o crea un professor, retorna l'ID
- **`obtenir_o_crear_semestre(codi, nom, data_inici, data_final)`**: Obté o crea un semestre, retorna l'ID

#### Funcions d'assignatures:
- **`inserir_assignatura_completa(...)`**: Inserir una assignatura amb tots els camps
- **`actualitzar_assignatura_completa(...)`**: Actualitza una assignatura amb tots els camps
  - Guarda els canvis a l'històric
  - Actualitza la data de modificació

#### Funcions de favorits:
- **`afegir_favorit(codi, usuari)`**: Afegir una assignatura a favorits
- **`eliminar_favorit(codi, usuari)`**: Eliminar una assignatura de favorits
- **`obtenir_favorits(usuari)`**: Obtenir totes les assignatures favorites d'un usuari

#### Funcions d'estat:
- **`obtenir_estat_importacio()`**: Retorna estadístiques sobre l'importació

### 3.2 Funcions Actualitzades
- **`obtenir_assignatures_aprovades()`**: Ara també retorna el camp `data_aprovacio`

---

## 4. Millores a l'Aplicació Flask (`app.py`)

### 4.1 Configuració i Maneig d'Errors
- **Configuració de logging**: Nivell INFO amb format detallat
- **Maneig d'errors global**:
  - Error 404: Plantilla personalitzada
  - Error 500: Plantilla personalitzada amb logging
- **Secret key**: Configurada per a les sessions i missatges flash

### 4.2 Filtres Jinja2
- **`truncar`**: Filtre per truncar text a una longitud determinada

### 4.3 Noves Rutes

#### Ruta de cerca:
```python
@aplicacio.route("/assignatures/cerca")
def cercar_assignatures():
    """Cercar assignatures per text (codi o títol)."""
```

#### Ruta per esborrar cache:
```python
@aplicacio.route("/cache/esborrar")
def esborrar_cache_ruta():
    """Esborrar el cache del scraper."""
```

#### Ruta per eliminar assignatures aprovades:
```python
@aplicacio.route('/aprovades/eliminar/<codi>', methods=['POST'])
def eliminar_aprovada(codi):
    """Eliminar una assignatura de les aprovades."""
```

### 4.4 Rutes Actualitzades
- **`importar_assignatures()`**:
  - Usa `obtenir_llista_graus_uoc()` per obtenir la llista de graus
  - Esborra el cache abans d'importar
  - Millor maneig d'errors amb logging i missatges flash
  - Missatge de success al finalitzar

- **`veure_aprovades()`**:
  - Missatge flash quan s'afegeix una assignatura

---

## 5. Millores a les Plantilles HTML

### 5.1 Nova Plantilla Base (`templates/base.html`)
- Plantilla base amb bloc de title, header i content
- **Suport per missatges flash**: Mostra missatges d'èxit, error i informació
- **Disseny consistent**: Header i main amb els mateixos estils

### 5.2 Plantilles Actualitzades

#### `index.html`:
- Extén de `base.html`
- Barra de cerca ràpida
- Enllaços actualitzats amb `url_for()`
- Botó per esborrar cache

#### `assignatures.html`:
- Extén de `base.html`
- Barra de cerca ràpida amb el text de cerca mantingut
- Columna de "Crèdits" afegida a la taula
- Enllaços actualitzats amb `url_for()`

#### `assignatura.html`:
- Extén de `base.html`
- Mostra el camp de crèdits si existeix
- Mostra descripció per defecte si no existeix
- Enllaços actualitzats amb `url_for()`

#### `aprovades.html`:
- Extén de `base.html`
- Columna d'Accions afegida amb botó d'eliminar
- Confirmació JavaScript abans d'eliminar
- Mostra '-' per camps buits

### 5.3 Noves Plantilles
- **`404.html`**: Pàgina d'error personalitzada
- **`500.html`**: Pàgina d'error intern del servidor

---

## 6. Millores al CSS (`static/estil.css`)

### 6.1 Missatges Flash
```css
.flash-message { padding, margin, border-radius, animation }
.flash-success { colors verds }
.flash-error { colors vermells }
.flash-info { colors blaus }
```

### 6.2 Barra de Cerca
```css
.barra-cerca { display: flex, gap, margin }
.barra-cerca input { flex, padding, border, border-radius }
.barra-cerca button { padding, colors, border, cursor }
```

### 6.3 Formularis
```css
form { display: flex, flex-wrap, gap, align-items }
form label { font-weight: bold }
form input, form select { padding, border, border-radius }
form button[type="submit"] { padding, colors, cursor }
```

### 6.4 Taules
```css
.taula-assignatures th { background-color, font-weight }
.taula-assignatures a { color, text-decoration }
.taula-assignatures a:hover { text-decoration: underline }
```

### 6.5 Animacions
```css
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.targeta { animation: fadeIn 0.3s ease-in; }
```

### 6.6 Responsive Design
```css
@media (max-width: 768px) {
    .contingut { padding: 16px; }
    .taula-assignatures { overflow-x: auto; display: block; }
    .boto { padding: 8px 12px; font-size: 14px; }
    form { flex-direction: column; align-items: stretch; }
}
```

---

## 7. Script de Migració

### `scripts/migrar_base_dades.py`
Script creat per migrar la base de dades existent al nou esquema:

- Comprova si les columnes ja existeixen abans d'intentar afegir-les
- Crea totes les noves taules
- Insereix dades inicials (llengües, semestres)
- Afegir índexs
- Mostra resum de la migració

**Ús:**
```bash
python3 scripts/migrar_base_dades.py
```

---

## 8. Documentació

### `ANALSI_I_MILLORES.md`
Document complet d'anàlisi amb:
- Resum del projecte actual
- Anàlisi detallada de millores per àrea
- Exemples de codi per a cada millora
- Llista de tasques a implementar amb prioritats
- Estimació de temps
- Recomanacions i recursos

---

## 9. Resum de Canvis per Fitxer

| Fitxer | Canvis Realitzats |
|--------|------------------|
| `base_dades.py` | +15 funcions noves, 1 funció actualitzada |
| `scraper.py` | Reescrit completament amb cache i noves funcions |
| `app.py` | +5 funcions noves, 3 funcions actualitzades, configuració millorada |
| `templates/base.html` | Nova plantilla base |
| `templates/index.html` | Actualitzada per usar base.html |
| `templates/assignatures.html` | Actualitzada per usar base.html, nova columna |
| `templates/assignatura.html` | Actualitzada per usar base.html |
| `templates/aprovades.html` | Actualitzada per usar base.html, botó d'eliminar |
| `templates/404.html` | Nova plantilla d'error |
| `templates/500.html` | Nova plantilla d'error |
| `static/estil.css` | Estils afegits per missatges flash, barra de cerca, responsive |
| `scripts/migrar_base_dades.py` | Nou script de migració |
| `dades/assignatures.sqlite` | Base de dades migrada amb nou esquema |

---

## 10. Pròxims Passos Recomanats

### 10.1 Prioritat Alta
1. **Provar l'aplicació completament**: Verificar que totes les noves funcions treballen correctament
2. **Actualitzar el README.md**: Documentar les noves funcionalitats
3. **Crear tests**: Implementar tests unitaris per les noves funcions

### 10.2 Prioritat Mitjana
1. **Implementar autenticació**: Usar Flask-Login per gestionar usuaris
2. **Millorar el scraper**: Afegir més camps (data d'inici/final, prerequisits, etc.)
3. **Implementar paginació**: Per les llistes llargues d'assignatures

### 10.3 Prioritat Baixa
1. **Crear API REST**: Per accedir a les dades des d'altres aplicacions
2. **Implementar notificacions**: Per canvis al pla docent
3. **Configurar Docker**: Per despliegue més fàcil
4. **Implementar tests d'integració**: Per garantir la qualitat del codi

---

## 11. Com Executar l'Aplicació

### 11.1 Requisits
- Python 3.14+
- Dependències a `requirements.txt`
- Base de dades migrada (ja feta)

### 11.2 Execució
```bash
# Activar entorn virtual
source entorn/bin/activate

# Instal·lar dependències (si cal)
pip install -r requirements.txt

# Executar l'aplicació
python app.py
```

### 11.3 Accés
Obrir el navegador a: http://127.0.0.1:5000

---

## 12. Estructura Final del Projecte

```
app_assignatures/
├── ANALSI_I_MILLORES.md          # Documentació d'anàlisi
├── RESUM_MILLORES_IMPLEMENTADES.md # Aquest document
├── README.md                     # Documentació original
├── app.py                        # Aplicació Flask (millorada)
├── base_dades.py                 # Gestió de BD (millorada)
├── scraper.py                    # Web scraping (millorat)
├── requirements.txt              # Dependències
├── proves_scraper.py             # Script de prova (original)
├── cache/                        # Directori de cache
│   └── *.json                    # Fitxers de cache
├── dades/                        # Base de dades
│   └── assignatures.sqlite       # Base de dades SQLite (migrada)
├── entorn/                       # Entorn virtual Python
├── scripts/                      # Scripts auxiliars
│   └── migrar_base_dades.py      # Script de migració
├── static/                       # Arxius estàtics
│   └── estil.css                 # CSS (millorat)
└── templates/                    # Plantilles HTML
    ├── base.html                 # Plantilla base (nova)
    ├── 404.html                  # Error 404 (nou)
    ├── 500.html                  # Error 500 (nou)
    ├── index.html                # Pàgina principal (millorada)
    ├── assignatures.html          # Llista d'assignatures (millorada)
    ├── assignatura.html           # Detall d'assignatura (millorada)
    └── aprovades.html            # Assignatures aprovades (millorada)
```

---

## 13. Estimació de Temps Invertit

| Tasca | Temps Invertit |
|-------|---------------|
| Anàlisi del projecte | 1-2 hores |
| Creació de documentació | 1 hora |
| Script de migració | 1 hora |
| Millores a base_dades.py | 1-2 hores |
| Millores a scraper.py | 2-3 hores |
| Millores a app.py | 1-2 hores |
| Millores a templates | 1-2 hores |
| Millores a CSS | 1 hora |
| **Total** | **9-14 hores** |

---

**Nota:** Aquest document detalla totes les millores implementades fins a la data. Es recomana revisar el document `ANALSI_I_MILLORES.md` per a més detalls sobre les millores proposades però encara no implementades.
