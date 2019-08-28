# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class resCompany(models.Model):
    _inherit = 'res.company'


    def duplicate_data(self):
        return {
            'name': 'Duplicado de Informacion',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'duplicate.models.data',
            'target': 'new',
        }

class wizardDuplicate(models.TransientModel):
    _name = "duplicate.models.data"
    _description = ""

    name = fields.Many2one('ir.model','Modelo', domain="[('model','in',('res.partner','account.tax'))]")
    company_id = fields.Many2one('res.company','Compañía')


    def reply_data(self):
        if self.company_id == self.env.user.company_id:
            raise ValidationError(_("No puede duplicar informacion de la misma compañía.\nAsegurece que este en la compañía correcta"))
        model = self.env[self.name.model]
        data_ids = model.sudo().search([('company_id','=',self.company_id.id)])
        active_id = self.env.context.get('active_id')
        default = {}
        default['company_id'] = active_id
        for data in data_ids:
            default['name'] =  data.name
            copy = data.copy_data(default)
            new = model.create(copy)
        return {'type': 'ir.actions.act_window_close'}
