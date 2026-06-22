# Importar llibreries
from flask import Flask, render_template

# Crear l'aplicació web
aplicacio = Flask(__name__)


@aplicacio.route("/")
def inici():
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

    #
    return render_template("index.html", assignatures=assignatures)

if __name__ == "__main__":
    aplicacio.run(debug=True)
