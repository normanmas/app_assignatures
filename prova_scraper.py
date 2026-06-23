from scraper import llegir_assignatures_grau
from scraper import llegir_detall_assignatura

url_grau = "https://www.uoc.edu/ca/estudis/graus/grau-data-science"
url = "https://apps.uoc.edu/PlaDocent/PlaDocent?Semestre=20261&SignatureCode=22.401&Context=3&Locale=ca"

#assignatures = llegir_assignatures_grau(url_grau)
#for assignatura in assignatures:
#    print(assignatura['codi'], assignatura['titol'])

detall = llegir_detall_assignatura(url)
print("Model d'avaluació:")
print(detall['model_avaluacio'])
print()
print('Inici de la descripció:')
print(detall['descripcio'][:300])  # Mostrar només els primers 300 caràcters de la descripció
