# Importar llibreries
from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.exceptions import NotFound, InternalServerError
import logging

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
    obtenir_assignatures_per_grau,
    afegir_assignatura_aprovada,
    eliminar_assignatura_aprovada,
    obtenir_assignatures_aprovades,
    obtenir_estat_importacio,
    afegir_assignatura_interessant,
    eliminar_assignatura_interessant,
    obtenir_assignatures_interessants,
    es_assignatura_interessant
)
from scraper import llegir_assignatures_grau, llegir_detall_assignatura, obtenir_llista_graus_uoc, esborrar_cache

# Crear l'aplicació web
aplicacio = Flask(__name__)

# Configuració de la aplicació
aplicacio.secret_key = 'clau_secreta_molt_segura_12345'  # Canviar en producció!

# Configuració de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Maneig d'errors global
@aplicacio.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@aplicacio.errorhandler(500)
def internal_error(e):
    logger.error(f"Error intern: {e}")
    return render_template('500.html'), 500

# Filtres personalitzats per Jinja2
@aplicacio.template_filter('truncar')
def truncar_filter(s, length=100):
    if len(s) <= length:
        return s
    return s[:length] + '...'
# assignatures = [
#   {"nom": "Matemàtiques", "credits": 6, "semestre": "Primer semestre"},
#   {"nom": "Programació 1", "credits": 6, "semestre": "Primer semestre"},
#   {"nom": "Bases de dades", "credits": 6, "semestre": "Segon semestre"}
#  ]

# Creació de rutes

# Ruta app principal
@aplicacio.route("/")
def inici():
    return render_template("index.html")


# Nova ruta: Cercar assignatures
@aplicacio.route("/assignatures/cerca")
def cercar_assignatures():
    """Cercar assignatures per text."""
    query = request.args.get('q', '')
    
    if not query:
        return redirect(url_for('veure_assignatures'))
    
    assignatures = obtenir_assignatures()
    
    # Filtrar per codi o títol (case insensitive)
    resultats = [
        a for a in assignatures 
        if query.lower() in a['codi'].lower() or query.lower() in a['titol'].lower()
    ]
    
    graus = obtenir_graus()
    
    return render_template(
        "assignatures.html",
        assignatures=resultats,
        graus=graus,
        grau_id=None,
        cercat=query
    )


# Ruta per esborrar el cache
@aplicacio.route("/cache/esborrar")
def esborrar_cache_ruta():
    """Esborrar el cache del scraper."""
    esborrar_cache()
    flash('Cache esborrat correctament', 'success')
    return redirect(url_for('veure_assignatures'))

# Ruta on es guarden totes les assignatures
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

    # Obtenir llistat de codis d'assignatures interessants per comprovar ràpidament
    codis_interessants = set()
    for item in obtenir_assignatures_interessants():
        codis_interessants.add(item['codi'])

    return render_template(
        "assignatures.html",
        assignatures = assignatures,
        graus=graus,
        grau_id=grau_id,
        codis_interessants=codis_interessants
        )


@aplicacio.route('/importar')
def importar_assignatures():
    """Importar assignatures de tots els graus de la UOC."""
    # Obtenir llista de graus des del scraper
    graus = obtenir_llista_graus_uoc()
    
    # Esborrar cache per obtenir dades fresques
    esborrar_cache()
    
    # Bucle per pasar per tots els graus
    for grau in graus:
        grau_id = obtenir_o_crear_grau(grau['nom'], grau['url'])
        
        try:
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
                    logger.info(f"Importada assignatura: {assignatura['codi']} - {assignatura['titol']}")
                
                # Relacionar assignatura amb grau
                relacionar_grau_assignatura(grau_id, assignatura['codi'])
            
            logger.info(f"Importades {len(assignatures_uoc)} assignatures del grau {grau['nom']}")
            
        except Exception as e:
            logger.error(f"Error important assignatures del grau {grau['nom']}: {e}")
            flash(f"Error important assignatures del grau {grau['nom']}", 'error')
    
    flash(f"Importació completada! S'han importat assignatures de {len(graus)} graus.", 'success')
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


@aplicacio.route("/aprovades", methods=["GET", "POST"])
def veure_aprovades():
    if request.method == "POST":
        codi = request.form.get("codi")
        semestre = request.form.get("semestre")
        nota = request.form.get("nota")
        observacions = request.form.get("observacions")

        if codi and semestre:
            afegir_assignatura_aprovada(codi, semestre, nota, observacions)
            flash('Assignatura afegida a les aprovades correctament', 'success')

        return redirect(url_for("veure_aprovades"))
    
    assignatures_aprovades = obtenir_assignatures_aprovades()

    return render_template(
        "aprovades.html",
        assignatures_aprovades=assignatures_aprovades
    )


@aplicacio.route('/aprovades/eliminar/<codi>', methods=['POST'])
def eliminar_aprovada(codi):
    """Eliminar una assignatura de les aprovades."""
    eliminar_assignatura_aprovada(codi)
    flash('Assignatura eliminada de les aprovades correctament', 'success')
    return redirect(url_for('veure_aprovades'))


@aplicacio.route("/interessants", methods=["GET", "POST"])
def veure_interessants():
    """Mostrar i gestionar les assignatures marcades com a interessants."""
    if request.method == "POST":
        codi = request.form.get("codi")
        
        if codi:
            afegir_assignatura_interessant(codi)
            flash('Assignatura afegida a les interessants correctament', 'success')
        
        return redirect(url_for("veure_interessants"))
    
    # Obtenir les assignatures interessants amb les seves dades completes
    codis_interessants = obtenir_assignatures_interessants()
    assignatures_interessants = []
    
    for item in codis_interessants:
        assignatura = obtenir_assignatura_codi(item['codi'])
        if assignatura:
            assignatura['data_afegit'] = item['data_afegit']
            assignatures_interessants.append(assignatura)
    
    return render_template(
        "interessants.html",
        assignatures_interessants=assignatures_interessants
    )


@aplicacio.route('/interessants/eliminar/<codi>', methods=['POST'])
def eliminar_interessant(codi):
    """Eliminar una assignatura de les interessants."""
    eliminar_assignatura_interessant(codi)
    flash('Assignatura eliminada de les interessants correctament', 'success')
    return redirect(url_for('veure_interessants'))


@aplicacio.route('/interessants/toggle/<codi>', methods=['POST'])
def toggle_interessant(codi):
    """Marcar o desmarcar una assignatura com a interessant."""
    if es_assignatura_interessant(codi):
        eliminar_assignatura_interessant(codi)
        flash('Assignatura desmarcada com a interessant', 'success')
    else:
        afegir_assignatura_interessant(codi)
        flash('Assignatura marcada com a interessant', 'success')
    return redirect(url_for('veure_assignatures'))


if __name__ == "__main__":
    crear_taules()              # Crear les taules a la base de dades si no existeixen
    afegir_dades_inicials()     # Afegir dades inicials si la base de dades està buida
    aplicacio.run(debug=True)