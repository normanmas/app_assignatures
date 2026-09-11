#!/usr/bin/env python3
"""
Script DEFINITIU per sincronitzar la base de dades amb la web UOC.
1. Esborra TOTES les relacions graus_assignatures
2. Crea les relacions basant-se en les assignatures de la web (SENSE DUPLICATS)
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

def sincronitzar():
    print("=" * 70)
    print("SINCRONITZACIÓ DEFINITIVA AMB LA WEB UOC")
    print("=" * 70)
    print()
    
    # Connectar a la base de dades
    conn = sqlite3.connect('dades/assignatures.sqlite')
    cursor = conn.cursor()
    
    try:
        # 1. Esborrar TOTES les relacions
        print("Esborrant TOTES les relacions existents...")
        cursor.execute("DELETE FROM graus_assignatures")
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM graus_assignatures")
        count = cursor.fetchone()[0]
        print(f"  Relacions després d'esborrar: {count}")
        print("✅ Relacions esborrades\n")
        
        # 2. Esborrar cache
        esborrar_cache()
        
        # 3. Obtenir graus de la web
        graus_coneguts = obtenir_llista_graus_uoc()
        graus_a_importar = [g for g in graus_coneguts if g['nom'] in GRAUS_A_IMPORTAR]
        
        print("Creant relacions (sense duplicats)...")
        total_relacions = 0
        
        # Obtenir IDs dels graus
        grau_ids = {}
        for grau in graus_a_importar:
            cursor.execute("SELECT id FROM graus WHERE nom = ?", (grau['nom'],))
            row = cursor.fetchone()
            if row:
                grau_ids[grau['nom']] = row[0]
            else:
                cursor.execute("INSERT INTO graus (nom, url) VALUES (?, ?)", (grau['nom'], grau['url']))
                grau_ids[grau['nom']] = cursor.lastrowid
                conn.commit()
        
        # Per cada grau, obtenir assignatures UNIQUES de la web i crear relacions
        for grau in graus_a_importar:
            if grau['nom'] not in grau_ids:
                continue
            
            grau_id = grau_ids[grau['nom']]
            print(f"  Processant: {grau['nom']} (ID: {grau_id})")
            
            try:
                # Obtenir assignatures de la web
                web_assignatures = llegir_assignatures_grau(grau['url'])
                
                # DEDUPLICAR: Només un codi per assignatura
                unique_assignatures = {}
                for assignatura in web_assignatures:
                    codi = assignatura['codi']
                    if codi not in unique_assignatures:
                        unique_assignatures[codi] = assignatura
                
                web_assignatures = list(unique_assignatures.values())
                print(f"    Assignatures úniques a la web: {len(web_assignatures)} (abans: {len(web_assignatures) + sum(len(web_assignatures) - len(set(a['codi'] for a in web_assignatures)) for _ in [1])} amb duplicats)")
                
                # Crear relacions
                for assignatura in web_assignatures:
                    codi = assignatura['codi']
                    
                    # Verificar que l'assignatura existeix a la BD
                    cursor.execute("SELECT id FROM assignatures WHERE codi = ?", (codi,))
                    if cursor.fetchone():
                        cursor.execute(
                            "INSERT OR IGNORE INTO graus_assignatures (grau_id, assignatura_codi) VALUES (?, ?)",
                            (grau_id, codi)
                        )
                        total_relacions += 1
                    else:
                        print(f"    ⚠️  Assignatura {codi} no existeix a la BD")
                
                print(f"    ✅ {len(web_assignatures)} relacions creades")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        # Commit de totes les relacions
        conn.commit()
        print(f"\n✅ Commit de {total_relacions} relacions\n")
        
        # 4. Verificar
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
        print("COMPROVACIÓ FINAL DE SINCRONITZACIÓ")
        print("=" * 70)
        
        sincronitzat = True
        all_web_codes_per_grau = {}
        
        # Obtenir tots els codis de la web per grau (sense duplicats)
        for grau in graus_a_importar:
            assignatures = llegir_assignatures_grau(grau['url'])
            unique_codes = {a['codi'] for a in assignatures}
            all_web_codes_per_grau[grau['nom']] = unique_codes
        
        for grau in graus_a_importar:
            grau_id = grau_ids[grau['nom']]
            
            # Obtenir codis de la BD per aquest grau
            cursor.execute("""
                SELECT assignatura_codi 
                FROM graus_assignatures 
                WHERE grau_id = ?
            """, (grau_id,))
            bd_codes = {row[0] for row in cursor.fetchall()}
            
            web_codes = all_web_codes_per_grau[grau['nom']]
            
            missing_in_bd = web_codes - bd_codes
            missing_in_web = bd_codes - web_codes
            
            if not missing_in_bd and not missing_in_web:
                print(f"✅ {grau['nom']:50s}: Web={len(web_codes)}, BD={len(bd_codes)}")
            else:
                print(f"⚠️  {grau['nom']:50s}: Web={len(web_codes)}, BD={len(bd_codes)}")
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
    success = sincronitzar()
    sys.exit(0 if success else 1)
