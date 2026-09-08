# -*- coding: utf-8 -*-
{
    'name': 'PDF Invoice Studio',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Invoicing',
    'summary': 'PAID / OVERDUE / DRAFT status watermark on invoices, plus address collapsing, company stamp and authorised signature',
    'description': """
PDF Invoice Studio for Odoo
===========================
Transforms standard Odoo customer invoices into branded, legally compliant business documents.

What it adds
------------

* Status Watermark: a diagonal PAID, PARTIALLY PAID, OVERDUE, DRAFT, CANCELLED or REVERSED stamp across the invoice. Odoo has no watermark of any kind, so status is otherwise only readable from the payment table at the foot of the page. Choose the colour, the intensity, and which statuses are stamped.
* Dynamic Address Collapsing: hides the shipping address when it merely repeats the billing address, and widens the remaining block so there is no empty gap. Standard Odoo prints the same address twice.
* Corporate Stamp and Authorised Signature: upload a company seal and a signature image, with signatory name and title.
* Custom Fiscal Label: print "KRA PIN", "GSTIN", "VAT No" or any local wording instead of Odoo's hardcoded "Tax ID".
* Invoice Title and Registration Number: set the document heading and show your company registration number in the header.
* Bulk Export to ZIP: export selected invoices as individually named PDFs in one archive, always as final invoices. Odoo 17's own bulk export falls back to a pro-forma for any invoice that has not been printed yet, and skips vendor bills.

Configured entirely from Invoicing, Configuration, Settings. No developer mode, no QWeb editing.

Tested against Odoo 17.0.

""",
    'author': 'Codzure',
    'website': 'https://github.com/codzure',
    'license': 'OPL-1',
    'depends': [
        'base',
        'account',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
        'report/report_invoice_templates.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
