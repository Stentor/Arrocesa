# -*- coding: utf-8 -*-
import logging
from math import ceil
from datetime import date
from odoo import api,fields,models, _
from odoo.exceptions import ValidationError

class Employee(models.Model):
    _name = "hr.employee"
    _inherit = "hr.employee"

    cargo_iess = fields.Many2one('iess.sectorial.cargo', string="Cargo IESS")
    payfortnight_ids = fields.One2many(comodel_name='hr.payfortnight', inverse_name='employee_id', string="Codigo Pago Quincenal")
    #salario_ref = fields.Float('Salario Referencial', compute="_get_dummy", store=True)
    salario_ref = fields.Float('Salario Referencial', related="cargo_iess.value", readonly=True)

    dummy = fields.Float("Valor calculado", compute="_get_dummy")

    mensualize_13 = fields.Boolean('Mensualizar decimotercero', default = False)
    mensualize_14 = fields.Boolean('Mensualizar decimocuarto', default = False)
    mensualize_fr = fields.Boolean('Mensualizar fondos de reserva', default = False)
    discapacitado = fields.Boolean('Tiene discapacidad', default = False)
    porc_discapacidad = fields.Float('Porcentaje discapacidad')
    director_sindical = fields.Boolean('Director sindical', default = False)
    horas_extra = fields.Boolean('Horas extra', default = False)
    horas_suple = fields.Boolean('Horas suplementarias', default = False) 
    pago_quincenal = fields.Boolean('Pago Quincenal', default = False)
    porcentaje_sueldo = fields.Float('Porcentaje Sueldo')
    anios_servicio = fields.Float("Años Servicio", compute="_get_anios")
    impuesto_renta = fields.Float('Impuesto Renta')
    galapagos_beneficiary =  fields.Boolean('Beneficiario Galapagos', default=False)
    catastrophic_disease = fields.Boolean('Enfermedad Catastrofica', default=False)
    apply_agreement = fields.Boolean('Aplica Convenio', default=False)
    partner_id = fields.Many2one('res.partner','Empleado Suplente')

    #Ejemplo de funcion calculada en la vista
    @api.depends('cargo_iess')
    @api.onchange('cargo_iess')
    @api.multi
    def _get_dummy(self):
        for s in self:
            s.dummy = s.salario_ref / 12.0
            #s.salario_ref = s.cargo_iess.value

    # Función para revisar si el empleado tiene hecho el pago quincenal
    def has_payment(self,fecha):
        obj_payfortnight = self.env['hr.payfortnight']
        pay = obj_payfortnight.search([('periodo_desde','<=',fecha),('periodo_hasta','>=',fecha),('employee_id','=',self.id)])
        if pay:
            return True
        return False

    def has_13months(self,fecha):
        date_start = min([c.date_start for c in self.contract_ids])
        if (fecha - date_start).days >= 365:
            return True
        return False   

    @api.depends('contract_id')
    def _get_anios(self):
        obj_contract = self.env['hr.contract'] 
        contract = obj_contract.search([('employee_id','=',self.id)],order='id asc', limit=1)  
        if contract:
            contract_active = obj_contract.search([('employee_id','=',self.id)],order='id desc', limit=1)
            if not contract_active.date_end:
                date_end = date.today()
            else:
                date_end = contract_active.date_end
            
            dif = date_end - contract.date_start
            self.anios_servicio = ceil(dif.days/365.2425)

    @api.constrains('identification_id')
    def create_partner(self):
        obj_partner = self.env['res.partner']
        partner_id = obj_partner.search([('identifier','=',self.identification_id)])
        if not partner_id:
            dct = {
                'company_type':'company',
                'type_identifier':'cedula' ,
                'identifier': self.identification_id,
                'supplier': True,
                'property_account_id':1,
                'name': self.name,
                'tipo_persona':'6',
                'is_employee':True,
                'customer':False,
                # 'company_id': self._uid.company_id.id
            }
            partner = partner_id.create(dct)
            self.address_home_id = partner.id
        else:
            self.address_home_id = partner_id.id

        


class settlementType(models.Model):
    _name = 'hr.settlement.type'
    _description = 'tipos de renuncia'

    name =  fields.Char('Descripcion')
    code = fields.Char('Codigo')
    active = fields.Boolean('Activo', default=True)


class contractIess(models.Model):
    _inherit = 'hr.contract'
    _description = 'Add field sectoral charge in contract and update in employee. '

    sectoral_id = fields.Many2one('iess.sectorial.cargo', string="Cargo IESS")

    @api.constrains('sectoral_id')
    def change_sectoral_employee(self):
        if self.state == 'open':
            self.employee_id.cargo_iess = self.sectoral_id.id

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id.cargo_iess:
            self.sectoral_id = self.employee_id.cargo_iess.id

    @api.constrains('state','employee','company_id')
    def constrains_employee_state(self):
        contract_ids = self.env['hr.contract'].search([('employee_id','=',self.employee_id.id),('state','=','open'),('id','!=',self.id),('company_id','=',self.company_id.id)])
        if self.state == 'open' and contract_ids:
            raise ValidationError(_('Un Empleado no puede tener mas de un contrato activo.'))