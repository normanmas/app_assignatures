# importar llibreries
import sqlite3

ruta_base_dades = "dades/assignatures.sqlite"

# Obrir una connexió a la base de dades
def obtenir_connexio():
    connexio = sqlite3.connect(ruta_base_dades)
    connexio.row_factory = sqlite3.Row
    return connexio

def crear_taules():
    connexio = obtenir_connexio()
    
    connexio.execute("""
        CREATE TABLE IF NOT EXISTS assignatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codi TEXT NOT NULL,
            titol TEXT NOT NULL,
            semestre TEXT NOT NULL,
            model_avaluacio TEXT,
            descripcio TEXT,
            url TEXT            
        )
    """)
    
    connexio.commit()
    connexio.close()

def inserir_assignatura(codi, titol, semestre, model_avaluacio, descripcio, url):
    connexio = obtenir_connexio()
    
    connexio.execute("""
        INSERT INTO assignatures (codi, titol, semestre, model_avaluacio, descripcio, url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (codi, titol, semestre, model_avaluacio, descripcio, url))
    
    connexio.commit()
    connexio.close()

def obtenir_assignatures():
    connexio = obtenir_connexio()
    
    assignatures = connexio.execute("""
                                    SELECT codi, titol, semestre, model_avaluacio, descripcio, url
                                    FROM assignatures
                                    ORDER BY codi
                                    """).fetchall()
        
    connexio.close()
    return assignatures

def comptar_assignatures():
    connexio = obtenir_connexio()
    
    resultat = connexio.execute("""
                            SELECT COUNT(*) AS total
                            FROM assignatures
                            """).fetchone()
    
    connexio.close()
    return resultat["total"]

def afegir_dades_inicials():
    if comptar_assignatures() == 0:
        inserir_assignatura("22.401",
                            "Fonaments de programació",
                            "2026-1",
                            "AC",
                            "Assignatura inicial de prova",
                            "https://apps.uoc.edu/PlaDocent/PlaDocent?Semestre=20261&SignatureCode=22.401&Context=3&Locale=ca"
        )
# Funció per buscar duplicats de les assignatures i evitar d'importar dos cops
def existeix_assignatura(codi):
    connexio = obtenir_connexio()
    
    resultat = connexio.execute("""
                            SELECT COUNT(*) AS total
                            FROM assignatures
                            WHERE codi = ?
                            """, (codi,)).fetchone()
    
    connexio.close()
    return resultat["total"] > 0
