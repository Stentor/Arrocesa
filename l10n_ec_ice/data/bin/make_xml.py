import csv
from mako.template import Template


with open('../ice.csv') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')
    
    taxes = []
    for row in reader:
        taxes.append(row)
        print(row)

    comXml = Template(filename='tpl/tax.tpl').render(taxes=taxes)
    

    fileComision = open('../ice_codes.xml', 'w')
    fileComision.write(comXml)
    fileComision.close()
