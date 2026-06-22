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
            nom TEXT NOT NULL,
            credits INTEGER NOT NULL,
            semestre TEXT NOT NULL
        )
    """)
    
    connexio.commit()
    connexio.close()

def inserir_assignatura(nom, credits, semestre):
    connexio = obtenir_connexio()
    
    connexio.execute("""
        INSERT INTO assignatures (nom, credits, semestre)
        VALUES (?, ?, ?)
    """, (nom, credits, semestre))
    
    connexio.commit()
    connexio.close()

def obtenir_assignatures():
    connexio = obtenir_connexio()
    
    assignatures = connexio.execute("""
                                    SELECT nom, credits, semestre
                                    FROM assignatures
                                    ORDER BY nom
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
        inserir_assignatura("Matemàtiques", 6, "Primer semestre")
        inserir_assignatura("Programació 1", 6, "Primer semestre")
        inserir_assignatura("Bases de dades", 6, "Segon semestre")
