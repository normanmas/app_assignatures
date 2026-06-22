# Importar llibreries
from flask import Flask, render_template

# Crear l'aplicació web
aplicacio = Flask(__name__)

# Valors de prova per a les assignatures
assignatures = [
    {
        "nom": "Matemàtiques",
        "credits": 6,
        "semestre": "Primer semestre"
    },
    {
        "nom": "Programació 1",
        "credits": 6,
        "semestre": "Primer semestre"
    },
    {
        "nom": "Bases de dades",
        "credits": 6,
        "semestre": "Segon semestre"
    }
]

@aplicacio.route("/")
def inici():
    return render_template("index.html")

@aplicacio.route("/assignatures")
def veure_assignatures():
    return render_template("assignatures.html", assignatures = assignatures)

if __name__ == "__main__":
    aplicacio.run(debug=True)
