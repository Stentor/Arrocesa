from openerp import api, models, fields
from openerp.exceptions import Warning as UserError

class Payments(models.Model):
    _name = 'account.payment.term'
    _inherit = 'account.payment.term'

    report_dinardap = fields.Boolean('Reportar a la dinardap', default=False)


class Payment(models.Model):
    _name = 'account.payment'
    _inherit = 'account.payment'

    dinardap_pay_method = fields.Selection(
        [
            ('E', 'Efectivo'),
            ('C', 'Cheque'),
            ('T', 'Tarjeta de credito')
        ], string="Metodo de pago (dinardap)", required=True, default="E"
    )