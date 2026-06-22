# Importar llibreries
from flask import Flask, render_template
from base_dades import crear_taules, afegir_dades_inicials, obtenir_assignatures

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

if __name__ == "__main__":
    crear_taules()              # Crear les taules a la base de dades si no existeixen
    afegir_dades_inicials()     # Afegir dades inicials si la base de dades està buida
    aplicacio.run(debug=True)
