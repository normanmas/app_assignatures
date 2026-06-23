# Importar llibreries
from flask import Flask, render_template, redirect, url_for
from base_dades import(
    crear_taules,
    afegir_dades_inicials,
    obtenir_assignatures,
    inserir_assignatura,
    existeix_assignatura,
    actualitzar_detall_assignatura
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

@aplicacio.route("/")
def inici():
    return render_template("index.html")

@aplicacio.route("/assignatures")
def veure_assignatures():
    assignatures = obtenir_assignatures()
    return render_template("assignatures.html", assignatures = assignatures)

@aplicacio.route('/importar')
def importar_assignatures():
    url_grau = 'https://www.uoc.edu/ca/estudis/graus/grau-data-science'
    assignatures_uoc = llegir_assignatures_grau(url_grau)
    for assignatura in assignatures_uoc:
        if not existeix_assignatura(assignatura['codi']):
            inserir_assignatura(assignatura['codi'],
                                assignatura['titol'],
                                "2026-1",
                                "Pendent",
                                "Pendent de llegir el pla docent",
                                assignatura['url']
                                )
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

if __name__ == "__main__":
    crear_taules()              # Crear les taules a la base de dades si no existeixen
    afegir_dades_inicials()     # Afegir dades inicials si la base de dades està buida
    aplicacio.run(debug=True)
