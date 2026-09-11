#!/usr/bin/env python3
"""
Script per migrar la base de dades actual a la nova versió.
Afegeix nous camps, taules auxiliars i índexs.
"""

import sqlite3
import os
import sys

# Ruta de la base de dades
DB_PATH = "dades/assignatures.sqlite"

def migrar_base_dades():
    """Migrar l'esquema actual al nou esquema."""
    
    # Comprovar que la base de dades existeix
    if not os.path.exists(DB_PATH):
        print(f"Error: La base de dades {DB_PATH} no existeix.")
        sys.exit(1)
    
    print("Iniciant migració de la base de dades...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Funció per comprovar si una columna existeix
    def columna_existeix(taula, columna):
        cursor.execute(f"PRAGMA table_info({taula})")
        return any(row[1] == columna for row in cursor.fetchall())
    
    try:
        # 1. Afegir nous camps a assignatures (només si no existeixen)
        print("Afegint nous camps a la taula assignatures...")
        
        if not columna_existeix('assignatures', 'credits'):
            cursor.execute("ALTER TABLE assignatures ADD COLUMN credits INTEGER")
        
        if not columna_existeix('assignatures', 'data_creacio'):
            cursor.execute("ALTER TABLE assignatures ADD COLUMN data_creacio TIMESTAMP")
        
        if not columna_existeix('assignatures', 'data_modificacio'):
            cursor.execute("ALTER TABLE assignatures ADD COLUMN data_modificacio TIMESTAMP")
        
        # 2. Crear taula de llengües
        print("Creant taula de llengües...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llengues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codi TEXT NOT NULL UNIQUE,
                nom TEXT NOT NULL
            )
        """)
        
        # 3. Afegir llengües per defecte
        llengues = [('ca', 'Català'), ('es', 'Castellà'), ('en', 'Anglès')]
        cursor.executemany(
            "INSERT OR IGNORE INTO llengues (codi, nom) VALUES (?, ?)",
            llengues
        )
        
        # 4. Afegir columna llengua_id a assignatures (només si no existeix)
        print("Afegint camp llengua_id a assignatures...")
        if not columna_existeix('assignatures', 'llengua_id'):
            cursor.execute("ALTER TABLE assignatures ADD COLUMN llengua_id INTEGER")
            
            # 5. Actualitzar llengua per defecte (Català)
            cursor.execute("""
                UPDATE assignatures 
                SET llengua_id = (SELECT id FROM llengues WHERE codi = 'ca')
                WHERE llengua_id IS NULL
            """)
        
        # 6. Crear taula de semestres acadèmics
        print("Creant taula de semestres acadèmics...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semestres_academics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codi TEXT NOT NULL UNIQUE,
                nom TEXT NOT NULL,
                data_inici DATE,
                data_final DATE
            )
        """)
        
        # 7. Inserir semestres coneguts
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
        
        # 8. Afegir columna semestre_id a assignatures
        print("Afegint camp semestre_id a assignatures...")
        if not columna_existeix('assignatures', 'semestre_id'):
            cursor.execute("ALTER TABLE assignatures ADD COLUMN semestre_id INTEGER")
        
        # 9. Mapejar valors actuals de semestre a semestre_id
        mapping = {
            '2026-1': 3,  # Primer semestre 2026
            '2025-2': 2,  # Segon semestre 2025
            '2025-1': 1,  # Primer semestre 2025
            '2026-2': 4,  # Segon semestre 2026
        }
        
        for codi_semestre, semestre_id in mapping.items():
            cursor.execute("""
                UPDATE assignatures 
                SET semestre_id = ?
                WHERE semestre = ?
            """, (semestre_id, codi_semestre))
        
        # 10. Crear taula de professors
        print("Creant taula de professors...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS professors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                email TEXT,
                departament TEXT
            )
        """)
        
        # 11. Afegir camp professor_id a assignatures
        if not columna_existeix('assignatures', 'professor_id'):
            cursor.execute("ALTER TABLE assignatures ADD COLUMN professor_id INTEGER")
        
        # 12. Afegir camp actiu a assignatures i graus
        print("Afegint camp actiu a assignatures i graus...")
        if not columna_existeix('assignatures', 'actiu'):
            cursor.execute("ALTER TABLE assignatures ADD COLUMN actiu BOOLEAN DEFAULT 1")
        
        if not columna_existeix('graus', 'actiu'):
            cursor.execute("ALTER TABLE graus ADD COLUMN actiu BOOLEAN DEFAULT 1")
        
        # 13. Afegir camp data_creacio a graus
        if not columna_existeix('graus', 'data_creacio'):
            cursor.execute("ALTER TABLE graus ADD COLUMN data_creacio TIMESTAMP")
        
        # 14. Afegir camp facultat a graus
        print("Afegint camp facultat a graus...")
        if not columna_existeix('graus', 'facultat'):
            cursor.execute("ALTER TABLE graus ADD COLUMN facultat TEXT")
            # Actualitzar amb valor per defecte
            cursor.execute("UPDATE graus SET facultat = ? WHERE facultat IS NULL", 
                           ("Estudis d'Informàtica",))
        
        # 15. Crear taula d'històric de canvis
        print("Creant taula d'històric de canvis...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignatures_historic (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignatura_id INTEGER NOT NULL,
                camp_modificat TEXT NOT NULL,
                valor_antic TEXT,
                valor_nou TEXT,
                data_modificacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuari TEXT,
                FOREIGN KEY (assignatura_id) REFERENCES assignatures(id)
            )
        """)
        
        # 16. Crear índexs per millorar rendiment
        print("Creant índexs per millorar rendiment...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignatures_codi ON assignatures(codi)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignatures_model_avaluacio ON assignatures(model_avaluacio)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignatures_actiu ON assignatures(actiu)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_graus_assignatures_grau ON graus_assignatures(grau_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_graus_assignatures_assignatura ON graus_assignatures(assignatura_codi)")
        
        # 17. Afegir camp data_aprovacio a assignatures_aprovades
        print("Actualitzant taula assignatures_aprovades...")
        if not columna_existeix('assignatures_aprovades', 'data_aprovacio'):
            cursor.execute("ALTER TABLE assignatures_aprovades ADD COLUMN data_aprovacio DATE")
        
        # 18. Afegir camp assignatura_id a assignatures_aprovades
        if not columna_existeix('assignatures_aprovades', 'assignatura_id'):
            cursor.execute("ALTER TABLE assignatures_aprovades ADD COLUMN assignatura_id INTEGER")
            
            # Actualitzar assignatura_id amb la relació
            cursor.execute("""
                UPDATE assignatures_aprovades 
                SET assignatura_id = (
                    SELECT id FROM assignatures 
                    WHERE assignatures.codi = assignatures_aprovades.codi
                )
            """)
        
        conn.commit()
        print("\nMigració completada amb èxit!")
        
        # Mostrar resum
        print("\n=== Resum de la migració ===")
        cursor.execute("SELECT COUNT(*) FROM assignatures")
        total_assignatures = cursor.fetchone()[0]
        print(f"Assignatures totals: {total_assignatures}")
        
        cursor.execute("SELECT COUNT(*) FROM graus")
        total_graus = cursor.fetchone()[0]
        print(f"Graus totals: {total_graus}")
        
        cursor.execute("SELECT COUNT(*) FROM llengues")
        total_llengues = cursor.fetchone()[0]
        print(f"Llengües totals: {total_llengues}")
        
        cursor.execute("SELECT COUNT(*) FROM semestres_academics")
        total_semestres = cursor.fetchone()[0]
        print(f"Semestres totals: {total_semestres}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\nError durant la migració: {e}")
        print("Canvis desfits. La base de dades roman sense canvis.")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # Canviar a el directori del projecte
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")
    
    success = migrar_base_dades()
    sys.exit(0 if success else 1)
