#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_dades import obtenir_assignatures_per_grau, obtenir_graus

graus = obtenir_graus()

print("Assignatures per grau després de la sincronització:")
print("=" * 70)

total = 0
for grau in graus:
    assignatures = obtenir_assignatures_per_grau(grau['id'])
    total += len(assignatures)
    print(f"{grau['nom']:50s}: {len(assignatures):3d} assignatures")

print("=" * 70)
print(f"Total: {total} assignatures")

# Comprovar si està sincronitzat
from scraper import obtenir_llista_graus_uoc, esborrar_cache

esborrar_cache()

GRAUS_A_IMPORTAR = [
    "Grau de Ciència de Dades Aplicada",
    "Grau de Desenvolupament i Proves de Software",
    "Grau d'Enginyeria i Telecomunicació",
    "Grau de Multimèdia",
    "Grau d'Enginyeria Biomèdica",
    "Grau d'Enginyeria Informàtica"
]

print("\n" + "=" * 70)
print("COMPROVACIÓ DE SINCRONITZACIÓ")
print("=" * 70)

for grau in graus:
    if grau['nom'] not in GRAUS_A_IMPORTAR:
        continue
    
    from scraper import llegir_assignatures_grau
    web_assignatures = llegir_assignatures_grau(grau['url'])
    bd_assignatures = obtenir_assignatures_per_grau(grau['id'])
    
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
