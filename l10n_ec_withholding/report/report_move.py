# -*- coding: utf-8 -*-

from itertools import groupby

from odoo import api, models


class ReporteComprobante(models.AbstractModel):

    _name = 'report.l10n_ec_withholding.reporte_move'

    def groupby(self, lines):
        """
        Codigo listo para permitir aggregaciones de lineas
        """
        glines = []
        for k, g in groupby(lines):
            debit = 0
            credit = 0
            for i in g:
                debit += i.debit
                credit += i.credit
            glines.append({
                'code': k.account_id.code,
                'name': k.account_id.name,
                'debit': debit,
                'credit': credit
            })
        print(glines)
        return glines

    @api.model
    def _get_report_values(self, docids, data=None):
        fact = self.env['account.invoice'].browse(docids)[0]
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': self.env['account.move'].search([('name', '=', fact.number)]),
            'groupby': self.groupby
        }
        return docargs
    
