import csv
from mako.template import Template

def parent_code(code, groups):
    try:
        result = max([g for g in groups if code.startswith(g) and code !=g])
    except ValueError:
        result = False
    finally: 
        return result

def process_csv():
    with open('../groups.csv') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')        
        groups = [row for row in reader]        
        codes = [g for g in map(lambda x: str(x['code']), groups)]
        for line in groups:
            code = parent_code(line['code'], codes)
            if code:
                line['parent'] = 'account_group_'+ code                    
        groupsXml = Template(filename='tpl/category.tpl').render(groups=groups)
        out_file = open('../category.xml', 'w')
        out_file.write(groupsXml)
        out_file.close()

if __name__=='__main__':
    process_csv()