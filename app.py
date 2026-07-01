# Importar llibreries
from flask import Flask, render_template, redirect, url_for, request
from base_dades import(
    crear_taules,
    afegir_dades_inicials,
    obtenir_assignatures,
    inserir_assignatura,
    existeix_assignatura,
    actualitzar_detall_assignatura,
    obtenir_o_crear_grau,
    relacionar_grau_assignatura,
    obtenir_assignatura_codi,
    obtenir_graus,
    obtenir_assignatures_per_grau
)
from scraper import llegir_assignatures_grau, llegir_detall_assignatura

# Crear l'aplicació web
aplicacio = Flask(__name__)

# Valors de prova per a les assignatures
# assignatures = [
#   {"nom": "Matemàtiques", "credits": 6, "semestre": "Primer semestre"},
#   {"nom": "Programació 1", "credits": 6, "semestre": "Primer semestre"},
#   {"nom": "Bases de dades", "credits": 6, "semestre": "Segon semestre"}
#  ]

# Creació de rutes
@aplicacio.route("/")
def inici():
    return render_template("index.html")


@aplicacio.route("/assignatures")
def veure_assignatures():
    grau_id = request.args.get("grau_id")
    model_avaluacio = request.args.get("model_avaluacio", "")
    graus = obtenir_graus()

    if grau_id:
        assignatures = obtenir_assignatures_per_grau(grau_id)
    else:
        assignatures = obtenir_assignatures()

    if model_avaluacio:
        assignatures_filtrades = []

        for assignatura in assignatures:
            if assignatura["model_avaluacio"] == model_avaluacio:
                assignatures_filtrades.append(assignatura)
        
        assignatures = assignatures_filtrades

    return render_template(
        "assignatures.html",
        assignatures = assignatures,
        graus=graus,
        grau_id=grau_id
        )


@aplicacio.route('/importar')
def importar_assignatures():
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
    # url_grau = 'https://www.uoc.edu/ca/estudis/graus/grau-data-science'
    # Bucle per passar per tots els graus d'Informàtica, Multimèdia i Telecomunicació
    for grau in graus:
        grau_id = obtenir_o_crear_grau(grau['nom'], grau['url'])
        assignatures_uoc = llegir_assignatures_grau(grau['url'])

        # Bucle per passar per totes les assignatures d'un grau
        for assignatura in assignatures_uoc:
            if not existeix_assignatura(assignatura['codi']):
                inserir_assignatura(assignatura['codi'],
                                    assignatura['titol'],
                                    "2026-1",
                                    "Pendent",
                                    "Pendent de llegir el pla docent",
                                    assignatura['url']
                                    )
            relacionar_grau_assignatura(grau_id, assignatura['codi'])
    return redirect(url_for('veure_assignatures'))


@aplicacio.route('/actualitzar-detall/<codi>')
def actualitzar_detall(codi):
    # Obtenir l'URL de l'assignatura a partir del codi
    assignatures = obtenir_assignatures()

    for assignatura in assignatures:
        if assignatura['codi'] == codi:
            # Llegir el pla docent i extreure la informació necessària
            detall = llegir_detall_assignatura(assignatura['url'])
            # Actualitzar la base de dades amb la informació obtinguda
            actualitzar_detall_assignatura(codi,
                                       detall['model_avaluacio'],
                                       detall['descripcio']
                                       )
    return redirect(url_for('veure_assignatures'))


@aplicacio.route('/assignatura/<codi>')
def veure_assignatura(codi):
    assignatura = obtenir_assignatura_codi(codi)
    return render_template('assignatura.html', assignatura=assignatura)


if __name__ == "__main__":
    crear_taules()              # Crear les taules a la base de dades si no existeixen
    afegir_dades_inicials()     # Afegir dades inicials si la base de dades està buida
    aplicacio.run(debug=True)
