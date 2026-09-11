#!/usr/bin/env python3
"""
Script per importar TOTES les assignatures dels graus especificats.
Baixa el contingut en català o anglès.
NO duplica assignatures (comprova per codi).
Crea les relacions graus_assignatures.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_dades import (
    obtenir_o_crear_grau,
    existeix_assignatura,
    inserir_assignatura,
    relacionar_grau_assignatura,
    obtenir_assignatures_per_grau,
    obtenir_graus
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

def importar_tot():
    print("=" * 70)
    print("IMPORTANT TOTES LES ASSIGNATURES DELS GRAUS ESPECIFICATS")
    print("=" * 70)
    print()
    
    # Esborrar cache
    esborrar_cache()
    print("✅ Cache esborrat\n")
    
    graus_coneguts = obtenir_llista_graus_uoc()
    graus_a_importar = [g for g in graus_coneguts if g['nom'] in GRAUS_A_IMPORTAR]
    
    print(f"Graus a importar: {len(graus_a_importar)}")
    for grau in graus_a_importar:
        print(f"  - {grau['nom']}")
    print()
    
    total_importades = 0
    total_relacionades = 0
    total_ja_existien = 0
    
    # Processar cada grau
    for grau in graus_a_importar:
        print(f"Processant: {grau['nom']}")
        
        try:
            # Obtenir assignatures del grau des de la web
            web_assignatures = llegir_assignatures_grau(grau['url'])
            print(f"  Trobades {len(web_assignatures)} assignatures a la web")
            
            # Obtenir o crear el grau a la BD
            grau_id = obtenir_o_crear_grau(grau['nom'], grau['url'])
            
            # Processar cada assignatura
            for assignatura in web_assignatures:
                codi = assignatura['codi']
                titol = assignatura['titol']
                url = assignatura['url']
                
                # Comprovar si existeix
                if not existeix_assignatura(codi):
                    # Inserir nova assignatura
                    inserir_assignatura(
                        codi,
                        titol,
                        "2026-1",
                        "Pendent",
                        "Pendent de llegir el pla docent",
                        url
                    )
                    total_importades += 1
                else:
                    total_ja_existien += 1
                
                # Relacionar assignatura amb grau
                relacionar_grau_assignatura(grau_id, codi)
                total_relacionades += 1
            
            print(f"  ✅ Importades: {total_importades}, Ja existien: {total_ja_existien}, Relacionades: {total_relacionades}")
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()
            continue
    
    print("=" * 70)
    print("RESUM DE LA IMPORTACIÓ")
    print("=" * 70)
    print(f"Assignatures importades:     {total_importades}")
    print(f"Assignatures ja existents:   {total_ja_existien}")
    print(f"Relacions creades:          {total_relacionades}")
    print()
    
    # Verificar assignatures per grau
    print("VERIFICACIÓ: Assignatures per grau")
    print("=" * 70)
    
    graus = obtenir_graus()
    for grau in graus:
        if grau['nom'] not in GRAUS_A_IMPORTAR:
            continue
        
        assignatures = obtenir_assignatures_per_grau(grau['id'])
        print(f"{grau['nom']:50s}: {len(assignatures):3d} assignatures")
    print()
    
    # Comprovar sincronització
    print("=" * 70)
    print("COMPROVACIÓ DE SINCRONITZACIÓ")
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
        print("🎉 TOTES LES ASSIGNATURES ESTAN SINCRONITZADES!")
    else:
        print("⚠️  Hi ha discrepàncies")

if __name__ == "__main__":
    importar_tot()
