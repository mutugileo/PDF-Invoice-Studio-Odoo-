# -*- coding: utf-8 -*-
{
    'name': 'PDF Invoice Studio',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Invoicing',
    # Store search is keyword driven, so the summary uses the words buyers
    # actually type. Every term here maps to a feature the module really has -
    # the vendor guidelines require feature claims to be accurate.
    'summary': 'Invoice watermark: PAID, OVERDUE, DRAFT stamp on invoice PDF. '
               'Company stamp, authorised signature, custom tax label, bank details, '
               'hides duplicate shipping address',
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
    'author': 'Codzure Solutions',
    'website': 'https://github.com/mutugileo',
    # Odoo's vendor guidelines: the address used for claims and support
    # requests. It is shown only to people who have bought the app, so it is
    # not exposed on the public listing page.
    'support': 'codzuresolutions@gmail.com',
    'license': 'OPL-1',
    # Odoo reads the listing price from the manifest. Only EUR and USD are
    # supported. Odoo also requires this to be the lowest price the module is
    # offered at anywhere on the web, so do not undercut it elsewhere.
    'price': 19.00,
    'currency': 'USD',
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
