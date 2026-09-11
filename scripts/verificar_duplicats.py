#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import obtenir_llista_graus_uoc, llegir_assignatures_grau, esborrar_cache

esborrar_cache()

# Graus que ens interessen
GRAUS_A_IMPORTAR = [
    "Grau de Ciència de Dades Aplicada",
    "Grau de Desenvolupament i Proves de Software",
    "Grau d'Enginyeria i Telecomunicació",
    "Grau de Multimèdia",
    "Grau d'Enginyeria Biomèdica",
    "Grau d'Enginyeria Informàtica"
]

graus_coneguts = obtenir_llista_graus_uoc()
graus_a_importar = [g for g in graus_coneguts if g['nom'] in GRAUS_A_IMPORTAR]

# Obtenir TOTES les assignatures de la web
all_web_assignatures = []
for grau in graus_a_importar:
    assignatures = llegir_assignatures_grau(grau['url'])
    for a in assignatures:
        all_web_assignatures.append((grau['nom'], a['codi'], a['titol']))

# Comptar quantes vegades apareix cada codi
from collections import Counter
codi_counter = Counter([a[1] for a in all_web_assignatures])

print("Codis que apareixen en MÚLTIPLES graus:")
print("=" * 70)

duplicats = {codi: count for codi, count in codi_counter.items() if count > 1}
print(f"Total codis duplicats: {len(duplicats)}")
print(f"Total assignatures a la web: {len(all_web_assignatures)}")
print(f"Codis únics: {len(codi_counter)}")

# Mostrar els codis més compartits
print("\nCodis que apareixen en més de 3 graus:")
for codi, count in sorted(duplicats.items(), key=lambda x: x[1], reverse=True)[:20]:
    # Trobar en quins graus apareix
    graus_with_codi = [a[0] for a in all_web_assignatures if a[1] == codi]
    print(f"  {codi}: {count} vegades (graus: {', '.join(graus_with_codi)})")

print(f"\nTotal relacions que s'intentarien crear: {len(all_web_assignatures)}")
print(f"Total relacions realment creades (codis únics): {len(codi_counter)}")
