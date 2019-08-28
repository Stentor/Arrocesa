import csv
from mako.template import Template


with open('../tabla.impuestos.renta.csv') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')
    
    impuestos = {}
    for row in reader:
        impuestos[row['code']] = row

    
    impuestosXml = Template(filename='tpl/imp_renta_pernat.tpl').render(impuestos=impuestos.values())


    fileImpuestos = open('../imp_renta_pernat.xml', 'w')
    fileImpuestos.write(impuestosXml)
    fileImpuestos.close()