# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    invoice_title = fields.Char(
        related='company_id.invoice_title',
        readonly=False,
    )
    business_registration_number = fields.Char(
        related='company_id.business_registration_number',
        readonly=False,
    )
    tax_id_label = fields.Char(
        related='company_id.tax_id_label',
        readonly=False,
    )
    show_tax_id = fields.Boolean(
        related='company_id.show_tax_id',
        readonly=False,
    )
    show_company_registry = fields.Boolean(
        related='company_id.show_company_registry',
        readonly=False,
    )
    show_billing_address = fields.Boolean(
        related='company_id.show_billing_address',
        readonly=False,
    )
    shipping_address_mode = fields.Selection(
        related='company_id.shipping_address_mode',
        readonly=False,
    )
    payment_instructions = fields.Html(
        related='company_id.payment_instructions',
        readonly=False,
    )
    invoice_footer_note = fields.Text(
        related='company_id.invoice_footer_note',
        readonly=False,
    )
    authorized_signature = fields.Binary(
        related='company_id.authorized_signature',
        readonly=False,
    )
    authorized_signatory_name = fields.Char(
        related='company_id.authorized_signatory_name',
        readonly=False,
    )
    authorized_signatory_title = fields.Char(
        related='company_id.authorized_signatory_title',
        readonly=False,
    )
    company_stamp = fields.Binary(
        related='company_id.company_stamp',
        readonly=False,
    )
    invoice_watermark_enabled = fields.Boolean(
        related='company_id.invoice_watermark_enabled',
        readonly=False,
    )
    invoice_watermark_show_paid = fields.Boolean(
        related='company_id.invoice_watermark_show_paid',
        readonly=False,
    )
    invoice_watermark_show_overdue = fields.Boolean(
        related='company_id.invoice_watermark_show_overdue',
        readonly=False,
    )
    invoice_watermark_show_draft = fields.Boolean(
        related='company_id.invoice_watermark_show_draft',
        readonly=False,
    )
    invoice_watermark_show_cancelled = fields.Boolean(
        related='company_id.invoice_watermark_show_cancelled',
        readonly=False,
    )
    invoice_watermark_color = fields.Char(
        related='company_id.invoice_watermark_color',
        readonly=False,
    )
    invoice_watermark_intensity = fields.Selection(
        related='company_id.invoice_watermark_intensity',
        readonly=False,
    )

    primary_color = fields.Char(
        related='company_id.primary_color',
        readonly=False,
    )
    secondary_color = fields.Char(
        related='company_id.secondary_color',
        readonly=False,
    )
