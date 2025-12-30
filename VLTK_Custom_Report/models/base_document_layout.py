from odoo import models, fields, api

class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    # Renombramos para evitar conflicto con el campo nativo de Odoo 18
    custom_report_layout_id = fields.Many2one(
        'ir.ui.view', 
        domain="[('type', '=', 'qweb'), ('key', 'ilike', 'external_layout_%')]",
        string="Estilo de Reporte Personalizado"
    )

    @api.onchange('custom_report_layout_id')
    def _onchange_custom_report_layout_id(self):
        """ Sincroniza la selección personalizada con el campo técnico de Odoo """
        if self.custom_report_layout_id:
            # Asignamos nuestra vista al campo que Odoo usa para validar el diseño
            self.external_report_layout_id = self.custom_report_layout_id

    def document_layout_save(self):
        """ Asegura que al guardar se mantenga el layout en la compañía """
        res = super(BaseDocumentLayout, self).document_layout_save()
        if self.custom_report_layout_id:
            self.company_id.external_report_layout_id = self.custom_report_layout_id
        return res