#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_dades import obtenir_assignatures, existeix_assignatura, obtenir_connexio

# Verificar algunes assignatures
codis_a_verificar = [
    "11.504",  # Física I
    "11.505",  # Fonaments de programació
    "11.506",  # Matemàtiques I
    "22.401",  # Fonaments de programació per a la ciència de dades
    "22.403",  # Programació per a la ciència de dades
]

print("Verificant assignatures:")
for codi in codis_a_verificar:
    existeix = existeix_assignatura(codi)
    print(f"  {codi}: {'✅ Existeix' if existeix else '❌ No existeix'}")

# Obtenir totes les assignatures de la BD
print("\nTotes les assignatures de la BD:")
all_assignatures = obtenir_assignatures()
print(f"Total: {len(all_assignatures)}")

# Mostrar els codis
codis_bd = sorted([a['codi'] for a in all_assignatures])
print(f"\nCodis a la BD: {codis_bd}")

# Verificar quants codis hi ha a la web
from scraper import obtenir_llista_graus_uoc, llegir_assignatures_grau, esborrar_cache

esborrar_cache()

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

print(f"\nCodis a la WEB: {len(all_web_codes)}")
print(f"Codis únics a la WEB: {len(all_web_codes)}")

# Comptar quants codis de la web NO estan a la BD
missing = all_web_codes - set(codis_bd)
print(f"\nCodis a la WEB que NO estan a la BD: {len(missing)}")
print(f"Exemples: {sorted(list(missing)[:10])}")

# Comptar quants codis de la BD NO estan a la web
extra = set(codis_bd) - all_web_codes
print(f"\nCodis a la BD que NO estan a la WEB: {len(extra)}")
print(f"Exemples: {sorted(list(extra)[:10])}")
