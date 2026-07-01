# importar llibreries
import sqlite3

ruta_base_dades = "dades/assignatures.sqlite"

# Crerar funcions de la base de dades
# Obrir una connexió a la base de dades
def obtenir_connexio():
    connexio = sqlite3.connect(ruta_base_dades)
    connexio.row_factory = sqlite3.Row
    return connexio

# Crear les taules per primer cop, per si no existeixen.
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
    connexio.execute("""
        CREATE TABLE IF NOT EXISTS graus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE
        )
    """)
    connexio.execute("""
        CREATE TABLE IF NOT EXISTS graus_assignatures (
            grau_id INTEGER NOT NULL,
            assignatura_codi TEXT NOT NULL,
            PRIMARY KEY (grau_id, assignatura_codi)
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
                                    SELECT
                                        assignatures.codi,
                                        assignatures.titol,
                                        assignatures.semestre,
                                        assignatures.model_avaluacio,
                                        assignatures.descripcio,
                                        assignatures.url,
                                        GROUP_CONCAT(graus.nom, ', ') AS graus
                                    FROM assignatures
                                    LEFT JOIN graus_assignatures
                                        ON graus_assignatures.assignatura_codi = assignatures.codi
                                    LEFT JOIN graus
                                        ON graus.id = graus_assignatures.grau_id
                                    GROUP BY
                                        assignatures.codi,
                                        assignatures.titol,
                                        assignatures.semestre,
                                        assignatures.model_avaluacio,
                                        assignatures.descripcio,
                                        assignatures.url
                                    ORDER BY assignatures.codi
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


def actualitzar_detall_assignatura(codi, model_avaluacio, descripcio):
    connexio = obtenir_connexio()
    
    connexio.execute("""
        UPDATE assignatures
        SET model_avaluacio = ?, descripcio = ?
        WHERE codi = ?
    """, (model_avaluacio, descripcio, codi))
    
    connexio.commit()
    connexio.close()


def obtenir_o_crear_grau(nom, url):
    connexio = obtenir_connexio()
    
    # Comprovar si el grau ja existeix
    grau = connexio.execute("""
        SELECT id
        FROM graus
        WHERE url = ?
    """, (url,)).fetchone()
    
    if grau:
        connexio.close()
        return grau['id']
    
    cursor = connexio.execute("""
        INSERT INTO graus (nom, url)
        VALUES (?, ?)
    """, (nom, url))
    
    connexio.commit()
    grau_id = cursor.lastrowid
    connexio.close()
    return grau_id


def relacionar_grau_assignatura(grau_id, assignatura_codi):
    connexio = obtenir_connexio()
    
    connexio.execute("""
        INSERT OR IGNORE INTO graus_assignatures (grau_id, assignatura_codi)
        VALUES (?, ?)
    """, (grau_id, assignatura_codi))
    
    connexio.commit()
    connexio.close( )


def obtenir_assignatura_codi(codi):
    connexio = obtenir_connexio()

    assignatura = connexio.execute("""
        SELECT
            assignatures.codi,
            assignatures.titol,
            assignatures.semestre,
            assignatures.model_avaluacio,
            assignatures.descripcio,
            assignatures.url,
            GROUP_CONCAT(graus.nom, ', ') AS graus
        FROM assignatures
        LEFT JOIN graus_assignatures
            ON graus_assignatures.assignatura_codi = assignatures.codi
        LEFT JOIN graus
            ON graus.id = graus_assignatures.grau_id
        WHERE assignatures.codi = ?
        GROUP BY
            assignatures.codi,
            assignatures.titol,
            assignatures.semestre,
            assignatures.model_avaluacio,
            assignatures.descripcio,
            assignatures.url
    """, (codi,)).fetchone()
    
    connexio.close()

    return assignatura


def obtenir_graus():
    connexio = obtenir_connexio()

    graus = connexio.execute("""
        SELECT id, nom, url
        FROM graus
        ORDER by nom
    """).fetchall()

    connexio.close()

    return graus

def obtenir_assignatures_per_grau(grau_id):
    connexio = obtenir_connexio()

    assignatures = connexio.execute("""
                                    SELECT
                                        assignatures.codi,
                                        assignatures.titol,
                                        assignatures.semestre,
                                        assignatures.model_avaluacio,
                                        assignatures.descripcio,
                                        assignatures.url,
                                        GROUP_CONCAT(graus.nom, ', ') AS graus
                                    FROM assignatures
                                    LEFT JOIN graus_assignatures
                                        ON graus_assignatures.assignatura_codi = assignatures.codi
                                    LEFT JOIN graus
                                        ON graus.id = graus_assignatures.grau_id
                                    WHERE assignatures.codi IN (
                                        SELECT assignatura_codi
                                        FROM graus_assignatures
                                        WHERE grau_id = ?
                                    )
                                    GROUP BY
                                        assignatures.codi,
                                        assignatures.titol,
                                        assignatures.semestre,
                                        assignatures.model_avaluacio,
                                        assignatures.descripcio,
                                        assignatures.url
                                    ORDER by assignatures.codi
                                    """, (grau_id,)).fetchall()
    
    connexio.close()

    return assignatures
