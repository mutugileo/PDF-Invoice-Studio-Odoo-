# -*- coding: utf-8 -*-

import re
from odoo import models, fields, _
from odoo.exceptions import UserError

# How strongly the status stamp prints, as an alpha against a white page.
#
# This is NOT applied as CSS opacity. wkhtmltopdf - the engine Odoo renders PDFs
# with - ignores `opacity` on the watermark and prints it at full strength, which
# turns a subtle tint into a solid block across the invoice. Verified on
# wkhtmltopdf 0.12.6 (patched qt). The alpha is therefore blended into the colour
# here, producing a flat hex that renders identically in the HTML preview and the
# PDF, with no dependence on renderer alpha support.
# These are tuned for an outline, not a filled glyph. A solid stamp - even a very
# pale one - sits on top of the line items and obscured the amounts in testing, and
# an invoice whose figures are covered is worse than one with no stamp. The stamp is
# therefore drawn as a hollow outline, which needs a stronger colour than a fill
# would to stay visible.
#
# The ceiling is deliberately well below full strength. At 0.70 the outline cut
# through the amount column hard enough to degrade "$ 11,750.00" on a printed page.
# Every value here was checked against a real PDF, not guessed.
WATERMARK_ALPHA = {
    'subtle': 0.18,
    'medium': 0.32,
    'bold': 0.50,
}

DEFAULT_WATERMARK_COLOR = '#9ca3af'

# Generating PDFs is slow and the archive is built in memory, so a batch is capped.
# Enforced both here (for the UI action) and in the controller, because the download
# route accepts move_ids straight from the query string and is reachable without it.
MAX_BULK_EXPORT = 300


class AccountMove(models.Model):
    _inherit = 'account.move'

    def is_shipping_identical_to_billing(self):
        """Helper for QWeb template: checks if delivery address matches invoice address."""
        self.ensure_one()
        shipping = self.partner_shipping_id
        billing = self.partner_id
        if not shipping or shipping == billing:
            return True

        billing_addr = (
            (billing.street or '').strip().lower(),
            (billing.street2 or '').strip().lower(),
            (billing.city or '').strip().lower(),
            (billing.zip or '').strip().lower(),
            billing.country_id.id,
        )
        shipping_addr = (
            (shipping.street or '').strip().lower(),
            (shipping.street2 or '').strip().lower(),
            (shipping.city or '').strip().lower(),
            (shipping.zip or '').strip().lower(),
            shipping.country_id.id,
        )
        return billing_addr == shipping_addr

    def _is_invoice_overdue(self):
        """Posted, still owing, and past its due date."""
        self.ensure_one()
        return bool(
            self.state == 'posted'
            and self.payment_state in ('not_paid', 'partial')
            and self.invoice_date_due
            and self.invoice_date_due < fields.Date.context_today(self)
        )

    def get_invoice_watermark(self):
        """Status stamp for this invoice, or '' when none should print.

        Odoo has no watermark of any kind, so an invoice's status is only
        readable from the payment table at the bottom. Order matters here: a
        paid invoice is never overdue, and a cancelled one is neither.
        """
        self.ensure_one()
        company = self.company_id

        if not company.invoice_watermark_enabled:
            return ''

        if self.state == 'cancel':
            return _('CANCELLED') if company.invoice_watermark_show_cancelled else ''

        if self.state == 'draft':
            return _('DRAFT') if company.invoice_watermark_show_draft else ''

        if self.payment_state == 'reversed':
            return _('REVERSED') if company.invoice_watermark_show_cancelled else ''

        if self.payment_state in ('paid', 'in_payment'):
            return _('PAID') if company.invoice_watermark_show_paid else ''

        if self._is_invoice_overdue():
            return _('OVERDUE') if company.invoice_watermark_show_overdue else ''

        if self.payment_state == 'partial':
            return _('PARTIALLY PAID') if company.invoice_watermark_show_paid else ''

        return ''

    def get_invoice_watermark_font_size(self):
        """Stamp size in px, scaled down for longer wording.

        A single size cannot serve both ends. "OVERDUE" at 58px is lost on a
        dense 30-line invoice, but "PARTIALLY PAID" - twice as long - runs off
        the right edge well before that size. Sizing by length keeps the stamp
        prominent without clipping, and a larger outline is actually kinder to
        the figures underneath: the stroke stays 1.5px while the glyphs spread
        further apart, so it crosses fewer characters.

        Widths were checked against printed A4 output, not estimated.
        """
        self.ensure_one()
        length = len(self.get_invoice_watermark())

        if length <= 9:          # PAID, DRAFT, OVERDUE, REVERSED, CANCELLED
            return 82
        if length <= 12:
            return 64
        return 52                # PARTIALLY PAID

    def get_invoice_watermark_color(self):
        """The stamp colour, with the intensity already blended toward white.

        Returns a flat hex rather than relying on CSS opacity, which the PDF
        engine ignores. See WATERMARK_ALPHA.
        """
        self.ensure_one()
        company = self.company_id
        raw = (company.invoice_watermark_color or '').strip() or DEFAULT_WATERMARK_COLOR
        alpha = WATERMARK_ALPHA.get(company.invoice_watermark_intensity, WATERMARK_ALPHA['subtle'])

        hex_digits = raw.lstrip('#')
        if len(hex_digits) == 3:
            hex_digits = ''.join(c * 2 for c in hex_digits)
        if len(hex_digits) != 6:
            hex_digits = DEFAULT_WATERMARK_COLOR.lstrip('#')

        try:
            channels = [int(hex_digits[i:i + 2], 16) for i in (0, 2, 4)]
        except ValueError:
            channels = [int(DEFAULT_WATERMARK_COLOR.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]

        blended = [round(c * alpha + 255 * (1 - alpha)) for c in channels]
        return '#%02x%02x%02x' % tuple(blended)

    def get_sanitized_invoice_filename(self):
        """Generates a clean, filesystem-safe filename for individual PDF export."""
        self.ensure_one()
        raw_number = self.name or f"invoice_{self.id}"
        clean_number = re.sub(r'[^A-Za-z0-9_\-\.]', '_', raw_number)
        partner_name = re.sub(r'[^A-Za-z0-9_\-]', '_', self.partner_id.name or 'customer')
        return f"{clean_number}_{partner_name}.pdf"

    def action_export_invoices_zip(self):
        """Server action on account.move to export selected invoices as an in-memory ZIP archive."""
        valid_moves = self.filtered(
            lambda m: m.state == 'posted' and m.move_type in (
                'out_invoice', 'out_refund', 'in_invoice', 'in_refund'
            )
        )
        if not valid_moves:
            raise UserError(_("Please select at least one posted customer invoice or vendor bill."))

        if len(valid_moves) > MAX_BULK_EXPORT:
            raise UserError(_(
                "Bulk export is capped at %s invoices per batch to prevent memory timeout.",
                MAX_BULK_EXPORT,
            ))

        move_ids_param = ",".join(map(str, valid_moves.ids))
        return {
            'type': 'ir.actions.act_url',
            'url': f'/pdf_invoice_studio/download_zip?move_ids={move_ids_param}',
            'target': 'self',
        }
