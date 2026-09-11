#!/usr/bin/env python3
"""
Script per sincronitzar la base de dades amb les assignatures de la UOC.
Només importa els graus especificats i evita duplicats.
Baixa el contingut en català o anglès.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_dades import (
    crear_taules,
    obtenir_connexio,
    obtenir_o_crear_grau,
    existeix_assignatura,
    inserir_assignatura,
    relacionar_grau_assignatura,
    obtenir_assignatures,
    actualitzar_detall_assignatura
)
from scraper import (
    llegir_assignatures_grau,
    llegir_detall_assignatura,
    esborrar_cache,
    obtenir_llista_graus_uoc
)
import time

# Graus que ens interessen (segons l'usuari)
GRAUS_A_IMPORTAR = [
    "Grau de Ciència de Dades Aplicada",
    "Grau de Desenvolupament i Proves de Software",
    "Grau d'Enginyeria i Telecomunicació",
    "Grau de Multimèdia",
    "Grau d'Enginyeria Biomèdica",
    "Grau d'Enginyeria Informàtica"
]

def sincronitzar():
    """Sincronitzar assignatures de la UOC amb la base de dades."""
    
    print("=" * 70)
    print("SINCRONITZANT BASE DE DADES AMB WEB UOC")
    print("=" * 70)
    print()
    
    # Esborrar cache per obtenir dades fresques
    print("Esborrant cache...")
    esborrar_cache()
    print("✅ Cache esborrat\n")
    
    # Obtenir llista de graus
    graus_coneguts = obtenir_llista_graus_uoc()
    
    # Filtrar només els graus que ens interessen
    graus_a_importar = [g for g in graus_coneguts if g['nom'] in GRAUS_A_IMPORTAR]
    
    print(f"Graus a importar: {len(graus_a_importar)}")
    for grau in graus_a_importar:
        print(f"  - {grau['nom']}")
    print()
    
    total_importades = 0
    total_actualitzades = 0
    total_relacionades = 0
    
    # Processar cada grau
    for grau in graus_a_importar:
        print(f"Processant: {grau['nom']}...")
        
        try:
            # Obtenir assignatures del grau des de la web
            print("  Obtenint assignatures de la web...")
            web_assignatures = llegir_assignatures_grau(grau['url'])
            print(f"  📥 Trobades {len(web_assignatures)} assignatures a la web")
            
            # Obtenir o crear el grau a la BD
            grau_id = obtenir_o_crear_grau(grau['nom'], grau['url'])
            print(f"  📝 Grau ID: {grau_id}")
            
            # Processar cada assignatura
            for idx, assignatura in enumerate(web_assignatures, 1):
                codi = assignatura['codi']
                titol = assignatura['titol']
                url = assignatura['url']
                
                # Comprovar si existeix
                if not existeix_assignatura(codi):
                    # Inserir nova assignatura
                    inserir_assignatura(
                        codi,
                        titol,
                        "2026-1",  # Semestre per defecte
                        "Pendent",
                        "Pendent de llegir el pla docent",
                        url
                    )
                    total_importades += 1
                    print(f"  ✅ Importada: {codi} - {titol[:50]}")
                else:
                    print(f"  ✓ Ja existeix: {codi} - {titol[:50]}")
                
                # Relacionar assignatura amb grau
                relacionar_grau_assignatura(grau_id, codi)
                total_relacionades += 1
                
                # Mostrar progrés cada 10 assignatures
                if idx % 10 == 0:
                    print(f"  ... Processades {idx}/{len(web_assignatures)} assignatures")
            
            print(f"  ✅ Processades {len(web_assignatures)} assignatures\n")
            
        except Exception as e:
            print(f"  ❌ Error processant {grau['nom']}: {e}\n")
            import traceback
            traceback.print_exc()
            continue
    
    # Ara actualitzar els detalls de les assignatures que tenen model_avaluacio = "Pendent"
    print("\n" + "=" * 70)
    print("ACTUALITZANT DETALLS DE LES ASSIGNATURES PENDENTS")
    print("=" * 70)
    print()
    
    # Obtenir totes les assignatures de la BD
    all_assignatures = obtenir_assignatures()
    pendents = [a for a in all_assignatures if a['model_avaluacio'] == 'Pendent']
    
    print(f"Assignatures pendents d'actualitzar: {len(pendents)}")
    print()
    
    for idx, assignatura in enumerate(pendents, 1):
        codi = assignatura['codi']
        url = assignatura['url']
        
        try:
            print(f"Actualitzant {idx}/{len(pendents)}: {codi}...")
            detall = llegir_detall_assignatura(url)
            
            # Actualitzar amb els nous camps
            actualitzar_detall_assignatura(
                codi,
                detall['model_avaluacio'],
                detall['descripcio']
            )
            
            total_actualitzades += 1
            print(f"  ✅ {codi}: Model={detall['model_avaluacio']}, Crèdits={detall['credits']}, Llengua={detall['llengua']}")
            
        except Exception as e:
            print(f"  ❌ Error actualitzant {codi}: {e}")
            # Continuar amb la següent
            pass
    
    print()
    print("=" * 70)
    print("RESUM DE LA SINCRONITZACIÓ")
    print("=" * 70)
    print(f"Assignatures importades:        {total_importades}")
    print(f"Relacions creades:             {total_relacionades}")
    print(f"Assignatures actualitzades:     {total_actualitzades}")
    print(f"Total assignatures a la BD:   {len(obtenir_assignatures())}")
    print()
    
    # Comprovar sincronització
    print("Comprovant sincronització...")
    for grau in graus_a_importar:
        web_assignatures = llegir_assignatures_grau(grau['url'])
        all_bd = obtenir_assignatures()
        bd_for_grau = [a for a in all_bd if a['graus'] and grau['nom'] in a['graus']]
        
        web_codes = {a['codi'] for a in web_assignatures}
        bd_codes = {a['codi'] for a in bd_for_grau}
        
        missing = web_codes - bd_codes
        
        status = "✅" if not missing else "⚠️"
        print(f"  {status} {grau['nom']}: Web={len(web_assignatures)}, BD={len(bd_for_grau)}")

if __name__ == "__main__":
    sincronitzar()
