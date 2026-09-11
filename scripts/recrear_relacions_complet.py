#!/usr/bin/env python3
"""
Script per recrear TOTES les relacions graus_assignatures.
1. Esborra TOTES les relacions existents
2. Tornar a crear-les basant-se en les assignatures actuals de la web
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from base_dades import obtenir_connexio, obtenir_o_crear_grau
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

def recrear_relacions():
    print("=" * 70)
    print("RECREANT TOTES LES RELACIONS GRAUS-ASSIGNATURES")
    print("=" * 70)
    print()
    
    # 1. Esborrar TOTES les relacions existents
    print("Esborrant TOTES les relacions existents...")
    conn = obtenir_connexio()
    conn.execute("DELETE FROM graus_assignatures")
    conn.commit()
    
    # Verificar que s'han esborrat
    cursor = conn.execute("SELECT COUNT(*) FROM graus_assignatures")
    count = cursor.fetchone()[0]
    print(f"  Relacions després d'esborrar: {count}")
    conn.close()
    print("✅ Totes les relacions esborrades\n")
    
    # 2. Esborrar cache
    esborrar_cache()
    
    # 3. Tornar a crear les relacions des de zero
    print("Creant noves relacions des de la web...")
    
    graus_coneguts = obtenir_llista_graus_uoc()
    graus_a_importar = [g for g in graus_coneguts if g['nom'] in GRAUS_A_IMPORTAR]
    
    total_relacions = 0
    
    for grau in graus_a_importar:
        print(f"  Processant: {grau['nom']}")
        
        try:
            # Obtenir assignatures del grau des de la web
            web_assignatures = llegir_assignatures_grau(grau['url'])
            print(f"    Assignatures a la web: {len(web_assignatures)}")
            
            # Obtenir ID del grau
            grau_id = obtenir_o_crear_grau(grau['nom'], grau['url'])
            
            # Crear relacions per totes les assignatures
            for assignatura in web_assignatures:
                codi = assignatura['codi']
                
                conn = obtenir_connexio()
                conn.execute(
                    "INSERT OR IGNORE INTO graus_assignatures (grau_id, assignatura_codi) VALUES (?, ?)",
                    (grau_id, codi)
                )
                conn.commit()
                conn.close()
                total_relacions += 1
            
            print(f"    ✅ {len(web_assignatures)} relacions creades")
            print()
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()
            continue
    
    print(f"✅ Total relacions creades: {total_relacions}\n")
    
    # 4. Verificar
    print("=" * 70)
    print("VERIFICACIÓ: Relacions per grau")
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
    print("COMPROVACIÓ FINAL DE SINCRONITZACIÓ")
    print("=" * 70)
    
    esborrar_cache()
    
    sincronitzat = True
    for grau in graus_a_importar:
        web_assignatures = llegir_assignatures_grau(grau['url'])
        grau_id = obtenir_o_crear_grau(grau['nom'], grau['url'])
        bd_assignatures = obtenir_assignatures_per_grau(grau_id)
        
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
            sincronitzat = False
    
    print()
    if sincronitzat:
        print("🎉 TOTES LES ASSIGNATURES ESTAN PERFECTAMENT SINCRONITZADES!")
    else:
        print("⚠️  Hi ha discrepàncies")
    
    return sincronitzat

if __name__ == "__main__":
    success = recrear_relacions()
    sys.exit(0 if success else 1)
