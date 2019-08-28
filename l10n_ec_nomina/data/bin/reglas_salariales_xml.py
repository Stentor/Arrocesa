import csv
from mako.template import Template


with open('../regla.salarial.csv', 'r',encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')
    categorias = {}
    parents = {}
    reglas = {}
    
    for row in reader:
        if not row['category_ids/code'] in categorias:
            categorias[row['category_ids/code']] = row

        if not row['category_ids/padre/code'] in parents:
            parents[row['category_ids/padre/code']] = row
        
        reglas[row['code']] = row

    
    
    catpXml = Template(filename='tpl/categoria_reglas_parent.tpl').render(categorias=parents.values())
    catXml = Template(filename='tpl/categoria_reglas.tpl').render(categorias=categorias.values())
    regXml = Template(filename='tpl/reglas_salariales.tpl').render(reglas=reglas.values())
    

    fileCategories = open('../categorias_reglas_salariales.xml', 'wb')
    fileCategories.write(catXml.encode('utf-8'))
    fileCategories.close()

    fileCategoriesp = open('../categorias_reglas_salariales_parent.xml', 'wb')
    fileCategoriesp.write(catpXml.encode('utf-8'))
    fileCategoriesp.close()

    fileRules = open('../reglas_salariales.xml', 'wb')
    fileRules.write(regXml.encode('utf-8'))
    fileRules.close()

    