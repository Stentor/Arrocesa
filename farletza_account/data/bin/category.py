import csv
from mako.template import Template
from collections import OrderedDict


with open('../Grupos_y_Sub-grupos_de_Cuentas.csv') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')
    
    groups = OrderedDict()
    for row in reader:
        groups[row['code']] = row

    for lines in groups.values():
        len_line = len(lines['code']) - 1
        data = lines['code'][0:len_line]
        for line in groups.values():
            if line['code'] == data:
                lines['parent'] = 'account_group_'+ line['code']
                continue

    
    groupsXml = Template(filename='tpl/category.tpl').render(groups=groups.values())
    fileImpuestos = open('../category.xml', 'w')
    fileImpuestos.write(groupsXml)
    fileImpuestos.close()