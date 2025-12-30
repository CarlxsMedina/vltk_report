from odoo import models, fields, api
from num2words import num2words


class AccountMoveVLTK(models.Model):
    _inherit = 'account.move'

    tgr_informacion_adicional = fields.Text(string="Información Adicional", help="Información extra para mostrar en el reporte PDF")

    def get_amount_in_words_vltk(self):
        """
        Convierte el monto total de la factura a texto en español.
        Método seguro que no falla si hay problemas.
        """
        self.ensure_one()
        
        try:
            # Separar parte entera y decimal
            amount_i, amount_d = divmod(self.amount_total, 1)
            amount_d = int(round(amount_d * 100, 2))
            
            # Convertir a palabras en español
            words = num2words(amount_i, lang='es')
            
            # Formato: "CINCO DÓLARES Y 00/100 CENTAVOS"
            result = f"{words.upper()} DÓLARES Y {amount_d:02d}/100 CENTAVOS"
            
            return result
        except Exception:
            # Si falla, devolver al menos el monto numérico
            return f"${self.amount_total:.2f}"

    def action_print_vltk_report(self):
        self.ensure_one()
        # Usamos el nuevo ID único para el botón
        return self.env.ref('VLTK_Custom_Report.account_invoices_vltk_btn').report_action(self)

    def get_vltk_qr_code_url(self):
        """
        Genera la URL COMPLETA para el src de la imagen del código QR.
        Usa sudo() para garantizar acceso a campos y hace logging para debug.
        """
        self.ensure_one()
        import urllib.parse
        import logging
        _logger = logging.getLogger(__name__)

        # Obtener valores con sudo por si acaso hay reglas de registro limitando
        record = self.sudo()
        
        base_url = "https://admin.factura.gob.sv/consultaPublica"
        ambiente = "00"
        cod_gen = record.tgr_l10n_sv_edi_codigo_generacion
        if not cod_gen:
            _logger.warning(f"VLTK QR: Codigo generacion vacio para factura {self.name} (ID: {self.id})")
            cod_gen = ""
            
        # Asegurar formato fecha YYYY-MM-DD
        date_str = str(record.invoice_date) if record.invoice_date else ""
        
        target_url = f"{base_url}?ambiente={ambiente}&codGen={cod_gen}&fechaEmi={date_str}"
        _logger.info(f"VLTK QR generated: {target_url}")
        
        # Codificar
        safe_value = urllib.parse.quote(target_url)
        return f"/report/barcode/?barcode_type=QR&value={safe_value}&width=115&height=115"

    def _message_post_after_hook(self, message, msg_vals):
        """
        Override para agregar automáticamente el PDF VLTK y el JSON del DTE
        cuando se envía un correo desde la factura.
        """
        res = super()._message_post_after_hook(message, msg_vals)
        
        # Solo procesar si es una factura/documento válido
        if self.move_type not in ['out_invoice', 'out_refund']:
            return res
            
        # Solo si el mensaje incluye adjuntos o es envío de factura
        if not msg_vals.get('attachment_ids') and not self._context.get('mark_invoice_as_sent'):
            return res
        
        attachments_to_add = []
        
        # 1. Generar y adjuntar el PDF del reporte VLTK
        try:
            report = self.env.ref('VLTK_Custom_Report.account_invoices_vltk_btn')
            pdf_content, _ = report._render_qweb_pdf(report.report_name, self.ids)
            
            pdf_name = f"Factura_{self.name.replace('/', '_')}_VLTK.pdf"
            pdf_attachment = self.env['ir.attachment'].create({
                'name': pdf_name,
                'type': 'binary',
                'datas': pdf_content,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf'
            })
            attachments_to_add.append(pdf_attachment.id)
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning(f"No se pudo adjuntar PDF VLTK para {self.name}: {e}")
        
        # 2. Buscar y adjuntar el archivo JSON del DTE si existe
        try:
            # Buscar el attachment del JSON DTE
            json_attachment = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', self.id),
                ('name', 'ilike', '.json'),
                '|',
                ('name', 'ilike', 'DTE'),
                ('name', 'ilike', self.name.replace('/', '_'))
            ], limit=1)
            
            if json_attachment:
                attachments_to_add.append(json_attachment.id)
            else:
                # Si no encontramos como attachment, intentar desde el campo del módulo TGR
                if hasattr(self, 'tgr_l10n_sv_edi_documento_json') and self.tgr_l10n_sv_edi_documento_json:
                    json_name = f"DTE_{self.name.replace('/', '_')}.json"
                    json_attachment = self.env['ir.attachment'].create({
                        'name': json_name,
                        'type': 'binary',
                        'datas': self.tgr_l10n_sv_edi_documento_json,
                        'res_model': self._name,
                        'res_id': self.id,
                        'mimetype': 'application/json'
                    })
                    attachments_to_add.append(json_attachment.id)
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning(f"No se pudo adjuntar JSON DTE para {self.name}: {e}")
        
        # Agregar los attachments al mensaje
        if attachments_to_add and message:
            message.write({'attachment_ids': [(4, att_id) for att_id in attachments_to_add]})
        
        return res
