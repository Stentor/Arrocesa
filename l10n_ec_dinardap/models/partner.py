from openerp import api, models, fields
from openerp.exceptions import Warning as UserError

SEXO = [
    (' ',' '),
    ('M', 'Masculino'),
    ('F', 'Femenino')
]

CIVIL_STATE = [
    (' ',' '),
    ('S', 'Soltero/a'),
    ('C', 'Casado/a'),
    ('D', 'Divorciado/a'),
    ('U', 'Union Libre'),
    ('V', 'Viudo/a')
]

ORIGEN_INGRESO = [
    (' ',' '),
    ('B', 'Empleado Publico'),
    ('V', 'Empleado Privado'),
    ('I', 'Independiente'),
    ('A', 'Ama de casa o Estudiante'),
    ('R', 'Rentista'),
    ('H', 'Jubilado'),
    ('M', 'Remesas del Exterior')

]

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    dinardap_id_type =  fields.Char('Tipo de identificacion', compute="_get_dinardap_data")
    dinardap_class = fields.Char('Tipo de sujeto', compute="_get_dinardap_data")
    dinardap_sexo = fields.Selection(SEXO, string='Sexo', default=' ')
    dinardap_civil_state = fields.Selection(CIVIL_STATE, string='Estado Civil', default=' ')
    dinardap_origin = fields.Selection(ORIGEN_INGRESO, string='Origen de los ingresos', default=' ')
    dinardap_province = fields.Many2one('ote.province', string="Provincia")
    dinardap_canton = fields.Many2one('ote.canton', string="Canton")
    dinardap_parroquia = fields.Many2one('ote.parroquia', string="Parroquia")

    @api.multi
    @api.onchange('type_identifier', 'identifier')
    def _get_dinardap_data(self):
        for s in self:
            if s.type_identifier=='ruc':
                s.dinardap_id_type = 'R'
            elif s.type_identifier=='cedula':
                s.dinardap_id_type = 'C'
            else:
                s.dinardap_id_type = 'E'
            if s.tipo_persona == '9':
                s.dinardap_class = 'J'
            else:
                s.dinardap_class = 'N'


class ResCompany(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    dinardap_id = fields.Char("Codigo Dinardap", length=7)

class OteProvince(models.Model):
    _name = 'ote.province'

    name = fields.Char('Nombre')
    code = fields.Char('Code', length=2)

class OteCanton(models.Model):
    _name =  'ote.canton'
    
    name = fields.Char('Nombre')
    code = fields.Char('Code', length=2)
    province_id = fields.Many2one('ote.province', 'Provincia')

class OteParroquia(models.Model):
    _name = 'ote.parroquia'

    name = fields.Char('Nombre')
    code = fields.Char('Code', length=2)
    canton_id = fields.Many2one('ote.canton', 'Canton')