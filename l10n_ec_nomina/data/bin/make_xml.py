import csv
from mako.template import Template


with open('../iess.sectorial.comision.csv') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    comisiones = {}
    ramas = {}
    cargos = {}
    for row in reader:
        if not row['code'] in comisiones:
            comisiones[row['code']] = row
        if not row['rama_ids/code'] in ramas:
            ramas[row['rama_ids/code']] = row
        cargos[row['cargos_ids/code']] = row

    comXml = Template(filename='tpl/comision.tpl').render(comisiones=comisiones.values())
    ramaXml = Template(filename='tpl/rama.tpl').render(ramas=ramas.values())
    cargosXml = Template(filename='tpl/cargo.tpl').render(cargos=cargos.values())


    fileComision = open('../comisiones.xml', 'w')
    fileComision.write(comXml)
    fileComision.close()

    fileRamas = open('../ramas.xml', 'w')
    fileRamas.write(ramaXml)
    fileRamas.close()

    fileCargos = open('../cargos.xml', 'w')
    fileCargos.write(cargosXml)
    fileCargos.close()