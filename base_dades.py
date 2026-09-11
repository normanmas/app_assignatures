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

    # Taula dels graus relacionats amb informàtica
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

    # Taula amb les diferents assignatures ja aprovades
    connexio.execute("""
                     CREATE TABLE IF NOT EXISTS assignatures_aprovades (
                     codi TEXT NOT NULL,
                     semestre TEXT NOT NULL,
                     nota,
                     observacions
        )
    """)

    # Taula amb les assignatures marcades com a interessants
    connexio.execute("""
                     CREATE TABLE IF NOT EXISTS assignatures_interessants (
                     codi TEXT NOT NULL PRIMARY KEY,
                     data_afegit TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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


# Gestió de les assignatures ja aprovades

# Afegir una assignatura ja aprovada
def afegir_assignatura_aprovada(codi, semestre, nota, observacions):
    connexio = obtenir_connexio()

    # Eliminar si ja estava creada per evitar duplicitats.
    connexio.execute("""
                     DELETE FROM assignatures_aprovades
                     WHERE codi = ?
                     """, (codi,))
    
    connexio.execute("""
                     INSERT INTO assignatures_aprovades (codi, semestre, nota, observacions)
                     VALUES (?, ?, ? ,?)
    """, (codi, semestre, nota, observacions))
    connexio.commit()
    connexio.close()

# Eliminar una assignatura ja aprovada
def eliminar_assignatura_aprovada(codi):
    connexio = obtenir_connexio()

    connexio.execute("""
                     DELETE FROM assignatures_aprovades
                     WHERE codi = ?
                     """, (codi,))
    connexio.commit()
    connexio.close()


# Funció per consultar assignatures ja aprovades
def obtenir_assignatures_aprovades():
    connexio = obtenir_connexio()

    assignatures_aprovades = connexio.execute("""
                             SELECT a.codi, a.titol, ap.semestre, ap.nota, ap.observacions, ap.data_aprovacio
                             FROM assignatures_aprovades ap
                             JOIN assignatures a ON ap.codi = a.codi
                             ORDER BY a.codi
                             """).fetchall()
    
    connexio.close()

    return assignatures_aprovades


# Gestió de les assignatures marcades com a interessants

# Afegir una assignatura com a interessant
def afegir_assignatura_interessant(codi):
    connexio = obtenir_connexio()

    # Eliminar si ja estava creada per evitar duplicitats.
    connexio.execute("""
                     DELETE FROM assignatures_interessants
                     WHERE codi = ?
                     """, (codi,))
    
    connexio.execute("""
                     INSERT INTO assignatures_interessants (codi)
                     VALUES (?)
    """, (codi,))
    connexio.commit()
    connexio.close()

# Eliminar una assignatura de les interessants
def eliminar_assignatura_interessant(codi):
    connexio = obtenir_connexio()

    connexio.execute("""
                     DELETE FROM assignatures_interessants
                     WHERE codi = ?
                     """, (codi,))
    connexio.commit()
    connexio.close()


# Funció per consultar si una assignatura és interessant
def es_assignatura_interessant(codi):
    connexio = obtenir_connexio()

    resultat = connexio.execute("""
                             SELECT COUNT(*) AS total
                             FROM assignatures_interessants
                             WHERE codi = ?
                             """, (codi,)).fetchone()
    
    connexio.close()

    return resultat["total"] > 0


# Funció per consultar assignatures interessants
def obtenir_assignatures_interessants():
    connexio = obtenir_connexio()

    assignatures_interessants = connexio.execute("""
                             SELECT codi, data_afegit
                             FROM assignatures_interessants
                             ORDER BY data_afegit DESC
                             """).fetchall()
    
    connexio.close()

    return assignatures_interessants


# ============================================================================
# NOVES FUNCIONS PER LA BASE DE DADES MILLORADA
# ============================================================================

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
    """Obtenir o crear una llengua. Retorna l'ID."""
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
    """Obtenir o crear un professor. Retorna l'ID."""
    connexio = obtenir_connexio()
    
    # Buscar per nom i email
    professor = connexio.execute("""
        SELECT id FROM professors WHERE nom = ? AND (email = ? OR email IS NULL)
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
    """Obtenir o crear un semestre acadèmic. Retorna l'ID."""
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


def actualitzar_assignatura_completa(codi, titol=None, semestre_codi=None, model_avaluacio=None,
                                     descripcio=None, url=None, credits=None, llengua_codi=None,
                                     professor_nom=None, actiu=None):
    """Actualitzar una assignatura amb tots els camps."""
    connexio = obtenir_connexio()
    
    # Obtenir assignatura actual
    assignatura = connexio.execute("""
        SELECT id, codi, titol, semestre, semestre_id, credits, model_avaluacio, 
               descripcio, url, llengua_id, professor_id, actiu
        FROM assignatures WHERE codi = ?
    """, (codi,)).fetchone()
    
    if not assignatura:
        connexio.close()
        return False
    
    # Preparar valors per actualitzar
    updates = []
    params = []
    
    if titol is not None:
        updates.append("titol = ?")
        params.append(titol)
    
    if semestre_codi is not None:
        semestre_id = obtenir_o_crear_semestre(semestre_codi, f"Semestre {semestre_codi}")
        updates.append("semestre = ?")
        params.append(semestre_codi)
        updates.append("semestre_id = ?")
        params.append(semestre_id)
    
    if model_avaluacio is not None:
        updates.append("model_avaluacio = ?")
        params.append(model_avaluacio)
    
    if descripcio is not None:
        updates.append("descripcio = ?")
        params.append(descripcio)
    
    if url is not None:
        updates.append("url = ?")
        params.append(url)
    
    if credits is not None:
        updates.append("credits = ?")
        params.append(credits)
    
    if llengua_codi is not None:
        llengua_id = obtenir_o_crear_llengua(llengua_codi, llengua_codi.upper())
        updates.append("llengua_id = ?")
        params.append(llengua_id)
    
    if professor_nom is not None:
        professor_id = obtenir_o_crear_professor(professor_nom)
        updates.append("professor_id = ?")
        params.append(professor_id)
    
    if actiu is not None:
        updates.append("actiu = ?")
        params.append(actiu)
    
    # Afegir data_modificacio
    updates.append("data_modificacio = CURRENT_TIMESTAMP")
    
    if updates:
        params.append(codi)
        query = f"UPDATE assignatures SET {', '.join(updates)} WHERE codi = ?"
        connexio.execute(query, params)
        
        # Guardar a històric si hi ha canvis
        if len(updates) > 1:  # Excloure data_modificacio
            for update in updates:
                if update != "data_modificacio = CURRENT_TIMESTAMP":
                    camp = update.split(" = ")[0]
                    # Obtenir valor antic
                    valor_antic = connexio.execute(f"SELECT {camp} FROM assignatures WHERE codi = ?", (codi,)).fetchone()[0]
                    # Obtenir valor nou
                    idx = updates.index(update)
                    if idx < len(params) - 1:  # Excloure l'últim paràmetre (codi)
                        valor_nou = params[idx]
                    else:
                        valor_nou = "CURRENT_TIMESTAMP"
                    
                    # Inserir a històric
                    connexio.execute("""
                        INSERT INTO assignatures_historic 
                        (assignatura_id, camp_modificat, valor_antic, valor_nou, usuari)
                        VALUES (?, ?, ?, ?, ?)
                    """, (assignatura['id'], camp, str(valor_antic), str(valor_nou), "system"))
        
        connexio.commit()
    
    connexio.close()
    return True


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


def afegir_favorit(codi, usuari):
    """Afegir una assignatura a favorits per un usuari."""
    connexio = obtenir_connexio()
    
    # Eliminar si ja existia
    connexio.execute("""
        DELETE FROM assignatures_favorites 
        WHERE assignatura_id = (SELECT id FROM assignatures WHERE codi = ?) AND usuari = ?
    """, (codi, usuari))
    
    # Afegir de nou
    connexio.execute("""
        INSERT INTO assignatures_favorites (assignatura_id, usuari)
        VALUES ((SELECT id FROM assignatures WHERE codi = ?), ?)
    """, (codi, usuari))
    
    connexio.commit()
    connexio.close()
    return True


def eliminar_favorit(codi, usuari):
    """Eliminar una assignatura de favorits per un usuari."""
    connexio = obtenir_connexio()
    
    connexio.execute("""
        DELETE FROM assignatures_favorites 
        WHERE assignatura_id = (SELECT id FROM assignatures WHERE codi = ?) AND usuari = ?
    """, (codi, usuari))
    
    connexio.commit()
    connexio.close()
    return True


def obtenir_favorits(usuari):
    """Obtenir totes les assignatures favorites d'un usuari."""
    connexio = obtenir_connexio()
    
    favorits = connexio.execute("""
        SELECT a.id, a.codi, a.titol, a.semestre, a.model_avaluacio, a.descripcio, a.url
        FROM assignatures_favorites af
        JOIN assignatures a ON af.assignatura_id = a.id
        WHERE af.usuari = ?
        ORDER BY af.data_afegit DESC
    """, (usuari,)).fetchall()
    
    connexio.close()
    return favorits
