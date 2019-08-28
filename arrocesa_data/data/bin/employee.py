import csv
from mako.template import Template

with open('../hr.employee.csv') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')
    
    employees = [e for e in reader]

    
    employeesXml = Template(filename='tpl/employees.tpl').render(employees=employees.values())
    resultFile = open('../account.xml', 'w')
    resultFile.write(employeesXml)
    resultFile.close()