# -*- coding: utf-8 -*-

from openerp import models, fields

class AtsPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'


    ats_resident = fields.Selection([
        ('01', 'PAGO A RESIDENTE/ESTABLECIMIENTO PERMANENTE'),
        ('02', 'PAGO A NO RESIDENTE ')
    ], string="Tipo de pago", default='01')

    ats_country = fields.Many2one('ats.country', string='Pais')
    ats_regimen_fiscal = fields.Selection([
        ('01', 'Regimen General'),
        ('02', 'Paraiso Fiscal'),
        ('03', 'Régimen fiscal preferente o jurisdicción de menor imposición')
    ], string='Regimen Fiscal', default='01')

    ats_doble_trib = fields.Boolean('Aplica doble tributacion', default=False)
    denopago = fields.Char('Denominacion', help='Denominación del régimen fiscal preferente o jurisdicción de menor imposición.')
    pag_ext_suj_ret_nor_leg = fields.Boolean('Sujeto a retencion', help='Pago al exterior sujeto a retención en aplicación a la norma legal', default=False)
    pago_reg_fis = fields.Boolean('Regimen Fiscal Preferente', help='El pago es a un régimen fiscal preferente o de menor imposición?', default=False)

   


class AtsCountry(models.Model):
    _name = 'ats.country'
    
    name = fields.Char('Nombre')
    code = fields.Char('Code')
    is_fiscal_paradise = fields.Boolean("Paraiso Fiscal")



class AtsEarning(models.Model):
    _name = 'ats.earning'

    name = fields.Char('Nombre')
    code = fields.Char('Code')