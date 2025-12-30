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
