#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_dades import obtenir_assignatures, existeix_assignatura, obtenir_connexio
from scraper import obtenir_llista_graus_uoc, llegir_assignatures_grau, esborrar_cache

esborrar_cache()

# Obtenir tots els codis de la web
all_web_codes = set()
graus = obtenir_llista_graus_uoc()
GRAUS_A_IMPORTAR = [
    "Grau de Ciència de Dades Aplicada",
    "Grau de Desenvolupament i Proves de Software",
    "Grau d'Enginyeria i Telecomunicació",
    "Grau de Multimèdia",
    "Grau d'Enginyeria Biomèdica",
    "Grau d'Enginyeria Informàtica"
]

for grau in graus:
    if grau['nom'] in GRAUS_A_IMPORTAR:
        assignatures = llegir_assignatures_grau(grau['url'])
        for a in assignatures:
            all_web_codes.add(a['codi'])

# Obtenir tots els codis de la BD
all_bd = obtenir_assignatures()
all_bd_codes = {a['codi'] for a in all_bd}

print(f"Codis a la WEB: {len(all_web_codes)}")
print(f"Codis a la BD: {len(all_bd_codes)}")

# Trobar codis de la web que NO estan a la BD
missing_in_bd = all_web_codes - all_bd_codes
print(f"\nCodis a la WEB que NO estan a la BD: {len(missing_in_bd)}")
if missing_in_bd:
    print(f"Exemples: {sorted(list(missing_in_bd)[:20])}")

# Trobar codis de la BD que NO estan a la web
extra_in_bd = all_bd_codes - all_web_codes
print(f"\nCodis a la BD que NO estan a la WEB: {len(extra_in_bd)}")
if extra_in_bd:
    print(f"Exemples: {sorted(list(extra_in_bd)[:20])}")

# Verificar totes les assignatures de la web
print(f"\nVerificant TOTES les assignatures de la web...")
no_existeixen = []
for codi in sorted(all_web_codes):
    if not existeix_assignatura(codi):
        no_existeixen.append(codi)

print(f"Assignatures de la web que NO existeixen a la BD: {len(no_existeixen)}")
if no_existeixen:
    print(f"Llista: {no_existeixen}")
