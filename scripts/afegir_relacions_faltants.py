#!/usr/bin/env python3
"""
Script per afegir les relacions que falten entre graus i assignatures.
NO esborra les relacions existents, només afegeix les que falten.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_dades import (
    obtenir_connexio,
    obtenir_o_crear_grau,
    obtenir_assignatures,
    existeix_assignatura
)
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

def afegir_relacions_faltants():
    print("=" * 70)
    print("AFEGINT RELACIONS FALTANTS")
    print("=" * 70)
    print()
    
    # Esborrar cache
    esborrar_cache()
    
    graus_coneguts = obtenir_llista_graus_uoc()
    graus_a_importar = [g for g in graus_coneguts if g['nom'] in GRAUS_A_IMPORTAR]
    
    total_relacions_afegides = 0
    
    for grau in graus_a_importar:
        print(f"Processant: {grau['nom']}")
        
        try:
            # Obtenir assignatures del grau des de la web
            web_assignatures = llegir_assignatures_grau(grau['url'])
            web_codes = {a['codi'] for a in web_assignatures}
            print(f"  Assignatures a la web: {len(web_assignatures)}")
            
            # Obtenir ID del grau
            grau_id = obtenir_o_crear_grau(grau['nom'], grau['url'])
            
            # Obtenir assignatures actuals de la BD per aquest grau
            conn = obtenir_connexio()
            cursor = conn.execute("""
                SELECT assignatura_codi 
                FROM graus_assignatures 
                WHERE grau_id = ?
            """, (grau_id,))
            bd_codes = {row['assignatura_codi'] for row in cursor.fetchall()}
            conn.close()
            
            print(f"  Assignatures a la BD: {len(bd_codes)}")
            
            # Trobar les que falten
            missing = web_codes - bd_codes
            print(f"  Relacions que falten: {len(missing)}")
            
            # Afegir les relacions que falten
            if missing:
                for codi in missing:
                    # Comprovar que l'assignatura existeix a la BD
                    if existeix_assignatura(codi):
                        conn = obtenir_connexio()
                        conn.execute(
                            "INSERT OR IGNORE INTO graus_assignatures (grau_id, assignatura_codi) VALUES (?, ?)",
                            (grau_id, codi)
                        )
                        conn.commit()
                        conn.close()
                        total_relacions_afegides += 1
                        
                print(f"  ✅ {len(missing)} relacions afegides")
            else:
                print(f"  ✅ No falten relacions")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 70)
    print(f"RESUM: {total_relacions_afegides} relacions afegides")
    print("=" * 70)
    print()
    
    # Verificar
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
        grau_id = obtenir_o_crear_grau(grau['nom'], grau['url'])
        web_assignatures = llegir_assignatures_grau(grau['url'])
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

if __name__ == "__main__":
    afegir_relacions_faltants()
