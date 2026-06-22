from scraper import llegir_assignatures_grau

url_grau = "https://www.uoc.edu/ca/estudis/graus/grau-data-science"

assignatures = llegir_assignatures_grau(url_grau)

for assignatura in assignatures:
    print(assignatura['codi'], assignatura['titol'])
