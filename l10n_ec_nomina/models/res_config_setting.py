# -*- coding: utf-8 -*-

from odoo import api,fields, models, _
from ast import literal_eval
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    struct_id = fields.Many2one('hr.payroll.structure', string='Estructura Salarial')
    journal_payroll = fields.Many2one('account.journal', string='Nomina')
    journal_payroll_pay = fields.Many2one('account.journal', string='Pago Nomina')
    journal_fortnight = fields.Many2one('account.journal', string='Quincena')
    journal_fortnight_pay = fields.Many2one('account.journal', string='Pago Quincena')
    journal_xiii = fields.Many2one('account.journal', string='Decimo Tercer Sueldo')
    journal_xiv = fields.Many2one('account.journal', string='Decimo Cuarto Sueldo')
    journal_vacation = fields.Many2one('account.journal', string='Vacaciones')
    journal_settlement = fields.Many2one('account.journal', string='Finiquito')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.default'].sudo()
        struct_id = ICPSudo.get("res.config.settings",'struct_id',False,self.env.user.company_id.id)
        journal_payroll = ICPSudo.get("res.config.settings",'journal_payroll',False,self.env.user.company_id.id)
        journal_payroll_pay = ICPSudo.get("res.config.settings",'journal_payroll_pay',False,self.env.user.company_id.id)
        journal_fortnight = ICPSudo.get("res.config.settings",'journal_fortnight',False,self.env.user.company_id.id)
        journal_fortnight_pay = ICPSudo.get("res.config.settings",'journal_fortnight_pay',False,self.env.user.company_id.id)
        journal_xiii = ICPSudo.get("res.config.settings",'journal_xiii',False,self.env.user.company_id.id)
        journal_xiv = ICPSudo.get("res.config.settings",'journal_xiv',False,self.env.user.company_id.id)
        journal_vacation = ICPSudo.get("res.config.settings",'journal_vacation',False,self.env.user.company_id.id)
        journal_settlement = ICPSudo.get("res.config.settings",'journal_settlement',False,self.env.user.company_id.id)

        res.update(
            struct_id=struct_id, 
            journal_payroll=journal_payroll,
            journal_payroll_pay=journal_payroll_pay,
            journal_fortnight=journal_fortnight,
            journal_fortnight_pay=journal_fortnight_pay,
            journal_xiii=journal_xiii,
            journal_xiv=journal_xiv,
            journal_vacation=journal_vacation,
            journal_settlement=journal_settlement,
            )
        return res


    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.default'].sudo()
        ICPSudo.set("res.config.settings",'struct_id',self.struct_id.id,False,self.env.user.company_id.id)
        ICPSudo.set("res.config.settings",'journal_payroll',self.journal_payroll.id,False,self.env.user.company_id.id)
        ICPSudo.set("res.config.settings",'journal_payroll_pay',self.journal_payroll_pay.id,False,self.env.user.company_id.id)
        ICPSudo.set("res.config.settings",'journal_fortnight',self.journal_fortnight.id,False,self.env.user.company_id.id)
        ICPSudo.set("res.config.settings",'journal_fortnight_pay',self.journal_fortnight_pay.id,False,self.env.user.company_id.id)
        ICPSudo.set("res.config.settings",'journal_xiii',self.journal_xiii.id,False,self.env.user.company_id.id)
        ICPSudo.set("res.config.settings",'journal_xiv',self.journal_xiv.id,False,self.env.user.company_id.id)
        ICPSudo.set("res.config.settings",'journal_vacation',self.journal_vacation.id,False,self.env.user.company_id.id)
        ICPSudo.set("res.config.settings",'journal_settlement',self.journal_settlement.id,False,self.env.user.company_id.id)
