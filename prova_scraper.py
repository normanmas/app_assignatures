from scraper import (llegir_assignatures_grau,
                     llegir_detall_assignatura,
                     crear_navegador,
                     llegir_detall_assignatura_amb_navegador
)

from base_dades import (
    crear_taules,
    inserir_assignatura,
    existeix_assignatura,
    obtenir_o_crear_grau,
    relacionar_grau_assignatura,
    obtenir_assignatures,
    actualitzar_detall_assignatura
)

opcio = "importar masiu"

url_grau = "https://www.uoc.edu/ca/estudis/graus/grau-data-science"
url = "https://apps.uoc.edu/PlaDocent/PlaDocent?Semestre=20261&SignatureCode=22.401&Context=3&Locale=ca"

# Prova 1
#assignatures = llegir_assignatures_grau(url_grau)
#for assignatura in assignatures:
#    print(assignatura['codi'], assignatura['titol'])

# Prova 2
#detall = llegir_detall_assignatura(url)
#print("Model d'avaluació:")
#print(detall['model_avaluacio'])
#print()
#print('Inici de la descripció:')
#print(detall['descripcio'][:300])  # Mostrar només els primers 300 caràcters de la descripció


# Prova 3
graus = [
    {
        "nom": "Grau de Ciència de Dades Aplicada",
        "url": "https://www.uoc.edu/ca/estudis/graus/grau-data-science"
    },
    {
        "nom": "Grau d'Enginyeria Biomèdica",
        "url": "https://www.uoc.edu/ca/estudis/graus/grau-enginyeria-biomedica"
    },
    {
        "nom": "Grau d'Enginyeria i Telecomunicació",
        "url": "https://www.uoc.edu/ca/estudis/graus/grau-tecnologies-telecomunicacio"
    },
    {
        "nom": "Grau d'Enginyeria Informàtica",
        "url": "https://www.uoc.edu/ca/estudis/graus/grau-enginyeria-informatica"
    },
    {
        "nom": "Grau de Multimèdia",
        "url": "https://www.uoc.edu/ca/estudis/graus/grau-multimedia"
    },
    {
        "nom": "Grau de Desenvolupament i Proves de Software",
        "url": "https://www.uoc.edu/ca/estudis/graus/grau-desenvolupament-proves-software"
    },
    {
        "nom": "Doble grau d'Informàtica i ADE",
        "url": "https://www.uoc.edu/ca/estudis/graus/grau-informatica-ade-doble-titulacio"
    }
]

crear_taules()

for grau in graus:
    print("Llegint grau:", grau["nom"])

    grau_id = obtenir_o_crear_grau(grau["nom"], grau["url"])
    assignatures = llegir_assignatures_grau(grau["url"])

    for assignatura in assignatures:
        print("Llegint assignatura:", assignatura["codi"], assignatura["titol"])

        if not existeix_assignatura(assignatura["codi"]):
            try:
                detall = llegir_detall_assignatura(assignatura["url"])

                inserir_assignatura(
                    assignatura["codi"],
                    assignatura["titol"],
                    "2026-1",
                    detall["model_avaluacio"],
                    detall["descripcio"],
                    assignatura["url"]
                )

            except Exception as error:
                print("No s'ha pogut llegir el detall de:", assignatura["codi"])
                print("Error:", error)

                inserir_assignatura(
                    assignatura["codi"],
                    assignatura["titol"],
                    "2026-1",
                    "Pendent",
                    "Pendent de llegir el pla docent",
                    assignatura["url"]
                )

        relacionar_grau_assignatura(grau_id, assignatura["codi"])

print("Càrrega massiva acabada")

print("Actualitzant assignatures pendents...")
assignatures_guardades = obtenir_assignatures()
navegador = crear_navegador()

try:
    for assignatura in assignatures_guardades:
        if assignatura["model_avaluacio"] == "Pendent":
            print("Actualitzant pendent:", assignatura["codi"], assignatura["titol"])

            try:
                detall = llegir_detall_assignatura_amb_navegador(navegador, assignatura["url"])

                actualitzar_detall_assignatura(
                    assignatura["codi"],
                    detall["model_avaluacio"],
                    detall["descripcio"]
                )
            except Exception as error:
                print("No s'ha pogut actualitzar: ", assignatura["codi"])
                print("Error: ", error)
finally:
    navegador.quit()

print("Actualització de pendents acabada!")
