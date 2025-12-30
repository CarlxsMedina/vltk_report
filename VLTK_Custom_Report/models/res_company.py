from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    # Relación para permitir seleccionar nuestro nuevo layout en los ajustes
    external_report_layout_id = fields.Many2one(
        'ir.ui.view', 
        domain="[('type', '=', 'qweb'), ('key', 'ilike', 'external_layout_%')]"
    )