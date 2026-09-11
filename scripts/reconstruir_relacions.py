#!/usr/bin/env python3
"""
Script per reconstruir les relacions entre graus i assignatures.
Esborra les relacions existents i les tornar a crear correctament.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from base_dades import obtenir_connexio, obtenir_o_crear_grau, obtenir_assignatures
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

def reconstruir_relacions():
    print("=" * 70)
    print("RECONSTRUINT RELACIONS GRAUS-ASSIGNATURES")
    print("=" * 70)
    print()
    
    # 1. Esborrar totes les relacions existents per als graus que ens interessen
    print("Esborrant relacions existents...")
    conn = obtenir_connexio()
    
    for grau_nom in GRAUS_A_IMPORTAR:
        cursor = conn.execute("SELECT id FROM graus WHERE nom = ?", (grau_nom,))
        grau_id = cursor.fetchone()
        if grau_id:
            conn.execute("DELETE FROM graus_assignatures WHERE grau_id = ?", (grau_id['id'],))
            print(f"  Esborrades relacions per: {grau_nom}")
    
    conn.commit()
    conn.close()
    print("✅ Relacions existents esborrades\n")
    
    # 2. Tornar a crear les relacions correctament
    print("Creant noves relacions...")
    
    graus_coneguts = obtenir_llista_graus_uoc()
    graus_a_importar = [g for g in graus_coneguts if g['nom'] in GRAUS_A_IMPORTAR]
    
    total_relacions = 0
    
    for grau in graus_a_importar:
        print(f"  Processant: {grau['nom']}")
        
        try:
            # Obtenir assignatures del grau des de la web
            web_assignatures = llegir_assignatures_grau(grau['url'])
            print(f"    Trobades {len(web_assignatures)} assignatures a la web")
            
            # Obtenir ID del grau
            grau_id = obtenir_o_crear_grau(grau['nom'], grau['url'])
            
            # Crear relacions
            for assignatura in web_assignatures:
                codi = assignatura['codi']
                
                # Inserir relació
                conn = obtenir_connexio()
                conn.execute(
                    "INSERT OR IGNORE INTO graus_assignatures (grau_id, assignatura_codi) VALUES (?, ?)",
                    (grau_id, codi)
                )
                conn.commit()
                conn.close()
                total_relacions += 1
            
            print(f"    ✅ {len(web_assignatures)} relacions creades")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ Total relacions creades: {total_relacions}\n")
    
    # 3. Verificar
    print("=" * 70)
    print("VERIFICACIÓ DE RELACIONS")
    print("=" * 70)
    
    from base_dades import obtenir_assignatures_per_grau, obtenir_graus
    
    graus = obtenir_graus()
    for grau in graus:
        if grau['nom'] not in GRAUS_A_IMPORTAR:
            continue
        
        assignatures = obtenir_assignatures_per_grau(grau['id'])
        print(f"{grau['nom']:50s}: {len(assignatures):3d} assignatures")
    
    # Comprovar sincronització
    print("\n" + "=" * 70)
    print("COMPROVACIÓ DE SINCRONITZACIÓ")
    print("=" * 70)
    
    esborrar_cache()
    
    for grau in graus_a_importar:
        web_assignatures = llegir_assignatures_grau(grau['url'])
        bd_assignatures = obtenir_assignatures_per_grau(obtenir_o_crear_grau(grau['nom'], grau['url']))
        
        web_codes = {a['codi'] for a in web_assignatures}
        bd_codes = {a['codi'] for a in bd_assignatures}
        
        missing_in_bd = web_codes - bd_codes
        missing_in_web = bd_codes - web_codes
        
        if not missing_in_bd and not missing_in_web:
            print(f"✅ {grau['nom']:50s}: Web={len(web_assignatures)}, BD={len(bd_assignatures)}")
        else:
            print(f"⚠️  {grau['nom']:50s}: Web={len(web_assignatures)}, BD={len(bd_assignatures)}")
            if missing_in_bd:
                print(f"     Falten a BD: {sorted(list(missing_in_bd)[:5])}...")
            if missing_in_web:
                print(f"     Falten a WEB: {sorted(list(missing_in_web)[:5])}...")

if __name__ == "__main__":
    reconstruir_relacions()
