# -*- coding: utf-8 -*-

import io
import zipfile
from datetime import datetime
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, UserError
from odoo.addons.pdf_invoice_studio.models.account_move import MAX_BULK_EXPORT


class PdfInvoiceStudioController(http.Controller):

    @http.route('/pdf_invoice_studio/download_zip', type='http', auth='user', methods=['GET'])
    def download_invoices_zip(self, move_ids=None, **kwargs):
        """Streams an in-memory ZIP archive containing individual PDFs for requested invoices."""
        if not move_ids:
            return request.not_found()

        try:
            ids = [int(x.strip()) for x in move_ids.split(',') if x.strip().isdigit()]
        except ValueError:
            return request.not_found()

        if not ids:
            return request.not_found()

        # move_ids arrives straight from the query string, so the batch cap has to be
        # applied here too. The UI action enforces it as well, but this route is
        # reachable by any signed-in user without going through that action, and the
        # archive is assembled entirely in memory.
        ids = list(dict.fromkeys(ids))
        if len(ids) > MAX_BULK_EXPORT:
            raise UserError(_(
                "Bulk export is capped at %s invoices per batch to prevent memory timeout.",
                MAX_BULK_EXPORT,
            ))

        moves = request.env['account.move'].browse(ids).exists()
        try:
            moves.check_access_rights('read')
            moves.check_access_rule('read')
        except AccessError:
            raise AccessError(_("You are not allowed to access these invoice records."))

        valid_moves = moves.filtered(
            lambda m: m.state == 'posted' and m.move_type in (
                'out_invoice', 'out_refund', 'in_invoice', 'in_refund'
            )
        )
        if not valid_moves:
            raise UserError(_("No valid posted invoices found to export."))

        report_action = request.env.ref('account.account_invoices', raise_if_not_found=False)
        if not report_action:
            report_action = request.env['ir.actions.report']._get_report_from_name('account.report_invoice')

        zip_buffer = io.BytesIO()
        used_filenames = set()

        with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for move in valid_moves:
                try:
                    pdf_content, _content_type = request.env['ir.actions.report']._render_qweb_pdf(
                        report_action.id if report_action else 'account.report_invoice',
                        [move.id]
                    )
                except Exception:
                    continue

                filename = move.get_sanitized_invoice_filename()
                counter = 1
                unique_filename = filename
                while unique_filename in used_filenames:
                    unique_filename = f"{filename[:-4]}_{counter}.pdf"
                    counter += 1
                used_filenames.add(unique_filename)

                archive.writestr(unique_filename, pdf_content)

        zip_buffer.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_name = f"invoices_export_{timestamp}.zip"

        return request.make_response(
            zip_buffer.getvalue(),
            headers=[
                ('Content-Type', 'application/zip'),
                ('Content-Disposition', f'attachment; filename="{download_name}"'),
                ('Content-Length', str(len(zip_buffer.getvalue()))),
            ]
        )
