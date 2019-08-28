import csv
from mako.template import Template

def compatible_code(code, groups):
    return max([g for g in groups if code.startswith(g)])

with open('../accounts.csv') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')
    
    groups_file = open('../groups.csv')
    group_reader = csv.DictReader(groups_file, delimiter=',')

    groups = map(lambda x: str(x['code']), [i for i in group_reader])
    groups = [g for g in groups]

    accounts = {}
    for row in reader:
        accounts[row['code']] = row
    for account in accounts.values():
        account['group'] = 'account_group_'+compatible_code(account['code'], groups)
        

    
    accountsXml = Template(filename='tpl/account.tpl').render(accounts=accounts.values())
    fileImpuestos = open('../account.xml', 'w')
    fileImpuestos.write(accountsXml)
    fileImpuestos.close()