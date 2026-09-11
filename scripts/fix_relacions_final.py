#!/usr/bin/env python3
"""
Script FINAL per fixar les relacions.
1. Esborra TOTES les relacions
2. Crea TOTES les relacions de nou en una transacció
3. Verifica
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from scraper import obtenir_llista_graus_uoc, llegir_assignatures_grau, esborrar_cache

# Graus que ens interessen
GRAUS_A_IMPORTAR = [
    "Grau de Ciència de Dades Aplicada",
    "Grau de Desenvolupament i Proves de Software",
    "Grau d'Enginyeria i Telecomunicació",
    "Grau de Multimèdia",
    "Grau d'Enginyeria Biomèdica",
    "Grau d'Enginyeria Informàtica"
]

def fix_relacions():
    print("=" * 70)
    print("FIXANT RELACIONS DEFINITIVAMENT")
    print("=" * 70)
    print()
    
    # Connectar a la base de dades (UNA SOLA CONNEXIÓ)
    conn = sqlite3.connect('dades/assignatures.sqlite')
    cursor = conn.cursor()
    
    try:
        # 1. Esborrar TOTES les relacions
        print("Esborrant TOTES les relacions...")
        cursor.execute("DELETE FROM graus_assignatures")
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM graus_assignatures")
        count = cursor.fetchone()[0]
        print(f"  Relacions després d'esborrar: {count}")
        print("✅ Relacions esborrades\n")
        
        # 2. Obtenir graus de la web
        esborrar_cache()
        graus_coneguts = obtenir_llista_graus_uoc()
        graus_a_importar = [g for g in graus_coneguts if g['nom'] in GRAUS_A_IMPORTAR]
        
        print("Creant relacions...")
        total_relacions = 0
        
        # Obtenir IDs dels graus
        grau_ids = {}
        for grau in graus_a_importar:
            cursor.execute("SELECT id FROM graus WHERE nom = ?", (grau['nom'],))
            row = cursor.fetchone()
            if row:
                grau_ids[grau['nom']] = row[0]
            else:
                # Crear el grau si no existeix
                cursor.execute("INSERT INTO graus (nom, url) VALUES (?, ?)", (grau['nom'], grau['url']))
                grau_ids[grau['nom']] = cursor.lastrowid
                conn.commit()
        
        # Per cada grau, obtenir assignatures de la web i crear relacions
        for grau in graus_a_importar:
            if grau['nom'] not in grau_ids:
                continue
            
            grau_id = grau_ids[grau['nom']]
            print(f"  Processant: {grau['nom']} (ID: {grau_id})")
            
            try:
                web_assignatures = llegir_assignatures_grau(grau['url'])
                print(f"    Assignatures a la web: {len(web_assignatures)}")
                
                # Crear totes les relacions en una sola transacció
                for assignatura in web_assignatures:
                    codi = assignatura['codi']
                    
                    # Verificar que l'assignatura existeix
                    cursor.execute("SELECT id FROM assignatures WHERE codi = ?", (codi,))
                    if cursor.fetchone():
                        cursor.execute(
                            "INSERT OR IGNORE INTO graus_assignatures (grau_id, assignatura_codi) VALUES (?, ?)",
                            (grau_id, codi)
                        )
                        total_relacions += 1
                    else:
                        print(f"    ⚠️  Assignatura {codi} no existeix a la BD")
                
                print(f"    ✅ {len(web_assignatures)} relacions afegides")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        # Commit de totes les relacions
        conn.commit()
        print(f"\n✅ Commit de {total_relacions} relacions\n")
        
        # 3. Verificar
        print("=" * 70)
        print("VERIFICACIÓ: Relacions per grau")
        print("=" * 70)
        
        cursor.execute("""
            SELECT g.nom, COUNT(*) as count
            FROM graus_assignatures ga
            JOIN graus g ON ga.grau_id = g.id
            GROUP BY g.id
            ORDER BY g.id
        """)
        
        for row in cursor.fetchall():
            print(f"{row[0]:50s}: {row[1]:3d} assignatures")
        
        cursor.execute("SELECT COUNT(*) FROM graus_assignatures")
        total_final = cursor.fetchone()[0]
        print(f"\nTotal relacions: {total_final}")
        
        # Verificar sincronització
        print("\n" + "=" * 70)
        print("COMPROVACIÓ FINAL")
        print("=" * 70)
        
        sincronitzat = True
        for grau in graus_a_importar:
            web_assignatures = llegir_assignatures_grau(grau['url'])
            web_codes = {a['codi'] for a in web_assignatures}
            
            # Obtenir codis de la BD per aquest grau
            cursor.execute("""
                SELECT assignatura_codi 
                FROM graus_assignatures 
                WHERE grau_id = ?
            """, (grau_ids[grau['nom']],))
            bd_codes = {row[0] for row in cursor.fetchall()}
            
            missing_in_bd = web_codes - bd_codes
            missing_in_web = bd_codes - web_codes
            
            if not missing_in_bd and not missing_in_web:
                print(f"✅ {grau['nom']:50s}: Web={len(web_assignatures)}, BD={len(bd_codes)}")
            else:
                print(f"⚠️  {grau['nom']:50s}: Web={len(web_assignatures)}, BD={len(bd_codes)}")
                if missing_in_bd:
                    print(f"     Falten a BD: {sorted(list(missing_in_bd)[:5])}...")
                if missing_in_web:
                    print(f"     Falten a WEB: {sorted(list(missing_in_web)[:5])}...")
                sincronitzat = False
        
        print()
        if sincronitzat:
            print("🎉 TOT ESTÀ PERFECTAMENT SINCRONITZAT!")
        else:
            print("⚠️  Hi ha discrepàncies")
        
        return sincronitzat
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = fix_relacions()
    sys.exit(0 if success else 1)
