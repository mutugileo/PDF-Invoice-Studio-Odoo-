# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    invoice_title = fields.Char(
        string='Invoice Document Title',
        default='TAX INVOICE',
        help='Title displayed prominently at the top of customer invoices.',
    )
    business_registration_number = fields.Char(
        string='Company Registration Number',
        help='Official corporate registration or business permit number.',
    )
    tax_id_label = fields.Char(
        string='Tax Identification Label',
        default='Tax / VAT PIN',
        help='Label used for displaying the tax identifier (e.g. VAT No, PIN, GSTIN).',
    )
    show_tax_id = fields.Boolean(
        string='Display Tax Identification',
        default=True,
    )
    show_company_registry = fields.Boolean(
        string='Display Company Registration',
        default=True,
    )
    show_billing_address = fields.Boolean(
        string='Display Billing Address',
        default=True,
        help='Whether to show the customer billing address block.',
    )
    shipping_address_mode = fields.Selection(
        selection=[
            ('always', 'Always Show'),
            ('auto', 'Hide if Matches Billing (Recommended)'),
            ('never', 'Never Show'),
        ],
        string='Shipping Address Display',
        default='auto',
        help='Controls when the shipping address is displayed. "Hide if Matches Billing" '
             'collapses duplicate shipping blocks and expands the billing block.',
    )
    payment_instructions = fields.Html(
        string='Payment Instructions & Bank Details',
        help='Bank account details, wire instructions, or mobile money payment steps '
             'rendered below invoice totals.',
    )
    invoice_footer_note = fields.Text(
        string='Invoice Footer Note',
        default='Thank you for your business.',
        help='Custom terms or thank you note displayed in the invoice footer.',
    )
    authorized_signature = fields.Binary(
        string='Authorized Signature Image',
        help='Transparent PNG or JPG of authorized sign-off signature.',
    )
    authorized_signatory_name = fields.Char(
        string='Signatory Name',
        help='Full name of the authorized signatory.',
    )
    authorized_signatory_title = fields.Char(
        string='Signatory Title',
        help='Job title of the authorized signatory (e.g. Finance Director, CFO).',
    )
    company_stamp = fields.Binary(
        string='Company Stamp / Seal Image',
        help='Official company stamp image placed alongside authorized signature.',
    )
    # --- Status watermark -------------------------------------------------
    # Odoo has no watermark concept anywhere in Community, so the status of an
    # invoice is only readable from the payment lines. A stamp makes it obvious
    # at a glance on a printed or forwarded copy.
    invoice_watermark_enabled = fields.Boolean(
        string='Show Status Watermark',
        default=True,
        help='Print a diagonal status stamp (PAID, OVERDUE, DRAFT...) across the invoice.',
    )
    invoice_watermark_show_paid = fields.Boolean(
        string='Stamp Paid Invoices', default=True,
    )
    invoice_watermark_show_overdue = fields.Boolean(
        string='Stamp Overdue Invoices', default=True,
    )
    invoice_watermark_show_draft = fields.Boolean(
        string='Stamp Drafts', default=True,
    )
    invoice_watermark_show_cancelled = fields.Boolean(
        string='Stamp Cancelled Invoices', default=True,
    )
    invoice_watermark_color = fields.Char(
        string='Watermark Color',
        default='#9ca3af',
        help='Hex color of the status stamp.',
    )
    invoice_watermark_intensity = fields.Selection(
        selection=[
            ('subtle', 'Subtle'),
            ('medium', 'Medium'),
            ('bold', 'Bold'),
        ],
        string='Watermark Intensity',
        default='subtle',
        help='How strongly the stamp is printed. Subtle keeps the invoice easy to read.',
    )

    primary_color = fields.Char(
        string='Primary Accent Color',
        default='#1e293b',
        help='Hex color code used for invoice table headers, borders, and main accents.',
    )
    secondary_color = fields.Char(
        string='Secondary Accent Color',
        default='#f8fafc',
        help='Hex color code used for alternating row shading and sub-panels.',
    )
